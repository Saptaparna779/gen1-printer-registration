**Key:** GAOR-1
**Type:** Story
**Priority:** Medium
**Component:** Printer Onboarding & Registration
**Status:** Done
**Sprint:** GEN1 Sprint 14

## Summary
Capture printer capabilities during registration

## Description
As a downstream service (Application-Based Printing, Email-to-Print), I want
printer capabilities (color support, scan support, max DPI) captured once
during registration, so that I don't need to re-query the physical device
every time a job is submitted.

## Acceptance Criteria
- [ ] On successful registration, a capability record is created for the
      printer.
- [ ] Capability detection is based on model number (e.g. models prefixed
      `HP-C` support color; models containing `MFP` support scan).
- [ ] The capability record is retrievable independently of the printer
      record.
- [ ] If registration fails and rolls back, the capability record must
      **not** persist.

## Notes
Included here as a *reference / already-implemented* story — useful for
demoing that the agentic workflow doesn't need to generate tests for every
ticket blindly, only for what's actually changed or unverified.
