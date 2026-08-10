# Test Cases: GOAR-8

## TC-GOAR-8-01

| Field | Value |
|---|---|
| Test ID | TC-GOAR-8-01 |
| Jira Story | GOAR-8 |
| Maps to AC # | 1 |
| Test Type | API |
| Scenario | Reject a claim attempt on a printer that is already claimed by a different user |
| Preconditions | A printer has already been registered and successfully claimed by owner-123; printer status is CLAIMED |
| Endpoint | /printers/claim |
| HTTP Method | POST |
| Test Data | {"claim_code": "<existing-claimed-printer-claim-code>", "user_id": "attacker-456"} |
| Expected Status | 400 |
| Expected Response | {"detail": "Printer is already claimed"}; existing ownership (owner-123) remains unchanged |
| Automation Framework | pytest |
| Automation Code | tests/test_GOAR-8_generated.py::test_TC_GOAR_8_01_reject_claim_on_already_claimed_printer |
| Expected Result | Pass |

## TC-GOAR-8-02

| Field | Value |
|---|---|
| Test ID | TC-GOAR-8-02 |
| Jira Story | GOAR-8 |
| Maps to AC # | 2 |
| Test Type | API |
| Scenario | Claim an unclaimed printer with a valid, unused claim code -- should still succeed |
| Preconditions | A printer has been registered and is in status REGISTERED, with a valid unused claim code |
| Endpoint | /printers/claim |
| HTTP Method | POST |
| Test Data | {"claim_code": "<valid-unused-claim-code>", "user_id": "user-123"} |
| Expected Status | 200 |
| Expected Response | {"printer_id": "<printer-id>", "status": "CLAIMED", "owner_user_id": "user-123"} |
| Automation Framework | pytest |
| Automation Code | tests/test_GOAR-8_generated.py::test_TC_GOAR_8_02_claim_registered_printer_with_valid_code |
| Expected Result | Pass |

## TC-GOAR-8-03

| Field | Value |
|---|---|
| Test ID | TC-GOAR-8-03 |
| Jira Story | GOAR-8 |
| Maps to AC # | 3 |
| Test Type | API |
| Scenario | Confirm existing owner is preserved after a rejected claim attempt |
| Preconditions | A printer has already been claimed by owner-123; printer status is CLAIMED |
| Endpoint | Step 1: POST /printers/claim; Step 2: GET /printers/{printer_id} |
| HTTP Method | POST, then GET |
| Test Data | Step 1: {"claim_code": "<existing-claimed-printer-claim-code>", "user_id": "attacker-456"} |
| Expected Status | Step 1: 400; Step 2: 200 |
| Expected Response | Step 1: {"detail": "Printer is already claimed"}; Step 2: printer resource shows owner_user_id "owner-123", status "CLAIMED" |
| Automation Framework | pytest |
| Automation Code | tests/test_GOAR-8_generated.py::test_TC_GOAR_8_03_preserve_existing_owner_after_rejected_claim_attempt |
| Expected Result | Pass |

## TC-GOAR-8-04

| Field | Value |
|---|---|
| Test ID | TC-GOAR-8-04 |
| Jira Story | GOAR-8 |
| Maps to AC # | 4 |
| Test Type | API |
| Scenario | Reject a claim attempt on an already-claimed printer even when the supplied code is otherwise valid and unused |
| Preconditions | A printer exists in status CLAIMED with a valid, unused claim code associated |
| Endpoint | /printers/claim |
| HTTP Method | POST |
| Test Data | {"claim_code": "<valid-unused-claim-code-for-claimed-printer>", "user_id": "attacker-456"} |
| Expected Status | 400 |
| Expected Response | {"detail": "Printer is already claimed"} |
| Automation Framework | pytest |
| Automation Code | tests/test_GOAR-8_generated.py::test_TC_GOAR_8_04_reject_claim_for_claimed_printer_even_with_valid_unused_code |
| Expected Result | Pass |

## TC-GOAR-8-05

| Field | Value |
|---|---|
| Test ID | TC-GOAR-8-05 |
| Jira Story | GOAR-8 |
| Maps to AC # | 5 |
| Test Type | API |
| Scenario | Reject a claim attempt identically whether it comes from the original owner or a different user |
| Preconditions | A printer has already been claimed by owner-123; printer status is CLAIMED |
| Endpoint | /printers/claim (called twice) |
| HTTP Method | POST |
| Test Data | Call 1: {"claim_code": "<code>", "user_id": "owner-123"}; Call 2: {"claim_code": "<code>", "user_id": "attacker-456"} |
| Expected Status | 400 for both calls |
| Expected Response | {"detail": "Printer is already claimed"} for both calls |
| Automation Framework | pytest |
| Automation Code | tests/test_GOAR-8_generated.py::test_TC_GOAR_8_05_reject_claim_from_original_owner_and_other_user |
| Expected Result | Pass |
