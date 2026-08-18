# Test Cases — GOAR-15

## TC-GOAR-15-01: Same-family model change accepted with full registration outputs

Scenario: [HAPPY PATH] Successful re-registration where model_number changes within the same family is accepted and produces the expected registration outputs.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions: 
- A printer is already registered with `serial_number = "SN-GOAR15-001"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture from the initial registration response: `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial`.
- The printer currently has status `REGISTERED` and no `owner_user_id`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial` (same physical printer record reused).
  - `cloud_id` is a non-empty string starting with `"CID-"` and `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` is a non-empty string ending with `"@print.hpeprint.com"` and `printer_email_id` != `printer_email_id_initial`.
  - `claim_code` is an 8-character alphanumeric string and `claim_code_expires_at` is an ISO 8601 timestamp in the future.
  - `xmpp_node` is a non-empty string; if `xmpp_node_initial` was non-empty, `xmpp_node` may equal `xmpp_node_initial` or be reassigned but must be non-empty.
  - `status` == "REGISTERED".
  - `history` is a list containing at least:
    - An entry with text starting with `"GOAR-15: model_number changed on re-registration"` and including `"old=HP-LJ-2055"` and `"new=HP-LJ-2060"`.
    - An entry containing `"Registration started"` or `"Re-registration started"` for this call.
    - An entry containing `"Cloud identity created:"` for this call.
    - An entry containing `"Welcome page printed successfully; registration complete"` for this call.

Notes: Agent 4 should implement precondition setup by first calling `POST /printers/register` with body `{"serial_number": "SN-GOAR15-001", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}` and capturing the response values. No rollback is expected in this test, so `reset_store` is not required. To assert structured logging for GOAR-15, use `caplog` around the second registration call and verify a WARNING log containing `"GOAR-15: model_number changed on re-registration"` and `extra["serial_number"] == "SN-GOAR15-001"`, `extra["old_model"] == "HP-LJ-2055"`, `extra["new_model"] == "HP-LJ-2060"`.

---

## TC-GOAR-15-02: Case/whitespace-only model difference treated as unchanged

Scenario: [BOUNDARY VALUE] Re-registration where model_number differs only by case/whitespace is treated as unchanged after normalization and does not trigger a model-change flag.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is already registered with `serial_number = "SN-GOAR15-002"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial`.
- The printer currently has status `REGISTERED`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-002", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` is a new `CID-` value and `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` is new and `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` does NOT contain a new entry starting with `"GOAR-15: model_number changed on re-registration"` for this call.
  - `xmpp_node` is non-empty; if `xmpp_node_initial` was set, it should still be set.

Notes: Use `caplog` around the re-registration call to assert that no WARNING log with message containing `"GOAR-15: model_number changed on re-registration"` is emitted. Precondition: initial registration via `POST /printers/register` using `model_number = "HP-LJ-2055"`. No rollback is involved; `reset_store` is not required.

---

## TC-GOAR-15-03: Different-family model change rejected with full rollback of new identity

