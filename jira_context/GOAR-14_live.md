# GOAR-14: Claim codes are not explicitly invalidated before printer deletion on deregistration

**Type:** Bug  
**Priority:** Low  
**Status:** Ready for QA  

## Description
deregister_printer() relies on deleting the entire printer record to
implicitly remove its claim code. If deletion partially fails or is
interrupted, a valid, unused claim code could theoretically remain
usable. This is a defense-in-depth gap rather than a currently
demonstrated exploit.
Acceptance Criteria:
Deregistration explicitly marks any outstanding claim code as
used/invalid before or as part of deleting the printer record.
Normal deregistration behavior is otherwise unchanged.

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-14_diff.txt and jira_context/GOAR-14_live.md).
