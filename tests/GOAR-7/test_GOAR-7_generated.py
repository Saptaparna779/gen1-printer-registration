"""
Generated tests for GOAR-7: claimed-printer re-registration must preserve existing claim codes and ownership while continuing to generate new claim codes for unclaimed printers, and rollback semantics must ensure failed registrations do not leave usable claim codes.

Automates the test cases in reports/testcases/GOAR-7_test_cases.md at the HTTP API level, using the `client` TestClient fixture from tests/conftest.py.
"""

import re
import pytest
import logging

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_7_01_reregister_claimed_printer_preserves_existing_claim_code(client):
    """Re-register an already-CLAIMED printer and confirm no new claim code is generated and the existing claim code value is preserved."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-001",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    printer_id = initial_body["printer_id"]
    claim_code_1 = initial_body["claim_code"]
    expires_at_1 = initial_body["claim_code_expires_at"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-a"},
    )
    assert claim_response.status_code == 200
    claim_body = claim_response.json()
    assert claim_body["status"] == "CLAIMED"
    assert claim_body["owner_user_id"] == "user-goar7-a"

    reregistration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-001",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration.status_code == 200
    body = reregistration.json()
    assert body["printer_id"] == printer_id
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    claim_code_2 = body["claim_code"]
    expires_at_2 = body["claim_code_expires_at"]
    assert claim_code_2 == claim_code_1
    assert expires_at_2 == expires_at_1
    assert body["xmpp_node"]
    assert body["status"] == "CLAIMED"
    assert any(
        "Registration started" in entry or "Re-registration started" in entry
        for entry in body["history"]
    )


def test_TC_GOAR_7_02_consecutive_reregistrations_of_claimed_printer_do_not_change_claim_code(client):
    """Perform two consecutive re-registrations of the same CLAIMED printer and confirm that the claim code remains unchanged across both calls."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-002",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    printer_id = initial_body["printer_id"]
    claim_code_1 = initial_body["claim_code"]
    expires_at_1 = initial_body["claim_code_expires_at"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-b"},
    )
    assert claim_response.status_code == 200
    assert claim_response.json()["status"] == "CLAIMED"

    reregistration_1 = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-002",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration_1.status_code == 200
    body_1 = reregistration_1.json()
    assert body_1["printer_id"] == printer_id
    assert CLOUD_ID_PATTERN.match(body_1["cloud_id"])
    assert EMAIL_PATTERN.match(body_1["printer_email_id"])
    claim_code_call1 = body_1["claim_code"]
    expires_at_call1 = body_1["claim_code_expires_at"]
    assert claim_code_call1 == claim_code_1
    assert expires_at_call1 == expires_at_1
    assert body_1["xmpp_node"]
    assert body_1["status"] == "CLAIMED"

    reregistration_2 = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-002",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration_2.status_code == 200
    body_2 = reregistration_2.json()
    assert body_2["printer_id"] == printer_id
    assert CLOUD_ID_PATTERN.match(body_2["cloud_id"])
    assert EMAIL_PATTERN.match(body_2["printer_email_id"])
    claim_code_call2 = body_2["claim_code"]
    expires_at_call2 = body_2["claim_code_expires_at"]
    assert claim_code_call2 == claim_code_1
    assert expires_at_call2 == expires_at_1
    assert body_2["xmpp_node"]
    assert body_2["status"] == "CLAIMED"


def test_TC_GOAR_7_03_ownership_preserved_when_reregistering_claimed_printer(client):
    """Re-register a CLAIMED printer and confirm that ownership-related fields remain unchanged when no new claim code is issued."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-003",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    printer_id = initial_body["printer_id"]
    claim_code_1 = initial_body["claim_code"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-c"},
    )
    assert claim_response.status_code == 200
    claim_body = claim_response.json()
    assert claim_body["status"] == "CLAIMED"
    assert claim_body["owner_user_id"] == "user-goar7-c"

    reregistration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-003",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration.status_code == 200
    body = reregistration.json()
    assert body["printer_id"] == printer_id
    assert body["claim_code"] == claim_code_1
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id
    assert lookup_body["serial_number"] == "SN-GOAR7-003"
    assert CLOUD_ID_PATTERN.match(lookup_body["cloud_id"])
    assert EMAIL_PATTERN.match(lookup_body["printer_email_id"])
    assert lookup_body["owner_user_id"] == "user-goar7-c"
    assert lookup_body["status"] == "CLAIMED"
    assert lookup_body["xmpp_node"]


def test_TC_GOAR_7_04_first_time_registration_of_unclaimed_printer_issues_claim_code_and_welcome_page(client):
    """First-time registration of an unclaimed printer generates a claim code and prints a Welcome Page as expected."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-004",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["claim_code_expires_at"]
    assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"
    history = body["history"]
    assert any("Registration started" in entry for entry in history)
    assert any("Cloud identity created" in entry for entry in history)
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history)


