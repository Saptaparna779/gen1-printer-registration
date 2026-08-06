# AC Enhancement: GOAR-8
## Original Acceptance Criteria
1. claim_printer() raises InvalidClaimCodeError if the target printer's status is already CLAIMED.
2. Claiming an unclaimed printer with a valid, unused code still succeeds (do not regress).
## Proposed Additions [PROPOSED -- NOT IN ORIGINAL TICKET]
3. When a claim attempt targets a printer that is already CLAIMED, the existing owner claim must remain unchanged and the claim attempt must fail before any ownership state mutation occurs.
   - Justification: docs/business_rules.md Rule 11 requires registration/re-registration logic to never silently overwrite or wipe out an existing owner's claim on a printer. This is a permission/ownership check edge case.
4. A valid, unused claim code must be rejected for any printer whose status is already CLAIMED, because claim codes are temporary security tokens and must not enable takeover of an already-owned printer.
   - Justification: docs/business_rules.md Rule 8 defines claim codes as temporary security tokens that must reject invalid or expired claims. Treating a code as invalid for an already-claimed printer addresses this ownership edge case.
5. Clarify whether the rejection behavior applies to claims attempted by the same owner as well as different owners, since the ticket only specifies a different owner scenario.
   - Justification: edge-case category ambiguousinput / permission check. The ticket wording is ambiguous about same-owner re-claim behavior and should be resolved before implementation.
## Flagged Conflicts
None identified.
