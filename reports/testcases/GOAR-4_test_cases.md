# Test Cases — GOAR-4

## TC-GOAR-4-01: Successful registration persists printer, capabilities and serial index

Scenario: [HAPPY PATH] Welcome Page prints successfully and printer record is persisted without invoking rollback.

Requirement: AC4

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-001" (store has no entry for this serial and no printer indexed by it).

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: {"serial_number": "SN-GOAR4-001", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:

  Status: 200

  Body contains: "printer_id" as a non-empty string; "cloud_id" starting with "CID-" and 16 characters total; "printer_email_id" ending with "@print.hpeprint.com"; "claim_code" as an 8-character uppercase alphanumeric string; "status" == "REGISTERED"; "history" list including an entry containing "Registration started" and an entry containing "Welcome page printed successfully; registration complete".

Notes: Agent 4 should implement this as a single POST call and assert the response fields. No rollback-specific verification is required in this test.

---

## TC-GOAR-4-02: Rollback removes printer record on Welcome Page failure (indirect)

Scenario: [ROLLBACK]   Simulated Welcome Page failure triggers rollback that removes the printer record created during registration.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-002".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: {"serial_number": "SN-GOAR4-002", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: "detail" == "Welcome page failed to print for printer_id=<printer_id>" where <printer_id> is the UUID generated for this attempt.

Notes: Agent 4 should assert status_code == 422 and that the detail string starts with "Welcome page failed to print for printer_id=". The rollback deleting the printer record is internal but is guaranteed by the implementation when this error is raised.

---

## TC-GOAR-4-03: Failed registration leaves no persistent printer record (serial reusable)

Scenario: [ROLLBACK]   Failed registration leaves no printer record and allows subsequent inspection to confirm absence of printer data.

Requirement: AC1

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-003".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-003", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-003", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST 422, second POST 200.

  Body contains: First POST detail string equal to "Welcome page failed to print for printer_id=<printer_id_1>". Second POST returns a new "printer_id" (capture as printer_id_2) with "status" == "REGISTERED". There is no HTTP error indicating duplicate serial on the second call.

Notes: This test uses the second successful registration as evidence that the failed attempt left no persistent printer or serial index record.

---

## TC-GOAR-4-04: Successful registration captures and persists capabilities

Scenario: [HAPPY PATH] Successful registration persists capability records for the printer_id and they remain after completion.

Requirement: AC4

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer or capability record for serial_number "SN-GOAR4-004" and model_number "HP-CMFP-500".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST /printers/register with {"serial_number": "SN-GOAR4-004", "model_number": "HP-CMFP-500", "firmware_version": "2.0.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id} using printer_id from POST response.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes non-empty "printer_id" and "status" == "REGISTERED". GET response has same "printer_id", "serial_number" == "SN-GOAR4-004", and "history" list containing an entry with "Capabilities captured" and an entry with "Welcome page printed successfully; registration complete".

Notes: Capability persistence is verified indirectly through the "Capabilities captured" log entry in the registration history returned by GET.

---

## TC-GOAR-4-05: Rollback deletes capability records on Welcome Page failure (indirect)

Scenario: [ROLLBACK]   Simulated Welcome Page failure triggers rollback that deletes capability records associated with the failed printer_id.

Requirement: AC2

Endpoint: POST /printers/register (twice) then GET /printers/{printer_id}

Auth: valid token

Preconditions: No prior registration for serial_number "SN-GOAR4-005".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-005", "model_number": "HP-CMFP-600", "firmware_version": "2.1.0", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-005", "model_number": "HP-CMFP-600", "firmware_version": "2.1.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id_2} using printer_id from second POST.

Expected response:

  Status: First POST 422; second POST 200; GET 200.

  Body contains: First POST detail == "Welcome page failed to print for printer_id=<printer_id_1>". Second POST returns printer_id_2 with "status" == "REGISTERED". GET response history contains exactly one "Capabilities captured" entry for printer_id_2; there is no way for the failed attempt's capabilities to be visible via this API, which is consistent with store.delete_capabilities in rollback.

Notes: This test ensures that capability capture for the successful registration is clean and that the earlier failed attempt does not result in any extra capability-related history for the successful printer_id.

---

## TC-GOAR-4-06: Failed registration capabilities are not exposed via GET

Scenario: [ROLLBACK]   After a failed registration, capability queries for the failed printer_id return no capability data.

Requirement: AC2

Endpoint: POST /printers/register (twice) then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer or capability for serial_number "SN-GOAR4-006".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-006", "model_number": "HP-M404", "firmware_version": "1.2.0", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-006", "model_number": "HP-M404", "firmware_version": "1.2.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id_2}.

Expected response:

  Status: First POST 422; second POST 200; GET 200.

  Body contains: First POST detail == "Welcome page failed to print for printer_id=<printer_id_1>". GET response history contains a single "Capabilities captured" entry associated with the successful registration; there is no evidence of capabilities from the failed attempt.

Notes: This test indirectly validates that capability records created during the failed attempt were removed and never exposed via GET.

---

## TC-GOAR-4-07: Successful registration reserves serial number and is visible via GET

Scenario: [HAPPY PATH] First-time successful registration with a given serial number completes and reserves that serial.

Requirement: AC4

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-007".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-007", "model_number": "HP-M404", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id}.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes non-empty "printer_id" and "status" == "REGISTERED". GET response includes "serial_number" == "SN-GOAR4-007" and "status" == "REGISTERED".

Notes: This test establishes the baseline behaviour that successful registrations create persistent records retrievable via GET.

---

## TC-GOAR-4-08: Rollback frees serial for fresh registration

Scenario: [ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.

Requirement: AC3

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-008".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-008", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-008", "model_number": "HP-M404", "firmware_version": "1.0.3", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST 422; second POST 200.

  Body contains: First POST detail == "Welcome page failed to print for printer_id=<printer_id_1>". Second POST returns "printer_id" (printer_id_2) and "status" == "REGISTERED". No error about duplicate serial is returned on the second call.

Notes: This test directly exercises AC3 by verifying that a serial involved in a failed registration can be reused successfully.

---

## TC-GOAR-4-09: Multiple failed registrations keep serial reusable

Scenario: [BOUNDARY]   Multiple consecutive failed registrations with the same serial number all roll back cleanly, leaving the serial reusable each time.

Requirement: AC3

Endpoint: POST /printers/register (three times)

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-009".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: Three sequential POST calls each with {"serial_number": "SN-GOAR4-009", "model_number": "HP-M404", "firmware_version": "1.0.4", "simulate_welcome_page_failure": true}.

Expected response:

  Status: All three POST calls return 422.

  Body contains: Each response detail string starts with "Welcome page failed to print for printer_id=" and the printer_id portion differs between calls (three distinct printer_id values).

Notes: This test confirms that each failed attempt is fully rolled back, and that serial index cleanup is idempotent across repeated failures.

---

## TC-GOAR-4-10: Successful registration unaffected by rollback logic

Scenario: [HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records unchanged by rollback.

Requirement: AC4

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer record for serial_number "SN-GOAR4-010".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-010", "model_number": "HP-CMFP-700", "firmware_version": "3.0.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id}.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id" and "status" == "REGISTERED". GET response shows non-empty "cloud_id", "printer_email_id" ending with "@print.hpeprint.com", and history entries including "Capabilities captured" and "Welcome page printed successfully; registration complete"; there are no history entries mentioning rollback.

Notes: This test guards against regressions where rollback might be mistakenly invoked on successful registrations.

---

## TC-GOAR-4-11: Idempotent rollback via repeated failed registrations

Scenario: [ROLLBACK]   Multiple invocations of _rollback_registration for the same printer_id leave no printer, capability, or serial index records without raising additional errors.

Requirement: AR1

Endpoint: POST /printers/register (two failed attempts)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-011".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: Two sequential POST calls, both with {"serial_number": "SN-GOAR4-011", "model_number": "HP-M404", "firmware_version": "1.0.5", "simulate_welcome_page_failure": true}.

Expected response:

  Status: Both POST calls return 422.

  Body contains: Each response detail starts with "Welcome page failed to print for printer_id=" and contains the printer_id for that attempt. No call returns a different error such as 409 for duplicate serial.

Notes: Because rollback is only exposed via failed registrations, repeated failures serve as a proxy for repeated _rollback_registration invocations and demonstrate idempotent cleanup.

---

## TC-GOAR-4-12: Boundary rollback behaviour with repeated failed attempts

Scenario: [BOUNDARY]   Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records.

Requirement: AR1

Endpoint: POST /printers/register (three failed attempts)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-012".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: Three sequential POST calls with {"serial_number": "SN-GOAR4-012", "model_number": "HP-M404", "firmware_version": "1.0.6", "simulate_welcome_page_failure": true}.

Expected response:

  Status: All three POST calls return 422.

  Body contains: Each response detail equals "Welcome page failed to print for printer_id=<printer_id_n>"; no call returns an unexpected error, demonstrating that rollback handles already-deleted records gracefully.

Notes: Direct partial store manipulation is not available via REST; repeated failed registrations serve as a boundary test for rollback robustness.

---

## TC-GOAR-4-13: Rollback deletes only failing printer’s data, leaving other printer intact

Scenario: [ROLLBACK]   Rollback for one printer_id deletes only that printer’s capabilities and leaves capabilities for other printers intact.

Requirement: AR2

Endpoint: POST /printers/register (two printers) then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printers for serial_number "SN-GOAR4-013A" or "SN-GOAR4-013B".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: 1) Register printer A: {"serial_number": "SN-GOAR4-013A", "model_number": "HP-CMFP-800", "firmware_version": "3.1.0", "simulate_welcome_page_failure": false}; capture printer_id_A. 2) Register printer B: {"serial_number": "SN-GOAR4-013B", "model_number": "HP-CMFP-900", "firmware_version": "3.2.0", "simulate_welcome_page_failure": true}; expect failure. 3) GET /printers/{printer_id_A}.

