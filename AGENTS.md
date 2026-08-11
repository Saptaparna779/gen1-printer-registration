# GEN 1 Printer Onboarding & Registration -- Agentic QA Workflow

## What this is
A pilot agentic QA validation workflow for the GEN 1 (Stratus) Printer
Onboarding & Registration service. When a developer marks a Jira ticket
"Ready for QA", this repository's automation fetches the live ticket and
code diff, and six separate, human-triggered GitHub Copilot sessions --
each a distinct agent role -- work in sequence to extract and enhance
requirements, design and automate tests, validate the fix, and
independently audit that validation, producing a scored, actionable
report that gets posted back to Jira.

## There are six agent roles, not one
None of the six agents are code living in this repository. Each is a
separate GitHub Copilot chat session, tied to the user's own GitHub
account and IDE, grounded by its own prompt template and its own
`.github/instructions/*.instructions.md` scoping file. Cloning this repo
gives you the SCAFFOLDING around all six agents:
- What each one reads for context (business rules, rubrics, live ticket,
  diff, and each other's outputs)
- What instructions each one follows (its own `.instructions.md` file,
  auto-applied by Copilot Chat based on which folder it's about to write to)
- The automation that prepares inputs and publishes the final output

## The six agents, in pipeline order
| # | Agent | Mode | Reads | Writes |
|---|---|---|---|---|
| 1 | Requirements Agent | Agent (1 file) | ticket, diff, business rules | reports/requirements/<TICKET>_requirements.md |
| 2 | Scenario Coverage Agent | Agent (1 file) | requirements report | reports/scenarios/<TICKET>_scenarios.md |
| 3 | Test Case Design Agent | Agent (1 file) | requirements report, scenario coverage | reports/testcases/<TICKET>_test_cases.md |
| 4 | Test Generation Agent | Agent (2 files) | test case file, smoke test (read-only) | tests/test_<TICKET>_generated.py, reports/<TICKET>_test_generation_report.md |
| 5 | Fix Validation Agent | Ask (1 file) | requirements, scenarios, test cases, diff, rubric, real test results | reports/<TICKET>_validation_report.md |
| 6 | Validation Audit Agent | Ask (1 file) | Agent 5's report, all upstream raw evidence, audit rubric | reports/audit/<TICKET>_audit.md |

Note: Agent 1 (Requirements Agent) is a merge of two earlier separate
roles -- Context Intake and AC Enhancement -- consolidated into one
agent. Their retired templates and instructions files are kept for
reference under docs/_archive/.

Agents 1-4 run in Agent mode because they need to write files, each
tightly scoped to exactly its own output path via `applyTo` in its
instructions file. Agents 5 and 6 stay in Ask mode -- they only reason
and score, never needing write access beyond their own single report.
Agent 6 runs with a genuinely fresh context and a different rubric
(docs/validation_audit_rubric.md) than Agent 5's
(docs/confidence_rubric.md) -- it independently re-checks the raw
evidence itself, rather than grading Agent 5's summary of it.

## Human checkpoint policy
Pause and review after EVERY agent (not just at the end of the pipeline).
Chosen deliberately: every real issue caught during this workflow's build
-- a stretched business-rule citation, an unresolved same-owner-reclaim
ambiguity, an AC numbering collision, an unreadable test-results file --
was only caught because review happened immediately after the agent that
produced it, before anything downstream built on top of the bad input.
Skipping intermediate checkpoints trades speed for a real risk of
compounding errors across multiple agents before anyone notices.

## What's actually in this repo
| Path | Purpose |
|---|---|
| app/ | The demo GEN 1 printer registration service (target under test), includes a /health liveness endpoint |
| tests/ | Regression tests, generated per-ticket tests, tests/conftest.py (TestClient fixture) |
| tests/smoke_test_health.py | Standalone liveness check -- starts the app as a real subprocess and confirms it's reachable over a real network call to /health, independent of the functional test suite |
| jira_context/ | Live ticket data fetched per-run (generated, not committed as source) |
| reports/requirements/, reports/scenarios/, reports/testcases/, reports/audit/ | Per-agent output for Agents 1-3 and Agent 6 (generated) |
| reports/ | Diffs, generated tests' companion reports, test results, and the final validation report (generated) |
| docs/business_rules.md | Business rules every agent grounds itself in |
| docs/confidence_rubric.md | Scoring rubric used by Fix Validation Agent (Agent 5) |
| docs/validation_audit_rubric.md | Separate trustworthiness rubric used by Validation Audit Agent (Agent 6) |
| docs/requirements_agent_prompt_template.md | Canonical prompt for Agent 1 |
| docs/scenario_coverage_prompt_template.md | Canonical prompt for Agent 2 |
| docs/test_case_design_prompt_template.md | Canonical prompt for Agent 3 (outputs a structured field-by-field table per test case) |
| docs/test_generation_prompt_template.md | Canonical prompt for Agent 4 |
| docs/validation_prompt_template.md | Canonical prompt for Agent 5 |
| docs/validation_audit_prompt_template.md | Canonical prompt for Agent 6 |
| docs/_archive/ | Retired Context Intake and AC Enhancement templates/instructions, kept for reference |
| .github/instructions/*.instructions.md | One scoping file per agent (6 files), auto-loaded by Copilot Chat based on which folder it's about to write to |
| .github/workflows/qa-prep.yml | GitHub Action: fetches ticket, generates diff, prepares Agent 5's prompt (does not yet generate the other 5 agents' prompts -- currently done manually) |
| fetch_jira_ticket.py | Pulls a live Jira ticket into jira_context/ |
| post_jira_comment.py | Posts a report back onto a Jira ticket; converts markdown (headings, bullets, inline code) into real Jira formatting, not raw symbols |
| run_qa_check.py | Local one-command runner (fetch + diff + prompt, all in one) -- covers Agent 5's inputs only |

## Setup for a new environment / new person cloning this repo

### 1. Clone and install
git clone <this-repo-url>
cd gen1-printer-registration
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt

### 2. Get your own GitHub Copilot access
Not included in the clone -- tied to your own GitHub account. Requires at
least Copilot Free, signed into your own VS Code.

### 3. Set up your own Jira credentials
Create a local .env file (never committed -- see .gitignore):
JIRA_BASE_URL=<your Jira site URL>
JIRA_EMAIL=<your Jira account email>
JIRA_API_TOKEN=<your personal API token>

### 4. Set up GitHub Secrets (for the automated trigger path only)
On YOUR OWN fork/copy of this repo: Settings -> Secrets and variables ->
Actions -> add JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.

### 5. Rebuild the Jira Automation rule (for the automated trigger path only)
Lives inside Jira itself, not in git. Trigger on status change to "Ready
for QA", action "Send web request" to
https://api.github.com/repos/<owner>/<repo>/dispatches with a GitHub
Personal Access Token and body: {"event_type": "qa_ready",
"client_payload": {"issue_key": "{{issue.key}}"}}

## Running it manually today (all 6 agents require manual prompt generation)
For each agent, in order:
1. Regenerate that agent's prompt: substitute {{ISSUE_KEY}} in the
   relevant docs/*_prompt_template.md into a file under reports/
2. Open a brand-new Copilot chat (never reuse a thread across agents or
   tickets)
3. Set the mode correctly: Agent mode for Agents 1-4, Ask mode for
   Agents 5 and 6
4. Paste the prompt, send, wait for it to finish
5. If Ask mode (Agents 5, 6): manually create the output file and paste
   the chat's response in, since Ask mode cannot write files itself
6. Run `git status --ignored` to confirm nothing outside the agent's
   scoped output path was touched
7. Review the output against the source files before moving to the next agent
8. `git add -f` the output (reports/ is gitignored; force-add is required)

## Known limitations / lessons learned (read before demoing)
- Ask mode cannot write files at all -- confirmed directly during this
  build. It only prints its answer in chat; you must manually save it.
  This is why Agents 5 and 6's outputs require a manual save step.
- Agent mode CAN write files, which is why Agents 1-4 use it -- but this
  requires strict `applyTo` scoping in each instructions file, and a
  `git status --ignored` check after every run, since Agent mode has
  previously deleted a test file and invented unrequested code changes
  despite explicit instructions not to.
- Always start a brand-new Copilot chat per agent, per ticket. Reusing a
  chat thread can cause it to repeat stale conclusions instead of
  genuinely re-checking current file state.
- Do not let any agent run shell commands to "verify" things itself. A
  fresh terminal session may not have this project's virtual environment
  active, which can cause false negatives.
- reports/ is in .gitignore. Every manual `git add` on a generated file
  needs the `-f` flag, or it will silently fail to stage.
- PowerShell's `>` redirect defaults to UTF-16, which agents may report
  as "unreadable." Use `| Out-File -Encoding utf8` instead when saving
  command output that an agent will later read.
- Business rule citations can drift: an agent may cite a real rule but
  stretch its meaning to justify a conclusion the rule doesn't quite
  support. Spot-check citations against docs/business_rules.md directly
  rather than trusting them at face value.
- The Validation Audit Agent (Agent 6) only adds value if it genuinely
  re-derives its findings from raw evidence -- if it's ever fed only
  Agent 5's report without the underlying files, it becomes a rubber
  stamp rather than an independent check.
- Cross-check anything surprising before posting to Jira. Verify claims
  against git status/log/actual test execution before publishing a report.
