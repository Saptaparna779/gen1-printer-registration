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


def test_printer_email_id_is_unique_across_printers():
    p1 = registration.register_printer(
        serial_number="SN-0005",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    p2 = registration.register_printer(
        serial_number="SN-0006",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    assert p1.printer_email_id != p2.printer_email_id
    assert store.get_printer_by_email(p1.printer_email_id).printer_id == p1.printer_id


def test_generate_printer_email_id_retries_on_collision(monkeypatch):
    calls = {"count": 0}
    fixed_slug = "abcdefghij"

    def fake_choices(pool, k):
        calls["count"] += 1
        return list(fixed_slug) if calls["count"] == 1 else list("zzzzzzzzzz")

    store.index_email(f"{fixed_slug}@print.hpeprint.com", "existing-printer-id")
    monkeypatch.setattr(registration.random, "choices", fake_choices)

    new_email = registration._generate_printer_email_id()
    assert new_email == "zzzzzzzzzz@print.hpeprint.com"
    assert calls["count"] == 2


def test_register_printer_rejects_whitespace_only_fields():
    with pytest.raises(registration.RegistrationError):
        registration.register_printer(
            serial_number="   ",
            model_number="HP-LJ-2055",
            firmware_version="1.0.0",
        )


def test_xmpp_node_not_reassigned_on_reregistration():
    p1 = registration.register_printer(
        serial_number="SN-0007",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    original_node = p1.xmpp_node

    p2 = registration.register_printer(
        serial_number="SN-0007",
        model_number="HP-LJ-2055",
        firmware_version="1.0.1",
    )

    assert p2.xmpp_node == original_node


def test_registration_history_distinguishes_reregistration():
    p1 = registration.register_printer(
        serial_number="SN-1000",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    assert "Registration started" in p1.registration_history[0]

    p2 = registration.register_printer(
        serial_number="SN-1000",
        model_number="HP-LJ-2055",
        firmware_version="1.0.1",
    )
    assert any("Re-registration started" in entry for entry in p2.registration_history)


def test_claim_printer_rejects_expired_claim_code():
    from datetime import datetime, timedelta
    printer = registration.register_printer(
        serial_number="SN-2000",
        model_number="HP-LJ-2055",
        firmware_version="1.0.0",
    )
    printer.claim_code.expires_at = datetime.utcnow() - timedelta(minutes=1)

    with pytest.raises(registration.InvalidClaimCodeError):
        registration.claim_printer(printer.claim_code.code, user_id="user-789")

    assert printer.status != "CLAIMED"
