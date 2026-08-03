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

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-2_diff.txt and jira_context/GOAR-2_live.md).
- **Saptaparna Dasgupta:** # Validation Report: GOAR-2
## Acceptance Criteria Check
- Claim codes expire exactly 15 minutes after created_at: met in implementation via `CLAIM_CODE_TTL_MINUTES = 15` and `_generate_claim_code()` sets `expires_at = created_at + timedelta(minutes=15)`.
- Attempting to claim a printer with an expired claim code returns a clear error (HTTP 400) and does NOT change printer ownership or status: met by `claim_printer()` raising `InvalidClaimCodeError("Claim code has expired")` and `app/main.py` mapping that exception to HTTP 400; `test_claim_printer_rejects_expired_claim_code()` verifies the expired code is rejected and the printer is not set to `CLAIMED`.
- Attempting to claim with a valid, unexpired code still works as before: met by existing `test_claim_printer_success()` and no change to the successful claim path.
- Attempting to reuse an already-used claim code is still rejected: met by preserving the existing `target.claim_code.used` check in `claim_printer()` and keeping the prior rejection behavior.
## Root Cause Assessment
The root cause was that the claim flow stored `claim_code.expires_at` but never checked it during `claim_printer()`. The diff fixes that root cause by adding an expiry validation step before using the claim code.
## Regression Risk
Low. The change is localized to `app/registration.py` and adds a single expiry guard. One note is that expiry is checked before the "already used" check, so an expired-but-used code will now raise the expired error rather than the already-used error; this is a minor semantic difference rather than a functional regression.
## Confidence Score
Score: 90/100
Justification: The fix addresses the root cause and satisfies the acceptance criteria, but the validation suite lacks an explicit test for the exact 15-minute TTL and an end-to-end HTTP 400 regression check for expired claim codes.
## Path to 100/100
- Add a regression test that asserts `claim_code.expires_at == claim_code.created_at + timedelta(minutes=15)` immediately after registration.
- Add a FastAPI route-level regression test confirming POST `/printers/claim` returns HTTP 400 with an expired claim code.
- Optionally reorder the checks in `claim_printer()` so "already used" is evaluated before "expired" if precise error semantics for reused expired codes are desired.
