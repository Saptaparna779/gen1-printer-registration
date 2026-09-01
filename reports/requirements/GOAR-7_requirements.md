# Requirements Report — GOAR-7

## 1. Summary

This ticket addresses a security and ownership bug where re-registering an already-CLAIMED printer was generating a fresh claim code, enabling potential takeover of a printer that someone else already owns. The fix ensures that `register_printer()` does not issue a new claim code when the printer status is `CLAIMED`, while preserving claim-code generation for first-time and unclaimed re-registrations. This matters because business rule 11 forbids registration/re-registration logic from silently overwriting or wiping out an existing owner's claim on a printer.

## 2. Affected Components

- **app/registration.py — `register_printer()`**
  - Endpoint: implicitly reached via the service’s printer registration API (not explicitly named in code, but this is the core registration function).
  - Behavior: generates Cloud ID, Printer Email ID, and Claim Code; handles new registration and re-registration flows; sets status and triggers Welcome Page printing.
  - GOAR-7-relevant logic:
    - Claim code generation is now conditional:
      - `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()`
      - For already-CLAIMED printers, existing `claim_code` is preserved; no new claim code is created.
    - Welcome page printing still uses `printer.claim_code.code`, assuming a claim code exists.
- **app/registration.py — `_generate_claim_code()`**
  - Helper that creates `ClaimCode` instances with TTL based on `CLAIM_CODE_TTL_MINUTES`.
  - Used by `register_printer()` for claim-code issuance; its behavior is unchanged by GOAR-7 but remains central to claim-code semantics.
- **app/models.py — `Printer`, `ClaimCode`, `PrinterStatus`**
  - `PrinterStatus.CLAIMED` is the state used to gate claim-code regeneration.
  - `ClaimCode` structure (code, created_at, expires_at, used) defines what a valid claim code is.
- **app/store.py**
  - Underlying persistence for `Printer` and claim code, plus serial and email indexing.
  - No GOAR-7-specific changes visible, but its behavior is relied on by `register_printer()`.
- **tests/test_registration.py**
  - Contains a scenario that simulates a second claim code being issued for an already-claimed printer (via manual assignment) and asserts that `claim_printer()` rejects the second claim attempt:
    - `test_claim_printer_rejects_already_claimed_printer()` manually assigns a new claim code to a claimed printer, then expects `InvalidClaimCodeError` when trying to claim again.
  - As noted in the Jira Validation Report comment, there is currently no explicit regression test that covers the "re-registering an already-CLAIMED printer must not generate a new claim code" scenario.

**Diff vs implementation note:**
- `reports/GOAR-7_diff.txt` contains only: "No commit found on main mentioning GOAR-7 (excluding bot commits)", meaning there is no explicit GOAR-7-tagged diff. The implementation in `app/registration.py` clearly includes GOAR-7-relevant conditional logic around claim-code generation (the `printer.status != PrinterStatus.CLAIMED` check), but this is not reflected in a GOAR-7-labelled diff file. This discrepancy is noted in Open Questions for downstream agents.

## 3. Applicable Business Rules

1. **Rule 8 — Claim Code**  
   **Exact sentence:**
   > "Claim Code: a **temporary** security token printed on the Welcome Page."
   > "Expired or invalid claim codes must be rejected."
   > "A claim code can only be used once."
   **Relevance:**
   - GOAR-7’s focus on claim-code regeneration for already-CLAIMED printers directly involves the semantics of claim codes as temporary, single-use security tokens. The fix must preserve these properties and avoid issuing a second, conflicting token for the same claimed printer.

2. **Rule 11 — Claiming & Ownership**  
   **Exact sentence:**
   > "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   **Relevance:**
   - GOAR-7 explicitly cites this rule in the Jira description. Preventing new claim-code issuance for already-CLAIMED printers is a concrete enforcement of this rule, because a new claim code on a claimed printer could allow another user to hijack ownership.

3. **Rule 3 — Registration / Cloud ID**  
   **Exact sentence:**
   > "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   **Relevance:**
   - While GOAR-7 is primarily about claim codes, the registration function involved (which governs claim-code behavior) also governs Cloud ID behavior. The ticket’s fix must not violate this rule; claim-code suppression for claimed printers must coexist with continued Cloud ID regeneration on re-registration.

## 4. Original Acceptance Criteria

Verbatim from `jira_context/GOAR-7_live.md`:

