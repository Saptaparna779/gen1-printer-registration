# Test Cases — GOAR-5

## TC-GOAR-5-01: Re-register claimed printer preserves owner_user_id (happy path)

Scenario: [HAPPY PATH] Re-register an already-claimed printer and confirm owner_user_id remains unchanged after re-registration.
Requirement: AC1
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed successfully with serial_number = "SN-G5-001". Capture printer_id_1, owner_user_id_1, and status_1 from the claim response, with status_1 == "CLAIMED" and owner_user_id_1 == "user-goar5-a".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-001", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_1; status == "CLAIMED"; owner_user_id is not present in this response (ownership verified separately via GET). cloud_id matches pattern "CID-[A-F0-9]{12}" and differs from the prior cloud_id captured during original registration; printer_email_id matches pattern "[a-z0-9]{10}@print.hpeprint.com"; claim_code field is present but unchanged (same code value as before claim, since no new claim code is issued for CLAIMED printers); history includes entries for both the initial registration and this re-registration (exact content not asserted). Ownership preservation will be verified via a subsequent GET.

Notes: Agent 4 should implement this test by first calling POST /printers/register to create the printer, then POST /printers/claim to claim it (user_id = "user-goar5-a"), capturing printer_id_1, cloud_id_initial, and owner_user_id_1. Then perform the re-registration POST above, capturing cloud_id_rereg. Finally, call GET /printers/{printer_id_1} and assert owner_user_id == owner_user_id_1 and status == "CLAIMED" while cloud_id == cloud_id_rereg. No rollback or store reset is required.

---

## TC-GOAR-5-02: Re-register claimed printer preserves all ownership fields

Scenario: [OWNERSHIP] Re-register a claimed printer that has an existing owner_user_id and confirm no ownership fields are cleared or reassigned.
Requirement: AC1
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-002" using user_id = "user-goar5-b". Capture printer_id_2, owner_user_id_before, and status_before from GET /printers/{printer_id_2}, confirming status_before == "CLAIMED" and owner_user_id_before == "user-goar5-b".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-002", "model_number": "HP-LJ-4200", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_2; status == "CLAIMED"; cloud_id is a new value matching "CID-[A-F0-9]{12}"; printer_email_id matches "[a-z0-9]{10}@print.hpeprint.com"; claim_code is unchanged compared to the value observed before the claim (no new code issued for CLAIMED printers). Ownership will be confirmed via follow-up GET.

Notes: After the re-registration POST, call GET /printers/{printer_id_2} and assert owner_user_id == "user-goar5-b" (unchanged), status == "CLAIMED", and serial_number == "SN-G5-002". This test focuses on verifying that no ownership-related fields (owner_user_id, status) are cleared or reassigned. No rollback required.

---

## TC-GOAR-5-03: Failed re-registration preserves owner_user_id (rollback)

Scenario: [ROLLBACK] Trigger a controlled failure during re-registration of a claimed printer and confirm owner_user_id remains intact after the failure.
Requirement: AC1
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-003" using user_id = "user-goar5-c". Capture printer_id_3 and owner_user_id_3 via GET /printers/{printer_id_3}, confirming status == "CLAIMED" and owner_user_id_3 == "user-goar5-c".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-003", "model_number": "HP-LJ-4200", "firmware_version": "1.0.3", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 on POST; 200 on follow-up GET
  Body contains: POST response body detail == "Welcome page failed to print for printer_id=" followed by printer_id_3. Follow-up GET /printers/{printer_id_3} response has owner_user_id == "user-goar5-c", status == "CLAIMED", serial_number == "SN-G5-003", and a cloud_id equal to the value that was present before the failed re-registration attempt (no new cloud_id persisted on failure).

Notes: This is a rollback test case. Agent 4 must capture pre-state via GET /printers/{printer_id_3} before the failing POST (record owner_user_id_pre, status_pre, cloud_id_pre). After the failing POST (simulate_welcome_page_failure = true), perform GET /printers/{printer_id_3} again and assert owner_user_id_post == owner_user_id_pre, status_post == status_pre == "CLAIMED", serial_number_post == "SN-G5-003", and cloud_id_post == cloud_id_pre. No reset_store is invoked by the test; rollback behaviour is internal to the service.

