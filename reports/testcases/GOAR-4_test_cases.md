# Test Cases — GOAR-4

## TC-GOAR-4-01: Successful registration persists printer record

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a printer record present.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-001".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-001",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "cloud_id": value matching regex "^CID-[A-F0-9]{12}$",
    "printer_email_id": value matching regex "^[a-z0-9]{10}@print.hpeprint.com$",
    "claim_code": value matching regex "^[A-Z0-9]{8}$",
    "status": "REGISTERED"
  }

Notes: After the POST succeeds, Agent 4 should perform a follow-up GET /printers/{printer_id} call (using the same auth state) and assert that the response is 200 and includes the same "printer_id" and "serial_number": "SN-GOAR4-001", confirming that the printer record persists after successful registration.

---

## TC-GOAR-4-02: Failed registration removes printer record

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes the printer record so no printer remains for that printer_id.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-002".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-002",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-002"
  }

Notes: Before invoking the POST, Agent 4 should confirm via GET /printers/{printer_id} that no record exists for this serial (expect 404 when using any placeholder id). After the 422 response, Agent 4 must assert that GET /printers/{printer_id} using the printer_id (if any) mentioned in logs is not possible via the API (expect 404 if a concrete printer_id was created then rolled back). This confirms that no printer record remains after rollback.

---

## TC-GOAR-4-03: Successful registration leaves capabilities present

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a capability record associated with the printer_id.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer or capability record exists yet for serial_number "SN-GOAR4-003".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-003",
    "model_number": "HP-C-MFP-9999",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "status": "REGISTERED"
  }

Notes: This scenario is UNTESTABLE via public HTTP APIs because capability records are not exposed by any endpoint in app/main.py. Agent 4 cannot directly verify that capabilities exist; only internal store functions can see them. Mark this scenario as requiring human clarification or additional endpoints before it can be automated.

---

## TC-GOAR-4-04: Failed registration removes capabilities

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes any capability record associated with the printer_id so none remain.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer or capability record exists yet for serial_number "SN-GOAR4-004".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-004",
    "model_number": "HP-C-MFP-9999",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-004"
  }

Notes: This scenario is UNTESTABLE via public HTTP APIs because capability records are not exposed by any endpoint in app/main.py. Agent 4 cannot verify deletion of capabilities through the API surface; it would require direct access to app.store. Flag this test as needing additional API support or test hooks before implementation.

---

## TC-GOAR-4-05: Successful registration allows serial lookup

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and allows lookup of the printer via its serial number.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-005".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-005",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.2",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "status": "REGISTERED",
    "history": list containing an entry with substring "Registration started"
  }

Notes: Serial-number lookup is not exposed by any endpoint in app/main.py (only lookup by printer_id is available). This scenario is therefore UNTESTABLE through the current API; Agent 4 cannot call store.get_printer_by_serial from tests. Mark as requiring a future GET /printers/by-serial/{serial_number} endpoint or similar before it can be automated.

---

## TC-GOAR-4-06: Failed registration frees serial for reuse

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes the serial index so a subsequent registration using the same serial number behaves like a fresh registration.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-006".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: First call (failure): {
    "serial_number": "SN-GOAR4-006",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-006"
  }

Notes: After the failed registration, Agent 4 should perform a second POST /printers/register for the same serial_number with simulate_welcome_page_failure set to false and assert a 200 response with status "REGISTERED" and a new printer_id. This confirms that the serial number behaves like a fresh registration. Reset of in-memory store between tests is handled by the test harness; no explicit reset_store call is needed here.

---

## TC-GOAR-4-07: Successful registration unaffected by rollback changes

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing persists printer, capabilities, and serial index and is not impacted by rollback changes.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-007".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-007",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.3",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "cloud_id": value matching regex "^CID-[A-F0-9]{12}$",
    "status": "REGISTERED"
  }

Notes: To confirm successful registrations are not impacted by rollback changes, Agent 4 should perform this successful registration after running a separate test that triggers rollback (e.g., TC-GOAR-4-06). The result should still be 200 with a valid printer record. No explicit rollback is expected in logs or behavior for this path.

---

