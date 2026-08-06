# Test Cases: GOAR-8

## TC-GOAR-8-01
Maps to: AC #1
Preconditions:
- A printer exists and is already claimed by user-abc.
- A separate valid, unused claim code for that printer is available to the tester.
Steps:
1. POST /printers/claim
   Request body:
   {
     "printer_id": "<existing-claimed-printer-id>",
     "claim_code": "<valid-unused-claim-code>",
     "user_id": "user-def"
   }
Expected Result:
- Status code: 409 Conflict
- Response body shape:
  {
    "error": {
      "code": "already_claimed",
      "message": "Printer is already claimed"
    }
  }
- The printer's owner remains unchanged (still user-abc).

## TC-GOAR-8-02
Maps to: AC #2
Preconditions:
- A new printer is registered and is not yet claimed.
Steps:
1. POST /printers/register
   Request body:
   {
     "serial_number": "PRN-TEST-001",
     "user_id": "user-abc"
   }
2. POST /printers/claim
   Request body:
   {
     "printer_id": "<printer-id-from-register-response>",
     "claim_code": "<claim-code-from-register-response>",
     "user_id": "user-abc"
   }
Expected Result:
- Status code: 200 OK
- Response body shape:
  {
    "printer_id": "<printer-id>",
    "status": "claimed",
    "owner_user_id": "user-abc"
  }
