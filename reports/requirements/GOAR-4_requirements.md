# Requirements Report — GOAR-4

## 1. Summary

Failed printer registrations (where the Welcome/Info Page does not print) were leaving behind orphaned capability records in the store. This violated the business rule that no partial registration data (printer record, capability record, serial index, etc.) may be retained when registration fails before the Welcome Page prints, and created GDPR compliance issues by retaining data without a corresponding printer record. The fix ensures that the rollback path for a failed registration removes all partial state: the printer record, its capability record, and the serial number index, while leaving successful registrations unchanged.

## 2. Affected Components

- `app/registration.py`
  - Function `_rollback_registration(printer: Printer) -> None`:
    - Updated to call `store.delete_capabilities(printer.printer_id)` in addition to existing cleanup of the printer record and serial index, so that capability records are also removed during rollback.
  - Function `register_printer(...) -> Printer`:
    - Uses `_rollback_registration(printer)` in the `WelcomePagePrintError` exception path; behavior otherwise unchanged for successful registrations.

- `reports/GOAR-4_diff.txt`
  - (Empty content in the repository snapshot, but Jira validation comments describe the logical diff as adding `store.delete_capabilities(printer.printer_id)` inside `_rollback_registration`.)

- `jira_context/GOAR-4_live.md`
  - Contains the Jira ticket description, acceptance criteria, and validation report that reference the rollback behavior and the added capability-deletion step.

## 3. Applicable Business Rules

1. **Registration Rule 1**
   - **Exact sentence:** "Registration is successful **only if** the Welcome/Info Page prints."
   - **Relation to this ticket:** GOAR-4 concerns the failure path before the Welcome Page prints. This rule defines the boundary between a successful registration (where data may be retained) and an unsuccessful one (where rollback must occur). The fix ensures that attempts where the Welcome Page fails are treated as unsuccessful registrations and do not leave behind partial data.

2. **Registration Rule 2**
   - **Exact sentence:** "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - **Relation to this ticket:** This is the primary rule GOAR-4 enforces. The bug was that capability records were not removed when registration failed before the Welcome Page printed, leaving orphaned capabilities. Updating `_rollback_registration` to delete capabilities alongside the printer record and serial index brings the implementation into alignment with the requirement that "no partial data (printer record, capability record, serial index, etc.) may be retained."

3. **Deregistration / GDPR Rule 12**
   - **Exact sentence:** "Deregistration must remove all cloud associations and printer data (GDPR compliance)."
   - **Relation to this ticket:** While GOAR-4 operates on registration rollback (not explicit deregistration), it addresses a similar GDPR concern by ensuring that failed registrations do not leave orphan records. The ticket description explicitly notes that orphaned capability records are "a GDPR compliance concern." Ensuring rollback removes capabilities aligns with the broader requirement that printer-related data not persist without a valid, intentional registration state.

4. **Non-Functional Expectations Rule 14**
   - **Exact sentence:** "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - **Relation to this ticket:** Although GOAR-4’s diff does not introduce new logging, the scenario it addresses (failed Welcome Page printing with rollback) is a type of registration failure. Any tests or future changes for this ticket should ensure that such failures remain observable via logs/telemetry; however, no specific additional logging behavior is mandated by the current ticket or diff.

## 4. Original Acceptance Criteria

(Quoted exactly from `jira_context/GOAR-4_live.md`)

1. "When Welcome Page printing fails, no printer record remains."
2. "When Welcome Page printing fails, no capability record remains for that printer_id."
3. "When Welcome Page printing fails, the serial number is free to be registered again from scratch."
4. "Successful registrations are unaffected (do not regress)."

## 5. Adopted Additional Requirements

1. **Requirement:** When `_rollback_registration` is invoked for a failed registration (i.e., failure before the Welcome Page prints), it must remove all three categories of partial data explicitly named in the business rules: the printer record, the capability record for that printer, and the serial index entry for the serial number used in the failed registration.
   - **Justification:** Business rules sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This requirement makes explicit that all three named data types must be cleaned up in the rollback helper, not only a subset, to avoid future regressions where one category (e.g., capabilities) is omitted.

2. **Requirement:** After a rollback due to Welcome Page print failure, a subsequent registration attempt using the same serial number must proceed as a fresh registration, with no lookup or reuse of any prior printer_id, capabilities, or indices from the failed attempt.
   - **Justification:** Business rules sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." If any previous identity or capability data influenced a future registration, then partial data from the failed attempt would effectively be retained. This requirement clarifies the expected behavior for the next registration attempt after rollback. [Edge case category: rollback]

3. **Requirement:** Rollback behavior for Welcome Page print failures must be identical whether the registration attempt is an initial registration or a re-registration of an existing serial number: in both cases, if the Welcome Page fails to print, no printer record, capability record, or serial index associated with the attempted registration may remain.
   - **Justification:** Business rules sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." The rule does not distinguish between first registrations and re-registrations; therefore, this requirement clarifies that rollback completeness applies uniformly in both scenarios. [Edge case category: rollback]

## 6. Open Questions

1. **Question:** Should capability deletion in `_rollback_registration` be conditional on the existence of a capability record, or is it acceptable to call `store.delete_capabilities(printer.printer_id)` unconditionally and rely on the store implementation to handle missing records gracefully?
   - **Why unresolved:** The available code and business rules specify that no capability record should remain but do not describe error-handling expectations for deleting non-existent capabilities. `app/store` behavior is not shown in the provided context, so it is unclear whether unconditional deletion might raise errors or is guaranteed to be idempotent.
   - **Downstream exclusion:** Until clarified, downstream agents should not score or assert behavior that depends on the exact error-handling semantics of `store.delete_capabilities` when no capabilities exist (e.g., whether it must be strictly idempotent).

2. **Question:** Are there any additional data artifacts (beyond printer record, capability record, and serial index) that must be removed during rollback to satisfy internal GDPR interpretations (for example, logs with personal data or auxiliary indices not described in `business_rules.md`)?
   - **Why unresolved:** The business rules enumerate "printer record, capability record, serial index, etc." but do not list every possible data artifact. The Jira ticket mentions GDPR compliance concerns but does not clarify whether other artifacts are considered in-scope for rollback, nor is the full data model available in this context.
   - **Downstream exclusion:** Downstream agents must not assume or assert requirements about deleting additional artifacts (beyond printer, capability, and serial index) as part of rollback until clarified by product/legal stakeholders. Scoring should focus only on the explicitly named artifacts.

3. **Question:** Should registration failures caused by Welcome Page print errors (and the corresponding rollback) emit specific structured logging or telemetry events beyond what is currently implemented, to satisfy observability expectations in Rule 14?
   - **Why unresolved:** Business Rule 14 requires registration failures to be observable, but the provided diff and ticket do not specify any new logging/telemetry requirements, nor do we see the current logging in the Welcome Page failure path beyond raising `WelcomePagePrintError`. Without visibility into existing logging around `generate_and_print_welcome_page` and `_rollback_registration`, we cannot determine whether current observability is sufficient.
   - **Downstream exclusion:** Downstream agents should not introduce or score tests that depend on the presence of specific new log fields or telemetry events for this ticket. Any such observability requirements must be confirmed separately.


Audit / Compliance Notes:
- This report is based on the contents of `jira_context/GOAR-4_live.md`, `reports/GOAR-4_diff.txt`, `docs/business_rules.md`, and `app/registration.py` as retrieved from the `main` branch of the repository.
- The core compliance concern addressed is preventing orphaned capability records for failed registrations, in line with GDPR-related expectations articulated in both `business_rules.md` (Rule 2 and Rule 12) and the Jira ticket.
