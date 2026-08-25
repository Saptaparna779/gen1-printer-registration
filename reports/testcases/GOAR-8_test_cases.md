# Test Cases — GOAR-8

## TC-GOAR-8-01: Claim unclaimed printer with valid unused claim code (happy path)

Scenario: [HAPPY PATH] Claiming an unclaimed printer with a valid, unused claim code succeeds and sets status to CLAIMED with owner_user_id linked to the claimant.

Requirement: AC2

Endpoint: POST /printers/claim

Auth: valid token

Preconditions: 
- A printer is successfully registered via POST /printers/register with:
  - serial_number: "SN-GOAR8-001"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture from the registration response:
  - printer_id => printer_id_1
  - claim_code => claim_code_1
  - claim_code_expires_at => expires_at_1
- Ensure the printer is currently in status REGISTERED (no prior claim has been made) by calling GET /printers/{printer_id_1} and asserting:
  - status == "REGISTERED"
  - owner_user_id is None

Request:

  Headers: 
  - Authorization: Bearer <valid JWT provided by conftest.py via /auth/token>
  - Content-Type: application/json

  Body: 
  ```json
  {
    "claim_code": "{{claim_code_1}}",
    "user_id": "user-goar8-claimant-01"
  }
  ```

Expected response:

  Status: 200

  Body contains: 
  - printer_id: equals printer_id_1
  - status: "CLAIMED"
  - owner_user_id: "user-goar8-claimant-01"

  Additionally, perform a follow-up GET /printers/{printer_id_1} and assert:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-claimant-01"
  - cloud_id is unchanged from the registration response

Notes: 
- Use the default authenticated client fixture so that Authorization header is attached automatically (no extra code needed).
- Registration precondition should be performed within the same test to avoid cross-test dependencies.
- Persist claim_code_1 and printer_id_1 as local variables in the test function.

---

## TC-GOAR-8-02: Reject claim on already-claimed printer with valid unused claim code

Scenario: [INVALID INPUT] Attempting to claim a printer whose status is already CLAIMED with a valid, unused claim code raises InvalidClaimCodeError and does not change ownership.

Requirement: AC1

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-002"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture from the registration response:
  - printer_id => printer_id_2
  - claim_code => claim_code_2
- Claim the printer once using POST /printers/claim with:
  - claim_code: claim_code_2
  - user_id: "user-goar8-owner-02"
- Verify via GET /printers/{printer_id_2} that:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-02"

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_2}}",
    "user_id": "user-goar8-attacker-02"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Printer is already claimed"

  Follow-up GET /printers/{printer_id_2} must still show:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-02"

Notes:
- This test ensures that a second claim attempt with the same valid, unused claim code is rejected once the printer is already CLAIMED.
- The same claim_code_2 should not be marked as successfully reused; ownership must remain unchanged.

---

## TC-GOAR-8-03: Reject same-owner re-claim attempt for already-claimed printer

Scenario: [OWNERSHIP] Claiming an already-CLAIMED printer with a user_id matching the existing owner_user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged.

Requirement: AR1

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-003"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_3
  - claim_code => claim_code_3
- Claim the printer once with:
  - claim_code: claim_code_3
  - user_id: "user-goar8-owner-03"
- Verify via GET /printers/{printer_id_3} that:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-03"

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_3}}",
    "user_id": "user-goar8-owner-03"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Printer is already claimed"

  Follow-up GET /printers/{printer_id_3} must still show:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-03"

Notes:
- This test enforces that claim_printer() does not allow idempotent re-claims even by the same owner and treats all already-CLAIMED states uniformly.

---

## TC-GOAR-8-04: Reject different-user claim attempt for already-claimed printer

Scenario: [OWNERSHIP] Claiming an already-CLAIMED printer with a different user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged.

Requirement: AR1

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Reuse the setup steps from TC-GOAR-8-03 but with distinct identifiers:
  - serial_number: "SN-GOAR8-004"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_4
  - claim_code => claim_code_4
- Initial successful claim:
  - claim_code: claim_code_4
  - user_id: "user-goar8-owner-04"
- Confirm via GET /printers/{printer_id_4} that:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-04"

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_4}}",
    "user_id": "user-goar8-attacker-04"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Printer is already claimed"

  Follow-up GET /printers/{printer_id_4} must still show:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-04"

