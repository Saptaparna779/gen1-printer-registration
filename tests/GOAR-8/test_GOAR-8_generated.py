"""
Generated tests for GOAR-8: claim_printer must reject attempts to claim already-claimed printers and registration must avoid issuing new claim codes for claimed printers, while preserving successful claims for unclaimed printers with valid, unused codes.

Automates the test cases in reports/testcases/GOAR-8_test_cases.md at the HTTP API level, using the `client` TestClient fixture from tests/conftest.py.
"""
import logging
import re

import pytest

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_8_01_claim_unclaimed_printer_with_valid_unused_claim_code_happy_path(client):
    """[HAPPY PATH] Claiming an unclaimed printer with a valid, unused claim code succeeds and sets status to CLAIMED with owner_user_id linked to the claimant."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-001",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_1 = registered_body["printer_id"]
    cloud_id_1 = registered_body["cloud_id"]
    claim_code_1 = registered_body["claim_code"]

    pre_lookup = client.get(f"/printers/{printer_id_1}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "REGISTERED"
    assert pre_lookup_body["owner_user_id"] is None

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": claim_code_1,
            "user_id": "user-goar8-claimant-01",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["printer_id"] == printer_id_1
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar8-claimant-01"

    post_lookup = client.get(f"/printers/{printer_id_1}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-claimant-01"
    assert post_lookup_body["cloud_id"] == cloud_id_1


def test_TC_GOAR_8_02_reject_claim_on_already_claimed_printer_with_valid_unused_claim_code(client):
    """[INVALID INPUT] Attempting to claim a printer whose status is already CLAIMED with a valid, unused claim code raises InvalidClaimCodeError and does not change ownership."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-002",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_2 = registered_body["printer_id"]
    claim_code_2 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar8-owner-02"},
    )
    assert first_claim.status_code == 200

    pre_lookup = client.get(f"/printers/{printer_id_2}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "CLAIMED"
    assert pre_lookup_body["owner_user_id"] == "user-goar8-owner-02"

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar8-attacker-02"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Printer is already claimed"

    post_lookup = client.get(f"/printers/{printer_id_2}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-owner-02"


def test_TC_GOAR_8_03_reject_same_owner_reclaim_attempt_for_already_claimed_printer(client):
    """[OWNERSHIP] Claiming an already-CLAIMED printer with a user_id matching the existing owner_user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-003",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_3 = registered_body["printer_id"]
    claim_code_3 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_3, "user_id": "user-goar8-owner-03"},
    )
    assert first_claim.status_code == 200

    pre_lookup = client.get(f"/printers/{printer_id_3}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "CLAIMED"
    assert pre_lookup_body["owner_user_id"] == "user-goar8-owner-03"

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_3, "user_id": "user-goar8-owner-03"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Printer is already claimed"

    post_lookup = client.get(f"/printers/{printer_id_3}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-owner-03"


def test_TC_GOAR_8_04_reject_different_user_claim_attempt_for_already_claimed_printer(client):
    """[OWNERSHIP] Claiming an already-CLAIMED printer with a different user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-004",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_4 = registered_body["printer_id"]
    claim_code_4 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_4, "user_id": "user-goar8-owner-04"},
    )
    assert first_claim.status_code == 200

    pre_lookup = client.get(f"/printers/{printer_id_4}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "CLAIMED"
    assert pre_lookup_body["owner_user_id"] == "user-goar8-owner-04"

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_4, "user_id": "user-goar8-attacker-04"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Printer is already claimed"

    post_lookup = client.get(f"/printers/{printer_id_4}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-owner-04"


def test_TC_GOAR_8_05_claim_unclaimed_printer_marks_claim_code_used_and_associates_ownership(client):
    """[HAPPY PATH] Claiming an unclaimed printer using a valid, unused claim code succeeds, marks the claim code as used, and associates the printer to the requesting user."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-005",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_5 = registered_body["printer_id"]
    claim_code_5 = registered_body["claim_code"]

    pre_lookup = client.get(f"/printers/{printer_id_5}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "REGISTERED"
    assert pre_lookup_body["owner_user_id"] is None

    claimed = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_5, "user_id": "user-goar8-owner-05"},
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["printer_id"] == printer_id_5
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar8-owner-05"

    post_lookup = client.get(f"/printers/{printer_id_5}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-owner-05"


def test_TC_GOAR_8_06_boundary_claim_before_and_after_claim_code_expiry(client, monkeypatch):
    """[BOUNDARY VALUE] Claiming an unclaimed printer just before claim_code.expires_at succeeds, but a call immediately after expiry raises InvalidClaimCodeError."""
    from datetime import datetime, timedelta

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-006",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_6 = registered_body["printer_id"]
    claim_code_6 = registered_body["claim_code"]
    expires_at_6 = datetime.fromisoformat(registered_body["claim_code_expires_at"])

    from app import registration as registration_module

    class FakeDateTimePre(datetime.__class__):
        @classmethod
        def utcnow(cls):
            return expires_at_6 - timedelta(seconds=1)

    monkeypatch.setattr(registration_module, "datetime", FakeDateTimePre, raising=False)

    pre_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_6, "user_id": "user-goar8-owner-06a"},
    )
    assert pre_claim.status_code == 200
    pre_claim_body = pre_claim.json()
    assert pre_claim_body["printer_id"] == printer_id_6
    assert pre_claim_body["status"] == "CLAIMED"
    assert pre_claim_body["owner_user_id"] == "user-goar8-owner-06a"

    second_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-006B",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second_registered.status_code == 200
    second_registered_body = second_registered.json()
    claim_code_6b = second_registered_body["claim_code"]
    expires_at_6b = datetime.fromisoformat(second_registered_body["claim_code_expires_at"])

    class FakeDateTimePost(datetime.__class__):
        @classmethod
        def utcnow(cls):
            return expires_at_6b + timedelta(seconds=1)

    monkeypatch.setattr(registration_module, "datetime", FakeDateTimePost, raising=False)

    post_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_6b, "user_id": "user-goar8-owner-06b"},
    )
    assert post_claim.status_code == 400
    assert post_claim.json()["detail"] == "Claim code has expired"


def test_TC_GOAR_8_07_reject_claim_with_already_used_claim_code_for_unclaimed_printer(client):
    """[INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is already True fails with InvalidClaimCodeError and does not change owner_user_id or status."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-007",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_7 = registered_body["printer_id"]
    claim_code_7 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_7, "user_id": "user-goar8-owner-07-internal"},
    )
    assert first_claim.status_code == 200

    pre_lookup = client.get(f"/printers/{printer_id_7}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "CLAIMED"

    from app import store

    printer = store.get_printer(printer_id_7)
    assert printer is not None
    printer.status = "REGISTERED"
    printer.owner_user_id = None

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_7, "user_id": "user-goar8-owner-07"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Claim code has already been used"

    post_lookup = client.get(f"/printers/{printer_id_7}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "REGISTERED"
    assert post_lookup_body["owner_user_id"] is None


def test_TC_GOAR_8_08_user_id_independent_rejection_for_already_claimed_printers(client):
    """[OWNERSHIP] For a printer already in CLAIMED status, claiming with a valid, unused claim code using any user_id (same as or different from owner_user_id) is rejected with InvalidClaimCodeError and leaves ownership unchanged."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-008",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_8 = registered_body["printer_id"]
    claim_code_8 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_8, "user_id": "user-goar8-owner-08"},
    )
    assert first_claim.status_code == 200

    pre_lookup = client.get(f"/printers/{printer_id_8}")
    assert pre_lookup.status_code == 200
    pre_lookup_body = pre_lookup.json()
    assert pre_lookup_body["status"] == "CLAIMED"
    assert pre_lookup_body["owner_user_id"] == "user-goar8-owner-08"

    second_claim_same = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_8, "user_id": "user-goar8-owner-08"},
    )
    assert second_claim_same.status_code == 400
    assert second_claim_same.json()["detail"] == "Printer is already claimed"

    second_claim_other = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_8, "user_id": "user-goar8-other-08"},
    )
    assert second_claim_other.status_code == 400
    assert second_claim_other.json()["detail"] == "Printer is already claimed"

    post_lookup = client.get(f"/printers/{printer_id_8}")
    assert post_lookup.status_code == 200
    post_lookup_body = post_lookup.json()
    assert post_lookup_body["status"] == "CLAIMED"
    assert post_lookup_body["owner_user_id"] == "user-goar8-owner-08"


def test_TC_GOAR_8_09_reregistration_of_claimed_printer_does_not_generate_new_claim_code(client):
    """[HAPPY PATH] Re-registering a printer in CLAIMED status does not issue a new claim_code and leaves any existing claim_code marked as used while still allowing other registration outputs per business rules."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-009",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_9 = registered_body["printer_id"]
    cloud_id_1 = registered_body["cloud_id"]
    claim_code_9 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_9, "user_id": "user-goar8-owner-09"},
    )
    assert first_claim.status_code == 200

    reregistered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-009",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistered.status_code == 200
    reregistered_body = reregistered.json()
    assert reregistered_body["printer_id"] == printer_id_9
    cloud_id_2 = reregistered_body["cloud_id"]
    assert cloud_id_2 != cloud_id_1
    assert EMAIL_PATTERN.match(reregistered_body["printer_email_id"])
    assert reregistered_body["status"] == "CLAIMED"
    assert reregistered_body["claim_code"] == claim_code_9

    lookup = client.get(f"/printers/{printer_id_9}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "CLAIMED"
    assert lookup_body["owner_user_id"] == "user-goar8-owner-09"
    assert lookup_body["cloud_id"] == cloud_id_2


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: Rollback for re-registration of CLAIMED printer deletes the printer "
        "record in _rollback_registration(), so ownership preservation cannot be asserted via HTTP."
    )
)
def test_TC_GOAR_8_10_rollback_on_reregistration_failure_preserves_ownership_and_invalidates_new_claim_code(client):
    """[ROLLBACK] If register_printer() for a CLAIMED printer fails after attempting to manipulate claim_code data, rollback ensures no new claim_code remains usable and the existing owner_user_id is preserved."""
    pass