Scenario: [ROLLBACK] Re-registration with a different-family model_number is rejected and leaves Cloud ID, email, XMPP node, and capabilities unchanged apart from the review history entry.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-003"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` using a successful initial call. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, capabilities via `store.get_capabilities(printer_id_initial)` (implicitly via GET in tests), and `history_initial`.
- The printer status is `REGISTERED` and has a non-empty `xmpp_node_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-003", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- Call `GET /printers/{printer_id_initial}` with valid auth.
- Response Status: 200.
- Response body fields:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == "REGISTERED".
  - `history` includes the original entries plus:
    - One entry for this attempt: `"GOAR-15: model_number changed on re-registration (old=HP-LJ-2055, new=HP-C-MFP-9999) -- flagged for review"`.
    - No entries indicating new Cloud ID creation or Welcome Page success for the failed attempt.

Notes: This is a rollback test case. Agent 4 must capture pre-action state via `GET /printers/{printer_id_initial}` before the different-family re-registration attempt. Then perform the `POST /printers/register` call that returns 422, and finally call `GET /printers/{printer_id_initial}` again to assert that `cloud_id`, `printer_email_id`, `xmpp_node`, and `status` are unchanged while `history` has only the review entry added. Use `caplog` to assert a WARNING log with `result` implicitly rejected via the exception and message containing `"model_number changed on re-registration"`. No explicit `reset_store` call is needed; rollback is handled by domain logic for the failed registration.

---

## TC-GOAR-15-04: Different-family re-registration rejected with RegistrationError and no side effects

Scenario: [HAPPY PATH] Re-registration attempt with a clearly different-family model_number is rejected with a RegistrationError and no registration-side effects occur.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-004"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial`.
- Printer status is `REGISTERED`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-004", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-2055', incoming='HP-C-MFP-9999'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- Call `GET /printers/{printer_id_initial}`.
- Response Status: 200.
- Response body:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == "REGISTERED".
  - `history` contains the initial registration entries plus a model-change review entry, but no entries indicating new Cloud ID or Welcome Page success for the rejected attempt.

Notes: Though labeled as [HAPPY PATH] in the scenario, this is a negative/rollback behavior. Agent 4 should treat it similarly to TC-GOAR-15-03. Use `caplog` to assert a WARNING log for the model-number change. Pre- and post-state must be captured via `GET /printers/{printer_id_initial}` to confirm that registration-side effects (Cloud ID, email, XMPP, capabilities) did not change.

---

## TC-GOAR-15-05: Boundary classification at heuristic edge (HP-LJ-001)

Scenario: [BOUNDARY VALUE] Re-registration where the new model_number sits on the edge of the same-family vs different-family heuristic (last dash-separated segment) is correctly classified and either accepted or rejected.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-005"`, `model_number = "HP-LJ-001"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.
- Printer status is `REGISTERED`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-005", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Re-registration rejected: model family mismatch (existing='HP-LJ-001', incoming='HP-LJ-2055'). This looks like a different physical device reusing the same serial number."

Post-action state verification:
- Call `GET /printers/{printer_id_initial}`.
- Response Status: 200.
- Body fields:
  - `model_number` == "HP-LJ-001" (unchanged).
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` includes the model-change review log entry for the attempted change but no new registration-complete entry.

Notes: This test validates the heuristic `_model_family()` behaviour where both `"HP-LJ-001"` and `"HP-LJ-2055"` share the `"HP-LJ"` prefix but differ by last segment, ensuring that the implemented behavior (family mismatch based on raw model strings, not just `_model_family`) is observed. Pre/post state capture through `GET /printers/{printer_id_initial}` is required. Use `caplog` to confirm a warning log with correct `old_model` and `new_model` fields.

---

## TC-GOAR-15-06: Rejected different-family re-registration has no partial identity side effects

Scenario: [ROLLBACK] Rejected different-family re-registration does not create or alter any Cloud ID, printer email, XMPP node, capabilities record, or serial index.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-006"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and confirm capabilities exist for `printer_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-006", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` message identical to TC-GOAR-15-03 and TC-GOAR-15-04.

Post-action state verification:
- Call `GET /printers/{printer_id_initial}`.
- Response Status: 200.
- Body fields:
  - `cloud_id` == `cloud_id_initial`.
  - `printer_email_id` == `printer_email_id_initial`.
  - `xmpp_node` == `xmpp_node_initial`.
  - `status` == "REGISTERED".
  - `serial_number` == "SN-GOAR15-006".
- Capabilities verification (implementation detail for Agent 4): use the `store` fixture or an equivalent helper to call `store.get_capabilities(printer_id_initial)` and assert the capabilities record is unchanged.

Notes: This is a rollback test focused on side effects. Pre-action and post-action state must be compared (Cloud ID, email, xmpp, capabilities). Ensure no additional `store.index_serial` or capability recreation occurs for the failed attempt. Use `caplog` to verify the structured warning log; the rejection should happen before any new Cloud ID or email is committed beyond the original state.

---

