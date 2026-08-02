# GOAR-8: claim_printer() does not check if the target printer is already claimed

**Type:** Bug  
**Priority:** Highest  
**Status:** Ready for QA  

## Description
claim_printer() only checks whether the claim_code itself has already been
used -- it never checks whether the target printer's status is already
CLAIMED by a different owner. Combined with GOAR-7, this is the concrete
exploit path for hijacking an already-owned printer.
Steps to Reproduce:
Register and claim a printer with user_id="user-abc".
Obtain any valid, unused claim code associated with that printer_id
(e.g. via GOAR-7's regeneration bug).
Call claim_printer() with that code and a different user_id.
Actual: the claim succeeds, overwriting owner_user_id.
Expected: claiming should be rejected if the printer is already
CLAIMED.
Acceptance Criteria:
claim_printer() raises InvalidClaimCodeError if the target printer's
status is already CLAIMED.
Claiming an unclaimed printer with a valid, unused code still succeeds
(do not regress).
Impact: Critical -- defense-in-depth gap enabling printer takeover.

