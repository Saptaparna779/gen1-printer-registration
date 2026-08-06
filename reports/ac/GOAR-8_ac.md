# AC Enhancement: GOAR-8

## Original Acceptance Criteria
- claim_printer() raises InvalidClaimCodeError if the target printer's status is already CLAIMED.
- Claiming an unclaimed printer with a valid, unused code still succeeds (do not regress).

## Proposed Additions [PROPOSED -- NOT IN ORIGINAL TICKET]
The original criteria capture the core bug, but they do not explicitly state the ownership-preservation and observability expectations required by the business rules.

1. When a claim attempt targets a printer that is already claimed, the existing owner claim must remain unchanged and the claim attempt must fail without overwriting ownership.
   - Justification: This addresses business rule 11, which states that registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer. This is also a permission/ownership check edge case.

2. Rejected claim attempts for an already-claimed printer should be observable as a failed claim attempt rather than silently ignored.
   - Justification: This addresses business rule 14, which requires registration failures to be observable through structured logging/telemetry rather than silent. This is an error state edge case.

## Flagged Conflicts
- None identified.
