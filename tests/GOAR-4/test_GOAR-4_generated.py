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


def test_TC_GOAR_4_01_rollback_removes_printer_record_when_welcome_page_fails(client):
    """[ROLLBACK] Simulated Welcome Page failure triggers rollback that removes the printer record created during the attempted registration."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-001",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-001"


def test_TC_GOAR_4_02_multiple_failed_registrations_leave_no_printer_record(client):
    """[BOUNDARY]  Multiple consecutive failed registrations for the same serial number all roll back without leaving any printer record in the store."""
    first = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-002",
            "model_number": "HP-M404",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert first.status_code == 422
    assert first.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-002"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-002",
            "model_number": "HP-M404",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert second.status_code == 422
    assert second.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-002"


def test_TC_GOAR_4_03_failed_registration_frees_serial_for_subsequent_first_time_registration(client):
    """[ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-003"

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-003",
            "model_number": "HP-M404",
            "firmware_version": "1.0.2",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    body = success.json()
    printer_id_2 = body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id_2}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id_2
    assert lookup_body["serial_number"] == "SN-GOAR4-003"
    assert lookup_body["status"] == "REGISTERED"


def test_TC_GOAR_4_04_multiple_cycles_of_failure_then_success_keep_serial_reusable(client):
    """[BOUNDARY]   Multiple cycles of failed registration followed by successful registration verify the serial number is always reusable with no stale associations."""
    first_failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-004",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": True,
        },
    )
    assert first_failed.status_code == 422
    assert first_failed.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-004"

    second_failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-004",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": True,
        },
    )
    assert second_failed.status_code == 422
    assert second_failed.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-004"

    third_success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-004",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": False,
        },
    )
    assert third_success.status_code == 200
    body_3 = third_success.json()
    printer_id_3 = body_3["printer_id"]
    assert CLOUD_ID_PATTERN.match(body_3["cloud_id"])
    assert body_3["status"] == "REGISTERED"

    fourth_success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-004",
            "model_number": "HP-M404",
            "firmware_version": "1.0.3",
            "simulate_welcome_page_failure": False,
        },
    )
    assert fourth_success.status_code == 200
    body_4 = fourth_success.json()
    printer_id_4 = body_4["printer_id"]
    assert CLOUD_ID_PATTERN.match(body_4["cloud_id"])
    assert body_4["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id_4}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id_4
    assert lookup_body["serial_number"] == "SN-GOAR4-004"
    assert lookup_body["status"] == "REGISTERED"


def test_TC_GOAR_4_05_successful_registration_persists_printer_and_serial_index(client):
    """[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer and serial index records without invoking rollback."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-005",
            "model_number": "HP-M404",
            "firmware_version": "1.1.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    body = registered.json()
    printer_id_5 = body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id_5}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id_5
    assert lookup_body["serial_number"] == "SN-GOAR4-005"
    assert lookup_body["status"] == "REGISTERED"


def test_TC_GOAR_4_06_successful_registration_after_failure_behaves_like_standard_success(client):
    """[BOUNDARY]   Successful registration immediately after a failed attempt still behaves as a standard success path and does not invoke rollback."""
    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-M404",
            "firmware_version": "1.1.1",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == "Welcome page failed to print for printer_id=SN-GOAR4-006"

    success = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR4-006",
            "model_number": "HP-M404",
            "firmware_version": "1.1.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert success.status_code == 200
    body = success.json()
    printer_id_6 = body["printer_id"]
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["status"] == "REGISTERED"

    lookup = client.get(f"/printers/{printer_id_6}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["printer_id"] == printer_id_6
    assert lookup_body["serial_number"] == "SN-GOAR4-006"
    assert lookup_body["status"] == "REGISTERED"
