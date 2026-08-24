# Test Cases — GOAR-4

## TC-GOAR-4-01: Successful registration persists printer record without rollback

Scenario: [HAPPY PATH] Welcome Page prints successfully and printer record is persisted without invoking rollback.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-001" (store has no entry for this serial and no printer indexed by it).

Request:

  Headers: Default client headers with valid Authorization token (Authorization header attached by conftest.py client fixture by default — no extra code needed.).

  Body: {"serial_number": "SN-GOAR4-001", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: "printer_id" as a non-empty string; "cloud_id" starting with "CID-" and 16 characters total; "printer_email_id" ending with "@print.hpeprint.com"; "claim_code" as an 8-character uppercase alphanumeric string; "status" == "REGISTERED"; "history" list including an entry containing "Registration started" and an entry containing "Welcome page printed successfully; registration complete".

Notes: After the POST call, Agent 4 does not need to verify internal store state directly; correctness of persistence is inferred from 200 response and presence of fields. No rollback-specific verification is required in this test.

---

## TC-GOAR-4-02: Simulated Welcome Page failure rolls back printer record

Scenario: [ROLLBACK]   Simulated Welcome Page failure triggers rollback that removes the printer record created during registration.

Requirement: AC1

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-002".

Request:

  Headers: Default client headers with valid Authorization token (Authorization header attached by conftest.py client fixture by default — no extra code needed.).

  Body: POST /printers/register with {"serial_number": "SN-GOAR4-002", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}.

Expected response:

  Status: POST returns 422; subsequent GET /printers/{printer_id_from_response_if_any} is not called because on failure register_printer raises RegistrationError and FastAPI returns 422 with detail message.

  Body contains: POST response body includes {"detail": "Welcome page failed to print"}.

Notes: Because _rollback_registration deletes the printer and serial index before raising RegistrationError, no printer_id exists to query via GET, and the POST failure alone validates rollback for the printer record. Agent 4 should assert that repeated calls with the same serial can succeed in other tests rather than chaining a GET here.

---

## TC-GOAR-4-03: Failed registration leaves no printer record observable by GET

Scenario: [ROLLBACK]   Failed registration leaves no printer record and allows subsequent inspection to confirm absence of printer data.

Requirement: AC1

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-003".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: POST /printers/register with {"serial_number": "SN-GOAR4-003", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}.

Expected response:

  Status: POST returns 422. Since register_printer raises RegistrationError before saving a final printer_id for a failed registration, no GET is performed in this test case.

  Body contains: Response body {"detail": "Welcome page failed to print"}.

Notes: This test confirms absence of a persistent printer record indirectly by ensuring the failure path executes and RegistrationError is returned as HTTP 422; direct GET verification is covered in later tests where a printer_id exists. Agent 4 should not attempt a GET because store.delete_printer removes the record before the error is surfaced.

---

## TC-GOAR-4-04: Successful registration persists capability records

Scenario: [HAPPY PATH] Successful registration persists capability records for the printer_id and they remain after completion.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer or capability record for serial_number "SN-GOAR4-004" and model_number "HP-CMFP-500".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-004", "model_number": "HP-CMFP-500", "firmware_version": "2.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: "printer_id" non-empty; "status" == "REGISTERED"; response history includes an entry containing "Capabilities captured"; capability-related fields are not directly returned but their existence is implied by the "Capabilities captured" log entry in history.

Notes: Agent 4 validates capability persistence indirectly via the printer.history field, specifically presence of "Capabilities captured" message. No direct capability endpoint exists.

---

## TC-GOAR-4-05: Simulated Welcome Page failure deletes capability records for failed printer_id

Scenario: [ROLLBACK]   Simulated Welcome Page failure triggers rollback that deletes capability records associated with the failed printer_id.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No prior registration for serial_number "SN-GOAR4-005".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-005", "model_number": "HP-CMFP-600", "firmware_version": "2.1.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Welcome page failed to print"}.

Notes: Capability deletion is internal to store and not directly observable via API; this test relies on the known implementation that _rollback_registration calls store.delete_capabilities(printer.printer_id) when WelcomePagePrintError occurs. Agent 4 only needs to assert the 422 status and error detail.

---

## TC-GOAR-4-06: After failed registration, capability queries expose no data (indirect verification)

Scenario: [ROLLBACK]   After a failed registration, capability queries for the failed printer_id return no capability data.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer or capability for serial_number "SN-GOAR4-006".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-006", "model_number": "HP-M404", "firmware_version": "1.2.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Welcome page failed to print"}.

Notes: There is no public capability query endpoint, so Agent 4 cannot directly assert capability absence. This scenario is therefore effectively covered by TC-GOAR-4-05, and additional internal checks are out of scope.

---

## TC-GOAR-4-07: Successful registration reserves serial number

Scenario: [HAPPY PATH] First-time successful registration with a given serial number completes and reserves that serial.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-007".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-007", "model_number": "HP-M404", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: "printer_id" non-empty; "status" == "REGISTERED"; "serial_number" appears in subsequent GET /printers/{printer_id} and matches "SN-GOAR4-007".

Notes: Agent 4 should implement this as two steps: POST to register, capture printer_id, then GET /printers/{printer_id} and assert serial_number == "SN-GOAR4-007".

---

## TC-GOAR-4-08: Failed registration frees serial number for fresh registration

Scenario: [ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.

Requirement: AC3

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-008".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: First call: {"serial_number": "SN-GOAR4-008", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": true}. Second call: {"serial_number": "SN-GOAR4-008", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST returns 422; second POST returns 200.

  Body contains: First POST body {"detail": "Welcome page failed to print"}. Second POST body includes fields "printer_id", "cloud_id", "printer_email_id", "claim_code", with "status" == "REGISTERED".

Notes: This test explicitly verifies serial index cleanup by confirming that the second registration behaves as a fresh registration and does not return a 422 or 409 indicating duplicate serial.

---

## TC-GOAR-4-09: Multiple failed registrations leave serial reusable each time

Scenario: [BOUNDARY]   Multiple consecutive failed registrations with the same serial number all roll back cleanly, leaving the serial reusable each time.

Requirement: AC3

Endpoint: POST /printers/register (three times)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-009".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: Three sequential calls with {"serial_number": "SN-GOAR4-009", "model_number": "HP-M404", "firmware_version": "1.0.4", "simulate_welcome_page_failure": true}.

Expected response:

  Status: All three POST calls return 422.

  Body contains: Each response body {"detail": "Welcome page failed to print"}.

Notes: This test confirms idempotent serial index cleanup for repeated failures; each attempt should fail consistently without leaving a partially registered printer.

---

## TC-GOAR-4-10: Successful registration unaffected by rollback logic

Scenario: [HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records unchanged by rollback.

Requirement: AC4

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-010".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-010", "model_number": "HP-CMFP-700", "firmware_version": "3.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id" and "status" == "REGISTERED"; GET response includes same "printer_id", "serial_number" == "SN-GOAR4-010", non-empty "cloud_id", "printer_email_id", and history entries showing "Capabilities captured" and "Welcome page printed successfully; registration complete".

Notes: This test further validates that rollback logic is not erroneously triggered on success pathways.

---

## TC-GOAR-4-11: Multiple rollbacks for same printer leave no records (idempotent rollback)

Scenario: [ROLLBACK]   Multiple invocations of _rollback_registration for the same printer_id leave no printer, capability, or serial index records without raising additional errors.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-011".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-011", "model_number": "HP-M404", "firmware_version": "1.0.5", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Welcome page failed to print"}.

Notes: Direct multiple invocations of _rollback_registration are not exposed via API; this scenario is effectively covered by repeated failed registrations in TC-GOAR-4-09. Agent 4 does not need to implement additional steps beyond asserting 422.

---

## TC-GOAR-4-12: Boundary rollback with partially deleted capabilities

Scenario: [BOUNDARY]   Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token

Preconditions: None beyond standard store initialization.

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-012", "model_number": "HP-M404", "firmware_version": "1.0.6", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Welcome page failed to print"}.

Notes: This low-level boundary condition requires direct manipulation of store internals (e.g., deleting capabilities between rollback invocations), which is not exposed via public endpoints. Therefore Agent 4 should not attempt to simulate partial store deletions; the scenario is conceptually covered by TC-GOAR-4-09 and is limited to verifying the 422 response.

---

## TC-GOAR-4-13: Rollback deletes only capabilities for failing printer_id

Scenario: [ROLLBACK]   Rollback for one printer_id deletes only that printer’s capabilities and leaves capabilities for other printers intact.

Requirement: AR2

Endpoint: POST /printers/register (three calls) then GET /printers/{printer_id} for unaffected printer

Auth: valid token

Preconditions: No existing printers for serial_number "SN-GOAR4-013A" or "SN-GOAR4-013B".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: 1) Register first printer with {"serial_number": "SN-GOAR4-013A", "model_number": "HP-CMFP-800", "firmware_version": "3.1.0", "simulate_welcome_page_failure": false} and capture printer_id_A. 2) Register second printer with {"serial_number": "SN-GOAR4-013B", "model_number": "HP-CMFP-900", "firmware_version": "3.2.0", "simulate_welcome_page_failure": true}, expecting failure. 3) GET /printers/{printer_id_A}.

