# Validation Report: GOAR-9
## Acceptance Criteria Check
- Before assigning a new Printer Email ID, the system checks it does not already exist on another printer record: met. `_generate_printer_email_id()` now calls `store.email_in_use(email)` and only returns a value that is not already indexed.
- If a collision is found, a new ID is generated and re-checked until a unique one is found: met. The function uses a `while True` retry loop and only returns after verifying uniqueness.
- Existing registration behavior is otherwise unaffected: partially met. Successful registration still proceeds normally, but the new implementation indexes email before final success and does not remove that index entry on rollback or deregistration, introducing potential state-management side effects.
## Root Cause Assessment
The ticket root cause is the unchecked random `Printer Email ID` generation in `_generate_printer_email_id()`. The diff addresses that directly by performing a uniqueness check against the email index and retrying on collisions. That is the correct root fix for the reported issue.

However, the fix does not fully handle the broader business rule context for registration state: if registration fails after the email is indexed, or if a printer is deregistered/re-registered, the stale `_email_index` mapping can remain and corrupt the uniqueness/in-use tracking.
## Regression Risk
- Stale `_email_index` entries may remain after a welcome page failure because rollback removes printer and serial index but not the email index.
- Deregistration also deletes the printer record without clearing the email index.
- Re-registration of an existing printer indexes a new email but does not remove the previous email mapping, leaving an outdated index entry.

These gaps could cause false collisions or incorrect email-to-printer lookup behavior later.
## Confidence Score
Score: 80/100
Justification: The diff satisfies the ticket acceptance criteria and fixes the root cause of unchecked email generation, but it leaves related email index cleanup unhandled and lacks explicit regression coverage for rollback/deregistration edge cases.
## Path to 100/100
- Add a store helper like `remove_email_index(email: str)` and ensure rollback clears the newly indexed email on failed registration.
- Ensure deregistration removes the printer's email index entry as part of cleanup.
- On re-registration, remove or update the old email index entry when a printer receives a new `printer_email_id`.
- Add regression tests for:
  - failed welcome page printing leaving no stale `_email_index` entry,
  - deregistration removing the email index,
  - re-registration not leaving an outdated old email mapping.
