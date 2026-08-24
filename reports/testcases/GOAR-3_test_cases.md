# Test Cases — GOAR-3

## TC-GOAR-3-01: Initial registration and re-registration generate different Cloud IDs

Scenario: [HAPPY PATH] Initial registration and subsequent re-registration of the same serial number both succeed and the second response returns a Cloud ID different from the first.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1001".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1001", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200
  Body contains: "printer_id" (non-empty string), "cloud_id" matching pattern CID-[A-F0-9]{12}, "printer_email_id" matching pattern [a-z0-9]{10}@print.hpeprint.com, "claim_code" matching pattern [A-Z0-9]{8}, "status" == "REGISTERED".

Notes: Agent 4 must implement two sequential POST calls with the same body. Capture cloud_id from the first call as cloud_id_1 and from the second as cloud_id_2; assert cloud_id_2 != cloud_id_1.

---

## TC-GOAR-3-02: Multiple sequential registrations yield unique Cloud IDs

Scenario: [BOUNDARY VALUE] Multiple sequential registrations for the same serial number (for example, three successful calls in a row) each return a Cloud ID that is unique across the entire sequence.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1002".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1002", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200
  Body contains: For each of three sequential calls, response includes "printer_id" (non-empty string), "cloud_id" matching CID-[A-F0-9]{12}, "status" == "REGISTERED".

Notes: Agent 4 must perform three POST /printers/register calls with identical bodies. Capture cloud_id_1, cloud_id_2, cloud_id_3 and assert all three are pairwise distinct.

---

## TC-GOAR-3-03: Re-registration regenerates printer_email_id and claim_code

Scenario: [HAPPY PATH] Re-registering an already-registered printer succeeds and the new response contains a printer_email_id and claim_code that both differ from those returned by the previous registration.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A printer has been registered with serial_number "SN-1003" using body {"serial_number": "SN-1003", "model_number": "HP-M404", "firmware_version": "1.0.1"}. Capture initial printer_email_id_initial and claim_code_initial from that registration response.

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1003", "model_number": "HP-M404", "firmware_version": "1.0.1"}

Expected response:
  Status: 200
  Body contains: "printer_email_id" != printer_email_id_initial and matches pattern [a-z0-9]{10}@print.hpeprint.com; "claim_code" != claim_code_initial and matches pattern [A-Z0-9]{8}; "cloud_id" matching CID-[A-F0-9]{12}; "status" == "REGISTERED".

Notes: Agent 4 must call POST /printers/register twice (initial + re-registration) and store the first response’s printer_email_id and claim_code. Assertions are made on the second response only.

---

## TC-GOAR-3-04: Duplicate printer_email_id on re-registration is rejected

Scenario: [INVALID INPUT] Re-registration with an otherwise valid request that attempts to reuse a previously assigned printer_email_id is rejected without changing any existing identifiers.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: The system has at least two registered printers:
  1) Printer A: registered with serial_number "SN-1004A".
  2) Printer B: registered with serial_number "SN-1004B".
Capture printer_email_id_A from printer A’s registration.

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1004B", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200
  Body contains: "printer_email_id" for printer B is not equal to printer_email_id_A, "cloud_id" matches CID-[A-F0-9]{12}, and existing identifiers for printer A remain unchanged when fetched via GET /printers/{printer_id_A}.

Notes: This scenario as written in the requirements assumes the ability to force a duplicate printer_email_id. The current implementation of _generate_printer_email_id() prevents reuse by looping until a unique email is found. Therefore, this scenario cannot be fulfilled by the public API alone and is effectively untestable without modifying internals. See Skipped Scenarios.

---

## TC-GOAR-3-05: Failed re-registration leaves printer_email_id and claim_code unchanged (rollback)

Scenario: [ROLLBACK] A failed re-registration that attempts to assign a duplicate printer_email_id leaves the persisted printer_email_id and claim_code unchanged from their pre-attempt values.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Printer C is registered with serial_number "SN-1005" and has known printer_email_id_C and claim_code_C. A mechanism to force _generate_printer_email_id() to return a duplicate value is not exposed by the public API.

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1005", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: N/A
  Body contains: N/A

Notes: This scenario depends on being able to induce a specific internal duplicate-email path, which cannot be controlled via the public API. It is therefore untestable as a black-box REST test without additional hooks. See Skipped Scenarios.

---

## TC-GOAR-3-06: Re-registration of CLAIMED printer preserves ownership and status

Scenario: [HAPPY PATH] Re-registering a printer that is already in CLAIMED status succeeds, returns a new Cloud ID, and the printer’s owner_user_id and CLAIMED status remain unchanged.

Requirement: AR1

Endpoint: POST /printers/register (re-registration), then GET /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A printer has been registered and claimed:
  1) Register serial_number "SN-1006" via POST /printers/register with body {"serial_number": "SN-1006", "model_number": "HP-M404", "firmware_version": "1.0.0"}; capture printer_id_1, cloud_id_1, claim_code_1.
  2) Claim via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-alpha"}; confirm response status == "CLAIMED" and owner_user_id == "user-alpha".

Request:
  Headers: {"Content-Type": "application/json"}
  Body (re-registration): {"serial_number": "SN-1006", "model_number": "HP-M404", "firmware_version": "1.0.1"}

Expected response:
  Status: 200 for POST; 200 for GET.
  Body contains: POST response has a "cloud_id" (cloud_id_2) matching CID-[A-F0-9]{12} with cloud_id_2 != cloud_id_1; "status" == "CLAIMED". GET /printers/{printer_id_1} response shows "owner_user_id" == "user-alpha" and "status" == "CLAIMED".

Notes: Agent 4 should perform POST /printers/register to re-register, then GET /printers/{printer_id_1} to verify ownership and status are unchanged.

---

## TC-GOAR-3-07: Non-owner re-registration cannot change owner_user_id

Scenario: [OWNERSHIP] A non-owner actor attempting to re-register a CLAIMED printer cannot change owner_user_id, and the printer remains associated with the original owner even though the Cloud ID is regenerated.

Requirement: AR1

Endpoint: POST /printers/register, then GET /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A printer has been registered and claimed by user "user-owner":
  1) Register serial_number "SN-1007" via POST /printers/register; capture printer_id_1, cloud_id_1, claim_code_1.
  2) Claim via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-owner"}; confirm owner_user_id == "user-owner".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1007", "model_number": "HP-M404", "firmware_version": "1.0.1"}

Expected response:
  Status: 200 for POST; 200 for GET.
  Body contains: POST /printers/register response has "cloud_id" (cloud_id_2) != cloud_id_1 and "status" == "CLAIMED". GET /printers/{printer_id_1} still reports "owner_user_id" == "user-owner".

Notes: Although the scenario mentions a "non-owner actor", the API’s auth layer only authenticates the caller and does not tie user_id to printer ownership; claim_printer controls ownership. This test therefore verifies that re-registration does not modify owner_user_id at all.

---

## TC-GOAR-3-08: Failed re-registration of CLAIMED printer rolls back without changing ownership

Scenario: [ROLLBACK] A failed re-registration of a CLAIMED printer before the Welcome Page prints leaves owner_user_id and CLAIMED status unchanged and does not persist any partial Cloud ID change.

Requirement: AR1

Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A printer has been registered and claimed:
  1) Register serial_number "SN-1008" via POST /printers/register; capture printer_id_1, cloud_id_1, claim_code_1.
  2) Claim via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-rollback"}; confirm status == "CLAIMED".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1008", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 for POST; 200 for subsequent GET.
  Body contains: POST /printers/register returns {"detail": "Welcome page failed to print for printer_id=<printer_id_1>"}. GET /printers/{printer_id_1} response shows the same "cloud_id" as before (cloud_id_1), "owner_user_id" == "user-rollback", and "status" == "CLAIMED".

Notes: This test assumes that a failed re-registration of a CLAIMED printer triggers rollback via _rollback_registration without deleting the existing printer record. However, the current implementation of _rollback_registration deletes the printer and its serial index entirely. Because of this mismatch, this scenario is untestable against the current codebase without clarifying the desired behaviour. See Skipped Scenarios.

---

## TC-GOAR-3-09: Two consecutive re-registrations produce three distinct Cloud IDs

Scenario: [HAPPY PATH] Initial registration followed by two consecutive successful re-registrations for the same serial number produces three responses whose Cloud IDs are all distinct from one another.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1009".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1009", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200 on all three calls.
  Body contains: For each call, response includes "cloud_id" matching CID-[A-F0-9]{12}. Capture cloud_id_1 (initial), cloud_id_2 (first re-registration), cloud_id_3 (second re-registration); assert all three are pairwise distinct.

Notes: Agent 4 should implement three sequential POST calls with the same body, storing and comparing all three cloud_id values.

---