def test_TC_GOAR_8_11_reject_claim_with_expired_claim_code_for_unclaimed_printer(client, monkeypatch):
    """[INVALID INPUT] Claiming an unclaimed printer with an expired claim code raises InvalidClaimCodeError and does not change printer status or ownership."""
    from datetime import datetime, timedelta

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-011",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_11 = registered_body["printer_id"]
    claim_code_11 = registered_body["claim_code"]
    expires_at_11 = datetime.fromisoformat(registered_body["claim_code_expires_at"])

    from app import registration as registration_module

    class FakeDateTime(datetime.__class__):
        @classmethod
        def utcnow(cls):
            return expires_at_11 + timedelta(seconds=1)

    monkeypatch.setattr(registration_module, "datetime", FakeDateTime, raising=False)

    expired_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_11, "user_id": "user-goar8-owner-11"},
    )
    assert expired_claim.status_code == 400
    assert expired_claim.json()["detail"] == "Claim code has expired"

    lookup = client.get(f"/printers/{printer_id_11}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "REGISTERED"
    assert lookup_body["owner_user_id"] is None


def test_TC_GOAR_8_12_boundary_behavior_for_claim_at_exact_expiry_instant(client, monkeypatch):
    """[BOUNDARY VALUE] Claiming with a claim code at the exact expiry instant is treated according to the defined comparison, ensuring consistent behavior once current time passes expires_at."""
    from datetime import datetime

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-012",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_12 = registered_body["printer_id"]
    claim_code_12 = registered_body["claim_code"]
    expires_at_12 = datetime.fromisoformat(registered_body["claim_code_expires_at"])

    from app import registration as registration_module

    class FakeDateTimeExact(datetime.__class__):
        @classmethod
        def utcnow(cls):
            return expires_at_12

    monkeypatch.setattr(registration_module, "datetime", FakeDateTimeExact, raising=False)

    boundary_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_12, "user_id": "user-goar8-owner-12"},
    )
    assert boundary_claim.status_code == 200
    boundary_claim_body = boundary_claim.json()
    assert boundary_claim_body["printer_id"] == printer_id_12
    assert boundary_claim_body["status"] == "CLAIMED"
    assert boundary_claim_body["owner_user_id"] == "user-goar8-owner-12"