Expected response:

  Status: First POST 200; second POST 422; GET 200.

  Body contains: First POST response includes history entries for printer A including "Capabilities captured" and "Welcome page printed successfully; registration complete". Second POST detail == "Welcome page failed to print for printer_id=<printer_id_B>". GET response for printer_id_A shows unchanged "serial_number" == "SN-GOAR4-013A" and "status" == "REGISTERED".

Notes: This test ensures that rollback for failed printer B does not affect existing data for printer A.

---

## TC-GOAR-4-14: Rollback does not alter other printers with different owners

Scenario: [OWNERSHIP]  Rollback for an unclaimed printer does not alter capabilities or records of other printers, including those with different owners.

Requirement: AR2

Endpoint: POST /printers/register (two printers), POST /printers/claim, then POST /printers/register (failed)

Auth: valid token

Preconditions: No existing printers for serial_number "SN-GOAR4-014A" or "SN-GOAR4-014B".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: 1) Register printer A: {"serial_number": "SN-GOAR4-014A", "model_number": "HP-M404", "firmware_version": "1.1.0", "simulate_welcome_page_failure": false}; capture printer_id_A and claim_code_A. 2) Claim printer A via POST /printers/claim with {"claim_code": claim_code_A, "user_id": "user-goar4-owner"}. 3) Register printer B: {"serial_number": "SN-GOAR4-014B", "model_number": "HP-M404", "firmware_version": "1.1.0", "simulate_welcome_page_failure": true}; expect 422.

