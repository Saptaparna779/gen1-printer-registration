# Test Cases — GOAR-4

## TC-GOAR-4-01: Successful registration leaves printer record present

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a printer record present.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: 
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-001".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-001", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: 
  - "printer_id": non-empty string
  - "cloud_id": string starting with "CID-"
  - "status": "REGISTERED"

Notes: After the POST, Agent 4 should call GET /printers/{printer_id} with the returned printer_id and assert 200 plus matching printer_id and serial_number "SN-GOAR4-001" to confirm the printer record remains.

---

## TC-GOAR-4-02: Failed registration removes printer record via rollback

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes the printer record so no printer remains for that printer_id.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions: 
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-002".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-002", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: 
  - "detail": string containing "Welcome page failed to print"

Notes: This is a rollback test. Before action, no printer exists for this serial. Action is the failing POST. After action, Agent 4 must call GET /printers/{printer_id_attempted} using the printer_id captured from logs or a prior successful attempt is not available; instead, Agent 4 should verify via store-level helpers (reset_store fixture context) that store.get_printer_by_serial("SN-GOAR4-002") is None. Since the API never returns the temporary printer_id on failure, state verification must be done indirectly by asserting GET /printers/{some_random_id} returns 404 for unrelated IDs and that no registration history for SN-GOAR4-002 exists if accessible.

---

## TC-GOAR-4-03: Successful registration leaves capability record present

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a capability record associated with the printer_id.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-003".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-003", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string (capture as printer_id)
  - "status": "REGISTERED"

Notes: Agent 4 should verify that capabilities were persisted by using store.get_capabilities(printer_id) in tests (via fixtures) and asserting a non-None result with supports_print=True, supports_scan=True, supports_color=True given model_number "HP-C-MFP-9999".

---

## TC-GOAR-4-04: Failed registration removes capability record via rollback

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes any capability record associated with the printer_id so none remain.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-004".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-004", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. Before action, no capabilities exist for this printer_id or serial. Action is the failing POST. After action, Agent 4 must assert that store.get_capabilities_for_serial("SN-GOAR4-004") or equivalent store lookup returns None; if only printer_id-based lookup exists, first confirm that no printer is present for that serial and then assert no capability mapping exists in store for any printer with that serial. Use reset_store fixture to isolate state.

---

## TC-GOAR-4-05: Successful registration allows lookup by serial index

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing completes and allows lookup of the printer via its serial number.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-005".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-005", "model_number": "HP-LJ-2060", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string (capture as printer_id)
  - "status": "REGISTERED"

Notes: After the POST, Agent 4 should verify that the serial index is populated by using a store.get_printer_by_serial("SN-GOAR4-005") helper if available, and that it returns the same printer_id. If only API-level verification is allowed, this can be implicitly confirmed by the absence of 422 errors on duplicate registration workflows in other tests.

---

## TC-GOAR-4-06: Failed registration frees serial number for reuse

Scenario: [ROLLBACK] Registration where Welcome Page printing fails removes the serial index so a subsequent registration using the same serial number behaves like a fresh registration.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-006".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-006", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. Before action, serial_number "SN-GOAR4-006" is unused. Action is the failing POST. After action, Agent 4 must perform a second POST /printers/register with the same body but simulate_welcome_page_failure=false and assert 200 with a new printer_id and cloud_id. This confirms that the serial index was cleared and the subsequent registration behaves like a fresh registration. Use reset_store to isolate the test.

---

## TC-GOAR-4-07: Successful registration persists all data and is unaffected by rollback changes

Scenario: [HAPPY PATH] Successful registration with Welcome Page printing persists printer, capabilities, and serial index and is not impacted by rollback changes.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-007".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-007", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string (capture as printer_id)
  - "cloud_id": string starting with "CID-"
  - "status": "REGISTERED"

Notes: After the successful registration, Agent 4 should verify that a subsequent unrelated failing registration for a different serial number (e.g., SN-GOAR4-007F) with simulate_welcome_page_failure=true does not affect the original printer: GET /printers/{printer_id} must still return 200 with unchanged printer_id and serial_number. This ensures rollback changes are scoped.

---

## TC-GOAR-4-08: Registration without Authorization header is rejected without creating data

Scenario: [AUTH] Registration attempt without an Authorization header is rejected and does not create any printer, capability, or serial index records.

Requirement: AC4

Endpoint: POST /printers/register

Auth: missing token (pass headers={} to override conftest.py default)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-008".

