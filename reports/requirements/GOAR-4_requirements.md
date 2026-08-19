# Requirements Report — GOAR-4

## 1. Summary

This ticket addresses a rollback defect in the printer registration flow when the Welcome/Info Page fails to print. According to the business rule that no partial registration data may be retained if registration fails before the Welcome Page prints, data audits found orphaned capability records in the store with no corresponding printer record. These orphans are left behind by failed registrations that currently remove the printer record (and serial index) but do not remove the associated capability record. The fix ensures that rollback removes all partial state for the failed registration — printer record, capability record, and serial index — so the serial number can be cleanly registered again and no orphaned capability records remain, which is important for GDPR compliance.

## 2. Affected Components

- app/registration.py
  - Function: `register_printer`
    - Uses `_rollback_registration(printer)` in the Welcome Page failure path via:
      - `generate_and_print_welcome_page(..., force_failure=simulate_welcome_page_failure, ...)` and the `except WelcomePagePrintError` block.
  - Function: `_rollback_registration`
    - Rollback helper invoked when Welcome Page printing fails.
    - Now deletes capabilities for the printer in addition to deleting the printer record and removing the serial index.

(Note: `reports/GOAR-4_diff.txt` is empty in the current repository snapshot; the effective implementation change appears directly in `app/registration.py` where `_rollback_registration` includes `store.delete_capabilities(printer.printer_id)`.)

## 3. Applicable Business Rules

### Rule 1 / 2 — Registration success condition & rollback completeness

- Exact sentences:
  - "1. Registration is successful **only if** the Welcome/Info Page prints."
  - "2. If any step fails **before** the Welcome Page prints, the entire
   registration must roll back — no partial data (printer record,
   capability record, serial index, etc.) may be retained."
- Relation to this ticket:
  - The ticket explicitly cites the business rule that partial registration data must not be retained on failure before the Welcome Page prints and describes capability records left without a corresponding printer record as a violation. The fix directly enforces rule 2 by ensuring `_rollback_registration` removes the capability record as well as the printer record and serial index when the Welcome Page fails, so no partial data remains.
  - Rule 1 is indirectly enforced: by treating a Welcome Page failure as a failed registration that must be rolled back, the system maintains the invariant that a registration is only considered successful once the Welcome Page has printed.

### Rule 4 — Capabilities capture

- Exact sentence:
  - "4. Printer capabilities are captured once at registration time so
   downstream services never need to re-query the device."
- Relation to this ticket:
  - The defect involves capability records created during registration and left orphaned when registration fails. Rule 4 explains why capability records exist as part of registration. The fix ensures that these capability records, which are created during registration, are also removed when registration fails and is rolled back, maintaining alignment with the registration lifecycle.

### Rule 12 — Deregistration and GDPR compliance (contextual)

- Exact sentence:
  - "12. Deregistration must remove all cloud associations and printer data
    (GDPR compliance)."
- Relation to this ticket:
  - While this rule explicitly governs deregistration, not registration rollback, it underscores the broader GDPR compliance requirement to remove residual printer-related data when the printer is no longer valid in the system. The ticket explicitly notes that orphaned capability records are a GDPR compliance concern. Ensuring rollback removes orphaned capability records aligns registration failure behavior with the same privacy/completeness expectations expressed for deregistration.

### Rule 14 — Observability of registration failures (contextual)

- Exact sentence:
  - "14. Registration failures should be observable (structured logging /
    telemetry), not silent — see BUD Section 10, \"Limited observability\"\n    as a known platform risk."
- Relation to this ticket:
  - The primary code change is focused on cleanup rather than logging, but the ticket is about a specific failure path (Welcome Page print failure) and its side effects. The existing `register_printer` logic already logs key events and uses an exception (`RegistrationError`) to signal failure. The addition of proper rollback ensures that the observable failure corresponds to a clean data state, supporting the spirit of rule 14 by avoiding hidden, non-obvious data inconsistencies such as orphaned capabilities.

## 4. Original Acceptance Criteria

Copied from `jira_context/GOAR-4_live.md`:

- "When Welcome Page printing fails, no printer record remains."
- "When Welcome Page printing fails, no capability record remains for that
printer_id."
- "When Welcome Page printing fails, the serial number is free to be
registered again from scratch."
- "Successful registrations are unaffected (do not regress)."

## 5. Adopted Additional Requirements

1. **Requirement:** When Welcome Page printing fails and `_rollback_registration` is invoked, the rollback must remove all three types of partial registration data listed in the business rule — printer record, capability record, and serial index — for the affected printer/serial number.
   - Justification: [exact rule sentence] "2. If any step fails **before** the Welcome Page prints, the entire
   registration must roll back — no partial data (printer record,
   capability record, serial index, etc.) may be retained."
   - Notes: The original acceptance criteria specify each of these effects individually (printer record, capability record, serial number being free). This requirement packages them explicitly as a single rollback invariant aligned with rule 2 so downstream tests can validate that no partial state of any of these types remains after rollback.

