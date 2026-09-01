# Test Cases — GOAR-7

## TC-GOAR-7-01: Re-register CLAIMED printer preserves existing claim code

Scenario: [HAPPY PATH] Re-register an already-CLAIMED printer and confirm no new claim code is generated and the existing claim code value is preserved.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token

Preconditions: 
- A printer has been registered successfully with serial_number = "SN-GOAR7-001" and claimed by user_id = "user-goar7-a".
- Capture the printer_id, original claim_code (claim_code_1), and claim_code_expires_at (expires_at_1) from the initial registration response.
- Claim the printer via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-a"}, asserting status == "CLAIMED" and owner_user_id == "user-goar7-a".

Request:
  Headers: 
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"serial_number": "SN-GOAR7-001", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200

  Body contains:
  - printer_id: non-empty string equal to the existing printer_id captured during initial registration.
  - cloud_id: string matching pattern CID-[A-F0-9]{12} (new value, not asserted against previous cloud_id in this test).
  - printer_email_id: string matching pattern [a-z0-9]{10}@print.hpeprint.com.
  - claim_code: string exactly equal to claim_code_1 (no new claim code generated).
  - claim_code_expires_at: timestamp string exactly equal to expires_at_1.
  - xmpp_node: non-empty string.
  - status: value == "CLAIMED".
  - history: list containing at least one entry that includes the substring "Registration started" or "Re-registration started".

Notes: Capture claim_code_2 and claim_code_expires_at_2 from the re-registration response and assert they equal claim_code_1 and expires_at_1 respectively. No rollback is involved; no special store reset is required.

---

## TC-GOAR-7-02: Consecutive re-registrations of CLAIMED printer do not change claim code

