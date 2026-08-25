# Requirements Report — GOAR-5

## 1. Summary

Re-registering an already-claimed printer (same serial number) was silently wiping out ownership and claim state by overwriting the existing printer record: `owner_user_id` was cleared, status was reset from CLAIMED to REGISTERED, and prior registration history was lost. This matters because it causes printers to disappear from HP Smart and breaks subscription services like Instant Ink, violating the ownership protection business rule. The underlying implementation now updates existing printer records on re-registration without changing their CLAIMED status or owner_user_id, and relies on claim-side logic to append history rather than replace it.

## 2. Affected Components

- app/registration.py — `register_printer()`, the core registration/re-registration flow reached via the onboarding endpoint (per app/main.py, not shown in this diff). The function updates existing `Printer` records when `store.get_printer_by_serial(serial_number)` returns a printer and ensures that status and ownership are not reset for already-claimed printers.
  - The implementation sets `printer.status` to `PrinterStatus.REGISTERED` only if `printer.status != PrinterStatus.CLAIMED`, leaving CLAIMED printers unchanged at the end of registration.
  - For existing printers, the function reuses the same `Printer` instance and does not null out `owner_user_id`, so ownership is preserved.
- app/registration.py — `_rollback_registration()`, called when the Welcome Page fails to print, ensures no partial registration data is retained on failure, consistent with rollback rules; this indirectly affects re-registration safety but is not directly changed by this ticket.

The diff file reports/GOAR-5_diff.txt is currently empty in the repository, so there is no machine-readable diff content to compare. All conclusions above are drawn directly from the current implementation in app/registration.py and the Jira ticket description. This is a discrepancy between the ticket comment (which references a prepared diff) and the repository contents.

## 3. Applicable Business Rules

1. Rule 11 — Claiming & Ownership — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - This rule directly governs the bug described in the ticket: re-registration was silently wiping the owner_user_id and claim status. The current implementation preserves CLAIMED status and does not clear owner_user_id during re-registration, aligning register_printer() with this rule.

2. Rule 9 — Claiming & Ownership — "A printer becomes visible to a user's applications only after a successful claim."
   - This rule explains why wiping owner_user_id and claim status is so damaging: once the printer is no longer CLAIMED, it disappears from HP Smart and similar applications. Ensuring that re-registration does not de-claim the printer preserves the visibility guarantee implied by this rule.

3. Rule 2 — Registration — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - This rule is relevant because re-registration of a claimed printer must either fully succeed (preserving ownership) or roll back completely if the Welcome Page fails, ensuring there is no partial state where ownership is lost but registration changes are partially applied.

4. Rule 14 — Non-Functional Expectations — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - This rule bears on the need to log notable events around re-registration of claimed printers, including any failures or unusual state changes, so ownership-impacting events are traceable.

## 4. Original Acceptance Criteria

Re-registering an already-claimed printer does not clear owner_user_id.
Re-registering an already-claimed printer does not reset status away
from CLAIMED.
Registration history is preserved (appended to, not replaced).
First-time registration of a genuinely new serial number is unaffected.

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Re-registering an already-claimed printer must not generate a new Claim Code or modify the existing claim code state.
   - Justification: Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Generating and printing a new claim code for a CLAIMED printer during re-registration could enable a second user to claim the same device or otherwise interfere with existing ownership, so the implementation condition `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()` should be treated as required behaviour.

2. Re-registering an already-claimed printer must still generate a new Cloud ID and Printer Email ID, without affecting ownership.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." The current implementation always assigns a new `cloud_id` and `printer_email_id` on registration, regardless of claim status. Tests should explicitly cover that CLAIMED printers receive new Cloud IDs and email IDs on re-registration while owner_user_id and status remain unchanged.

3. If re-registration of a claimed printer fails before the Welcome Page prints (e.g., due to `WelcomePagePrintError`), the rollback must not alter the existing claimed printer's owner_user_id, status, or prior registration history.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." combined with Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." When re-registering a claimed printer, rollback must restore the previous, fully-claimed state, not leave the printer unclaimed or in a partially updated state.

4. Re-registering a printer that is not claimed (status != CLAIMED) must continue to behave as a normal registration: generate a new Cloud ID, Printer Email ID, and Claim Code, and set status to REGISTERED on successful completion.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 8 — "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once." This proposed requirement clarifies that the special handling for CLAIMED printers must not change the expected behaviour for unclaimed/REGISTERED printers, ensuring first-time and subsequent non-claimed registrations still issue claim codes and maintain normal onboarding semantics.

5. Audit logs for re-registration of a claimed printer must include the printer_id, serial_number, previous status, new status, and a flag indicating that the printer was already claimed.
   - Justification: Rule 14 — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." Although Rule 14 is framed around failures, re-registration of CLAIMED printers has direct customer-impacting risk; logging these events with structured metadata improves observability and supports investigation of any future ownership issues.

## 6. Flagged Conflicts

None identified. The current implementation of register_printer() can satisfy the original acceptance criteria while complying with the cited business rules:
- It preserves owner_user_id and CLAIMED status by only setting status to REGISTERED when the printer is not already CLAIMED.
- It generates a new Cloud ID on every registration call, as required by Rules 3 and 6, without changing ownership.

The Jira acceptance criterion that "Registration history is preserved (appended to, not replaced)" cannot be fully verified from app/registration.py alone, because history persistence appears to be handled via `printer.log(...)` and the underlying `store` implementation, which are outside the inspected code. This is treated as an open question rather than a direct conflict.

## 7. Open Questions

1. How exactly is \"registration history\" defined and persisted, and does the current implementation append to history rather than replacing it during re-registration of claimed printers?
   - Why it is unresolvable: The Jira ticket requires that \"Registration history is preserved (appended to, not replaced),\" but app/registration.py only shows `printer.log(...)` calls without exposing how logs are stored or whether prior entries are retained. The `store` implementation and any audit/history components are not included in the current context, so we cannot confirm compliance.
   - Downstream agents to exclude from scoring: Scenario designers (Agent 2), test case generators (Agents 3–4), and automated test runners (Agents 5–6) must not treat history-append behaviour as verified or required beyond the logging calls visible here; they should not fail tests solely on assumptions about history persistence.

2. Should re-registration of a claimed printer emit explicit, structured log events indicating that ownership was preserved (e.g., fields showing owner_user_id before and after, and status remaining CLAIMED)?
   - Why it is unresolvable: Rule 14 requires observable failures, but does not explicitly mandate logging for successful re-registrations, even when they affect claimed printers. The current implementation logs "Re-registration started" and \"Welcome page printed successfully; registration complete\" but does not include explicit ownership-related fields. Without additional logging requirements in the Jira ticket or business rules, we cannot assert that more detailed logging is mandatory.
   - Downstream agents to exclude from scoring: Agents responsible for non-functional logging/telemetry tests (primarily scenario and test designers focusing on observability) should not mark the absence of ownership-specific logs as a failure without human clarification.

3. What, if any, additional behaviours are expected when \"First-time registration of a genuinely new serial number is unaffected\" for printers that later become claimed and are then re-registered?
   - Why it is unresolvable: The acceptance criterion mentions first-time registration being unaffected, but does not clarify whether there are special cases for printers that go through the sequence: first-time registration → claim → re-registration. The current implementation appears to handle this correctly (reusing the same Printer object, preserving ownership), but the AC does not specify detailed expectations for this lifecycle.
   - Downstream agents to exclude from scoring: Agents designing lifecycle or multi-step scenario tests should not assume additional constraints beyond those explicitly stated; they should avoid failing tests based on speculative expectations about this lifecycle.
