**Key:** GEN1-301
**Type:** Maintenance / Tech Debt
**Priority:** Medium
**Component:** Printer Onboarding & Registration
**Status:** In Progress
**Linked Risk:** BUD Section 10 — "Limited observability"

## Summary
Add structured logging/telemetry for registration failures

## Description
GEN 1 is called out in the BUD as having limited observability as a
platform-wide risk. Currently, when registration fails
(`RegistrationError`), the only trace is the exception message returned to
the caller — nothing is logged or emitted for BAU/Ops to monitor trends or
correlate with incident reports (see BUD Section 13 — Defect & Incident
Analysis).

This is a stability/maintenance improvement, not a new feature — it should
not change registration behaviour or API responses.

## Acceptance Criteria
- [ ] Every registration failure emits a structured log entry containing
      at minimum: `serial_number`, `model_number`, `failure_reason`,
      `timestamp`.
- [ ] Successful registrations are unaffected — no behavioural change,
      only added observability.
- [ ] Logging must not raise its own exceptions or block the rollback
      path (rollback must still complete even if logging fails).
- [ ] No sensitive data (e.g. full claim codes) is written to logs.

## Notes for QA
This ticket is a good candidate for testing that logging doesn't break the
existing rollback/error-handling behaviour verified under GEN1-202 —
regression, not new functional coverage.
