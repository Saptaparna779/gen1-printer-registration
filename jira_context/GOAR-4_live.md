# GOAR-4: Failed registration leaves an orphaned capability record

**Type:** Bug  
**Priority:** High  
**Status:** Ready for QA  

## Description
Business rule: "Partial registration data must not be retained" if
registration fails before the Welcome Page prints successfully. A recent
data audit found capability records in the store with no corresponding
printer record -- these are orphans left behind by failed registrations.
Steps to Reproduce:
Call register with simulate_welcome_page_failure=True.
Actual: the printer record is removed (rollback partially works), but
the capability record created earlier is NOT removed.
Expected: rollback removes ALL partial state -- printer record,
capability record, and serial index -- leaving nothing behind.
Acceptance Criteria:
When Welcome Page printing fails, no printer record remains.
When Welcome Page printing fails, no capability record remains for that
printer_id.
When Welcome Page printing fails, the serial number is free to be
registered again from scratch.
Successful registrations are unaffected (do not regress).
Impact: High -- orphaned records are a GDPR compliance concern.

