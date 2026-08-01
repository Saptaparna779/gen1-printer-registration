# GEN 1 — Printer Onboarding & Registration (Demo Codebase)

A deliberately small, self-contained FastAPI service implementing the
**Printer Onboarding & Registration** flow from the GEN 1 Business &
Functional Understanding Document (Section 11.1–11.3), built to serve as
the "dummy environment" for prototyping an agentic Copilot QA workflow.

It contains **four intentional bugs** and **one intentionally unfinished
feature**, each tied to a corresponding Jira ticket in `jira_tickets/`, so
you can simulate: developer picks up ticket → fixes code → moves ticket to
"Ready for QA" → agentic workflow verifies the fix against the ticket's
acceptance criteria.

## Structure
```
gen1-printer-registration/
├── app/
│   ├── models.py          # Printer, PrinterCapabilities, ClaimCode
│   ├── store.py           # in-memory data store
│   ├── xmpp.py            # mock XMPP connectivity
│   ├── welcome_page.py    # mock Welcome Page print (the final checkpoint)
│   ├── registration.py    # core business logic (bugs live here)
│   └── main.py            # FastAPI endpoints
├── tests/
│   └── test_registration.py   # baseline happy-path tests ONLY
├── jira_tickets/           # sample tickets (stories, bugs, maintenance)
├── docs/business_rules.md  # extracted rules — feed this to the agent as context
├── internal/ANSWER_KEY.md  # facilitator-only: exact bug locations & fixes
└── requirements.txt
```

## Running It
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# Docs / try-it-out UI: http://localhost:8000/docs

# Run baseline tests
pytest tests/ -v
```

## The Tickets

| Key | Type | Summary |
|---|---|---|
| GEN1-101 | Story (Done) | Capture printer capabilities — reference, already correct |
| GEN1-102 | Story (In Progress) | Enforce claim code expiry — **not yet implemented** |
| GEN1-201 | Bug | Cloud ID not regenerated on re-registration |
| GEN1-202 | Bug | Rollback leaves orphaned capability record |
| GEN1-203 | Bug (Critical) | Re-registration silently un-claims an owned printer |
| GEN1-301 | Maintenance | No structured logging on registration failure |

Bug locations and one-line fixes are in `internal/ANSWER_KEY.md` — keep
that out of view during the actual demo; it's there so you can drive the
"developer fixes it" step confidently and know what the agent *should*
catch.

## Suggested Demo Flow
1. Show the codebase and the (deliberately thin) baseline test suite passing.
2. Pick a ticket, e.g. **GEN1-203**, status "In Progress."
3. Play "developer": apply the fix from the answer key.
4. Move the ticket to **"Ready for QA"** — this is your trigger.
5. Agentic workflow fires: pulls the ticket, reads `docs/business_rules.md`
   and the diff, generates/executes tests against the acceptance criteria,
   posts a pass/fail report.
6. For contrast, run the workflow *before* applying the fix once, to show
   it correctly fails and explains why.

---

## What You Still Need to Build the Actual Agentic Workflow

The codebase above is the *target system under test*. It is not yet the
workflow itself. Here's what's still missing, in the order I'd build them:

### 1. A real Git host (not just local files)
Copilot's agentic capabilities (Copilot coding agent, Copilot code review,
Copilot CLI/extensions) are built around GitHub. Push this repo to a
**GitHub repo** (private is fine for a demo) — that becomes the substrate
everything else hooks into.

### 2. A Jira instance (or a good mock of one)
You need something that can hold ticket state and status transitions.
Two options:
- **Real (free) Jira Cloud instance** — most realistic for a client demo;
  lets you actually drag a card to "Ready for QA."
- **Mocked Jira** — a small local API (or just these markdown files read
  by a script) if you don't want to stand up real Jira yet. Fine for a
  first pass, but won't demo the "trigger" as convincingly.

If using real Jira, you'll also want the **Jira REST API** or an MCP
Jira connector so the workflow can fetch ticket fields (summary,
description, acceptance criteria) programmatically rather than you
pasting them in by hand.

### 3. The trigger mechanism
"Once a developer completes... and marks it Ready for QA" needs an actual
event source. Realistic options, roughly in order of effort:
- **Jira Automation rule** → webhook → your workflow, on status transition
  to "Ready for QA." (Most faithful to your stated trigger.)
- **GitHub Action** on PR merge to a branch, where the PR description/
  branch name references the Jira key (e.g. `GEN1-203`). Simpler to demo
  since it stays inside GitHub, but conflates "PR merged" with "Ready for
  QA" — fine for a demo, worth noting the gap to the client.

### 4. The agent itself
This is the actual "test user stories and bug fixes" logic. It needs to:
- Fetch the ticket (summary, description, acceptance criteria/steps to
  reproduce).
- Fetch the relevant code diff or current state of the service.
- Read `docs/business_rules.md` (or equivalent) for grounded context.
- Generate test cases mapped to the acceptance criteria.
- Execute them against the running/deployed service.
- Report results back (PR comment, Jira comment, Slack, etc.)

For the demo, this can be:
- **GitHub Copilot coding agent** assigned the issue directly (if you
  mirror Jira tickets as GitHub Issues), or
- **Copilot Chat / Copilot CLI** driven by a script that pulls ticket
  text and code, or
- A **Claude-powered agent** (via API, using the ticket + business rules
  as context) if you want more control over the test-generation logic
  than Copilot's issue-to-PR flow currently gives you — worth prototyping
  both and comparing for the client.

### 5. A place for results to land
Decide where the "QA report" surfaces: a PR comment, a new Jira comment/
attachment, a Slack message, or a generated test report file. For a demo,
a simple markdown report attached to the PR or ticket is usually enough.

### 6. (Optional but strengthens the demo) CI to actually run the tests
Wire a GitHub Actions workflow (`pytest`) so generated tests aren't just
*proposed* by the agent but actually **executed**, with real pass/fail
output the client can see.

---

### My suggested next step
Stand up the repo on GitHub + a free Jira Cloud site, mirror these six
tickets there, and wire a single Jira Automation rule → GitHub webhook for
just **one** ticket (e.g. GEN1-203) end-to-end before generalizing. Prove
the full loop once, then template it across the rest.