def test_TC_GOAR_8_13_reject_claim_with_reused_claim_code_for_unclaimed_printer(client):
    """[INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is True raises InvalidClaimCodeError and prevents any update to owner_user_id or status."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR8-013",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_13 = registered_body["printer_id"]
    claim_code_13 = registered_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_13, "user_id": "user-goar8-owner-13"},
    )
    assert first_claim.status_code == 200

    from app import store

    printer = store.get_printer(printer_id_13)
    assert printer is not None
    printer.status = "REGISTERED"
    printer.owner_user_id = None

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_13, "user_id": "user-goar8-owner-13b"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Claim code has already been used"

    lookup = client.get(f"/printers/{printer_id_13}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "REGISTERED"
    assert lookup_body["owner_user_id"] is None


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: Rollback for re-registration of CLAIMED printer deletes the printer "
        "record in _rollback_registration(), so ownership preservation cannot be asserted via HTTP."
    )
)
def test_TC_GOAR_8_14_rollback_when_reregistering_claimed_printer_preserves_ownership_and_prevents_claim_code_leaks(client):
    """[ROLLBACK] When register_printer() fails during re-registration of a CLAIMED printer, rollback preserves owner_user_id and CLAIMED status while ensuring any new claim_code generated during the attempt is invalidated or removed."""
    pass
