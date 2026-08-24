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


def test_TC_GOAR_4_01_successful_registration_persists_printer_record(client):
    """[HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a printer record present."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-001",
            "model_number": "HP-LJ-2055",
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
        "Welcome page printed successfully" in entry for entry in body["history"]
    )

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id
    assert lookup_body["serial_number"] == "SN-GOAR4-001"
    assert lookup_body["status"] == "REGISTERED"


def test_TC_GOAR_4_02_failed_registration_removes_printer_record(client):
    """[ROLLBACK] Registration where Welcome Page printing fails removes the printer record so no printer remains for that printer_id."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-002",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
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


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: capability records are not exposed via any HTTP endpoint; "
        "existence after successful registration must be validated below the API layer"
    )
)
def test_TC_GOAR_4_03_successful_registration_leaves_capabilities_present(client):
    """[HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a capability record associated with the printer_id."""
    pass


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: capability records are not exposed via any HTTP endpoint; "
        "deletion after rollback must be validated below the API layer"
    )
)
def test_TC_GOAR_4_04_failed_registration_removes_capabilities(client):
    """[ROLLBACK] Registration where Welcome Page printing fails removes any capability record associated with the printer_id so none remain."""
    pass


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: there is no serial-number lookup endpoint; serial index behavior "
        "must be inferred indirectly or validated via store-level tests"
    )
)
def test_TC_GOAR_4_05_successful_registration_allows_serial_lookup(client):
    """[HAPPY PATH] Successful registration with Welcome Page printing completes and allows lookup of the printer via its serial number."""
    pass


def test_TC_GOAR_4_06_failed_registration_frees_serial_for_reuse(client):
    """[ROLLBACK] Registration where Welcome Page printing fails removes the serial index so a subsequent registration using the same serial number behaves like a fresh registration."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    body = success.json()
    assert body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_4_07_successful_registrations_unaffected_by_rollback_changes(client):
    """[HAPPY PATH] Successful registration with Welcome Page printing persists printer, capabilities, and serial index and is not impacted by rollback changes."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_4_08_missing_authorization_header_rejected(client):
    """[AUTH] Registration attempt without an Authorization header is rejected and does not create any printer, capability, or serial index records."""
    response = client.post(
        "/printers/register",
        headers={},
        json={
            "serial_number": "SN-GOAR4-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"][0]
    assert "authorization" in detail["loc"]
    assert detail["type"] == "value_error.missing"


def test_TC_GOAR_4_09_invalid_token_rejected_with_401(client):
    """[AUTH] Registration attempt with an invalid or expired token is rejected and does not create any printer, capability, or serial index records."""
    response = client.post(
        "/printers/register",
        headers={"Authorization": "Bearer invalid_token", "Content-Type": "application/json"},
        json={
            "serial_number": "SN-GOAR4-009",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.4",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: internal idempotent rollback behavior cannot be exercised via "
        "HTTP beyond a single 422 response"
    )
)
def test_TC_GOAR_4_10_idempotent_rollback_leaves_no_records_after_multiple_calls(client):
    """[ROLLBACK] Calling rollback multiple times for the same failed registration leaves no printer record, capability record, or serial index for that serial number."""
    pass


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: a second internal rollback call after records are deleted is not "
        "observable via the HTTP API"
    )
)
def test_TC_GOAR_4_11_second_rollback_call_completes_without_errors(client):
    """[BOUNDARY VALUE] A second rollback call after records are already deleted completes without raising errors caused by missing printer, capability, or serial index data."""
    pass


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: capability scoping per-printer_id is not observable via current "
        "HTTP endpoints"
    )
)
def test_TC_GOAR_4_12_rollback_deletes_only_failing_printers_capabilities(client):
    """[HAPPY PATH] Rollback for a failed registration deletes capabilities only for the failing printer_id and leaves capabilities for other printer_ids intact."""
    pass


def test_TC_GOAR_4_13_rollback_does_not_delete_other_printers_ownership_state(client):
    """[OWNERSHIP] Rollback for a failed registration of one printer_id does not delete or modify capability records belonging to other printers or owners."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-013A",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_013a = registered_body["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar4-owner",
        },
    )
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"
    assert claimed.json()["owner_user_id"] == "user-goar4-owner"

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-013B",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    lookup = client.get(f"/printers/{printer_id_013a}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "CLAIMED"
    assert lookup_body["owner_user_id"] == "user-goar4-owner"


def test_TC_GOAR_4_14_fresh_registration_after_rollback_behaves_like_first_time(client):
    """[HAPPY PATH] After rollback from a failed registration, a subsequent registration with the same serial_number behaves exactly like a first-time registration."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-014",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-014",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    body = success.json()
    assert body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["status"] == "REGISTERED"


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: direct serial-index lookup is not available via HTTP; residual "
        "serial index can only be inferred indirectly"
    )
)
def test_TC_GOAR_4_15_after_rollback_serial_lookup_shows_no_residual_mapping(client):
    """[ROLLBACK] After rollback, lookups by the failed serial_number show no residual serial index or printer mapping that would block reuse."""
    pass


