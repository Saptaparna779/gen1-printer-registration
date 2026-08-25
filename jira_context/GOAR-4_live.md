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

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-4_diff.txt and jira_context/GOAR-4_live.md).
- **Saptaparna Dasgupta:** # Validation Report: GOAR-4
## Acceptance Criteria Check
- When Welcome Page printing fails, no printer record remains: met, because `_rollback_registration` already deletes the printer record for the failed registration.
- When Welcome Page printing fails, no capability record remains for that printer_id: met, because the diff adds `store.delete_capabilities(printer.printer_id)` to the rollback path.
- When Welcome Page printing fails, the serial number is free to be registered again from scratch: met, because `_rollback_registration` removes the serial index as part of rollback.
- Successful registrations are unaffected: met, since the change only modifies rollback cleanup and does not alter the normal registration path.
## Root Cause Assessment
The ticket and business rules point to incomplete rollback cleanup as the root cause. The diff fixes that root cause by ensuring rollback removes all partial state, including orphaned capability records, rather than only deleting the printer record and serial index.
## Regression Risk
Low. The change is isolated to the rollback path and only adds missing cleanup of capability records; it does not change successful registration behavior.
## Confidence Score
Score: 95/100
Justification: The fix directly closes the reported rollback gap and satisfies all acceptance criteria with minimal regression risk.
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-4_diff.txt and jira_context/GOAR-4_live.md).
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-4_diff.txt and jira_context/GOAR-4_live.md).
