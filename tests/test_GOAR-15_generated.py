"""
Generated tests for GOAR-15: model_number change and re-registration behaviour,
including same-family acceptance, different-family rejection with rollback,
identity regeneration, ownership preservation, auth failures, and structured
logging requirements.

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
    """[HAPPY PATH] Successful re-registration where model_number changes within the same family is accepted and produces the expected registration outputs."""

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

    assert isinstance(printer_id_initial, str)
    assert isinstance(cloud_id_initial, str)
    assert isinstance(printer_email_id_initial, str)
    assert isinstance(xmpp_node_initial, str)
    assert isinstance(history_initial, list)
    assert initial_body["status"] == "REGISTERED"
    assert initial_body["owner_user_id"] is None

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-001",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert isinstance(body["claim_code_expires_at"], str)
    assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert isinstance(history, list)
    assert any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        and "old=HP-LJ-2055" in entry
        and "new=HP-LJ-2060" in entry
        for entry in history
    )
    assert any("Registration started" in entry or "Re-registration started" in entry for entry in history)
    assert any("Cloud identity created:" in entry for entry in history)
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


def test_TC_GOAR_15_02_case_whitespace_only_model_difference_treated_as_unchanged(client, caplog):
    """[BOUNDARY VALUE] Re-registration where model_number differs only by case/whitespace is treated as unchanged after normalization and does not trigger a model-change flag."""

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
    history_initial = initial_body["history"]

    assert isinstance(printer_id_initial, str)
    assert isinstance(cloud_id_initial, str)
    assert isinstance(printer_email_id_initial, str)
    assert isinstance(xmpp_node_initial, str)
    assert isinstance(history_initial, list)
    assert initial_body["status"] == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-002",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"
    assert body["xmpp_node"]

    history = body["history"]
    assert isinstance(history, list)
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
    assert len(warning_records) == 0


def test_TC_GOAR_15_03_different_family_model_change_rejected_with_rollback(client, caplog):
    """[ROLLBACK] Re-registration with a different-family model_number is rejected and leaves Cloud ID, email, XMPP node, and capabilities unchanged apart from the review history entry."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]
    history_initial = pre_body["history"]

    assert status_initial == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-003",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial

    post_history = post_body["history"]
    assert len(post_history) >= len(history_initial)
    assert any(
        entry
        == "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        for entry in post_history
    )
    assert not any("Cloud identity created" in entry for entry in post_history)
    assert not any("Welcome page printed successfully; registration complete" in entry for entry in post_history)

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
    """[HAPPY PATH] Re-registration attempt with a clearly different-family model_number is rejected with a RegistrationError and no registration-side effects occur."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]
    history_initial = pre_body["history"]

    assert status_initial == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-004",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.2",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial

    post_history = post_body["history"]
    assert len(post_history) >= len(history_initial)
    assert any(
        entry
        == "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        for entry in post_history
    )
    assert not any("Cloud identity created" in entry for entry in post_history)
    assert not any("Welcome page printed successfully; registration complete" in entry for entry in post_history)

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


def test_TC_GOAR_15_05_boundary_classification_heuristic_edge_HP_LJ_001(client, caplog):
    """[BOUNDARY VALUE] Re-registration where the new model_number sits on the edge of the same-family vs different-family heuristic (last dash-separated segment) is correctly classified and rejected."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    status_initial = pre_body["status"]
    history_initial = pre_body["history"]

    assert status_initial == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-005",
                "model_number": "HP-LJ-2055",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-001', incoming='HP-LJ-2055'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["model_number"] == "HP-LJ-001"
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["status"] == "REGISTERED"

    post_history = post_body["history"]
    assert len(post_history) >= len(history_initial)
    assert any(
        entry
        == "GOAR-15: model_number changed on re-registration (old=HP-LJ-001, new=HP-LJ-2055) -- flagged for review"
        for entry in post_history
    )
    assert not any("Welcome page printed successfully; registration complete" in entry for entry in post_history)

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
    """[ROLLBACK] Rejected different-family re-registration does not create or alter any Cloud ID, printer email, XMPP node, capabilities record, or serial index."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]

    assert status_initial == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-006",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial
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


def test_TC_GOAR_15_07_identical_identity_fields_reregistration_succeeds_new_identity(client):
    """[HAPPY PATH] Re-registration with identical model_number and firmware_version succeeds and generates a new Cloud ID, email ID, and XMPP node as per existing rules."""

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
    status_initial = initial_body["status"]
    history_initial = initial_body["history"]

    assert status_initial == "REGISTERED"

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

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
    assert isinstance(history, list)
    assert len(history) >= len(history_initial)
    assert any("Re-registration started" in entry for entry in history)
    assert any("Cloud identity created:" in entry for entry in history)
    assert any("Welcome page printed successfully; registration complete" in entry for entry in history)


def test_TC_GOAR_15_08_reregistration_with_updated_firmware_preserves_ownership(client):
    """[HAPPY PATH] Re-registration with identical model_number but updated firmware_version succeeds and regenerates Cloud ID and printer email while preserving ownership."""

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_claimed = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    xmpp_node_initial = registered_body["xmpp_node"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar15-owner",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar15-owner"

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_09_non_goar_15_pre_welcome_page_failure_rolls_back_fully(client):
    """[ROLLBACK] Failed re-registration due to a non-GOAR-15 pre-Welcome-Page error rolls back fully and leaves prior Cloud ID, email, and XMPP state unchanged."""

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
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    history_initial = pre_body["history"]

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

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 404
    assert post_state.json()["detail"] == "Printer not found"


def test_TC_GOAR_15_10_normalized_case_whitespace_comparison_avoids_model_change_warning(client, caplog):
    """[HAPPY PATH] Re-registration where old and new model_number differ only in case/whitespace does not trigger a model-change warning and is treated as the same model."""

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
    history_initial = initial_body["history"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-010",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert isinstance(history, list)
    assert len(history) >= len(history_initial)
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
    assert len(warning_records) == 0


def test_TC_GOAR_15_11_normalization_collision_treated_consistently_as_unchanged(client, caplog):
    """[BOUNDARY VALUE] Re-registration where normalization causes two visually distinct model_number strings to collide is still treated consistently as unchanged."""

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
    history_initial = initial_body["history"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-011",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert isinstance(history, list)
    assert len(history) >= len(history_initial)
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
    assert len(warning_records) == 0


def test_TC_GOAR_15_12_multi_segment_model_number_family_extraction_behaves_consistently(client):
    """[BOUNDARY VALUE] Re-registration with multiple dash-separated segments in model_number verifies that _model_family() consistently extracts the family and classifies same-family vs different-family."""

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

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert isinstance(history, list)
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )


def test_TC_GOAR_15_13_no_dash_model_number_treated_as_single_family_string(client):
    """[BOUNDARY VALUE] Re-registration for a model_number with no dash separator verifies that the entire string is treated as the family and behaves consistently."""

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

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HPLJMFP9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert isinstance(history, list)
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )


def test_TC_GOAR_15_14_rejected_different_family_leaves_printer_state_unchanged(client, caplog):
    """[ROLLBACK] Different-family re-registration that is rejected leaves the printer record, capabilities, serial index, Cloud ID, email, and XMPP node exactly as before the attempt."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]
    serial_number_initial = pre_body["serial_number"]
    history_initial = pre_body["history"]

    assert status_initial == "REGISTERED"
    assert serial_number_initial == "SN-GOAR15-014"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-014",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial
    assert post_body["serial_number"] == serial_number_initial

    post_history = post_body["history"]
    assert len(post_history) >= len(history_initial)
    assert any(
        entry
        == "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        for entry in post_history
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


def test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_behaves_normally(client):
    """[ROLLBACK (initial registration)] Rejected re-registration for a previously unregistered serial_number cannot occur; initial registration succeeds with normal identity creation."""

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-015",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    body = registered.json()

    assert isinstance(body["printer_id"], str)
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert isinstance(body["claim_code_expires_at"], str)
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership(client):
    """[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged model_number succeeds while preserving owner_user_id and CLAIMED status."""

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_claimed = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    xmpp_node_initial = registered_body["xmpp_node"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar15-claimant",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar15-claimant"

    lookup_before = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_before.status_code == 200
    lookup_before_body = lookup_before.json()
    assert lookup_before_body["status"] == "CLAIMED"
    assert lookup_before_body["owner_user_id"] == "user-goar15-claimant"

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    assert body["status"] == "CLAIMED"

    lookup_after = client.get(f"/printers/{printer_id_claimed}")
    assert lookup_after.status_code == 200
    lookup_after_body = lookup_after.json()
    assert lookup_after_body["owner_user_id"] == "user-goar15-claimant"
    assert lookup_after_body["status"] == "CLAIMED"


def test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership(client, caplog):
    """[HAPPY PATH] Re-registration of a CLAIMED printer with same-family model_number succeeds, logs the model change, and preserves owner_user_id and CLAIMED status."""

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-017",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_claimed = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    xmpp_node_initial = registered_body["xmpp_node"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar15-claimant-2",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar15-claimant-2"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-017",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-claimant-2"
    assert lookup_body["status"] == "CLAIMED"

    history = body["history"]
    assert isinstance(history, list)
    assert any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        and "old=HP-LJ-2055" in entry
        and "new=HP-LJ-2060" in entry
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
    assert record.serial_number == "SN-GOAR15-017"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-LJ-2060"


def test_TC_GOAR_15_18_reregistration_from_different_user_context_does_not_transfer_ownership(client):
    """[OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context does not transfer or clear ownership and leaves ownership unchanged."""

    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_claimed = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": registered_body["claim_code"],
            "user_id": "user-goar15-owner-3",
        },
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == "user-goar15-owner-3"

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert body["printer_id"] == printer_id_claimed
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner-3"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_19_same_family_model_change_emits_structured_warning_log(client, caplog):
    """[HAPPY PATH] Same-family model-number change on re-registration emits a structured warning log with serial_number, old_model, and new_model fields while the registration succeeds."""

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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-019",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 200
    body = re_registered.json()

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
    """[ROLLBACK] Different-family model-number change that is rejected emits a structured warning log with serial_number, old_model, and new_model while leaving printer state unchanged."""

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

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        re_registered = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-020",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert re_registered.status_code == 422
    assert re_registered.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). "
        "This looks like a different physical device reusing the same "
        "serial number."
    )

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()

    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial

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


