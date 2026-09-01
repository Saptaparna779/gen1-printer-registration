# GOAR-15: Re-registration allows arbitrary model/firmware overwrite with no spoofing protection

**Type:** Bug  
**Priority:** High  
**Status:** Ready for QA  

## Description
When re-registering an existing serial number, register_printer() updates
model_number and firmware_version on the existing record with no
validation that this looks like the same physical device. A completely
different model_number could silently overwrite the original identity
tied to that serial number, with no protection against serial-number
reuse or spoofing across different physical printers.
Acceptance Criteria:
At minimum, a re-registration that changes model_number from what was
previously recorded is flagged/logged as a notable event for review.
(Stretch) Re-registration with a materially different model family is
rejected or requires explicit confirmation.
Legitimate re-registrations with matching or compatible model/firmware
data continue to work as before.

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-15_diff.txt and jira_context/GOAR-15_live.md).
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-15_diff.txt and jira_context/GOAR-15_live.md).
