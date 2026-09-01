"""
QA workflow endpoints for the GEN 1 agentic testing pipeline.

Wraps the logic previously in trigger_aava_workflow.py so the browser console
can start a run without ever holding a credential. All tokens are read from
the server's environment and never returned to the client.

Endpoints
---------
POST /qa/trigger              start an AAVA run for a Jira ticket
GET  /qa/runs                 list runs started since the server booted
GET  /qa/status/{ticket_id}   per-stage progress for one run
GET  /qa/artifact/{ticket_id}/{key}   fetch one generated file's contents

Progress model
--------------
AAVA has no confirmed completion endpoint, so progress is inferred from the
files the agents commit back to GitHub. On trigger we snapshot each expected
file's current git SHA. A stage is only "done" once its SHA differs from that
snapshot, which means re-running the same ticket reports correctly instead of
showing stale artifacts from an earlier run as finished.
"""
import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional

import requests
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.auth import verify_token

load_dotenv()

router = APIRouter(prefix="/qa", tags=["qa"])

AAVA_BASE_URL = os.environ.get("AAVA_BASE_URL", "https://int-ai.aava.ai")
AAVA_PIPELINE_ID = os.environ.get("AAVA_PIPELINE_ID", "21464")
AAVA_USER_EMAIL = os.environ.get("AAVA_USER_EMAIL", "saptaparna700@gmail.com")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "Saptaparna779/gen1-printer-registration")
GITHUB_BRANCH = os.environ.get("GITHUB_BRANCH", "main")

GITHUB_API = "https://api.github.com"
HTTP_TIMEOUT = 30

# The four agent outputs, in pipeline order. Edit these paths if your
# pipeline's file naming changes -- the UI reads this list from the server.
STAGES: List[Dict[str, str]] = [
    {"key": "requirements", "label": "Requirements",
     "path": "reports/requirements/{t}_requirements.md"},
    {"key": "scenarios", "label": "Scenarios",
     "path": "reports/scenarios/{t}_scenarios.md"},
    {"key": "testcases", "label": "Test cases",
     "path": "reports/testcases/{t}_test_cases.md"},
    # The test-generation agent writes into a per-ticket subfolder,
    # e.g. tests/GOAR-5/test_GOAR-5_generated.py
    {"key": "tests", "label": "Generated tests",
     "path": "tests/{t}/test_{t}_generated.py"},
]

# Context the qa-prep workflow commits. Shown alongside the agent output but
# not counted as pipeline stages.
CONTEXT_FILES: List[Dict[str, str]] = [
    {"key": "jira", "label": "Jira ticket", "path": "jira_context/{t}_live.md"},
    {"key": "diff", "label": "Code diff", "path": "reports/{t}_diff.txt"},
]

ALL_FILES = STAGES + CONTEXT_FILES

# ticket_id -> run record. In-memory only; cleared on server restart, which is
# fine for a demo but means baselines are lost if you restart mid-run.
_runs: Dict[str, dict] = {}


def _require_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise HTTPException(
            status_code=500,
            detail=f"{name} is not set on the server. Add it to your .env file and restart uvicorn.",
        )
    return value


def _github_headers() -> dict:
    return {
        "Authorization": f"Bearer {_require_env('GH_PAT')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _github_file(path: str) -> Optional[dict]:
    """
    Return the GitHub contents payload for a path, or None if it does not
    exist yet. Raises HTTPException on auth/rate-limit failures so those are
    not silently reported to the UI as 'still waiting'.
    """
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"
    try:
        res = requests.get(
            url,
            headers=_github_headers(),
            params={"ref": GITHUB_BRANCH},
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach GitHub: {exc}") from exc

    if res.status_code == 404:
        return None
    if res.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub rejected the request "
                f"({res.status_code}). Check GH_PAT is valid, unexpired, and has repo read access."
            ),
        )
    if not res.ok:
        raise HTTPException(status_code=502, detail=f"GitHub returned {res.status_code} for {path}")

    payload = res.json()
    if isinstance(payload, list):
        # Path resolved to a directory, not a file.
        return None
    return payload


def _snapshot(ticket_id: str) -> Dict[str, Optional[str]]:
    """Record the current SHA of every expected file before a run starts."""
    baseline: Dict[str, Optional[str]] = {}
    for spec in ALL_FILES:
        info = _github_file(spec["path"].format(t=ticket_id))
        baseline[spec["key"]] = info.get("sha") if info else None
    return baseline


class TriggerRequest(BaseModel):
    ticket_id: str


