# Test Cases: GOAR-8

## TC-GOAR-8-01
Maps to: AC #1
Preconditions:
- A printer has already been registered and successfully claimed by `owner-123`.
- The printer is in status `CLAIMED`.

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
- The existing ownership is preserved and not overwritten.

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

## TC-GOAR-8-03
Maps to: AC #1 [unconfirmed]
Preconditions:
- A printer has already been claimed by `owner-123` and is in status `CLAIMED`.
- The printer retains its original ownership claim.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "attacker-456"
   }
2. Call `GET /printers/<printer-id>` to verify ownership.

Expected Result:
- Step 1 returns HTTP 400 with response body:
  {
    "detail": "Printer is already claimed"
  }
- Step 2 returns HTTP 200 and the printer resource shows:
  {
    "printer_id": "<printer-id>",
    "status": "CLAIMED",
    "owner_user_id": "owner-123"
  }
- The existing owner claim remains unchanged and ownership is not overwritten.

## TC-GOAR-8-04
Maps to: AC #2 [unconfirmed]
Preconditions:
- A printer is already claimed and in status `CLAIMED`.
- A claim attempt is made using the printer's existing claim code.

Steps:
1. Call `POST /printers/claim` with request body:
   {
     "claim_code": "<existing-claimed-printer-claim-code>",
     "user_id": "attacker-456"
   }

Expected Result:
- HTTP 400 response.
- Response body contains a structured error object:
  {
    "detail": "Printer is already claimed"
  }
- The failure is explicitly observable as a rejected claim attempt and not silently ignored.
