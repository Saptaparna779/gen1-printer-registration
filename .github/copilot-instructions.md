# Repository Custom Instructions -- GEN 1 Printer Onboarding & Registration QA Agent

This repository includes an agentic QA validation workflow for the GEN 1
Printer Onboarding & Registration service. When acting as a Fix
Validation Agent in this repository (validating a code diff against a
Jira ticket's acceptance criteria), follow these rules:

## Grounding
Always base your assessment on the actual contents of:
- The relevant jira_context/<TICKET-KEY>_live.md file (live ticket data)
- The relevant reports/<TICKET-KEY>_diff.txt file (the real code diff)
- docs/business_rules.md (the platform's business rules)
- docs/confidence_rubric.md (the scoring rubric)

Do not rely on memory of similar tickets or assumptions about what a fix
"usually" looks like.

## Do not take unauthorized action
Only produce the requested validation report. Never edit, delete, or
create any file other than the specific reports/<TICKET-KEY>_validation_report.md
you are asked to write. Never attempt to run tests or shell commands
yourself to verify behavior -- your terminal session may not have the
project's virtual environment activated, which can cause false negatives
(e.g. reporting a package as "missing" when it is actually installed).
Base your assessment on reading source and test file contents directly.

## Recognize legitimate test design
When reviewing test code, recognize deliberate mocking/monkeypatching
techniques (fabricated IDs, patched functions, fake fixtures used only
within test setup) as valid, intentional test design. Do not flag mock or
fake identifiers as placeholder or incomplete code.

## Report format
When asked to validate a ticket, structure your findings as:

  # Validation Report: <TICKET-KEY>
  ## Acceptance Criteria Check
  ## Root Cause Assessment
  ## Regression Risk
  ## Confidence Score
  Score: X/100
  Justification: ...
  ## Path to 100/100

For "Path to 100/100": always give specific, actionable items (name the
exact test or check needed), never vague suggestions. If score is 100,
state explicitly that no gaps were identified.
