"""
Generated tests for GOAR-16: registration and deregistration must return sanitized, non-leaking error messages while detailed RegistrationError information is logged server-side.

Automates the test cases in reports/testcases/GOAR-16_test_cases.md at the HTTP API level, using the `client` TestClient fixture from tests/conftest.py.
"""
import logging
import re

import pytest

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_16_01_registration_error_returns_sanitized_message_on_registration_error(client):
    """[HAPPY PATH] Registration endpoint returns a generic, non-specific error message when a RegistrationError is raised, with no internal implementation details exposed."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-001",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]


def test_TC_GOAR_16_02_deregistration_error_returns_sanitized_message_on_registration_error(client):
    """[HAPPY PATH] Deregistration endpoint returns a generic, non-specific error message when a RegistrationError is raised, with no internal implementation details exposed."""
    response = client.delete(
        "/printers/non-existent-id-GOAR16-002",
    )

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Printer not found."
    assert "deregister_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]


def test_TC_GOAR_16_03_registration_error_message_excludes_internal_identifiers(client):
    """[INVALID INPUT] Registration error response is verified to avoid including internal function names, module names, stack trace fragments, or configuration values in the returned message."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "",
            "model_number": "",
            "firmware_version": "",
            "simulate_welcome_page_failure": False,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]


def test_TC_GOAR_16_04_deregistration_error_message_excludes_internal_identifiers(client):
    """[INVALID INPUT] Deregistration error response is verified to avoid including internal function names, module names, stack trace fragments, or configuration values in the returned message."""
    response = client.delete(
        "/printers/non-existent-id-GOAR16-004",
    )

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Printer not found."
    assert "deregister_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]


def test_TC_GOAR_16_05_registration_logs_detailed_exception_while_returning_sanitized_error(client, caplog):
    """[HAPPY PATH] When a RegistrationError occurs during registration, a server-side log entry is generated that contains the detailed exception text while the client sees only the sanitized message."""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR16-005",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
                "simulate_welcome_page_failure": True,
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."

    error_logs = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR
        and "Registration failed for serial_number=SN-GOAR16-005" in record.getMessage()
        and "Welcome page failed to print" in record.getMessage()
    ]
    assert len(error_logs) >= 1


def test_TC_GOAR_16_06_deregistration_logs_detailed_exception_while_returning_sanitized_error(client, caplog):
    """[HAPPY PATH] When a RegistrationError occurs during deregistration, a server-side log entry is generated that contains the detailed exception text while the client sees only the sanitized message."""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = client.delete("/printers/non-existent-id-GOAR16-006")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Printer not found."

    error_logs = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR
        and "Deregistration failed for printer_id=non-existent-id-GOAR16-006" in record.getMessage()
        and "No printer found with id" in record.getMessage()
    ]
    assert len(error_logs) >= 1


def test_TC_GOAR_16_07_multiple_registration_errors_still_log_detailed_exceptions_with_consistent_response(client, caplog):
    """[ROLLBACK]   Multiple sequential RegistrationError occurrences on registration produce corresponding detailed log entries without altering the external API error message format."""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        first = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR16-007",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
                "simulate_welcome_page_failure": True,
            },
        )
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR16-007",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
                "simulate_welcome_page_failure": True,
            },
        )

    assert first.status_code == 422
    assert second.status_code == 422

    first_body = first.json()
    second_body = second.json()
    assert first_body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert second_body["detail"] == "Registration could not be completed. Please check your request and try again."

    error_logs = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR
        and "Registration failed for serial_number=SN-GOAR16-007" in record.getMessage()
    ]
    assert len(error_logs) >= 2


def test_TC_GOAR_16_08_multiple_deregistration_errors_still_log_detailed_exceptions_with_consistent_response(client, caplog):
    """[ROLLBACK]   Multiple sequential RegistrationError occurrences on deregistration produce corresponding detailed log entries without altering the external API error message format."""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        first = client.delete("/printers/non-existent-id-GOAR16-008")
        second = client.delete("/printers/non-existent-id-GOAR16-008")

    assert first.status_code == 404
    assert second.status_code == 404

    first_body = first.json()
    second_body = second.json()
    assert first_body["detail"] == "Printer not found."
    assert second_body["detail"] == "Printer not found."

    error_logs = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR
        and "Deregistration failed for printer_id=non-existent-id-GOAR16-008" in record.getMessage()
    ]
    assert len(error_logs) >= 2


