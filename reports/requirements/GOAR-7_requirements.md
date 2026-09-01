# Requirements Report — GOAR-7

## 1. Summary

GOAR-7 addresses a security and ownership flaw in the printer re-registration flow: when a printer is already CLAIMED, re-registering it was regenerating a new claim code, which could enable a second user to hijack the printer using the fresh claim code printed on a new Welcome Page. The fix ensures that register_printer() preserves the existing claim code and does not issue a new one for already-CLAIMED printers, while keeping first-time registration and re-registration of unclaimed printers behaving as before. This matters because claim codes are an ownership bootstrap mechanism, and issuing new codes for already-claimed devices conflicts with the business rule that existing ownership must never be silently overwritten.

## 2. Affected Components

- app/registration.py — register_printer(). Reached via the printer registration endpoint (not explicitly named in the repo, but this function is the core registration entry point referenced by tests in tests/test_registration.py). The relevant logic is:
  - Cloud identity creation: `printer.cloud_id = _generate_cloud_id()`.
  - Printer email assignment: `printer.printer_email_id = _generate_printer_email_id()` plus `store.index_email(...)`.
  - Claim code generation now gated by printer status: `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()`.
  This implements the GOAR-7 behavior that already-CLAIMED printers do not receive a new claim code on re-registration.

- app/models.py — PrinterStatus, ClaimCode, Printer. These models define the CLAIMED status and the ClaimCode structure used by registration and claiming:
  - PrinterStatus.CLAIMED is the state that triggers suppression of new claim-code issuance in register_printer().
  - ClaimCode includes `code`, `created_at`, `expires_at`, and `used`, which underpin the "temporary" and "single-use" properties.

- app/store.py — used indirectly by register_printer() and claim_printer() but not modified for GOAR-7. It provides `get_printer_by_serial`, `save_printer`, and indices used in the registration flow.

- app/registration.py — claim_printer(). Reached via the printer claiming endpoint (again, not explicitly named, but used by tests). It enforces Claim Code validity and single-use constraints and is directly impacted by the decision to preserve claim codes for already-CLAIMED printers:
  - Rejects non-existent claim codes.
  - Rejects claims for already-CLAIMED printers.
  - Rejects expired claim codes.
  - Rejects claim codes marked `used`.

- tests/test_registration.py — baseline tests, including:
  - `test_claim_printer_rejects_already_claimed_printer()`, which simulates a second valid claim code on an already-CLAIMED printer and asserts that claim_printer() rejects the attempt with InvalidClaimCodeError. This test documents the expected behavior in the presence of multiple claim codes but predates GOAR-7’s specific fix; no test directly asserts the new "no new claim code on re-registration of CLAIMED printers" requirement.

Diff vs. implementation:
- reports/GOAR-7_diff.txt currently contains only: "No commit found on main mentioning GOAR-7 (excluding bot commits)", so it does not show any code changes.
- The actual implementation in app/registration.py clearly contains GOAR-7-related logic: the conditional `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()` directly enforces the ticket’s acceptance criteria.
- Therefore, there is a discrepancy: the diff file does not reflect the code changes that fulfill GOAR-7, but the source implementation does contain those changes.

## 3. Applicable Business Rules

- Rule 8 — Claim Code: "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."  
  This rule defines the security properties of claim codes and underpins GOAR-7’s concern that issuing additional claim codes for the same already-claimed printer can create ownership takeover vectors. The implementation’s preservation of the existing claim code for CLAIMED printers must still respect temporary and single-use constraints.

- Rule 11 — Claiming & Ownership: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."  
  This rule is directly cited in the Jira description and is the core business rule GOAR-7 enforces. Suppressing new claim-code generation for already-CLAIMED printers is how the registration logic avoids silently enabling a second owner to claim the printer, which would effectively overwrite the first owner’s claim.

- Rule 2 — Registration rollback: "If any step fails **before** the Welcome Page prints, the entire\n   registration must roll back — no partial data (printer record,\n   capability record, serial index, etc.) may be retained."  
  While not mentioned explicitly in the Jira description, this rule governs behavior when Welcome Page printing fails, including claim-code handling. For GOAR-7, it implies that claim codes generated during a failed registration or re-registration must not persist as usable takeover tokens.

## 4. Original Acceptance Criteria

Copied verbatim from jira_context/GOAR-7_live.md:

Re-registering an already-CLAIMED printer does not generate a new claim
code.
First-time registration and re-registration of an unclaimed printer
continue to generate a claim code as before (do not regress).

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. When re-registering an already-CLAIMED printer, the existing claim code must remain valid according to its original TTL and single-use constraints; re-registration must not silently extend the claim code’s expiration time or reset its `used` flag.  
   Justification: Rule 8 — "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once." This proposal ensures that suppressing new claim-code generation for CLAIMED printers does not inadvertently weaken the temporary/single-use properties of the existing claim code.

2. If re-registration of a printer (CLAIMED or unclaimed) fails before the Welcome Page prints and triggers rollback, any claim code generated during that attempt must not be usable afterwards; subsequent successful registration must generate and print a fresh claim code.  
   Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire\n   registration must roll back — no partial data (printer record,\n   capability record, serial index, etc.) may be retained." This proposal extends the rollback principle explicitly to claim codes, ensuring that failed re-registrations do not leave orphaned claim codes that could be misused.

