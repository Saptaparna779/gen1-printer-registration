def _register_printer(client, serial_number="SN-GOAR-8-01", model_number="HP-C100", firmware_version="1.0.0"):
    response = client.post(
        "/printers/register",
        json={
            "serial_number": serial_number,
            "model_number": model_number,
            "firmware_version": firmware_version,
        },
    )
    assert response.status_code == 200
    return response.json()


def _claim_printer(client, claim_code, user_id):
    return client.post(
        "/printers/claim",
        json={"claim_code": claim_code, "user_id": user_id},
    )


def test_TC_GOAR_8_01_reject_claim_on_already_claimed_printer(client):
    registered_printer = _register_printer(client, serial_number="SN-GOAR-8-01")
    first_claim_response = _claim_printer(client, registered_printer["claim_code"], "owner-123")
    assert first_claim_response.status_code == 200

    second_claim_response = _claim_printer(client, registered_printer["claim_code"], "attacker-456")

    assert second_claim_response.status_code == 400
    assert second_claim_response.json() == {"detail": "Printer is already claimed"}

    printer_lookup = client.get(f"/printers/{registered_printer['printer_id']}")
    assert printer_lookup.status_code == 200
    assert printer_lookup.json()["status"] == "CLAIMED"
    assert printer_lookup.json()["owner_user_id"] == "owner-123"


def test_TC_GOAR_8_02_claim_registered_printer_with_valid_code(client):
    registered_printer = _register_printer(client, serial_number="SN-GOAR-8-02")

    response = _claim_printer(client, registered_printer["claim_code"], "user-123")

    assert response.status_code == 200
    assert response.json() == {
        "printer_id": registered_printer["printer_id"],
        "status": "CLAIMED",
        "owner_user_id": "user-123",
    }


def test_TC_GOAR_8_03_preserve_existing_owner_after_rejected_claim_attempt(client):
    registered_printer = _register_printer(client, serial_number="SN-GOAR-8-03")
    first_claim_response = _claim_printer(client, registered_printer["claim_code"], "owner-123")
    assert first_claim_response.status_code == 200

    rejected_claim_response = _claim_printer(client, registered_printer["claim_code"], "attacker-456")
    assert rejected_claim_response.status_code == 400
    assert rejected_claim_response.json() == {"detail": "Printer is already claimed"}

    printer_lookup = client.get(f"/printers/{registered_printer['printer_id']}")
    assert printer_lookup.status_code == 200
    assert printer_lookup.json() == {
        "printer_id": registered_printer["printer_id"],
        "serial_number": "SN-GOAR-8-03",
        "cloud_id": printer_lookup.json()["cloud_id"],
        "printer_email_id": printer_lookup.json()["printer_email_id"],
        "status": "CLAIMED",
        "owner_user_id": "owner-123",
        "xmpp_node": printer_lookup.json()["xmpp_node"],
        "history": printer_lookup.json()["history"],
    }


def test_TC_GOAR_8_04_reject_claim_for_claimed_printer_even_with_valid_unused_code(client):
    registered_printer = _register_printer(client, serial_number="SN-GOAR-8-04")
    first_claim_response = _claim_printer(client, registered_printer["claim_code"], "owner-123")
    assert first_claim_response.status_code == 200

    second_claim_response = _claim_printer(client, registered_printer["claim_code"], "attacker-456")

    assert second_claim_response.status_code == 400
    assert second_claim_response.json() == {"detail": "Printer is already claimed"}


def test_TC_GOAR_8_05_reject_claim_from_original_owner_and_other_user(client):
    registered_printer = _register_printer(client, serial_number="SN-GOAR-8-05")
    first_claim_response = _claim_printer(client, registered_printer["claim_code"], "owner-123")
    assert first_claim_response.status_code == 200

    first_rejection = _claim_printer(client, registered_printer["claim_code"], "owner-123")
    second_rejection = _claim_printer(client, registered_printer["claim_code"], "attacker-456")

    assert first_rejection.status_code == 400
    assert first_rejection.json() == {"detail": "Printer is already claimed"}
    assert second_rejection.status_code == 400
    assert second_rejection.json() == {"detail": "Printer is already claimed"}