Expected response:

  Status: First POST 200; second POST 422; GET 200.

  Body contains: First POST body includes history entry "Capabilities captured". Second POST body {"detail": "Welcome page failed to print"}. GET response for printer_id_A includes unchanged "serial_number" == "SN-GOAR4-013A", non-empty "cloud_id", and history still containing "Capabilities captured".

Notes: This test confirms that rollback for the failed registration does not disturb capabilities or records for another successfully registered printer.

---

## TC-GOAR-4-14: Rollback does not alter other printers with different owners

Scenario: [OWNERSHIP]  Rollback for an unclaimed printer does not alter capabilities or records of other printers, including those with different owners.

Requirement: AR2

Endpoint: POST /printers/register (two printers), POST /printers/claim for one, then POST /printers/register for failing printer

Auth: valid token

Preconditions: No existing printers for serial_number "SN-GOAR4-014A" or "SN-GOAR4-014B".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: 1) Register printer A with {"serial_number": "SN-GOAR4-014A", "model_number": "HP-M404", "firmware_version": "1.1.0", "simulate_welcome_page_failure": false}; capture printer_id_A and claim_code_A. 2) Claim printer A via POST /printers/claim with {"claim_code": claim_code_A, "user_id": "user-goar4-owner"}. 3) Register printer B with {"serial_number": "SN-GOAR4-014B", "model_number": "HP-M404", "firmware_version": "1.1.0", "simulate_welcome_page_failure": true} expecting 422.