def test_TC_GOAR_16_09_registration_errors_still_return_http_422_after_sanitization(client):
    """[HAPPY PATH] Registration failures that raise RegistrationError continue to return HTTP 422 responses after sanitization changes are applied."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-009",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."


def test_TC_GOAR_16_10_deregistration_errors_still_return_http_404_after_sanitization(client):
    """[HAPPY PATH] Deregistration failures that raise RegistrationError continue to return HTTP 404 responses after sanitization changes are applied."""
    response = client.delete("/printers/non-existent-id-GOAR16-010")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Printer not found."


def test_TC_GOAR_16_11_different_registration_error_causes_still_mapped_to_http_422(client):
    """[BOUNDARY VALUE] Registration error handling is validated across different RegistrationError causes to confirm all still map to HTTP 422 responses."""
    response_missing_fields = client.post(
        "/printers/register",
        json={
            "serial_number": "",
            "model_number": "",
            "firmware_version": "",
            "simulate_welcome_page_failure": False,
        },
    )

    assert response_missing_fields.status_code == 422
    body_missing_fields = response_missing_fields.json()
    assert body_missing_fields["detail"] == "Registration could not be completed. Please check your request and try again."

    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-011",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200

    mismatch = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-011",
            "model_number": "HP-COLOR-1000",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )

    assert mismatch.status_code == 422
    mismatch_body = mismatch.json()
    assert mismatch_body["detail"] == "Registration could not be completed. Please check your request and try again."


def test_TC_GOAR_16_12_different_deregistration_error_causes_still_mapped_to_http_404(client):
    """[BOUNDARY VALUE] Deregistration error handling is validated across different RegistrationError causes to confirm all still map to HTTP 404 responses."""
    missing = client.delete("/printers/non-existent-id-GOAR16-012-A")
    assert missing.status_code == 404
    missing_body = missing.json()
    assert missing_body["detail"] == "Printer not found."

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-012",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    printer_id = registered.json()["printer_id"]

    first_delete = client.delete(f"/printers/{printer_id}")
    assert first_delete.status_code == 200

    second_delete = client.delete(f"/printers/{printer_id}")
    assert second_delete.status_code == 404
    second_body = second_delete.json()
    assert second_body["detail"] == "Printer not found."


def test_TC_GOAR_16_13_all_registration_registration_error_paths_return_consistent_sanitized_message(client):
    """[HAPPY PATH] Any RegistrationError path within POST /printers/register is verified to return the same generic sanitized error message pattern without leaking internal identifiers."""
    response_missing_fields = client.post(
        "/printers/register",
        json={
            "serial_number": "",
            "model_number": "",
            "firmware_version": "",
            "simulate_welcome_page_failure": False,
        },
    )

    assert response_missing_fields.status_code == 422
    body_missing_fields = response_missing_fields.json()
    assert body_missing_fields["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in body_missing_fields["detail"]
    assert "app.registration" not in body_missing_fields["detail"]
    assert "Traceback" not in body_missing_fields["detail"]

    response_welcome_failure = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-013",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )

    assert response_welcome_failure.status_code == 422
    body_welcome_failure = response_welcome_failure.json()
    assert body_welcome_failure["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in body_welcome_failure["detail"]
    assert "app.registration" not in body_welcome_failure["detail"]
    assert "Traceback" not in body_welcome_failure["detail"]


def test_TC_GOAR_16_14_newly_introduced_registration_error_branches_still_produce_sanitized_messages(client):
    """[BOUNDARY VALUE] Newly introduced or less common RegistrationError branches in registration are exercised to confirm they still produce sanitized, non-leaking error messages."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-014",
            "model_number": "HP-LJ-4200",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200

    mismatch = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-014",
            "model_number": "HP-COLOR-1000",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )

    assert mismatch.status_code == 422
    mismatch_body = mismatch.json()
    assert mismatch_body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in mismatch_body["detail"]
    assert "app.registration" not in mismatch_body["detail"]
    assert "Traceback" not in mismatch_body["detail"]


def test_TC_GOAR_16_15_registration_rollback_paths_expose_only_sanitized_messages(client, caplog):
    """[ROLLBACK]   A failed registration via any RegistrationError path leaves only sanitized error details visible externally while all detailed context remains confined to server logs."""
    with caplog.at_level(logging.ERROR, logger="app.main"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR16-015",
                "model_number": "HP-M404",
                "firmware_version": "1.0.0",
                "simulate_welcome_page_failure": True,
            },
        )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "register_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]

    error_logs = [
        record
        for record in caplog.records
        if record.levelno == logging.ERROR
        and "Registration failed for serial_number=SN-GOAR16-015" in record.getMessage()
    ]
    assert len(error_logs) >= 1


def test_TC_GOAR_16_16_all_deregistration_registration_error_paths_return_consistent_sanitized_message(client):
    """[HAPPY PATH] Any RegistrationError path within DELETE /printers/{printer_id} is verified to return a generic sanitized error message such as "Printer not found." without exposing internal details."""
    missing = client.delete("/printers/non-existent-id-GOAR16-016-A")

    assert missing.status_code == 404
    missing_body = missing.json()
    assert missing_body["detail"] == "Printer not found."
    assert "deregister_printer" not in missing_body["detail"]
    assert "app.registration" not in missing_body["detail"]
    assert "Traceback" not in missing_body["detail"]

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR16-016",
            "model_number": "HP-M404",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    printer_id = registered.json()["printer_id"]

    first_delete = client.delete(f"/printers/{printer_id}")
    assert first_delete.status_code == 200

    second_delete = client.delete(f"/printers/{printer_id}")

    assert second_delete.status_code == 404
    second_body = second_delete.json()
    assert second_body["detail"] == "Printer not found."
    assert "deregister_printer" not in second_body["detail"]
    assert "app.registration" not in second_body["detail"]
    assert "Traceback" not in second_body["detail"]


def test_TC_GOAR_16_17_deregistration_boundary_error_paths_still_sanitized(client):
    """[BOUNDARY VALUE] Less frequently used or newly added RegistrationError branches for deregistration are exercised to confirm they all surface the same sanitized error pattern."""
    response = client.delete("/printers/boundary-non-existent-id-GOAR16-017")

    assert response.status_code == 404
    body = response.json()
    assert body["detail"] == "Printer not found."
    assert "deregister_printer" not in body["detail"]
    assert "app.registration" not in body["detail"]
    assert "Traceback" not in body["detail"]


def test_TC_GOAR_16_18_error_responses_never_echo_user_supplied_free_form_values(client):
    """[INVALID INPUT] Registration error responses are checked to ensure they never echo user-supplied free-form values (such as arbitrary request fields) back to the client in the error detail."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "   ",
            "model_number": "<script>alert('x')</script>",
            "firmware_version": "{\"key\": \"value\"}",
            "simulate_welcome_page_failure": False,
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["detail"] == "Registration could not be completed. Please check your request and try again."
    assert "<script>alert('x')</script>" not in body["detail"]
    assert "{\"key\": \"value\"}" not in body["detail"]
