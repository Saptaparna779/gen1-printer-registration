# Test Cases — GOAR-16

## TC-GOAR-16-01: Registration error returns sanitized message on RegistrationError

Scenario: [HAPPY PATH] Registration endpoint returns a generic, non-specific error message when a RegistrationError is raised, with no internal implementation details exposed.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: A registration attempt for serial_number "SN-GOAR16-001" will trigger a RegistrationError by causing a WelcomePagePrintError via simulate_welcome_page_failure=true.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR16-001", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."}

Notes: This test relies on registration.register_printer raising RegistrationError by way of WelcomePagePrintError when simulate_welcome_page_failure is true. No state verification is required after the call because rollback behavior is covered by GOAR-3.

---

## TC-GOAR-16-02: Deregistration error returns sanitized message on RegistrationError

Scenario: [HAPPY PATH] Deregistration endpoint returns a generic, non-specific error message when a RegistrationError is raised, with no internal implementation details exposed.

Requirement: AC1

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: No printer exists with printer_id "non-existent-id-GOAR16-002" so that registration.deregister_printer raises RegistrationError("No printer found with id non-existent-id-GOAR16-002").

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none

Expected response:

  Status: 404

  Body contains: {"detail": "Printer not found."}

Notes: This test ensures that internal exception text (e.g., "No printer found with id ...") is not exposed; only the sanitized message is returned.

---

## TC-GOAR-16-03: Registration error message excludes internal identifiers

Scenario: [INVALID INPUT] Registration error response is verified to avoid including internal function names, module names, stack trace fragments, or configuration values in the returned message.

Requirement: AC1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Prepare a registration request that will raise RegistrationError due to missing required fields by using empty strings for serial_number, model_number, and firmware_version.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "", "model_number": "", "firmware_version": "", "simulate_welcome_page_failure": false}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."} and must not contain substrings like "register_printer", "app.registration", "Traceback", or environment/configuration values.

Notes: Agent 4 should assert the exact detail string and additionally check absence (e.g., using "not in") for known internal-identifiers substrings.

---

## TC-GOAR-16-04: Deregistration error message excludes internal identifiers

Scenario: [INVALID INPUT] Deregistration error response is verified to avoid including internal function names, module names, stack trace fragments, or configuration values in the returned message.

Requirement: AC1

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Use a clearly invalid printer_id value "non-existent-id-GOAR16-004" for which registration.deregister_printer will raise RegistrationError("No printer found with id non-existent-id-GOAR16-004").

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none

Expected response:

  Status: 404

  Body contains: {"detail": "Printer not found."} and must not contain substrings like "deregister_printer", "app.registration", "Traceback", or configuration values.

Notes: Agent 4 should assert the exact detail string and additionally check that the response body does not include internal-identifiers substrings.

---

## TC-GOAR-16-05: Registration logs detailed exception while returning sanitized error

Scenario: [HAPPY PATH] When a RegistrationError occurs during registration, a server-side log entry is generated that contains the detailed exception text while the client sees only the sanitized message.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Configure logging capture in the pytest test (using caplog fixture) for logger "app.main" or root logger so that log records from app.main are visible. Use a registration request that will cause RegistrationError via simulate_welcome_page_failure=true for serial_number "SN-GOAR16-005".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR16-005", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."}

Notes: Agent 4 must assert that caplog.records contains at least one record with level ERROR where the message starts with "Registration failed for serial_number=SN-GOAR16-005" and includes the original exception text from RegistrationError (e.g., "Welcome page failed to print"), while the HTTP response detail remains the sanitized message.

---

## TC-GOAR-16-06: Deregistration logs detailed exception while returning sanitized error

Scenario: [HAPPY PATH] When a RegistrationError occurs during deregistration, a server-side log entry is generated that contains the detailed exception text while the client sees only the sanitized message.

Requirement: AC2

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Configure logging capture in pytest (caplog fixture) for logger "app.main" or root logger. Use printer_id "non-existent-id-GOAR16-006" which will cause registration.deregister_printer to raise RegistrationError("No printer found with id non-existent-id-GOAR16-006").

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none

Expected response:

  Status: 404

  Body contains: {"detail": "Printer not found."}

Notes: Agent 4 must assert that caplog.records contains at least one ERROR-level log whose message starts with "Deregistration failed for printer_id=non-existent-id-GOAR16-006" and includes the original exception text from RegistrationError, while the HTTP response detail remains the sanitized message.

---

## TC-GOAR-16-07: Multiple registration errors still log detailed exceptions with consistent response

