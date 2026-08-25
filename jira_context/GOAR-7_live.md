# GOAR-7: Re-registration regenerates claim code even for an already-claimed printer, enabling takeover

**Type:** Bug  
**Priority:** Highest  
**Status:** Ready for QA  

## Description
Business rule: "Registration/re-registration logic must never silently
overwrite or wipe out an existing owner's claim on a printer." Currently,
register_printer() unconditionally generates a new Claim Code on every
call, including re-registration of a printer that is already CLAIMED. A
new Welcome Page gets printed with a fresh claim code -- anyone who sees
that reprinted page (e.g. a technician during a firmware update visit)
could use it to claim a printer someone else already owns.
Steps to Reproduce:
Register and claim a printer with user_id="user-abc".
Trigger a re-registration for the same serial number (e.g. firmware
update handshake).
Actual: a brand new claim_code is generated and would be printed on a
new Welcome Page.
Expected: no new claim code should be issued for a printer that is
already CLAIMED.
Acceptance Criteria:
Re-registering an already-CLAIMED printer does not generate a new claim
code.
First-time registration and re-registration of an unclaimed printer
continue to generate a claim code as before (do not regress).
Impact: Critical -- direct security/ownership risk, printer hijack vector.

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-7_diff.txt and jira_context/GOAR-7_live.md).
- **Saptaparna Dasgupta:** ﻿# Validation Report: GOAR-7
## Files Investigated
- `jira_context/GOAR-7_live.md`: ticket summary, description, and acceptance criteria for GOAR-7.
- `docs/business_rules.md`: confirmed the claim-code and ownership preservation rules, especially "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim."
- `docs/confidence_rubric.md`: used the rubric to score the current implementation against acceptance criteria and root-cause coverage.
- `app/registration.py`: inspected `register_printer()` and `claim_printer()` logic for claimed vs unclaimed printer handling and claim-code issuance.
- `app/store.py`: confirmed how serial lookup and persistence behave during re-registration flows.
- `app/models.py`: verified `PrinterStatus` values and the semantics of `ClaimCode` and `Printer`.
- `tests/test_registration.py`: reviewed baseline coverage and found no existing regression test for the claimed-printer re-registration case.
## Acceptance Criteria Check
- Re-registering an already-CLAIMED printer does not generate a new claim code: met. `register_printer()` only generates a new claim code when `printer.status != PrinterStatus.CLAIMED`, preserving the existing claim code for already claimed devices.
- First-time registration and re-registration of an unclaimed printer continue to generate a claim code as before (do not regress): met. New printers and existing printers that are not CLAIMED both receive a new claim code under the current conditional logic.
## Root Cause Assessment
The current implementation addresses the root cause reported in GOAR-7: unconditional claim-code regeneration during re-registration. The fix is not a narrow symptom patch; it correctly preserves claim codes for already-CLAIMED printers while still generating codes for unclaimed registrations.
## Regression Risk
Low. The conditional generation is clearly scoped to `PrinterStatus.CLAIMED`, and unclaimed/new registration paths remain unchanged. One residual risk is if a claimed printer somehow lacks a valid `claim_code` object, but that is a separate data-integrity issue, not a ticket regression.
## Confidence Score
Score: 90/100
Justification: The code satisfies both acceptance criteria and is aligned with the business rule against overwriting an existing owner claim. The score is slightly reduced because an explicit regression test for this specific claimed-printer re-registration scenario is not present in the current test suite.