Request:

  Headers: {} (overrides default to omit Authorization)

  Body: {"serial_number": "SN-GOAR4-008", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 422

  Body contains:
  - Validation error payload from FastAPI indicating missing Authorization header

Notes: After the rejected call, Agent 4 should confirm that no printer was created for serial_number "SN-GOAR4-008" by checking that a subsequent authorized registration with the same serial_number succeeds with 200 and behaves as a fresh registration.

---

## TC-GOAR-4-09: Registration with invalid token is rejected without creating data

Scenario: [AUTH] Registration attempt with an invalid or expired token is rejected and does not create any printer, capability, or serial index records.

Requirement: AC4

Endpoint: POST /printers/register

Auth: invalid token (pass headers={"Authorization": "Bearer invalid_token"} to override default)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-009".

Request:

  Headers: {"Authorization": "Bearer invalid_token", "Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-009", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 401

  Body contains:
  - "detail": "Invalid or expired token"

Notes: After the rejected call, Agent 4 should confirm that no printer was created for serial_number "SN-GOAR4-009" by issuing a validly authorized registration with the same serial_number and asserting 200 with status "REGISTERED".

---

## TC-GOAR-4-10: Non-simulated pre-Welcome-Page failure triggers rollback

Scenario: [HAPPY PATH] A non-simulated failure before the Welcome Page prints triggers rollback that removes printer record, capability record, and serial index.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-010".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 422

  Body contains:
  - "detail": "serial_number, model_number and firmware_version are required"

Notes: This uses a validation-style failure to simulate a pre-Welcome-Page error; rollback must ensure that no printer, capability, or serial index is created for the invalid request. Agent 4 should assert that store.get_printer_by_serial("") returns None and that no capabilities exist for any printer with an empty serial; since such a serial is invalid, the primary assertion is that no state changes occur.

---

## TC-GOAR-4-11: Simulated and real WelcomePagePrintError both invoke rollback

Scenario: [ROLLBACK] Simulated Welcome Page print failure and a real WelcomePagePrintError both invoke rollback so that no partial printer, capability, or serial index data remains afterward.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-011A" or "SN-GOAR4-011B".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: For simulated failure: {"serial_number": "SN-GOAR4-011A", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}; for real failure, configure test double of generate_and_print_welcome_page to raise WelcomePagePrintError for serial_number "SN-GOAR4-011B" with simulate_welcome_page_failure=false.

Expected response:

  Status: 422 for both calls

  Body contains:
  - "detail": string containing "Welcome page failed to print" for each failure

Notes: Rollback test. Before each action, no state exists for the respective serial. After each failing POST, Agent 4 must assert via store helpers that both printers remain absent (get_printer_by_serial returns None), no capabilities exist for their printer_ids, and their serial numbers can be reused in a subsequent successful registration.

---

## TC-GOAR-4-12: Failed registration with capabilities created leaves none after rollback

Scenario: [ROLLBACK] A failed registration where capabilities were created during the current attempt leaves no capability record for the printer_id after rollback, avoiding orphans.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-012".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-012", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. Because capabilities are captured before the Welcome Page, this failure path exercises deletion of capabilities. Agent 4 should assert that no capabilities remain for the failed printer after rollback by checking store.get_capabilities_for_serial("SN-GOAR4-012") or equivalent, and that a subsequent successful registration with the same serial_number creates fresh capabilities.

---

## TC-GOAR-4-13: Rollback is safe when no capabilities exist

Scenario: [BOUNDARY VALUE] Rollback on a failed registration where no capability record exists for the printer_id completes without error and still deletes any printer record and serial index.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-013".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-013", "model_number": "HP-LJ-001", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. This scenario assumes an implementation detail (capabilities may not yet exist) that cannot be guaranteed solely via public API; therefore Agent 4 should mark this scenario as UNTESTABLE at the API level and skip automated implementation until store-level hooks to simulate missing capabilities during rollback are available.

---

## TC-GOAR-4-14: Serial index not stale after rollback

Scenario: [ROLLBACK] After rollback from a failed registration, lookups by the failed serial number do not return any stale printer_id mapping.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-014".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-014", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. After the failing POST, Agent 4 should assert via store.get_printer_by_serial("SN-GOAR4-014") that no printer_id is mapped to this serial. A subsequent successful registration with the same serial_number must behave as a fresh registration and confirm that a new mapping is created.

---

## TC-GOAR-4-15: Serial index removed even if printer record was never persisted

Scenario: [BOUNDARY VALUE] Failed registration where serial index was created but printer record was never persisted still removes the serial index during rollback so the serial can be reused.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-015".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-015", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. This boundary case depends on an internal ordering where the serial index may be written before the printer record is fully persisted; since this cannot be forced via the public API, Agent 4 should mark this scenario as UNTESTABLE and skip implementation until hooks are provided to simulate partial persistence.

---

## TC-GOAR-4-16: Rollback does not affect unrelated printers

Scenario: [HAPPY PATH] Failed registration for a new printer rolls back printer, capability, and serial index for that printer_id while leaving existing printers untouched.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset.
- A baseline printer is registered successfully with serial_number "SN-GOAR4-016A" and model_number "HP-LJ-2055".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-016B", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. After the failing registration for "SN-GOAR4-016B", Agent 4 should assert that the baseline printer "SN-GOAR4-016A" is still present and unchanged via GET /printers/{baseline_printer_id}, while no printer or capabilities exist for "SN-GOAR4-016B" and its serial can be reused in a later successful registration.

---

## TC-GOAR-4-17: Rollback for one printer does not modify others' data

Scenario: [OWNERSHIP] Rollback for a failed registration of one printer_id does not delete or modify printer records, capabilities, or serial indices belonging to other printers.

Requirement: AR4

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset.
- Two printers are registered successfully upfront: serial_number "SN-GOAR4-017A" with model_number "HP-LJ-2055" and serial_number "SN-GOAR4-017B" with model_number "HP-C-MFP-9999".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-017C", "model_number": "HP-LJ-2060", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains:
  - "detail": string containing "Welcome page failed to print"

Notes: Rollback test. After the failing registration for "SN-GOAR4-017C", Agent 4 must call GET /printers/{printer_id_A} and GET /printers/{printer_id_B} and assert both still return 200 with their original serial_number and model_number values. Also assert that no printer or capabilities exist for "SN-GOAR4-017C".

---

## TC-GOAR-4-18: Successful registration after prior failures persists all data

Scenario: [HAPPY PATH] After one or more failed registration attempts that rolled back fully, a subsequent successful registration for the same serial number persists printer, capability, and serial index data.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-018".
- At least one prior failed registration has been executed for "SN-GOAR4-018" using simulate_welcome_page_failure=true.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-018", "model_number": "HP-C-MFP-9999", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string (capture as printer_id)
  - "status": "REGISTERED"

Notes: After the successful registration, Agent 4 should assert that capabilities are present for printer_id and that store.get_printer_by_serial("SN-GOAR4-018") returns printer_id. This confirms that prior rollbacks did not prevent a subsequent successful registration from persisting full state.

---

## TC-GOAR-4-19: Rollback does not remove data from later successful registration

Scenario: [ROLLBACK] Previous failed registrations that invoked rollback do not remove or corrupt printer, capability, or serial index data created by a later successful registration.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- Test store is reset so no existing printer uses serial_number "SN-GOAR4-019".
- One failed registration has been executed for "SN-GOAR4-019" (simulate_welcome_page_failure=true) and then one successful registration for the same serial_number (simulate_welcome_page_failure=false).

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-019", "model_number": "HP-LJ-2055", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string (capture as printer_id_latest)
  - "status": "REGISTERED" or "CLAIMED" depending on prior operations

Notes: Rollback test. After this additional successful registration, Agent 4 should ensure that no subsequent rollback is triggered for past failures and that the final printer state (queried via GET /printers/{printer_id_latest}) shows consistent serial_number, model_number, and capabilities. This primarily validates that rollback logic is only invoked on failure and does not retroactively affect successful registrations.

---

## TC-GOAR-4-20: UNTESTABLE scenario for AR2 boundary condition

Scenario: [ROLLBACK] Previous failed registrations that invoked rollback do not remove or corrupt printer, capability, or serial index data created by a later successful registration.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed)

Preconditions:
- This scenario is UNTESTABLE with current public APIs and store hooks.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR4-020", "model_number": "HP-LJ-2055", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains:
  - "printer_id": non-empty string

Notes: This scenario is marked UNTESTABLE because it duplicates AR5 behavior already covered and introduces no new observable behavior. Agent 4 should skip this test and treat it as documentation only.

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
| TC-GOAR-4-10 | HAPPY PATH | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-11 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-12 | ROLLBACK | AR2 | POST /printers/register | valid token |
| TC-GOAR-4-13 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-4-14 | ROLLBACK | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-15 | BOUNDARY VALUE | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-16 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-4-17 | OWNERSHIP | AR4 | POST /printers/register | valid token |
| TC-GOAR-4-18 | HAPPY PATH | AR5 | POST /printers/register | valid token |
| TC-GOAR-4-19 | ROLLBACK | AR5 | POST /printers/register | valid token |
| TC-GOAR-4-20 | ROLLBACK | AR5 | POST /printers/register | valid token |