---

## TC-GOAR-5-04: Re-register claimed printer maintains CLAIMED status (happy path)

Scenario: [HAPPY PATH] Re-register an already-claimed printer and confirm its status remains CLAIMED after re-registration.
Requirement: AC2
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-004" using user_id = "user-goar5-d". Capture printer_id_4 and status_before via GET /printers/{printer_id_4}, asserting status_before == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-004", "model_number": "HP-LJ-4200", "firmware_version": "2.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_4; status == "CLAIMED"; cloud_id matches "CID-[A-F0-9]{12}"; printer_email_id matches "[a-z0-9]{10}@print.hpeprint.com". No change to claim_code (no new claim code issued for CLAIMED printers).

Notes: After the POST, call GET /printers/{printer_id_4} to re-verify that status remains "CLAIMED" and owner_user_id remains "user-goar5-d". This test focuses on the status field specifically.

---

## TC-GOAR-5-05: Re-register claimed printer does not reset status to REGISTERED

Scenario: [OWNERSHIP] Re-register a claimed printer and confirm its CLAIMED status is not changed to REGISTERED or any non-claimed state.
Requirement: AC2
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-005" using user_id = "user-goar5-e". Capture printer_id_5 and status_before via GET /printers/{printer_id_5}, asserting status_before == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-005", "model_number": "HP-LJ-4200", "firmware_version": "2.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_5; status == "CLAIMED" in the POST response; GET /printers/{printer_id_5} after re-registration also returns status == "CLAIMED". At no point does status take the value "REGISTERED" during or after re-registration of this claimed printer.

Notes: Implementation for Agent 4 should explicitly assert that status is never observed as "REGISTERED" for this printer across the re-registration flow (POST response and follow-up GET). No rollback is involved.

---

## TC-GOAR-5-06: Failed re-registration keeps status CLAIMED after rollback

Scenario: [ROLLBACK] Cause re-registration of a claimed printer to fail before completion and confirm its status remains CLAIMED after rollback.
Requirement: AC2
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-006" using user_id = "user-goar5-f". Capture printer_id_6 and status_before via GET /printers/{printer_id_6}, asserting status_before == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-006", "model_number": "HP-LJ-4200", "firmware_version": "2.0.2", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 on POST; 200 on follow-up GET
  Body contains: POST response detail == "Welcome page failed to print for printer_id=" followed by printer_id_6. Follow-up GET /printers/{printer_id_6} body has status == "CLAIMED" and owner_user_id == "user-goar5-f".

Notes: Rollback test. Agent 4 must capture pre-state via GET (status_pre == "CLAIMED") before invoking the failing POST. After the 422, a second GET must show status_post == status_pre == "CLAIMED" and owner_user_id unchanged. No explicit store reset is required; rely on service rollback.

---

## TC-GOAR-5-07: Re-registration of claimed printer appends registration history (SKIPPED)

Scenario: [HAPPY PATH] Re-register a claimed printer and confirm registration history entries are appended rather than replacing existing history.
Requirement: AC3
Endpoint: POST /printers/register, then GET /printers/{printer_id}
Auth: valid token

SKIPPED: Registration history persistence semantics are an open question; tests cannot assert that history is appended versus replaced because printer.registration_history structure and store behavior are not fully specified.

---

## TC-GOAR-5-08: Failed re-registration does not introduce partial history entries (SKIPPED)

Scenario: [ROLLBACK] Trigger a failed re-registration attempt and confirm registration history reflects only successful registrations with no partial or duplicate entries.
Requirement: AC3
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token

SKIPPED: Registration history definition and persistence are unresolved (Open Question 1); cannot reliably distinguish "partial" vs "successful" history entries.

---

## TC-GOAR-5-09: First-time registration for new serial follows standard flow

