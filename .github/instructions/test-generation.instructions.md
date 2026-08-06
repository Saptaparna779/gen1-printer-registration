---
description: "Test Generation Agent -- automates approved manual test cases against real API endpoints, plus a human-readable report"
applyTo: "tests/**"
---
# Test Generation Agent
Automates the manual test cases in reports/testcases/<TICKET-KEY>_test_cases.md
into real, executable pytest tests against the deployed API surface, plus
a human-readable report summarizing what was generated -- suitable for
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
Only automate the test cases explicitly listed in
reports/testcases/<TICKET-KEY>_test_cases.md. Do not invent new test
cases, acceptance criteria, features, or "improvements." Every test case
in that file must have a corresponding test function -- if one can't be
automated, note why in the report rather than skipping it silently.
## Style
Test against real HTTP endpoints, not internal Python functions. Use the
`client` fixture from tests/conftest.py (a FastAPI TestClient) to make
calls, e.g. `client.post("/printers/claim", json={...})`. Handle any
setup a test case's Preconditions require using the same client calls,
not direct store/app function access. Name each test function clearly
after the specific test case ID it automates.
## The companion report
Write reports/<TICKET-KEY>_test_generation_report.md as:
  # Test Generation Report: <TICKET-KEY>
  ## Test Cases Covered
  ## Generated Tests
  ## File Created
  ## Notes
The "Generated Tests" section must be written in plain language a
non-technical reader can understand without reading Python code.
