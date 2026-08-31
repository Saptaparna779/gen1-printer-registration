# Test Cases — GOAR-15

## TC-GOAR-15-01: Same-family model change accepted with full registration outputs

Scenario: [HAPPY PATH] Successful re-registration where the normalized model_number changes within the same model family is accepted and produces new Cloud ID, printer email ID, and claim code as per existing rules.  
           Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration has completed successfully for `serial_number = "SN-GOAR15-001"` with `model_number = "HP-LJ-2055"` and `firmware_version = "1.0.0"`, using `simulate_welcome_page_failure = false`.
- From the initial `POST /printers/register` response, capture: `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.
- The printer currently has `status == "REGISTERED"` and no `owner_user_id` (verified via `GET /printers/{printer_id_initial}` if needed).

Request:
  Headers: use default client headers (Authorization automatically set with a valid bearer token).
  Body: `{"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` is a non-empty string starting with `"CID-"` and `cloud_id != cloud_id_initial`.
  - `printer_email_id` is a non-empty string ending with `"@print.hpeprint.com"` and `printer_email_id != printer_email_id_initial`.
  - `claim_code` is an 8-character alphanumeric string; `claim_code_expires_at` is an ISO 8601 timestamp strictly later than the current time at assertion.
  - `xmpp_node` is a non-empty string (may equal the previous XMPP node if one was already assigned, but must not be empty).
  - `status` == "REGISTERED".
  - `history` includes at least:
    - An entry containing `"GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-LJ-2060) -- flagged for review"`.
    - An entry containing `"Re-registration started"` for this call.
    - An entry containing `"Cloud identity created:"` for this call.
    - An entry containing `"Welcome page printed successfully; registration complete"` for this call.

Notes: Agent 4 must implement preconditions by first calling `POST /printers/register` with `{"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}` and capturing the response. Use `caplog` around the second registration call to assert a `logging.WARNING` record from logger `app.registration` whose message contains `"GOAR-15: model_number changed on re-registration"` and whose `record.serial_number == "SN-GOAR15-001"`, `record.old_model == "HP-LJ-2055"`, `record.new_model == "HP-LJ-2060"`.

---

## TC-GOAR-15-02: Case/whitespace-only model difference treated as unchanged

Scenario: [BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading/trailing whitespace is treated as unchanged after normalization and does not trigger a model-change flag or warning log.  
           Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer is already registered with `serial_number = "SN-GOAR15-002"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, and `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial` from the initial registration response.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-002", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` starts with `"CID-"` and `cloud_id != cloud_id_initial`.
  - `printer_email_id` ends with `"@print.hpeprint.com"` and `printer_email_id != printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` entries for this call do NOT include any string starting with `"GOAR-15: model_number changed on re-registration"`.

Notes: Use `caplog` at WARNING level around the second registration call and assert that there is no log record whose message contains `"GOAR-15: model_number changed on re-registration"`. This ensures normalization avoids spurious warnings. No rollback or additional GET calls are required beyond precondition setup.

---

## TC-GOAR-15-03: Different-family model change rejected with unchanged cloud identity

Scenario: [ROLLBACK] Re-registration where the normalized model_number changes and resolves to a different model family is rejected and leaves Cloud ID, printer email ID, XMPP node, capabilities, and ownership unchanged apart from the review history entry and warning log.  
           Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-003"` succeeded with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, and `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial` via `GET /printers/{printer_id_initial}`.
- Confirm capabilities exist for this printer via a helper that calls `store.get_capabilities(printer_id_initial)` (used in assertions by Agent 4).

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-003", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- Call `GET /printers/{printer_id_initial}` with valid auth.
- Response status: 200.
- Body contains:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == "REGISTERED".
  - `serial_number` == "SN-GOAR15-003".
  - `history` includes all prior entries plus exactly one new entry containing `"GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"`; no new entries indicating a fresh cloud identity or welcome-page success should appear for the failed attempt.
- Using store helpers, assert that capabilities for `printer_id_initial` still exist and are unchanged.

Notes: This is a rollback test. Agent 4 must capture pre-state via `GET /printers/{printer_id_initial}` before performing the failing POST, then compare to the post-state. Use `caplog` to assert a WARNING log from `app.registration` with `serial_number = "SN-GOAR15-003"`, `old_model = "HP-LJ-2055"`, and `new_model = "HP-C-MFP-9999"`. No explicit `reset_store` call is required for rollback.

---

## TC-GOAR-15-04: Different-family re-registration rejected with RegistrationError and unchanged state

Scenario: [INVALID INPUT] Re-registration attempt for an already-registered serial_number with a clearly different-family model_number is rejected with RegistrationError and no registration-side effects occur.  
           Requirement: AC2

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer exists with `serial_number = "SN-GOAR15-004"`, `model_number = "HP-LJ-2055"`, and `firmware_version = "1.0.0"`, created via a successful registration.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `xmpp_node_initial` via `GET /printers/{printer_id_initial}`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-004", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- `GET /printers/{printer_id_initial}` returns status 200.
- Body has:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == "REGISTERED".
  - `history` includes a GOAR-15 model-change entry but no additional registration-complete entry for this attempt.

Notes: Functionally similar to TC-GOAR-15-03 but keyed to AC2. Agent 4 can reuse helpers for pre/post comparisons and the WARNING log assertion. No rollback beyond the internal `_rollback_registration` needed.

---

## TC-GOAR-15-05: Edge heuristic classification between model families

Scenario: [BOUNDARY VALUE] Re-registration where the new model_number sits on the edge of the same-family vs different-family heuristic (changing only the last dash-separated segment) is correctly classified and either accepted or rejected with appropriate logging.  
           Requirement: AC2

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration succeeded for `serial_number = "SN-GOAR15-005"` with `model_number = "HP-LJ-2055"` and `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-005", "model_number": "HP-LJ-4250", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial` and starts with `"CID-"`.
  - `printer_email_id` != `printer_email_id_initial` and ends with `"@print.hpeprint.com"`.
  - `status` == "REGISTERED".
  - `history` includes a GOAR-15 model-change entry for `old=HP-LJ-2055`, `new=HP-LJ-4250`.

Notes: `_model_family("HP-LJ-2055")` and `_model_family("HP-LJ-4250")` both return `"HP-LJ"`, so this boundary test confirms that same-family but different last segment is accepted, while still logging the model-number change. Use `caplog` to assert the expected WARNING log. This scenario must not assert rejection.

---

## TC-GOAR-15-06: Rejected different-family re-registration leaves identity and capabilities intact

Scenario: [ROLLBACK] Rejected different-family re-registration does not create or alter any Cloud ID, printer email ID, XMPP node, capabilities record, or serial index, confirming full rollback on the GOAR-15 rejection path.  
           Requirement: AC2

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer is registered for `serial_number = "SN-GOAR15-006"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture pre-state using `GET /printers/{printer_id_initial}`: `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, `status_initial`, and `history_initial`.
- Confirm via helper that capabilities exist for `printer_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-006", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` identical to TC-GOAR-15-03 (model family mismatch message).

Post-action state verification:
- `GET /printers/{printer_id_initial}` still returns status 200.
- Body fields:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == `status_initial` (expected "REGISTERED").
- Capabilities: `store.get_capabilities(printer_id_initial)` returns a record identical to pre-state.
- Serial index: helper assertions confirm that `store.get_printer_by_serial("SN-GOAR15-006")` still returns `printer_id_initial`.

Notes: This rollback-focused test is similar to TC-GOAR-15-03/04 but explicitly adds capabilities and serial-index checks. Ensure Agent 4 implements helper utilities for interacting with `store` in a black-box-compatible way (e.g., via fixtures). Use `caplog` to confirm the warning log is present.

---

## TC-GOAR-15-07: Re-registration with identical identity fields succeeds with new Cloud ID and email

Scenario: [HAPPY PATH] Re-registration with identical model_number and firmware_version succeeds and generates a new Cloud ID, printer email ID, and claim code while preserving ownership and visibility.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer has been registered with `serial_number = "SN-GOAR-15-007"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `status_initial` (expected "REGISTERED"), and `history_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR-15-007", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial` and matches pattern `"CID-"` + 12 uppercase hex characters.
  - `printer_email_id` != `printer_email_id_initial` and matches `[a-z0-9]{10}@print.hpeprint.com`.
  - `status` == "REGISTERED".
  - `history` includes new entries for this re-registration: `"Re-registration started"`, `"Cloud identity created:"`, and `"Welcome page printed successfully; registration complete"`.

Notes: This control test confirms that GOAR-15 did not break the baseline GOAR-3 behavior for re-registration without model changes. No rollback is involved.

---

## TC-GOAR-15-08: Re-registration with updated firmware on claimed printer preserves ownership

Scenario: [HAPPY PATH] Re-registration with identical model_number but updated firmware_version succeeds, regenerates Cloud ID and printer email ID, and updates stored firmware_version without introducing additional validation.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR-15-008"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture the claim code from the registration response.
- Claim the printer via `POST /printers/claim` with `{"claim_code": <captured_claim_code>, "user_id": "user-goar15-owner"}`.
- Confirm via `GET /printers/{printer_id}` that `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner"`. Capture `printer_id_claimed`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR-15-008", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_claimed`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".

Post-action ownership verification:
- `GET /printers/{printer_id_claimed}` returns `owner_user_id == "user-goar15-owner"` and `status == "CLAIMED"`.

Notes: This test confirms firmware changes alone do not affect ownership or claim status and that firmware is not being specially validated in GOAR-15.

---

## TC-GOAR-15-09: Welcome-page failure during re-registration triggers full rollback

Scenario: [ROLLBACK] Failed re-registration due to a non-GOAR-15 pre–Welcome-Page error rolls back fully and leaves prior Cloud ID, printer email ID, XMPP node, capabilities, and ownership state unchanged.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial successful registration for `serial_number = "SN-GOAR15-009"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and confirm capabilities exist.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-009", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == `"Welcome page failed to print for printer_id=" + printer_id_initial`.

Post-action state verification:
- `GET /printers/{printer_id_initial}` returns status 404 with body `{"detail": "Printer not found"}`.

Notes: This verifies that `_rollback_registration` removes the printer record, serial index, and capabilities. Agent 4 must construct the expected `detail` string from the captured `printer_id_initial`.

---

## TC-GOAR-15-10: Normalized case/whitespace comparison avoids model-change warning

Scenario: [HAPPY PATH] Re-registration where old and new model_number differ only in case and/or leading/trailing whitespace is treated as the same model after normalization and does not append a GOAR-15 model-change history entry or emit a warning log.  
           Requirement: AR1

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-010"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` completed successfully.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-010", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` contains no new entry starting with `"GOAR-15: model_number changed on re-registration"`.

Notes: Use `caplog` to ensure no WARNING log for GOAR-15 model-number change is emitted. This test is similar to TC-GOAR-15-02 but mapped to AR1.

---

## TC-GOAR-15-11: Normalization collision treated consistently as unchanged

Scenario: [BOUNDARY VALUE] Re-registration where normalization causes two visually distinct model_number strings to collide (e.g., extra internal spaces or mixed case) is still treated consistently as unchanged and avoids spurious spoofing flags.  
           Requirement: AR1

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer exists with `serial_number = "SN-GOAR15-011"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: `{"serial_number": "SN-GOAR15-011", "model_number": "HP  -lj-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - No GOAR-15 model-change warning entry in `history`.

Notes: Even though `