Scenario: [HAPPY PATH] Perform first-time registration for a new serial number and confirm it follows the standard registration flow and outcomes.
Requirement: AC4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: No printer exists yet with serial_number = "SN-G5-009" (clean serial). Confirm by scanning store via GET /printers/{printer_id} for all known IDs, or rely on a clean test store setup.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-009", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id is a non-empty string UUID; cloud_id matches "CID-[A-F0-9]{12}"; printer_email_id matches "[a-z0-9]{10}@print.hpeprint.com"; claim_code is an 8-character alphanumeric string; claim_code_expires_at is an ISO8601 timestamp at least 14 and at most 16 minutes after the current UTC time; xmpp_node is a non-empty string; status == "REGISTERED"; history includes at least an entry containing "Registration started" and an entry containing "Welcome page printed successfully; registration complete".

Notes: Agent 4 should structure assertions around field formats and status, without assuming any specific printer_id value. No rollback is involved.

---

## TC-GOAR-5-10: First-time registration rejected for invalid serial number

Scenario: [INVALID INPUT] Attempt first-time registration with an invalid or malformed serial number and confirm registration is rejected without creating a printer record.
Requirement: AC4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: Ensure no printer exists with serial_number = "" (empty) or whitespace-only; store should be clean or checked via internal utilities.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "   ", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains: detail == "serial_number, model_number and firmware_version are required".

Notes: After the 422 response, Agent 4 should verify via any available store access helper (if exposed) or by attempting to register again with a valid serial_number that no printer record was created for the whitespace serial value. If no internal store helpers are exposed to tests, skip the secondary verification and rely on the error plus visible behavior.

---

## TC-GOAR-5-11: First-time registration boundary serial behaves like standard registration

Scenario: [BOUNDARY VALUE] Perform first-time registration using a serial number at the boundary of validity (e.g., shortest or longest allowed) and confirm behavior matches standard registration.
Requirement: AC4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: Assume serial_number is free-form non-empty; choose a minimal-length serial "S" and a long but reasonable serial "SN-G5-011-BOUNDARY-1234567890". Ensure neither exists beforehand (clean store).

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-011-BOUNDARY-1234567890", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id non-empty UUID string; cloud_id matches "CID-[A-F0-9]{12}"; printer_email_id matches "[a-z0-9]{10}@print.hpeprint.com"; claim_code is an 8-character alphanumeric string; status == "REGISTERED"; serial_number in the response history and/or GET /printers/{printer_id} matches the provided boundary serial value exactly.

Notes: Agent 4 may implement separate tests for minimal-length and long serials if desired, but from scenario perspective one boundary case is sufficient. No rollback.

---

## TC-GOAR-5-12: Re-register claimed printer does not issue new claim code

Scenario: [HAPPY PATH] Re-register an already-claimed printer and confirm no new claim code is generated or returned.
Requirement: AR1
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-012" using user_id = "user-goar5-g". Capture printer_id_12 and claim_code_before from GET /printers/{printer_id_12} or from the original registration response. Confirm status == "CLAIMED" before re-registration.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-012", "model_number": "HP-LJ-4200", "firmware_version": "1.1.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_12; status == "CLAIMED"; claim_code in the POST response is identical to claim_code_before (no new claim code); cloud_id is a new value matching "CID-[A-F0-9]{12}"; printer_email_id is a new value matching "[a-z0-9]{10}@print.hpeprint.com".

Notes: After POST, perform GET /printers/{printer_id_12} and assert claim_code in the printer record still equals claim_code_before and status == "CLAIMED". No rollback.

---

## TC-GOAR-5-13: Re-register claimed printer keeps existing claim code unchanged

Scenario: [OWNERSHIP] Re-register a claimed printer and confirm the previously issued claim code remains unchanged and no additional claim code is issued.
Requirement: AR1
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-013" using user_id = "user-goar5-h". Capture printer_id_13 and claim_code_before from GET /printers/{printer_id_13}.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-013", "model_number": "HP-LJ-4200", "firmware_version": "1.1.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_13; status == "CLAIMED"; claim_code == claim_code_before; no evidence of a second claim code (only single claim_code field present). cloud_id and printer_email_id are new values.

Notes: Follow up with GET /printers/{printer_id_13} to confirm the printer record still has exactly one claim_code field, equal to claim_code_before, and that owner_user_id remains "user-goar5-h".

---

## TC-GOAR-5-14: Failed re-registration leaves claim code state unchanged (rollback)