1. "Re-registering an already-CLAIMED printer does not generate a new claim code."
2. "First-time registration and re-registration of an unclaimed printer continue to generate a claim code as before (do not regress)."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. **Claim-code presence requirement for claimed printers during re-registration**  
   **Requirement (testable behavior):**
   - When `register_printer()` is called for a printer whose `status` is `PrinterStatus.CLAIMED`, the function must not only avoid generating a new claim code, but it must also ensure that a valid, non-expired `claim_code` object is present on the printer before attempting to print the Welcome Page. If no valid claim code exists (e.g., `claim_code` is `None`, expired, or marked `used`), the registration should fail with a clear error rather than proceeding with an invalid or missing claim code.
   **Justification:**
   - Business Rule 8 — "Claim Code: a **temporary** security token printed on the Welcome Page" and "Expired or invalid claim codes must be rejected". Proceeding with re-registration and Welcome Page printing without a valid claim code would violate the requirement to reject expired/invalid claim codes and could confuse ownership semantics.

2. **Ownership preservation under Cloud ID regeneration**  
   **Requirement (testable behavior):**
   - When a claimed printer is re-registered and receives a new Cloud ID (per Rule 3), its `owner_user_id` must remain unchanged, and its `status` must remain `PrinterStatus.CLAIMED` throughout the operation. The re-registration must not revert the printer to `REGISTERED` status or clear `owner_user_id` as a side effect of Cloud ID regeneration.
   **Justification:**
   - Business Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Changing `owner_user_id` or downgrading status from `CLAIMED` to `REGISTERED` during re-registration would silently undermine existing ownership.

3. **Boundary behavior for repeated re-registration of claimed printers**  
   **Requirement (testable behavior):**
   - Multiple consecutive re-registration calls for the same already-CLAIMED serial number must not produce new claim codes on any of those calls, and the existing claim code (and ownership) must remain stable. Tests should cover at least two consecutive re-registrations of a claimed printer and assert that `printer.claim_code.code` remains unchanged.
   **Justification:**
   - Edge-case category: **repeated operations** and **boundary values**. The original AC addresses a single re-registration event but does not explicitly cover repeated re-registrations. Ensuring stability across repeated operations is important for robustness and for upholding Rule 11’s ownership guarantee.

4. **Rollback behavior when Welcome Page printing fails for a claimed printer**  
   **Requirement (testable behavior):**
   - If a re-registration attempt for an already-CLAIMED printer fails due to a `WelcomePagePrintError`, the rollback must not alter the printer’s existing ownership (`owner_user_id`) or its existing claim code. After rollback, the printer should still be in the `CLAIMED` status with the same `owner_user_id` and claim code as before the attempted re-registration.
   **Justification:**
   - Business Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."  
   - Business Rule 11 — ownership must not be wiped out. Rollback for claimed printers must be carefully defined to avoid erasing legitimate ownership while still removing any partial changes introduced by the failed re-registration.

5. **Logging/observability of suppressed claim-code regeneration**  
   **Requirement (testable behavior):**
   - When `register_printer()` is invoked for a printer with `PrinterStatus.CLAIMED` and therefore skips claim-code generation, the operation must log a structured event indicating that claim-code regeneration was suppressed due to the printer being claimed, including fields such as `serial_number`, `printer_id`, previous `claim_code`, and `owner_user_id`.
   **Justification:**
   - Business Rule 14 — "Registration failures should be observable (structured logging / telemetry), not silent". While suppression of claim-code regeneration is not a failure, it is a security-relevant behavior change associated with GOAR-7, and having it clearly observable aids in audit and incident analysis.

## 6. Flagged Conflicts

1. **Claim-code suppression vs. Welcome Page printing expectations**
   - The implementation of `register_printer()` calls `generate_and_print_welcome_page(..., claim_code=printer.claim_code.code, ...)` regardless of printer status. For already-CLAIMED printers, AC1 requires that no new claim code be generated, but the code still expects a claim code value when printing the Welcome Page. If a claimed printer has a `claim_code` that is expired or marked `used`, Rule 8 requires that such codes be rejected, which could conflict with the expectation that the Welcome Page still prints successfully on re-registration.
   - This potential conflict between AC1 and Rule 8 is noted as an Open Question because the ticket does not specify how re-registration should behave when a claimed printer’s existing claim code is no longer valid.