@router.post("/trigger")
def trigger_run(req: TriggerRequest, user_id: str = Depends(verify_token)):
    """Snapshot the repo, then submit the ticket to the AAVA pipeline."""
    ticket_id = req.ticket_id.strip().upper()
    if not ticket_id:
        raise HTTPException(status_code=422, detail="A Jira ticket ID is required.")

    aava_token = _require_env("AAVA_API_TOKEN")
    github_pat = _require_env("GH_PAT")
    jira_pat = os.environ.get("JIRA_PAT") or _require_env("JIRA_API_TOKEN")

    baseline = _snapshot(ticket_id)

    execution_id = str(uuid.uuid4())
    user_inputs = json.dumps({
        "TicketID": ticket_id,
        "GitHubrepoURL": f"https://github.com/{GITHUB_REPO}",
        "GitHubPAT": github_pat,
        "JiraPAT": jira_pat,
    })
    files = {
        "pipelineId": (None, AAVA_PIPELINE_ID),
        "user": (None, AAVA_USER_EMAIL),
        "userInputs": (None, user_inputs),
        "priority": (None, "1"),
        "executionId": (None, execution_id),
    }

    try:
        res = requests.post(
            f"{AAVA_BASE_URL}/workflows/workflow-executions",
            headers={
                "Authorization": f"Bearer {aava_token}",
                "Accept": "application/json, text/plain, */*",
            },
            files=files,
            timeout=HTTP_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach AAVA: {exc}") from exc

    if res.status_code in (401, 403):
        raise HTTPException(
            status_code=502,
            detail=f"AAVA rejected the request ({res.status_code}). AAVA_API_TOKEN may have expired.",
        )
    if not res.ok:
        raise HTTPException(status_code=502, detail=f"AAVA returned {res.status_code}: {res.text[:300]}")

    data = res.json().get("data", {}) or {}
    run = {
        "ticket_id": ticket_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "started_by": user_id,
        "execution_id": execution_id,
        "workflow_execution_id": data.get("workflowExecutionId"),
        "job_id": data.get("jobId"),
        "baseline": baseline,
        "repo": GITHUB_REPO,
        "branch": GITHUB_BRANCH,
    }
    _runs[ticket_id] = run
    return _public_run(run)


def _public_run(run: dict) -> dict:
    """Strip internal fields before returning a run to the client."""
    return {k: v for k, v in run.items() if k != "baseline"}


@router.get("/runs")
def list_runs(user_id: str = Depends(verify_token)):
    runs = sorted(_runs.values(), key=lambda r: r["started_at"], reverse=True)
    return {"runs": [_public_run(r) for r in runs]}


@router.get("/status/{ticket_id}")
def run_status(ticket_id: str, user_id: str = Depends(verify_token)):
    """
    Per-file progress for a ticket. A file is 'done' when its SHA differs
    from the baseline captured at trigger time.
    """
    ticket_id = ticket_id.strip().upper()
    run = _runs.get(ticket_id)
    baseline = run["baseline"] if run else {}

    def describe(spec: Dict[str, str]) -> dict:
        path = spec["path"].format(t=ticket_id)
        info = _github_file(path)
        sha = info.get("sha") if info else None
        if sha is None:
            status = "waiting"
        elif run and sha == baseline.get(spec["key"]):
            status = "stale"      # exists, but unchanged since this run started
        else:
            status = "done"
        return {
            "key": spec["key"],
            "label": spec["label"],
            "path": path,
            "status": status,
            "size": info.get("size") if info else None,
            "html_url": info.get("html_url") if info else None,
        }

    stages = [describe(s) for s in STAGES]
    context = [describe(c) for c in CONTEXT_FILES]
    done = sum(1 for s in stages if s["status"] == "done")

    return {
        "ticket_id": ticket_id,
        "tracked": run is not None,
        "run": _public_run(run) if run else None,
        "stages": stages,
        "context": context,
        "completed": done,
        "total": len(stages),
        "finished": done == len(stages),
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/artifact/{ticket_id}/{key}")
def get_artifact(ticket_id: str, key: str, user_id: str = Depends(verify_token)):
    """Return the decoded text of one generated file."""
    ticket_id = ticket_id.strip().upper()
    spec = next((f for f in ALL_FILES if f["key"] == key), None)
    if spec is None:
        raise HTTPException(status_code=404, detail=f"Unknown artifact '{key}'.")

    path = spec["path"].format(t=ticket_id)
    info = _github_file(path)
    if info is None:
        raise HTTPException(status_code=404, detail=f"{path} has not been generated yet.")

    try:
        text = base64.b64decode(info.get("content", "")).decode("utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not decode {path}: {exc}") from exc

    return {
        "ticket_id": ticket_id,
        "key": key,
        "label": spec["label"],
        "path": path,
        "html_url": info.get("html_url"),
        "size": info.get("size"),
        "content": text,
    }


@router.get("/config")
def qa_config(user_id: str = Depends(verify_token)):
    """What the UI needs to render the pipeline without hardcoding paths."""
    return {
        "repo": GITHUB_REPO,
        "branch": GITHUB_BRANCH,
        "pipeline_id": AAVA_PIPELINE_ID,
        "stages": [{"key": s["key"], "label": s["label"]} for s in STAGES],
        "context": [{"key": c["key"], "label": c["label"]} for c in CONTEXT_FILES],
        # Presence only -- the values themselves never leave the server.
        "credentials": {
            "AAVA_API_TOKEN": bool(os.environ.get("AAVA_API_TOKEN")),
            "GH_PAT": bool(os.environ.get("GH_PAT")),
            "JIRA_API_TOKEN": bool(
                os.environ.get("JIRA_API_TOKEN") or os.environ.get("JIRA_PAT")
            ),
        },
    }