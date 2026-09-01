# Requirements Report — GOAR-5

## 1. Summary

Re-registering an already-claimed printer (same serial number) was silently wiping out ownership and claim state by overwriting the existing printer record: `owner_user_id` was cleared, status was reset from CLAIMED to REGISTERED, and prior registration history was lost. This matters because it causes printers to disappear from HP Smart and breaks subscription services like Instant Ink, violating the ownership protection business rule. The current implementation in `register_printer()` now reuses the existing printer record on re-registration, preserves `owner_user_id` and CLAIMED status, and ensures rollback on Welcome Page failure does not leave the printer in a partially updated or unclaimed state.

## 2. Affected Components

- app/registration.py — `register_printer()`, the core registration/re-registration flow for printers, reached via the POST `/printers/register` endpoint (per app/main.py, not shown in this context). This function:
  - Validates `serial_number`, `model_number`, and `firmware_version`.
  - Uses `store.get_printer_by_serial(serial_number)` to decide whether to create a new `Printer` or reuse an existing one.
  - For existing printers, updates `model_number` and `firmware_version` on the same `Printer` instance instead of creating a new record, and crucially:
    - Sets `printer.status = PrinterStatus.REGISTERED` **only if** `printer.status != PrinterStatus.CLAIMED`, so already-claimed printers remain CLAIMED after re-registration.
    - Does not clear or modify `owner_user_id`, so ownership is preserved across re-registration.
  - Always generates a new `cloud_id` and `printer_email_id` on registration, re-indexes the email, and generates a new claim code **only when** `status != CLAIMED`.
  - Performs capability capture and XMPP assignment, then prints the Welcome Page; on success, it sets status to REGISTERED only for non-CLAIMED printers.

- app/registration.py — `_rollback_registration(printer)`, invoked when `generate_and_print_welcome_page` raises `WelcomePagePrintError`. For any registration (including re-registration of claimed printers), this helper:
  - Deletes the printer record (`store.delete_printer(printer.printer_id)`).
  - Removes the serial index (`store.remove_serial_index(printer.serial_number)`).
  - Deletes capabilities (`store.delete_capabilities(printer.printer_id)`).
  This enforces the business rule that no partial data is retained if the Welcome Page fails to print.

The diff file `reports/GOAR-5_diff.txt` contains only generated tests (`tests/GOAR-5/test_GOAR-5_generated.py`) and no direct code changes under `app/`. The behavioral change for GOAR-5 is already present in `app/registration.py` (the conditional status update and claim-code guard). The discrepancy is that the diff shows only test additions, while the implementation contains the fix logic; this is noted here as an implementation–diff mismatch.

## 3. Applicable Business Rules

1. Rule 11 — Claiming & Ownership — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - This rule directly governs GOAR-5: the bug described in the ticket was that re-registration silently wiped out `owner_user_id` and RESET the CLAIMED status to REGISTERED. The current implementation respects this rule by preserving `owner_user_id` and retaining CLAIMED status during re-registration, and by avoiding any reassignment of claim state.

2. Rule 9 — Claiming & Ownership — "A printer becomes visible to a user's applications only after a successful claim."
   - This rule explains the impact described in the ticket: when re-registration un-claimed the printer, it stopped being visible in HP Smart and similar applications. Ensuring that re-registration retains CLAIMED status and `owner_user_id` preserves the visibility guaranteed by this rule.

3. Rule 2 — Registration — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - This rule is relevant because GOAR-5 must also ensure that a failed re-registration attempt for a claimed printer does not leave the printer in a partially updated or unclaimed state. `_rollback_registration()` deletes the printer record and associated indices/capabilities, ensuring that a failure before the Welcome Page prints results in a clean rollback.

4. Rule 3 — Registration — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - This rule bears on the Cloud ID behavior during re-registration. The implementation in `register_printer()` assigns `printer.cloud_id = _generate_cloud_id()` on every registration call, including re-registration of claimed printers, thereby complying with this rule while still preserving ownership.

5. Rule 6 — Cloud ID, Printer Email ID & Claim Code — "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - This rule reinforces Rule 3's requirement for Cloud ID regeneration and uniqueness. The current implementation generates a fresh Cloud ID on each registration and does so without affecting `owner_user_id` or CLAIMED status, which is central to GOAR-5.

6. Rule 8 — Cloud ID, Printer Email ID & Claim Code — "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."
   - This rule is relevant because the implementation only generates a new claim code if `printer.status != PrinterStatus.CLAIMED`, preventing a new claim code being printed for an already-claimed printer. This helps avoid multiple active claim codes for the same device and protects existing ownership, aligning with the one-time-use requirement.

7. Rule 14 — Non-Functional Expectations — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - This rule underpins the need for logging around registration failures and, by extension, re-registration and rollback behavior. While the code uses `printer.log(...)` and the Welcome Page error propagates via `RegistrationError`, the specific audit logging schema for ownership changes is not fully visible, and is treated as partially open.

## 4. Original Acceptance Criteria

Re-registering an already-claimed printer does not clear owner_user_id.
Re-registering an already-claimed printer does not reset status away
from CLAIMED.
Registration history is preserved (appended to, not replaced).
First-time registration of a genuinely new serial number is unaffected.

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Re-registering an already-claimed printer must not generate a new Claim Code or modify the existing claim code state.
   - Justification: Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." and Rule 8 — "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once." Generating and printing a new claim code for a CLAIMED printer during re-registration could enable a second user to claim the same device or otherwise interfere with the existing owner’s claim. The implementation’s guard `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()` should be treated as required behaviour and explicitly tested.