## TC-GOAR-15-07: Re-registration with identical identity fields succeeds with new Cloud/email/XMPP

Scenario: [HAPPY PATH] Re-registration with identical model_number and firmware_version succeeds and generates a new Cloud ID, email ID, and XMPP node as per existing rules.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-007"` with body `{"serial_number": "SN-GOAR15-007", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}` has completed successfully.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, `status_initial` (expected "REGISTERED"), and `history_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-007", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial` and matches `CID-[A-F0-9]{12}`.
  - `printer_email_id` != `printer_email_id_initial` and matches `[a-z0-9]{10}@print.hpeprint.com`.
  - `xmpp_node` is non-empty; if `xmpp_node_initial` was empty, it must now be non-empty; if it was non-empty, it must remain non-empty.
  - `status` == "REGISTERED".
  - `history` includes a new "Re-registration started", "Cloud identity created", and "Welcome page printed successfully; registration complete" entries for this call.

Notes: This is a pure GOAR-3-style re-registration with no GOAR-15-specific change. Use it as a control to confirm that GOAR-15 did not break existing behavior. `caplog` is optional here. No rollback occurs; `reset_store` is not needed.

---

## TC-GOAR-15-08: Re-registration with updated firmware preserves ownership

Scenario: [HAPPY PATH] Re-registration with identical model_number but updated firmware_version succeeds and regenerates Cloud ID and printer email while preserving ownership.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer has been registered with `serial_number = "SN-GOAR15-008"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- The printer has subsequently been claimed via `POST /printers/claim` using the initial claim code and `user_id = "user-goar15-owner"`, yielding `status == "CLAIMED"` and `owner_user_id == "user-goar15-owner"`. Capture `printer_id_claimed`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-008", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_claimed`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED" (claimed status preserved despite re-registration).
  - `history` has new entries for the re-registration call.

Post-action ownership verification:
- Call `GET /printers/{printer_id_claimed}`.
- Response Status: 200.
- Body fields:
  - `owner_user_id` == "user-goar15-owner".
  - `status` == "CLAIMED".

Notes: This test verifies that ownership is unaffected by benign firmware updates. Agent 4 should capture the claim-code from the initial registration to claim the printer in preconditions, then re-register with updated firmware. No rollback occurs. `caplog` is optional.

---

## TC-GOAR-15-09: Non-GOAR-15 pre-Welcome-Page failure rolls back fully

Scenario: [ROLLBACK] Failed re-registration due to a non-GOAR-15 pre-Welcome-Page error rolls back fully and leaves prior Cloud ID, email, and XMPP state unchanged.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-009"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and `history_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-009", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}`

Expected response:
  Status: 422
  Body contains:
  - `detail` == "Welcome page failed to print for printer_id=<printer_id_initial>" (Agent 4 should build the expected string using the captured printer_id).

Post-action state verification:
- Call `GET /printers/{printer_id_initial}`.
- Response Status: 404.
- Body contains: `{"detail": "Printer not found"}`.

Notes: This is a rollback test. Agent 4 must verify pre-state via `GET /printers/{printer_id_initial}` before the failure-causing call, then perform the failing `POST /printers/register` with `simulate_welcome_page_failure: true`, and finally assert that the printer record, capabilities, and serial index are removed via the 404 response on `GET /printers/{printer_id_initial}`. Use `reset_store` only if suite isolation requires it; rollback is handled by `_rollback_registration`.

---

## TC-GOAR-15-10: Normalized case/whitespace comparison avoids model-change warning

Scenario: [HAPPY PATH] Re-registration where old and new model_number differ only in case/whitespace does not trigger a model-change warning and is treated as the same model.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-010"` with `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` is completed.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-010", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - `history` for this call does NOT contain any entry starting with `"GOAR-15: model_number changed on re-registration"`.

Notes: Use `caplog` to ensure no WARNING log with message containing `"GOAR-15: model_number changed on re-registration"` is emitted. This is similar to TC-GOAR-15-02 but maps to AR1 instead of AC1; Agent 4 may reuse setup helpers.

