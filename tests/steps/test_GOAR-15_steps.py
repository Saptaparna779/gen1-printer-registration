"""
pytest-bdd step definitions for GOAR-15: re-registration must flag/log any
model_number change and reject a materially different model family, while
matching or compatible re-registrations (including for claimed printers)
keep succeeding as before.

Mirrors tests/test_GOAR-15_generated.py's coverage of
reports/testcases/GOAR-15_test_cases.md, but expressed as Gherkin
scenarios (tests/features/GOAR-15.feature) for stakeholder readability.
Every step below makes real HTTP calls through the `client` fixture from
tests/conftest.py -- no internal app functions are called directly.
"""
import logging

from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when

from app.main import app

scenarios("../features/GOAR-15.feature")


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------


def _no_auth_client() -> TestClient:
    """
    A TestClient with no Authorization header pre-attached. Used for
    "missing token" steps, since the `client` fixture always attaches a
    valid token by default.
    """
    return TestClient(app)


def _register(client, serial_number, model_number, firmware_version):
    return client.post(
        "/printers/register",
        json={
            "serial_number": serial_number,
            "model_number": model_number,
            "firmware_version": firmware_version,
        },
    )


def _claim(client, claim_code, user_id):
    return client.post(
        "/printers/claim",
        json={"claim_code": claim_code, "user_id": user_id},
    )


# ---------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------


@given(
    parsers.parse(
        'a printer has been registered with serial number "{serial}", '
        'model number "{model}", and firmware version "{firmware}"'
    ),
    target_fixture="context",
)
def printer_already_registered(client, serial, model, firmware):
    response = _register(client, serial, model, firmware)
    assert response.status_code == 200
    body = response.json()
    return {
        "serial_number": serial,
        "model_number": model,
        "firmware_version": firmware,
        "printer_id": body["printer_id"],
        "cloud_id": body["cloud_id"],
        "printer_email_id": body["printer_email_id"],
        "claim_code": body["claim_code"],
        "xmpp_node": body["xmpp_node"],
        "history": body["history"],
    }


@given(
    parsers.parse(
        'a printer has been registered and claimed: serial number "{serial}", '
        'model number "{model}", and firmware version "{firmware}", '
        'claimed by user "{user}"'
    ),
    target_fixture="context",
)
def printer_registered_and_claimed(client, serial, model, firmware, user):
    registered = _register(client, serial, model, firmware)
    assert registered.status_code == 200
    reg_body = registered.json()

    claimed = _claim(client, reg_body["claim_code"], user)
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == user

    return {
        "serial_number": serial,
        "model_number": model,
        "firmware_version": firmware,
        "printer_id": reg_body["printer_id"],
        "cloud_id": reg_body["cloud_id"],
        "printer_email_id": reg_body["printer_email_id"],
        "xmpp_node": reg_body["xmpp_node"],
        "history": reg_body["history"],
        "owner_user_id": user,
    }


# ---------------------------------------------------------------------
# When
# ---------------------------------------------------------------------


@when(
    parsers.parse(
        'the printer is re-registered with serial number "{serial}", '
        'model number "{model}", and firmware version "{firmware}"'
    )
)
def printer_reregistered(client, context, caplog, serial, model, firmware):
    with caplog.at_level(logging.WARNING, logger="app.registration"):
        response = _register(client, serial, model, firmware)
    body = response.json()
    context["response_status_code"] = response.status_code
    context["response_body"] = body
    context["new_status"] = body.get("status")
    context["new_cloud_id"] = body.get("cloud_id")
    context["new_printer_email_id"] = body.get("printer_email_id")
    context["new_xmpp_node"] = body.get("xmpp_node")
    context["warning_records"] = [r for r in caplog.records if r.levelno == logging.WARNING]


@when(
    parsers.parse(
        'a registration request for serial number "{serial}" is submitted with no Authorization header'
    ),
    target_fixture="context",
)
def registration_request_no_auth_header(serial):
    response = _register(_no_auth_client(), serial, "HP-LJ-4200", "1.0.0")
    return {"response_status_code": response.status_code, "response_body": response.json()}


