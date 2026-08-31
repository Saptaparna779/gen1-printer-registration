"""
Generated tests for GOAR-15: model-number change detection on re-registration, model-family gate for spoofing protection, structured warning logs, and rollback-safe rejection, while preserving existing Cloud ID, email, claim, and auth behaviors.

Automates the test cases in reports/testcases/GOAR-15_test_cases.md at the HTTP API level, using the `client` TestClient fixture from
tests/conftest.py.
"""

import logging
import re

import pytest

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def _find_history_entry(history, substring):
    return [entry for entry in history if substring in entry]


def test_TC_GOAR_15_01_same_family_model_change_accepted_with_full_registration_outputs(client, caplog):
    """[HAPPY PATH] Same-serial re-registration where the normalized model_number changes within the same model family succeeds, generates new Cloud identity, and records GOAR-15 history and WARNING log."""
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
    claim_code_initial = initial_body["claim_code"]

    lookup_initial = client.get(f"/printers/{printer_id_initial}")
    assert lookup_initial.status_code == 200
    lookup_initial_body = lookup_initial.json()
    assert lookup_initial_body["status"] == "REGISTERED"
    assert lookup_initial_body["owner_user_id"] is None

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-001",
                "model_number": "HP-LJ-2060",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"].startswith("CID-")
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"].endswith("@print.hpeprint.com")
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert CLAIM_CODE_PATTERN.match(second_body["claim_code"])
    assert second_body["claim_code"] != claim_code_initial
    assert second_body["status"] == "REGISTERED"
    assert second_body["xmpp_node"]

    history = second_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-LJ-2060) -- flagged for review"
        in entry
        for entry in history
    )
    assert any("Re-registration started" in entry for entry in history)
    assert any("Cloud identity created:" in entry for entry in history)
    assert any(
        "Welcome page printed successfully; registration complete" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1
    first_warning = warning_records[0]
    assert getattr(first_warning, "serial_number") == "SN-GOAR15-001"
    assert getattr(first_warning, "old_model") == "HP-LJ-2055"
    assert getattr(first_warning, "new_model") == "HP-LJ-2060"


def test_TC_GOAR_15_02_case_whitespace_only_model_difference_treated_as_unchanged(client, caplog):
    """[BOUNDARY VALUE] Re-registration where model_number differs only by case/whitespace is treated as unchanged and does not emit GOAR-15 warning or history entry."""
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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-002",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"].startswith("CID-")
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"].endswith("@print.hpeprint.com")
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "REGISTERED"

    history = second_body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert not warning_records


