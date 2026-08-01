# GOAR-5: Re-registration silently un-claims an already-claimed printer

**Type:** Bug  
**Priority:** Highest  
**Status:** Ready for QA  

## Description
A customer reported their printer suddenly disappeared from HP Smart and
Instant Ink stopped working, despite never removing it. Investigation shows
that when a printer with the same serial number is registered again (e.g.
triggered by a firmware update that re-runs the onboarding handshake), the
system creates a brand-new internal printer record and overwrites the
existing one -- wiping the owner_user_id, claim status, and registration
history of the already-claimed printer in the process.
Steps to Reproduce:
Register printer SN-9999 and claim it with user_id="user-abc".
Confirm GET /printers/{id} shows status: CLAIMED, owner_user_id:
"user-abc".
Call register again with serial SN-9999 (simulating a re-onboard
handshake).
Actual: the printer's status resets to REGISTERED and owner_user_id
becomes null. Registration history prior to the re-registration is lost.
Expected: re-registering an already-CLAIMED printer must preserve
owner_user_id, status, and prior history.
Acceptance Criteria:
Re-registering an already-claimed printer does not clear owner_user_id.
Re-registering an already-claimed printer does not reset status away
from CLAIMED.
Registration history is preserved (appended to, not replaced).
First-time registration of a genuinely new serial number is unaffected.
Impact: Critical -- direct customer-facing impact, loss of subscription
linkage.

