"""
Prepare everything needed for a Copilot Agent validation run against a
Jira ticket: fetches the live ticket, generates the code diff, opens the
relevant files in VS Code, and pre-writes the exact prompt to paste into
Copilot Chat.

Usage:
    python run_qa_check.py GOAR-3 trailbranch
    python run_qa_check.py GOAR-3 trailbranch main   (explicit base branch)
"""
import os
import subprocess
import sys


def main():
    if len(sys.argv) < 3:
        print("Usage: python run_qa_check.py <ISSUE-KEY> <fix-branch> [base-branch]")
        sys.exit(1)

    issue_key = sys.argv[1].upper()
    fix_branch = sys.argv[2]
    base_branch = sys.argv[3] if len(sys.argv) > 3 else "main"

    print(f"[1/3] Fetching live ticket {issue_key} from Jira...")
    subprocess.run([sys.executable, "fetch_jira_ticket.py", issue_key], check=True)

    print(f"[2/3] Generating diff between {base_branch} and {fix_branch}...")
    os.makedirs("reports", exist_ok=True)
    diff_path = os.path.join("reports", f"{issue_key}_diff.txt")
    diff_result = subprocess.run(
        ["git", "diff", base_branch, fix_branch, "--", "app/"],
        capture_output=True,
        text=True,
        check=True,
    )
    with open(diff_path, "w", encoding="utf-8") as f:
        f.write(diff_result.stdout)

    if not diff_result.stdout.strip():
        print(
            f"WARNING: diff between {base_branch} and {fix_branch} is empty. "
            "Check your branch names."
        )
    else:
        print(f"      Diff saved to {diff_path}")

    ticket_path = os.path.join("jira_context", f"{issue_key}_live.md")
    business_rules_path = os.path.join("docs", "business_rules.md")
    rubric_path = os.path.join("docs", "confidence_rubric.md")
    report_path = os.path.join("reports", f"{issue_key}_validation_report.md")

    print("[3/3] Opening relevant files in VS Code...")
    for path in (ticket_path, diff_path, business_rules_path, rubric_path):
        try:
            subprocess.run(["code", path], check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(
                f"      Could not auto-open {path} (the 'code' command may not "
                "be on PATH) -- please open it manually in VS Code."
            )

    template_path = os.path.join("docs", "validation_prompt_template.md")
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    prompt = template.replace("{{ISSUE_KEY}}", issue_key)

    prompt_path = os.path.join("reports", f"{issue_key}_copilot_prompt.txt")
    with open(prompt_path, "w", encoding="utf-8") as f:
        f.write(prompt)

    print("\n" + "=" * 72)
    print("READY. Paste the prompt below into Copilot Chat (Agent mode).")
    print(f"(Also saved to {prompt_path} if you'd rather open and copy it there.)")
    print("=" * 72)
    print(prompt)
    print("=" * 72)
    print(f"\nAfter Copilot finishes, review {report_path}, then run:")
    print(f"  python post_jira_comment.py {issue_key} {report_path}")


if __name__ == "__main__":
    main()