def test_TC_GOAR_15_21_unchanged_model_successful_reregistration_regenerates_identity(client):
    """[HAPPY PATH] Successful re-registration with unchanged model_number generates a new Cloud ID, a new printer email ID, and assigns an XMPP node if missing, all differing from prior values."""

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

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-021",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_22_same_family_model_change_successful_reregistration_regenerates_identity(client):
    """[HAPPY PATH] Successful re-registration with same-family model_number change generates new Cloud ID and printer email while preserving or assigning XMPP connectivity."""

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

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-022",
            "model_number": "HP-LJ-2060",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_23_reregistration_for_printer_with_existing_xmpp_preserves_connectivity(client):
    """[BOUNDARY VALUE] Re-registration of a printer that already has an XMPP node verifies that the node is preserved or correctly reassigned without violating connectivity rules."""

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

    re_registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-023",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert re_registered.status_code == 200
    body = re_registered.json()

    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_24_missing_authorization_header_yields_422_no_side_effects(client):
    """[AUTH] Re-registration request to the protected registration endpoint without an Authorization header is rejected with no registration-side effects."""

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
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]

    missing_auth_response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-024",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
        headers={},
    )
    assert missing_auth_response.status_code == 422
    error_body = missing_auth_response.json()
    assert error_body["detail"]

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial


def test_TC_GOAR_15_25_invalid_bearer_token_yields_401_no_side_effects(client):
    """[AUTH] Re-registration request to the protected registration endpoint with an invalid or expired bearer token is rejected with no registration-side effects."""

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
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]

    pre_state = client.get(f"/printers/{printer_id_initial}")
    assert pre_state.status_code == 200
    pre_body = pre_state.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]

    invalid_token_response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-025",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert invalid_token_response.status_code == 401
    assert invalid_token_response.json()["detail"] == "Invalid or expired token"

    post_state = client.get(f"/printers/{printer_id_initial}")
    assert post_state.status_code == 200
    post_body = post_state.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial


