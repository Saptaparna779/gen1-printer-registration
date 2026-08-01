**Key:** GOAR-2
**Type:** Story
**Priority:** High
**Component:** Printer Onboarding & Registration
**Status:** In Progress
**Sprint:** GEN1 Sprint 21

## Summary
Enforce Claim Code expiry (15 minutes)

## Description
As HP, I want Claim Codes to expire 15 minutes after they are generated, so
that a leaked or stale claim code printed on an old Welcome Page cannot be
used indefinitely to claim a printer that isn't actually the claimant's.

Currently, `ClaimCode.expires_at` is calculated and stored at registration
time, but nothing in the claim flow actually checks it — an expired code is
still accepted.

## Acceptance Criteria
- [ ] Claim codes expire exactly 15 minutes after `created_at`.
- [ ] Attempting to claim a printer with an expired claim code returns a
      clear error (`InvalidClaimCodeError` / HTTP 400) and does **not**
      change printer ownership or status.
- [ ] Attempting to claim with a valid, unexpired code still works as
      before.
- [ ] Attempting to reuse an already-used claim code is still rejected
      (existing behaviour — do not regress).

## Steps to Reproduce (current bug behaviour)
1. Register a printer, capture the claim code and `claim_code_expires_at`.
2. Wait until (or simulate) `expires_at` has passed.
3. Call `POST /printers/claim` with that code.
4. **Actual:** claim succeeds.
5. **Expected:** claim is rejected with an "expired" error.

## Dev Notes
Ready for QA once `registration.claim_printer()` checks
`claim_code.expires_at` against current time.