def test_TC_GOAR_7_05_reregistration_of_unclaimed_printer_continues_to_issue_claim_code(client):
    """Re-register an unclaimed printer and confirm a claim code is generated and associated with the printer on each successful re-registration."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-005",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    printer_id_1 = first_body["printer_id"]
    claim_code_1 = first_body["claim_code"]
    assert first_body["status"] == "REGISTERED"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-005",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_1
    assert CLOUD_ID_PATTERN.match(second_body["cloud_id"])
    assert EMAIL_PATTERN.match(second_body["printer_email_id"])
    claim_code_2 = second_body["claim_code"]
    assert CLAIM_CODE_PATTERN.match(claim_code_2)
    assert second_body["claim_code_expires_at"]
    assert second_body["xmpp_node"]
    assert second_body["status"] == "REGISTERED"
    assert claim_code_2 != claim_code_1


def test_TC_GOAR_7_06_consecutive_reregistrations_of_unclaimed_printer_generate_distinct_claim_codes(client):
    """Re-register an unclaimed printer twice in succession and confirm each successful call generates a new, distinct claim code."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-006",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    printer_id_1 = first_body["printer_id"]
    claim_code_1 = first_body["claim_code"]
    assert first_body["status"] == "REGISTERED"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-006",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_1
    claim_code_2 = second_body["claim_code"]
    assert second_body["status"] == "REGISTERED"

    third = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-006",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert third.status_code == 200
    third_body = third.json()
    assert third_body["printer_id"] == printer_id_1
    claim_code_3 = third_body["claim_code"]
    assert third_body["status"] == "REGISTERED"

    assert claim_code_1 != claim_code_2
    assert claim_code_2 != claim_code_3
    assert claim_code_1 != claim_code_3


def test_TC_GOAR_7_07_reregister_claimed_printer_does_not_change_claim_code_ttl_or_used_flag(client):
    """Re-register a CLAIMED printer with a currently valid, unused claim code and confirm that the claim code’s expiry remains unchanged after re-registration."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-007",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    printer_id = initial_body["printer_id"]
    claim_code_1 = initial_body["claim_code"]
    expires_at_1 = initial_body["claim_code_expires_at"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-d"},
    )
    assert claim_response.status_code == 200
    claim_body = claim_response.json()
    assert claim_body["status"] == "CLAIMED"
    assert claim_body["owner_user_id"] == "user-goar7-d"

    reregistration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-007",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration.status_code == 200
    body = reregistration.json()
    assert body["claim_code"] == claim_code_1
    assert body["claim_code_expires_at"] == expires_at_1

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "CLAIMED"
    assert lookup_body["owner_user_id"] == "user-goar7-d"


def test_TC_GOAR_7_08_reregister_claimed_printer_close_to_expiry_does_not_extend_ttl(client):
    """Re-register a CLAIMED printer whose claim code is close to expiry and confirm that re-registration does not extend the expiration time."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-008",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    claim_code_1 = initial_body["claim_code"]
    expires_at_1 = initial_body["claim_code_expires_at"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-e"},
    )
    assert claim_response.status_code == 200

    reregistration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-008",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration.status_code == 200
    body = reregistration.json()
    assert body["claim_code"] == claim_code_1
    assert body["claim_code_expires_at"] == expires_at_1


