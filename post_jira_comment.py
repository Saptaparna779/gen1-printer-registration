"""
Post a comment onto a Jira ticket.
Usage:
    python post_jira_comment.py GOR-3 path/to/report.md
"""
import os
import re
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

JIRA_BASE_URL = os.environ["JIRA_BASE_URL"].rstrip("/")
JIRA_EMAIL = os.environ["JIRA_EMAIL"]
JIRA_API_TOKEN = os.environ["JIRA_API_TOKEN"]


def _inline_text_nodes(line: str) -> list:
    """Turn `code` spans into ADF code-formatted text nodes; everything else
    stays as plain text. Keeps this simple -- no bold/italic handling needed
    yet since the reports don't currently use them."""
    nodes = []
    parts = re.split(r"(`[^`]+`)", line)
    for part in parts:
        if part == "":
            continue
        if part.startswith("`") and part.endswith("`") and len(part) > 1:
            nodes.append(
                {
                    "type": "text",
                    "text": part[1:-1],
                    "marks": [{"type": "code"}],
                }
            )
        else:
            nodes.append({"type": "text", "text": part})
    return nodes or [{"type": "text", "text": line}]


def text_to_adf(text: str) -> dict:
    """Convert markdown-ish report text into Atlassian Document Format.
    Supports: #/##/### headings, "- " bullet lists, and plain paragraphs.
    Inline `code` spans are converted to ADF code marks."""
    content = []
    bullet_items = []

    def flush_bullets():
        nonlocal bullet_items
        if bullet_items:
            content.append(
                {
                    "type": "bulletList",
                    "content": [
                        {
                            "type": "listItem",
                            "content": [
                                {
                                    "type": "paragraph",
                                    "content": _inline_text_nodes(item),
                                }
                            ],
                        }
                        for item in bullet_items
                    ],
                }
            )
            bullet_items = []

    for raw_line in text.split("\n"):
        line = raw_line.strip()
        if line == "":
            continue

        heading_match = re.match(r"^(#{1,3})\s+(.*)", line)
        bullet_match = re.match(r"^-\s+(.*)", line)

        if heading_match:
            flush_bullets()
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2)
            content.append(
                {
                    "type": "heading",
                    "attrs": {"level": level},
                    "content": _inline_text_nodes(heading_text),
                }
            )
        elif bullet_match:
            bullet_items.append(bullet_match.group(1))
        else:
            flush_bullets()
            content.append({"type": "paragraph", "content": _inline_text_nodes(line)})

    flush_bullets()

    if not content:
        content = [{"type": "paragraph", "content": [{"type": "text", "text": text}]}]

    return {"type": "doc", "version": 1, "content": content}


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
