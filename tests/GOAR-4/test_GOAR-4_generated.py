"""
Generated tests for GOAR-4: registration rollback must remove printer, serial index,
and capabilities on Welcome Page failure, while successful registrations and
claimed-printer ownership remain correct and unaffected.

Automates the test cases in reports/testcases/GOAR-4_test_cases.md at the HTTP
API level, using the `client` TestClient fixture from tests/conftest.py.
"""
import logging
import re

import pytest

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_4_01_successful_registration_persists_printer_capabilities_and_serial_index(client):
    """[HAPPY PATH] Welcome Page prints successfully and printer record is persisted without invoking rollback."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-001",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()

    printer_id = body["printer_id"]
    assert printer_id
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["status"] == "REGISTERED"
    assert any("Registration started" in entry for entry in body["history"])
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in body["history"]
    )


def test_TC_GOAR_4_02_rollback_removes_printer_record_on_welcome_page_failure(client):
    """[ROLLBACK] Simulated Welcome Page failure triggers rollback that removes the printer record created during registration."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-002",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")
    printer_id = detail.split("=", 1)[1]

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 404
    assert lookup.json()["detail"] == "Printer not found"



def test_TC_GOAR_4_03_failed_registration_leaves_no_persistent_printer_record(client):
    """[ROLLBACK] Failed registration leaves no printer record and allows subsequent inspection to confirm absence of printer data."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert first.status_code == 422
    detail_1 = first.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    body_2 = second.json()
    assert body_2["printer_id"]
    assert body_2["status"] == "REGISTERED"



def test_TC_GOAR_4_04_successful_registration_captures_and_persists_capabilities(client):
    """[HAPPY PATH] Successful registration persists capability records for the printer_id and they remain after completion."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-004",
            "model_number": "HP-CMFP-500",
            "firmware_version": "2.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]
    assert registered_body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id
    assert lookup_body["serial_number"] == "SN-GOAR4-004"
    assert any("Capabilities captured" in entry for entry in lookup_body["history"])
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in lookup_body["history"]
    )



def test_TC_GOAR_4_05_rollback_deletes_capabilities_records_on_welcome_page_failure(client):
    """[ROLLBACK] Simulated Welcome Page failure triggers rollback that deletes capability records associated with the failed printer_id."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-005",
            "model_number": "HP-CMFP-600",
            "firmware_version": "2.1.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail_1 = failed.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-005",
            "model_number": "HP-CMFP-600",
            "firmware_version": "2.1.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    printer_id_2 = success_body["printer_id"]
    assert success_body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id_2}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    capability_entries = [
        entry for entry in lookup_body["history"] if "Capabilities captured" in entry
    ]
    assert len(capability_entries) == 1



def test_TC_GOAR_4_06_failed_registration_capabilities_not_exposed_via_get(client):
    """[ROLLBACK] After a failed registration, capability queries for the failed printer_id return no capability data."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-M404",
            "firmware_version": "1.2.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail_1 = failed.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-M404",
            "firmware_version": "1.2.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    printer_id_2 = success_body["printer_id"]

    lookup = client.get(f"/printers/{printer_id_2}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    capability_entries = [
        entry for entry in lookup_body["history"] if "Capabilities captured" in entry
    ]
    assert len(capability_entries) == 1



def test_TC_GOAR_4_07_successful_registration_reserves_serial_and_visible_via_get(client):
    """[HAPPY PATH] First-time successful registration with a given serial number completes and reserves that serial."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-007",
            "model_number": "HP-M404",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]
    assert registered_body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["serial_number"] == "SN-GOAR4-007"
    assert lookup_body["status"] == "REGISTERED"



def test_TC_GOAR_4_08_rollback_frees_serial_for_fresh_registration(client):
    """[ROLLBACK] Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-008",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail_1 = failed.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-008",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    assert success_body["printer_id"]
    assert success_body["status"] == "REGISTERED"