Scenario: [ROLLBACK] Force a failure during re-registration of a claimed printer and confirm claim code state is unchanged after rollback.
Requirement: AR1
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-014" using user_id = "user-goar5-i". Capture printer_id_14 and claim_code_before via GET /printers/{printer_id_14}. Confirm status == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-014", "model_number": "HP-LJ-4200", "firmware_version": "1.1.2", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 on POST; 200 on follow-up GET
  Body contains: POST response detail == "Welcome page failed to print for printer_id=" followed by printer_id_14. Follow-up GET /printers/{printer_id_14} returns claim_code == claim_code_before, status == "CLAIMED", and owner_user_id == "user-goar5-i".

Notes: Rollback test. Agent 4 must verify that claim_code does not change across the failed re-registration. Pre-state and post-state must be compared via GET.

---

## TC-GOAR-5-15: Re-register claimed printer generates new Cloud ID and Printer Email ID

Scenario: [HAPPY PATH] Re-register an already-claimed printer and confirm a new Cloud ID and Printer Email ID are generated while ownership details remain unchanged.
Requirement: AR2
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-015" using user_id = "user-goar5-j". Capture printer_id_15, cloud_id_before, printer_email_id_before, owner_user_id_before, and status_before via GET /printers/{printer_id_15}, confirming status_before == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-015", "model_number": "HP-LJ-4200", "firmware_version": "2.1.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_15; cloud_id != cloud_id_before and matches "CID-[A-F0-9]{12}"; printer_email_id != printer_email_id_before and matches "[a-z0-9]{10}@print.hpeprint.com"; status == "CLAIMED".

Notes: After POST, perform GET /printers/{printer_id_15} and assert that cloud_id and printer_email_id have been updated to the new values while owner_user_id and status remain unchanged.

---

## TC-GOAR-5-16: Multiple re-registrations of claimed printer generate distinct IDs

Scenario: [BOUNDARY VALUE] Re-register a claimed printer multiple times in succession and confirm each registration generates distinct Cloud ID and Printer Email ID values.
Requirement: AR2
Endpoint: POST /printers/register (called three times)
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-016" using user_id = "user-goar5-k". Capture printer_id_16.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: Call 1: {"serial_number": "SN-G5-016", "model_number": "HP-LJ-4200", "firmware_version": "2.1.1", "simulate_welcome_page_failure": false}
        Call 2: same body as Call 1
        Call 3: same body as Call 1

Expected response:
  Status: 200 for all three calls
  Body contains: Capture cloud_id_1, printer_email_id_1 from call 1; cloud_id_2, printer_email_id_2 from call 2; cloud_id_3, printer_email_id_3 from call 3. Assert all cloud_id values match "CID-[A-F0-9]{12}" and cloud_id_1, cloud_id_2, cloud_id_3 are pairwise distinct. Assert all printer_email_id values match "[a-z0-9]{10}@print.hpeprint.com" and printer_email_id_1, printer_email_id_2, printer_email_id_3 are pairwise distinct.

Notes: After the three POST calls, a GET /printers/{printer_id_16} may be used to confirm the latest cloud_id and printer_email_id match the values from call 3 and that status remains "CLAIMED". No rollback.

---

## TC-GOAR-5-17: Failed re-registration does not persist new Cloud ID or Printer Email ID (rollback)

Scenario: [ROLLBACK] Trigger a failed re-registration of a claimed printer and confirm no new Cloud ID or Printer Email ID is persisted after rollback.
Requirement: AR2
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-017" using user_id = "user-goar5-l". Capture printer_id_17, cloud_id_before, and printer_email_id_before via GET /printers/{printer_id_17}, confirming status == "CLAIMED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-017", "model_number": "HP-LJ-4200", "firmware_version": "2.1.2", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 on POST; 200 on follow-up GET
  Body contains: POST response detail == "Welcome page failed to print for printer_id=" followed by printer_id_17. Follow-up GET /printers/{printer_id_17} returns cloud_id == cloud_id_before and printer_email_id == printer_email_id_before (no changes persisted), status == "CLAIMED", and owner_user_id unchanged.