2. **Rollback semantics for claimed printers**
   - Rule 2 demands full rollback on failure before the Welcome Page prints, including deletion of the printer record. For claimed printers, deleting the printer record would effectively wipe out ownership, which Rule 11 forbids. The current implementation calls `_rollback_registration(printer)` on `WelcomePagePrintError`, which deletes the printer and removes serial and capabilities indices. The ticket does not clarify how to reconcile these rules for claimed printers, and the acceptance criteria focus only on claim-code generation. This is therefore a flagged conflict requiring human interpretation.

## 7. Open Questions

1. **Handling of expired/used claim codes on claimed printers during re-registration**  
   - **Question:** For an already-CLAIMED printer whose existing claim code is expired or marked `used`, what is the expected behavior when `register_printer()` is called? Should re-registration:
     - (a) proceed without a claim code and still print a Welcome Page,  
     - (b) fail and surface an error indicating invalid claim code state, or  
     - (c) regenerate a new claim code even though the printer is claimed?
   - **Why unresolvable from available inputs:**
     - The Jira ticket describes the bug and acceptance criteria in terms of preventing new claim-code issuance for claimed printers but does not address the state of existing claim codes (valid vs expired/used). Business Rule 8 requires rejection of expired/invalid claim codes, but does not prescribe behavior for claimed printers specifically.
   - **Downstream agents to exclude from scoring:**
     - Agents responsible for test generation, execution, and scoring (agents 3–6 in the pipeline) must not treat any particular answer to this question as required behavior.

2. **Exact behavior of rollback for claimed printers (ownership preservation vs data deletion)**  
   - **Question:** When re-registration of a claimed printer fails before the Welcome Page prints and rollback is triggered, should the system:
     - (a) delete the printer record and all related data as per Rule 2, or  
     - (b) preserve the printer record and ownership, treating rollback differently for claimed printers?
   - **Why unresolvable from available inputs:**
     - Rule 2 and Rule 11 can conflict for claimed printers; the current code deletes the printer record on rollback, but the Jira ticket for GOAR-7 does not discuss rollback behavior at all.
   - **Downstream agents to exclude from scoring:**
     - Scenario-design and scoring agents (agents 4–6) must not assume a specific rollback behavior for claimed printers without human clarification.

3. **Welcome Page content for claimed printers after re-registration**  
   - **Question:** For an already-CLAIMED printer where re-registration does not generate a new claim code, what should the Welcome Page show?
     - Should it still print the original claim code (even though it may have already been used), or should it omit claim-code content altogether for claimed printers?
   - **Why unresolvable from available inputs:**
     - The Jira ticket’s Expected behavior only states "no new claim code should be issued"; it is silent on whether the existing claim code is printed again or suppressed. Business Rule 8 defines claim codes as temporary, single-use tokens but does not address reprinting them after use.
   - **Downstream agents to exclude from scoring:**
     - Agents defining or scoring UI/content-level expectations (agents 4–6) must exclude this from scoring.

4. **Diff completeness and traceability for GOAR-7**  
   - **Question:** Since `reports/GOAR-7_diff.txt` says "No commit found on main mentioning GOAR-7 (excluding bot commits)", how should the pipeline treat changes to `app/registration.py` that implement the GOAR-7 fix but are not tagged with GOAR-7 in commit messages? Is there a canonical commit or tag that should be used instead for traceability?
   - **Why unresolvable from available inputs:**
     - The diff file provides no direct link between the GOAR-7 ticket and specific commits. The implementation clearly reflects GOAR-7 behavior (conditional claim-code generation), but there is no authoritative mapping provided.
   - **Downstream agents to exclude from scoring:**
     - Agents performing diff-based validation or traceability scoring (agents 2–3 and 6) must not penalize or reward behavior based on the missing GOAR-7-tagged diff.

5. **Need for dedicated regression tests for claimed-printer re-registration**  
   - **Question:** Should the pipeline treat the absence of a dedicated test (e.g., `test_reregistration_does_not_generate_new_claim_code_for_claimed_printer`) as a requirement for GOAR-7 completion, or is it acceptable for now to rely on manual validation and more generic claim-code tests?
   - **Why unresolvable from available inputs:**
     - The Jira Validation Report comment notes: "found no existing regression test for the claimed-printer re-registration case" but does not explicitly state that such a test is required to close the ticket.
   - **Downstream agents to exclude from scoring:**
     - Test-generation and coverage-scoring agents (agents 3–6) must not assume that this specific test must exist for GOAR-7 to be considered compliant.