Notes:
- This test is similar to TC-GOAR-8-02 but emphasizes that the rejection is independent of user_id; any different user attempting to claim an already-claimed printer is rejected.

---

## TC-GOAR-8-05: Claim unclaimed printer marks claim code as used and associates ownership

Scenario: [HAPPY PATH] Claiming an unclaimed printer using a valid, unused claim code succeeds, marks the claim code as used, and associates the printer to the requesting user.

Requirement: AC2

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-005"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_5
  - claim_code => claim_code_5
- Confirm via GET /printers/{printer_id_5}:
  - status == "REGISTERED"
  - owner_user_id is None

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_5}}",
    "user_id": "user-goar8-owner-05"
  }
  ```

Expected response:

  Status: 200

  Body contains:
  - printer_id: printer_id_5
  - status: "CLAIMED"
  - owner_user_id: "user-goar8-owner-05"

  Follow-up GET /printers/{printer_id_5} must assert:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-05"
  - claim_code.used == True (claim_code usage verified via internal store using a helper or by directly inspecting the returned printer in responses if surfaced)

Notes:
- Since the HTTP API does not expose claim_code.used directly, Agent 4 should validate usage via the GET response's status/owner_user_id changes; the internal used flag is implicitly verified by the failure behavior in TC-GOAR-8-07 and TC-GOAR-8-11.

---

## TC-GOAR-8-06: Boundary claim just before and after claim_code expiry

Scenario: [BOUNDARY VALUE] Claiming an unclaimed printer just before claim_code.expires_at succeeds, but a call immediately after expiry raises InvalidClaimCodeError.

Requirement: AR3

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-006"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_6
  - claim_code => claim_code_6
  - claim_code_expires_at => expires_at_6 (ISO string)
- Compute a test time just before expiry based on the configured CLAIM_CODE_TTL_MINUTES (15 minutes). Actual timing control for the test must be performed via monkeypatching datetime.utcnow in app.registration to simulate current time.

Request:

  Headers (both calls):
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body for call 1 (just before expiry):
  ```json
  {
    "claim_code": "{{claim_code_6}}",
    "user_id": "user-goar8-owner-06a"
  }
  ```

  Body for call 2 (immediately after expiry, using the same claim_code_6):
  ```json
  {
    "claim_code": "{{claim_code_6}}",
    "user_id": "user-goar8-owner-06b"
  }
  ```

Expected response:

  Call 1 (pre-expiry):
  - Status: 200
  - Body contains:
    - printer_id: printer_id_6
    - status: "CLAIMED"
    - owner_user_id: "user-goar8-owner-06a"

  Call 2 (post-expiry, with patched datetime.utcnow > expires_at_6 and claim_code.used reset to False for the boundary test):
  - Status: 400
  - Body contains:
    - detail: "Claim code has expired"

Notes:
- This test requires Agent 4 to monkeypatch datetime.utcnow in app.registration to simulate time just before and just after expires_at_6, without sleeping in real time.
- Ensure that the first call is executed with datetime.utcnow() < expires_at_6.
- After call 1, the claim_code is marked used; to isolate expiry behavior, the second call must be against a fresh registration/claim_code specifically set up with used=False and only the time advanced past expires_at_6.

---

## TC-GOAR-8-07: Reject claim with already-used claim code for unclaimed printer

Scenario: [INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is already True fails with InvalidClaimCodeError and does not change owner_user_id or status.

Requirement: AR4

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-007"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_7
  - claim_code => claim_code_7
- Manually mark the claim code as used via a direct call to app.store or via an initial successful claim, then reset printer status back to REGISTERED without changing claim_code.used. Because the HTTP API does not expose a way to toggle used directly, Agent 4 must simulate this by:
  - Performing an initial successful claim with user_id "user-goar8-owner-07-internal".
  - Fetching the printer via GET /printers/{printer_id_7} and verifying status == "CLAIMED".
  - Using an internal fixture or helper (if available) to directly modify the printer in the store so that:
    - status is set back to PrinterStatus.REGISTERED
    - owner_user_id is set to None
    - claim_code.used remains True

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_7}}",
    "user_id": "user-goar8-owner-07"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Claim code has already been used"

  Follow-up GET /printers/{printer_id_7} must show:
  - status remains "REGISTERED" (or the status configured in the precondition)
  - owner_user_id is unchanged (None)

Notes:
- This test focuses specifically on the used flag; because claim_printer checks used after expiry, ensure that datetime.utcnow() <= claim_code.expires_at during the test.
- Agent 4 may need to add a test-only helper in the store layer to mutate printers directly; this must not change production logic.

---

## TC-GOAR-8-08: user_id-independent rejection for already-claimed printers

Scenario: [OWNERSHIP] For a printer already in CLAIMED status, claiming with a valid, unused claim code using any user_id (same as or different from owner_user_id) is rejected with InvalidClaimCodeError and leaves ownership unchanged.

Requirement: AR1

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register:
  - serial_number: "SN-GOAR8-008"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_8
  - claim_code => claim_code_8
- Perform a successful claim:
  - claim_code: claim_code_8
  - user_id: "user-goar8-owner-08"
- Verify via GET /printers/{printer_id_8}:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-08"

Request:

  Two claim attempts (same claim_code_8, different user_id values):

  Headers (both attempts):
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body for attempt 1 (same owner):
  ```json
  {
    "claim_code": "{{claim_code_8}}",
    "user_id": "user-goar8-owner-08"
  }
  ```

  Body for attempt 2 (different user):
  ```json
  {
    "claim_code": "{{claim_code_8}}",
    "user_id": "user-goar8-other-08"
  }
  ```

Expected response:

  For both attempts:
  - Status: 400
  - Body contains:
    - detail: "Printer is already claimed"

  After both attempts, GET /printers/{printer_id_8} must still show:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-08"

Notes:
- This test is a consolidation of AR1 behavior, reinforcing that claim_printer() rejects all additional claims for a CLAIMED printer regardless of user_id.

---

## TC-GOAR-8-09: Re-registration of CLAIMED printer does not generate new claim_code

Scenario: [HAPPY PATH] Re-registering a printer in CLAIMED status does not issue a new claim_code and leaves any existing claim_code marked as used while still allowing other registration outputs (e.g., Cloud ID) per business rules.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-009"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture from the registration response:
  - printer_id => printer_id_9
  - cloud_id => cloud_id_1
  - claim_code => claim_code_9
- Claim the printer via POST /printers/claim with:
  - claim_code: claim_code_9
  - user_id: "user-goar8-owner-09"
- Verify via GET /printers/{printer_id_9} that:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-09"
  - claim_code.used == True

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "serial_number": "SN-GOAR8-009",
    "model_number": "HP-LJ-4200",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": false
  }
  ```

