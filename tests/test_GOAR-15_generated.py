"""
Generated tests for GOAR-15: model-family aware re-registration, rollback,
ownership preservation, auth behavior, and structured logging.

Automates the test cases in reports/testcases/GOAR-15_test_cases.md at
the HTTP API level, using the `client` TestClient fixture from
tests/conftest.py.
"""

import logging
import re

import pytest

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def test_TC_GOAR_15_01_same_family_model_change_accepted(client, caplog):
    """[HAPPY PATH] Successful same-family model change on re-registration produces new cloud_id, email, and logs history+warning."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-001",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]
    history_initial = initial_body["history"]

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-001",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["claim_code_expires_at"] > initial_body["claim_code_expires_at"]
    assert isinstance(body["xmpp_node"], str)
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-2055" in entry
        and "new=HP-LJ-2060" in entry
        for entry in history
    )
    assert any("Registration started" in entry or "Re-registration started" in entry for entry in history)
    assert any("Cloud identity created" in entry for entry in history)
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history)

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-001"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-LJ-2060"


def test_TC_GOAR_15_02_case_whitespace_model_difference_treated_as_unchanged(client, caplog):
    """[BOUNDARY VALUE] Case/whitespace-only model difference does not produce GOAR-15 model-change warning or history entry."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-002",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-002",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert not warning_records


def test_TC_GOAR_15_03_different_family_model_change_rejected_with_rollback(client, caplog):
    """[ROLLBACK] Different-family model_number change is rejected with 422 and leaves identity fields unchanged except history review entry."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-003",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-003",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-2055" in entry
        and "new=HP-C-MFP-9999" in entry
        for entry in history
    )
    assert not any("Cloud identity created" in entry for entry in history if entry not in initial_body["history"])
    assert not any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in history
        if entry not in initial_body["history"]
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-003"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-C-MFP-9999"


def test_TC_GOAR_15_04_different_family_reregistration_rejected_no_side_effects(client, caplog):
    """[HAPPY PATH negative] Different-family re-registration rejected via RegistrationError with identity fields unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-004",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-004",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.2",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-2055" in entry
        and "new=HP-C-MFP-9999" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-004"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-C-MFP-9999"


def test_TC_GOAR_15_05_boundary_model_family_mismatch_rejected(client, caplog):
    """[BOUNDARY VALUE] Heuristic edge case HP-LJ-001 vs HP-LJ-2055 rejected and leaves model/identity unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-005",
            "model_number": "HP-LJ-001",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-005",
                "model_number": "HP-LJ-2055",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-001', incoming='HP-LJ-2055'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["model_number"] == "HP-LJ-001"
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-001" in entry
        and "new=HP-LJ-2055" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-005"
    assert record.old_model == "HP-LJ-001"
    assert record.new_model == "HP-LJ-2055"


def test_TC_GOAR_15_06_rejected_different_family_has_no_partial_identity_side_effects(client, caplog):
    """[ROLLBACK] Different-family rejection leaves cloud_id, email, xmpp_node, serial_number, and capabilities unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-006",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-006",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"
    assert post_body["serial_number"] == "SN-GOAR15-006"

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-006"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-C-MFP-9999"


def test_TC_GOAR_15_07_identical_identity_reregistration_generates_new_cloud_email_xmpp(client):
    """[HAPPY PATH] Re-registration with identical model and firmware regenerates cloud_id, email, and XMPP node while keeping REGISTERED status."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert any("Re-registration started" in entry for entry in history)
    assert any("Cloud identity created" in entry for entry in history)
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history)


def test_TC_GOAR_15_08_reregistration_with_updated_firmware_preserves_ownership(client):
    """[HAPPY PATH] Re-registration with updated firmware regenerates cloud/email but preserves CLAIMED status and owner_user_id."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": initial_body["claim_code"],
            "user_id": "user-goar15-owner",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar15-owner"

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_09_non_goar15_pre_welcome_page_failure_rolls_back_printer_record(client):
    """[ROLLBACK] simulate_welcome_page_failure=True removes printer record and returns 422 error detail."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-009",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    printer_id_initial = initial.json()["printer_id"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-009",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": True,
        },
    )
    assert failed.status_code == 422
    assert failed.json()["detail"] == f"Welcome page failed to print for printer_id={printer_id_initial}"

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 404
    assert post_get.json()["detail"] == "Printer not found"


def test_TC_GOAR_15_10_normalized_case_whitespace_comparison_avoids_model_change_warning(client, caplog):
    """[HAPPY PATH] Normalization of case/whitespace avoids GOAR-15 model-change warning for equivalent model strings."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-010",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-010",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert not warning_records