## TC-GOAR-4-08: Missing Authorization header rejects registration and leaves no records

Scenario: [AUTH] Registration attempt without an Authorization header is rejected and does not create any printer, capability, or serial index records.

Requirement: AC4

Endpoint: POST /printers/register

Auth: missing token (pass headers={} to override conftest.py default)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-008".

Request:

  Headers: {}

  Body: {
    "serial_number": "SN-GOAR4-008",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": [validation error message indicating missing Authorization header]
  }

Notes: FastAPI will return a 422 Unprocessable Entity because the verify_token dependency requires the Authorization header. After the 422, Agent 4 should not expect any printer record to exist; however, this cannot be verified via serial lookup or capabilities, only indirectly by ensuring no side effects are asserted in other tests that reuse this serial number.

---

## TC-GOAR-4-09: Invalid token rejects registration and leaves no records

Scenario: [AUTH] Registration attempt with an invalid or expired token is rejected and does not create any printer, capability, or serial index records.

Requirement: AC4

Endpoint: POST /printers/register

Auth: invalid token (pass headers={"Authorization": "Bearer invalid_token"} to override default)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-009".

Request:

  Headers: {
    "Authorization": "Bearer invalid_token",
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-009",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.4",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 401

  Body contains: {
    "detail": "Invalid or expired token"
  }

Notes: Because verify_token raises HTTPException(401) before reaching registration.register_printer, no printer, capability, or serial index data will be created. Agent 4 can indirectly validate this by later reusing "SN-GOAR4-009" in a successful registration test and confirming it behaves like a first-time registration.

---

## TC-GOAR-4-10: Idempotent rollback leaves no records after multiple calls

Scenario: [ROLLBACK] Calling rollback multiple times for the same failed registration leaves no printer record, capability record, or serial index for that serial number.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-010".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-010",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-010"
  }

Notes: This scenario is UNTESTABLE strictly from the HTTP API because multiple calls to _rollback_registration are internal implementation details. Agent 4 can only observe a single 422 error. Verifying that a second internal rollback call is harmless would require direct access to the registration._rollback_registration function or store mocks. Mark as requiring lower-level tests beyond API scope.

---

## TC-GOAR-4-11: Second rollback call completes without errors

Scenario: [BOUNDARY VALUE] A second rollback call after records are already deleted completes without raising errors caused by missing printer, capability, or serial index data.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-011".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-011",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-011"
  }

Notes: Like TC-GOAR-4-10, the second rollback invocation is not exposed via the HTTP API. The API returns only one 422 per failed call. This scenario is UNTESTABLE at the API layer and should be validated with unit tests around _rollback_registration using a fake store.

---

## TC-GOAR-4-12: Rollback deletes only failing printer’s capabilities

Scenario: [HAPPY PATH] Rollback for a failed registration deletes capabilities only for the failing printer_id and leaves capabilities for other printer_ids intact.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: Two distinct serial numbers are unused: "SN-GOAR4-012A" and "SN-GOAR4-012B".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: First, successful registration for serial "SN-GOAR4-012A": {
    "serial_number": "SN-GOAR4-012A",
    "model_number": "HP-C-MFP-9999",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "status": "REGISTERED"
  }

Notes: This scenario is UNTESTABLE via API because capabilities for each printer_id are not exposed. Rollback scoping to a specific printer_id cannot be observed through available endpoints. Mark as needing store-level or integration tests with additional API support.

---

## TC-GOAR-4-13: Rollback does not delete capabilities for other printers or owners

Scenario: [OWNERSHIP] Rollback for a failed registration of one printer_id does not delete or modify capability records belonging to other printers or owners.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: One printer has been successfully registered and claimed: serial_number "SN-GOAR4-013A" is registered and claimed by user "user-goar4-owner"; another serial_number "SN-GOAR4-013B" is unused.

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: Failed registration for serial "SN-GOAR4-013B": {
    "serial_number": "SN-GOAR4-013B",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-013B"
  }

