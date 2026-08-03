# GEN 1 Printer Onboarding & Registration -- Agentic QA Validation Workflow

## Purpose
Reduce manual QA effort and improve consistency of bug-fix and user-story
validation by having an AI agent (GitHub Copilot) automatically read a
Jira ticket's acceptance criteria, evaluate the corresponding code
change against them, and report a structured, confidence-scored
assessment back onto the ticket.

## Architecture at a glance

Developer fixes bug -> PR -> merge -> Jira: In Progress -> Ready for QA
        |
        | (AUTOMATIC -- Jira Automation rule)
        v
GitHub webhook fires (repository_dispatch: qa_ready)
        |
        | (AUTOMATIC -- GitHub Action: .github/workflows/qa-prep.yml)
        v
Fetch live ticket (Jira REST API) -> find real fix commit (by ticket key
in commit message) -> generate code diff -> generate Copilot prompt from
template -> commit results -> notify Jira "ready for review"
        |
        | (HUMAN -- deliberate checkpoint)
        v
QA opens VS Code, new Copilot chat, ASK mode, pastes generated prompt
        |
        | (AGENTIC -- the one real reasoning step)
        v
Copilot reads ticket + diff + business rules + rubric -> checks every
acceptance criterion -> assesses root cause vs. symptom -> flags
regression risk -> scores 0-100 -> lists concrete gaps to reach 100
        |
        | (HUMAN -- review before publishing)
        v
QA verifies report against reality -> posts to Jira (REST API)
        |
        v
Permanent, auditable comment on the ticket

## Full step-by-step flow

### Part 1 -- Developer
1. Move ticket to "In Progress"
2. Create a branch, fix the bug, add a regression test
3. Run tests locally
4. Commit with a message containing the ticket key (e.g. "Fix GOAR-13: ...")
5. Push, open PR, merge into main
6. Move ticket to "Ready for QA"

### Part 2 -- Automatic prep (zero manual steps)
7. Jira Automation rule detects the status change, sends a webhook to
   GitHub (https://api.github.com/repos/<owner>/<repo>/dispatches)
8. GitHub Action wakes up and:
   - Fetches the live ticket via Jira's REST API (fetch_jira_ticket.py)
   - Finds the real fix commit by searching main's commit history for
     the ticket key, excluding the automation's own bookkeeping commits
   - Generates the diff for that commit (app/ and tests/ only)
   - Generates the Copilot prompt from the canonical template
   - Commits all of this back to the repo
   - Posts a Jira comment saying prep is ready

### Part 3 -- Agentic validation (the one real agent)
9. QA pulls the latest changes
10. Starts a brand-new Copilot chat (never reuses an old thread -- reused
    threads can repeat stale conclusions instead of re-checking)
11. Sets mode to Ask, not Agent (Ask cannot edit files or run
    commands -- removes the risk of unauthorized action entirely)
12. Pastes the auto-generated prompt (or simply asks Copilot to validate
    the ticket -- .github/copilot-instructions.md auto-applies the
    same grounding rules and guardrails to every chat in this repo)
13. Copilot reads the ticket, diff, business rules, and rubric, and
    produces a structured report with a score and actionable gaps

### Part 4 -- Close the loop
14. QA reviews the report against reality (git status/log, actual test
    results) before trusting it
15. Runs post_jira_comment.py to publish it to the ticket via Jira's
    REST API
16. Result: a permanent, auditable comment on the ticket

## The one real agent
GitHub Copilot is the only agent in this workflow. Everything else --
the Jira Automation rule, the GitHub Action, fetch_jira_ticket.py,
post_jira_comment.py -- is deterministic automation with no judgment
involved. Copilot is the sole component that reads unstructured
information (ticket text, code, rules) and produces a genuine, reasoned
assessment rather than following a fixed script.

| Original 6-role design | What it actually is |
|---|---|
| Trigger Agent | Automation -- Jira Automation rule |
| Ticket Context Agent | Automation -- GitHub Action + Jira REST API |
| Requirements Enrichment Agent | Folded into the one real Copilot call |
| Fix Validation Agent | The real agent -- GitHub Copilot |
| Confidence Scoring Agent | Folded into the one real Copilot call |
| Reporting Agent | Automation -- Python script + Jira REST API |

## Guardrails against hallucination / misjudgment
Added after specific incidents caught during real testing, not
speculatively:
- Grounding: every validation points to real files (ticket, diff,
  business rules, rubric) instead of letting the model answer from
  memory or assumption.
- "Do not run shell commands yourself": added after Copilot once
  claimed a real dependency (pytest) was "missing" -- it had tried
  running a command in a terminal without the project's virtual
  environment active, and hallucinated the wrong conclusion.
- "Recognize legitimate test mocking": added after Copilot once
  flagged a deliberate monkeypatch test as "broken placeholder code."
- Ask mode instead of Agent mode: added after Agent mode, despite
  explicit instructions not to modify other files, deleted a test file
  and invented an unrequested "atomic email-claim API." Prompt wording
  is a suggestion; Ask mode removes the capability structurally.
- Fresh chat per ticket: added after a repeated prompt in an old
  chat thread returned an identical, stale score even after the
  underlying code had changed.
- Human review before posting: no guardrail set fully eliminates
  hallucination risk, so a person verifies the report against reality
  before it becomes a permanent Jira record.

## Proof points (from real testing on this repo)
- GOAR-7: scored 20/100 on genuinely broken code, 90/100 after a
  real fix -- same ticket, same prompt, correct opposite verdicts.
- GOAR-8: scored 30/100 broken, 100/100 fixed, correctly crediting
  the specific regression test added to close the gap.
- GOAR-9: uncovered a real bug in the automation itself (diff
  generation was grabbing the wrong commit due to a branch-name
  assumption, then a bot-commit collision) -- found and fixed live.
- GOAR-7 (autonomous test): given only a ticket key, no pre-selected
  files, Copilot searched the repository itself and correctly identified
  the relevant source files before validating.

## What's automatic vs. manual today
| Stage | Automatic | Manual |
|---|---|---|
| Trigger (status change -> webhook) | Yes | -- |
| Context gathering (fetch ticket, diff, prompt) | Yes | -- |
| Fix validation & scoring | -- | Yes (human opens Copilot, Ask mode) |
| Publishing the result | -- | Yes (one command, after human review) |

Closing the remaining manual gap would require either GitHub Copilot's
paid "coding agent" (works via GitHub Issues, different mechanics) or an
LLM API call inside the GitHub Action itself (small per-run cost,
removes the human-trigger step for the reasoning stage).

## File map
| File | Role in this workflow |
|---|---|
| .github/workflows/qa-prep.yml | Automation: trigger receiver, fetch, diff, prompt generation |
| .github/copilot-instructions.md | Auto-loaded grounding rules + guardrails for Copilot in this repo |
| docs/validation_prompt_template.md | Canonical prompt, single source of truth |
| docs/business_rules.md | Ground truth business rules the agent checks against |
| docs/confidence_rubric.md | Scoring rubric |
| fetch_jira_ticket.py | Pulls live ticket data via Jira REST API |
| post_jira_comment.py | Publishes the report via Jira REST API |
| run_qa_check.py | Local one-command manual runner |
| jira_context/, reports/ | Generated artifacts (not source, not committed manually) |