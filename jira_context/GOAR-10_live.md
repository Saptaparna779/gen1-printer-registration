# GOAR-10: Capability capture overwrites existing data on every re-registration

**Type:** Bug  
**Priority:** Medium  
**Status:** Ready for QA  

## Description
Business rule states printer capabilities are "captured once at
registration time" so downstream services never need to re-query the
device. Currently, register_printer() recaptures and overwrites the
capability record on every single call, including re-registrations --
silently discarding any prior capability data with no audit trail.
Steps to Reproduce:
Register a printer, capture its capability record.
Re-register the same serial number.
Actual: a brand new capability record overwrites the original.
Expected: capabilities should only be captured once, unless there is
an explicit reason to refresh them.
Acceptance Criteria:
On first-time registration, capabilities are captured as before.
On re-registration of a printer that already has a capability record,
the existing record is not silently overwritten.
If capabilities genuinely need to change (e.g. hardware upgrade), that
should be an explicit, auditable action -- not a silent side effect of
re-registration.