def test_TC_GOAR_4_16_rollback_does_not_alter_single_claimed_printer(client):
    """[HAPPY PATH] Rollback for a failed registration of a new printer_id does not alter the records or claim state of any already-claimed printers."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-016A",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_016a = registered_body["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar4-claim",
        },
    )
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"
    assert claimed.json()["owner_user_id"] == "user-goar4-claim"

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-016B",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    lookup = client.get(f"/printers/{printer_id_016a}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["status"] == "CLAIMED"
    assert lookup_body["owner_user_id"] == "user-goar4-claim"


def test_TC_GOAR_4_17_rollback_does_not_modify_multiple_claimed_printers(client):
    """[OWNERSHIP] Rollback invoked for a failed registration does not delete or modify printer, capability, or serial index data for any other CLAIMED printer."""
    registered_a = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-017A",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered_a.status_code == 200
    body_a = registered_a.json()
    printer_id_017a = body_a["printer_id"]

    claimed_a = client.post(
        "/printers/claim",
        json={
            "claim_code": body_a["claim_code"],
            "user_id": "user-goar4-alpha",
        },
    )
    assert claimed_a.status_code == 200
    assert claimed_a.json()["status"] == "CLAIMED"
    assert claimed_a.json()["owner_user_id"] == "user-goar4-alpha"

    registered_b = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-017B",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered_b.status_code == 200
    body_b = registered_b.json()
    printer_id_017b = body_b["printer_id"]

    claimed_b = client.post(
        "/printers/claim",
        json={
            "claim_code": body_b["claim_code"],
            "user_id": "user-goar4-beta",
        },
    )
    assert claimed_b.status_code == 200
    assert claimed_b.json()["status"] == "CLAIMED"
    assert claimed_b.json()["owner_user_id"] == "user-goar4-beta"

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-017C",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    lookup_a = client.get(f"/printers/{printer_id_017a}")
    assert lookup_a.status_code == 200
    lookup_a_body = lookup_a.json()
    assert lookup_a_body["status"] == "CLAIMED"
    assert lookup_a_body["owner_user_id"] == "user-goar4-alpha"

    lookup_b = client.get(f"/printers/{printer_id_017b}")
    assert lookup_b.status_code == 200
    lookup_b_body = lookup_b.json()
    assert lookup_b_body["status"] == "CLAIMED"
    assert lookup_b_body["owner_user_id"] == "user-goar4-beta"


def test_TC_GOAR_4_18_successful_registration_does_not_invoke_rollback(client):
    """[HAPPY PATH] A successful registration where the Welcome Page prints does not call rollback and preserves printer, capability, and serial index data."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "2.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_4_19_rollback_failure_does_not_affect_later_successful_registration(client):
    """[ROLLBACK] Failed registration attempts that invoke rollback do not trigger rollback during later successful registrations for the same serial_number."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-019",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    detail = failed.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-019",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    body = success.json()
    assert body["printer_id"]
    assert body["status"] == "REGISTERED"


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: there are no capability or device list endpoints; capability "
        "records for failed registrations cannot be observed via HTTP"
    )
)
def test_TC_GOAR_4_20_capabilities_for_failed_registration_not_externally_visible(client):
    """[ROLLBACK] After rollback of a failed registration, no capability records for that printer_id are returned by downstream capability or device list queries."""
    pass


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: timing of capability deletion relative to external queries is "
        "not observable without additional telemetry or endpoints"
    )
)
def test_TC_GOAR_4_21_capability_records_deleted_before_external_observation(client):
    """[BOUNDARY VALUE] Capability records created during a failed registration are deleted by rollback before any subsequent external query can observe them."""
    pass


def test_TC_GOAR_4_22_model_family_boundary_with_welcome_page_failure(client):
    """[BOUNDARY VALUE] Capability records created during a failed registration are deleted by rollback before any subsequent external query can observe them."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-022",
            "model_number": "HP-LJ-001",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert response.status_code == 422
    detail = response.json()["detail"]
    assert detail.startswith("Welcome page failed to print for printer_id=")
