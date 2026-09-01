# Requirements Report — GOAR-4

## 1. Summary

Failed printer registrations that abort at the Welcome/Info Page printing step are leaving behind orphaned capability records with no corresponding printer record, which violates the business rule that no partial registration data may be retained. GOAR-4 ensures that when the Welcome Page fails to print, the registration rollback path removes all partial state associated with that attempted registration — specifically the printer record, the capability record, and the serial index — so there are no orphaned records and the serial number can be cleanly re-registered. Successful registrations remain unchanged.

## 2. Affected Components

- app/registration.py — register_printer()
  - Entry point for printer registration and re-registration, including a `simulate_welcome_page_failure` flag used in the Jira ticket’s reproduction steps.
  - On Welcome Page failure (`WelcomePagePrintError`), calls `_rollback_registration(printer)` and then raises `RegistrationError`.

- app/registration.py — _rollback_registration(printer: Printer)
  - Rollback helper invoked when registration fails before the Welcome Page prints.
  - Current implementation:
    - `store.delete_printer(printer.printer_id)` — removes the printer record.
    - `store.remove_serial_index(printer.serial_number)` — removes the serial index entry.
    - `store.delete_capabilities(printer.printer_id)` — removes any capability record for that printer_id (the GOAR-4 fix).

Diff vs implementation note:
- reports/GOAR-4_diff.txt is empty in the repo snapshot, so it does not explicitly show the addition of `store.delete_capabilities(printer.printer_id)` to `_rollback_registration`.
- The Jira Validation Report and the actual implementation in app/registration.py both show that capability deletion is now part of rollback. This mismatch is recorded as an open question; tests and requirements should trust the source implementation over the empty diff.

## 3. Applicable Business Rules

### Rule 1 — Registration success requires Welcome/Info Page

"Registration is successful **only if** the Welcome/Info Page prints."

How it applies:
- The ticket’s reproduction path uses `simulate_welcome_page_failure=True` to force a Welcome Page failure. Under Rule 1, such a run is not a successful registration and must not leave a printer in a "registered" state. GOAR-4’s rollback behavior is triggered on this failure, ensuring that failed attempts do not masquerade as successful registrations.

### Rule 2 — Full rollback on failure before Welcome Page

"If any step fails **before** the Welcome Page prints, the entire
registration must roll back — no partial data (printer record,
capability record, serial index, etc.) may be retained."

How it applies:
- This is the primary rule enforced by GOAR-4. Prior to the fix, the rollback path removed the printer record and serial index but left a capability record, contradicting Rule 2’s explicit requirement that capability records (and other partial data) must not be retained.
- The updated `_rollback_registration` now deletes all three categories of partial data listed in the rule: printer record, capability record, and serial index, aligning implementation with the stated business requirement.

### Rule 4 — Capabilities captured once at registration time

"Printer capabilities are captured once at registration time so
 downstream services never need to re-query the device."

How it applies:
- `register_printer` captures capabilities during registration and persists them via `store.save_capabilities`. GOAR-4 ensures that these capability records only persist when registration actually succeeds (Welcome Page prints). For failed registrations, they are removed by `_rollback_registration`, preventing downstream services from seeing capabilities for a printer that did not successfully register.

### Rule 12 — Deregistration must remove data (GDPR compliance)

"Deregistration must remove all cloud associations and printer data
 (GDPR compliance)."

How it applies:
- While this rule is about deregistration, the Jira ticket explicitly cites orphaned capability records as a "GDPR compliance concern." GOAR-4’s rollback behavior mirrors the spirit of Rule 12 by ensuring that failed registrations do not leave behind persistent printer data, including capabilities, that could be considered personal or device-identifying information.

## 4. Original Acceptance Criteria

(From jira_context/GOAR-4_live.md, verbatim.)

- "When Welcome Page printing fails, no printer record remains."
- "When Welcome Page printing fails, no capability record remains for that
printer_id."
- "When Welcome Page printing fails, the serial number is free to be
registered again from scratch."
- "Successful registrations are unaffected (do not regress)."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Capability rollback is idempotent
   - Requirement: Multiple invocations of `_rollback_registration` for the same printer must not leave any printer record, capability record, or serial index for that serial number, and must not raise errors solely because the records were already deleted.
   - Justification: Edge case category — rollback/partial-failure behaviour. Supported by Rule 2: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This extends the rule to repeated rollback scenarios.

2. Rollback deletes only data for the failing printer_id
   - Requirement: `_rollback_registration` must only delete capabilities, printer records, and serial indices associated with the specific `printer.printer_id` and `printer.serial_number` being rolled back; it must not affect other printers’ data, even if they share attributes like model_number.
   - Justification: Edge case category — ownership conflicts. Rule 2 requires removal of partial data for the failed registration, not unrelated data. Scoping deletions to the passed-in printer_id ensures other printers (potentially claimed by different owners) are not impacted.