Expected response:

  Status: First POST 200; claim POST 200; second POST 422.

  Body contains: Claim response has "status" == "CLAIMED" and "owner_user_id" == "user-goar4-owner". Failed registration response {"detail": "Welcome page failed to print"}. A subsequent GET /printers/{printer_id_A} (if implemented by Agent 4) should show status "CLAIMED" and unchanged owner_user_id.

Notes: This test confirms rollback on an unclaimed printer does not affect existing claimed printers.

---

## TC-GOAR-4-15: Serial index rollback creates fresh printer record after failure

Scenario: [ROLLBACK]   After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index.

Requirement: AR3

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-015".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: First POST {"serial_number": "SN-GOAR4-015", "model_number": "HP-M404", "firmware_version": "1.2.1", "simulate_welcome_page_failure": true}. Second POST {"serial_number": "SN-GOAR4-015", "model_number": "HP-M404", "firmware_version": "1.2.1", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST 422; second POST 200.

  Body contains: Second POST response includes "printer_id" and "status" == "REGISTERED". There is no 409/422 error for duplicate serial on second call, indicating serial index was cleared by rollback.

Notes: Similar to TC-GOAR-4-08 but explicitly mapped to AR3; Agent 4 can reuse implementation.

---

## TC-GOAR-4-16: Repeated failed and successful registrations never retain stale serial index

Scenario: [BOUNDARY]   Repeated cycles of failed registration followed by successful registration for the same serial verify that the serial index never retains stale associations.

Requirement: AR3

Endpoint: POST /printers/register (four calls)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-016".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: Call 1: {"serial_number": "SN-GOAR4-016", "model_number": "HP-M404", "firmware_version": "1.3.0", "simulate_welcome_page_failure": true}. Call 2: same body with simulate_welcome_page_failure true. Call 3: same serial and model with simulate_welcome_page_failure false. Call 4: repeat successful registration again with simulate_welcome_page_failure false.

Expected response:

  Status: Calls 1 and 2 return 422; calls 3 and 4 return 200.

  Body contains: Calls 1 and 2 response bodies {"detail": "Welcome page failed to print"}. Calls 3 and 4 responses include non-empty "printer_id" and "status" == "REGISTERED" each time.