Notes: Capability modification for other printers cannot be verified through the public API. However, Agent 4 can at least assert that after the failure, GET /printers/{printer_id_of_013A} still returns 200 with status "CLAIMED" and owner_user_id "user-goar4-owner". The specific capability records remain UNOBSERVABLE via API, so full AR2 verification is UNTESTABLE at this layer.

---

## TC-GOAR-4-14: Fresh registration after rollback behaves as first-time registration

Scenario: [HAPPY PATH] After rollback from a failed registration, a subsequent registration with the same serial_number behaves exactly like a first-time registration.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-014".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: First call (failure): {
    "serial_number": "SN-GOAR4-014",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-014"
  }

Notes: After the failed registration, Agent 4 should call POST /printers/register again with the same serial_number, same model_number, firmware_version "1.0.1", and simulate_welcome_page_failure=false. The second call should return 200 with a new printer_id, status "REGISTERED", and a cloud_id matching the CID pattern, confirming first-time registration behavior after rollback.

---

## TC-GOAR-4-15: After rollback, serial lookup shows no residual mapping

Scenario: [ROLLBACK] After rollback, lookups by the failed serial_number show no residual serial index or printer mapping that would block reuse.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-015".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-015",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-015"
  }

Notes: Direct serial lookup is not available via the API, so residual serial index state is UNTESTABLE from the HTTP layer. As in TC-GOAR-4-14, Agent 4 can infer absence of blocking state by performing a subsequent successful registration for the same serial and asserting 200 with a new printer_id, but it cannot directly inspect the serial index. Mark the direct lookup aspect as UNTESTABLE via current endpoints.

---

## TC-GOAR-4-16: Rollback does not alter already-claimed printers

Scenario: [HAPPY PATH] Rollback for a failed registration of a new printer_id does not alter the records or claim state of any already-claimed printers.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: One printer has been registered and claimed: serial_number "SN-GOAR4-016A" registered with model_number "HP-LJ-2055" and claimed by user_id "user-goar4-claim" via POST /printers/claim. A second serial_number "SN-GOAR4-016B" is unused.

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: Failed registration for "SN-GOAR4-016B": {
    "serial_number": "SN-GOAR4-016B",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-016B"
  }

Notes: Before triggering the failed registration, Agent 4 should call GET /printers/{printer_id_of_016A} and assert status 200, status "CLAIMED", and owner_user_id "user-goar4-claim". After the failed registration and rollback, Agent 4 must call GET /printers/{printer_id_of_016A} again and assert these fields are unchanged, confirming rollback did not alter the claimed printer.

---

## TC-GOAR-4-17: Rollback does not modify other CLAIMED printers

Scenario: [OWNERSHIP] Rollback invoked for a failed registration does not delete or modify printer, capability, or serial index data for any other CLAIMED printer.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: Two printers have been registered and claimed: serial "SN-GOAR4-017A" claimed by "user-goar4-alpha" and serial "SN-GOAR4-017B" claimed by "user-goar4-beta". A third serial "SN-GOAR4-017C" is unused.

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: Failed registration for unused serial "SN-GOAR4-017C": {
    "serial_number": "SN-GOAR4-017C",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-017C"
  }

Notes: After the failed registration, Agent 4 should call GET /printers/{printer_id_of_017A} and GET /printers/{printer_id_of_017B} and assert both still return 200 with status "CLAIMED" and owner_user_id values unchanged. Capability and serial index data remain UNOBSERVABLE; ensure no deletions are inferred from API responses.

---

## TC-GOAR-4-18: Successful registration does not invoke rollback

Scenario: [HAPPY PATH] A successful registration where the Welcome Page prints does not call rollback and preserves printer, capability, and serial index data.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-018".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-018",
    "model_number": "HP-LJ-2055",
    "firmware_version": "2.0.0",
    "simulate_welcome_page_failure": false
  }

Expected response:

  Status: 200

  Body contains: {
    "printer_id": <non-empty string>,
    "status": "REGISTERED"
  }

Notes: Whether _rollback_registration is called internally cannot be observed directly from API responses. Agent 4 should treat this as a standard successful registration test. Any verification that rollback is not invoked should be deferred to unit tests with mocks on store.delete_printer/remove_serial_index/delete_capabilities. This scenario is partially UNTESTABLE at API level for the rollback invocation detail.