def test_TC_GOAR_7_09_claim_code_remains_single_use_after_claiming_and_reregistering_claimed_printer(client):
    """After successfully claiming a printer and then re-registering it, confirm that the claim code still behaves as single-use and ownership is not weakened."""
    initial_registration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-009",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial_registration.status_code == 200
    initial_body = initial_registration.json()
    printer_id = initial_body["printer_id"]
    claim_code_1 = initial_body["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-f"},
    )
    assert first_claim.status_code == 200
    first_claim_body = first_claim.json()
    assert first_claim_body["status"] == "CLAIMED"
    assert first_claim_body["owner_user_id"] == "user-goar7-f"

    reregistration = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-009",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert reregistration.status_code == 200

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-g"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Claim code has already been used"

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar7-f"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_7_10_failed_registration_for_unclaimed_printer_invalidates_claim_code(client):
    """Trigger a registration failure before Welcome Page printing for an unclaimed printer and confirm that any claim code generated during the failed attempt cannot be used to claim the printer afterwards."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-010",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == "Registration could not be completed. Please check your request and try again."

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-010",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    printer_id = success_body["printer_id"]
    claim_code_success = success_body["claim_code"]

    invalid_claim = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID10", "user_id": "user-goar7-h"},
    )
    assert invalid_claim.status_code == 400
    assert invalid_claim.json()["detail"] == "Claim code not recognized"

    valid_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_success, "user_id": "user-goar7-h"},
    )
    assert valid_claim.status_code == 200
    assert valid_claim.json()["printer_id"] == printer_id


def test_TC_GOAR_7_11_new_claim_code_issued_after_failed_registration(client):
    """After a failed registration that invalidated a claim code, perform a subsequent successful registration and confirm a fresh claim code is generated and is the only usable one."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-011",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-011",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    claim_code_success = success_body["claim_code"]

    claim_response = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_success, "user_id": "user-goar7-i"},
    )
    assert claim_response.status_code == 200
    claim_body = claim_response.json()
    assert claim_body["status"] == "CLAIMED"
    assert claim_body["owner_user_id"] == "user-goar7-i"


def test_TC_GOAR_7_12_rollback_removes_claim_code_when_failure_occurs_before_welcome_page(client):
    """Simulate a failure at the last step before Welcome Page printing and confirm that rollback still removes any claim code generated in that attempt."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-012",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == "Registration could not be completed. Please check your request and try again."

    claim_attempt = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID12", "user_id": "user-goar7-h"},
    )
    assert claim_attempt.status_code == 400
    assert claim_attempt.json()["detail"] == "Claim code not recognized"


def test_TC_GOAR_7_13_multiple_successful_registrations_for_unclaimed_printer_produce_unique_claim_codes(client):
    """Perform two successful registrations for the same unclaimed printer and confirm each Welcome Page print uses a new claim code."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-013",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first.status_code == 200
    body_1 = first.json()
    claim_code_1 = body_1["claim_code"]
    assert body_1["status"] == "REGISTERED"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-013",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    body_2 = second.json()
    claim_code_2 = body_2["claim_code"]
    assert body_2["status"] == "REGISTERED"

    assert CLAIM_CODE_PATTERN.match(claim_code_1)
    assert CLAIM_CODE_PATTERN.match(claim_code_2)
    assert claim_code_1 != claim_code_2
    history_1 = body_1["history"]
    history_2 = body_2["history"]
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history_1)
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history_2)


def test_TC_GOAR_7_14_three_registrations_for_unclaimed_printer_yield_pairwise_distinct_claim_codes(client):
    """Perform a third successful registration for the same unclaimed printer and confirm all three claim codes are distinct."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-014",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first.status_code == 200
    claim_code_1 = first.json()["claim_code"]

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-014",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    claim_code_2 = second.json()["claim_code"]

    third = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-014",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert third.status_code == 200
    claim_code_3 = third.json()["claim_code"]

    assert CLAIM_CODE_PATTERN.match(claim_code_1)
    assert CLAIM_CODE_PATTERN.match(claim_code_2)
    assert CLAIM_CODE_PATTERN.match(claim_code_3)
    assert claim_code_1 != claim_code_2
    assert claim_code_2 != claim_code_3
    assert claim_code_1 != claim_code_3


def test_TC_GOAR_7_15_reusing_old_claim_code_for_unclaimed_printer_is_rejected(client):
    """Attempt to re-use an old claim code from a prior registration for an unclaimed printer and confirm it is rejected as invalid."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-015",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first.status_code == 200
    claim_code_1 = first.json()["claim_code"]

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-015",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    claim_code_2 = second.json()["claim_code"]

    claim_attempt = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-j"},
    )
    assert claim_attempt.status_code == 400
    detail = claim_attempt.json()["detail"]
    assert detail in {"Claim code not recognized", "Claim code has expired"}

    successful_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar7-j"},
    )
    assert successful_claim.status_code == 200


