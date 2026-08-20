# Requirements Report — GOAR-4

## 1. Summary

This ticket addresses incomplete rollback behaviour during printer registration when the Welcome/Info Page fails to print. Currently, registration rollback removes the printer record and serial index but leaves behind an orphaned capability record with no corresponding printer, violating the business rule that no partial registration data may be retained. The fix ensures that when Welcome Page printing fails, all partial state for that registration attempt is removed — printer record, capability record, and serial index — so the serial number can be safely registered again and no orphaned capability data remains.

## 2. Affected Components

- `app/registration.py`
  - Function `_rollback_registration(printer: Printer) -> None`
  - Function `register_printer(...) -> Printer` (behavioural context for rollback, including `simulate_welcome_page_failure` flow)

- `app/store.py` (implied by calls from `registration.py`; not modified by this diff but behaviourally involved)
  - `store.delete_printer(printer_id)`
  - `store.remove_serial_index(serial_number)`
  - `store.delete_capabilities(printer_id)`

## 3. Applicable Business Rules

### Rule 1 — Registration success depends on Welcome Page

- **Exact sentence:** "Registration is successful **only if** the Welcome/Info Page prints."  
- **Relation to this ticket:** This rule defines the failure condition under which rollback must occur. GOAR-4 specifically targets the case where Welcome Page printing fails (simulated via `simulate_welcome_page_failure=True`), and ensures that such failures are treated as unsuccessful registrations requiring complete rollback.

### Rule 2 — No partial data on failed registration / rollback completeness

- **Exact sentence:** "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."  
- **Relation to this ticket:** This is the primary rule GOAR-4 enforces. The ticket describes a failure mode where capability records remain after a failed registration, creating orphans. The fix adds `store.delete_capabilities(printer.printer_id)` to `_rollback_registration`, so that printer record, capability record, and serial index are all removed when Welcome Page printing fails, satisfying the "no partial data" requirement.

### Rule 12 — Deregistration and GDPR compliance (contextual)

- **Exact sentence:** "Deregistration must remove all cloud associations and printer data (GDPR compliance)."  
- **Relation to this ticket:** While this rule is about deregistration rather than registration rollback, it reinforces the GDPR compliance concern cited in GOAR-4’s impact statement. Orphaned capability records constitute retained printer data without a valid registration context, which conflicts with the spirit of rule 12’s requirement to remove printer data when it should no longer be retained.

### Rule 14 — Observability of registration failures (contextual)

- **Exact sentence:** "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."  
- **Relation to this ticket:** GOAR-4’s primary focus is rollback completeness, not logging, but the existence of orphaned capability records resulted from failures that were not fully cleaned up. Ensuring rollback is complete supports clearer operational observability (no confusing orphaned data). The current diff and `registration.py` implementation log registration start and completion, and exceptions like `WelcomePagePrintError` are raised; however, this ticket does not explicitly modify logging.

## 4. Original Acceptance Criteria

Copied directly from `jira_context/GOAR-4_live.md`:

- "When Welcome Page printing fails, no printer record remains."
- "When Welcome Page printing fails, no capability record remains for that printer_id."
- "When Welcome Page printing fails, the serial number is free to be registered again from scratch."
- "Successful registrations are unaffected (do not regress)."

## 5. Adopted Additional Requirements

All additions below are grounded either in explicit business rule sentences or recognised edge case categories (boundary value, auth failures, ownership conflicts, rollback behaviour).

### 5.1 Rollback must be invoked for *any* failure before Welcome Page prints, not only simulated failures

- **Requirement statement:** For any registration attempt where a failure occurs before the Welcome/Info Page prints — regardless of whether it is triggered via `simulate_welcome_page_failure` or a real `WelcomePagePrintError` — `_rollback_registration` must be invoked, and the rollback must remove the printer record, capability record, and serial index for the affected printer.
- **Justification:** [exact rule sentence] Business rules `docs/business_rules.md`: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This requirement generalises the AC from the specific simulated failure path to any failure path, which is demanded by the "any step fails" scope of Rule 2.

### 5.2 Rollback must remove capabilities even if they were pre-existing for that printer_id

- **Requirement statement:** If a registration or re-registration attempt for a given `printer_id` fails before the Welcome Page prints, `_rollback_registration` must remove any capability record associated with that `printer_id`, even if that capability record was created during a prior successful registration and not newly created in the current attempt.
- **Justification:** [edge case category: rollback behaviour] The original AC is written in terms of "no capability record remains for that printer_id" but does not explicitly address the case where capabilities already existed prior to the failed attempt (e.g., re-registration with `store.get_capabilities(printer_id)` returning a record). Rule 2’s "no partial data ... may be retained" sentence covers capabilities generally, and rollback must ensure that after a failed registration attempt, there is no capability record tied to a `printer_id` that no longer has a corresponding printer record.

### 5.3 Serial index removal must ensure no stale serial mapping remains