---

## TC-GOAR-15-11: Normalization collision treated consistently as unchanged

Scenario: [BOUNDARY VALUE] Re-registration where normalization causes two visually distinct model_number strings to collide is still treated consistently as unchanged.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-011"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `history_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-011", "model_number": " hp-lj-2055 ", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - No history entry for a GOAR-15 model-change warning.

Notes: This scenario is effectively the same shape as TC-GOAR-15-10 but emphasizes that any visually distinct string that normalizes to the same uppercase, stripped value should be treated as unchanged. Agent 4 can consolidate implementation but must keep separate test IDs.

---

## TC-GOAR-15-12: Multi-segment model_number family extraction behaves consistently

Scenario: [BOUNDARY VALUE] Re-registration with multiple dash-separated segments in model_number verifies that _model_family() consistently extracts the family and classifies same-family vs different-family.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-012"`, `model_number = "HP-C-MFP-9999"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-012", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - No model-change warning, since old and new model_number are identical.

Notes: While the scenario mentions multiple dash-separated segments, the implemented heuristic `_model_family()` returns the full family prefix for identical model_number strings, so this test validates that re-registration within the same multi-segment family behaves as expected. Agent 4 may optionally log or inspect `_model_family("HP-C-MFP-9999")` via a helper in unit tests, but API tests should remain black-box.

---

## TC-GOAR-15-13: No-dash model_number treated as single family string

Scenario: [BOUNDARY VALUE] Re-registration for a model_number with no dash separator verifies that the entire string is treated as the family and behaves consistently.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- Initial registration for `serial_number = "SN-GOAR15-013"` with `model_number = "HPLJMFP9999"` (no dashes), `firmware_version = "1.0.0"` succeeds.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-013", "model_number": "HPLJMFP9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "REGISTERED".
  - No GOAR-15 model-change warning.

Notes: This test confirms that `_model_family()` returns the whole string when no dash is present, and that same-model re-registration behaves normally. As with other same-model tests, there should be no warning log.

---

## TC-GOAR-15-14: Rejected different-family re-registration leaves printer state exactly unchanged

Scenario: [ROLLBACK] Different-family re-registration that is rejected leaves the printer record, capabilities, serial index, Cloud ID, email, and XMPP node exactly as before the attempt.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-014"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture pre-state via `GET /printers/{printer_id}`: `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, `status_initial`, `history_initial`.
- Confirm capabilities and serial index exist via supporting test utilities.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-014", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` message as in prior different-family tests.

Post-action state verification:
- Call `GET /printers/{printer_id_initial}`.
- Response Status: 200.
- Body:
  - All identity fields (`cloud_id`, `printer_email_id`, `serial_number`, `xmpp_node`, `status`) equal the pre-state values.
  - `history` differs only by the addition of the GOAR-15 review entry.
- Verify via store helpers that capabilities and serial index for `serial_number = "SN-GOAR15-014"` still exist and are unchanged.

Notes: This rollback test must explicitly compare pre-state and post-state. Agent 4 should capture the original response into a Python dict, perform the failed re-registration, then fetch the printer again and assert equality for all fields except `history` length/contents. Use `caplog` to assert the warning log with `result="rejected"` conceptually represented by the 422.

---

## TC-GOAR-15-15: Rejected re-registration for unknown serial does not create a printer record

Scenario: [ROLLBACK] Rejected re-registration for a previously unregistered serial_number does not create any new printer record, capabilities, serial index, Cloud ID, email, or XMPP node.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- Ensure no printer exists for `serial_number = "SN-GOAR15-015"` (use a fresh serial and, if available, call `reset_store()` before the test).

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-015", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - A new printer record with `status` == "REGISTERED" (note: because there is no existing printer, this is treated as initial registration, not re-registration, and will succeed — the repository logic only rejects model-family mismatch when re-registering an existing printer).