Scenario: [ROLLBACK]   Multiple sequential RegistrationError occurrences on registration produce corresponding detailed log entries without altering the external API error message format.

Requirement: AC2

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Configure caplog to capture logs for logger "app.main". Use the same serial_number "SN-GOAR16-007" for two sequential registration attempts with simulate_welcome_page_failure=true, ensuring each attempt raises RegistrationError via WelcomePagePrintError.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: Two sequential POST calls with body {"serial_number": "SN-GOAR16-007", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422 for both calls

  Body contains: For each call, response body {"detail": "Registration could not be completed. Please check your request and try again."}.

Notes: This is a rollback-path logging test. Agent 4 must verify that caplog.records includes at least two ERROR-level entries for the given serial_number and that each error log corresponds to one call (e.g., by counting entries where message starts with "Registration failed for serial_number=SN-GOAR16-007"). No additional state verification is required because registration rollback is validated in other tickets.

---

## TC-GOAR-16-08: Multiple deregistration errors still log detailed exceptions with consistent response

Scenario: [ROLLBACK]   Multiple sequential RegistrationError occurrences on deregistration produce corresponding detailed log entries without altering the external API error message format.

Requirement: AC2

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Configure caplog to capture logs for logger "app.main". Use a fixed printer_id "non-existent-id-GOAR16-008" for two sequential DELETE calls so that registration.deregister_printer raises RegistrationError each time.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none for each call

Expected response:

  Status: 404 for both calls

  Body contains: For each call, response body {"detail": "Printer not found."}.

Notes: This is a rollback-path equivalent for deregistration errors. Agent 4 must verify that caplog.records contains at least two ERROR-level log entries starting with "Deregistration failed for printer_id=non-existent-id-GOAR16-008" and that every error response keeps the same sanitized message.

---

## TC-GOAR-16-09: Registration errors still return HTTP 422 after sanitization

Scenario: [HAPPY PATH] Registration failures that raise RegistrationError continue to return HTTP 422 responses after sanitization changes are applied.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Use a registration request that raises RegistrationError via simulate_welcome_page_failure=true for serial_number "SN-GOAR16-009".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR16-009", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."}.

Notes: This test focuses specifically on confirming the HTTP status code remains 422 for RegistrationError on registration.

---

## TC-GOAR-16-10: Deregistration errors still return HTTP 404 after sanitization

Scenario: [HAPPY PATH] Deregistration failures that raise RegistrationError continue to return HTTP 404 responses after sanitization changes are applied.

Requirement: AC3

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Use printer_id "non-existent-id-GOAR16-010" without any existing printer, ensuring registration.deregister_printer raises RegistrationError.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none

Expected response:

  Status: 404

  Body contains: {"detail": "Printer not found."}.

Notes: This test focuses specifically on confirming the HTTP status code remains 404 for RegistrationError on deregistration.

---

## TC-GOAR-16-11: Different registration error causes still mapped to HTTP 422

Scenario: [BOUNDARY VALUE] Registration error handling is validated across different RegistrationError causes to confirm all still map to HTTP 422 responses.

