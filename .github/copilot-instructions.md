This repository contains an agentic QA workflow with five distinct agent
roles, each defined in its own path-specific instructions file under
.github/instructions/, and each grounded by its own canonical prompt
template under docs/:

- context-intake.instructions.md -- summarizes a ticket, diff, and
  business rules into a structured brief (active when working with
  reports/context/).
- ac-enhancement.instructions.md -- checks a ticket's acceptance criteria
  for completeness against business rules, proposing additions for human
  sign-off (active when working with reports/ac/).
- test-case-design.instructions.md -- designs manual test cases against
  the real API surface from approved acceptance criteria (active when
  working with reports/testcases/).
- test-generation.instructions.md -- automates approved test cases into
  real, executable pytest tests against real API endpoints (active when
  working with tests/).
- fix-validation.instructions.md -- validates a code diff against a
  ticket's approved acceptance criteria and cross-checks test coverage
  (active when working with reports/).

Agents run in sequence, each with a human review checkpoint after every
single agent before moving to the next -- see AGENTS.md's "Human
checkpoint policy" for why.

See AGENTS.md and docs/AGENTIC_WORKFLOW.md for the full workflow and
architecture.