def test_TC_GOAR_15_03_different_family_model_change_rejected_with_unchanged_identity_and_capabilities(client, caplog):
    """[ROLLBACK] Different-family model_number change is rejected and leaves identity and capabilities unchanged except for GOAR-15 history/log."""
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

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    history_initial = pre_body["history"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-003",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert failed.status_code == 422
    assert (
        failed.json()["detail"]
        == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"
    assert post_body["serial_number"] == "SN-GOAR15-003"

    history = post_body["history"]
    assert len(history) >= len(history_initial) + 1
    assert any(
        "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        in entry
        for entry in history
    )
    assert not any(
        "Cloud identity created:" in entry and "HP-C-MFP-9999" in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1
    first_warning = warning_records[0]
    assert getattr(first_warning, "serial_number") == "SN-GOAR15-003"
    assert getattr(first_warning, "old_model") == "HP-LJ-2055"
    assert getattr(first_warning, "new_model") == "HP-C-MFP-9999"


def test_TC_GOAR_15_04_different_family_reregistration_rejected_with_unchanged_state(client, caplog):
    """[INVALID INPUT] Different-family re-registration is rejected with RegistrationError translated to 422 and state unchanged."""
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

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-004",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.2",
                "simulate_welcome_page_failure": False,
            },
        )

    assert failed.status_code == 422
    assert (
        failed.json()["detail"]
        == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == "REGISTERED"

    history = post_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"
        in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1


def test_TC_GOAR_15_05_same_family_last_segment_change_accepted_with_warning(client, caplog):
    """[BOUNDARY VALUE] Same-family model_number change differing only in last segment is accepted and logged with GOAR-15 warning."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-005",
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
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-005",
                "model_number": "HP-LJ-4250",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"].startswith("CID-")
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"].endswith("@print.hpeprint.com")
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "REGISTERED"

    history = second_body["history"]
    assert any(
        "GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-LJ-4250) -- flagged for review"
        in entry
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1
    first_warning = warning_records[0]
    assert getattr(first_warning, "serial_number") == "SN-GOAR15-005"
    assert getattr(first_warning, "old_model") == "HP-LJ-2055"
    assert getattr(first_warning, "new_model") == "HP-LJ-4250"


def test_TC_GOAR_15_06_rejected_different_family_reregistration_leaves_identity_intact(client, caplog):
    """[ROLLBACK] Different-family re-registration rejection leaves Cloud ID, email, XMPP node, and status unchanged."""
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

    pre_lookup = client.get(f"/printers/{printer_id_initial}")
    assert pre_lookup.status_code == 200
    pre_body = pre_lookup.json()
    cloud_id_initial = pre_body["cloud_id"]
    printer_email_id_initial = pre_body["printer_email_id"]
    xmpp_node_initial = pre_body["xmpp_node"]
    status_initial = pre_body["status"]

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        failed = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-006",
                "model_number": "HP-C-MFP-9999",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert failed.status_code == 422
    assert (
        failed.json()["detail"]
        == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."
    )

    post_lookup = client.get(f"/printers/{printer_id_initial}")
    assert post_lookup.status_code == 200
    post_body = post_lookup.json()
    assert post_body["cloud_id"] == cloud_id_initial
    assert post_body["printer_email_id"] == printer_email_id_initial
    assert post_body["xmpp_node"] == xmpp_node_initial
    assert post_body["status"] == status_initial

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1


def test_TC_GOAR_15_07_reregistration_with_identical_identity_regenerates_cloud_id_and_email(client):
    """[HAPPY PATH] Re-registration with identical model_number and firmware_version generates a new Cloud ID and printer email ID."""
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

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-007",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(second_body["cloud_id"])
    assert second_body["cloud_id"] != cloud_id_initial
    assert EMAIL_PATTERN.match(second_body["printer_email_id"])
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "REGISTERED"


def test_TC_GOAR_15_08_reregistration_of_claimed_printer_with_firmware_update_preserves_ownership(client):
    """[HAPPY PATH] Re-registration of a claimed printer with same model but new firmware regenerates identities and preserves ownership."""
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
    printer_id_initial = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    claim_code_initial = registered_body["claim_code"]

    claimed = client.post(
        "/printers/claim",
        json={"claim_code": claim_code_initial, "user_id": "user-goar15-owner"},
    )
    assert claimed.status_code == 200

    lookup_claimed = client.get(f"/printers/{printer_id_initial}")
    assert lookup_claimed.status_code == 200
    lookup_claimed_body = lookup_claimed.json()
    assert lookup_claimed_body["status"] == "CLAIMED"
    assert lookup_claimed_body["owner_user_id"] == "user-goar15-owner"

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-008",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "CLAIMED"

    lookup_after = client.get(f"/printers/{printer_id_initial}")
    assert lookup_after.status_code == 200
    lookup_after_body = lookup_after.json()
    assert lookup_after_body["owner_user_id"] == "user-goar15-owner"
    assert lookup_after_body["status"] == "CLAIMED"


def test_TC_GOAR_15_09_welcome_page_failure_during_reregistration_rolls_back_completely(client):
    """[ROLLBACK] Welcome-page failure during re-registration rolls back completely leaving no printer record."""
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
    assert (
        failed.json()["detail"]
        == f"Welcome page failed to print for printer_id={printer_id_initial}"
    )

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 404
    assert lookup.json()["detail"] == "Printer not found"


def test_TC_GOAR_15_10_normalized_model_equality_avoids_goar15_warning_and_history(client, caplog):
    """[ROLLBACK] Normalized equality for model_number avoids GOAR-15 warning and history entry while still regenerating identities."""
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
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-010",
                "model_number": " hp-lj-2055 ",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "REGISTERED"

    history = second_body["history"]
    assert not any(
        entry.startswith("GOAR-15: model_number changed on re-registration")
        for entry in history
    )

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert not warning_records


@pytest.mark.skip(
    reason=(
        "UNTESTABLE: Current implementation normalizes only strip().upper(); "
        "testing normalization collisions would require assumptions about additional"
        " normalization beyond app.registration._model_family."
    )
)
def test_TC_GOAR_15_11_normalization_collision_treated_consistently_as_unchanged(client):
    """[BOUNDARY VALUE] Re-registration where normalization collision would occur is not testable without additional normalization behavior."""
    pass


def test_TC_GOAR_15_12_cloud_id_generation_only_on_accepted_model_family_checks(client):
    """[BOUNDARY VALUE] Rejected model-family mismatch does not persist a new Cloud ID; existing Cloud ID remains unchanged."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]

    failed = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-012",
            "model_number": "HP-C-MFP-9999",
            "firmware_version": "1.0.1",
            "simulate_welcome_page_failure": False,
        },
    )
    assert failed.status_code == 422
    assert (
        failed.json()["detail"]
        == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."
    )

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["cloud_id"] == cloud_id_initial


