# GOAR-2: Enforce Claim Code expiry (15 minutes)

**Type:** Story  
**Priority:** High  
**Status:** Ready for QA  

## Description
As HP, I want Claim Codes to expire 15 minutes after they are generated, so
that a leaked or stale claim code printed on an old Welcome Page cannot be
used indefinitely to claim a printer that isn't actually the claimant's.
Currently, ClaimCode.expires_at is calculated and stored at registration
time, but nothing in the claim flow actually checks it -- an expired code is
still accepted.
Steps to Reproduce (current bug behaviour):
Register a printer, capture the claim code and claim_code_expires_at.
Wait until (or simulate) expires_at has passed.
Call POST /printers/claim with that code.
Actual: claim succeeds.
Expected: claim is rejected with an "expired" error.
Acceptance Criteria:
Claim codes expire exactly 15 minutes after created_at.
Attempting to claim a printer with an expired claim code returns a clear
error (HTTP 400) and does NOT change printer ownership or status.
Attempting to claim with a valid, unexpired code still works as before.
Attempting to reuse an already-used claim code is still rejected
(existing behaviour -- do not regress).