Requirement: AC3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Two different RegistrationError conditions must be triggered:
  1. Missing required fields by using empty strings.
  2. Model family mismatch on re-registration by registering an initial printer and then attempting to re-register with a different-model-family value.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: 
    - Call A (missing fields): {"serial_number": "", "model_number": "", "firmware_version": "", "simulate_welcome_page_failure": false}
    - Call B1 (initial registration): {"serial_number": "SN-GOAR16-011", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
    - Call B2 (re-registration with different family): {"serial_number": "SN-GOAR16-011", "model_number": "HP-COLOR-1000", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:

  Status: 
    - Call A: 422
    - Call B2: 422

  Body contains: For both RegistrationError cases, response detail "Registration could not be completed. Please check your request and try again.".

Notes: Agent 4 should verify that both different causes of RegistrationError (validation failure and model family mismatch) still result in HTTP 422 with the same sanitized error message.

---

## TC-GOAR-16-12: Different deregistration error causes still mapped to HTTP 404

Scenario: [BOUNDARY VALUE] Deregistration error handling is validated across different RegistrationError causes to confirm all still map to HTTP 404 responses.

Requirement: AC3

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Trigger two different RegistrationError conditions in deregister_printer:
  1. Directly using a non-existent printer_id.
  2. Deregistering a printer_id that has been deleted in advance.

Request:

  Headers: {"Content-Type": "application/json"}

  Body:
    - Call A: DELETE /printers/non-existent-id-GOAR16-012-A
    - Call B1: Register a printer via POST /printers/register with body {"serial_number": "SN-GOAR16-012", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false} to obtain printer_id.
    - Call B2: DELETE /printers/{printer_id} to deregister successfully.
    - Call B3: DELETE /printers/{same printer_id} again to raise RegistrationError from deregister_printer because store.get_printer returns None.

Expected response:

  Status:
    - Call A: 404
    - Call B3: 404

  Body contains: For both error cases, response detail {"detail": "Printer not found."}.

Notes: Agent 4 must issue calls in the described sequence to create the second error condition and then assert both error responses have status 404 with the sanitized message.

---

## TC-GOAR-16-13: All registration RegistrationError paths return consistent sanitized message

Scenario: [HAPPY PATH] Any RegistrationError path within POST /printers/register is verified to return the same generic sanitized error message pattern without leaking internal identifiers.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: The test must exercise at least two distinct RegistrationError sources for registration: missing required fields and WelcomePagePrintError rollback.

Request:

  Headers: {"Content-Type": "application/json"}

  Body:
    - Call A: {"serial_number": "", "model_number": "", "firmware_version": "", "simulate_welcome_page_failure": false}
    - Call B: {"serial_number": "SN-GOAR16-013", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status:
    - Call A: 422
    - Call B: 422

  Body contains: For both calls, response detail "Registration could not be completed. Please check your request and try again." and no internal identifiers.

Notes: Agent 4 should assert identical detail strings across the two error cases and confirm absence of internal-identifiers substrings in both responses.

---

## TC-GOAR-16-14: Newly introduced registration error branches still produce sanitized messages

Scenario: [BOUNDARY VALUE] Newly introduced or less common RegistrationError branches in registration are exercised to confirm they still produce sanitized, non-leaking error messages.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Exercise the model family mismatch branch in registration.register_printer, which is a less common error path, by first registering a printer and then re-registering the same serial_number with a different model family.

Request:

  Headers: {"Content-Type": "application/json"}

  Body:
    - Call A: {"serial_number": "SN-GOAR16-014", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}
    - Call B: {"serial_number": "SN-GOAR16-014", "model_number": "HP-COLOR-1000", "firmware_version": "1.0.1", "simulate_welcome_page_failure": false}

Expected response:

  Status: Call B returns 422

  Body contains: For Call B, response detail "Registration could not be completed. Please check your request and try again." without internal identifiers.

Notes: This test specifically validates that the GOAR-15 model family mismatch RegistrationError path is also sanitized by the GOAR-16 changes.

---

## TC-GOAR-16-15: Registration rollback paths expose only sanitized messages

Scenario: [ROLLBACK]   A failed registration via any RegistrationError path leaves only sanitized error details visible externally while all detailed context remains confined to server logs.

Requirement: AR1

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Configure caplog to capture logs for logger "app.main" and "app.registration". Trigger a WelcomePagePrintError via simulate_welcome_page_failure=true for serial_number "SN-GOAR16-015".

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "SN-GOAR16-015", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."} and no internal identifiers.

Notes: This is a rollback test. Agent 4 must: (1) assert that caplog contains a RegistrationError-related log entry with detailed text (e.g., message from WelcomePagePrintError) and (2) confirm that the HTTP response only contains the sanitized message. No state re-check is needed because rollback semantics are handled in other tickets.

---

## TC-GOAR-16-16: All deregistration RegistrationError paths return consistent sanitized message

Scenario: [HAPPY PATH] Any RegistrationError path within DELETE /printers/{printer_id} is verified to return a generic sanitized error message such as "Printer not found." without exposing internal details.

Requirement: AR2

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Trigger at least two different deregistration error conditions that both lead to RegistrationError in deregister_printer: deleting a non-existent printer_id and re-deleting a printer_id that has already been deleted.

Request:

  Headers: {"Content-Type": "application/json"}

  Body:
    - Call A: DELETE /printers/non-existent-id-GOAR16-016-A
    - Call B1: POST /printers/register with {"serial_number": "SN-GOAR16-016", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false} to obtain printer_id.
    - Call B2: DELETE /printers/{printer_id} (successful deregistration).
    - Call B3: DELETE /printers/{same printer_id} again.

Expected response:

  Status:
    - Call A: 404
    - Call B3: 404

  Body contains: For both error calls, detail {"detail": "Printer not found."} with no internal identifiers.

Notes: Agent 4 should confirm identical sanitized messages for both deregistration error paths and absence of internal-identifiers substrings.

---

## TC-GOAR-16-17: Deregistration boundary error paths still sanitized

Scenario: [BOUNDARY VALUE] Less frequently used or newly added RegistrationError branches for deregistration are exercised to confirm they all surface the same sanitized error pattern.

Requirement: AR2

Endpoint: DELETE /printers/{printer_id}

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Use a synthetic printer_id "boundary-non-existent-id-GOAR16-017" that will always cause registration.deregister_printer to raise RegistrationError("No printer found with id boundary-non-existent-id-GOAR16-017").

Request:

  Headers: {"Content-Type": "application/json"}

  Body: none

Expected response:

  Status: 404

  Body contains: {"detail": "Printer not found."} and no internal identifiers.

Notes: This test explicitly targets the boundary case of a non-existent printer_id with a distinct pattern to ensure error handling does not treat certain IDs differently.

---

## TC-GOAR-16-18: Error responses never echo user-supplied free-form values

Scenario: [INVALID INPUT] Registration error responses are checked to ensure they never echo user-supplied free-form values (such as arbitrary request fields) back to the client in the error detail.

Requirement: AR3

Endpoint: POST /printers/register

Auth: valid token (Authorization header attached by conftest.py client fixture by default — no extra code needed.)

Preconditions: Use a registration request with deliberately crafted free-form values containing special characters, HTML, and JSON-like text to trigger RegistrationError via missing required fields or WelcomePagePrintError.

Request:

  Headers: {"Content-Type": "application/json"}

  Body: {"serial_number": "   ", "model_number": "<script>alert('x')</script>", "firmware_version": "{\"key\": \"value\"}", "simulate_welcome_page_failure": false}

Expected response:

  Status: 422

  Body contains: {"detail": "Registration could not be completed. Please check your request and try again."} and must not contain any of the user-supplied free-form substrings such as "<script>alert('x')</script>" or "{\"key\": \"value\"}".

Notes: Agent 4 should assert both the exact sanitized detail and that none of the specially-crafted input substrings appear in the error message.

---

## Skipped Scenarios

[INVALID INPUT] Deregistration error responses are checked to ensure they never echo user-supplied free-form values (such as arbitrary identifiers or payload content) back to the client in the error detail.                 Requirement: AR3 — SKIPPED: The DELETE /printers/{printer_id} endpoint does not accept a request body; deregistration errors derive from server-side lookup failures on the path parameter value. GOAR-16 open question 1 excludes assumptions about sanitization for non-RegistrationError exception types, so additional user-input reflection tests on other endpoints (e.g., /printers/claim) are out of scope.
[BOUNDARY VALUE] Error responses are validated using user-supplied inputs containing special characters, HTML, or JSON-like text to confirm none of these values appear in the sanitized messages.                  Requirement: AR3 — SKIPPED: This scenario is broader than RegistrationError on register/deregister endpoints and overlaps with open question 1 (scope of sanitization beyond RegistrationError). Without explicit guidance, treating all possible error types and endpoints as sanitized would require assumptions beyond GOAR-16.

## Summary Table

| TC ID | Category | Requirement | Endpoint | Auth |
|-------|----------|-------------|----------|------|
| TC-GOAR-16-01 | HAPPY PATH | AC1 | POST /printers/register | valid token |
| TC-GOAR-16-02 | HAPPY PATH | AC1 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-03 | INVALID INPUT | AC1 | POST /printers/register | valid token |
| TC-GOAR-16-04 | INVALID INPUT | AC1 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-05 | HAPPY PATH | AC2 | POST /printers/register | valid token |
| TC-GOAR-16-06 | HAPPY PATH | AC2 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-07 | ROLLBACK | AC2 | POST /printers/register | valid token |
| TC-GOAR-16-08 | ROLLBACK | AC2 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-09 | HAPPY PATH | AC3 | POST /printers/register | valid token |
| TC-GOAR-16-10 | HAPPY PATH | AC3 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-11 | BOUNDARY VALUE | AC3 | POST /printers/register | valid token |
| TC-GOAR-16-12 | BOUNDARY VALUE | AC3 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-13 | HAPPY PATH | AR1 | POST /printers/register | valid token |
| TC-GOAR-16-14 | BOUNDARY VALUE | AR1 | POST /printers/register | valid token |
| TC-GOAR-16-15 | ROLLBACK | AR1 | POST /printers/register | valid token |
| TC-GOAR-16-16 | HAPPY PATH | AR2 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-17 | BOUNDARY VALUE | AR2 | DELETE /printers/{printer_id} | valid token |
| TC-GOAR-16-18 | INVALID INPUT | AR3 | POST /printers/register | valid token |

