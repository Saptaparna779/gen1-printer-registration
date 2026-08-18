"""
trigger_aava_pipeline.py

Called by qa-prep.yml after live.md and diff are committed
to the repository. Triggers all four AAVA agents in sequence,
waiting for each to complete before starting the next.

Usage:
    python trigger_aava_pipeline.py <TICKET_ID>

Environment variables required:
    AAVA_API_TOKEN   — AAVA Bearer token (from GitHub secret)
    GITHUB_PAT       — GitHub Personal Access Token
    JIRA_PAT         — Jira Personal Access Token

WARNING: AAVA_API_TOKEN expires on 2026-08-31.
Before that date, generate a new token from AAVA and
update the secret in GitHub repo Settings > Secrets > AAVA_API_TOKEN.
"""

import sys
import time
import json
import os
import requests

# ── Configuration ──────────────────────────────────────────────────────────────

AAVA_BASE_URL = "https://int-ai.aava.ai"
GITHUB_REPO   = "https://github.com/Saptaparna779/gen1-printer-registration"

AGENT_IDS = {
    "Requirements Agent":      54860,
    "Scenario Coverage Agent": 54894,
    "Test Case Design Agent":  54917,
    "Pytest Generator Agent":  54941,
}

POLL_INTERVAL_SECONDS = 15
POLL_TIMEOUT_SECONDS  = 900   # 15 minutes max per agent

# ── Helpers ────────────────────────────────────────────────────────────────────

def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/json, text/plain, */*",
    }


def submit_agent(
    agent_id:   int,
    ticket_id:  str,
    github_pat: str,
    jira_pat:   str,
    aava_token: str,
) -> str:
    """
    Submit one agent execution to AAVA.
    Returns the agentExecutionId to poll against.
    """
    url = f"{AAVA_BASE_URL}/agents/execute/agent-executions"

    user_inputs = json.dumps({
        "ticketId":      ticket_id,
        "githubRepoUrl": GITHUB_REPO,
        "githubPAT":     github_pat,
        "jiraPAT":       jira_pat,
    })

    # AAVA expects multipart/form-data
    files = {
        "agentId":    (None, str(agent_id)),
        "userInputs": (None, user_inputs),
    }

    response = requests.post(
        url,
        headers=get_headers(aava_token),
        files=files,
        timeout=30,
    )
    response.raise_for_status()

    data         = response.json()
    execution_id = data["data"]["agentExecutionId"]
    job_id       = data["data"]["jobId"]

    print(f"  Submitted → agentExecutionId: {execution_id}  jobId: {job_id}")
    return execution_id


def poll_until_complete(
    execution_id: str,
    agent_name:   str,
    aava_token:   str,
) -> dict:
    """
    Poll AAVA every POLL_INTERVAL_SECONDS until the execution
    reaches SUCCESS or FAILURE.
    """
    url = (
        f"{AAVA_BASE_URL}/agents/execute/history/execution"
        f"?execution_id={execution_id}"
    )

    elapsed = 0
    while elapsed < POLL_TIMEOUT_SECONDS:
        response = requests.get(
            url,
            headers=get_headers(aava_token),
            timeout=30,
        )
        response.raise_for_status()
        data   = response.json()
        status = data.get("status", "UNKNOWN")

        print(f"  [{agent_name}] status={status} ({elapsed}s elapsed)")

        if status == "SUCCESS":
            return data

        if status in ("FAILURE", "ERROR", "FAILED"):
            output = data.get("output", "no output returned")
            raise RuntimeError(
                f"\n❌ {agent_name} failed.\n"
                f"Status: {status}\n"
                f"Output: {output[:500]}"
            )

        time.sleep(POLL_INTERVAL_SECONDS)
        elapsed += POLL_INTERVAL_SECONDS

    raise TimeoutError(
        f"\n⏱ {agent_name} did not complete within "
        f"{POLL_TIMEOUT_SECONDS} seconds.\n"
        f"execution_id: {execution_id}"
    )


def run_agent(
    agent_name:  str,
    agent_id:    int,
    ticket_id:   str,
    github_pat:  str,
    jira_pat:    str,
    aava_token:  str,
) -> dict:
    """
    Submit and wait for a single agent.
    """
    print(f"\n{'─'*60}")
    print(f"▶  {agent_name}  (agent_id={agent_id})")
    print(f"{'─'*60}")

    execution_id = submit_agent(
        agent_id, ticket_id, github_pat, jira_pat, aava_token
    )
    result = poll_until_complete(execution_id, agent_name, aava_token)

    print(f"✅  {agent_name} complete.")
    return result


# ── Main pipeline ──────────────────────────────────────────────────────────────

def run_pipeline(ticket_id: str):
    """
    Run all four agents in sequence.
    """
    aava_token = os.environ.get("AAVA_API_TOKEN")
    github_pat = os.environ.get("GITHUB_PAT")
    jira_pat   = os.environ.get("JIRA_PAT")

    missing_secrets = []
    if not aava_token: missing_secrets.append("AAVA_API_TOKEN")
    if not github_pat: missing_secrets.append("GITHUB_PAT")
    if not jira_pat:   missing_secrets.append("JIRA_PAT")

    if missing_secrets:
        raise EnvironmentError(
            f"Missing required environment variables: "
            f"{', '.join(missing_secrets)}\n"
            f"Set these in GitHub repository secrets."
        )

    print(f"\n{'='*60}")
    print(f"  AAVA QA Pipeline")
    print(f"  Ticket:  {ticket_id}")
    print(f"  Repo:    {GITHUB_REPO}")
    print(f"{'='*60}")

    kwargs = dict(
        ticket_id=ticket_id,
        github_pat=github_pat,
        jira_pat=jira_pat,
        aava_token=aava_token,
    )

    run_agent("Requirements Agent",      54860, **kwargs)
    run_agent("Scenario Coverage Agent", 54894, **kwargs)
    run_agent("Test Case Design Agent",  54917, **kwargs)
    run_agent("Pytest Generator Agent",  54941, **kwargs)

    print(f"\n{'='*60}")
    print(f"  ✅  Pipeline complete for {ticket_id}")
    print(f"  Check your repo for generated files:")
    print(f"  • reports/requirements/{ticket_id}_requirements.md")
    print(f"  • reports/scenarios/{ticket_id}_scenarios.md")
    print(f"  • reports/testcases/{ticket_id}_test_cases.md")
    print(f"  • tests/test_{ticket_id}_generated.py")
    print(f"  • reports/{ticket_id}_test_generation_report.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trigger_aava_pipeline.py <TICKET_ID>")
        print("Example: python trigger_aava_pipeline.py GOAR-15")
        sys.exit(1)

    run_pipeline(ticket_id=sys.argv[1])