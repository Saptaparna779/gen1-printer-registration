"""
pytest-bdd step definitions for GOAR-3: re-registration must always
generate a new Cloud ID (per business rule 3/6), while Printer Email ID
and Claim Code regeneration, claimed-printer status/ownership, and
deregister-then-re-register behavior remain correct.

Mirrors tests/test_GOAR-3_generated.py's coverage of
reports/testcases/GOAR-3_test_cases.md, but expressed as Gherkin
scenarios (tests/features/GOAR-3.feature) for stakeholder readability.
Every step below makes real HTTP calls through the `client` fixture from
tests/conftest.py -- no internal app functions are called directly. All
test cases use a valid auth token, so no step overrides the
Authorization header.
"""
import re

from pytest_bdd import given, parsers, scenarios, then, when

scenarios("../features/GOAR-3.feature")

CLOUD_ID_PATTERN = re.compile(r"^CID-[A-F0-9]{12}$")
EMAIL_PATTERN = re.compile(r"^[a-z0-9]{10}@print\.hpeprint\.com$")
CLAIM_CODE_PATTERN = re.compile(r"^[A-Z0-9]{8}$")


def _post_register(client, serial, firmware="1.0.0", simulate_failure=None):
    payload = {
        "serial_number": serial,
        "model_number": "HP-M404",
        "firmware_version": firmware,
    }
    if simulate_failure is not None:
        payload["simulate_welcome_page_failure"] = simulate_failure
    return client.post("/printers/register", json=payload)


def _baseline_from_response(serial, response):
    body = response.json()
    return {
        "serial_number": serial,
        "printer_id": body["printer_id"],
        "cloud_id": body["cloud_id"],
        "printer_email_id": body["printer_email_id"],
        "claim_code": body["claim_code"],
    }


def _capture_result(context, response):
    body = response.json()
    context["response_status_code"] = response.status_code
    context["response_body"] = body
    context["new_printer_id"] = body.get("printer_id")
    context["new_cloud_id"] = body.get("cloud_id")
    context["new_status"] = body.get("status")
    context["new_printer_email_id"] = body.get("printer_email_id")
    context["new_claim_code"] = body.get("claim_code")
    return context


# ---------------------------------------------------------------------
# Given
# ---------------------------------------------------------------------


@given(
    parsers.parse('a printer has been registered with serial number "{serial}"'),
    target_fixture="context",
)
def printer_already_registered(client, serial):
    response = _post_register(client, serial)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "REGISTERED"
    return _baseline_from_response(serial, response)


@given(
    parsers.parse('no printer is registered yet for serial number "{serial}"'),
    target_fixture="context",
)
def no_printer_registered_yet(serial):
    return {"serial_number": serial}


@given(
    parsers.parse(
        'a printer has been registered with serial number "{serial}" '
        'and claimed by user "{user}"'
    ),
    target_fixture="context",
)
def printer_registered_and_claimed(client, serial, user):
    registered = _post_register(client, serial)
    assert registered.status_code == 200
    context = _baseline_from_response(serial, registered)

    claimed = client.post(
        "/printers/claim",
        json={"claim_code": context["claim_code"], "user_id": user},
    )
    assert claimed.status_code == 200
    claimed_body = claimed.json()
    assert claimed_body["status"] == "CLAIMED"
    assert claimed_body["owner_user_id"] == user
    context["owner_user_id"] = user
    return context


@given(
    parsers.parse(
        'a printer has been registered with serial number "{serial}", '
        "and a re-registration attempt for it failed and was rolled back"
    ),
    target_fixture="context",
)
def printer_registered_then_failed_reregistration(client, serial):
    registered = _post_register(client, serial)
    assert registered.status_code == 200
    context = _baseline_from_response(serial, registered)

    failed = _post_register(client, serial, simulate_failure=True)
    assert failed.status_code == 422
    return context


@given(
    parsers.parse(
        'a printer has been registered with serial number "{serial}" '
        "and then deregistered"
    ),
    target_fixture="context",
)
def printer_registered_then_deregistered(client, serial):
    registered = _post_register(client, serial)
    assert registered.status_code == 200
    context = _baseline_from_response(serial, registered)

    deregistered = client.delete(f"/printers/{context['printer_id']}")
    assert deregistered.status_code == 200
    assert deregistered.json() == {
        "status": "DEREGISTERED",
        "printer_id": context["printer_id"],
    }
    return context


