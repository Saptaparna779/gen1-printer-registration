"""
Fetch a live Jira ticket (summary, description, status, comments) and save
it as a local markdown file so Copilot Agent can read it as context.

Usage:
    python fetch_jira_ticket.py GOAR-3
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]


def adf_to_text(node) -> str:
    """Very small Atlassian Document Format -> plain text converter."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return "\n".join(adf_to_text(n) for n in node)
    if isinstance(node, dict):
        if node.get("type") == "text":
            return node.get("text", "")
        children = [adf_to_text(child) for child in node.get("content", []) or []]
        return "\n".join(c for c in children if c)
    return ""


def fetch_ticket(issue_key: str) -> dict:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}"
    params = {"fields": "summary,description,status,comment,issuetype,priority"}
    resp = requests.get(
        url,
        params=params,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json"},
    )
    resp.raise_for_status()
    return resp.json()


def main():
    if len(sys.argv) != 2:
        print("Usage: python fetch_jira_ticket.py <ISSUE-KEY>   e.g. GOR-3")
        sys.exit(1)

    issue_key = sys.argv[1].upper()
    data = fetch_ticket(issue_key)
    fields = data["fields"]

    summary = fields.get("summary", "")
    status = fields.get("status", {}).get("name", "")
    issue_type = fields.get("issuetype", {}).get("name", "")
    priority = (fields.get("priority") or {}).get("name", "")
    description = adf_to_text(fields.get("description"))

    comments = []
    comment_field = fields.get("comment", {}) or {}
    for c in comment_field.get("comments", []):
        author = c.get("author", {}).get("displayName", "Unknown")
        body = adf_to_text(c.get("body"))
        comments.append(f"- **{author}:** {body}")

    out_dir = "jira_context"
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{issue_key}_live.md")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# {issue_key}: {summary}\n\n")
        f.write(f"**Type:** {issue_type}  \n")
        f.write(f"**Priority:** {priority}  \n")
        f.write(f"**Status:** {status}  \n\n")
        f.write("## Description\n")
        f.write(description + "\n\n")
        if comments:
            f.write("## Comments\n")
            f.write("\n".join(comments) + "\n")

    print(f"Fetched {issue_key} -> {out_path}")


if __name__ == "__main__":
    main()