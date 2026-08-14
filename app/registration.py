"""
Core business logic for Printer Onboarding & Registration.

Implements the flow described in BUD section 11.1:
  1. Validate printer identity
  2. Create cloud identity (Cloud ID, Printer Email ID, Claim Code)
  3. Capture printer capabilities
  4. Assign XMPP node
  5. Generate + print Welcome/Info page (final success checkpoint)
  6. Roll back completely on failure before the Welcome Page prints
"""
import logging
import random
import string
import uuid
from datetime import datetime, timedelta

from app import store
from app.models import Printer, PrinterCapabilities, PrinterStatus, ClaimCode
from app.welcome_page import generate_and_print_welcome_page, WelcomePagePrintError
from app.xmpp import assign_xmpp_node

logger = logging.getLogger(__name__)


class RegistrationError(Exception):
    pass


class InvalidClaimCodeError(Exception):
    pass


CLAIM_CODE_TTL_MINUTES = 15  # intended TTL per Claim Code business rule


def _generate_cloud_id() -> str:
    return f"CID-{uuid.uuid4().hex[:12].upper()}"


def _generate_printer_email_id() -> str:
    while True:
        slug = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        email = f"{slug}@print.hpeprint.com"
        if not store.email_in_use(email):
            return email


def _generate_claim_code() -> ClaimCode:
    code = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    now = datetime.utcnow()
    return ClaimCode(
        code=code,
        created_at=now,
        expires_at=now + timedelta(minutes=CLAIM_CODE_TTL_MINUTES),
    )


def _model_family(model_number: str) -> str:
    """
    GOAR-15: crude model-family extraction used to distinguish a firmware/
    revision-level model_number change from a materially different physical
    device, e.g. 'HP-LJ-4200' -> 'HP-LJ', 'HP-LJ-4250' -> 'HP-LJ'.
    Intentionally simple for now; a real implementation would use a proper
    model catalog/lookup.
    """
    parts = model_number.strip().upper().split("-")
    return "-".join(parts[:-1]) if len(parts) > 1 else parts[0]


def _capture_capabilities(printer_id: str, model_number: str) -> PrinterCapabilities:
    """
    Capture printer capabilities so downstream services (app printing,
    email-to-print) don't need to re-query the device. Very small mock
    lookup table keyed by model prefix.
    """
    color = model_number.upper().startswith("HP-C")
    scan = "MFP" in model_number.upper()
    return PrinterCapabilities(
        printer_id=printer_id,
        supports_print=True,
        supports_scan=scan,
        supports_color=color,
        max_dpi=1200 if color else 600,
    )