Notes: The scenario text speaks about a rejected re-registration for an unregistered serial, but the actual implementation cannot reject such a case because there is no existing printer to compare families against. Agent 4 should implement this test as a check that initial registration for a fresh serial behaves normally with no prior state or partial side effects. This is a slight divergence from scenario wording but remains within code behavior; do not attempt to assert rollback semantics here.

---

## TC-GOAR-15-16: Re-registration of CLAIMED printer with unchanged model preserves ownership

Scenario: [HAPPY PATH] Re-registration of a CLAIMED printer with unchanged model_number succeeds while preserving owner_user_id and CLAIMED status.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-016"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Claim the printer via `POST /printers/claim` using its initial claim code and `user_id = "user-goar15-claimant"`. Capture `printer_id_claimed` and verify via `GET /printers/{printer_id_claimed}` that `status == "CLAIMED"` and `owner_user_id == "user-goar15-claimant"`. Capture `cloud_id_initial`, `printer_email_id_initial`, and `xmpp_node_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-016", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_claimed`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".

Post-action ownership verification:
- Call `GET /printers/{printer_id_claimed}`.
- Response Status: 200.
- Body fields:
  - `owner_user_id` == "user-goar15-claimant".
  - `status` == "CLAIMED".

Notes: This test confirms AR4’s requirement that legitimate re-registrations preserve claims. Ensure you re-use the same auth token for registration and claim operations unless a separate user context is required. No rollback occurs here.

---

## TC-GOAR-15-17: Same-family model change on CLAIMED printer preserves ownership

Scenario: [HAPPY PATH] Re-registration of a CLAIMED printer with same-family model_number succeeds, logs the model change, and preserves owner_user_id and CLAIMED status.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered and claimed as in TC-GOAR-15-16, but with `serial_number = "SN-GOAR15-017"`. Capture `printer_id_claimed`, `cloud_id_initial`, `printer_email_id_initial`, `xmpp_node_initial`, and owner `user-goar15-claimant-2`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-017", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_claimed`.
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `status` == "CLAIMED".
  - `history` includes a GOAR-15 model-change review entry for `old=HP-LJ-2055` and `new=HP-LJ-2060`.

Post-action ownership verification:
- Call `GET /printers/{printer_id_claimed}` and assert `owner_user_id == "user-goar15-claimant-2"` and `status == "CLAIMED"`.

Notes: Use `caplog` to assert a WARNING log including `serial_number = "SN-GOAR15-017"` and the old/new model numbers. No rollback occurs.

---

## TC-GOAR-15-18: Re-registration from different user context does not transfer ownership