@when(
    parsers.parse(
        'a registration request for serial number "{serial}" is submitted '
        "with an invalid Authorization token"
    ),
    target_fixture="context",
)
def registration_request_invalid_token(client, serial):
    response = client.post(
        "/printers/register",
        json={"serial_number": serial, "model_number": "HP-LJ-4200", "firmware_version": "1.0.0"},
        headers={"Authorization": "Bearer not-a-real-jwt-token"},
    )
    return {"response_status_code": response.status_code, "response_body": response.json()}


@when("a claim request is submitted with no Authorization header", target_fixture="context")
def claim_request_no_auth_header():
    response = _claim(_no_auth_client(), "ABCD1234", "user-goar15-x")
    return {"response_status_code": response.status_code, "response_body": response.json()}


@when("a claim request is submitted with an invalid Authorization token", target_fixture="context")
def claim_request_invalid_token(client):
    response = client.post(
        "/printers/claim",
        json={"claim_code": "ABCD1234", "user_id": "user-goar15-x"},
        headers={"Authorization": "Bearer not-a-real-jwt-token"},
    )
    return {"response_status_code": response.status_code, "response_body": response.json()}


@when("looking up that printer with no Authorization header")
def lookup_printer_no_auth_header(context):
    response = _no_auth_client().get(f"/printers/{context['printer_id']}")
    context["response_status_code"] = response.status_code
    context["response_body"] = response.json()


@when("looking up that printer with an invalid Authorization token")
def lookup_printer_invalid_token(client, context):
    response = client.get(
        f"/printers/{context['printer_id']}",
        headers={"Authorization": "Bearer not-a-real-jwt-token"},
    )
    context["response_status_code"] = response.status_code
    context["response_body"] = response.json()


# ---------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------


@then("the re-registration succeeds")
def reregistration_succeeds(context):
    assert context["response_status_code"] == 200


@then(
    parsers.parse(
        'the registration history records the model number change from "{old}" to "{new}" '
        "and flags it for review"
    )
)
def history_records_model_change(context, old, new):
    history_text = " | ".join(context["response_body"]["history"])
    assert "GOAR-15: model_number changed on re-registration" in history_text
    assert f"old={old}" in history_text
    assert f"new={new}" in history_text
    assert "flagged for review" in history_text


@then(
    parsers.parse(
        'a warning is logged mentioning serial number "{serial}", old model "{old}", '
        'and new model "{new}"'
    )
)
def warning_logged_message(context, serial, old, new):
    assert any(
        serial in r.getMessage() and old in r.getMessage() and new in r.getMessage()
        for r in context["warning_records"]
    )


@then(
    "the registration history shows no model number change and no flag for review, "
    "only the standard re-registration entries"
)
def history_shows_no_model_change(context):
    history_text = " | ".join(context["response_body"]["history"])
    assert "model_number changed" not in history_text
    assert "flagged for review" not in history_text
    assert "Re-registration started" in history_text


@then("no warning is logged")
def no_warning_logged(context):
    assert context["warning_records"] == []


@then(
    parsers.parse(
        'the re-registration is rejected as a model family mismatch between "{existing}" and "{incoming}"'
    )
)
def reregistration_rejected_family_mismatch(context, existing, incoming):
    assert context["response_status_code"] == 422
    assert context["response_body"]["detail"] == (
        "Re-registration rejected: model family mismatch "
        f"(existing='{existing}', incoming='{incoming}'). "
        "This looks like a different physical device reusing the same serial number."
    )


@then(parsers.parse('the re-registration outcome is "{outcome}"'))
def reregistration_outcome(context, outcome):
    if outcome == "accepted":
        assert context["response_status_code"] == 200
    else:
        assert context["response_status_code"] == 422
        assert "model family mismatch" in context["response_body"]["detail"]


@then("the re-registration succeeds with a new Cloud ID different from the original")
def reregistration_new_cloud_id(context):
    assert context["response_status_code"] == 200
    assert context["new_cloud_id"]
    assert context["new_cloud_id"] != context["cloud_id"]