# ---------------------------------------------------------------------
# When
# ---------------------------------------------------------------------


@when(parsers.parse('the printer is re-registered with the same serial number "{serial}"'))
def printer_reregistered(client, context, serial):
    response = _post_register(client, serial)
    _capture_result(context, response)


@when(
    parsers.parse(
        'the printer is re-registered with the same serial number "{serial}" '
        'and an updated firmware version "{firmware}"'
    )
)
def printer_reregistered_with_firmware(client, context, serial, firmware):
    response = _post_register(client, serial, firmware=firmware)
    _capture_result(context, response)


@when(
    parsers.parse(
        "the printer is registered three times in succession "
        'with serial number "{serial}"'
    )
)
def printer_registered_three_times(client, context, serial):
    cloud_ids = []
    for _ in range(3):
        response = _post_register(client, serial)
        assert response.status_code == 200
        cloud_ids.append(response.json()["cloud_id"])
    context["cloud_ids"] = cloud_ids


@when(
    parsers.parse(
        'the printer for serial number "{serial}" is re-registered '
        "with a simulated Welcome Page failure"
    )
)
def printer_reregistered_with_failure(client, context, serial):
    response = _post_register(client, serial, simulate_failure=True)
    context["response_status_code"] = response.status_code
    context["response_body"] = response.json()


# ---------------------------------------------------------------------
# Then
# ---------------------------------------------------------------------


@then(parsers.parse('the re-registration succeeds with status "{status}"'))
def reregistration_succeeds_with_status(context, status):
    assert context["new_status"] == status


@then("the new Cloud ID is different from the original Cloud ID")
def new_cloud_id_differs(context):
    assert context["response_status_code"] == 200
    assert CLOUD_ID_PATTERN.match(context["new_cloud_id"])
    assert context["new_cloud_id"] != context["cloud_id"]


@then("a new printer ID is issued, different from the original")
def new_printer_id_differs(context):
    assert context["new_printer_id"] != context["printer_id"]


@then("the printer email address is different from the original and follows the expected format")
def printer_email_differs(context):
    assert EMAIL_PATTERN.match(context["new_printer_email_id"])
    assert context["new_printer_email_id"] != context["printer_email_id"]


@then("the claim code is different from the original and follows the expected format")
def claim_code_differs(context):
    assert CLAIM_CODE_PATTERN.match(context["new_claim_code"])
    assert context["new_claim_code"] != context["claim_code"]


@then(
    parsers.parse(
        'looking up the printer shows its owner is still "{user}" '
        'and its status is still "CLAIMED"'
    )
)
def owner_and_status_unchanged(client, context, user):
    lookup = client.get(f"/printers/{context['printer_id']}")
    assert lookup.status_code == 200
    body = lookup.json()
    assert body["owner_user_id"] == user
    assert body["status"] == "CLAIMED"


@then("all three Cloud IDs returned are different from one another")
def three_cloud_ids_distinct(context):
    cloud_id_1, cloud_id_2, cloud_id_3 = context["cloud_ids"]
    for cloud_id in (cloud_id_1, cloud_id_2, cloud_id_3):
        assert CLOUD_ID_PATTERN.match(cloud_id)
    assert cloud_id_1 != cloud_id_2
    assert cloud_id_2 != cloud_id_3
    assert cloud_id_1 != cloud_id_3


@then("the Cloud ID from the second re-registration is different from the very first Cloud ID")
def third_cloud_id_differs_from_first(context):
    cloud_id_1 = context["cloud_ids"][0]
    cloud_id_3 = context["cloud_ids"][2]
    assert cloud_id_3 != cloud_id_1


@then("the re-registration fails with a Welcome Page print error and the printer record is fully removed")
def reregistration_rolled_back(client, context):
    assert context["response_status_code"] == 422
    expected_detail = f"Welcome page failed to print for printer_id={context['printer_id']}"
    assert context["response_body"]["detail"] == expected_detail

    lookup = client.get(f"/printers/{context['printer_id']}")
    assert lookup.status_code == 404
    assert lookup.json()["detail"] == "Printer not found"