Expected response:

  Status: Registration for A 200; claim 200; registration for B 422.

  Body contains: Claim response includes "status" == "CLAIMED" and "owner_user_id" == "user-goar4-owner". Failed registration response detail == "Welcome page failed to print for printer_id=<printer_id_B>". A follow-up GET /printers/{printer_id_A} (optional in automation) should show status "CLAIMED" and unchanged owner_user_id.

Notes: This test confirms that rollback for B does not affect the ownership state of already-claimed printer A.

---

## TC-GOAR-4-15: Serial index rollback creates fresh printer record after failure

Scenario: [ROLLBACK]   After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index.

Requirement: AR3

Endpoint: POST /printers/register (twice)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-015".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-015", "model_number": "HP-M404", "firmware_version": "1.2.1", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-015", "model_number": "HP-M404", "firmware_version": "1.2.1", "simulate_welcome_page_failure": false}.

Expected response:

  Status: First POST 422; second POST 200.

  Body contains: First POST detail == "Welcome page failed to print for printer_id=<printer_id_1>". Second POST returns "printer_id" (printer_id_2) and "status" == "REGISTERED"; no error indicates stale serial index.

Notes: This is explicitly mapped to AR3 and overlaps with AC3 behaviour from TC-GOAR-4-08.

---

## TC-GOAR-4-16: Repeated failed and successful registrations never retain stale serial index

