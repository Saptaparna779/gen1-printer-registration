This repository contains an agentic QA workflow with five distinct agent
roles, each defined in its own path-specific instructions file under
.github/instructions/, and each grounded by its own canonical prompt
template under docs/:

- requirements.instructions.md -- fetches a ticket, extracts its
  business requirement and acceptance criteria, and proposes
  enhancements against business rules when they're unclear or
  incomplete (active when working with reports/requirements/).
- test-case-design.instructions.md -- designs manual test cases against
  the real API surface from approved acceptance criteria (active when
  working with reports/testcases/).
- test-generation.instructions.md -- automates approved test cases into
  real, executable pytest tests against real API endpoints (active when
  working with tests/).
- fix-validation.instructions.md -- validates a code diff against a
  ticket's approved acceptance criteria and cross-checks test coverage
  (active when working with reports/).

Two earlier separate roles -- context intake and AC enhancement -- have
been merged into the single Requirements Agent above. Retired templates
and instructions files are kept for reference under docs/_archive/.

Agents run in sequence, each with a human review checkpoint after every
single agent before moving to the next -- see AGENTS.md's "Human
checkpoint policy" for why.

See AGENTS.md and docs/AGENTIC_WORKFLOW.md for the full workflow and
architecture.
