"""
Generated tests for GOAR-3: re-registration must always generate a new
Cloud ID (per business rule 3/6), while Printer Email ID and Claim Code
regeneration, claimed-printer status/ownership, and deregister-then-
re-register behavior remain correct.

Automates the test cases in reports/testcases/GOAR-3_test_cases.md at
the HTTP API level, using the `client` TestClient fixture from
tests/conftest.py.
"""
import re

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_3_01_reregistration_generates_new_cloud_id(client):
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1001",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    assert CLOUD_ID_PATTERN.match(first_body["cloud_id"])
    assert first_body["status"] == "REGISTERED"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1001",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert CLOUD_ID_PATTERN.match(second_body["cloud_id"])
    assert second_body["status"] == "REGISTERED"

    assert second_body["cloud_id"] != first_body["cloud_id"]


def test_TC_GOAR_3_02_reregistration_regenerates_email_and_claim_code(client):
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1002",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert first.status_code == 200
    first_body = first.json()

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1002",
            "model_number": "HP-M404",
            "firmware_version": "1.0.1",
        },
    )
    assert second.status_code == 200
    second_body = second.json()

    assert EMAIL_PATTERN.match(second_body["printer_email_id"])
    assert second_body["printer_email_id"] != first_body["printer_email_id"]

    assert CLAIM_CODE_PATTERN.match(second_body["claim_code"])
    assert second_body["claim_code"] != first_body["claim_code"]


def test_TC_GOAR_3_03_reregistration_of_claimed_printer_gets_new_cloud_id_keeps_claimed_status(client):
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    cloud_id_1 = registered_body["cloud_id"]

    claimed = client.post(
        "/printers/claim",
        json={"claim_code": registered_body["claim_code"], "user_id": "user-alpha"},
    )
    assert claimed.status_code == 200
    assert claimed.json()["status"] == "CLAIMED"

    reregistered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert reregistered.status_code == 200
    reregistered_body = reregistered.json()

    assert reregistered_body["cloud_id"] != cloud_id_1
    assert reregistered_body["status"] == "CLAIMED"


def test_TC_GOAR_3_04_reregistration_of_claimed_printer_preserves_owner(client):
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1004b",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id = registered_body["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={"claim_code": registered_body["claim_code"], "user_id": "user-beta"},
    )
    assert claimed.status_code == 200
    assert claimed.json()["owner_user_id"] == "user-beta"

    reregistered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1004b",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert reregistered.status_code == 200

    lookup = client.get(f"/printers/{printer_id}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-beta"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_3_05_three_consecutive_registrations_produce_three_distinct_cloud_ids(client):
    cloud_ids = []
    for _ in range(3):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-1005",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
            },
        )
        assert response.status_code == 200
        cloud_ids.append(response.json()["cloud_id"])

    cloud_id_1, cloud_id_2, cloud_id_3 = cloud_ids
    assert cloud_id_1 != cloud_id_2
    assert cloud_id_2 != cloud_id_3
    assert cloud_id_1 != cloud_id_3


def test_TC_GOAR_3_06_second_reregistration_cloud_id_differs_from_very_first(client):
    cloud_ids = []
    for _ in range(3):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-1006",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
            },
        )
        assert response.status_code == 200
        cloud_ids.append(response.json()["cloud_id"])

    cloud_id_1 = cloud_ids[0]
    cloud_id_3 = cloud_ids[2]
    assert cloud_id_3 != cloud_id_1


def test_TC_GOAR_3_07_recovery_after_failed_reregistration_gets_fresh_cloud_id(client):
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1007",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert initial.status_code == 200
    cloud_id_1 = initial.json()["cloud_id"]

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1007",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422

    recovery = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1007",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert recovery.status_code == 200
    recovery_body = recovery.json()
    assert CLOUD_ID_PATTERN.match(recovery_body["cloud_id"])
    assert recovery_body["cloud_id"] != cloud_id_1


def test_TC_GOAR_3_08_failed_reregistration_rolls_back_printer_record(client):
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1008",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert registered.status_code == 200
    printer_id_1 = registered.json()["printer_id"]

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1008",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == f"Welcome page failed to print for printer_id={printer_id_1}"

    lookup = client.get(f"/printers/{printer_id_1}")
    assert lookup.status_code == 404
    assert lookup.json()["detail"] == "Printer not found"


def test_TC_GOAR_3_09_reregistration_after_deregistration_generates_new_cloud_id(client):
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1009",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert first.status_code == 200
    first_body = first.json()
    printer_id_1 = first_body["printer_id"]
    cloud_id_1 = first_body["cloud_id"]

    deregistered = client.delete(f"/printers/{printer_id_1}")
    assert deregistered.status_code == 200
    assert deregistered.json() == {"status": "DEREGISTERED", "printer_id": printer_id_1}

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-1009",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert CLOUD_ID_PATTERN.match(second_body["cloud_id"])
    assert second_body["cloud_id"] != cloud_id_1
