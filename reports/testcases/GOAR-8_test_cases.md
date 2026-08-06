# Test Cases: GOAR-8

## TC-GOAR-8-01
Maps to: AC #1
Preconditions:
- A printer has already been registered and successfully claimed by `owner-123`.
- The printer is in status `CLAIMED`.
- The printer has an existing claim code value that can be used in the request.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "attacker-456"
   }

Expected Result:
- HTTP 400 response.
- Response body contains:
  {
    "detail": "Printer is already claimed"
  }
- The existing ownership claim is preserved and not overwritten.

## TC-GOAR-8-02
Maps to: AC #2
Preconditions:
- A printer has been registered and is currently in status `REGISTERED`.
- The printer has a valid, unused claim code that has not expired.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<valid-unused-claim-code>",
     "user_id": "user-123"
   }

Expected Result:
- HTTP 200 response.
- Response body contains:
  {
    "printer_id": "<printer-id>",
    "status": "CLAIMED",
    "owner_user_id": "user-123"
  }
- The printer transitions to status `CLAIMED` and ownership is assigned to `user-123`.

## TC-GOAR-8-03
Maps to: AC #3
Preconditions:
- A printer has already been claimed by `owner-123` and is in status `CLAIMED`.
- The printer retains its original owner identity.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "attacker-456"
   }
2. Call `GET /printers/<printer-id>`.

Expected Result:
- Step 1 returns HTTP 400 with response body:
  {
    "detail": "Printer is already claimed"
  }
- Step 2 returns HTTP 200 with the printer resource showing:
  {
    "printer_id": "<printer-id>",
    "status": "CLAIMED",
    "owner_user_id": "owner-123"
  }
- No ownership state mutation occurs and the existing owner claim remains unchanged.

## TC-GOAR-8-04
Maps to: AC #4
Preconditions:
- A printer exists in status `CLAIMED`.
- A valid claim code is associated with that printer and is still unused and unexpired.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<valid-unused-claim-code-for-claimed-printer>",
     "user_id": "attacker-456"
   }

Expected Result:
- HTTP 400 response.
- Response body contains:
  {
    "detail": "Printer is already claimed"
  }
- The claim attempt is rejected even though the code itself is valid and unused, preventing takeover of the already-owned printer.

## TC-GOAR-8-05
Maps to: AC #5
Preconditions:
- A printer has already been claimed by `owner-123` and is in status `CLAIMED`.
- The printer has a known claim code value.

Steps:
1. Call `POST /printers/claim` with request body using the original owner:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "owner-123"
   }
2. Call `POST /printers/claim` with request body using a different user:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "attacker-456"
   }

Expected Result:
- Both steps return HTTP 400 responses.
- Both response bodies contain:
  {
    "detail": "Printer is already claimed"
  }
- The rejection is the same regardless of whether the claim attempt comes from the original owner or a different user.