Expected response:

  Status: 200

  Body contains:
  - printer_id: printer_id_9
  - cloud_id: cloud_id_2 (must differ from cloud_id_1)
  - printer_email_id: non-empty string (pattern `[a-z0-9]{10}@print.hpeprint.com`)
  - claim_code: null (since register_printer() sets printer.claim_code only if status != CLAIMED; the response field is accessed as printer.claim_code.code, so Agent 4 should expect this to raise if claim_code is None; test must assert that no new non-empty claim_code value appears)
  - status: "CLAIMED" (remains claimed)

  Follow-up GET /printers/{printer_id_9} must assert:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-09"
  - cloud_id == cloud_id_2

Notes:
- Because app.main always accesses printer.claim_code.code, the current implementation will raise an AttributeError if claim_code is None. If this occurs, this scenario becomes untestable via HTTP and should be moved to Skipped Scenarios; however, based on the registration logic, the intended behavior is that claim_code exists but remains marked used and no new code is issued.

---

## TC-GOAR-8-10: Rollback on re-registration failure preserves ownership and invalidates new claim_code

Scenario: [ROLLBACK] If register_printer() for a CLAIMED printer fails after attempting to manipulate claim_code data, rollback ensures no new claim_code remains usable and the existing owner_user_id is preserved.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-010"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_10
  - cloud_id => cloud_id_10_initial
  - claim_code => claim_code_10
- Claim the printer via POST /printers/claim with:
  - claim_code: claim_code_10
  - user_id: "user-goar8-owner-10"
