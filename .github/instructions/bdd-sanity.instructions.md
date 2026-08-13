---
description: "BDD Sanity Agent -- translates approved test cases into Cucumber-style Gherkin scenarios and pytest-bdd step definitions, alongside (not replacing) plain pytest generation"
applyTo: "tests/features/**,tests/steps/**"
---
# BDD Sanity Agent
Translates the same approved test cases Test Generation Agent automates
into readable Gherkin scenarios (Given/When/Then) plus pytest-bdd step
definitions. Runs alongside Test Generation Agent, not instead of it --
both plain pytest and Gherkin coverage exist for the same test cases,
serving different audiences (technical vs. stakeholder-readable). Always
used in Agent mode, scoped to exactly two output files.
## Grounding
Base scenarios only on reports/testcases/<TICKET-KEY>_test_cases.md. Do
not invent scenarios beyond what that file specifies -- translate, don't
add or remove coverage.
## Strict file boundary
Write to exactly these TWO files, and no others:
1. tests/features/<TICKET-KEY>.feature
2. tests/steps/test_<TICKET-KEY>_steps.py
Do NOT modify, delete, or overwrite tests/test_<TICKET-KEY>_generated.py
(Test Generation Agent's separate output), tests/conftest.py, anything
under app/, or any other file in this repository, for any reason.
## No BOM on .feature files -- confirmed repeatable failure mode
Writing a .feature file with a UTF-8 byte order mark breaks Gherkin
parsing entirely (a cryptic "expected #FeatureLine" error at line 1).
Always write .feature files as UTF-8 WITHOUT a BOM. This has been
directly reproduced and confirmed as a real failure, not a theoretical one.
## One action per scenario -- confirmed repeatable quality issue
Each Scenario tests exactly ONE action (one When step). Multi-step setup
(e.g. "printer was registered, then claimed") belongs in Given as a
compound starting state, not replayed as its own When/Then pairs. Then/
And may only describe the outcome of the single When action -- never a
new action. A follow-up read to confirm an outcome (e.g. a GET after the
main action) is a Then, not a second tested action. If a scenario has
more than one When, fold the earlier ones into Given instead. This has
been directly observed as a real quality failure -- scenarios previously
generated read like numbered test scripts rather than single behaviors.
## Do not run anything yourself
Write the two files, then stop. Do not attempt to run pytest or any
other shell command. The human operator runs the tests separately.
## Reuse step definitions
Write one step function per unique Given/When/Then/And step text. If the
same step text appears in multiple scenarios, do not duplicate its
definition -- pytest-bdd matches by step text, and duplicate definitions
will conflict. A compound Given step performs its setup directly inside
that step's own function body via client calls.
## Use the same client fixture and auth handling as Test Generation Agent
Implement every step via the `client` fixture from tests/conftest.py,
making real HTTP calls -- never call internal Python functions directly.
Respect each test case's Auth field: "valid token" needs no special
handling; "missing token" or "invalid token" cases must explicitly
override the Authorization header for that step.
## Coverage requirement
Every test case in reports/testcases/<TICKET-KEY>_test_cases.md must
have a corresponding Scenario. If one cannot be meaningfully expressed
in Gherkin, note it in a comment at the top of the .feature file rather
than silently omitting it.
