# GEN 1 Printer Onboarding & Registration -- Repository Instructions

This repository contains an agentic QA workflow with two distinct agent
roles, each defined in its own path-specific instructions file under
.github/instructions/:

- fix-validation.instructions.md -- validates a code diff against a
  ticket's acceptance criteria (active when working with reports/).
- test-generation.instructions.md -- generates real, executable tests
  proving acceptance criteria are met (active when working with tests/).

See AGENTS.md and docs/AGENTIC_WORKFLOW.md for the full workflow and
architecture.