@then("a new printer email address is issued, different from the original")
def new_printer_email_issued(context):
    assert context["new_printer_email_id"]
    assert context["new_printer_email_id"] != context["printer_email_id"]


@then("an XMPP node is assigned")
def xmpp_node_assigned(context):
    assert context["new_xmpp_node"]


@then(parsers.parse('the printer status is "{status}"'))
def printer_status_is(context, status):
    assert context["new_status"] == status


@then(
    "the registration history shows capability capture, XMPP assignment, and a successful "
    "welcome page print, with no model-number flag"
)
def history_shows_full_registration_steps(context):
    history_text = " | ".join(context["response_body"]["history"])
    assert "Capabilities" in history_text
    assert "XMPP node assigned" in history_text
    assert "Welcome page printed successfully; registration complete" in history_text
    assert "flagged for review" not in history_text


@then("a new Cloud ID is present")
def new_cloud_id_present(context):
    assert context["new_cloud_id"]


@then(
    parsers.parse(
        'looking up the printer shows its owner is still "{user}" and status is still "CLAIMED"'
    )
)
def owner_and_status_unchanged(client, context, user):
    lookup = client.get(f"/printers/{context['printer_id']}")
    assert lookup.status_code == 200
    body = lookup.json()
    assert body["owner_user_id"] == user
    assert body["status"] == "CLAIMED"


@then("the request is rejected as missing the authorization header")
def request_rejected_missing_auth_header(context):
    assert context["response_status_code"] == 422
    detail = context["response_body"]["detail"]
    assert any(
        item.get("loc") == ["header", "authorization"] and item.get("msg") == "Field required"
        for item in detail
    )


@then("the request is rejected as unauthorized due to an invalid token")
def request_rejected_invalid_token(context):
    assert context["response_status_code"] == 401
    assert context["response_body"] == {"detail": "Invalid or expired token"}


@then(
    parsers.parse(
        'a warning log record has discrete fields serial_number "{serial}", '
        'old_model "{old}", and new_model "{new}"'
    )
)
def warning_log_has_discrete_fields(context, serial, old, new):
    matching = [
        r
        for r in context["warning_records"]
        if getattr(r, "serial_number", None) == serial
        and getattr(r, "old_model", None) == old
        and getattr(r, "new_model", None) == new
    ]
    assert matching, "expected a WARNING record with discrete serial_number/old_model/new_model attributes"


@then("a warning is logged for this event")
def warning_logged_for_event(context):
    assert context["warning_records"]


@then("looking up the printer shows only the review-flag entry was added and the Cloud ID is unchanged")
def lookup_shows_only_flag_entry_added(client, context):
    lookup = client.get(f"/printers/{context['printer_id']}")
    assert lookup.status_code == 200
    body = lookup.json()
    original_history = context["history"]

    assert body["cloud_id"] == context["cloud_id"]
    assert body["history"][: len(original_history)] == original_history
    assert len(body["history"]) == len(original_history) + 1
    assert "flagged for review" in body["history"][-1]
    for marker in ("Cloud identity created", "Capabilities captured", "XMPP node assigned", "Welcome page printed"):
        assert marker not in body["history"][-1]


@then(
    "looking up the printer confirms no Cloud ID, printer email, or XMPP node changes occurred "
    "and no side-effect entries were added"
)
def lookup_confirms_zero_side_effects(client, context):
    lookup = client.get(f"/printers/{context['printer_id']}")
    assert lookup.status_code == 200
    body = lookup.json()
    original_history = context["history"]

    assert body["cloud_id"] == context["cloud_id"]
    assert body["printer_email_id"] == context["printer_email_id"]
    assert body["xmpp_node"] == context["xmpp_node"]

    assert body["history"][: len(original_history)] == original_history
    assert len(body["history"]) == len(original_history) + 1
    assert "flagged for review" in body["history"][-1]
    for marker in (
        "Cloud identity created",
        "Capabilities captured",
        "Capabilities already on record",
        "XMPP node assigned",
        "Welcome page printed",
    ):
        assert marker not in body["history"][-1]
