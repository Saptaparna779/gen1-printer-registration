# Requirements Report — GOAR-4

## 1. Summary

Failed printer registrations that abort at the Welcome/Info Page printing step are leaving behind orphaned capability records with no corresponding printer record, which violates the business rule that no partial registration data may be retained. GOAR-4 ensures that when the Welcome Page fails to print, the registration rollback path removes all partial state associated with that attempted registration — specifically the printer record, the capability record, and the serial index — so there are no orphaned records and the serial number can be cleanly re-registered. Successful registrations remain unchanged.

## 2. Affected Components

- `app/registration.py`
  - `register_printer(...)`
    - Uses `simulate_welcome_page_failure` to trigger rollback on `WelcomePagePrintError`.
    - On failure, calls `_rollback_registration(printer)` before raising `RegistrationError`.
  - `_rollback_registration(printer: Printer) -> None`
    - Rollback behavior updated to delete printer capabilities as well as the printer record and serial index:
      - `store.delete_printer(printer.printer_id)`
      - `store.remove_serial_index(printer.serial_number)`
      - `store.delete_capabilities(printer.printer_id)` (cleanup for GOAR-4, now present in implementation).

- Store interface (indirectly via `app.store`)
  - `store.delete_printer(printer_id)` — used in rollback.
  - `store.remove_serial_index(serial_number)` — used in rollback.
  - `store.delete_capabilities(printer.printer_id)` — now also used in rollback; capability records for failed registrations are removed.

The diff file `reports/GOAR-4_diff.txt` is empty in the provided input, so the specific change set is not visible. However, the Jira Validation Report text and the current implementation of `_rollback_registration` in `app/registration.py` both indicate that `store.delete_capabilities(printer.printer_id)` has been added to the rollback path. Because the diff is empty but the implementation shows the cleanup in place, this is a minor inconsistency and is noted explicitly in Open Questions.

## 3. Applicable Business Rules

### Rule 1 — Registration success requires Welcome/Info Page

> "Registration is successful **only if** the Welcome/Info Page prints."  

Relation to GOAR-4:
- The ticket’s steps to reproduce explicitly use `simulate_welcome_page_failure=True` in `register_printer(...)` to simulate the Welcome Page failing to print. Under Rule 1, those attempts must be treated as failed registrations. GOAR-4’s change to `_rollback_registration` ensures that such failures are handled consistently and do not leave behind partial registration artifacts (e.g., capabilities) for an attempt that never reached successful registration.

### Rule 2 — Full rollback on failure before Welcome Page

> "If any step fails **before** the Welcome Page prints, the entire
>    registration must roll back — no partial data (printer record,
>    capability record, serial index, etc.) may be retained."  

Relation to GOAR-4:
- This rule is the direct driver of the GOAR-4 fix. The Jira description notes that capability records were left behind when a simulated Welcome Page failure occurred, meaning rollback was incomplete. The updated `_rollback_registration` now deletes:
  - the printer record (`store.delete_printer(printer.printer_id)`),
  - the serial index (`store.remove_serial_index(printer.serial_number)`), and
  - the capability record (`store.delete_capabilities(printer.printer_id)`),
  which aligns the implementation with the explicit list of partial data in Rule 2.

### Rule 4 — Capabilities captured once at registration time

> "Printer capabilities are captured once at registration time so
>    downstream services never need to re-query the device."  

Relation to GOAR-4:
- `register_printer` captures capabilities via `_capture_capabilities(...)` and persists them with `store.save_capabilities(capabilities)`. GOAR-4 ensures that if registration ultimately fails before the Welcome Page, those capabilities are removed via `store.delete_capabilities(printer.printer_id)` in `_rollback_registration`. This maintains the invariant that only successfully registered printers have persistent capability data, avoiding misleading capability records for printers that did not complete registration.

### Rule 12 — Deregistration must remove all cloud associations and printer data (GDPR compliance)

> "Deregistration must remove all cloud associations and printer data
>    (GDPR compliance)."  

Relation to GOAR-4:
- While Rule 12 is formally about deregistration rather than failed registration, the Jira ticket explicitly cites GDPR concerns around orphaned capability records. GOAR-4’s rollback enhancement mirrors the spirit of Rule 12 by ensuring that failed registrations do not leave behind persistent printer-related data (including capabilities) that could be considered personal or device-identifiable information. This keeps both deregistration and failed-registration flows aligned with the platform’s GDPR-compliance expectations.