Notes: Rollback test focusing specifically on cloud_id and printer_email_id. Agent 4 must capture pre-state and compare to post-state via GET.

---

## TC-GOAR-5-18: Rollback on failed re-registration preserves claimed state

Scenario: [ROLLBACK] Cause re-registration of a claimed printer to fail before the Welcome Page prints and confirm owner_user_id, status, and prior registration-related data remain unchanged.
Requirement: AR3
Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-018" using user_id = "user-goar5-m". Capture printer_id_18, owner_user_id_before, status_before, cloud_id_before, and printer_email_id_before via GET /printers/{printer_id_18}.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-018", "model_number": "HP-LJ-4200", "firmware_version": "2.2.0", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 on POST; 200 on follow-up GET
  Body contains: POST response detail == "Welcome page failed to print for printer_id=" followed by printer_id_18. Follow-up GET /printers/{printer_id_18} returns owner_user_id == owner_user_id_before; status == status_before == "CLAIMED"; cloud_id == cloud_id_before; printer_email_id == printer_email_id_before; serial_number == "SN-G5-018".

Notes: Rollback test. Agent 4 must compare pre-state and post-state across all key ownership and identity fields to confirm no partial updates are persisted.

---

## TC-GOAR-5-19: Repeated failed re-registrations preserve claimed state

Scenario: [ROLLBACK] Simulate repeated failures during re-registration of a claimed printer and confirm each failure leaves the printer in the same claimed state with no partial updates.
Requirement: AR3
Endpoint: POST /printers/register (failure, repeated), then GET /printers/{printer_id}
Auth: valid token
Preconditions: A printer has been registered and claimed with serial_number = "SN-G5-019" using user_id = "user-goar5-n". Capture printer_id_19 and pre-state fields via GET /printers/{printer_id_19}.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: Two consecutive failing calls: Call 1 body {"serial_number": "SN-G5-019", "model_number": "HP-LJ-4200", "firmware_version": "2.2.1", "simulate_welcome_page_failure": true}; Call 2 body identical to Call 1.

Expected response:
  Status: 422 for both POST calls; 200 on final GET
  Body contains: Each POST returns detail == "Welcome page failed to print for printer_id=" followed by printer_id_19. Final GET /printers/{printer_id_19} returns owner_user_id, status, cloud_id, printer_email_id, and serial_number all equal to their pre-state values, confirming no cumulative partial updates.

Notes: Rollback test. Agent 4 should capture pre-state, perform two failing POST calls, and then GET. Assertions must confirm that repeated failures do not alter the claimed state or identity fields.

---

## TC-GOAR-5-20: Rollback does not affect printer visibility to owner (SKIPPED)

Scenario: [OWNERSHIP] Verify that rollback after a failed re-registration does not affect the printer’s visibility or ownership in client applications.
Requirement: AR3
Endpoint: External client application or integration
Auth: valid token

SKIPPED: Client application visibility and external integrations are outside the scope of this repo; there is no testable API surface or documented behavior for HP Smart visibility.

---

## TC-GOAR-5-21: Re-register non-claimed printer behaves as normal registration

Scenario: [HAPPY PATH] Re-register a non-claimed printer and confirm it behaves as a normal registration, generating new Cloud ID, Printer Email ID, and Claim Code, and ending with status REGISTERED.
Requirement: AR4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered but not claimed with serial_number = "SN-G5-021". Capture printer_id_21, cloud_id_initial, printer_email_id_initial, claim_code_initial, and status_initial via initial registration response, asserting status_initial == "REGISTERED".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-021", "model_number": "HP-LJ-4200", "firmware_version": "3.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200
  Body contains: printer_id == printer_id_21; cloud_id != cloud_id_initial and matches "CID-[A-F0-9]{12}"; printer_email_id != printer_email_id_initial and matches "[a-z0-9]{10}@print.hpeprint.com"; claim_code != claim_code_initial and is an 8-character alphanumeric string; status == "REGISTERED".

Notes: After POST, GET /printers/{printer_id_21} should confirm status == "REGISTERED" and that all three identity fields have been updated to the new values. No rollback.

---