def test_TC_GOAR_15_11_normalization_collision_treated_as_unchanged(client, caplog):
    """[BOUNDARY VALUE] Normalization collision where two strings normalize the same still avoids GOAR-15 model-change warning."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-011",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-011",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert not warning_records


def test_TC_GOAR_15_12_multi_segment_model_family_same_model_reregistration_behaves_normally(client):
    """[BOUNDARY VALUE] Re-registration with identical multi-segment model HP-C-MFP-9999 regenerates cloud/email and keeps REGISTERED."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )


def test_TC_GOAR_15_13_no_dash_model_number_treated_as_single_family_string(client):
    """[BOUNDARY VALUE] Re-registration for no-dash model HPLJMFP9999 regenerates cloud/email and keeps REGISTERED with no warning."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HPLJMFP9999",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HPLJMFP9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )


def test_TC_GOAR_15_14_rejected_different_family_leaves_printer_state_exactly_unchanged(client, caplog):
    """[ROLLBACK] Different-family rejection keeps all identity fields equal to pre-state except added review history entry."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-014",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-014",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["cloud_id"] == pre_body["cloud_id"]
    assert post_body["printer_email_id"] == pre_body["printer_email_id"]
    assert post_body["serial_number"] == pre_body["serial_number"]
    assert post_body["xmpp_node"] == pre_body["xmpp_node"]
    assert post_body["status"] == pre_body["status"]

    history = post_body["history"]
    assert len(history) >= len(pre_body["history"])
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-2055" in entry
        and "new=HP-C-MFP-9999" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-014"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-C-MFP-9999"


def test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_succeeds_normally(client):
    """[ROLLBACK (initial registration)] Fresh serial behaves as initial registration with normal REGISTERED state and no rollback."""
    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-015",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()

    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership(client):
    """[HAPPY PATH] CLAIMED printer re-registration with unchanged model regenerates cloud/email but preserves owner and CLAIMED status."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_claimed = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": initial_body["claim_code"],
            "user_id": "user-goar15-claimant",
        },
    )
    assert claimed.status_code == 200

    lookup_before = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_before.status_code == 200
    lookup_body_before = lookup_before.json()
    assert lookup_body_before["status"] == "CLAIMED"
    assert lookup_body_before["owner_user_id"] == "user-goar15-claimant"

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup_after = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_after.status_code == 200
    lookup_body_after = lookup_after.json()
    assert lookup_body_after["owner_user_id"] == "user-goar15-claimant"
    assert lookup_body_after["status"] == "CLAIMED"


def test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership_and_logs_history(client, caplog):
    """[HAPPY PATH] CLAIMED printer same-family model change regenerates identity, preserves owner, and logs GOAR-15 review+warning."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-017",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_claimed = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": initial_body["claim_code"],
            "user_id": "user-goar15-claimant-2",
        },
    )
    assert claimed.status_code == 200

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-017",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    history = body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        and "old=HP-LJ-2055" in entry
        and "new=HP-LJ-2060" in entry
        for entry in history
    )

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-claimant-2"
    assert lookup_body["status"] == "CLAIMED"

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-017"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-LJ-2060"