### Rule 14 — Registration failures must be observable

> "Registration failures should be observable (structured logging /
>    telemetry), not silent — see BUD Section 10, \"Limited observability\"
>    as a known platform risk."  

Relation to GOAR-4:
- GOAR-4 is primarily a data integrity/rollback fix; the existing `register_printer` behavior already raises a `RegistrationError` and logs events via `printer.log(...)` when the Welcome Page fails. This satisfies the basic observability expectation that failures are not silent. The current implementation does not add new structured logging fields specific to capability rollback, but the presence of an exception and printer logs means the failure path is at least visible.

## 4. Original Acceptance Criteria

(From `jira_context/GOAR-4_live.md`, copied verbatim.)

1. "When Welcome Page printing fails, no printer record remains."
2. "When Welcome Page printing fails, no capability record remains for that
printer_id."
3. "When Welcome Page printing fails, the serial number is free to be
registered again from scratch."
4. "Successful registrations are unaffected (do not regress)."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

### 5.1. Capability rollback must be idempotent

**Requirement statement**  
If `_rollback_registration` is called multiple times for the same `printer.printer_id` (e.g., due to repeated error handling or retries), the combined effect must still satisfy Rule 2: no printer record, capability record, or serial index may remain for that serial number, and no additional errors should be raised solely because the records have already been deleted.

**Justification**  
- Edge case category: rollback/partial-failure behaviour.
- Supported by Rule 2’s sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."  
This requirement extends Rule 2 to repeated-rollback scenarios, ensuring that rollback logic is robust and idempotent.

### 5.2. Capability rollback must be scoped to the failing registration’s printer_id

**Requirement statement**  
`_rollback_registration` must only delete capabilities associated with the specific `printer.printer_id` passed to it. Under no circumstances may rollback delete capability records for other printers, even if they share the same model number or other attributes.

**Justification**  
- Edge case category: ownership conflicts.
- Supported by Rule 2’s sentence: "no partial data (printer record, capability record, serial index, etc.) may be retained."  
This rule demands removal of partial data for the failed registration but does not authorize deletion of unrelated printers’ data. Scoping rollback to `printer.printer_id` ensures data belonging to other printers/owners is not accidentally removed.

### 5.3. Serial index rollback must fully free the serial for reuse

**Requirement statement**  
After `_rollback_registration` executes for a failed registration, subsequent calls to `register_printer` with the same `serial_number` must behave exactly as a first-time registration (i.e., `store.get_printer_by_serial(serial_number)` returns no printer, and a new `Printer` record is created), with no residual indexing or references preventing reuse.

**Justification**  
- Edge case category: repeated operations.
- Exact rule sentence: "no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
- Also directly aligned with AC #3: "When Welcome Page printing fails, the serial number is free to be registered again from scratch."  
This requirement makes explicit that serial index cleanup must be complete enough that the entire registration flow behaves as "from scratch" for that serial number.

### 5.4. Rollback must not change the state of already-claimed printers unrelated to the failing registration

**Requirement statement**  
When `_rollback_registration` is invoked for a failed registration attempt, it must not delete capabilities, printer records, or serial indices for any printer that is already in a `CLAIMED` state and is not the printer being rolled back. Rollback must be limited strictly to the printer and serial number associated with the failed registration attempt.

**Justification**  
- Edge case category: ownership conflicts.
- Exact rule sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)  
While GOAR-4’s main focus is failed registrations before a printer is fully registered/claimed, Rule 11 requires that registration flows (including rollback logic) do not inadvertently disturb existing owners’ claims. Limiting rollback to the printer associated with the failure ensures that claimed printers’ data and claims are not silently removed or altered.

### 5.5. Successful registration must never invoke rollback

**Requirement statement**  
On a successful registration (Welcome Page prints without raising `WelcomePagePrintError`), `_rollback_registration` must not be called, and no deletion of printer, capabilities, or serial index may occur as part of the normal success path.

**Justification**  
- Edge case category: post-deregistration state is not applicable here; focus is on separation of success and failure paths.
- Exact rule sentence: "Registration is successful **only if** the Welcome/Info Page prints." (Rule 1)  
- Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data ... may be retained." (Rule 2)  
These rules together imply a clear bifurcation: success (after Welcome Page) should preserve data; failure (before Welcome Page) requires rollback. This requirement ensures GOAR-4’s rollback enhancements do not inadvertently affect successful registration flows, reinforcing AC #4.