def test_TC_GOAR_15_13_accepted_reregistration_never_reuses_old_cloud_id(client):
    """[ROLL FORWARD] Successful re-registration always persists a new Cloud ID distinct from prior value."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200
    initial_body = initial.json()
    printer_id_initial = initial_body["printer_id"]
    cloud_id_initial = initial_body["cloud_id"]

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-013",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert CLOUD_ID_PATTERN.match(second_body["cloud_id"])
    assert second_body["cloud_id"] != cloud_id_initial


def test_TC_GOAR_15_14_structured_warning_log_with_serial_old_model_new_model(client, caplog):
    """[HAPPY PATH] Same-family model change emits structured WARNING log with serial_number, old_model, and new_model fields."""
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

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-014",
                "model_number": "HP-LJ-4250",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert getattr(record, "serial_number") == "SN-GOAR15-014"
    assert getattr(record, "old_model") == "HP-LJ-2055"
    assert getattr(record, "new_model") == "HP-LJ-4250"


def test_TC_GOAR_15_15_multiple_same_family_model_changes_emit_structured_warning_logs(client, caplog):
    """[BOUNDARY VALUE] Multiple same-family model changes each emit structured WARNING logs with consistent fields."""
    initial = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-015",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert initial.status_code == 200

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        first_change = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-015",
                "model_number": "HP-LJ-4250",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )
        second_change = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-015",
                "model_number": "HP-LJ-4300",
                "firmware_version": "1.0.2",
                "simulate_welcome_page_failure": False,
            },
        )

    assert first_change.status_code == 200
    assert second_change.status_code == 200

    records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(records) >= 2
    assert any(
        getattr(r, "serial_number") == "SN-GOAR15-015"
        and getattr(r, "old_model") == "HP-LJ-2055"
        and getattr(r, "new_model") == "HP-LJ-4250"
        for r in records
    )
    assert any(
        getattr(r, "serial_number") == "SN-GOAR15-015"
        and getattr(r, "old_model") == "HP-LJ-4250"
        and getattr(r, "new_model") == "HP-LJ-4300"
        for r in records
    )


def test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership(client):
    """[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged model keeps owner_user_id and CLAIMED status while regenerating identities."""
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
    printer_id_initial = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    claim_code_initial = registered_body["claim_code"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": claim_code_initial,
            "user_id": "user-goar15-owner-16",
        },
    )
    assert claimed.status_code == 200

    second = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-016",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner-16"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_17_reregistration_of_claimed_printer_with_same_family_model_change_preserves_ownership(client, caplog):
    """[HAPPY PATH] Re-registration of a CLAIMED printer with same-family model change logs GOAR-15 warning and preserves ownership."""
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
    printer_id_initial = registered_body["printer_id"]
    cloud_id_initial = registered_body["cloud_id"]
    printer_email_id_initial = registered_body["printer_email_id"]
    claim_code_initial = registered_body["claim_code"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": claim_code_initial,
            "user_id": "user-goar15-owner-17",
        },
    )
    assert claimed.status_code == 200

    with caplog.at_level(logging.WARNING, logger="app.registration"):
        second = client.post(
            "/printers/register",
            json={
                "serial_number": "SN-GOAR15-017",
                "model_number": "HP-LJ-4250",
                "firmware_version": "1.0.1",
                "simulate_welcome_page_failure": False,
            },
        )

    assert second.status_code == 200
    second_body = second.json()
    assert second_body["printer_id"] == printer_id_initial
    assert second_body["cloud_id"] != cloud_id_initial
    assert second_body["printer_email_id"] != printer_email_id_initial
    assert second_body["status"] == "CLAIMED"

    lookup = client.get(f"/printers/{printer_id_initial}")
    assert lookup.status_code == 200
    lookup_body = lookup.json()
    assert lookup_body["owner_user_id"] == "user-goar15-owner-17"
    assert lookup_body["status"] == "CLAIMED"

    warning_records = [
        r
        for r in caplog.records
        if r.levelno == logging.WARNING
        and "GOAR-15: model_number changed on re-registration" in r.getMessage()
    ]
    assert len(warning_records) >= 1
    record = warning_records[0]
    assert getattr(record, "serial_number") == "SN-GOAR15-017"
    assert getattr(record, "old_model") == "HP-LJ-2055"
    assert getattr(record, "new_model") == "HP-LJ-4250"


def test_TC_GOAR_15_18_reregistration_of_claimed_printer_with_invalid_token_does_not_change_ownership(client):
    """[OWNERSHIP] Re-registration of a CLAIMED printer with invalid token is rejected and ownership remains unchanged."""
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
    printer_id_initial = registered_body["printer_id"]
    claim_code_initial = registered_body["claim_code"]

    claimed = client.post(
        "/printers/claim",
        json={
            "claim_code": claim_code_initial,
            "user_id": "user-goar15-owner-18",
        },
    )
    assert claimed.status_code == 200

    response = client.post(
        "/printers/register",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "serial_number": "SN-GOAR15-018",
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
    assert lookup_body["owner_user_id"] == "user-goar15-owner-18"
    assert lookup_body["status"] == "CLAIMED"


def test_TC_GOAR_15_19_missing_authorization_header_rejected_on_registration(client):
    """[AUTH] Registration request without Authorization header is rejected with 422 and does not register a printer."""
    response = client.post(
        "/printers/register",
        headers={},
        json={
            "serial_number": "SN-GOAR15-019",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 422
    body = response.json()
    assert isinstance(body.get("detail"), list)
    assert any(
        item.get("loc") == ["header", "authorization"]
        and "field required" in item.get("msg", "")
        for item in body["detail"]
    )


def test_TC_GOAR_15_20_invalid_token_rejected_on_registration_with_no_side_effects(client):
    """[AUTH] Registration request with invalid token is rejected with 401 and does not register a printer."""
    response = client.post(
        "/printers/register",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "serial_number": "SN-GOAR15-020",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired token"


def test_TC_GOAR_15_21_missing_authorization_header_rejected_on_claim_and_lookup(client):
    """[AUTH] Claim and lookup without Authorization header are rejected with 422 and leave ownership unchanged."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-021",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_initial = registered_body["printer_id"]
    claim_code_initial = registered_body["claim_code"]

    claim_response = client.post(
        "/printers/claim",
        headers={},
        json={
            "claim_code": claim_code_initial,
            "user_id": "user-goar15-claim-21",
        },
    )
    assert claim_response.status_code == 422

    lookup_response = client.get(
        f"/printers/{printer_id_initial}",
        headers={},
    )
    assert lookup_response.status_code == 422

    lookup_valid = client.get(f"/printers/{printer_id_initial}")
    assert lookup_valid.status_code == 200
    lookup_valid_body = lookup_valid.json()
    assert lookup_valid_body["status"] == "REGISTERED"
    assert lookup_valid_body["owner_user_id"] is None


def test_TC_GOAR_15_22_invalid_token_rejected_on_claim_lookup_and_deregister(client):
    """[AUTH] Claim, lookup, and deregister with invalid token are rejected with 401 and do not change printer state."""
    registered = client.post(
        "/printers/register",
        json={
            "serial_number": "SN-GOAR15-022",
            "model_number": "HP-LJ-2055",
            "firmware_version": "1.0.0",
            "simulate_welcome_page_failure": False,
        },
    )
    assert registered.status_code == 200
    registered_body = registered.json()
    printer_id_initial = registered_body["printer_id"]
    claim_code_initial = registered_body["claim_code"]

    claim_response = client.post(
        "/printers/claim",
        headers={"Authorization": "Bearer invalid_token"},
        json={
            "claim_code": claim_code_initial,
            "user_id": "user-goar15-claim-22",
        },
    )
    assert claim_response.status_code == 401
    assert claim_response.json()["detail"] == "Invalid or expired token"

    lookup_response = client.get(
        f"/printers/{printer_id_initial}",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert lookup_response.status_code == 401
    assert lookup_response.json()["detail"] == "Invalid or expired token"

    delete_response = client.delete(
        f"/printers/{printer_id_initial}",
        headers={"Authorization": "Bearer invalid_token"},
    )
    assert delete_response.status_code == 401
    assert delete_response.json()["detail"] == "Invalid or expired token"

    lookup_valid = client.get(f"/printers/{printer_id_initial}")
    assert lookup_valid.status_code == 200
    lookup_valid_body = lookup_valid.json()
    assert lookup_valid_body["status"] == "REGISTERED"
    assert lookup_valid_body["owner_user_id"] is None

