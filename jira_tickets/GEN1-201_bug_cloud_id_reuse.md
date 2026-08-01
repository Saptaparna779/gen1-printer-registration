**Key:** GEN1-201
**Type:** Bug
**Priority:** High
**Component:** Printer Onboarding & Registration
**Status:** In Progress
**Reported By:** BAU Support (production incident)

## Summary
Re-registering a printer reuses the old Cloud ID instead of generating a new one

## Description
Per the GEN 1 business rules: *"Re-registration always generates a new
Cloud ID."* Support has observed printers that were factory-reset and
re-registered still reporting the **same** Cloud ID as before the reset,
which is causing stale references in downstream billing/subscription
systems that key off Cloud ID.

## Steps to Reproduce
1. Register a printer with serial `SN-1234` → note the returned `cloud_id`.
2. Without deregistering, call register again with the same serial
   `SN-1234` (simulating a factory reset + re-onboard).
3. **Actual:** the second response returns the identical `cloud_id` from
   step 1.
4. **Expected:** the second response returns a **new, different**
   `cloud_id`.

## Acceptance Criteria
- [ ] Every call to register a printer — whether first-time or a
      re-registration of an existing serial number — generates a brand
      new Cloud ID.
- [ ] Printer Email ID and Claim Code continue to be regenerated on
      re-registration (unaffected, do not regress).

## Impact
Medium-high — affects billing/subscription reconciliation and any system
that treats Cloud ID as a stable identity per onboarding event.
