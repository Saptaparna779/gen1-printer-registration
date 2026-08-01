"""
Post a comment onto a Jira ticket.

Usage:
    python post_jira_comment.py GOR-3 path/to/report.md
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]


def text_to_adf(text: str) -> dict:
    """Wrap plain text lines into a minimal Atlassian Document Format body."""
    paragraphs = []
    for line in text.split("\n"):
        if line.strip() == "":
            continue
        paragraphs.append(
            {"type": "paragraph", "content": [{"type": "text", "text": line}]}
        )
    if not paragraphs:
        paragraphs = [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]
    return {"type": "doc", "version": 1, "content": paragraphs}


def post_comment(issue_key: str, text: str) -> None:
    url = f"{JIRA_BASE_URL}/rest/api/3/issue/{issue_key}/comment"
    payload = {"body": text_to_adf(text)}
    resp = requests.post(
        url,
        json=payload,
        auth=(JIRA_EMAIL, JIRA_API_TOKEN),
        headers={"Accept": "application/json", "Content-Type": "application/json"},
    )
    resp.raise_for_status()
    print(f"Comment posted to {issue_key}")


def main():
    if len(sys.argv) != 3:
        print("Usage: python post_jira_comment.py <ISSUE-KEY> <path-to-report-file>")
        sys.exit(1)

    issue_key = sys.argv[1].upper()
    report_path = sys.argv[2]

    with open(report_path, "r", encoding="utf-8") as f:
        text = f.read()

    post_comment(issue_key, text)


if __name__ == "__main__":
    main()