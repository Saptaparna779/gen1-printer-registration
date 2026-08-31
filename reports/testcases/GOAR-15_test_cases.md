# Test Cases — GOAR-15

## TC-GOAR-15-01: Same-family model change accepted with full registration outputs

Scenario: [HAPPY PATH] Same-serial re-registration where the normalized model_number changes within the same model family succeeds, generates new Cloud identity (Cloud ID, printer email ID, and claim code if applicable), and records a GOAR-15 history entry plus WARNING log.  
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
  Body: {"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

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
    - An entry containing `"Cloud identity created: "` for this call.
    - An entry containing `"Welcome page printed successfully; registration complete"` for this call.

Notes: Agent 4 must implement preconditions by first calling `POST /printers/register` with {"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false} and capturing the response. Use `caplog` around the second registration call to assert a `logging.WARNING` record from logger `app.registration` whose message contains `"GOAR-15: model_number changed on re-registration"` and whose `record.serial_number == "SN-GOAR15-001"`, `record.old_model == "HP-LJ-2055"`, `record.new_model == "HP-LJ-2060"`.

---

## TC-GOAR-15-02: Case/whitespace-only model difference treated as unchanged

Scenario: [BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading/trailing whitespace is treated as unchanged after normalization and therefore does not append a GOAR-15 history entry or emit a model-change WARNING log.  
           Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer is already registered with `serial_number = "SN-GOAR15-002"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, and `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial` from the initial registration response.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-002", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

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

Scenario: [ROLLBACK] Re-registration where the normalized model_number change leads to a different model family is rejected, appends a GOAR-15 history entry and WARNING log, and leaves all persisted printer identity fields (Cloud ID, printer email ID, firmware_version, capabilities, XMPP node, ownership) unchanged.  
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
  Body: {"serial_number": "SN-GOAR15-003", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

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

Scenario: [INVALID INPUT] Re-registration attempt for an already-registered serial_number with a clearly different-family normalized model_number is rejected with RegistrationError and translated to HTTP 422 by POST /printers/register, with no registration-side effects.  
           Requirement: AC2

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer exists with `serial_number = "SN-GOAR15-004"`, `model_number = "HP-LJ-2055"`, and `firmware_version = "1.0.0"`, created via a successful registration.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `xmpp_node_initial` via `GET /printers/{printer_id_initial}`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-004", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

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

## TC-GOAR-15-05: Same-family heuristic boundary accepted and logged

Scenario: [BOUNDARY VALUE] Re-registration where the new normalized model_number differs only in the last dash-separated segment (same prefix family) is classified as same-family and accepted, whereas a change in the prefix segments is classified as different-family and rejected.  
           Requirement: AC2

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration succeeded for `serial_number = "SN-GOAR15-005"` with `model_number = "HP-LJ-2055"` and `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-005", "model_number": "HP-LJ-4250", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial` and starts with "CID-".
  - `printer_email_id` != `printer_email_id_initial` and ends with "@print.hpeprint.com".
  - `status` == "REGISTERED".
  - `history` includes a GOAR-15 model-change entry for `old=HP-LJ-2055`, `new=HP-LJ-4250`.

Notes: `_model_family("HP-LJ-2055")` and `_model_family("HP-LJ-4250")` both return "HP-LJ", so this boundary test confirms that same-family but different last segment is accepted, while still logging the model-number change. Use `caplog` to assert the expected WARNING log. This scenario must not assert rejection.

---

## TC-GOAR-15-06: Different-family rejection path leaves identity and capabilities intact

Scenario: [ROLLBACK] Different-family re-registration rejection path leaves Cloud ID, printer email ID, capabilities, XMPP node, serial index, and ownership state identical to the pre-attempt state, confirming full rollback for the GOAR-15 gate.  
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
  Body: {"serial_number": "SN-GOAR15-006", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- `GET /printers/{printer_id_initial}` still returns status 200.
- Body fields:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == `status_initial` (expected "REGISTERED").
- Capabilities: `store.get_capabilities(printer_id_initial)` returns a record identical to pre-state.
- Serial index: helper assertions confirm that `store.get_printer_by_serial("SN-GOAR15-006")` still returns the same printer.

Notes: This rollback-focused test is similar to TC-GOAR-15-03/04 but explicitly adds capabilities and serial-index checks. Ensure Agent 4 implements helper utilities for interacting with `store` in a black-box-compatible way (e.g., via fixtures). Use `caplog` to confirm the warning log is present.

---

## TC-GOAR-15-07: Re-registration with identical identity fields succeeds with new Cloud ID and email

Scenario: [HAPPY PATH] Re-registration with identical normalized model_number and unchanged firmware_version succeeds and generates a new Cloud ID, printer email ID, and (if unclaimed) claim code while preserving ownership and visibility semantics.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer has been registered with `serial_number = "SN-GOAR15-007"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `status_initial` (expected "REGISTERED"), and `history_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-007", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial` and matches pattern `CID-` followed by 12 uppercase hexadecimal characters.
  - `printer_email_id` != `printer_email_id_initial` and matches pattern `[a-z0-9]{10}@print.hpeprint.com`.
  - `status` == "REGISTERED".
  - `history` includes new entries for this re-registration: "Re-registration started", "Cloud identity created: ", and "Welcome page printed successfully; registration complete".

Notes: This control test confirms that GOAR-15 did not break the baseline GOAR-3 behavior for re-registration without model changes. No rollback is involved.

---

## TC-GOAR-15-08: Re-registration with updated firmware succeeds and preserves ownership

Scenario: [HAPPY PATH] Re-registration with identical normalized model_number but updated firmware_version succeeds, regenerates Cloud ID and printer email ID, updates stored firmware_version, and does not introduce additional firmware-specific validation or logging.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-008"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture the claim code and `printer_id_initial` from the registration response.
- Claim the printer via `POST /printers/claim` with body {"claim_code": <captured_claim_code>, "user_id": "user-goar15-owner"}.
- Confirm via `GET /printers/{printer_id_initial}` that `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner"`. Capture `cloud_id_initial` and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-008", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".

Post-action ownership verification:
- `GET /printers/{printer_id_initial}` returns `owner_user_id == "user-goar15-owner"` and `status == "CLAIMED"`.

Notes: This test confirms firmware changes alone do not affect ownership or claim status and that firmware is not being specially validated in GOAR-15.

---

## TC-GOAR-15-09: Welcome-page failure during re-registration triggers full rollback

Scenario: [ROLLBACK] Failed re-registration due to a non-GOAR-15 pre–Welcome-Page error (e.g., welcome-page print failure) rolls back fully and leaves prior Cloud ID, printer email ID, XMPP node, capabilities, serial index, and ownership state unchanged.  
           Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial successful registration for `serial_number = "SN-GOAR15-009"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`, `simulate_welcome_page_failure = false`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and confirm capabilities exist.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-009", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Welcome page failed to print for printer_id=" followed by `printer_id_initial`.

Post-action state verification:
- `GET /printers/{printer_id_initial}` returns status 404 with body {"detail": "Printer not found"}.

Notes: This verifies that `_rollback_registration` removes the printer record, serial index, and capabilities. Agent 4 must construct the expected `detail` string from the captured `printer_id_initial`.

---

## TC-GOAR-15-10: Normalized case/whitespace comparison avoids model-change warning

Scenario: [BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading/trailing whitespace is treated as unchanged after normalization and therefore does not append a GOAR-15 history entry or emit a model-change WARNING log.  
           Requirement: AR1

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-010"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` completed successfully.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-010", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` contains no new entry starting with "GOAR-15: model_number changed on re-registration".

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
  Body: {"serial_number": "SN-GOAR15-011", "model_number": "HP-LJ-2055   ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - No GOAR-15 model-change warning entry in `history`.

Notes: Use `caplog` to confirm that no WARNING log with "GOAR-15: model_number changed on re-registration" is emitted. This ensures normalization behavior does not cause false positives.

---

## TC-GOAR-15-12: Accepted same-family model change emits structured WARNING log

Scenario: [HAPPY PATH] Accepted same-family model_number change on re-registration emits a WARNING log whose structured `extra` fields consistently expose serial_number, old_model, and new_model for downstream telemetry.  
           Requirement: AR3

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-012"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-012", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` contains a GOAR-15 model-change entry for `old=HP-LJ-2055`, `new=HP-LJ-2060`.

Logging assertions:
- Using `caplog` configured for logger `app.registration` at WARNING level, assert there is a log record with:
  - `record.levelname == "WARNING"`.
  - `"GOAR-15: model_number changed on re-registration"` in `record.message`.
  - `record.serial_number == "SN-GOAR15-012"`.
  - `record.old_model == "HP-LJ-2055"`.
  - `record.new_model == "HP-LJ-2060"`.

Notes: This test focuses on the structured logging fields attached via the `extra` parameter and must verify field names and values exactly as implemented.

---

## TC-GOAR-15-13: Multiple successive same-family model changes produce stable WARNING fields

Scenario: [BOUNDARY VALUE] Multiple successive re-registrations that change model_number within the same family verify that every model-change event produces a structured WARNING log with stable field names and types.  
           Requirement: AR3

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-013"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body sequence:
  1. {"serial_number": "SN-GOAR15-013", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}
  2. {"serial_number": "SN-GOAR15-013", "model_number": "HP-LJ-2070", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200 for both calls.

Logging assertions:
- With `caplog` capturing WARNING logs from `app.registration`, assert there are two separate records:
  - Record 1: `serial_number == "SN-GOAR15-013"`, `old_model == "HP-LJ-2055"`, `new_model == "HP-LJ-2060"`.
  - Record 2: `serial_number == "SN-GOAR15-013"`, `old_model == "HP-LJ-2060"`, `new_model == "HP-LJ-2070"`.
- Both records must include the same field names (`serial_number`, `old_model`, `new_model`) and be of consistent types (all strings).

Notes: The primary focus is on logging field stability across multiple events rather than full response body validation, though Agent 4 should still assert that both responses are successful.

---

## TC-GOAR-15-14: Re-registration of CLAIMED printer with unchanged model preserves ownership

Scenario: [HAPPY PATH] Re-registration of a CLAIMED printer with unchanged normalized model_number succeeds, regenerates Cloud ID and printer email ID, and preserves owner_user_id and CLAIMED status.  
           Requirement: AR4

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-014"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `claim_code` and `printer_id_initial`.
- Claim the printer via `POST /printers/claim` using body {"claim_code": <captured_claim_code>, "user_id": "user-goar15-owner-014"}.
- Confirm via `GET /printers/{printer_id_initial}` that `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner-014"`. Capture `cloud_id_initial` and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-014", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".

Post-action ownership verification:
- `GET /printers/{printer_id_initial}` still returns `owner_user_id == "user-goar15-owner-014"` and `status == "CLAIMED"`.

Notes: This test validates that GOAR-15 changes do not interfere with ownership preservation when re-registering a claimed printer whose model_number has not changed.

---

## TC-GOAR-15-15: Re-registration of CLAIMED printer with same-family model change preserves ownership

Scenario: [HAPPY PATH] Re-registration of a CLAIMED printer with a same-family normalized model_number change succeeds, logs the model change, and still preserves owner_user_id and CLAIMED status.  
           Requirement: AR4

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-015"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `claim_code` and `printer_id_initial`.
- Claim the printer via `POST /printers/claim` with body {"claim_code": <captured_claim_code>, "user_id": "user-goar15-owner-015"}.
- Confirm via `GET /printers/{printer_id_initial}` that `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner-015"`. Capture `cloud_id_initial` and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-015", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".
  - `history` contains a GOAR-15 model-change entry noting the change from `HP-LJ-2055` to `HP-LJ-2060`.

Post-action ownership verification:
- `GET /printers/{printer_id_initial}` returns `owner_user_id == "user-goar15-owner-015"` and `status == "CLAIMED"`.

Notes: Use `caplog` to assert the GOAR-15 WARNING log with `serial_number == "SN-GOAR15-015"`, `old_model == "HP-LJ-2055"`, and `new_model == "HP-LJ-2060"`.

---

## TC-GOAR-15-16: Different-user re-registration attempt does not change ownership

Scenario: [OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context (different bearer token) does not transfer or clear ownership and is rejected or ignored while keeping owner_user_id and CLAIMED status intact.  
           Requirement: AR4

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — but using a token whose subject differs from the claiming user.

Preconditions:
- Issue two tokens via `POST /auth/token`: one for `user_id = "user-goar15-owner-016"` (owner) and one for `user_id = "user-goar15-attacker-016"` (attacker).
- Using the owner token, register a printer with `serial_number = "SN-GOAR15-016"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` and then claim it using the returned `claim_code`.
- Confirm via `GET /printers/{printer_id}` with the owner token that `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner-016"`. Capture `cloud_id_initial` and `printer_email_id_initial`.

Request:
  Headers: override default client headers to use the attacker token: {"Authorization": "Bearer <attacker_token>"}.
  Body: {"serial_number": "SN-GOAR15-016", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action ownership verification:
- Using the owner token, call `GET /printers/{printer_id}`.
- Response body still has `owner_user_id == "user-goar15-owner-016"` and `status == "CLAIMED"`.
- `cloud_id` and `printer_email_id` remain equal to `cloud_id_initial` and `printer_email_id_initial` (no side effects).

Notes: Although GOAR-15 does not explicitly inspect the calling user when deciding model-family rejection, this test demonstrates that an attacker cannot use re-registration to transfer or clear ownership. Agent 4 must ensure headers are correctly switched between owner and attacker contexts.

---

## TC-GOAR-15-17: Missing Authorization on registration yields 422

Scenario: [AUTH] Registration request to POST /printers/register with no Authorization header is rejected with HTTP 422 and leaves registration state unchanged.  
           Requirement: Auth Scenarios

Requirement: Auth Scenarios

Endpoint: POST /printers/register

Auth: missing token — pass headers={} to override conftest.py default.

Preconditions:
- None required; this test targets auth validation before registration logic runs.

Request:
  Headers: {} (empty dict explicitly passed to client).
  Body: {"serial_number": "SN-GOAR15-017", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422 (FastAPI validation error because required Authorization header is missing).
  Body contains:
  - A `detail` list including an entry with `"loc": ["header", "authorization"]` and `"msg": "field required"`.

Notes: Agent 4 must ensure the test client does not attach the default Authorization header by passing `headers={}`. No store or follow-up GET calls are required.

---

## TC-GOAR-15-18: Invalid bearer token on registration yields 401

Scenario: [AUTH] Registration request to POST /printers/register with an invalid or expired bearer token is rejected and leaves printer registration state unchanged.  
           Requirement: Auth Scenarios

Requirement: Auth Scenarios

Endpoint: POST /printers/register

Auth: invalid token — pass headers={"Authorization": "Bearer invalid_token"} to override default.

Preconditions:
- None required; test focuses on token verification.

Request:
  Headers: {"Authorization": "Bearer invalid_token"}.
  Body: {"serial_number": "SN-GOAR15-018", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 401
  Body contains:
  - `detail` == "Invalid or expired token".

Notes: This test asserts behavior of `verify_token` when JWT decoding fails. No follow-up state checks are necessary for this ticket.

---

## TC-GOAR-15-19: Missing Authorization on claim and lookup yields 422

Scenario: [AUTH] Claim and lookup requests to POST /printers/claim and GET /printers/{printer_id} with no Authorization header are rejected with HTTP 422 and leave ownership and visibility unchanged.  
           Requirement: Auth Scenarios

Requirement: Auth Scenarios

Endpoint: POST /printers/claim and GET /printers/{printer_id}

Auth: missing token — pass headers={} to override conftest.py default.

Preconditions:
- Register a printer via `POST /printers/register` with valid auth, capture `printer_id` and `claim_code`.

Request:
  Headers: {} for both claim and lookup.
  Bodies:
  - Claim: {"claim_code": <captured_claim_code>, "user_id": "user-goar15-auth"}.
  - Lookup: no body; path param `printer_id` = captured `printer_id`.

Expected response:
  Status:
  - 422 for `POST /printers/claim`.
  - 422 for `GET /printers/{printer_id}`.
  Body contains for each:
  - A `detail` list with an entry where `loc` includes `"header", "authorization"` and `msg` == "field required".

Notes: After these failed calls, a subsequent `GET /printers/{printer_id}` with valid auth should still show the printer as unclaimed (status "REGISTERED" and `owner_user_id` is null/empty), confirming no ownership changes occurred. Agent 4 may optionally assert this follow-up state.

---

## TC-GOAR-15-20: Invalid bearer token on claim, lookup, and deregister yields 401

Scenario: [AUTH] Claim, lookup, and deregister requests with an invalid or expired bearer token are rejected and leave printer ownership, visibility, and registration state unchanged.  
           Requirement: Auth Scenarios

Requirement: Auth Scenarios

Endpoint: POST /printers/claim, GET /printers/{printer_id}, DELETE /printers/{printer_id}

Auth: invalid token — pass headers={"Authorization": "Bearer invalid_token"} to override default.

Preconditions:
- Register a printer with valid auth, capture `printer_id` and `claim_code`.

Request:
  Headers: {"Authorization": "Bearer invalid_token"} for all three endpoints.
  Bodies:
  - Claim: {"claim_code": <captured_claim_code>, "user_id": "user-goar15-auth-invalid"}.
  - Lookup: no body.
  - Deregister: no body.

Expected response:
  Status: 401 for each call.
  Body contains:
  - `detail` == "Invalid or expired token".

Notes: No follow-up state checks are strictly required, but Agent 4 may optionally assert via a valid-auth `GET /printers/{printer_id}` that status remains "REGISTERED" and the printer record still exists, confirming no changes occurred.

---

## TC-GOAR-15-21: Rejected re-registration for unknown serial creates no printer record

Scenario: [ROLLBACK] Rejected re-registration for a serial_number that was not previously registered does not create any new printer record, capabilities, serial index, Cloud ID, printer email ID, or XMPP node.  
           Requirement: AR1

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Ensure `store.get_printer_by_serial("SN-GOAR15-021")` returns None (no existing printer) using a fixture that clears the store or verifies emptiness.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-021", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200 (because the first registration path is taken; there is no prior printer to re-register).
  Body contains:
  - `printer_id` is a non-empty UUID-like string.
  - `cloud_id` starts with "CID-".
  - `printer_email_id` ends with "@print.hpeprint.com".
  - `status` == "REGISTERED".

Notes: The scenario description in Section AR1 refers to "rejected re-registration for a serial_number that was not previously registered", but the implementation cannot reject such a case because `existing` is None and the flow becomes a first-time registration. This test is included mainly to demonstrate that attempting to "re-register" an unknown serial actually results in a normal registration with full side effects; it does not exercise a GOAR-15-specific rejection path.

---

## TC-GOAR-15-22: Cloud ID generation only persists on successful registration

Scenario: [BOUNDARY VALUE] Re-registration that triggers a model-family mismatch verifies that any Cloud ID generated before failure is not persisted or reused, so that rejected re-registrations do not consume Cloud IDs or leave inconsistent identity traces.  
           Requirement: AR2

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-022"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-022", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- `GET /printers/{printer_id_initial}` returns status 200.
- Body has `cloud_id == cloud_id_initial` and `printer_email_id == printer_email_id_initial`.

Notes: Although the implementation calls `_generate_cloud_id()` before performing GOAR-15 checks, this test confirms that any newly generated Cloud ID for the failed attempt is not persisted; the printer retains its previous `cloud_id`. Agent 4 cannot directly inspect discarded IDs but can assert that the persisted identity values remain unchanged.

---

## TC-GOAR-15-23: Successful re-registration regenerates Cloud ID and does not reuse prior IDs

Scenario: [ROLLBACK] Successful re-registration path verifies that Cloud ID generation occurs only on acceptance and that rejected attempts never persist or reuse a Cloud ID produced earlier in the flow.  
           Requirement: AR2

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-023"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `cloud_id_initial`.
- Perform a failed re-registration as in TC-GOAR-15-22 with a different-family model and confirm rollback (cloud_id unchanged).

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-023", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `cloud_id` is a new value that differs from `cloud_id_initial` and still matches the `CID-` pattern.

Notes: This test ensures that after a failed re-registration, a subsequent successful same-family re-registration generates a fresh Cloud ID that is distinct from the original and is not equal to any intermediate discarded Cloud IDs.

---

## TC-GOAR-15-24: Post-deregistration registration with different-family model treated as fresh device

Scenario: [BOUNDARY VALUE] Printer that has been fully deregistered and then re-registered with the same serial_number but a different model family is treated as a fresh device without historical model-family continuity, provided business confirms this behaviour when implemented.  
           Requirement: AR5

Requirement: AR5

Endpoint: POST /printers/register and DELETE /printers/{printer_id}

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-024"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`.
- Deregister the printer via `DELETE /printers/{printer_id_initial}` and confirm response `{"status": "DEREGISTERED", "printer_id": printer_id_initial}`.
- Confirm via `GET /printers/{printer_id_initial}` that the printer no longer exists (404, "Printer not found").

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-024", "model_number": "HP-C-MFP-9500", "firmware_version": "2.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` is a new identifier distinct from `printer_id_initial`.
  - `cloud_id` starts with "CID-".
  - `printer_email_id` ends with "@print.hpeprint.com".
  - `status` == "REGISTERED".

Notes: This scenario depends on Open Question 3 about model-family semantics after deregistration and is therefore out of scope according to Section 7. It is included here only for documentation but should not be automated or scored as part of GOAR-15 until business clarifies the intended behavior.

---

## TC-GOAR-15-25: Post-deregistration registration with same-family model behaves as first-time registration

Scenario: [BOUNDARY VALUE] Printer that has been deregistered and re-registered with the same serial_number and same-family model_number behaves identically to a first-time registration, confirming that GOAR-15 checks do not inadvertently block legitimate post-deregistration flows.  
           Requirement: AR5

Requirement: AR5

Endpoint: POST /printers/register and DELETE /printers/{printer_id}

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed.

Preconditions:
- Register a printer with `serial_number = "SN-GOAR15-025"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`.
- Deregister via `DELETE /printers/{printer_id_initial}`.

Request:
  Headers: default client headers (valid Authorization).
  Body: {"serial_number": "SN-GOAR15-025", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains:
  - `printer_id` is a new identifier distinct from `printer_id_initial`.
  - `cloud_id` starts with "CID-".
  - `printer_email_id` ends with "@print.hpeprint.com".
  - `status` == "REGISTERED".

Notes: Like TC-GOAR-15-24, this scenario depends on Open Question 3 and should be treated as out of scope for GOAR-15 automation until business clarifies whether model-family checks apply post-deregistration.

---

## TC-GOAR-15-26: Auth-protected deregister with invalid token rejected without side effects

Scenario: [AUTH] Claim, lookup, and deregister requests with an invalid or expired bearer token are rejected and leave printer ownership, visibility, and registration state unchanged.  
           Requirement: Auth Scenarios

Requirement: Auth Scenarios

Endpoint: DELETE /printers/{printer_id}

Auth: invalid token — pass headers={"Authorization": "Bearer invalid_token"} to override default.

Preconditions:
- Register a printer with valid auth, capture `printer_id`.

Request:
  Headers: {"Authorization": "Bearer invalid_token"}.
  Body: none.

Expected response:
  Status: 401
  Body contains:
  - `detail` == "Invalid or expired token".

Notes: This is a focused variant of TC-GOAR-15-20 specifically asserting DELETE behavior. Agent 4 should avoid actually deregistering the printer due to the invalid token and may optionally confirm via a valid-auth `GET /printers/{printer_id}` that the printer still exists.

---

## Skipped Scenarios

[BOUNDARY VALUE] Printer that has been fully deregistered and then re-registered with the same serial_number but a different model family is treated as a fresh device without historical model-family continuity, provided business confirms this behaviour when implemented.  
           Requirement: AR5 — SKIPPED: Depends on Open Question 3 about model-family semantics after deregistration; behavior is not defined in current business rules or implementation.

[BOUNDARY VALUE] Printer that has been deregistered and re-registered with the same serial_number and same-family model_number behaves identically to a first-time registration, confirming that GOAR-15 checks do not inadvertently block legitimate post-deregistration flows.  
           Requirement: AR5 — SKIPPED: Depends on Open Question 3 about post-deregistration model-family behavior; cannot be reliably tested without business decision.

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-15-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-02 | BOUNDARY VALUE | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-03 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-04 | INVALID INPUT | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-05 | BOUNDARY VALUE | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-06 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-07 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-08 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-09 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-10 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-15-11 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-15-12 | HAPPY PATH | AR3 | POST /printers/register | valid token |
| TC-GOAR-15-13 | BOUNDARY VALUE | AR3 | POST /printers/register | valid token |
| TC-GOAR-15-14 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-15-15 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-15-16 | OWNERSHIP | AR4 | POST /printers/register | valid token (different user) |
| TC-GOAR-15-17 | AUTH | Auth Scenarios | POST /printers/register | missing token |
| TC-GOAR-15-18 | AUTH | Auth Scenarios | POST /printers/register | invalid token |
| TC-GOAR-15-19 | AUTH | Auth Scenarios | POST /printers/claim, GET /printers/{printer_id} | missing token |
| TC-GOAR-15-20 | AUTH | Auth Scenarios | POST /printers/claim, GET /printers/{printer_id}, DELETE /printers/{printer_id} | invalid token |
| TC-GOAR-15-21 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-15-22 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-15-23 | ROLLBACK | AR2 | POST /printers/register | valid token |
| TC-GOAR-15-24 | BOUNDARY VALUE | AR5 | POST /printers/register, DELETE /printers/{printer_id} | valid token |
| TC-GOAR-15-25 | BOUNDARY VALUE | AR5 | POST /printers/register, DELETE /printers/{printer_id} | valid token |
| TC-GOAR-15-26 | AUTH | Auth Scenarios | DELETE /printers/{printer_id} | invalid token |