Scenario: [BOUNDARY]   Repeated cycles of failed registration followed by successful registration for the same serial verify that the serial index never retains stale associations.

Requirement: AR3

Endpoint: POST /printers/register (four calls)

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-016".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: Call 1: {"serial_number": "SN-GOAR4-016", "model_number": "HP-M404", "firmware_version": "1.3.0", "simulate_welcome_page_failure": true}. Call 2: same body with simulate_welcome_page_failure true. Call 3: same serial and model with simulate_welcome_page_failure false. Call 4: same serial and model with simulate_welcome_page_failure false.

Expected response:

  Status: Calls 1 and 2 return 422; calls 3 and 4 return 200.

  Body contains: Calls 1 and 2 detail == "Welcome page failed to print for printer_id=<printer_id_1>" and "...<printer_id_2>" respectively. Calls 3 and 4 each return non-empty "printer_id" and "status" == "REGISTERED".

Notes: This test ensures that the serial index is correctly removed on each failure and re-created on each success; there should be no duplicate-serial errors at any point.

---

## TC-GOAR-4-17: Rollback does not change state of already-claimed printers

Scenario: [OWNERSHIP]  Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.

Requirement: AR4

Endpoint: POST /printers/register (claimed printer), POST /printers/claim, POST /printers/register (failed), GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-017A" or "SN-GOAR4-017B".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: 1) Register printer A: {"serial_number": "SN-GOAR4-017A", "model_number": "HP-M404", "firmware_version": "1.3.1", "simulate_welcome_page_failure": false}; capture printer_id_A and claim_code_A. 2) Claim printer A: POST /printers/claim with {"claim_code": claim_code_A, "user_id": "user-goar4-claim"}. 3) Register printer B: {"serial_number": "SN-GOAR4-017B", "model_number": "HP-M404", "firmware_version": "1.3.1", "simulate_welcome_page_failure": true}; 4) GET /printers/{printer_id_A}.

Expected response:

  Status: Registration for A returns 200; claim returns 200; registration for B returns 422; GET returns 200.

  Body contains: Claim response has "status" == "CLAIMED" and "owner_user_id" == "user-goar4-claim". Failed registration response detail == "Welcome page failed to print for printer_id=<printer_id_B>". GET response shows "status" == "CLAIMED" and "owner_user_id" == "user-goar4-claim".

Notes: This test directly validates AR4 by showing that rollback for B does not alter the claimed state of A.

---

## TC-GOAR-4-18: Successful registration never invokes rollback