## TC-GOAR-3-10: Second re-registration Cloud ID differs from both prior IDs

Scenario: [BOUNDARY VALUE] The Cloud ID from the second re-registration is explicitly verified to be different from both the first registration’s Cloud ID and the first re-registration’s Cloud ID, ensuring no reuse of earlier values.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1010".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1010", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200 on all three calls.
  Body contains: cloud_id_1, cloud_id_2, cloud_id_3 each match CID-[A-F0-9]{12}, with cloud_id_2 != cloud_id_1, cloud_id_3 != cloud_id_2, and cloud_id_3 != cloud_id_1.

Notes: This test is similar to TC-GOAR-3-09 but emphasises the comparison of cloud_id_3 to both prior IDs.

---

## TC-GOAR-3-11: Recovery re-registration after failed attempt yields a fresh Cloud ID

Scenario: [HAPPY PATH] After a failed re-registration attempt that triggers rollback, a subsequent successful re-registration for the same serial number returns a Cloud ID that is new and distinct from both the original Cloud ID and any Cloud ID generated during the failed attempt.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1011".

Request:
  Headers: {"Content-Type": "application/json"}
  Body sequence:
    1) Initial registration: {"serial_number": "SN-1011", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
    2) Failing re-registration: {"serial_number": "SN-1011", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}
    3) Recovery registration: {"serial_number": "SN-1011", "model_number": "HP-M404", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200 for initial and recovery registrations; 422 for failing re-registration.
  Body contains: Initial registration returns cloud_id_1. Failing re-registration returns {"detail": "Welcome page failed to print for printer_id=<printer_id_1>"} and no Cloud ID. Recovery registration returns cloud_id_recovery matching CID-[A-F0-9]{12} with cloud_id_recovery != cloud_id_1.

Notes: Since the rollback deletes the printer record, the recovery registration behaves as a fresh registration. Agent 4 must treat the serial_number as unused after the failing re-registration.

---

## TC-GOAR-3-12: Rollback leaves stored Cloud ID and indexes unchanged on failure

Scenario: [ROLLBACK] A re-registration attempt that fails before the Welcome Page prints leaves the stored printer record, including Cloud ID and indexes, exactly as before the attempt with no partial changes.

Requirement: AR3

Endpoint: POST /printers/register (failure), then GET /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A printer is registered with serial_number "SN-1012"; capture printer_id_1, cloud_id_1, printer_email_id_1.

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1012", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422 for POST; GET /printers/{printer_id_1} expected to be 404 under current implementation.
  Body contains: POST returns {"detail": "Welcome page failed to print for printer_id=<printer_id_1>"}. GET returns {"detail": "Printer not found"}.

Notes: The scenario text assumes the record remains with unchanged Cloud ID, but the actual implementation deletes the printer entirely in _rollback_registration. This test is therefore reframed as verification that rollback removes the record. It overlaps with AR5 and will be consolidated there; see Skipped Scenarios for the original AR3 rollback scenario as stated.

---

## TC-GOAR-3-13: Deregister and re-register yields new Cloud ID

Scenario: [HAPPY PATH] Registering, then deregistering, and then re-registering the same serial number all succeed and the Cloud ID assigned after re-registration differs from the Cloud ID that existed before deregistration.

Requirement: AR4

Endpoint: POST /printers/register, DELETE /printers/{printer_id}, POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1013".

Request:
  Headers: {"Content-Type": "application/json"}
  Body sequence:
    1) POST 1: {"serial_number": "SN-1013", "model_number": "HP-M404", "firmware_version": "1.0.0"}
    2) DELETE: path param printer_id = printer_id_1 from POST 1
    3) POST 2: {"serial_number": "SN-1013", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200 for all three calls.
  Body contains: POST 1 returns cloud_id_1 and printer_id_1. DELETE returns {"status": "DEREGISTERED", "printer_id": printer_id_1}. POST 2 returns cloud_id_2 matching CID-[A-F0-9]{12} with cloud_id_2 != cloud_id_1.

Notes: This directly validates AR4.

---

## TC-GOAR-3-14: Multiple deregister/re-register cycles yield fresh Cloud IDs each time

Scenario: [BOUNDARY VALUE] Multiple deregister-then-re-register cycles for the same serial number each produce a new Cloud ID that has never been used before for that serial number.

Requirement: AR4

Endpoint: POST /printers/register, DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1014".

Request:
  Headers: {"Content-Type": "application/json"}
  Body: {"serial_number": "SN-1014", "model_number": "HP-M404", "firmware_version": "1.0.0"}

Expected response:
  Status: 200 for all calls.
  Body contains: For two complete cycles (register -> delete -> register -> delete -> register), capture cloud_id_1, cloud_id_2, cloud_id_3; assert all three are pairwise distinct.

Notes: Agent 4 should implement a loop performing register/delete/register/delete/register for the same serial_number and compare all collected cloud_id values.

---

## TC-GOAR-3-15: Failed re-registration removes printer and indexes; next registration behaves as fresh

Scenario: [ROLLBACK] A re-registration attempt that fails before the Welcome Page prints removes the printer record and all associated indexes so that a subsequent registration of the same serial number behaves as a fresh first-time registration.

Requirement: AR5

Endpoint: POST /printers/register (failure), GET /printers/{printer_id} (verify removal), POST /printers/register (fresh registration)

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer record exists yet for serial_number "SN-1015".

Request:
  Headers: {"Content-Type": "application/json"}
  Body sequence:
    1) Initial registration: {"serial_number": "SN-1015", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
    2) Failing re-registration: {"serial_number": "SN-1015", "model_number": "HP-M404", "firmware_version": "1.0.1", "simulate_welcome_page_failure": true}
    3) Verification GET: GET /printers/{printer_id_1}
    4) Fresh registration: {"serial_number": "SN-1015", "model_number": "HP-M404", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200 for initial and fresh registrations; 422 for failing re-registration; 404 for verification GET.
  Body contains: Initial registration returns printer_id_1 and cloud_id_1. Failing re-registration returns {"detail": "Welcome page failed to print for printer_id=<printer_id_1>"}. GET /printers/{printer_id_1} returns {"detail": "Printer not found"}. Fresh registration returns new printer_id_2 != printer_id_1 and cloud_id_fresh matching CID-[A-F0-9]{12}.

Notes: This is a rollback test. Agent 4 should verify pre-state via initial registration, trigger failure, verify removal via GET, then verify fresh registration behaves like first-time registration.

---

## Skipped Scenarios

[INVALID INPUT] Re-registration with an otherwise valid request that attempts to reuse a previously assigned printer_email_id is rejected without changing any existing identifiers. — SKIPPED: Requires forcing _generate_printer_email_id() to return a specific duplicate value, which is not controllable via the public REST API. Untestable without internal hooks or configuration overrides.

[ROLLBACK] A failed re-registration that attempts to assign a duplicate printer_email_id leaves the persisted printer_email_id and claim_code unchanged from their pre-attempt values. — SKIPPED: Depends on the same internal duplicate-email path as the previous scenario; cannot be reliably induced via black-box REST calls.

[ROLLBACK] A failed re-registration of a CLAIMED printer before the Welcome Page prints leaves owner_user_id and CLAIMED status unchanged and does not persist any partial Cloud ID change. — SKIPPED: Current implementation of _rollback_registration deletes the printer record entirely, so the post-failure state described in the scenario cannot be reproduced. Behaviour requires product decision and/or code change.

[ROLLBACK] A re-registration attempt that fails before the Welcome Page prints leaves the stored printer record, including Cloud ID and indexes, exactly as before the attempt with no partial changes. — SKIPPED: Conflicts with implemented rollback semantics, which delete the printer and indexes. Test would require alternate implementation or explicit product decision.

---

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-3-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-3-02 | BOUNDARY VALUE | AC1 | POST /printers/register | valid token |
| TC-GOAR-3-03 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-3-04 | INVALID INPUT | AC2 | POST /printers/register | valid token |
| TC-GOAR-3-05 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-3-06 | HAPPY PATH | AR1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-3-07 | OWNERSHIP | AR1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-3-08 | ROLLBACK | AR1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-3-09 | HAPPY PATH | AR2 | POST /printers/register | valid token |
| TC-GOAR-3-10 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-3-11 | HAPPY PATH | AR3 | POST /printers/register | valid token |
| TC-GOAR-3-12 | ROLLBACK | AR3 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-3-13 | HAPPY PATH | AR4 | POST /printers/register, DELETE /printers/{printer_id}, POST /printers/register | valid token |
| TC-GOAR-3-14 | BOUNDARY VALUE | AR4 | POST /printers/register, DELETE /printers/{printer_id} | valid token |
| TC-GOAR-3-15 | ROLLBACK | AR5 | POST /printers/register, GET /printers/{printer_id}, POST /printers/register | valid token |