2. **Requirement:** When Welcome Page printing fails and registration is rolled back, any subsequent registration attempt for the same serial number must behave as a fresh registration, with no reuse of prior capabilities or other state carried over from the failed attempt.
   - Justification: [exact rule sentence] "2. If any step fails **before** the Welcome Page prints, the entire
   registration must roll back — no partial data (printer record,
   capability record, serial index, etc.) may be retained."
   - Edge case category: boundary/rollback — repeated registration attempts after a failure.
   - Notes: The ticket states that "the serial number is free to be registered again from scratch" but does not explicitly require verification that no prior capabilities or other registration artifacts are reused. This requirement makes explicit that a re-attempt after rollback must be indistinguishable from a first-time registration for that serial number, consistent with rule 2's prohibition on retaining partial data.

3. **Requirement:** If a Welcome Page print failure occurs for a re-registration (i.e., the serial number already had an existing printer record prior to the new registration attempt), rollback must only remove data created as part of the failed registration attempt and must not delete the pre-existing printer record or its capabilities.
   - Justification: [edge case category: ownership/rollback]
   - Rationale: The business rules do not explicitly describe how rollback should behave when a registration attempt is made against an already registered serial number, but re-registration is supported (see rules 3 and 6). To avoid silently wiping or corrupting an existing printer's data in such a scenario, tests should verify that rollback is scoped to the newly created/modified state for the current attempt. This requirement is framed as a rollback/ownership edge case derived from the need to avoid unintended data loss; however, because no specific business rule sentence governs partial re-registration rollback on existing printers, this requirement should be interpreted with caution (see Open Questions).

## 6. Open Questions

1. **Question:** How should rollback behave when a registration attempt with `simulate_welcome_page_failure=True` is made for a serial number that already has a fully registered printer record (i.e., a re-registration scenario)?
   - Why unresolved: The business rules specify that re-registration always generates a new Cloud ID and that registration/re-registration must not silently overwrite or wipe out an existing owner's claim (rules 3, 6, 11), but they do not explicitly describe rollback semantics when a re-registration fails before the Welcome Page prints. The ticket's steps to reproduce describe a failure during registration but do not distinguish between first-time registration and re-registration for an already registered printer.
   - Exclusion for downstream agents: Until clarified, downstream agents should not create or score tests that assume specific rollback behavior for failed re-registrations (e.g., whether the existing printer record and its capabilities should be preserved vs. partially or fully removed).

2. **Question:** Should capability records created during a failed registration attempt be retained if they contain additional telemetry or diagnostic information useful for debugging or compliance investigations, provided they are no longer linked to a live printer record?
   - Why unresolved: Business rule 2 states that "no partial data (printer record, capability record, serial index, etc.) may be retained" when registration fails before the Welcome Page prints, which appears to prohibit retention of such capability records. However, the broader non-functional expectations (rule 14) emphasize observability and telemetry. The ticket identifies orphaned capability records as a GDPR concern, but it does not explicitly address whether de-identified or repurposed diagnostic data is acceptable.
   - Exclusion for downstream agents: Downstream agents must not assume that keeping de-identified capability or diagnostic data is allowed or disallowed; tests should focus only on verifying that capability records directly associated with a printer_id from a failed registration are removed.

3. **Question:** Are there any additional data structures or indices in `app.store` (beyond printer records, capability records, and serial index) that should also be cleaned up during rollback to fully satisfy the "no partial data" requirement?
   - Why unresolved: The business rules explicitly mention "printer record, capability record, serial index" as examples but use "etc." to indicate that other partial data might exist. The available code (`app/registration.py`) shows cleanup of these three elements in `_rollback_registration`, but the implementation of `app.store` is not provided in the current context, so we cannot determine whether other indices or caches need to be cleared.
   - Exclusion for downstream agents: Agents must not create or score tests for cleanup of store structures beyond the explicitly known ones (printer record, capability record, serial index) without additional documentation about `app.store`'s internal data structures.

4. **Question:** Given that `reports/GOAR-4_diff.txt` is currently empty, is there any risk that the actual code changes deployed to production differ from the version of `app/registration.py` examined here, particularly in the `_rollback_registration` implementation?
   - Why unresolved: The instructions reference `reports/GOAR-4_diff.txt` as the authoritative diff for this fix, but the file is empty in the repository snapshot. The implementation in `app/registration.py` includes `store.delete_capabilities(printer.printer_id)` in `_rollback_registration`, which appears to satisfy the ticket; however, without a non-empty diff file, there is a potential mismatch between the ticket's validation report, the intended diff, and the actual deployed code history.
   - Exclusion for downstream agents: Until the diff file is corrected or cross-checked, downstream agents should base their tests on the current `app/registration.py` behavior but avoid using the missing diff file as evidence. Any scoring or validation that depends on historical change tracking should be deferred until the diff discrepancy is resolved.