Scenario: [HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated records.

Requirement: AR5

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-018".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-018", "model_number": "HP-CMFP-1000", "firmware_version": "4.0.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id}.

Expected response:

  Status: POST 200; GET 200.

  Body contains: POST response includes "printer_id" and "status" == "REGISTERED". GET response includes "status" == "REGISTERED" and history entries indicating successful registration without any rollback-related messages (no deletions; printer remains retrievable).

Notes: Absence of rollback is inferred from the printer remaining available via GET and having consistent history.

---

## TC-GOAR-4-19: Logging-based confirmation of successful registration via history

Scenario: [ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.

Requirement: AR5

Endpoint: POST /printers/register then GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-019".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: POST: {"serial_number": "SN-GOAR4-019", "model_number": "HP-M404", "firmware_version": "1.3.2", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id}.

Expected response:

  Status: POST 200; GET 200.

  Body contains: GET response history includes entries such as "Registration started", "Cloud identity created", "Capabilities captured", and "Welcome page printed successfully; registration complete"; there are no entries indicating rollback or deletion.

Notes: This test uses the registration history as an externally observable log to confirm the success path without rollback.

---

## TC-GOAR-4-20: Capabilities for failed registrations are never exposed externally

Scenario: [ROLLBACK]   After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.

Requirement: AR6

Endpoint: POST /printers/register (failed) then POST /printers/register (success) and GET /printers/{printer_id}

Auth: valid token

Preconditions: No existing printer for serial_number "SN-GOAR4-020".

Request:

  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.

  Body: First POST: {"serial_number": "SN-GOAR4-020", "model_number": "HP-CMFP-1100", "firmware_version": "4.1.0", "simulate_welcome_page_failure": true}. Second POST: {"serial_number": "SN-GOAR4-020", "model_number": "HP-CMFP-1100", "firmware_version": "4.1.0", "simulate_welcome_page_failure": false}. Then GET /printers/{printer_id_2}.

Expected response:

  Status: First POST 422; second POST 200; GET 200.

  Body contains: First POST detail == "Welcome page failed to print for printer_id=<printer_id_1>". GET response for printer_id_2 shows only capabilities and history associated with the successful registration (e.g., single "Capabilities captured" entry) and no evidence of capabilities from the failed attempt.

Notes: Since capabilities are only observable indirectly via history, this test confirms that failed registration capabilities are cleaned up and never exposed to clients.

---

## Skipped Scenarios

[BOUNDARY]   Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records.             Requirement: AR1 — SKIPPED: Requires direct control over store internals and manual invocation of _rollback_registration, which are not exposed via public REST endpoints.

[ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.             Requirement: AR5 — SKIPPED: Would require access to internal logging or tracing beyond the registration history exposed via GET /printers/{printer_id}.

[ROLLBACK]   After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.             Requirement: AR6 — SKIPPED: There is no public API to list or query capabilities directly; only indirect verification via history is possible and covered by TC-GOAR-4-20.

[BOUNDARY]   Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.             Requirement: AR6 — SKIPPED: There is no public API to observe transient capability visibility; only final state can be asserted.


## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-4-01 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-4-02 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-03 | ROLLBACK | AC1 | POST /printers/register | valid token |
| TC-GOAR-4-04 | HAPPY PATH | AC4 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-05 | ROLLBACK | AC2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-06 | ROLLBACK | AC2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-07 | HAPPY PATH | AC4 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-08 | ROLLBACK | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-09 | BOUNDARY | AC3 | POST /printers/register | valid token |
| TC-GOAR-4-10 | HAPPY PATH | AC4 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-11 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-12 | BOUNDARY | AR1 | POST /printers/register | valid token |
| TC-GOAR-4-13 | ROLLBACK | AR2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-14 | OWNERSHIP | AR2 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-4-15 | ROLLBACK | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-16 | BOUNDARY | AR3 | POST /printers/register | valid token |
| TC-GOAR-4-17 | OWNERSHIP | AR4 | POST /printers/register, POST /printers/claim, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-18 | HAPPY PATH | AR5 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-19 | ROLLBACK | AR5 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-4-20 | ROLLBACK | AR6 | POST /printers/register, GET /printers/{printer_id} | valid token |
