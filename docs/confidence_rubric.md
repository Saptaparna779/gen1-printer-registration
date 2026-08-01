# Fix Validation Confidence Rubric

Used to score how well a code change addresses a Jira ticket's acceptance
criteria and underlying business rule — not just whether tests pass.

| Score Range | Meaning |
|---|---|
| 90-100 | Diff addresses the root cause, satisfies all acceptance criteria, no regression risk detected |
| 70-89 | Satisfies acceptance criteria but the fix looks narrow/symptom-level, or there's a minor untested edge case |
| 40-69 | Partially addresses the criteria; at least one acceptance criterion is likely unmet |
| 0-39 | Diff doesn't appear to address the ticket, or introduces a likely regression |

## What "root cause vs symptom" means here
A symptom-level fix makes the *specific reported scenario* pass without
fixing the general rule. Example: hardcoding a special case for one serial
number, instead of fixing the underlying logic for all re-registrations.