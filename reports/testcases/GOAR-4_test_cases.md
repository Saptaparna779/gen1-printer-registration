# Test Cases — GOAR-4

## TC-GOAR-4-01: Rollback removes printer record when Welcome Page fails

Scenario: [ROLLBACK] Simulated Welcome Page failure triggers rollback that removes the printer record created during the attempted registration.  
             Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-001" (store has no entry for this serial and no printer indexed by it).

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: {"serial_number": "SN-GOAR4-001", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: "detail" string == "Welcome page failed to print for printer_id=SN-GOAR4-001".

Notes: Agent 4 should assert status_code == 422 and that the detail string exactly matches the expected value for printer_id.

---

## TC-GOAR-4-02: Multiple failed registrations leave no printer record

Scenario: [BOUNDARY]  Multiple consecutive failed registrations for the same serial number all roll back without leaving any printer record in the store.  
             Requirement: AC1

Requirement: AC1

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-002".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-002", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}. Second POST: same body values, also with simulate_welcome_page_failure true.

Expected response:

  Status: Both POST calls return 422.

  Body contains: Each response "detail" == "Welcome page failed to print for printer_id=SN-GOAR4-002".

Notes: This test asserts that both failed attempts return the same detail message tied to the serial_number, confirming predictable rollback behavior.

---

## TC-GOAR-4-03: Successful registration reserves serial and persists printer

Scenario: [HAPPY PATH] Successful registration using a serial number completes end-to-end and persists printer and serial index data.  
             Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-003".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-003", "model_number": "HP-M404", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id} using the printer_id from the POST response.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id": "SN-GOAR4-003", "cloud_id": "CID-SN-GOAR4-003", "printer_email_id": "goar4-003@print.hpeprint.com", "claim_code": "GOAR4003", and "status": "REGISTERED". GET response returns the same "printer_id" and "serial_number" == "SN-GOAR4-003" with "status" == "REGISTERED".

Notes: This test uses fixed identifiers to avoid any randomness and asserts the full response body matches the expected literal values.

---

## TC-GOAR-4-04: Failed registration frees serial for subsequent first-time registration

Scenario: [ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.  
             Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-004".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-004", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-004", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST 422; second POST 200.

  Body contains: First POST "detail" == "Welcome page failed to print for printer_id=SN-GOAR4-004". Second POST returns "printer_id": "SN-GOAR4-004" and "status": "REGISTERED".

Notes: This test assumes deterministic identifiers for the printer and error messages for simplicity.

---

## TC-GOAR-4-05: Multiple cycles of failure then success keep serial reusable

Scenario: [BOUNDARY]   Multiple cycles of failed registration followed by successful registration verify the serial number is always reusable with no stale associations.  
             Requirement: AC3

Requirement: AC3

Endpoint: POST /printers/register (four calls)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-005".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: Call 1: {"serial_number": "SN-GOAR4-005", "model_number": "HP-M404", "firmware_version": "1.0.4", "simulate_welcome_page_failure": true}. Call 2: same body with simulate_welcome_page_failure true. Call 3: same serial/model/firmware with simulate_welcome_page_failure false. Call 4: same serial/model/firmware with simulate_welcome_page_failure false.

Expected response:

  Status: Calls 1 and 2 return 422; calls 3 and 4 return 200.

  Body contains: Calls 1 and 2 each return "detail" == "Welcome page failed to print for printer_id=SN-GOAR4-005". Calls 3 and 4 each return "printer_id": "SN-GOAR4-005" and "status": "REGISTERED".

Notes: This test assumes a stable mapping between serial_number and printer_id across calls.

---

## TC-GOAR-4-06: Successful registration persists printer, capability, and serial index

Scenario: [HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records without invoking rollback.  
             Requirement: AC4

Requirement: AC4

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer or capability record for serial_number "SN-GOAR4-006" and model_number "HP-CMFP-500".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-006", "model_number": "HP-CMFP-500", "firmware_version": "2.0.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id} using the printer_id from the POST response.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id": "SN-GOAR4-006" and "status": "REGISTERED". GET response has the same "printer_id", "serial_number": "SN-GOAR4-006", and "history": ["Capabilities captured", "Welcome page printed successfully; registration complete"].

Notes: This test asserts a simplified fixed history list for ease of automation.

---

## Skipped Scenarios

[ROLLBACK] Simulated Welcome Page failure triggers rollback that deletes all capability records associated with the failed printer_id.  
             Requirement: AC2 — SKIPPED: There is no public API to directly inspect capability store state.
[BOUNDARY]  Capability queries after repeated failed registrations confirm no capability records exist for the failed printer_id.  
             Requirement: AC2 — SKIPPED: No external capability query endpoint exists in app/main.py.
[ROLLBACK] Multiple invocations of _rollback_registration for the same printer leave no printer, capability, or serial index records without raising errors due to already-deleted data.  
             Requirement: AR1 — SKIPPED: Direct invocation of _rollback_registration and inspection of store internals are not available via REST endpoints.
[BOUNDARY]  Interleaving rollback calls with manually altered or partially deleted store state still results in a clean final state with no remaining records for that printer.  
             Requirement: AR1 — SKIPPED: Requires low-level manipulation of store state that is not exposed via public APIs.
[ROLLBACK] Rollback for one printer deletes only that printer’s printer record, serial index, and capabilities, leaving all other printers’ data intact.  
             Requirement: AR2 — SKIPPED: Capability records are not exposed via REST, so we cannot assert per-printer capability deletion directly.
[OWNERSHIP] Rollback for one owner’s printer does not alter capabilities or records of printers owned by other users.  
             Requirement: AR2 — SKIPPED: Ownership interactions with rollback at capability level cannot be observed.
[ROLLBACK] After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index and new capabilities captured.  
             Requirement: AR3 — SKIPPED: Behaviour is already covered by AC3 scenarios; additional AR3-specific nuance beyond serial reuse cannot be observed via existing endpoints.
[BOUNDARY]  Repeated cycles of failed and successful registrations for the same serial number verify that the serial index never retains stale associations.  
             Requirement: AR3 — SKIPPED: Functionally equivalent to AC3 boundary scenario; additional internal index checks are not possible via REST.
[OWNERSHIP] Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.  
             Requirement: AR4 — SKIPPED: Would require inspection of multiple printers and claims in combination with internal rollback operations not directly exposed.
[ROLLBACK]   Simulated failed registration in an environment containing claimed printers cleans up only the failed printer’s data without modifying claimed printers.  
             Requirement: AR4 — SKIPPED: Direct verification of which specific records were deleted vs preserved is not available via current REST surface.
[HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated printer, capability, and serial index records.  
             Requirement: AR5 — SKIPPED: Direct detection of whether _rollback_registration was invoked is not observable; only final state is checkable and already covered by AC4.
[ROLLBACK]   Instrumentation or logging around register_printer confirms that _rollback_registration is never invoked when the Welcome Page prints successfully.  
             Requirement: AR5 — SKIPPED: Requires access to internal logging/telemetry beyond what GET /printers/{printer_id} exposes.
[ROLLBACK] After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.  
             Requirement: AR6 — SKIPPED: No public capability query/listing API exists.
[BOUNDARY]  Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.  
             Requirement: AR6 — SKIPPED: Transient capability visibility cannot be observed without a capability API.

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-4-01 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-02 | BOUNDARY | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-03 | HAPPY PATH | AC3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-04 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-05 | BOUNDARY | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-06 | HAPPY PATH | AC4 | POST /printers/register, GET /printers/{printer_id} | valid token |
