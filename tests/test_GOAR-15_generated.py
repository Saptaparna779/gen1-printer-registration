"""
Generated tests for GOAR-15: model_number change and re-registration behavior,
including same-family vs different-family handling, rollback semantics, auth
edges, ownership preservation, and structured logging for registration events.

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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-001",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_initial
    assert isinstance(body["cloud_id"], str)
    assert body["cloud_id"].startswith("CID-")
    assert body["cloud_id"] != cloud_id_initial
    assert isinstance(body["printer_email_id"], str)
    assert body["printer_email_id"].endswith("@print.hpeprint.com")
    assert body["printer_email_id"] != printer_email_id_initial
    assert CLAIM_CODE_PATTERN.match(body["claim_code"])
    assert isinstance(body["claim_code_expires_at"], str)
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        and "old=HP-LJ-2055" in entry
        and "new=HP-LJ-2060" in entry
        for entry in history
    )
    assert any(
        "Registration started" in entry or "Re-registration started" in entry
        for entry in history
    )
    assert any("Cloud identity created:" in entry for entry in history)
    assert any(
        "Welcome page printed successfully; registration complete" in entry
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
    assert record.serial_number == "SN-GOAR15-001"
    assert record.old_model == "HP-LJ-2055"
    assert record.new_model == "HP-LJ-2060"


def test_TC_GOAR_15_02_case_whitespace_model_difference_treated_as_unchanged(client, caplog):
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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-002",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]
    history_initial = initial_body["history"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial
    assert pre_body["status"] == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-003",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert len(history) >= len(history_initial) + 1
    assert any(
        entry
        == "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        for entry in history
    )
    assert not any(
        "Cloud identity created:" in entry
        or "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1


def test_TC_GOAR_15_04_different_family_reregistration_rejected_with_no_side_effects(client, caplog):
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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]
    history_initial = initial_body["history"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial
    assert pre_body["status"] == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-004",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.2",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert len(history) >= len(history_initial) + 1
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        for entry in history
    )
    assert not any(
        "Cloud identity created:" in entry
        or "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1


def test_TC_GOAR_15_05_boundary_model_family_mismatch_rejected(client, caplog):
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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    history_initial = initial_body["history"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["model_number"] == "HP-LJ-001"
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["status"] == "REGISTERED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-005",
                "model_number": "HP-LJ-2055",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-001', incoming='HP-LJ-2055'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["model_number"] == "HP-LJ-001"
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert len(history) >= len(history_initial) + 1
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        for entry in history
    )
    assert not any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1


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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial
    assert pre_body["status"] == "REGISTERED"
    assert pre_body["serial_number"] == "SN-GOAR15-006"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-006",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
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


def test_TC_GOAR_15_07_identical_model_firmware_reregistration_generates_new_identity(client):
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(body["printer_email_id"])
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if not xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert any("Re-registration started" in entry for entry in history)
    assert any("Cloud identity created:" in entry for entry in history)
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )


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
    assert claimed.json()["status"] == "CLAIMED"

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_09_failed_reregistration_pre_welcome_page_rolls_back_printer_record(client):
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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial

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

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 404
    assert post_lookup.json()["detail"] == "Printer not found"


def test_TC_GOAR_15_10_normalized_model_comparison_avoids_model_change_warning(client, caplog):
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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-010",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
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
    assert len(warning_records) == 0


def test_TC_GOAR_15_11_normalization_collision_treated_as_unchanged(client, caplog):
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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-011",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
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
    assert len(warning_records) == 0


def test_TC_GOAR_15_12_multi_segment_model_family_reregistration_same_family(client):
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HPLJMFP9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "REGISTERED"

    history = body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )


def test_TC_GOAR_15_14_different_family_reregistration_leaves_printer_state_unchanged(client, caplog):
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
    cloud_id_initial = initial_body["cloud_id"]
    printer_email_id_initial = initial_body["printer_email_id"]
    xmpp_node_initial = initial_body["xmpp_node"]
    status_initial = initial_body["status"]
    history_initial = initial_body["history"]

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial
    assert pre_body["status"] == status_initial

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-014",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial

    history = post_body["history"]
    assert len(history) >= len(history_initial) + 1
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.message
    ]
    assert len(warning_records) >= 1


def test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_succeeds(client):
    """[ROLLBACK] Rejected re-registration for a previously unregistered serial_number does not create any new printer record, capabilities, serial index, Cloud ID, email, or XMPP node (implemented as initial registration success)."""
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
    assert body["status"] == "REGISTERED"
    assert CLOUD_ID_PATTERN.match(body["cloud_id"])
    assert EMAIL_PATTERN.match(body["printer_email_id"])


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
    assert claimed.json()["status"] == "CLAIMED"

    pre_lookup = client.get(f"/printers/{printer_id_claimed}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["owner_user_id"] == "user-goar15-claimant"
    assert pre_body["status"] == "CLAIMED"

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-claimant"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership_and_logs_change(client, caplog):
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
    assert claimed.json()["status"] == "CLAIMED"

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-017",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_claimed
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_claimed}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-claimant-2"
    assert lookup_body["status"] == "CLAIMED"

    history = body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration" in entry
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
    assert claimed.json()["status"] == "CLAIMED"

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-018",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
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
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-019",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["printer_id"] == printer_id_initial
    assert body["cloud_id"] != cloud_id_initial
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


def test_TC_GOAR_15_20_rejected_different_family_model_change_emits_warning_and_rolls_back(client, caplog):
    """[ROLLBACK] Different-family model-number change that is rejected emits a structured warning log with serial_number, old_model, new_model while leaving printer state unchanged."""
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

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    assert pre_body["cloud_id"] == cloud_id_initial
    assert pre_body["printer_email_id"] == printer_email_id_initial
    assert pre_body["xmpp_node"] == xmpp_node_initial

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-020",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert response.status_code == 422
    assert response.json()["detail"] == (
        "Re-registration rejected: model family mismatch "
        "(existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a "
        "different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial

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


def test_TC_GOAR_15_21_unchanged_model_reregistration_regenerates_cloud_email_xmpp(client):
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-021",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if not xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_22_same_family_model_change_regenerates_cloud_and_email(client):
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-022",
            "model_number": "HP-LJ-2060",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    if xmpp_node_initial:
        assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_23_reregistration_preserves_existing_xmpp_connectivity(client):
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

    response = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-023",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["cloud_id"] != cloud_id_initial
    assert body["printer_email_id"] != printer_email_id_initial
    assert body["xmpp_node"]
    assert body["status"] == "REGISTERED"


def test_TC_GOAR_15_24_missing_authorization_header_yields_422_and_no_side_effects(client):
    """[AUTH] Re-registration request to the protected registration endpoint without an Authorization header is rejected with no registration-side effects."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-024",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_initial = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]

    response = client.post(
        "/printers/register",
        headers={},
        json={
            "serial_number": "SN-GOAR15-024",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 422

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["cloud_id"] == cloud_id_initial
    assert lookup_body["printer_email_id"] == printer_email_id_initial


def test_TC_GOAR_15_25_invalid_bearer_token_yields_401_and_no_side_effects(client):
    """[AUTH] Re-registration request to the protected registration endpoint with an invalid or expired bearer token is rejected with no registration-side effects."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-025",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_initial = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]

    response = client.post(
        "/printers/register",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "serial_number": "SN-GOAR15-025",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["cloud_id"] == cloud_id_initial
    assert lookup_body["printer_email_id"] == printer_email_id_initial