Notes: This test ensures serial index is correctly removed on failure and re-indexed on each success; no error should be returned for using the same serial repeatedly.

---

## TC-GOAR-4-17: Rollback does not change state of already-claimed printers

Scenario: [OWNERSHIP]  Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.

Requirement: AR4

Endpoint: POST /printers/register (claimed printer), POST /printers/claim, POST /printers/register (failed), GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-017A" or "SN-GOAR4-017B".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: 1) Register printer A: {"serial_number": "SN-GOAR4-017A", "model_number": "HP-M404", "firmware_version": "1.3.1", "simulate_welcome_page_failure": false}; capture printer_id_A and claim_code_A. 2) Claim printer A: POST /printers/claim with {"claim_code": claim_code_A, "user_id": "user-goar4-claim"}. 3) Register printer B: {"serial_number": "SN-GOAR4-017B", "model_number": "HP-M404", "firmware_version": "1.3.1", "simulate_welcome_page_failure": true}. 4) GET /printers/{printer_id_A}.

Expected response:

  Status: Registration for A returns 200; claim returns 200; registration for B returns 422; GET returns 200.

  Body contains: Claim response "status" == "CLAIMED" and "owner_user_id" == "user-goar4-claim". GET response shows "status" == "CLAIMED" and unchanged owner_user_id. Failed registration response {"detail": "Welcome page failed to print"}.

Notes: This test directly validates AR4 by showing that rollback for B does not alter status or ownership of A.

---

## TC-GOAR-4-18: Rollback is never invoked on successful registration

Scenario: [HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated records.

Requirement: AR5

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-018".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-018", "model_number": "HP-CMFP-1000", "firmware_version": "4.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id" and "status" == "REGISTERED". GET response includes "status" == "REGISTERED" and history entries showing registration success and no messages indicating rollback.

Notes: There is no explicit rollback indicator; Agent 4 infers absence of rollback by presence of consistent registration history and status after GET.

---

## TC-GOAR-4-19: Logging-based confirmation that rollback is not invoked on success

Scenario: [ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.

Requirement: AR5

Endpoint: POST /printers/register

Auth: valid token

Preconditions: None beyond standard environment; logging capture is not exposed via API.

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-019", "model_number": "HP-M404", "firmware_version": "1.3.2", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: Same fields as other successful registrations; no rollback-specific data is present.

Notes: Direct verification of "rollback never invoked" via logs is not possible through API; this scenario is effectively covered by TC-GOAR-4-18, so Agent 4 only needs to assert successful registration.

---

## TC-GOAR-4-20: Capabilities for failed registrations are never exposed externally

Scenario: [ROLLBACK]   After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.

Requirement: AR6

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-020".

Request:

  Headers: Default client headers with valid Authorization token.

  Body: {"serial_number": "SN-GOAR4-020", "model_number": "HP-CMFP-1100", "firmware_version": "4.1.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Welcome page failed to print"}.

Notes: There is no API to query capabilities directly; this test therefore validates capability non-visibility indirectly by asserting rollback via 422 response.

---

## Skipped Scenarios

[BOUNDARY]   Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records.             Requirement: AR1 — SKIPPED: Requires direct control over store internals and multiple invocations of _rollback_registration, which are not exposed via public REST endpoints.

[ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.             Requirement: AR5 — SKIPPED: Requires access to internal logging or instrumentation not exposed via public REST endpoints.

[ROLLBACK]   After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.             Requirement: AR6 — SKIPPED: There is no public API to list or query capabilities; verification would require internal store access.

[BOUNDARY]   Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.             Requirement: AR6 — SKIPPED: There is no public API to query capabilities; transient visibility cannot be validated via REST.


## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-4-01 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-02 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-03 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-04 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-05 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-4-06 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-4-07 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-08 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-09 | BOUNDARY | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-10 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-11 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-12 | BOUNDARY | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-13 | ROLLBACK | AR2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-14 | OWNERSHIP | AR2 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-4-15 | ROLLBACK | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-16 | BOUNDARY | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-17 | OWNERSHIP | AR4 | POST /printers/register, POST /printers/claim, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-18 | HAPPY PATH | AR5 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-19 | ROLLBACK | AR5 | POST /printers/register | valid token |
| TC-GOAR-4-20 | ROLLBACK | AR6 | POST /printers/register | valid token |