3. Serial index cleanup fully resets first-time registration behaviour
   - Requirement: After rollback for a failed registration, a subsequent call to `register_printer` with the same serial_number must behave exactly as an initial registration (no existing printer returned from `get_printer_by_serial`, new Printer object created, new Cloud ID and capabilities captured).
   - Justification: Edge case category — repeated operations. Supported by Rule 2’s phrase "no partial data ... may be retained" and the AC: "When Welcome Page printing fails, the serial number is free to be registered again from scratch." This ensures serial index cleanup is complete.

4. Rollback must not disturb existing claimed printers unrelated to the failure
   - Requirement: When `_rollback_registration` is invoked, it must not delete any records for printers in `PrinterStatus.CLAIMED` state other than the printer being rolled back.
   - Justification: Edge case category — ownership conflicts. Rule 11 states: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Limiting rollback scope prevents accidental loss of data or claims for other owners.

5. Successful registrations must never trigger rollback
   - Requirement: When the Welcome Page prints successfully (no `WelcomePagePrintError`), `_rollback_registration` must not be called, and no deletion of printer, capability, or serial index data may occur as part of the success path.
   - Justification: Edge case category — rollback/partial-failure behaviour. Based on Rule 1 ("Registration is successful **only if** the Welcome/Info Page prints.") and Rule 2. Together they imply that rollback is only appropriate for pre-Welcome Page failures, not for successful registrations.

6. Capability records for failed registrations must not be externally observable
   - Requirement: Any capability records created during a registration attempt that ultimately fails before the Welcome Page prints must be deleted by `_rollback_registration` before they can be read by or exposed to downstream consumers (e.g., lists of printers, capability queries), so external systems never see capabilities for a non-registered printer.
   - Justification: Edge case category — rollback/partial-failure behaviour. Supported by Rule 2: "no partial data (printer record, capability record, serial index, etc.) may be retained" and informed by Rule 12’s GDPR framing of printer data removal.

## 6. Flagged Conflicts

None identified. The acceptance criteria are fully consistent with Rules 1, 2, 4, and 12 as written. The implementation of `_rollback_registration` in app/registration.py deletes printer records, capability records, and serial indices on Welcome Page failure, which matches both the ticket and the business rules.

## 7. Open Questions

1. Empty diff vs. implementation for GOAR-4
   - Question: Why is `reports/GOAR-4_diff.txt` empty, even though the Jira Validation Report and current implementation show `store.delete_capabilities(printer.printer_id)` in `_rollback_registration` as the GOAR-4 fix?
   - Why unresolvable: The diff file contains no content, and there is no additional metadata indicating whether this is intentional or an automation error. We cannot reconstruct the exact change set from the available inputs.
   - Exclude from scoring: Downstream agents that rely on diffs (scenario design, diff-based test generation, and any tooling that compares behavior "before vs after" using reports/GOAR-4_diff.txt) must not treat the empty diff as authoritative.

2. Required ordering/atomicity of rollback deletions
   - Question: Does `_rollback_registration` need to enforce a particular order or transactional guarantee across `delete_printer`, `remove_serial_index`, and `delete_capabilities` (e.g., all-or-nothing semantics), or is best-effort deletion sufficient as long as normal operation leaves no partial data?
   - Why unresolvable: Rule 2 mandates that no partial data may be retained but does not define how to handle failures inside rollback itself. The current implementation performs three independent operations without transaction semantics; the Jira ticket does not address error handling within rollback.
   - Exclude from scoring: Agents focused on fault-injection, transaction semantics, or store-level failure modes should not assume a particular ordering or atomicity until clarified by product owners or architects.

3. Logging/telemetry requirements for rollback cleanup
   - Question: Are additional structured logs or telemetry events required when `_rollback_registration` deletes capability records and other partial data (e.g., explicit fields for printer_id, serial_number, and cause="welcome_page_failure"), beyond the existing `RegistrationError` and printer logs?
   - Why unresolvable: Rule 14 requires that registration failures be observable, but it does not specify the granularity or structure of logs for rollback cleanup. The Jira ticket and code diff do not mention logging enhancements.
   - Exclude from scoring: Agents evaluating observability or telemetry must not assume new logging fields or metrics specific to GOAR-4; they should score only on correctness of data rollback unless explicit logging requirements are later added.

4. GDPR-specific expectations for capability records
   - Question: Beyond deleting orphaned capability records on rollback, are there any additional GDPR-related requirements (e.g., retention policies, anonymization, or audit logging) that apply specifically to capability data created during failed registrations?
   - Why unresolvable: Rule 12 frames deregistration in terms of GDPR but does not define GDPR handling for failed registrations or isolated capability records; the ticket only states that orphaned capability records are "a GDPR compliance concern" without elaboration.
   - Exclude from scoring: Compliance-focused agents must not infer additional GDPR behaviours (such as specific retention windows or audit exports) for capability records beyond the explicit requirement to delete them on rollback.
