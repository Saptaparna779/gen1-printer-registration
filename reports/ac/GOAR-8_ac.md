# AC Enhancement: GOAR-8
## Original Acceptance Criteria
1. claim_printer() raises InvalidClaimCodeError if the target printer's status is already CLAIMED.
2. Claiming an unclaimed printer with a valid, unused code still succeeds (do not regress).
## Proposed Additions [PROPOSED -- NOT IN ORIGINAL TICKET]
3. When a claim attempt targets a printer that is already CLAIMED, the existing owner claim must remain unchanged and the claim attempt must fail before any ownership state mutation occurs.
   - Justification: docs/business_rules.md Rule 11 requires registration/re-registration logic to never silently overwrite or wipe out an existing owner's claim on a printer. This is a permission/ownership check edge case.
4. A valid, unused claim code must be rejected for any printer whose status is already CLAIMED, because claim codes are temporary security tokens and must not enable takeover of an already-owned printer.
   - Justification: docs/business_rules.md Rule 8 defines claim codes as temporary security tokens that must reject invalid or expired claims. Treating a code as invalid for an already-claimed printer addresses this ownership edge case.
5. A claim attempt must be rejected the same way regardless of whether it comes from the original owner or a different user — being the already-claimed printer's own owner does not exempt a claim attempt from rejection.
   - Justification: consistent with docs/business_rules.md Rule 3, which establishes that re-claiming/re-registering never reuses an existing identity silently — the same no-special-treatment principle applies here.
## Flagged Conflicts
None identified.
