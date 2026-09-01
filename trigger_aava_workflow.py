"""
trigger_aava_workflow.py

Triggers the full AAVA QA pipeline as a single saved workflow
(pipelineId 21464). Fires the trigger and exits immediately —
does not poll for completion (polling endpoint not yet confirmed).
Check your repo manually (git pull) to confirm the agents' output
files landed.

Usage:
    python trigger_aava_workflow.py <TICKET_ID>

Environment variables required:
    AAVA_API_TOKEN, GH_PAT, JIRA_PAT

WARNING: AAVA_API_TOKEN expires on 2026-08-31.
"""

import sys
import json
import os
import uuid
import requests
from dotenv import load_dotenv

load_dotenv()

AAVA_BASE_URL = "https://int-ai.aava.ai"
GITHUB_REPO   = "https://github.com/Saptaparna779/gen1-printer-registration"
PIPELINE_ID   = "21464"


def get_headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept":        "application/json, text/plain, */*",
    }


def submit_workflow(ticket_id, github_pat, jira_pat, aava_token, user_email):
    url = f"{AAVA_BASE_URL}/workflows/workflow-executions"
    execution_id = str(uuid.uuid4())

    user_inputs = json.dumps({
        "TicketID":      ticket_id,
        "GitHubrepoURL": GITHUB_REPO,
        "GitHubPAT":     github_pat,
        "JiraPAT":       jira_pat,
    })

    files = {
        "pipelineId":  (None, PIPELINE_ID),
        "user":        (None, user_email),
        "userInputs":  (None, user_inputs),
        "priority":    (None, "1"),
        "executionId": (None, execution_id),
    }

    response = requests.post(url, headers=get_headers(aava_token), files=files, timeout=30)
    response.raise_for_status()
    data = response.json()

    workflow_execution_id = data.get("data", {}).get("workflowExecutionId", "unknown")
    job_id = data.get("data", {}).get("jobId", "unknown")

    print(f"\n{'='*60}")
    print(f"  AAVA workflow triggered (pipeline {PIPELINE_ID})")
    print(f"  Ticket: {ticket_id}")
    print(f"  workflowExecutionId: {workflow_execution_id}")
    print(f"  jobId: {job_id}")
    print(f"{'='*60}")
    print(f"\n  This pipeline does NOT poll for completion yet.")
    print(f"  Check the repo manually in a few minutes for:")
    print(f"  • reports/requirements/{ticket_id}_requirements.md")
    print(f"  • reports/scenarios/{ticket_id}_scenarios.md")
    print(f"  • reports/testcases/{ticket_id}_test_cases.md")
    print(f"  • tests/test_{ticket_id}_generated.py")
    print(f"{'='*60}\n")

    return data


def run_pipeline(ticket_id: str):
    aava_token = os.environ.get("AAVA_API_TOKEN")
    github_pat = os.environ.get("GH_PAT")
    jira_pat   = os.environ.get("JIRA_PAT") or os.environ.get("JIRA_API_TOKEN")
    user_email = os.environ.get("AAVA_USER_EMAIL", "saptaparna700@gmail.com")

    missing = [n for n, v in [("AAVA_API_TOKEN", aava_token), ("GH_PAT", github_pat), ("JIRA_PAT", jira_pat)] if not v]
    if missing:
        raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    submit_workflow(ticket_id, github_pat, jira_pat, aava_token, user_email)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python trigger_aava_workflow.py <TICKET_ID>")
        sys.exit(1)
    run_pipeline(ticket_id=sys.argv[1])