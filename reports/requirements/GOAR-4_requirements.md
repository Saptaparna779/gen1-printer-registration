# Requirements Report — GOAR-4

## 1. Summary

Failed registrations that abort at the Welcome Page print step were leaving behind orphaned capability records (and potentially other partial state) in the store. Specifically, when registration fails with `simulate_welcome_page_failure=True`, the printer record was removed but the associated capability record for that `printer_id` was not, violating the rollback business rule that prohibits retention of partial registration data. The fix ensures that `_rollback_registration()` removes all partial state created during registration for that printer: the printer record, its capabilities, and the serial index, so that no orphaned capability records remain and the serial number can be registered again from scratch. Successful registrations are unaffected.

## 2. Affected Components

- `app/registration.py`
  - Function `register_printer(...)`
    - Uses the `simulate_welcome_page_failure` flag to trigger rollback via `_rollback_registration(printer)` when `generate_and_print_welcome_page` raises `WelcomePagePrintError`.
  - Function `_rollback_registration(printer: Printer) -> None`
    - Rollback logic updated to delete capabilities:
      - `store.delete_printer(printer.printer_id)`
      - `store.remove_serial_index(printer.serial_number)`
      - `store.delete_capabilities(printer.printer_id)` (newly added cleanup ensuring no orphaned capability record remains).

- Store interactions (indirect, via `app.store`):
  - `store.delete_printer(printer.printer_id)` — printer record removal.
  - `store.remove_serial_index(printer.serial_number)` — serial index removal.
  - `store.delete_capabilities(printer.printer_id)` — capability record removal for the failed registration.

## 3. Applicable Business Rules

**Rule 1 — Registration success condition**

- Exact sentence: "Registration is successful **only if** the Welcome/Info Page prints."
- Relation to this ticket: This rule defines the boundary between success and failure for registration. GOAR-4 concerns the failure path when the Welcome Page does not print (e.g., via `simulate_welcome_page_failure=True`), so this rule establishes that such a scenario must be treated as a failed registration, triggering rollback rather than partial success.

**Rule 2 — Rollback on failure / no partial data retention**

- Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
- Relation to this ticket: This is the core rule GOAR-4 enforces. The Jira description explicitly references this rule and describes a violation: capability records remaining after a failed registration. The fix to `_rollback_registration()` ensures that printer record, capability record, and serial index are all removed when the Welcome Page fails to print, aligning implementation with this rule.

**Rule 4 — Capabilities captured at registration**

- Exact sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."
- Relation to this ticket: This rule explains why capability records exist and why orphaned capability records are problematic. If a capability record exists without a corresponding printer record, downstream services might incorrectly treat the printer as present or usable based solely on capabilities, which contradicts the intended model. GOAR-4 ensures capability records are cleaned up when registration fails, keeping capabilities aligned with actual registered printers.

**Rule 12 — Deregistration and GDPR compliance**

- Exact sentence: "Deregistration must remove all cloud associations and printer data (GDPR compliance)."
- Relation to this ticket: While GOAR-4 focuses on failed registration rollback rather than explicit deregistration, the Jira ticket notes "Impact: High -- orphaned records are a GDPR compliance concern." This mirrors Rule 12's rationale that incomplete data removal poses GDPR risks. GOAR-4's fix reduces such risk on the failure path by ensuring no partial registration data (including capabilities) remains for an unregistered printer, consistent with the same compliance intent.

**Rule 14 — Observability of registration failures**

- Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
- Relation to this ticket: Although GOAR-4’s diff focuses on rollback cleanup rather than logging, the failure path in `register_printer` raises `RegistrationError` after rollback when the Welcome Page fails. This contributes to making registration failures observable to callers and systems, in line with Rule 14. No new logging is added by GOAR-4, but the error propagation and rollback behavior remain consistent with this rule.

## 4. Original Acceptance Criteria

Copied from `jira_context/GOAR-4_live.md`:

- "When Welcome Page printing fails, no printer record remains."
- "When Welcome Page printing fails, no capability record remains for that printer_id."
- "When Welcome Page printing fails, the serial number is free to be registered again from scratch."
- "Successful registrations are unaffected (do not regress)."

## 5. Adopted Additional Requirements

### 5.1 Requirement: Capability cleanup must occur for every rollback invocation, not only when capabilities were created in the current attempt

- Requirement statement:
  - When `_rollback_registration(printer)` is invoked due to failure before the Welcome Page prints, it must call `store.delete_capabilities(printer.printer_id)` regardless of whether capabilities were created during the current registration attempt or were already on record, ensuring that no capabilities remain associated with a printer that failed to complete registration.

- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - Explanation: Rule 2 explicitly lists "capability record" as data that must not be retained when registration fails before the Welcome Page prints. The existing implementation may sometimes skip capability capture if `store.get_capabilities(printer_id)` already returns a record, which means failed registrations could leave a pre-existing capability record associated with a printer that did not successfully register in this attempt. Applying `store.delete_capabilities(printer.printer_id)` unconditionally in rollback ensures that any capability record tied to the printer is removed, satisfying the "no partial data" requirement even in cases where capabilities predated the failed attempt. Edge case category: boundary value / repeated-operation check (handling both first-time and re-registration attempts identically on failure).

### 5.2 Requirement: Rollback must occur for all failures before the Welcome Page prints, not only simulated failures

- Requirement statement:
  - Any failure that occurs before the Welcome Page prints — whether triggered by `simulate_welcome_page_failure=True` or by a real `WelcomePagePrintError` or other exceptions in the Welcome Page generation/printing step — must invoke `_rollback_registration(printer)` and result in the removal of printer record, capability record, and serial index, leaving no partial registration data behind.

- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
  - Explanation: The Jira ticket describes steps using `simulate_welcome_page_failure=True` as a reproducible scenario, but the business rule applies to any failure before the Welcome Page prints, not just simulation flags. Ensuring rollback for real-world failures (e.g., printer offline, page generation errors, transport failures) is necessary to uphold Rule 2 across all paths, not solely the artificial test path. Edge case category: error state / rollback behavior.

### 5.3 Requirement: Serial index must be removed for both initial registration and re-registration failures

- Requirement statement:
  - When registration or re-registration fails before the Welcome Page prints, `_rollback_registration(printer)` must call `store.remove_serial_index(printer.serial_number)` so that the serial number can be used to register again from scratch, regardless of whether the failing attempt was an initial registration or a re-registration.

- Justification:
  - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
  - Jira acceptance criterion: "When Welcome Page printing fails, the serial number is free to be registered again from scratch."
  - Explanation: The existing implementation already calls `store.remove_serial_index(printer.serial_number)` within `_rollback_registration`. This requirement makes explicit that removal must occur for any failed attempt, including re-registration, so that the serial number is not blocked by stale index entries. This aligns with Rule 2’s explicit mention of "serial index" as data that must be rolled back and mirrors the Jira AC about serial number reuse. Edge case category: boundary value / repeated-operation check.

### 5.4 Requirement: Rollback must not alter claimed printers outside the failure path defined by Rule 2

- Requirement statement:
  - `_rollback_registration(printer)` must only be invoked for registration attempts that have not yet reached a successful Welcome Page print. It must not be used as a general cleanup mechanism for already claimed printers or other lifecycle events; deletion of printer, capabilities, and serial index through rollback must be limited to failure-before-Welcome-Page scenarios.

- Justification:
  - Exact rule sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)
  - Explanation: While GOAR-4 is focused on failed registrations, the rollback function deletes core printer data, including capabilities and serial index. Misuse of rollback outside the failure-before-Welcome-Page context (e.g., calling `_rollback_registration` for a claimed printer instead of using proper deregistration) could silently remove an owner’s claim, conflicting with Rule 11. This requirement constrains rollback usage to the context described by Rule 2, protecting claimed printers and ensuring that ownership is not inadvertently wiped out. Edge case category: ownership.

## 6. Open Questions

### 6.1 Orphaned printer_email_id and XMPP node on failed registrations

- The question:
  - On a registration failure before the Welcome Page prints, should `_rollback_registration(printer)` also remove or invalidate any associated `printer_email_id` index entries and XMPP node assignments created earlier in the registration flow, to ensure no partial cloud identity remains?

- Why it cannot be resolved from available inputs:
  - Business rules explicitly mention that "no partial data (printer record, capability record, serial index, etc.) may be retained" (Rule 2), but do not specify whether email indices or XMPP node assignments count as "partial data" that must be removed on rollback. The current implementation’s `_rollback_registration` removes only the printer record, serial index, and capabilities, and does not interact with email indexing or XMPP node deallocation. The Jira ticket for GOAR-4 focuses specifically on orphaned capability records and serial reuse, not on email or XMPP cleanup.

- What downstream agents must exclude from scoring:
  - Any tests or scoring that assume email indices and XMPP nodes are removed on rollback must be excluded until product owners clarify whether these elements are in scope for Rule 2’s "no partial data" requirement.

### 6.2 Behavior when capabilities pre-exist before a failed re-registration

- The question:
  - If a printer already has a capability record from a past successful registration, and a subsequent re-registration attempt fails before the Welcome Page prints, should `_rollback_registration(printer)` delete the existing capabilities, or should they remain because the printer was previously successfully registered?

- Why it cannot be resolved from available inputs:
  - Rule 2 mandates that "no partial data (printer record, capability record, serial index, etc.) may be retained" for the failing registration attempt. However, it does not clearly distinguish between data created in the current attempt versus data created during earlier successful registrations. The current implementation unconditionally calls `store.delete_capabilities(printer.printer_id)`, which would remove pre-existing capabilities even if they originated from a prior success. The Jira ticket’s description targets orphaned capability records from failed registrations but does not explicitly address the re-registration-with-existing-data scenario.

- What downstream agents must exclude from scoring:
  - Tests and scoring that rely on a specific interpretation (e.g., always deleting historical capabilities on any failed re-registration vs. preserving them) must be excluded. Downstream agents should focus only on the clear case: no capabilities remain for a printer that has just failed its registration and has no prior successfully registered state represented in the store.

### 6.3 GDPR expectations for logging and audit trail on rollback

- The question:
  - Are there explicit GDPR or compliance requirements for logging rollback operations (e.g., structured audit logs for deletion of printer records, capabilities, and serial indices), beyond the logical cleanup enforced by GOAR-4?

- Why it cannot be resolved from available inputs:
  - Rule 12 ties deregistration to GDPR compliance, and the Jira ticket notes that orphaned records are a "GDPR compliance concern," but neither the ticket nor `docs/business_rules.md` specify the required level of logging or auditing for rollback actions. The current implementation logs registration events through `printer.log(...)` and raises `RegistrationError`, but no explicit compliance logging for deletions is described.

- What downstream agents must exclude from scoring:
  - Any tests or scoring that assume specific audit logging structures or compliance evidence (e.g., log schemas, retention policies) for rollback actions must be excluded until governance or compliance teams specify these requirements.

