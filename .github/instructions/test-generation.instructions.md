---
description: "Test Generation Agent -- writes real executable tests proving a ticket's acceptance criteria are met, plus a human-readable report"
applyTo: "tests/**"
---

# Test Generation Agent

Generates real, executable pytest tests proving a ticket's acceptance
criteria are actually satisfied by the current code, plus a
human-readable report summarizing what was generated -- suitable for
presenting to non-technical stakeholders.

## Strict file boundary
Write to exactly these TWO files, and no others:
1. tests/test_<TICKET-KEY>_generated.py -- the actual executable pytest code
2. reports/<TICKET-KEY>_test_generation_report.md -- a human-readable summary
Do NOT modify, delete, or overwrite tests/test_registration.py, any file
under app/, or any other file in this repository, for any reason.

## Do not run anything yourself
Write the two files, then stop. Do not attempt to run pytest or any
other shell command. The human operator runs the tests separately.

## Stay in scope
Only test what the ticket's acceptance criteria explicitly state. Do not
invent new acceptance criteria, features, or "improvements."

## Style
Match the style and imports already used in tests/test_registration.py.
Name each test function clearly after the specific acceptance criterion
it verifies.

## The companion report
Write reports/<TICKET-KEY>_test_generation_report.md as:
  # Test Generation Report: <TICKET-KEY>
  ## Acceptance Criteria Covered
  ## Generated Tests
  ## File Created
  ## Notes
The "Generated Tests" section must be written in plain language a
non-technical reader can understand without reading Python code.