def register_printer(
    serial_number: str,
    model_number: str,
    firmware_version: str,
    simulate_welcome_page_failure: bool = False,
) -> Printer:
    """
    Register a new printer, or re-register one that already exists.
    Returns the resulting Printer record on success.
    Raises RegistrationError on failure (after rolling back partial state).
    """
    if not serial_number.strip() or not model_number.strip() or not firmware_version.strip():
        raise RegistrationError("serial_number, model_number and firmware_version are required")

    existing = store.get_printer_by_serial(serial_number)

    if existing:
        printer = existing

        # GOAR-15 fix applied: re-registration allowed arbitrary model/firmware
        # overwrite with no spoofing protection. A model_number change on an
        # existing serial number is now flagged for review, and a materially
        # different model family is rejected outright.
        if printer.model_number.strip().upper() != model_number.strip().upper():
            printer.log(
                f"GOAR-15: model_number changed on re-registration "
                f"(old={printer.model_number}, new={model_number}) -- flagged for review"
            )
            logger.warning(
                "GOAR-15: model_number changed on re-registration | "
                f"serial={serial_number} old_model={printer.model_number} new_model={model_number}",
                extra={
                    "serial_number": serial_number,
                    "old_model": printer.model_number,
                    "new_model": model_number,
                },
            )

            if _model_family(printer.model_number) != _model_family(model_number):
                raise RegistrationError(
                    "Re-registration rejected: model family mismatch "
                    f"(existing='{printer.model_number}', incoming='{model_number}'). "
                    "This looks like a different physical device reusing the same "
                    "serial number."
                )

        printer.model_number = model_number
        printer.firmware_version = firmware_version
    else:
        printer = Printer(
            printer_id=str(uuid.uuid4()),
            serial_number=serial_number,
            model_number=model_number,
            firmware_version=firmware_version,
            status=PrinterStatus.PENDING,
        )
    printer_id = printer.printer_id
    printer.log("Re-registration started" if existing else "Registration started")

    # Step 1: Cloud identity
    # GOAR-3: always generate a NEW Cloud ID on every registration call --
    # including re-registration -- per business rule 3/6. Never reuse an
    # existing printer's cloud_id, even if one is already on record.
    printer.cloud_id = _generate_cloud_id()

    printer.printer_email_id = _generate_printer_email_id()
    store.index_email(printer.printer_email_id, printer_id)
    if printer.status != PrinterStatus.CLAIMED:
        printer.claim_code = _generate_claim_code()

    printer.log(f"Cloud identity created: {printer.cloud_id}")

    store.save_printer(printer)

    # Step 2: Capture capabilities
    if not store.get_capabilities(printer_id):
        capabilities = _capture_capabilities(printer_id, model_number)
        store.save_capabilities(capabilities)
        printer.log("Capabilities captured")
    else:
        printer.log("Capabilities already on record; skipped recapture")

    # Step 3: XMPP connectivity
    if not printer.xmpp_node:
        printer.xmpp_node = assign_xmpp_node(printer_id)
        printer.log(f"XMPP node assigned: {printer.xmpp_node}")
    store.save_printer(printer)

    # Step 4: Welcome / Info page -- final checkpoint
    try:
        generate_and_print_welcome_page(
            printer_id=printer.printer_id,
            cloud_id=printer.cloud_id,
            printer_email_id=printer.printer_email_id,
            claim_code=printer.claim_code.code,
            force_failure=simulate_welcome_page_failure,
        )
    except WelcomePagePrintError as exc:
        _rollback_registration(printer)
        raise RegistrationError(str(exc)) from exc

    if printer.status != PrinterStatus.CLAIMED:
        printer.status = PrinterStatus.REGISTERED
    printer.log("Welcome page printed successfully; registration complete")
    store.save_printer(printer)
    store.index_serial(serial_number, printer_id)

    return printer


def _rollback_registration(printer: Printer) -> None:
    """
    Roll back a failed registration. Per business rule, no partial data
    should be retained if the Welcome Page fails to print.
    """
    store.delete_printer(printer.printer_id)
    store.remove_serial_index(printer.serial_number)
    store.delete_capabilities(printer.printer_id)


def claim_printer(claim_code: str, user_id: str) -> Printer:
    """
    Link a printer to a user account using its Claim Code.
    See BUD section 11.3.
    """
    target = None
    for printer in store.all_printers():
        if printer.claim_code and printer.claim_code.code == claim_code:
            target = printer
            break

    if target is None:
        raise InvalidClaimCodeError("Claim code not recognized")

    if target.status == PrinterStatus.CLAIMED:
        raise InvalidClaimCodeError("Printer is already claimed")

    if datetime.utcnow() > target.claim_code.expires_at:
        raise InvalidClaimCodeError("Claim code has expired")

    if target.claim_code.used:
        raise InvalidClaimCodeError("Claim code has already been used")

    target.owner_user_id = user_id
    target.status = PrinterStatus.CLAIMED
    target.claim_code.used = True
    target.log(f"Claimed by user {user_id}")
    store.save_printer(target)
    return target


def deregister_printer(printer_id: str) -> None:
    """
    Remove a printer from cloud services and clean up its data.
    See BUD section 11.10.
    """
    printer = store.get_printer(printer_id)
    if printer is None:
        raise RegistrationError(f"No printer found with id {printer_id}")

    if printer.claim_code:
        printer.claim_code.used = True

    store.delete_capabilities(printer_id)
    store.remove_serial_index(printer.serial_number)
    store.delete_printer(printer_id)