## TC-GOAR-5-22: Invalid re-registration for non-claimed printer fails without changing record

Scenario: [INVALID INPUT] Attempt re-registration of a non-claimed printer with invalid required fields and confirm registration fails without changing existing records.
Requirement: AR4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered but not claimed with serial_number = "SN-G5-022" and status == "REGISTERED". Capture printer_id_22, cloud_id_before, printer_email_id_before, claim_code_before, and firmware_version_before via GET /printers/{printer_id_22}.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-022", "model_number": "   ", "firmware_version": "", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains: detail == "serial_number, model_number and firmware_version are required".

Notes: After the 422 response, GET /printers/{printer_id_22} must show that cloud_id, printer_email_id, claim_code, firmware_version, and status all remain equal to their pre-state values, confirming no partial update on invalid input.

---

## TC-GOAR-5-23: Repeated re-registrations of non-claimed printer maintain REGISTERED status

Scenario: [BOUNDARY VALUE] Perform repeated re-registrations of a non-claimed printer and confirm each registration produces new identifiers while maintaining status REGISTERED.
Requirement: AR4
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered but not claimed with serial_number = "SN-G5-023" and status == "REGISTERED". Capture printer_id_23.

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: Call 1: {"serial_number": "SN-G5-023", "model_number": "HP-LJ-4200", "firmware_version": "3.0.1", "simulate_welcome_page_failure": false}
        Call 2: same body as Call 1
        Call 3: same body as Call 1

Expected response:
  Status: 200 on all three calls
  Body contains: cloud_id_1, cloud_id_2, cloud_id_3 all match "CID-[A-F0-9]{12}" and are pairwise distinct; printer_email_id_1, printer_email_id_2, printer_email_id_3 all match "[a-z0-9]{10}@print.hpeprint.com" and are pairwise distinct; claim_code_1, claim_code_2, claim_code_3 are 8-character alphanumeric strings and are pairwise distinct; status == "REGISTERED" in every POST response.

Notes: After the sequence, GET /printers/{printer_id_23} may be used to confirm that status is still "REGISTERED" and that the latest identity values correspond to call 3.

---

## TC-GOAR-5-24: Audit logging for re-registration of claimed printer (SKIPPED)

Scenario: [HAPPY PATH] Re-register a claimed printer and confirm audit logs include printer_id, serial_number, previous status, new status, and a flag indicating it was already claimed.
Requirement: AR5
Endpoint: Internal logging/telemetry sink
Auth: valid token

SKIPPED: Logging and telemetry sinks are not exposed via the API; there is no supported way to assert specific log fields from tests.

---

## TC-GOAR-5-25: Audit logging on invalid re-registration input (SKIPPED)

Scenario: [INVALID INPUT] Perform a re-registration attempt for a claimed printer with invalid input and confirm audit logs capture the failure details without logging misleading ownership changes.
Requirement: AR5
Endpoint: Internal logging/telemetry sink
Auth: valid token

SKIPPED: No API or test harness support exists to inspect structured logs for this service; behavior is untestable from the repository.

---

## TC-GOAR-5-26: Audit logging of rollback during re-registration (SKIPPED)

Scenario: [ROLLBACK] Trigger a rollback during re-registration of a claimed printer and confirm audit logs clearly record the rollback event and that claimed ownership was preserved.
Requirement: AR5
Endpoint: Internal logging/telemetry sink
Auth: valid token

SKIPPED: Logging internals and audit event schema are not exposed; cannot verify log content.

---

## TC-GOAR-5-27: Model family mismatch on re-registration is rejected for claimed printer

Scenario: [BOUNDARY VALUE] Perform re-registration of a claimed printer where the incoming model_number belongs to a different model family and confirm registration is rejected.
Requirement: AR4 (edge / boundary)
Endpoint: POST /printers/register
Auth: valid token
Preconditions: A printer has been registered but not claimed initially with serial_number = "SN-G5-027" and model_number = "HP-LJ-4200"; then claimed using user_id = "user-goar5-o" so that status == "CLAIMED". Capture printer_id_27 and model_number_existing == "HP-LJ-4200".

