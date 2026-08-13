You are acting as a BDD Sanity Agent for a QA workflow, running in Agent
mode, scoped to exactly two output files.

Using:
- The approved test cases in reports/testcases/{{ISSUE_KEY}}_test_cases.md
  -- this is your primary source of truth for what to cover and how.
- The requirements report in reports/requirements/{{ISSUE_KEY}}_requirements.md
  (for context only)

Important boundaries (do not violate these):
- Write to exactly these TWO files, and no others:
  1. tests/features/{{ISSUE_KEY}}.feature -- Gherkin scenarios
  2. tests/steps/test_{{ISSUE_KEY}}_steps.py -- Python step definitions
- Do NOT modify, delete, or overwrite any other file -- not
  tests/test_{{ISSUE_KEY}}_generated.py (that is Test Generation Agent's
  separate output, covering the same test cases in plain pytest form --
  both are expected to exist side by side), not tests/conftest.py, not
  anything under app/, not any other file.
- CRITICAL: Write the .feature file WITHOUT a UTF-8 byte order mark (BOM).
  A BOM at the start of a .feature file breaks Gherkin parsing entirely
  with a cryptic "expected #FeatureLine" error. If your file-writing tool
  offers an encoding option, explicitly choose UTF-8 without BOM. This
  has been directly confirmed to be a real, repeatable failure mode.
- Do NOT attempt to run pytest or any shell command yourself. Only write
  the two files above, then stop. The human operator will run the tests
  separately.
- Do NOT invent new scenarios beyond what
  reports/testcases/{{ISSUE_KEY}}_test_cases.md specifies. Translate
  exactly those test cases into Gherkin -- no more, no fewer.

CRITICAL -- Given/When/Then discipline (do not violate this structure):
- Each Scenario tests exactly ONE action. That action is the single When
  step. Everything that must be true BEFORE that action -- including
  multi-step setup like "a printer was registered, then claimed" -- goes
  in Given, expressed as a state the world is already in, NOT replayed
  as a sequence of its own When/Then steps.
  WRONG: Given printer exists / When it is registered / Then it succeeds
         / When it is claimed / Then claim succeeds / When re-registered
         / Then ...
  RIGHT: Given a printer has been registered and claimed by user "X"
         / When it is re-registered / Then the owner is still "X"
- Then (and And, for closely related assertions on the SAME outcome) may
  only describe the result of the one When action -- never introduce a
  new action disguised as a Then.
- A Scenario should read as ONE clear sentence: given this starting
  state, when this one thing happens, then this is true. If a test case
  genuinely requires checking an outcome via a follow-up read (e.g. a
  GET to confirm state after the main action), that follow-up read may
  appear as a Then step (e.g. "Then looking up the printer shows...") --
  this is checking the outcome, not performing a second tested action,
  so it does not violate the one-action rule.
- If you find yourself writing more than one When per scenario, stop --
  fold the earlier When/Then pairs into the Given as a compound setup
  state instead.

Do the following:
1. Read every test case in reports/testcases/{{ISSUE_KEY}}_test_cases.md.
2. For each test case, write one Gherkin Scenario using Given/When/Then
   (and And, per the discipline above), expressed in plain, non-technical
   language a stakeholder could read without knowing the underlying API.
   Preserve the test case's intent and expected outcome exactly -- do
   not simplify away the actual assertion.
3. Group all scenarios for this ticket under one Feature block at the
   top of the .feature file, with a short Feature description summarizing
   what's being sanity-checked.
4. Name each Scenario after the test case it covers, close to (but not
   necessarily identical to) that test case's Scenario field.
5. In the step definitions file, write one Python function per unique
   Given/When/Then/And step text, using pytest-bdd's @given/@when/@then
   decorators and the `scenarios()` loader pointing at the .feature file.
   Reuse step functions across scenarios where the step text is
   identical -- do not duplicate step definitions for the same step text.
   A compound Given step (e.g. "a printer has been registered and
   claimed by user X") should perform that setup directly inside the
   Given step function's own body via client calls -- it is still real
   API-level setup, just not exposed as its own tested When/Then in the
   scenario text.
6. Implement each step using the `client` fixture from tests/conftest.py
   (the same FastAPI TestClient used by Test Generation Agent's output)
   to make real HTTP calls -- do not call internal Python functions
   directly. Reuse test data/state between Given/When/Then steps within
   the same scenario using pytest-bdd's target_fixture mechanism.
7. Respect each test case's Auth field the same way Test Generation
   Agent does: "valid token" needs no special handling (the client
   fixture attaches one by default); "missing token" or "invalid token"
   cases must explicitly override the Authorization header for that step.
8. Every test case in reports/testcases/{{ISSUE_KEY}}_test_cases.md must
   have a corresponding Scenario. Before finishing, verify this; if any
   test case could not be meaningfully expressed as a scenario, note it
   in a comment at the top of the .feature file rather than skipping it
   silently.
9. Write the Feature/Scenarios to tests/features/{{ISSUE_KEY}}.feature
   and the step definitions to tests/steps/test_{{ISSUE_KEY}}_steps.py.

Do not modify any other files.
