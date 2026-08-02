# GOAR-9: Printer Email ID uniqueness is never verified

**Type:** Bug  
**Priority:** Medium  
**Status:** Ready for QA  

## Description
Business rule: "Printer Email ID: must be globally unique." The current
_generate_printer_email_id() function generates a random slug with no
check against existing records, so a collision (however rare) is
theoretically possible and completely unguarded against.
Acceptance Criteria:
Before assigning a new Printer Email ID, the system checks it does not
already exist on another printer record.
If a collision is found, a new ID is generated and re-checked until a
unique one is found.
Existing registration behavior is otherwise unaffected.
Impact: Medium -- collision could cause Email-to-Print jobs to be
misdelivered to the wrong printer.

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-9_diff.txt and jira_context/GOAR-9_live.md).
