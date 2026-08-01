**Key:** GEN1-202
**Type:** Bug
**Priority:** High
**Component:** Printer Onboarding & Registration
**Status:** In Progress
**Reported By:** BAU Support (GDPR/data-cleanup audit)

## Summary
Failed registration (Welcome Page print failure) leaves an orphaned capability record

## Description
Business rule: *"Partial registration data must not be retained"* if
registration fails before the Welcome Page prints successfully. A recent
data audit found capability records in the store with no corresponding
printer record — these are orphans left behind by failed registrations.

## Steps to Reproduce
1. Call register with `simulate_welcome_page_failure=True`.
2. **Actual:** the printer record is removed (rollback partially works),
   but the capability record created in the capability-capture step is
   **not** removed.
3. **Expected:** rollback removes *all* partial state — printer record,
   capability record, and serial index — leaving nothing behind.

## Acceptance Criteria
- [ ] When Welcome Page printing fails, no printer record remains.
- [ ] When Welcome Page printing fails, no capability record remains for
      that printer_id.
- [ ] When Welcome Page printing fails, the serial number is free to be
      registered again from scratch (not blocked by a stale index entry).
- [ ] Successful registrations are unaffected (do not regress).

## Impact
High — orphaned records are a GDPR compliance concern (BUD Section 11.10)
and pollute downstream data.