def test_TC_GOAR_7_16_claim_with_rolled_back_claim_code_is_rejected(client):
    """Attempt to claim a printer using a claim code originating from a registration that was rolled back and confirm the claim attempt is rejected."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-016",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422

    claim_attempt = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID16", "user_id": "user-goar7-k"},
    )
    assert claim_attempt.status_code == 400
    assert claim_attempt.json()["detail"] == "Claim code not recognized"


def test_TC_GOAR_7_17_printer_cannot_be_claimed_by_any_rolled_back_claim_code_after_rollback(client):
    """After rollback of a failed registration, confirm the printer cannot be claimed by any claim code that was generated during that failed attempt."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-017",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422

    claim_attempt = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID17", "user_id": "user-goar7-l"},
    )
    assert claim_attempt.status_code == 400
    assert claim_attempt.json()["detail"] == "Claim code not recognized"


def test_TC_GOAR_7_18_rolled_back_claim_code_cannot_be_used_immediately_or_later(client):
    """Attempt to claim with a rolled-back claim code immediately after rollback and again after some time has passed, confirming both attempts are rejected."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-018",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422

    immediate_claim = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID18", "user_id": "user-goar7-m"},
    )
    assert immediate_claim.status_code == 400
    assert immediate_claim.json()["detail"] == "Claim code not recognized"

    delayed_claim = client.post(
        "/printers/claim",
        json={"claim_code": "INVALID18", "user_id": "user-goar7-n"},
    )
    assert delayed_claim.status_code == 400
    assert delayed_claim.json()["detail"] == "Claim code not recognized"


def test_TC_GOAR_7_19_multiple_claim_codes_for_unclaimed_printer_allow_only_first_claim(client):
    """Issue multiple claim codes for the same unclaimed printer via overlapping registration attempts and confirm that only the first successful claim transitions the printer to CLAIMED."""
    first_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-019",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first_reg.status_code == 200
    body_1 = first_reg.json()
    claim_code_1 = body_1["claim_code"]

    second_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-019",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second_reg.status_code == 200
    body_2 = second_reg.json()
    claim_code_2 = body_2["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-o"},
    )
    assert first_claim.status_code == 200
    first_claim_body = first_claim.json()
    assert first_claim_body["status"] == "CLAIMED"
    assert first_claim_body["owner_user_id"] == "user-goar7-o"

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar7-p"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Printer is already claimed"


def test_TC_GOAR_7_20_ownership_unchanged_when_attempting_second_claim_with_different_claim_code(client):
    """After the printer becomes CLAIMED via one claim code, attempt to claim it using another valid-looking claim code and confirm ownership does not change and the second claim is rejected."""
    first_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-020",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first_reg.status_code == 200
    body_1 = first_reg.json()
    printer_id = body_1["printer_id"]
    claim_code_1 = body_1["claim_code"]

    second_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-020",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second_reg.status_code == 200
    body_2 = second_reg.json()
    claim_code_2 = body_2["claim_code"]

    first_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-q"},
    )
    assert first_claim.status_code == 200

    second_claim = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar7-r"},
    )
    assert second_claim.status_code == 400
    assert second_claim.json()["detail"] == "Printer is already claimed"

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar7-q"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_7_21_concurrent_claim_attempts_with_two_claim_codes_yield_at_most_one_successful_claim(client):
    """Attempt to claim the printer simultaneously with two different claim codes and confirm that at most one claim succeeds and subsequent claims are rejected."""
    first_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-021",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert first_reg.status_code == 200
    body_1 = first_reg.json()
    claim_code_1 = body_1["claim_code"]

    second_reg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR7-021",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second_reg.status_code == 200
    body_2 = second_reg.json()
    claim_code_2 = body_2["claim_code"]

    claim_a = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_1, "user_id": "user-goar7-s"},
    )
    claim_b = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_2, "user_id": "user-goar7-t"},
    )

    statuses = {claim_a.status_code, claim_b.status_code}
    assert statuses == {200, 400}

    successful = claim_a if claim_a.status_code == 200 else claim_b
    failed = claim_b if claim_a.status_code == 200 else claim_a

    assert successful.json()["status"] == "CLAIMED"
    assert failed.json()["detail"] == "Printer is already claimed"
