"""
Baseline regression tests for Printer Onboarding & Registration.

NOTE (demo): this file intentionally covers only the happy path. It
represents the test coverage that exists BEFORE the agentic Copilot
workflow runs. The workflow is expected to read the relevant Jira
ticket(s) and generate additional tests for the acceptance criteria,
edge cases, and bug-fix verification that aren't covered here yet.
"""
import pytest
from app import registration, store


def test_register_new_printer_success():
    printer = registration.register_printer(
        serial_number="SN-0001",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )

    assert printer.cloud_id is not None
    assert printer.printer_email_id.endswith("@print.hpeprint.com")
    assert printer.claim_code is not None
    assert printer.xmpp_node is not None
    assert printer.status == "REGISTERED"


def test_claim_printer_success():
    printer = registration.register_printer(
        serial_number="SN-0002",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )

    claimed = registration.claim_printer(printer.claim_code.code, user_id="user-123")

    assert claimed.status == "CLAIMED"
    assert claimed.owner_user_id == "user-123"


def test_capabilities_captured_for_color_mfp_model():
    printer = registration.register_printer(
        serial_number="SN-0003",
        model_number="HP-C-MFP-9500",
        firmware_version="2.1.0",
    )

    caps = store.get_capabilities(printer.printer_id)
    assert caps.supports_color is True
    assert caps.supports_scan is True


def test_claim_printer_rejects_already_claimed_printer():
    printer = registration.register_printer(
        serial_number="SN-0004",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    registration.claim_printer(printer.claim_code.code, user_id="user-123")

    # Simulate someone obtaining a second valid, unused claim code for
    # the same already-claimed printer (e.g. via a re-registration bug),
    # and attempting to claim it again with a different user.
    printer.claim_code = registration._generate_claim_code()

    with pytest.raises(registration.InvalidClaimCodeError):
        registration.claim_printer(printer.claim_code.code, user_id="user-456")