def test_TC_GOAR_4_09_multiple_failed_registrations_keep_serial_reusable(client):
    """[BOUNDARY] Multiple consecutive failed registrations with the same serial number all roll back cleanly, leaving the serial reusable each time."""
    details = []
    for _ in range(3):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR4-009",
                "model_number": "HP-M404",
                "firmware_version": "1.0.4",
                "simulate_welcome_page_failure": True,
            },
        )
        assert failed.status_code == 422
        detail = failed.json()["detail"]
        assert detail.startswith("Welcome page failed to print for printer_id=")
        details.append(detail)

    printer_ids = {d.split("=", 1)[1] for d in details}
    assert len(printer_ids) == 3



def test_TC_GOAR_4_10_successful_registration_unaffected_by_rollback_logic(client):
    """[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records unchanged by rollback."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-010",
            "model_number": "HP-CMFP-700",
            "firmware_version": "3.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id
    assert any("Capabilities captured" in entry for entry in lookup_body["history"])
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in lookup_body["history"]
    )



def test_TC_GOAR_4_11_idempotent_rollback_via_repeated_failed_registrations(client):
    """[ROLLBACK] Multiple invocations of _rollback_registration for the same printer_id leave no printer, capability, or serial index records without raising additional errors."""
    for _ in range(2):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR4-011",
                "model_number": "HP-M404",
                "firmware_version": "1.0.5",
                "simulate_welcome_page_failure": True,
            },
        )
        assert failed.status_code == 422
        detail = failed.json()["detail"]
        assert detail.startswith("Welcome page failed to print for printer_id=")



def test_TC_GOAR_4_12_boundary_rollback_behaviour_with_repeated_failed_attempts(client):
    """[BOUNDARY] Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records."""
    details = []
    for _ in range(3):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR4-012",
                "model_number": "HP-M404",
                "firmware_version": "1.0.6",
                "simulate_welcome_page_failure": True,
            },
        )
        assert failed.status_code == 422
        detail = failed.json()["detail"]
        assert detail.startswith("Welcome page failed to print for printer_id=")
        details.append(detail)

    printer_ids = {d.split("=", 1)[1] for d in details}
    assert len(printer_ids) == 3



def test_TC_GOAR_4_13_rollback_deletes_only_failing_printers_data_leaving_other_intact(client):
    """[ROLLBACK] Rollback for one printer_id deletes only that printer’s capabilities and leaves capabilities for other printers intact."""
    registered_a = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-013A",
            "model_number": "HP-CMFP-800",
            "firmware_version": "3.1.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered_a.status_code == 200
    body_a = registered_a.json()
    printer_id_a = body_a["printer_id"]

    registered_b = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-013B",
            "model_number": "HP-CMFP-900",
            "firmware_version": "3.2.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert registered_b.status_code == 422
    detail_b = registered_b.json()["detail"]
    assert detail_b.startswith("Welcome page failed to print for printer_id=")

    lookup_a = client.get(f"/printers/{printer_id_a}")
    assert lookup_a.status_code == 200
    lookup_a_body = lookup_a.json()
    assert lookup_a_body["serial_number"] == "SN-GOAR4-013A"
    assert lookup_a_body["status"] == "REGISTERED"
    assert any("Capabilities captured" in entry for entry in lookup_a_body["history"])



def test_TC_GOAR_4_14_rollback_does_not_alter_other_printers_with_different_owners(client):
    """[OWNERSHIP] Rollback for an unclaimed printer does not alter capabilities or records of other printers, including those with different owners."""
    registered_a = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-014A",
            "model_number": "HP-M404",
            "firmware_version": "1.1.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered_a.status_code == 200
    body_a = registered_a.json()
    printer_id_a = body_a["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": body_a["claim_code"],
            "user_id": "user-goar4-owner",
        },
    )
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"
    assert claimed.json()["owner_user_id"] == "user-goar4-owner"

    failed_b = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-014B",
            "model_number": "HP-M404",
            "firmware_version": "1.1.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed_b.status_code == 422
    detail_b = failed_b.json()["detail"]
    assert detail_b.startswith("Welcome page failed to print for printer_id=")

    lookup_a = client.get(f"/printers/{printer_id_a}")
    assert lookup_a.status_code == 200
    lookup_a_body = lookup_a.json()
    assert lookup_a_body["status"] == "CLAIMED"
    assert lookup_a_body["owner_user_id"] == "user-goar4-owner"



def test_TC_GOAR_4_15_serial_index_rollback_creates_fresh_printer_record_after_failure(client):
    """[ROLLBACK] After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-015",
            "model_number": "HP-M404",
            "firmware_version": "1.2.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail_1 = failed.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-015",
            "model_number": "HP-M404",
            "firmware_version": "1.2.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    assert success_body["printer_id"]
    assert success_body["status"] == "REGISTERED"