2. Re-registering an already-claimed printer must still generate a new Cloud ID and Printer Email ID, without affecting ownership.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." The implementation already regenerates Cloud ID and printer email ID on every registration call. This requirement makes explicit that this must hold for CLAIMED printers, while `owner_user_id` and CLAIMED status remain unchanged, so that identity refresh does not disturb ownership.

3. If re-registration of a claimed printer fails before the Welcome Page prints (e.g., due to `WelcomePagePrintError`), the rollback must restore or preserve the prior claimed state, ensuring `owner_user_id`, status, and any pre-existing history remain exactly as before the attempted re-registration.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." combined with Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." For claimed printers, rollback must not only remove partial new data but also avoid wiping or altering the existing claim; tests should verify that failed re-registrations leave the claimed printer’s ownership fields unchanged.

4. Re-registering a printer that is not claimed (status != CLAIMED) must behave as a normal registration: generate a new Cloud ID, Printer Email ID, and Claim Code, assign an XMPP node if needed, and end with status REGISTERED on successful completion.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 7/8 — "Printer Email ID: must be globally unique; used for Email-to-Print." / "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once." This requirement clarifies that the special-casing for CLAIMED printers (no new claim code and no status reset) must not alter the expected onboarding behaviour for non-claimed printers, ensuring that first-time and subsequent non-claimed registrations produce new identities and claim codes as normal.

5. Multiple successful re-registrations of the same claimed printer must produce distinct Cloud IDs and Printer Email IDs over time while preserving `owner_user_id` and CLAIMED status.
   - Justification: Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." and Rule 7 — "Printer Email ID: must be globally unique; used for Email-to-Print." This is a repeated-operation and boundary-value edge case: regenerating identifiers must not only produce values different from the immediately previous ones, but must ensure uniqueness across multiple re-registrations for the same printer, with ownership unaffected.

6. Failed re-registration attempts (for both claimed and non-claimed printers) must not persist any newly generated Cloud ID or Printer Email ID; subsequent successful registrations must still generate fresh identifiers.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This requirement clarifies that any identifiers generated during a failed registration attempt must be rolled back along with the printer record and indices, and must not be reused or left attached to the printer in store.

7. Audit or operational logs for re-registration of claimed printers should include structured fields indicating the printer was already claimed (status prior to re-registration) and that ownership was preserved (same `owner_user_id` before and after), and should record any registration failures affecting claimed printers.
   - Justification: Rule 14 — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." While Rule 14 is framed around failures, re-registration of CLAIMED printers has high customer-impact risk; structured logging of these events (including ownership metadata) improves observability and supports incident investigation.

## 6. Flagged Conflicts

None identified. As currently written, the acceptance criteria and the cited business rules can both hold:
- The implementation preserves CLAIMED status and `owner_user_id` during re-registration, satisfying the first two acceptance criteria and Rule 11.
- It generates new Cloud IDs for all registrations, including re-registrations, as required by Rules 3 and 6.
- Claim codes are not regenerated for CLAIMED printers, which is consistent with Rule 8’s one-time-use semantics and the intent of preserving ownership.

The acceptance criterion that \"Registration history is preserved (appended to, not replaced)\" cannot be fully validated from `app/registration.py` alone, because history persistence appears to depend on `printer.log(...)` and the underlying `store` implementation, which is not visible here. This is treated as an open question rather than a conflict.

## 7. Open Questions

1. How is \"registration history\" defined and persisted, and does re-registration of a claimed printer append to history rather than replacing or truncating existing entries?
   - Why it is unresolvable: The Jira ticket requires that \"Registration history is preserved (appended to, not replaced),\" but `app/registration.py` only shows `printer.log(...)` calls and does not reveal how logs/history are stored or whether prior entries are retained. The `store` implementation and any persistent audit/history layer are not in scope for this analysis.
   - Downstream agents to exclude from scoring: Scenario designers and test generators (Agents 2–4) and automated test validators (Agents 5–6) must not treat specific registration-history semantics as verified; they should avoid failing tests based solely on assumptions about history append vs. replace behaviour.

2. Should re-registration of claimed printers emit explicit, structured log events indicating ownership preservation (fields for previous and new status and `owner_user_id`)?
   - Why it is unresolvable: Rule 14 mandates observability of registration failures but does not explicitly require structured logging for successful re-registrations of claimed printers. The current implementation logs generic registration progress messages without explicit ownership metadata. The Jira ticket does not specify logging schema, so we cannot assert that more detailed logging is required.
   - Downstream agents to exclude from scoring: Agents focusing on non-functional observability and audit logging must not mark the absence of ownership-specific structured logs as a defect without additional human clarification.

3. What precise behaviour is expected when a printer transitions through first-time registration (unclaimed) → claim → one or more re-registrations, particularly regarding claim-code retention and reuse across that lifecycle?
   - Why it is unresolvable: The acceptance criteria state that first-time registration of a new serial number is unaffected and that re-registration must preserve ownership, but do not spell out claim-code lifecycle semantics beyond Rule 8’s one-time-use guarantee. The implementation retains the original claim code for claimed printers and does not generate a new one; whether this is the long-term intended behaviour (e.g., claim code remaining visible in GET responses) is not explicitly documented.
   - Downstream agents to exclude from scoring: Agents designing lifecycle and repeated-operation scenarios must avoid assuming additional claim-code behaviours (such as hiding claim codes after claim, or rotating claim codes on re-registration) beyond what is explicitly specified.