def test_TC_GOAR_15_18_reregistration_from_different_user_context_does_not_transfer_ownership(client):
    """[OWNERSHIP] Re-registering a CLAIMED printer from another user context leaves owner_user_id and CLAIMED status unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_claimed = initial_body["printer_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": initial_body["claim_code"],
            "user_id": "user-goar15-owner-3",
        },
    )
    assert claimed.status_code == 200

    lookup_before = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_before.status_code == 200
    lookup_body_before = lookup_before.json()
    assert lookup_body_before["owner_user_id"] == "user-goar15-owner-3"
    assert lookup_body_before["status"] == "CLAIMED"

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["status"] == "CLAIMED"

    lookup_after = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_after.status_code == 200
    lookup_body_after = lookup_after.json()
    assert lookup_body_after["owner_user_id"] == "user-goar15-owner-3"
    assert lookup_body_after["status"] == "CLAIMED"


def test_TC_GOAR_15_19_same_family_model_change_emits_structured_warning_log(client, caplog):
    """[HAPPY PATH] Same-family model change on re-registration emits structured WARNING log and succeeds."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-019",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-019",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 200
    body = rereg.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-019"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-LJ-2060"


def test_TC_GOAR_15_20_rejected_different_family_model_change_emits_structured_warning_log(client, caplog):
    """[ROLLBACK] Different-family rejection emits structured WARNING log and keeps printer state unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-020",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_get = client.get(f"/printers/{printer_id_initial}")
    assert pre_get.status_code == 200
    pre_body = pre_get.json()

    with caplog.at_level(
        logging.WARNING,
        logger="app.registration",
    ):
        rereg = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-020",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert rereg.status_code == 422
    expected_detail = (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )
    assert rereg.json()["detail"] == expected_detail

    post_get = client.get(f"/printers/{printer_id_initial}")
    assert post_get.status_code == 200
    post_body = post_get.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == pre_body["status"]

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert record.serial_number == "SN-GOAR15-020"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-C-MFP-9999"


def test_TC_GOAR_15_21_unchanged_model_successful_reregeneration_of_cloud_email_xmpp(client):
    """[HAPPY PATH] Unchanged model re-registration regenerates cloud_id, email, and XMPP as in GOAR-3."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-021",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-021",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_22_same_family_model_change_successful_reregeneration_of_cloud_email(client):
    """[HAPPY PATH] Same-family model change regenerates cloud_id and printer_email while keeping xmpp_node non-empty and status REGISTERED."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-022",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-022",
            "model_number": "HP-LJ-2060",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_23_reregistration_for_printer_with_existing_xmpp_node_preserves_connectivity(client):
    """[BOUNDARY VALUE] Re-registration of printer with existing xmpp_node keeps xmpp_node non-empty while regenerating cloud/email."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-023",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]
    assert xmpp_node_initial

    rereg = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-023",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert rereg.status_code == 200
    body = rereg.json()

    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_24_missing_authorization_header_yields_422_and_no_side_effects(client):
    """[AUTH] Missing Authorization header yields 422 validation error and leaves printer identity unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-024",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    printer_id_initial = initial.json()["printer_id"]
    cloud_id_initial = initial.json()["cloud_id"]
    printer_email_id_initial = initial.json()["printer_email_id"]

    missing = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-024",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
        headers={},
    )
    assert missing.status_code == 422
    body = missing.json()
    assert "detail" in body

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["cloud_id"] == cloud_id_initial
    assert lookup_body["printer_email_id"] == printer_email_id_initial


def test_TC_GOAR_15_25_invalid_bearer_token_yields_401_and_no_side_effects(client):
    """[AUTH] Invalid bearer token yields 401 and leaves printer identity unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-025",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    printer_id_initial = initial.json()["printer_id"]
    cloud_id_initial = initial.json()["cloud_id"]
    printer_email_id_initial = initial.json()["printer_email_id"]

    invalid = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-025",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert invalid.status_code == 401
    assert invalid.json()["detail"] == "Invalid or expired token"

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["cloud_id"] == cloud_id_initial
    assert lookup_body["printer_email_id"] == printer_email_id_initial