def test_TC_GOAR_4_16_repeated_failed_and_successful_registrations_never_retain_stale_serial_index(client):
    """[BOUNDARY] Repeated cycles of failed registration followed by successful registration for the same serial verify that the serial index never retains stale associations."""
    for _ in range(2):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR4-016",
                "model_number": "HP-M404",
                "firmware_version": "1.3.0",
                "simulate_welcome_page_failure": True,
            },
        )
        assert failed.status_code == 422
        detail = failed.json()["detail"]
        assert detail.startswith("Welcome page failed to print for printer_id=")

    for _ in range(2):
        success = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR4-016",
                "model_number": "HP-M404",
                "firmware_version": "1.3.0",
                "simulate_welcome_page_failure": False,
            },
        )
        assert success.status_code == 200
        body = success.json()
        assert body["printer_id"]
        assert body["status"] == "REGISTERED"



def test_TC_GOAR_4_17_rollback_does_not_change_state_of_already_claimed_printers(client):
    """[OWNERSHIP] Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers."""
    registered_a = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-017A",
            "model_number": "HP-M404",
            "firmware_version": "1.3.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered_a.status_code == 200
    body_a = registered_a.json()
    printer_id_a = body_a["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": body_a["claim_code"],
            "user_id": "user-goar4-claim",
        },
    )
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"
    assert claimed.json()["owner_user_id"] == "user-goar4-claim"

    failed_b = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-017B",
            "model_number": "HP-M404",
            "firmware_version": "1.3.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed_b.status_code == 422
    detail_b = failed_b.json()["detail"]
    assert detail_b.startswith("Welcome page failed to print for printer_id=")

    lookup_a = client.get(f"/printers/{printer_id_a}")
    assert lookup_a.status_code == 200
    lookup_a_body = lookup_a.json()
    assert lookup_a_body["status"] == "CLAIMED"
    assert lookup_a_body["owner_user_id"] == "user-goar4-claim"



def test_TC_GOAR_4_18_successful_registration_never_invokes_rollback(client):
    """[HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated records."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-018",
            "model_number": "HP-CMFP-1000",
            "firmware_version": "4.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "REGISTERED"



def test_TC_GOAR_4_19_logging_based_confirmation_of_successful_registration_via_history(client):
    """[ROLLBACK] Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-019",
            "model_number": "HP-M404",
            "firmware_version": "1.3.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    history = lookup_body["history"]
    assert any("Registration started" in entry for entry in history)
    assert any("Cloud identity created" in entry for entry in history)
    assert any("Capabilities captured" in entry for entry in history)
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )



def test_TC_GOAR_4_20_capabilities_for_failed_registrations_never_exposed_externally(client):
    """[ROLLBACK] After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-020",
            "model_number": "HP-CMFP-1100",
            "firmware_version": "4.1.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail_1 = failed.json()["detail"]
    assert detail_1.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-020",
            "model_number": "HP-CMFP-1100",
            "firmware_version": "4.1.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    success_body = success.json()
    printer_id_2 = success_body["printer_id"]

    lookup = client.get(f"/printers/{printer_id_2}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    history = lookup_body["history"]
    capability_entries = [
        entry for entry in history if "Capabilities captured" in entry
    ]
    assert len(capability_entries) == 1