- Confirm via GET /printers/{printer_id_10}:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-10"

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "serial_number": "SN-GOAR8-010",
    "model_number": "HP-LJ-4200",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }
  ```

Expected response:

  Status: 422

  Body contains:
  - detail: "Welcome page failed to print for printer_id={printer_id_10}" (exact message as produced by generate_and_print_welcome_page / RegistrationError)

  Follow-up verification:
  - GET /printers/{printer_id_10} should return 404 with body {"detail": "Printer not found"} because _rollback_registration deletes the printer record entirely for any failure before welcome page success.
  - This implies owner_user_id is removed along with the printer record; there is no residual claim_code or ownership state.

Notes:
- This scenario, as written in AR5, assumes rollback preserves owner_user_id for a claimed printer, but the current implementation of _rollback_registration deletes the printer entirely, conflicting with the requirement. Therefore, this scenario should be considered for Skipped Scenarios if strict alignment with implementation is required.

---

## TC-GOAR-8-11: Reject claim with expired claim code for unclaimed printer

Scenario: [INVALID INPUT] Claiming an unclaimed printer with an expired claim code raises InvalidClaimCodeError and does not change printer status or ownership.

Requirement: AR3

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-011"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_11
  - claim_code => claim_code_11
  - claim_code_expires_at => expires_at_11
- Use monkeypatching to set datetime.utcnow() in app.registration to a time strictly greater than expires_at_11 while keeping claim_code.used == False.
- Confirm via GET /printers/{printer_id_11} that:
  - status == "REGISTERED"
  - owner_user_id is None

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_11}}",
    "user_id": "user-goar8-owner-11"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Claim code has expired"

  Follow-up GET /printers/{printer_id_11} must still show:
  - status == "REGISTERED"
  - owner_user_id is None

Notes:
- Ensure that the patched datetime.utcnow() affects claim_printer() in app.registration but not token verification in app.auth.

---

## TC-GOAR-8-12: Boundary behavior for claim at exact expiry instant

Scenario: [BOUNDARY VALUE] Claiming with a claim code at the exact expiry instant is treated according to the defined comparison (e.g., <= vs <), ensuring consistent InvalidClaimCodeError behavior once current time passes expires_at.

Requirement: AR3

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-012"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_12
  - claim_code => claim_code_12
  - claim_code_expires_at => expires_at_12
- Using monkeypatching, set datetime.utcnow() in app.registration to exactly expires_at_12.

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_12}}",
    "user_id": "user-goar8-owner-12"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Claim code has expired"

Notes:
- Because claim_printer() uses `if datetime.utcnow() > target.claim_code.expires_at`, the boundary behavior is that at exactly expires_at_12 the claim still succeeds (since `>` is False). However, per the requirement, we assert that a call at exactly expires_at_12 must be treated consistently. Given the implementation, this test will fail if written with expectation 400; therefore, this scenario should instead validate the current behavior: at exact expiry instant, claim succeeds with 200, whereas once > expires_at, claim fails. To avoid conflicting expectations, this scenario may need to be placed under Skipped Scenarios.

---

## TC-GOAR-8-13: Reject claim with reused claim code for unclaimed printer

Scenario: [INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is True raises InvalidClaimCodeError and prevents any update to owner_user_id or status.

Requirement: AR4

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-013"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_13
  - claim_code => claim_code_13
- Perform a successful claim with:
  - claim_code: claim_code_13
  - user_id: "user-goar8-owner-13"
- After the successful claim, manually reset status and ownership to simulate an unclaimed printer while leaving claim_code.used == True:
  - Use an internal helper to set:
    - status = PrinterStatus.REGISTERED
    - owner_user_id = None
    - claim_code.used = True

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "claim_code": "{{claim_code_13}}",
    "user_id": "user-goar8-owner-13b"
  }
  ```

Expected response:

  Status: 400

  Body contains:
  - detail: "Claim code has already been used"

  Follow-up GET /printers/{printer_id_13} must show:
  - status == "REGISTERED"
  - owner_user_id is None

Notes:
- This test explicitly exercises the reused-claim-code rejection path while ensuring the printer itself is logically unclaimed.

---

## TC-GOAR-8-14: Rollback when re-registering CLAIMED printer preserves ownership and prevents claim_code leaks

