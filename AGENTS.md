# GEN 1 Printer Onboarding & Registration -- Agentic QA Workflow

## What this is
A pilot agentic QA validation workflow for the GEN 1 (Stratus) Printer
Onboarding & Registration service. When a developer marks a Jira ticket
"Ready for QA", this repository's automation fetches the live ticket and
code diff, and a human-triggered GitHub Copilot session (the "agent")
validates the fix against the ticket's acceptance criteria, producing a
scored, actionable report that gets posted back to the Jira ticket.

## There is no single "agent" file
The agent itself is GitHub Copilot -- an external AI tool tied to each
user's own GitHub account and IDE, not code inside this repository.
Cloning this repo gives you the SCAFFOLDING around the agent:
- What it reads for context (business rules, rubric, live ticket, diff)
- What instructions it follows (.github/copilot-instructions.md,
  docs/validation_prompt_template.md)
- The automation that prepares its inputs and publishes its output

## What's actually in this repo
| Path | Purpose |
|---|---|
| app/ | The demo GEN 1 printer registration service (target under test) |
| tests/ | Regression tests |
| jira_tickets/ | Static reference copies of demo tickets |
| docs/business_rules.md | Business rules the agent validates against |
| docs/confidence_rubric.md | Scoring rubric |
| docs/validation_prompt_template.md | Canonical prompt (manual paste, portable to any Copilot mode/IDE) |
| .github/copilot-instructions.md | Repository custom instructions -- auto-loaded by Copilot Chat in this repo, no manual paste needed |
| .github/workflows/qa-prep.yml | GitHub Action: fetches ticket, generates diff, prepares prompt |
| fetch_jira_ticket.py | Pulls a live Jira ticket into jira_context/ |
| post_jira_comment.py | Posts a report back onto a Jira ticket |
| run_qa_check.py | Local one-command runner (fetch + diff + prompt, all in one) |

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

Cloud Jira: generate a token at
https://id.atlassian.com/manage-profile/security/api-tokens
Self-hosted (Data Center/Server) Jira: generate a Personal Access Token
from your account's profile settings (if enabled by your Jira admin);
note the API path differs (/rest/api/2/ instead of /rest/api/3/) and
fetch_jira_ticket.py / post_jira_comment.py would need small adjustments
for that API version and for ADF vs. plain-text description fields.

### 4. Set up GitHub Secrets (for the automated trigger path only)
On YOUR OWN fork/copy of this repo: Settings -> Secrets and variables ->
Actions -> add JIRA_BASE_URL, JIRA_EMAIL, JIRA_API_TOKEN.

### 5. Rebuild the Jira Automation rule (for the automated trigger path only)
This lives inside Jira itself, not in git, so it does not come with a
clone. Recreate a rule: trigger on ticket status change to "Ready for
QA", action "Send web request" to
https://api.github.com/repos/<owner>/<repo>/dispatches with a GitHub
Personal Access Token and a JSON body: {"event_type": "qa_ready",
"client_payload": {"issue_key": "{{issue.key}}"}}

## Running it manually (no automation needed)
python fetch_jira_ticket.py <TICKET-KEY>
git diff <commit>^ <commit> -- app/ tests/ > reports/<TICKET-KEY>_diff.txt

Then open a NEW Copilot Chat, set mode to Ask (not Agent -- see "Known
limitations" below), and either:
- paste the contents of docs/validation_prompt_template.md (replace
  {{ISSUE_KEY}} with the real ticket key), or
- simply ask Copilot to validate the ticket -- .github/copilot-
  instructions.md is automatically applied to every chat in this repo,
  so it already knows the grounding rules, guardrails, and report format.

## Known limitations / lessons learned (read before demoing)
- Use Ask mode, not Agent mode, for validation. Agent mode has full
  file-edit and command-execution ability; in testing it once deleted a
  test file and invented unrequested code changes despite explicit
  instructions not to. Ask mode can reason but cannot take action.
- Always start a brand-new Copilot chat per ticket. Reusing a chat
  thread can cause it to repeat stale conclusions instead of genuinely
  re-checking current file state.
- Do not let the agent run shell commands to "verify" things itself.
  A fresh terminal session may not have this project's virtual
  environment active, which can cause false negatives (e.g. reporting a
  real dependency as "missing").
- Cross-check anything surprising before posting to Jira. The agent
  can misjudge -- verify claims against git status / git log / actually
  running the tests yourself before publishing a report.
