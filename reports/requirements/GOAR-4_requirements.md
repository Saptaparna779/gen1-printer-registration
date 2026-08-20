# Requirements Report — GOAR-4

## 1. Summary

This ticket fixes incomplete rollback behavior when printer registration fails at the Welcome Page printing step. Previously, if `simulate_welcome_page_failure=True` caused the Welcome Page to fail, the system deleted the printer record and removed the serial index but left behind a capability record for that `printer_id`, creating an orphaned capability entry with no corresponding printer. This violated the business rule that no partial registration data may be retained and raised GDPR compliance concerns. The fix ensures that rollback removes the capability record as well, so failed registrations leave no printer record, no capability record, and no serial index.

## 2. Affected Components

- `app/registration.py`
  - `register_printer(...)`
    - Uses `simulate_welcome_page_failure` to trigger rollback via `_rollback_registration(printer)` when `generate_and_print_welcome_page` raises `WelcomePagePrintError`.
  - `_rollback_registration(printer: Printer) -> None`
    - Updated logic to delete all partial registration state:
      - `store.delete_printer(printer.printer_id)`
      - `store.remove_serial_index(printer.serial_number)`
      - `store.delete_capabilities(printer.printer_id)` (newly added cleanup for GOAR-4).

- `store` module (indirectly)
  - `delete_printer(printer_id)` — removes printer record.
  - `remove_serial_index(serial_number)` — frees serial number for reuse.
  - `delete_capabilities(printer_id)` — removes capability record; now called during rollback.

- `app/welcome_page.generate_and_print_welcome_page(...)`
  - Behavior unchanged; still raises `WelcomePagePrintError` on failure, which triggers `_rollback_registration`.

## 3. Applicable Business Rules

### Rule 1 — Registration success depends on Welcome Page

- Exact sentence: "Registration is successful **only if** the Welcome/Info Page prints."
- Relation to this ticket: This rule defines the success boundary for registration. GOAR-4 focuses on the failure path when the Welcome Page does not print; ensuring that failed registrations are fully rolled back is consistent with the idea that no successful registration exists until the page prints.

### Rule 2 — No partial data on failure / full rollback

- Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
- Relation to this ticket: This is the core rule driving GOAR-4. The bug is that capability records remained after a failure, violating the "no partial data" requirement. The fix adds `store.delete_capabilities(printer.printer_id)` to `_rollback_registration`, so printer record, capability record, and serial index are all removed when the Welcome Page fails.

### Rule 4 — Capabilities captured at registration

- Exact sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."
- Relation to this ticket: Because capabilities are captured during registration, a failed registration that leaves capabilities behind creates an inconsistent state: downstream services could see capabilities for a printer that does not exist. GOAR-4 ensures that these capability records are removed on rollback, maintaining consistency between printer and capability data.

### Rule 12 — Deregistration must remove all printer data (GDPR)

- Exact sentence: "Deregistration must remove all cloud associations and printer data (GDPR compliance)."
- Relation to this ticket: While GOAR-4 is about failed registration rather than deregistration, the GDPR compliance concern is similar: orphaned capability records constitute retained printer data without a corresponding printer. Full rollback on registration failure (including capability deletion) aligns with the spirit of this rule by avoiding orphaned data that could violate GDPR expectations.

### Rule 14 — Failures must be observable

- Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
- Relation to this ticket: The existing `register_printer` implementation logs events (e.g., "Registration started", "Welcome page printed successfully; registration complete") and raises `WelcomePagePrintError` which becomes a `RegistrationError`. GOAR-4 does not change logging directly, but the rollback path that is exercised on failure remains part of an observable failure flow, consistent with this rule. The focus here is on data cleanup, not observability changes.

## 4. Original Acceptance Criteria

(Verbatim from `jira_context/GOAR-4_live.md`)

- "When Welcome Page printing fails, no printer record remains."
- "When Welcome Page printing fails, no capability record remains for that printer_id."
- "When Welcome Page printing fails, the serial number is free to be registered again from scratch."
- "Successful registrations are unaffected (do not regress)."

## 5. Adopted Additional Requirements

### 5.1 Rollback must be triggered for any failure prior to successful Welcome Page printing

- Requirement statement:
  - If any error occurs before the Welcome Page prints successfully (including but not limited to `WelcomePagePrintError`), the registration flow must invoke `_rollback_registration` so that no partial data (printer record, capability record, serial index) is retained.
- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - This extends the AC beyond the specific `simulate_welcome_page_failure` case to cover any pre-Welcome-Page failure, matching the rule’s "any step fails" wording.

### 5.2 Capability deletion in rollback must be idempotent and safe when no capability exists

- Requirement statement:
  - `_rollback_registration` must be safe to call regardless of whether a capability record exists for `printer.printer_id`; calling `store.delete_capabilities(printer.printer_id)` when no capabilities are present must not raise errors that would abort rollback or leave other partial data (printer record, serial index) undeleted.
- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - Edge case category: boundary / repeated-operation — rollback must fully complete even when some entities are already missing, to ensure no remaining partial state.

### 5.3 Serial index removal must succeed even if printer record creation partially failed

- Requirement statement:
  - `_rollback_registration` must remove the serial index (`store.remove_serial_index(printer.serial_number)`) even if the printer record was never successfully saved, so that failed or partially failed registrations cannot leave the serial number blocked for future registrations.
- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - Edge case category: boundary — partial failures that occur after indexing but before full save must still clean up the serial index.

### 5.4 Rollback must not affect existing printers unrelated to the failed registration

- Requirement statement:
  - `_rollback_registration` for a failed registration of a given `printer.printer_id` and `serial_number` must only delete the printer record, capability record, and serial index associated with that specific printer. No other printers’ records, capability entries, or serial indices may be modified.
- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - Edge case category: ownership / data isolation — rollback cleanup must be scoped to the failing registration to avoid unintended data loss.

### 5.5 Successful registrations must persist all required data even after intermittent failures

- Requirement statement:
  - When a registration attempt succeeds (Welcome Page prints successfully), printer record, capability record, and serial index must all remain intact and consistent, even if there were previous failed attempts for the same serial number that triggered `_rollback_registration`.
- Justification:
  - Exact rule sentence: "Registration is successful **only if** the Welcome/Info Page prints."
  - Exact rule sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."
  - Edge case category: rollback — prior failures must not cause over-aggressive cleanup that affects a subsequent successful registration.

## 6. Open Questions

### 6.1 Scope of rollback for failures after capabilities are captured but after XMPP assignment

- The question:
  - If a failure occurs after capabilities are captured and XMPP node is assigned, but still before the Welcome Page prints (e.g., an error in generating the page), should `_rollback_registration` also clear XMPP-related data, or is XMPP cleanup handled elsewhere?
- Why it cannot be resolved from available inputs:
  - `docs/business_rules.md` explicitly lists "printer record, capability record, serial index" in the rollback context but does not mention XMPP nodes in the rollback rule. The `register_printer` implementation assigns an XMPP node before the Welcome Page, yet `_rollback_registration` currently only deletes the printer, serial index, and capabilities. The ticket GOAR-4 and the diff focus solely on capability records and do not specify XMPP rollback behavior.
- What downstream agents must exclude from scoring:
  - Any tests or scoring that assume XMPP node cleanup is required or not required during rollback must be excluded until the product owner clarifies whether XMPP associations are considered registration data that must be removed on pre-Welcome-Page failure.

### 6.2 Behavior when `generate_and_print_welcome_page` fails after partially printing

- The question:
  - If the Welcome Page begins printing but fails mid-way (e.g., printer out of paper) and `generate_and_print_welcome_page` raises `WelcomePagePrintError`, should this still trigger full rollback per rule 2, or is there a different rule for partial prints?
- Why it cannot be resolved from available inputs:
  - Business rule 1 states that registration is successful "only if the Welcome/Info Page prints" but does not define partial prints. Business rule 2 refers to steps failing "before the Welcome Page prints"; it is ambiguous whether a partial print is treated as "prints" or "fails before it prints". The current implementation unconditionally rolls back on `WelcomePagePrintError`, but the semantic expectation around partial printing is not documented.
- What downstream agents must exclude from scoring:
  - Any tests or scoring that differentiate between partial vs. non-started Welcome Page printing must be excluded. Downstream agents should treat all `WelcomePagePrintError` cases uniformly for now but not assert business-level correctness about partial print semantics.

### 6.3 Rollback behavior when a re-registration fails for a previously registered/claimed printer

- The question:
  - If an existing printer (already REGISTERED or CLAIMED) is being re-registered and the Welcome Page printing fails, should `_rollback_registration` delete the existing printer record and capabilities, or only the new/partial state? How is "partial state" defined for re-registration vs. initial registration?
- Why it cannot be resolved from available inputs:
  - Business rule 2 speaks in terms of "registration" generally and does not distinguish between first-time registration and re-registration. The implementation of `_rollback_registration` accepts a `Printer` object and deletes its record, serial index, and capabilities. For re-registration of an already-registered printer, this may mean deleting long-lived data, which could conflict with ownership rules (e.g., rule 11) or re-registration semantics (rules 3 and 6). GOAR-4 describes the bug in terms of failed registrations and orphaned capability records but does not clarify expected behavior for re-registration rollback.
- What downstream agents must exclude from scoring:
  - Any tests or scoring that assume a specific rollback behavior for re-registration failures (e.g., that existing printer data should be preserved vs. deleted) must be excluded until clarified. Focus downstream testing on initial registration failure scenarios where the printer did not previously exist.