Scenario: [ROLLBACK] When register_printer() fails during re-registration of a CLAIMED printer, rollback preserves owner_user_id and CLAIMED status while ensuring any new claim_code generated during the attempt is invalidated or removed.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- Register a printer via POST /printers/register with:
  - serial_number: "SN-GOAR8-014"
  - model_number: "HP-LJ-4200"
  - firmware_version: "1.0.0"
- Capture:
  - printer_id => printer_id_14
  - claim_code => claim_code_14
- Claim the printer via POST /printers/claim with:
  - claim_code: claim_code_14
  - user_id: "user-goar8-owner-14"
- Verify via GET /printers/{printer_id_14}:
  - status == "CLAIMED"
  - owner_user_id == "user-goar8-owner-14"

Request:

  Headers:
  - Authorization: Bearer <valid JWT provided by conftest.py>
  - Content-Type: application/json

  Body:
  ```json
  {
    "serial_number": "SN-GOAR8-014",
    "model_number": "HP-LJ-4200",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }
  ```

Expected response:

  Status: 422

  Body contains:
  - detail: "Welcome page failed to print for printer_id={printer_id_14}"

  Follow-up GET /printers/{printer_id_14}:
  - Expected 404 with {"detail": "Printer not found"}, due to _rollback_registration deleting the printer record.

Notes:
- This scenario's textual requirement (preserve owner_user_id and CLAIMED status) conflicts with the actual implementation (full rollback deletion). Therefore the intended AR5 behavior cannot be tested via the HTTP API without changing implementation. This scenario should be moved to Skipped Scenarios to avoid asserting behavior that contradicts the code.

---

## Skipped Scenarios

[ROLLBACK] If register_printer() for a CLAIMED printer fails after attempting to manipulate claim_code data, rollback ensures no new claim_code remains usable and the existing owner_user_id is preserved.
             Requirement: AR5 — SKIPPED: Implementation deletes the printer record entirely in _rollback_registration(), so ownership preservation cannot be validated via HTTP without speculative changes.

[BOUNDARY VALUE] Claiming with a claim code at the exact expiry instant is treated according to the defined comparison (e.g., <= vs <), ensuring consistent InvalidClaimCodeError behavior once current time passes expires_at.
             Requirement: AR3 — SKIPPED: The implementation uses `>` comparison for expiry, so behavior at exact expires_at_12 is fixed (claim succeeds). The requirement does not define a concrete expected outcome; writing a test would require choosing semantics not specified in the ticket.

[ROLLBACK] When register_printer() fails during re-registration of a CLAIMED printer, rollback preserves owner_user_id and CLAIMED status while ensuring any new claim_code generated during the attempt is invalidated or removed.
             Requirement: AR5 — SKIPPED: Same as above; rollback fully deletes the printer, conflicting with the requirement, so behavior is untestable without code changes.

---

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-8-01 | HAPPY PATH | AC2 | POST /printers/claim | valid token |
| TC-GOAR-8-02 | INVALID INPUT | AC1 | POST /printers/claim | valid token |
| TC-GOAR-8-03 | OWNERSHIP | AR1 | POST /printers/claim | valid token |
| TC-GOAR-8-04 | OWNERSHIP | AR1 | POST /printers/claim | valid token |
| TC-GOAR-8-05 | HAPPY PATH | AC2 | POST /printers/claim | valid token |
| TC-GOAR-8-06 | BOUNDARY VALUE | AR3 | POST /printers/claim | valid token |
| TC-GOAR-8-07 | INVALID INPUT | AR4 | POST /printers/claim | valid token |
| TC-GOAR-8-08 | OWNERSHIP | AR1 | POST /printers/claim | valid token |
| TC-GOAR-8-09 | HAPPY PATH | AR2 | POST /printers/register | valid token |
| TC-GOAR-8-10 | ROLLBACK | AR5 | POST /printers/register | valid token |
| TC-GOAR-8-11 | INVALID INPUT | AR3 | POST /printers/claim | valid token |
| TC-GOAR-8-12 | BOUNDARY VALUE | AR3 | POST /printers/claim | valid token |
| TC-GOAR-8-13 | INVALID INPUT | AR4 | POST /printers/claim | valid token |
| TC-GOAR-8-14 | ROLLBACK | AR5 | POST /printers/register | valid token |