Request:
  Headers: Authorization header attached by conftest.py client fixture by default — no extra code needed.
  Body: {"serial_number": "SN-G5-027", "model_number": "HP-CM-750", "firmware_version": "3.1.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 422
  Body contains: detail == "Re-registration rejected: model family mismatch (existing='HP-LJ-4200', incoming='HP-CM-750'). This looks like a different physical device reusing the same serial number.".

Notes: After the 422 response, GET /printers/{printer_id_27} should confirm that model_number remains "HP-LJ-4200", status remains "CLAIMED", and owner_user_id remains "user-goar5-o".

---

## Skipped Scenarios

[HAPPY PATH] Re-register a claimed printer and confirm registration history entries are appended rather than replacing existing history.              Requirement: AC3 — SKIPPED: Registration history persistence is unresolved and not fully testable from app/registration.py and store APIs.
[ROLLBACK] Trigger a failed re-registration attempt and confirm registration history reflects only successful registrations with no partial or duplicate entries.              Requirement: AC3 — SKIPPED: Cannot assert detailed history filtering or deduplication due to undefined registration_history semantics.
[OWNERSHIP] Verify that rollback after a failed re-registration does not affect the printer’s visibility or ownership in client applications.              Requirement: AR3 — SKIPPED: Client application visibility behavior is not exposed via this API; no HP Smart integration is testable.
[HAPPY PATH] Re-register a claimed printer and confirm audit logs include printer_id, serial_number, previous status, new status, and a flag indicating it was already claimed.              Requirement: AR5 — SKIPPED: Logging internals are not exposed; no ability to assert audit log contents.
[INVALID INPUT] Perform a re-registration attempt for a claimed printer with invalid input and confirm audit logs capture the failure details without logging misleading ownership changes.              Requirement: AR5 — SKIPPED: No access to logging/telemetry sinks from tests.
[ROLLBACK] Trigger a rollback during re-registration of a claimed printer and confirm audit logs clearly record the rollback event and that claimed ownership was preserved.              Requirement: AR5 — SKIPPED: Audit event schema and sink are out of scope for this repo.

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-5-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-5-02 | OWNERSHIP | AC1 | POST /printers/register | valid token |
| TC-GOAR-5-03 | ROLLBACK | AC1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-04 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-5-05 | OWNERSHIP | AC2 | POST /printers/register | valid token |
| TC-GOAR-5-06 | ROLLBACK | AC2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-07 | HAPPY PATH (SKIPPED) | AC3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-08 | ROLLBACK (SKIPPED) | AC3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-09 | HAPPY PATH | AC4 | POST /printers/register | valid token |
| TC-GOAR-5-10 | INVALID INPUT | AC4 | POST /printers/register | valid token |
| TC-GOAR-5-11 | BOUNDARY VALUE | AC4 | POST /printers/register | valid token |
| TC-GOAR-5-12 | HAPPY PATH | AR1 | POST /printers/register | valid token |
| TC-GOAR-5-13 | OWNERSHIP | AR1 | POST /printers/register | valid token |
| TC-GOAR-5-14 | ROLLBACK | AR1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-15 | HAPPY PATH | AR2 | POST /printers/register | valid token |
| TC-GOAR-5-16 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-5-17 | ROLLBACK | AR2 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-18 | ROLLBACK | AR3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-19 | ROLLBACK | AR3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-5-20 | OWNERSHIP (SKIPPED) | AR3 | External client integration | valid token |
| TC-GOAR-5-21 | HAPPY PATH | AR4 | POST /printers/register | valid token |
| TC-GOAR-5-22 | INVALID INPUT | AR4 | POST /printers/register | valid token |
| TC-GOAR-5-23 | BOUNDARY VALUE | AR4 | POST /printers/register | valid token |
| TC-GOAR-5-24 | HAPPY PATH (SKIPPED) | AR5 | Internal logging | valid token |
| TC-GOAR-5-25 | INVALID INPUT (SKIPPED) | AR5 | Internal logging | valid token |
| TC-GOAR-5-26 | ROLLBACK (SKIPPED) | AR5 | Internal logging | valid token |
| TC-GOAR-5-27 | BOUNDARY VALUE | AR4 | POST /printers/register | valid token |