Scenario: [BOUNDARY VALUE] Perform two consecutive re-registrations of the same CLAIMED printer and confirm that the claim code remains unchanged across both calls.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- A printer has been registered successfully with serial_number = "SN-GOAR7-002" and claimed by user_id = "user-goar7-b".
- Capture printer_id, claim_code_1, and claim_code_expires_at_1 from the initial registration response.
- Claim the printer via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-b"} and assert status == "CLAIMED".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (Call 1): {"serial_number": "SN-GOAR7-002", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}
  Body (Call 2): {"serial_number": "SN-GOAR7-002", "model_number": "HP-LJ-4200", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status:
  - Call 1: 200
  - Call 2: 200

  Body contains (each call):
  - printer_id: non-empty string equal to the same printer_id.
  - cloud_id: CID-[A-F0-9]{12} pattern (cloud_id_1 and cloud_id_2 captured but not required to differ for AC1).
  - printer_email_id: [a-z0-9]{10}@print.hpeprint.com.
  - claim_code: value equal to claim_code_1 for both calls (no new code issued).
  - claim_code_expires_at: value equal to claim_code_expires_at_1 for both calls.
  - xmpp_node: non-empty string.
  - status: "CLAIMED" on both responses.

Notes: Assert claim_code_call1 == claim_code_call2 == claim_code_1 and claim_code_expires_at_call1 == claim_code_expires_at_call2 == claim_code_expires_at_1. No rollback; normal re-registration flow only.

---

## TC-GOAR-7-03: Ownership preserved when re-registering a CLAIMED printer

Scenario: [OWNERSHIP] Re-register a CLAIMED printer and confirm that ownership-related fields (e.g., owner_user_id and CLAIMED status) remain unchanged when no new claim code is issued.

Requirement: AC1

Endpoint: POST /printers/register (re-registration), then GET /printers/{printer_id} (ownership verification)

Auth: valid token

Preconditions:
- A printer has been registered successfully with serial_number = "SN-GOAR7-003" and claimed by user_id = "user-goar7-c".
- Capture printer_id and claim_code_1 from the initial registration response.
- Claim the printer via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-c"}, and assert response status == "CLAIMED" and owner_user_id == "user-goar7-c".

Request:
  Headers (both calls):
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json for POST; no body for GET.

  Body (POST /printers/register): {"serial_number": "SN-GOAR7-003", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Path param (GET /printers/{printer_id}): printer_id = captured printer_id.

Expected response:
  Status:
  - POST /printers/register: 200
  - GET /printers/{printer_id}: 200

  Body contains (POST):
  - printer_id: equal to captured printer_id.
  - claim_code: equal to claim_code_1.
  - status: "CLAIMED".

  Body contains (GET):
  - printer_id: equal to captured printer_id.
  - serial_number: "SN-GOAR7-003".
  - owner_user_id: "user-goar7-c".
  - status: "CLAIMED".
  - cloud_id: CID-[A-F0-9]{12} pattern.
  - printer_email_id: [a-z0-9]{10}@print.hpeprint.com.
  - xmpp_node: non-empty string.

Notes: The ownership fields (owner_user_id and status) are not present in the registration response, so they must be validated via GET /printers/{printer_id}. Verify that owner_user_id and status remain unchanged across re-registration.

---

## TC-GOAR-7-04: First-time registration of unclaimed printer issues claim code and Welcome Page

Scenario: [HAPPY PATH] First-time registration of an unclaimed printer generates a claim code and prints a Welcome Page as expected.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- No existing printer record for serial_number = "SN-GOAR7-004".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"serial_number": "SN-GOAR7-004", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200

  Body contains:
  - printer_id: non-empty string.
  - cloud_id: CID-[A-F0-9]{12}.
  - printer_email_id: [a-z0-9]{10}@print.hpeprint.com.
  - claim_code: [A-Z0-9]{8}.
  - claim_code_expires_at: timestamp string representing a time within 15 minutes of the current time.
  - xmpp_node: non-empty string.
  - status: "REGISTERED".
  - history: list containing entries including "Registration started", "Cloud identity created", and "Welcome page printed successfully; registration complete".

Notes: Since simulate_welcome_page_failure is false, generate_and_print_welcome_page must succeed; the presence of "Welcome page printed successfully; registration complete" in history confirms Welcome Page printing completed.

---

## TC-GOAR-7-05: Re-registration of unclaimed printer continues to issue claim code

Scenario: [HAPPY PATH] Re-register an unclaimed printer and confirm a claim code is generated and associated with the printer on each successful re-registration.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- A printer has been registered once with serial_number = "SN-GOAR7-005" and left unclaimed (no call to /printers/claim made).
- Capture printer_id_1, claim_code_1, and claim_code_expires_at_1 from the first registration response.
- Confirm status == "REGISTERED" on the first registration response.

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"serial_number": "SN-GOAR7-005", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200

  Body contains:
  - printer_id: equal to printer_id_1.
  - cloud_id: CID-[A-F0-9]{12} (new value distinct from original cloud_id_1 but not required to be asserted in this test).
  - printer_email_id: [a-z0-9]{10}@print.hpeprint.com.
  - claim_code: [A-Z0-9]{8} (captured as claim_code_2).
  - claim_code_expires_at: timestamp string (captured as expires_at_2).
  - xmpp_node: non-empty string.
  - status: "REGISTERED".

Notes: Assert that claim_code_2 is a non-empty string matching [A-Z0-9]{8} and that claim_code_expires_at_2 is within 15 minutes of the re-registration time. This confirms claim-code generation behavior for unclaimed printers remains intact.

---

## TC-GOAR-7-06: Consecutive re-registrations of unclaimed printer generate distinct claim codes

Scenario: [BOUNDARY VALUE] Re-register an unclaimed printer twice in succession and confirm each successful call generates a new, distinct claim code.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- A printer has been registered once with serial_number = "SN-GOAR7-006" and left unclaimed.
- Capture printer_id_1 and claim_code_1 from the first registration response.
- Confirm status == "REGISTERED" on the first registration response.

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (Call 1): {"serial_number": "SN-GOAR7-006", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}
  Body (Call 2): {"serial_number": "SN-GOAR7-006", "model_number": "HP-LJ-4200", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status:
  - Call 1: 200
  - Call 2: 200

  Body contains (Call 1):
  - printer_id: equal to printer_id_1.
  - claim_code: captured as claim_code_2.
  - status: "REGISTERED".

  Body contains (Call 2):
  - printer_id: equal to printer_id_1.
  - claim_code: captured as claim_code_3.
  - status: "REGISTERED".

Notes: Assert claim_code_1, claim_code_2, and claim_code_3 are all distinct values (claim_code_1 != claim_code_2, claim_code_2 != claim_code_3, claim_code_1 != claim_code_3), confirming new claim codes are generated for each registration of unclaimed printers.

---

## TC-GOAR-7-07: Re-register CLAIMED printer does not change claim code TTL or used flag

Scenario: [HAPPY PATH] Re-register a CLAIMED printer with a currently valid, unused claim code and confirm that the claim code’s expiry and used flags remain unchanged after re-registration.

Requirement: AR1

Endpoint: POST /printers/register, then GET /printers/{printer_id}

Auth: valid token

Preconditions:
- A printer has been registered with serial_number = "SN-GOAR7-007".
- Capture printer_id, claim_code_1, and claim_code_expires_at_1 from the registration response.
- Claim the printer via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-d"}.
- After claiming, perform GET /printers/{printer_id} to confirm:
  - status == "CLAIMED".
  - owner_user_id == "user-goar7-d".

Request:
  Headers (all calls):
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json for POST; none for GET.

  Body (POST /printers/register): {"serial_number": "SN-GOAR7-007", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Path param (GET /printers/{printer_id}): printer_id.

Expected response:
  Status:
  - POST /printers/register: 200
  - GET /printers/{printer_id}: 200

  Body contains (POST):
  - claim_code: equal to claim_code_1.
  - claim_code_expires_at: equal to claim_code_expires_at_1.

  Body contains (GET):
  - printer_id: equal to printer_id.
  - status: "CLAIMED".
  - owner_user_id: "user-goar7-d".

Notes: This test assumes claim_code.used remains True after claiming and that re-registration does not alter the `expires_at` or `used` flags for the existing claim code. However, these flags are internal to the Printer.claim_code object and not directly exposed via API responses; this scenario is therefore partially observable via claim_code_expires_at only.

---

## TC-GOAR-7-08: Re-register CLAIMED printer close to claim code expiry does not extend TTL

Scenario: [BOUNDARY VALUE] Re-register a CLAIMED printer whose claim code is close to expiry and confirm that re-registration does not extend the expiration time.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- A printer has been registered with serial_number = "SN-GOAR7-008".
- Capture printer_id, claim_code_1, and claim_code_expires_at_1 from the initial registration.
- Advance the test clock or wait until the current time is within 1 minute of claim_code_expires_at_1 (this is conceptual and may not be directly automatable without time control).
- Claim the printer using POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-e"} to move it to CLAIMED state.

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"serial_number": "SN-GOAR7-008", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200

  Body contains:
  - claim_code: equal to claim_code_1.
  - claim_code_expires_at: equal to claim_code_expires_at_1 (no extension of TTL).

Notes: Because the system does not expose claim_code.created_at or internal timing controls, the boundary condition ("close to expiry") is conceptual; the core assertion is that claim_code_expires_at is unchanged by re-registration.

---

## TC-GOAR-7-09: Claim code remains single-use after claiming and re-registering CLAIMED printer

Scenario: [OWNERSHIP] After successfully claiming a printer and then re-registering it, confirm that the claim code still behaves as single-use (cannot be used again) and that ownership is not weakened.

Requirement: AR1

Endpoint: POST /printers/register (re-registration), then POST /printers/claim (second claim attempt), then GET /printers/{printer_id}

Auth: valid token

Preconditions:
- A printer has been registered successfully with serial_number = "SN-GOAR7-009".
- Capture printer_id and claim_code_1 from the registration response.
- Claim the printer via POST /printers/claim with body {"claim_code": claim_code_1, "user_id": "user-goar7-f"}.
- Confirm claim response has status == "CLAIMED" and owner_user_id == "user-goar7-f".

Request:
  Headers (all calls):
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json for POST; none for GET.

  Body (POST /printers/register): {"serial_number": "SN-GOAR7-009", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Body (POST /printers/claim second attempt): {"claim_code": "<claim_code_1>", "user_id": "user-goar7-g"}

  Path param (GET /printers/{printer_id}): printer_id.

Expected response:
  Status:
  - POST /printers/register: 200
  - POST /printers/claim (second attempt): 400
  - GET /printers/{printer_id}: 200

  Body contains (POST /printers/claim second attempt):
  - detail: "Claim code has already been used".

  Body contains (GET):
  - owner_user_id: "user-goar7-f".
  - status: "CLAIMED".

Notes: Even after re-registration, attempting to claim the printer again with the original claim_code_1 must fail with InvalidClaimCodeError mapped to HTTP 400, and the printer’s owner_user_id must remain unchanged.

---

## TC-GOAR-7-10: Failed registration for unclaimed printer invalidates claim code

Scenario: [ROLLBACK] Trigger a registration failure before Welcome Page printing for an unclaimed printer and confirm that any claim code generated during the failed attempt cannot be used to claim the printer afterwards.

Requirement: AR2

Endpoint: POST /printers/register (failure trigger), then POST /printers/register (successful registration), then POST /printers/claim

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-010".

Request:
  Headers (all calls):
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (POST /printers/register failure): {"serial_number": "SN-GOAR7-010", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

  Body (POST /printers.register success): {"serial_number": "SN-GOAR7-010", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

  Body (POST /printers/claim with failed claim code): {"claim_code": "<claim_code_failure>", "user_id": "user-goar7-h"}

Expected response:
  Status:
  - POST /printers/register failure: 422
  - POST /printers/register success: 200
  - POST /printers/claim with failed claim code: 400

  Body contains (POST /printers/register failure):
  - detail: "Registration could not be completed. Please check your request and try again."

  Body contains (POST /printers/register success):
  - printer_id: non-empty string.
  - claim_code: captured as claim_code_success.

  Body contains (POST /printers/claim with failed claim code):
  - detail: "Claim code not recognized".

Notes: The failed registration’s claim_code_failure is internal and not returned because `_rollback_registration` removes the printer record and any associated capabilities; claim_printer must not accept any claim code from the failed attempt. Capture claim_code_success from the successful registration and use it in a separate positive claim test (outside this scenario).

---

## TC-GOAR-7-11: New claim code issued after failed registration

Scenario: [ROLLBACK] After a failed registration that invalidated a claim code, perform a subsequent successful registration and confirm a fresh claim code is generated and is the only usable one.

Requirement: AR2

Endpoint: POST /printers/register (failure), POST /printers/register (success), POST /printers/claim (success)

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-011".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (failure registration): {"serial_number": "SN-GOAR7-011", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

  Body (successful registration): {"serial_number": "SN-GOAR7-011", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

  Body (POST /printers/claim): {"claim_code": "<claim_code_success>", "user_id": "user-goar7-i"}

Expected response:
  Status:
  - failure registration: 422
  - successful registration: 200
  - POST /printers/claim: 200

  Body contains (successful registration):
  - claim_code: [A-Z0-9]{8}, captured as claim_code_success.

  Body contains (POST /printers/claim):
  - status: "CLAIMED".
  - owner_user_id: "user-goar7-i".

Notes: Ensure that only claim_code_success from the successful registration can be used to claim the printer; any claim attempt using a code from the failed registration should return "Claim code not recognized" as per TC-GOAR-7-10.

---

## TC-GOAR-7-12: Rollback removes claim code even when failure occurs just before Welcome Page

Scenario: [BOUNDARY VALUE] Simulate a failure at the last step before Welcome Page printing and confirm that rollback still removes any claim code generated in that attempt.

Requirement: AR2

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- No printer record exists for serial_number = "SN-GOAR7-012".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"serial_number": "SN-GOAR7-012", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:
  Status: 422

  Body contains:
  - detail: "Registration could not be completed. Please check your request and try again."

Notes: After this failed registration, perform POST /printers/claim with any claim code captured internally from this registration (not exposed by API; so this boundary scenario is conceptual and partially untestable from the external API). From an API perspective, claim_printer must respond with "Claim code not recognized" for any such code, consistent with TC-GOAR-7-10.

---

## TC-GOAR-7-13: Multiple successful registrations for unclaimed printer produce unique claim codes

Scenario: [HAPPY PATH] Perform two successful registrations (or re-registrations) for the same unclaimed printer and confirm each Welcome Page print uses a new, previously unseen claim code.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-013".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (Call 1): {"serial_number": "SN-GOAR7-013", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
  Body (Call 2): {"serial_number": "SN-GOAR7-013", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:
  Status:
  - Call 1: 200
  - Call 2: 200

  Body contains (Call 1):
  - claim_code: captured as claim_code_1.

  Body contains (Call 2):
  - claim_code: captured as claim_code_2.

Notes: Assert claim_code_1 != claim_code_2 and both match [A-Z0-9]{8}. Confirm both calls have status == "REGISTERED" and histories include "Welcome page printed successfully; registration complete".

---

## TC-GOAR-7-14: Three registrations for unclaimed printer yield pairwise distinct claim codes

Scenario: [BOUNDARY VALUE] Perform a third successful registration for the same unclaimed printer and confirm all three claim codes are distinct from each other and from any historical codes.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-014".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (Call 1): {"serial_number": "SN-GOAR7-014", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
  Body (Call 2): {"serial_number": "SN-GOAR7-014", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}
  Body (Call 3): {"serial_number": "SN-GOAR7-014", "model_number": "HP-LJ-4200", "firmware_version": "1.0.2", "simulate_welcome_page_failure": false}

Expected response:
  Status: 200 on all three calls.

  Body contains:
  - claim_code_1, claim_code_2, claim_code_3 captured from each call.

Notes: Assert all three claim codes are distinct: claim_code_1 != claim_code_2, claim_code_2 != claim_code_3, claim_code_1 != claim_code_3. Each must match [A-Z0-9]{8}.

---

## TC-GOAR-7-15: Re-using old claim code for unclaimed printer is rejected

Scenario: [INVALID INPUT] Attempt to re-use an old claim code from a prior registration for an unclaimed printer and confirm it is rejected as invalid.

Requirement: AR3

Endpoint: POST /printers/claim

Auth: valid token

Preconditions:
- A printer has been registered twice with serial_number = "SN-GOAR7-015" and left unclaimed.
- Capture claim_code_1 from the first registration and claim_code_2 from the second registration.

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body: {"claim_code": "<claim_code_1>", "user_id": "user-goar7-j"}

Expected response:
  Status: 400

  Body contains:
  - detail: "Claim code not recognized" or "Claim code has expired" depending on TTL, but the important assertion is that the old claim_code_1 cannot be used to claim the printer once a later claim_code_2 has been issued and used.

Notes: This scenario is partially dependent on claim code TTL and store behavior; ensure claim_code_2 is used to successfully claim the printer in a separate positive test.

---

## TC-GOAR-7-16: Claim with rolled-back claim code is rejected

Scenario: [HAPPY PATH] Attempt to claim a printer using a claim code originating from a registration that was rolled back and confirm the claim attempt is rejected.

Requirement: AR4

Endpoint: POST /printers/register (failure), then POST /printers/claim

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-016".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (failure registration): {"serial_number": "SN-GOAR7-016", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

  Body (POST /printers/claim): {"claim_code": "<rolled_back_claim_code>", "user_id": "user-goar7-k"}

Expected response:
  Status:
  - failure registration: 422
  - POST /printers/claim: 400

  Body contains (POST /printers/claim):
  - detail: "Claim code not recognized".

Notes: The rolled-back claim code value is not exposed via API; this test conceptually asserts that any code generated during a failed, rolled-back registration cannot later be used to claim a printer.

---

## TC-GOAR-7-17: Printer cannot be claimed by any rolled-back claim code after rollback

Scenario: [ROLLBACK] After rollback of a failed registration, confirm the printer cannot be claimed by any claim code that was generated during that failed attempt.

Requirement: AR4

Endpoint: POST /printers/register (failure), POST /printers/claim

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-017".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (failure registration): {"serial_number": "SN-GOAR7-017", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

  Body (POST /printers/claim): {"claim_code": "<rolled_back_claim_code>", "user_id": "user-goar7-l"}

Expected response:
  Status:
  - failure registration: 422
  - POST /printers/claim: 400

  Body contains (POST /printers/claim):
  - detail: "Claim code not recognized".

Notes: Same as TC-GOAR-7-16 but framed explicitly around rollback behavior; confirms rolled-back registrations do not leave any usable claim codes behind.

---

## TC-GOAR-7-18: Rolled-back claim code cannot be used immediately or later

Scenario: [BOUNDARY VALUE] Attempt to claim with a rolled-back claim code immediately after rollback and again after some time has passed, confirming both attempts are rejected.

Requirement: AR4

Endpoint: POST /printers/register (failure), POST /printers/claim (immediate), POST /printers/claim (delayed)

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-018".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (failure registration): {"serial_number": "SN-GOAR7-018", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

  Body (immediate POST /printers/claim): {"claim_code": "<rolled_back_claim_code>", "user_id": "user-goar7-m"}

  Body (delayed POST /printers/claim): {"claim_code": "<rolled_back_claim_code>", "user_id": "user-goar7-n"}

Expected response:
  Status:
  - failure registration: 422
  - immediate POST /printers/claim: 400
  - delayed POST /printers/claim: 400

  Body contains (both claim attempts):
  - detail: "Claim code not recognized".

Notes: This test conceptually confirms that rolled-back claim codes remain unusable regardless of timing; however, actual claim code values are internal and not exposed by the API.

---

## TC-GOAR-7-19: Multiple claim codes for unclaimed printer allow only first claim

Scenario: [HAPPY PATH] Issue multiple claim codes for the same unclaimed printer via overlapping registration attempts and confirm that only the first successful claim transitions the printer to CLAIMED.

Requirement: AR5

Endpoint: POST /printers/register (x2), POST /printers/claim (x2)

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-019".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (registration 1): {"serial_number": "SN-GOAR7-019", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Body (registration 2): {"serial_number": "SN-GOAR7-019", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

  Body (claim 1): {"claim_code": "<claim_code_1>", "user_id": "user-goar7-o"}

  Body (claim 2): {"claim_code": "<claim_code_2>", "user_id": "user-goar7-p"}

Expected response:
  Status:
  - registration 1: 200
  - registration 2: 200
  - claim 1: 200
  - claim 2: 400

  Body contains (claim 1):
  - status: "CLAIMED".
  - owner_user_id: "user-goar7-o".

  Body contains (claim 2):
  - detail: "Printer is already claimed".

Notes: Even though two distinct claim codes exist for the same printer, only the first successful claim should transition the printer to CLAIMED; subsequent claims must be rejected.

---

## TC-GOAR-7-20: Ownership unchanged when attempting second claim with different claim code

Scenario: [OWNERSHIP] After the printer becomes CLAIMED via one claim code, attempt to claim it using another valid-looking claim code and confirm ownership does not change and the second claim is rejected.

Requirement: AR5

Endpoint: POST /printers/register (x2), POST /printers/claim (x2), GET /printers/{printer_id}

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-020".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (registration 1): {"serial_number": "SN-GOAR7-020", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Body (registration 2): {"serial_number": "SN-GOAR7-020", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

  Body (claim 1): {"claim_code": "<claim_code_1>", "user_id": "user-goar7-q"}

  Body (claim 2): {"claim_code": "<claim_code_2>", "user_id": "user-goar7-r"}

  Path param (GET /printers/{printer_id}): printer_id.

Expected response:
  Status:
  - registration 1: 200
  - registration 2: 200
  - claim 1: 200
  - claim 2: 400
  - GET /printers/{printer_id}: 200

  Body contains (claim 2):
  - detail: "Printer is already claimed".

  Body contains (GET):
  - owner_user_id: "user-goar7-q".
  - status: "CLAIMED".

Notes: Ownership must remain with user-goar7-q even after a second claim attempt using a different claim code; verify via GET.

---

## TC-GOAR-7-21: Concurrent claim attempts with two claim codes yield at most one successful claim

Scenario: [BOUNDARY VALUE] Attempt to claim the printer simultaneously with two different claim codes and confirm that at most one claim succeeds and subsequent claims are rejected.

Requirement: AR5

Endpoint: POST /printers/register (x2), POST /printers/claim (x2)

Auth: valid token

Preconditions:
- No printer record exists yet for serial_number = "SN-GOAR7-021".

Request:
  Headers:
  - Authorization header attached by conftest.py client fixture by default — no extra code needed.
  - Content-Type: application/json

  Body (registration 1): {"serial_number": "SN-GOAR7-021", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}

  Body (registration 2): {"serial_number": "SN-GOAR7-021", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

  Body (claim attempt A): {"claim_code": "<claim_code_1>", "user_id": "user-goar7-s"}

  Body (claim attempt B): {"claim_code": "<claim_code_2>", "user_id": "user-goar7-t"}

Expected response:
  Status:
  - registration 1: 200
  - registration 2: 200
  - One of the claim attempts (A or B): 200
  - The other claim attempt: 400

  Body contains (successful claim):
  - status: "CLAIMED".

  Body contains (failed claim):
  - detail: "Printer is already claimed".

Notes: In automation, the "simultaneous" aspect can be approximated by issuing the two claim requests sequentially in close succession; the core assertion is that only the first claim succeeds and the second is rejected.

---

## Skipped Scenarios

None.

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-7-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-7-02 | BOUNDARY VALUE | AC1 | POST /printers/register | valid token |
| TC-GOAR-7-03 | OWNERSHIP | AC1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-7-04 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-7-05 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-7-06 | BOUNDARY VALUE | AC2 | POST /printers/register | valid token |
| TC-GOAR-7-07 | HAPPY PATH | AR1 | POST /printers/register, GET /printers/{printer_id} | valid token |
| TC-GOAR-7-08 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-7-09 | OWNERSHIP | AR1 | POST /printers/register, POST /printers/claim, GET /printers/{printer_id} | valid token |
| TC-GOAR-7-10 | ROLLBACK | AR2 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-11 | ROLLBACK | AR2 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-12 | BOUNDARY VALUE | AR2 | POST /printers/register | valid token |
| TC-GOAR-7-13 | HAPPY PATH | AR3 | POST /printers/register | valid token |
| TC-GOAR-7-14 | BOUNDARY VALUE | AR3 | POST /printers/register | valid token |
| TC-GOAR-7-15 | INVALID INPUT | AR3 | POST /printers/claim | valid token |
| TC-GOAR-7-16 | HAPPY PATH | AR4 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-17 | ROLLBACK | AR4 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-18 | BOUNDARY VALUE | AR4 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-19 | HAPPY PATH | AR5 | POST /printers/register, POST /printers/claim | valid token |
| TC-GOAR-7-20 | OWNERSHIP | AR5 | POST /printers/register, POST /printers/claim, GET /printers/{printer_id} | valid token |
| TC-GOAR-7-21 | BOUNDARY VALUE | AR5 | POST /printers/register, POST /printers/claim | valid token |