- **Requirement statement:** On rollback, `store.remove_serial_index(printer.serial_number)` must guarantee that no index or mapping remains which would cause `store.get_printer_by_serial(serial_number)` to return a stale `printer_id` after the failed registration. Subsequent successful registrations using the same serial number must behave as a fresh registration, with no linkage to any prior failed attempt.
- **Justification:** [exact rule sentence] Business rules `docs/business_rules.md`: "no partial data (printer record, capability record, serial index, etc.) may be retained." The explicit mention of "serial index" requires that any indexing structure mapping serial numbers to printers be cleared such that there is no possibility of stale mappings persisting after rollback.

### 5.4 Rollback behaviour must be identical for first-time registration and re-registration failures

- **Requirement statement:** When a re-registration attempt (for a serial number that already has an existing printer record) fails before the Welcome Page prints, rollback must remove the printer record, capability record, and serial index for that `printer_id` in the same way as for a first-time registration failure, leaving no registration state behind for that serial number.
- **Justification:** [exact rule sentence] Business rules `docs/business_rules.md`: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." The rule does not distinguish between first-time registration and re-registration. Ensuring identical rollback behaviour covers this edge case and prevents orphaned data when re-registration fails.

### 5.5 Rollback must be idempotent for a given failed registration attempt

- **Requirement statement:** Invoking `_rollback_registration(printer)` multiple times for the same failed registration attempt must not cause errors or leave residual data; repeated calls must either perform no-op deletions on already-removed records or consistently result in a state where no printer record, capability record, or serial index exists for that printer.
- **Justification:** [edge case category: rollback behaviour] Rule 2 mandates complete rollback and no partial data retention. In distributed or retried error-handling scenarios, rollback may be invoked more than once; ensuring idempotent behaviour prevents inconsistent states where some elements (e.g., serial index) are removed but others (e.g., capabilities) remain because of partial rollback on repeated invocations.

## 6. Open Questions

### 6.1 Behaviour when capabilities existed from a prior successful registration

- **The question:** If a re-registration attempt fails before the Welcome Page prints, and capabilities for that `printer_id` already existed from a prior successful registration, should rollback delete those pre-existing capabilities (as now implemented with `store.delete_capabilities(printer.printer_id)`), or should they be preserved as part of the last known-good registration?
- **Why it cannot be resolved from available inputs:** Rule 2 states that "no partial data ... may be retained" when a step fails before the Welcome Page prints, but it does not explicitly distinguish data created during the current failed attempt from data created during a prior successful registration. The Jira ticket text for GOAR-4 describes orphaned capabilities arising from failed registrations where the printer record is removed, implying capabilities were created during that attempt. It does not explicitly discuss the case where capabilities predate the failure. The diff and current implementation always delete capabilities on rollback, but it is unclear if this is the intended behaviour in the re-registration-with-existing-capabilities scenario.
- **Downstream exclusion:** Until clarified, downstream test design and scoring must avoid treating deletion of pre-existing capabilities on re-registration failure as either required or forbidden. Tests should focus on the simpler, clearly in-scope case where capabilities are created during the failed attempt and must be removed to avoid orphans.

### 6.2 Logging and observability requirements for rollback

- **The question:** Should `_rollback_registration` explicitly log structured information (e.g., printer_id, serial_number, reason for rollback) to meet rule 14’s observability expectations, or is the existing logging around registration start, completion, and exception handling considered sufficient for this ticket?
- **Why it cannot be resolved from available inputs:** Rule 14 requires registration failures to be observable via structured logging/telemetry, but neither the GOAR-4 ticket nor the provided diff mention logging changes. The current implementation logs some registration events, but there is no explicit requirement in GOAR-4 about logging granularity for rollback. Without explicit Jira text or business rule guidance targeted at this ticket, it is ambiguous whether additional logging should be part of the acceptance criteria.
- **Downstream exclusion:** Downstream agents must not score or fail this ticket based on the presence or absence of additional rollback-specific logging. Tests should verify functional rollback behaviour (no printer, capabilities, or serial index remaining), not logging details, unless another ticket explicitly introduces logging ACs.

### 6.3 Interaction with deregistration (Rule 12) when registration fails

- **The question:** In scenarios where a printer was previously deregistered (per Rule 12) and then a new registration attempt fails before the Welcome Page prints, is there any additional GDPR-specific cleanup required beyond removing printer record, capabilities, and serial index for the failed attempt?
- **Why it cannot be resolved from available inputs:** Rule 12 describes full data removal on deregistration, and Rule 2 describes full rollback on failed registration. The combination suggests that no printer data should remain in either case, but the Jira ticket does not describe this combined scenario, and the code/diff do not show any special-case handling for "previously deregistered" printers during rollback. As a result, it is unclear whether extra requirements (e.g., auditing or notification) apply when both mechanisms are involved.
- **Downstream exclusion:** Downstream agents must avoid adding test cases or scoring criteria that presume special GDPR behaviours for "failed registration after prior deregistration" beyond the generic rollback behaviour already covered by Rule 2.