### 5.6. Capability records for failed registrations must not be externally visible

**Requirement statement**  
Any capability records created during a registration attempt that ultimately fails before the Welcome Page prints must be deleted by `_rollback_registration` before they can be used or surfaced by downstream services (e.g., capability queries, device lists), so that no external system can observe or act on a capability record for a printer that did not successfully register.

**Justification**  
- Edge case category: rollback/partial-failure behaviour.
- Exact rule sentence: "no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
- Exact rule sentence: "Deregistration must remove all cloud associations and printer data (GDPR compliance)." (Rule 12)  
This requirement combines Rule 2’s prohibition on partial data with Rule 12’s GDPR framing to ensure that temporary capability records from failed registrations are removed promptly and do not become externally visible or actionable.

## 6. Flagged Conflicts

None identified. The original acceptance criteria are consistent with Rules 1, 2, 4, 12, and 14 as literally stated. The implementation in `_rollback_registration` matches the ticket’s rollback intent and does not conflict with any cited rule.

## 7. Open Questions

### 7.1. Diff/implementation mismatch for GOAR-4

**Question**  
Why is `reports/GOAR-4_diff.txt` empty when the Jira Validation Report explicitly states that the diff adds `store.delete_capabilities(printer.printer_id)` to the rollback path, and the current implementation of `_rollback_registration` in `app/registration.py` already includes this call?

**Why it is unresolvable from available inputs**  
- The diff file in the repository contains no content, so it cannot be used to confirm what changed for GOAR-4.
- The Jira Validation Report describes a change that is already present in the implementation, but does not clarify whether this was committed in a different change set or if the diff file is incomplete.

**Downstream agents that must exclude this from scoring**  
- Agents responsible for diff-based validation (e.g., scenario design and test generation that rely on the diff as ground truth) must not assume the empty diff is authoritative for GOAR-4.

### 7.2. Timing and atomicity of capability deletion vs. other rollback steps

**Question**  
Must `_rollback_registration` guarantee a specific order or atomic transaction semantics when deleting the printer record, serial index, and capabilities (e.g., all-or-nothing behavior if one deletion fails), or is best-effort deletion sufficient as long as no partial data remains under normal conditions?

**Why it is unresolvable from available inputs**  
- The business rules state "no partial data ... may be retained" but do not specify transactional guarantees or failure-handling for the rollback itself.
- The current implementation calls three separate store methods (`delete_printer`, `remove_serial_index`, `delete_capabilities`) without explicit transaction management, and the Jira ticket doesn’t address failure modes for the rollback operations themselves.

**Downstream agents that must exclude this from scoring**  
- Agents designing failure-injection or transactional-rollback tests should not assume atomicity or a required order of operations until product owners clarify the desired guarantees.

### 7.3. Observability requirements specifically for orphan cleanup

**Question**  
Should there be explicit structured logging or telemetry events when `_rollback_registration` deletes orphaned capability records (e.g., fields for `printer_id`, `serial_number`, and an indicator that a partial registration was cleaned up), beyond the existing `RegistrationError` and printer logs?

**Why it is unresolvable from available inputs**  
- Rule 14 requires registration failures to be observable, but does not prescribe the granularity or specific fields for logging capability deletion.
- The Jira ticket and diff do not mention logging changes; they focus solely on data cleanup.

**Downstream agents that must exclude this from scoring**  
- Agents scoring log/telemetry-related behavior must not assume specific structured log fields or metrics for capability deletion are required; they should focus on data-state correctness unless new logging requirements are defined.

### 7.4. Scope of GDPR concerns for capability records

**Question**  
Do printer capability records alone (without an associated printer record) constitute personal or device-identifying information under GDPR for this platform, and are there additional compliance requirements (e.g., retention windows, anonymization) that should be applied specifically to capabilities beyond simply deleting them on rollback?

**Why it is unresolvable from available inputs**  
- Rule 12 references "GDPR compliance" in the context of deregistration, but does not define GDPR expectations for failed registrations or isolated capability records.
- The Jira ticket states that orphaned capability records are a "GDPR compliance concern" but does not elaborate on whether additional safeguards (beyond deletion on rollback) are required.

**Downstream agents that must exclude this from scoring**  
- Agents focusing on GDPR and broader compliance behaviors must not assume additional requirements (e.g., audit logging, data export) for capability records beyond what is explicitly stated; they should limit validation to verifying that capability records are deleted on rollback.