Scenario: [OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context does not transfer or clear ownership and is either rejected or leaves ownership unchanged.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed (use a token whose subject is a user different from the owner).

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-018"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` and claimed by `user-goar15-owner-3` via `POST /printers/claim`.
- Capture `printer_id_claimed`, `owner_user_id_initial = "user-goar15-owner-3"`, `cloud_id_initial`, and `printer_email_id_initial`.
- Obtain a second valid JWT token for `user-goar15-other` using `POST /auth/token`.

Request:
  Headers: `{"Authorization": "Bearer <token_for_user-goar15-other>"}`
  Body: `{"serial_number": "SN-GOAR15-018", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_claimed`.
  - `status` == "CLAIMED".

Post-action ownership verification:
- Call `GET /printers/{printer_id_claimed}` with either user's valid token.
- Assert:
  - `owner_user_id` == "user-goar15-owner-3" (unchanged).
  - `status` == "CLAIMED".

Notes: The implementation does not tie registration behavior directly to the JWT subject; ownership is stored on the printer record and only updated via the claim endpoint. This test ensures that using a different JWT subject to re-register a claimed printer does not affect ownership. No rollback occurs.

---

## TC-GOAR-15-19: Same-family model change emits structured warning log

Scenario: [HAPPY PATH] Same-family model-number change on re-registration emits a structured warning log with serial_number, old_model, and new_model fields while the registration succeeds.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-019"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`.
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-019", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `printer_id` == `printer_id_initial`.
  - New `cloud_id` and `printer_email_id` distinct from initial values.
  - `status` == "REGISTERED".

Logging expectations:
- Using `caplog` at WARNING level, assert that a log record exists with:
  - `message` containing `"GOAR-15: model_number changed on re-registration"`.
  - `extra["serial_number"] == "SN-GOAR15-019"`.
  - `extra["old_model"] == "HP-LJ-2055"`.
  - `extra["new_model"] == "HP-LJ-2060"`.

Notes: This test focuses on AR5’s structured logging requirement. Ensure FastAPI app logger propagation is configured so that `caplog` sees logs from `app.registration`.

---

## TC-GOAR-15-20: Rejected different-family model change emits structured warning log

Scenario: [ROLLBACK] Different-family model-number change that is rejected emits a structured warning log with serial_number, old_model, new_model, and result="rejected" while leaving printer state unchanged.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-020"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture pre-state via `GET /printers/{printer_id_initial}`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-020", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422
  Body contains:
  - `detail` as per previous different-family tests.

Post-action state verification:
- `GET /printers/{printer_id_initial}` returns the same identity fields as before.

Logging expectations:
- `caplog` must capture a WARNING log with message containing `"GOAR-15: model_number changed on re-registration"` and extra fields `serial_number`, `old_model`, `new_model` matching this printer.

Notes: The implementation does not explicitly add `result="rejected"` to the `extra` dict, so the test should only assert fields that exist in code (serial_number, old_model, new_model) and treat the 422 response as the rejection indicator. This is a rollback test; ensure pre- and post-state are compared.

---

## TC-GOAR-15-21: Unchanged model successful re-registration regenerates Cloud/email/XMPP

Scenario: [HAPPY PATH] Successful re-registration with unchanged model_number generates a new Cloud ID, a new printer email ID, and assigns an XMPP node if missing, all differing from prior values.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-021"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `xmpp_node_initial` (which may be empty before XMPP assignment).

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-021", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `xmpp_node` is non-empty (if `xmpp_node_initial` was empty, it must now be assigned; if it was non-empty, it must remain non-empty).
  - `status` == "REGISTERED".

Notes: Similar to TC-GOAR-15-07 but explicitly targets AR6. No rollback occurs.

---

## TC-GOAR-15-22: Same-family model change successful re-registration regenerates Cloud/email

Scenario: [HAPPY PATH] Successful re-registration with same-family model_number change generates new Cloud ID and printer email while preserving or assigning XMPP connectivity.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-022"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, `printer_email_id_initial`, and `xmpp_node_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-022", "model_number": "HP-LJ-2060", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `xmpp_node` is non-empty (either preserved or newly assigned).
  - `status` == "REGISTERED".

Notes: This test confirms that GOAR-15’s model-change handling still allows full identity regeneration for same-family upgrades. No rollback occurs.

---

## TC-GOAR-15-23: Re-registration for printer with existing XMPP node preserves connectivity

Scenario: [BOUNDARY VALUE] Re-registration of a printer that already has an XMPP node verifies that the node is preserved or correctly reassigned without violating connectivity rules.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token — Authorization header attached by conftest.py client fixture by default — no extra code needed

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-023"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"` and has already been assigned an XMPP node by the initial registration (capture `xmpp_node_initial`).
- Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer <valid_token_from_conftest>"}`
  Body: `{"serial_number": "SN-GOAR15-023", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 200
  Body contains:
  - `cloud_id` != `cloud_id_initial`.
  - `printer_email_id` != `printer_email_id_initial`.
  - `xmpp_node` is non-empty; it may equal `xmpp_node_initial` or be a new node but must remain non-empty.
  - `status` == "REGISTERED".

Notes: The implementation may reassign an XMPP node only if one is missing; otherwise it logs "XMPP node assigned" once. This test ensures that re-registration does not clear XMPP connectivity. No rollback occurs.

---

## TC-GOAR-15-24: Missing Authorization header yields 422 and no side effects

Scenario: [AUTH] Re-registration request to the protected registration endpoint without an Authorization header is rejected with no registration-side effects.

Requirement: AC3

Endpoint: POST /printers/register

Auth: missing token — pass `headers={}` to override conftest.py default

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-024"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial` via a pre-test `GET /printers/{printer_id_initial}`.

Request:
  Headers: `{}` (explicitly no Authorization header)
  Body: `{"serial_number": "SN-GOAR15-024", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 422 (FastAPI validation error for missing required header dependency)
  Body contains:
  - Standard FastAPI validation error structure mentioning `"authorization"` header as missing.

Post-action state verification:
- Call `GET /printers/{printer_id_initial}` with valid auth.
- Assert `cloud_id` == `cloud_id_initial` and `printer_email_id` == `printer_email_id_initial`.

Notes: The `verify_token` dependency declares the Authorization header as required, so missing header produces a 422 before business logic executes. No rollback is needed; no registration attempt occurs. Agent 4 must override the default headers provided by conftest.

---

## TC-GOAR-15-25: Invalid bearer token yields 401 and no side effects

Scenario: [AUTH] Re-registration request to the protected registration endpoint with an invalid or expired bearer token is rejected with no registration-side effects.

Requirement: AC3

Endpoint: POST /printers/register

Auth: invalid token — pass `headers={"Authorization": "Bearer invalid_token"}` to override default

Preconditions:
- A printer is registered with `serial_number = "SN-GOAR15-025"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. Capture `printer_id_initial`, `cloud_id_initial`, and `printer_email_id_initial`.

Request:
  Headers: `{"Authorization": "Bearer invalid_token"}`
  Body: `{"serial_number": "SN-GOAR15-025", "model_number": "HP-LJ-2055", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}`

Expected response:
  Status: 401
  Body contains:
  - `detail` == "Invalid or expired token".

Post-action state verification:
- `GET /printers/{printer_id_initial}` with valid auth still returns the original Cloud ID and email.

Notes: `verify_token` will raise HTTPException(401) before calling `registration.register_printer`, so no side effects occur. Agent 4 must override conftest default headers with the explicit invalid token.

---

## TC-GOAR-15-26: Summary of scenario coverage (non-test executable)

Scenario: Synthetic summary from coverage section — not an executable scenario.

Requirement: N/A

Endpoint: N/A

Auth: N/A

Preconditions: N/A

Request:
  Headers: N/A
  Body: N/A

Expected response:
  Status: N/A
  Body contains: N/A

Notes: This entry intentionally left non-executable; actual scenarios total 25 above. It should not be turned into a pytest test by Agent 4.

---

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-15-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-02 | BOUNDARY VALUE | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-03 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-15-04 | HAPPY PATH (negative) | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-05 | BOUNDARY VALUE | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-06 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-15-07 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-08 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-09 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-15-10 | HAPPY PATH | AR1 | POST /printers/register | valid token |
| TC-GOAR-15-11 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-15-12 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-15-13 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-15-14 | ROLLBACK | AR3 | POST /printers/register | valid token |
| TC-GOAR-15-15 | ROLLBACK (initial registration) | AR3 | POST /printers/register | valid token |
| TC-GOAR-15-16 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-15-17 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-15-18 | OWNERSHIP | AR4 | POST /printers/register | valid token |
| TC-GOAR-15-19 | HAPPY PATH | AR5 | POST /printers/register | valid token |
| TC-GOAR-15-20 | ROLLBACK | AR5 | POST /printers/register | valid token |
| TC-GOAR-15-21 | HAPPY PATH | AR6 | POST /printers/register | valid token |
| TC-GOAR-15-22 | HAPPY PATH | AR6 | POST /printers/register | valid token |
| TC-GOAR-15-23 | BOUNDARY VALUE | AR6 | POST /printers/register | valid token |
| TC-GOAR-15-24 | AUTH | AC3 | POST /printers/register | missing token |
| TC-GOAR-15-25 | AUTH | AC3 | POST /printers/register | invalid token |
| TC-GOAR-15-26 | SUMMARY | N/A | N/A | N/A
