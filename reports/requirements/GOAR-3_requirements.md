# Requirements: GOAR-3

## Summary
Re-registering a printer (same serial number, e.g. after a factory reset) was returning the same `cloud_id` as before the reset, instead of a new one, which broke downstream billing/subscription systems that key off Cloud ID. The fix ensures `register_printer()` always generates a brand-new Cloud ID on every call to `/printers/register`, whether it is a first-time registration or a re-registration, per business rule 3/6. Printer Email ID and Claim Code regeneration behavior on re-registration is intended to be unaffected by this change.

## Systems/Endpoints Touched
- `app/registration.py` — `register_printer()`, specifically the "Step 1: Cloud identity" block where `printer.cloud_id = _generate_cloud_id()` is set. Reached via the `POST /printers/register` endpoint (per `app/main.py`).
- `app/registration.py` — `deregister_printer()` — diff shows only a trailing blank-line addition at end of file; no logic change.

## Business Rules Implicated
- Rule 3: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." — the core rule this ticket enforces.
- Rule 6: "Cloud ID: system-generated, unique, regenerated on every re-registration." — restates/reinforces rule 3 for the Cloud ID specifically.
- Rule 7: "Printer Email ID: must be globally unique; used for Email-to-Print." — relevant to AC2's claim that Printer Email ID regeneration is unaffected.
- Rule 8: "Claim Code: a **temporary** security token... Expired or invalid claim codes must be rejected. A claim code can only be used once." — relevant to AC2's claim that Claim Code regeneration is unaffected.
- Rule 11: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." — relevant because Claim Code regeneration touches the same re-registration path; see Open Questions.
- Rule 13: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." — extends rule 3 to the deregister-then-reregister case, which is in scope for this ticket's stated behavior even though not explicitly named in the AC.

## Original Acceptance Criteria
1. Every call to register a printer -- first-time or re-registration -- generates a brand new Cloud ID.
2. Printer Email ID and Claim Code continue to be regenerated on re-registration (unaffected, do not regress).

## Proposed Additions [PROPOSED -- NOT IN ORIGINAL TICKET]
3. Re-registering a printer that is currently `CLAIMED` still receives a new Cloud ID, and this must not change the printer's `CLAIMED` status or its `owner_user_id`. *Justification: rule 3 states Cloud ID regeneration applies to re-registration without carving out claimed printers; rule 11 requires that re-registration never silently overwrite or wipe out an existing owner's claim. This AC makes explicit that the two rules must hold simultaneously.*
4. Two consecutive re-registrations of the same serial number produce three distinct Cloud IDs overall (initial + two re-registrations), not merely a Cloud ID different from the immediately preceding one. *Justification: rule 6 requires the Cloud ID to be "unique," which is a stronger property than "different from the last value" — edge-case category: boundary value / repeated-operation check.*
5. If a re-registration attempt fails before the Welcome Page prints and is rolled back (per rule 2), the Cloud ID generated during that failed attempt must not be retained or reused, and the next successful registration attempt for the same serial number must still generate a fresh Cloud ID. *Justification: rule 2 ("no partial data... may be retained") combined with rule 3 — edge-case category: error state / rollback interaction.*
6. Re-registration after a prior deregistration of the same serial number generates a new Cloud ID, distinct from any Cloud ID previously associated with that serial number. *Justification: rule 13 explicitly extends rule 3/6 to the post-deregistration case; the original AC only describes re-registration "without deregistering" (per the ticket's Steps to Reproduce), so this case is not explicitly covered by AC1/AC2.*

## Flagged Conflicts
None identified. AC1 and AC2 are consistent with rules 3, 6, 7, and 8 as literally stated. (A possible tension between AC2 and rule 11 is noted under Open Questions rather than here, since it is an ambiguity in scope/interpretation rather than a stated conflict.)

## Open Questions
1. The diff in `reports/GOAR-3_diff.txt` shows only a comment being added above the pre-existing line `printer.cloud_id = _generate_cloud_id()`; it does not show any removal of conditional reuse logic (e.g. an `if existing: printer.cloud_id = existing.cloud_id` branch being deleted). This is inconsistent with the ticket's posted Validation Report comment, which states "The diff removes the conditional reuse of `existing.cloud_id` and always calls `_generate_cloud_id()`." It is unclear whether `reports/GOAR-3_diff.txt` is the complete/authoritative diff for this fix, or whether the conditional-reuse removal happened in a separate, undiffed change. This should be confirmed before treating the diff as sufficient evidence that AC1 is met.
2. AC2 states Claim Code "continue[s] to be regenerated on re-registration" without qualification. Rule 11 requires that re-registration never silently overwrite or wipe out an existing owner's claim. If Claim Code regeneration were skipped specifically for already-`CLAIMED` printers (as a safeguard related to rule 11), would that be a regression against the literal wording of AC2, or is it the intended/correct behavior? This needs explicit clarification from the ticket owner, since the ticket text does not address the claimed-printer case.
3. Neither the ticket nor `docs/business_rules.md` states whether the *old* Cloud ID should become invalid or inert after re-registration (e.g., whether downstream systems doing a lookup by the old Cloud ID should get a "not found"/redirect, versus the old value simply no longer being returned by this service). The ticket's stated impact ("stale references in downstream billing/subscription systems") suggests this matters, but it is out of scope for what this service alone can verify or guarantee.