---

## TC-GOAR-4-19: Rollback on failed registration does not affect later successful registration

Scenario: [ROLLBACK] Failed registration attempts that invoke rollback do not trigger rollback during later successful registrations for the same serial_number.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-019".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: First call (failure): {
    "serial_number": "SN-GOAR4-019",
    "model_number": "HP-LJ-2055",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-019"
  }

Notes: After the failed registration, Agent 4 should perform a second POST /printers/register with the same serial_number, model_number "HP-LJ-2055", firmware_version "1.0.1", and simulate_welcome_page_failure=false. The second call should return 200 with status "REGISTERED" and a valid cloud_id, showing that rollback from the first attempt does not cause subsequent success to be rolled back.

---

## TC-GOAR-4-20: Capabilities for failed registration not externally visible via API

Scenario: [ROLLBACK] After rollback of a failed registration, no capability records for that printer_id are returned by downstream capability or device list queries.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-020".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-020",
    "model_number": "HP-C-MFP-9999",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-020"
  }

Notes: There are no capability or device list endpoints in app/main.py, so this scenario is UNTESTABLE at the HTTP API layer. Downstream queries cannot be simulated without additional services or endpoints. Mark as requiring broader system integration to validate AR6.

---

## TC-GOAR-4-21: Capability records deleted before any external observation

Scenario: [BOUNDARY VALUE] Capability records created during a failed registration are deleted by rollback before any subsequent external query can observe them.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-021".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-021",
    "model_number": "HP-C-MFP-9999",
    "firmware_version": "1.0.1",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-021"
  }

Notes: As with TC-GOAR-4-20, capability visibility cannot be tested via the current API. Agent 4 can only assert that the POST returns 422; verifying deletion timing relative to external queries requires additional observability or API endpoints. Mark as UNTESTABLE at API level for the timing aspect.

---

## TC-GOAR-4-22: Registration rollback for model family boundary case

Scenario: [BOUNDARY VALUE] Capability records created during a failed registration are deleted by rollback before any subsequent external query can observe them.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: No printer record exists yet for serial_number "SN-GOAR4-022".

Request:

  Headers: {
    "Content-Type": "application/json"
  }

  Body: {
    "serial_number": "SN-GOAR4-022",
    "model_number": "HP-LJ-001",
    "firmware_version": "1.0.0",
    "simulate_welcome_page_failure": true
  }

Expected response:

  Status: 422

  Body contains: {
    "detail": "Welcome page failed to print for printer_id=SN-GOAR4-022"
  }

Notes: This test uses the model_number boundary case "HP-LJ-001" to ensure rollback behaves correctly even for models at the edge of the _model_family heuristic. As with other AR6 scenarios, capability deletion timing is UNTESTABLE via current API endpoints. Focus on ensuring the failure yields 422 and that subsequent successful registration for the same serial_number works as expected if implemented in additional tests.

---

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-4-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-02 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-03 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-4-04 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-4-05 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-06 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-07 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-08 | AUTH | AC4 | POST /printers/register | missing token |
| TC-GOAR-4-09 | AUTH | AC4 | POST /printers/register | invalid token |
| TC-GOAR-4-10 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-11 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-12 | HAPPY PATH | AR2 | POST /printers/register | valid token |
| TC-GOAR-4-13 | OWNERSHIP | AR2 | POST /printers/register | valid token |
| TC-GOAR-4-14 | HAPPY PATH | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-15 | ROLLBACK | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-16 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-4-17 | OWNERSHIP | AR4 | POST /printers/register | valid token |
| TC-GOAR-4-18 | HAPPY PATH | AR5 | POST /printers/register | valid token |
| TC-GOAR-4-19 | ROLLBACK | AR5 | POST /printers/register | valid token |
| TC-GOAR-4-20 | ROLLBACK | AR6 | POST /printers/register | valid token |
| TC-GOAR-4-21 | BOUNDARY VALUE | AR6 | POST /printers/register | valid token |
| TC-GOAR-4-22 | BOUNDARY VALUE | AR6 | POST /printers/register | valid token |