3. For first-time registration and re-registration of an unclaimed printer, each registration attempt that successfully prints a Welcome Page must generate a new claim code that has never been issued before for that printer, even if a previous claim code exists but was never used.  
   Justification: Rule 8 — "A claim code can only be used once." Combined with the temporary nature of claim codes, this proposal clarifies that repeated successful registrations for unclaimed printers should not reuse old, potentially stale claim codes, avoiding ambiguity around multi-issue vs. reuse.

4. Attempting to claim a printer using a claim code that originated from a prior registration attempt which has been rolled back (e.g., due to Welcome Page failure) must be rejected as invalid.  
   Justification: Rule 2 — "no partial data (printer record, capability record, serial index, etc.) may be retained" — named edge case category: rollback/partial-failure behaviour. This proposal ensures that claim codes are treated as part of the registration data that must not survive a rollback.

5. Multiple concurrent claim codes for the same printer (e.g., caused by overlapping registration attempts) must not allow more than one successful claim: only the first successfully used claim code should result in the printer transitioning to CLAIMED, and subsequent uses of any claim code for that printer must be rejected.  
   Justification: Rule 8 — "A claim code can only be used once." — named edge case category: repeated operations. This proposal makes explicit how single-use semantics apply when multiple claim codes exist for the same printer.

## 6. Flagged Conflicts

None identified.

The original acceptance criteria (no new claim code for already-CLAIMED printers; unchanged claim-code behavior for first-time and unclaimed re-registrations) are consistent with Rule 8’s definition of claim-code behavior and Rule 11’s requirement to preserve existing ownership. Rule 2’s rollback requirements are not in direct conflict but do leave some behavior around claim-code invalidation during rollback unspecified (see Open Questions).

## 7. Open Questions

1. What should happen to the existing claim code and Welcome Page for a printer that is already CLAIMED when re-registration succeeds? Should a new Welcome Page be printed without a claim code, or should Welcome Page printing be suppressed entirely for CLAIMED printers?  
   Unresolvable because: jira_context/GOAR-7_live.md specifies that no new claim code should be issued for CLAIMED printers but does not state whether the Welcome Page should still print or what content it should contain; app/registration.py currently always calls generate_and_print_welcome_page with `claim_code=printer.claim_code.code`, which assumes a claim code is present. docs/business_rules.md defines claim codes as printed on the Welcome Page but does not distinguish CLAIMED vs unclaimed printers for that print behavior.  
   Downstream agents to exclude from scoring: Test generation and evaluation agents (Agents 3–6 in the pipeline) must not treat any assumption about Welcome Page content for CLAIMED printers as a scored requirement.

2. How should the system behave if a CLAIMED printer somehow has `printer.claim_code is None` during re-registration (data integrity issue)? Should re-registration generate a new claim code despite the CLAIMED status, or should it reject the re-registration or attempt to repair the missing claim code?  
   Unresolvable because: The ticket and business_rules.md do not define behavior for inconsistent states where a CLAIMED printer lacks a claim code. app/registration.py currently would raise an error when calling generate_and_print_welcome_page with `claim_code=printer.claim_code.code` if claim_code is None, but this is an implementation detail, not an explicitly defined requirement.  
   Downstream agents to exclude from scoring: Scenario design and test-case evaluation agents must treat this as out-of-scope and not score tests that assume a particular remediation behavior.

3. When re-registering an unclaimed printer that previously had a claim code which was never used, should that previous claim code be explicitly invalidated when a new claim code is issued, or can multiple unused claim codes exist concurrently for the same unclaimed printer?  
   Unresolvable because: Rule 8 states "A claim code can only be used once" but is silent on whether multiple unused codes can coexist and how they should be invalidated. jira_context/GOAR-7_live.md focuses on the CLAIMED case and does not address unused, prior claim codes for unclaimed printers. app/registration.py simply overwrites `printer.claim_code` with a new ClaimCode on re-registration for non-CLAIMED printers, without touching any historical codes.  
   Downstream agents to exclude from scoring: Agents responsible for edge-case test generation and scoring must not assume either "invalidate all old codes" or "allow multiple unused codes" as a requirement.

4. In rollback scenarios where Welcome Page printing fails for an unclaimed printer, should claim-code invalidation be observable in logs/telemetry (e.g., explicit events noting that a claim code was invalidated due to rollback)?  
   Unresolvable because: docs/business_rules.md rule 14 mentions observability for registration failures in general but does not specify claim-code-level logging, and jira_context/GOAR-7_live.md does not reference logging or telemetry at all. app/registration.py logs registration events but does not explicitly log claim-code invalidation or rollback of claim codes.  
   Downstream agents to exclude from scoring: Any agents scoring non-functional requirements (logging/telemetry coverage) must not assume specific claim-code logging behavior as required.

5. Given that reports/GOAR-7_diff.txt states "No commit found on main mentioning GOAR-7 (excluding bot commits)", should the GOAR-7 validation pipeline treat the existing implementation in app/registration.py as the authoritative fix, or must it block until a diff explicitly tagged with GOAR-7 is present?  
   Unresolvable because: The ticket comments and Validation Report in jira_context/GOAR-7_live.md assert that GOAR-7 is met and describe conditional claim-code generation behavior, but the diff file does not contain any code changes or commit references. The workflow rules provided do not state whether validation can rely solely on current main-branch behavior when the diff file is empty.  
   Downstream agents to exclude from scoring: Any agents that reason about change tracking or diff-based validation must not assume that the absence of a GOAR-7-tagged commit in reports/GOAR-7_diff.txt is either acceptable or unacceptable; they should treat this as an unresolved process question.
