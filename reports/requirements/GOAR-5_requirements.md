# Requirements Report — GOAR-5

## 1. Summary

Re-registering an already-claimed printer (same serial number) was silently wiping out ownership and claim state by overwriting or resetting the existing printer record: `owner_user_id` was cleared, status was reset from CLAIMED to REGISTERED, and prior registration history appeared lost at the API surface. This causes printers to disappear from HP Smart and breaks subscription services like Instant Ink, violating the ownership protection business rule. The current implementation in `register_printer()` now reuses the existing printer record on re-registration, preserves `owner_user_id` and CLAIMED status, regenerates Cloud ID and Printer Email ID as required, and ensures rollback on Welcome Page failure does not leave the printer in a partially updated or unclaimed state.

## 2. Affected Components

- app/registration.py — `register_printer()`, the core registration/re-registration flow for printers, reached via the POST `/printers/register` endpoint (per app/main.py, not shown in this context). This function:
  - Validates `serial_number`, `model_number`, and `firmware_version`.
  - Uses `store.get_printer_by_serial(serial_number)` to decide whether to create a new `Printer` or reuse an existing one.
  - For existing printers (including already-claimed ones), updates `model_number` and `firmware_version` on the same `Printer` instance instead of creating a new record and:
    - Always generates a new `cloud_id` (`printer.cloud_id = _generate_cloud_id()`) and a new `printer_email_id` on every call.
    - Indexes the email via `store.index_email(printer.printer_email_id, printer_id)`.
    - Generates a new claim code **only if** `printer.status != PrinterStatus.CLAIMED`, leaving the existing claim code unchanged for claimed printers.
    - After successful Welcome Page printing, sets `printer.status = PrinterStatus.REGISTERED` **only if** `printer.status != PrinterStatus.CLAIMED`; already-claimed printers remain CLAIMED.
  - Logs registration progress via `printer.log(...)` but does not explicitly modify `owner_user_id` during re-registration, so ownership remains as previously set by `claim_printer()`.

- app/registration.py — `_rollback_registration(printer)`, invoked when `generate_and_print_welcome_page` raises `WelcomePagePrintError`. For any registration (including re-registration of claimed printers), this helper:
  - Deletes the printer record (`store.delete_printer(printer.printer_id)`).
  - Removes the serial index (`store.remove_serial_index(printer.serial_number)`).
  - Deletes capabilities (`store.delete_capabilities(printer.printer_id)`).
  This enforces the business rule that no partial data is retained if the Welcome Page fails to print. However, it also removes any existing claimed record for that printer ID; the ticket and rules do not clarify whether rollback during re-registration of an already-claimed printer should instead restore the prior claimed record rather than deleting it.

- tests/GOAR-5/test_GOAR-5_generated.py — generated HTTP-level tests for GOAR-5, exercising `/printers/register`, `/printers/claim`, and `/printers/{id}`. These tests:
  - Validate that re-registering a claimed printer preserves `owner_user_id` and CLAIMED status (e.g., TC_GOAR_5_01, TC_GOAR_5_02, TC_GOAR_5_04, TC_GOAR_5_05).
  - Confirm that re-registration of claimed printers regenerates Cloud ID and Printer Email ID while leaving claim code and ownership unchanged (e.g., TC_GOAR_5_15, TC_GOAR_5_16).
  - Confirm that failed re-registrations (using `simulate_welcome_page_failure=True`) do not change ownership or status and do not persist new Cloud ID or Printer Email ID (e.g., TC_GOAR_5_03, TC_GOAR_5_06, TC_GOAR_5_17–TC_GOAR_5_19).
  - Exercise first-time registration and re-registration for non-claimed printers, ensuring standard registration flow and identifiers (e.g., TC_GOAR_5_09, TC_GOAR_5_21–TC_GOAR_5_23).
  - Mark registration history and audit logging tests as skipped because history persistence and log schema are unresolved (TC_GOAR_5_07–TC_GOAR_5_08, TC_GOAR_5_24–TC_GOAR_5_26).

Note: The diff file `reports/GOAR-5_diff.txt` contains only the generated test file and no direct modification to `app/registration.py`. The behavioural changes required by GOAR-5 (preserving CLAIMED status and `owner_user_id`, avoiding new claim codes for CLAIMED printers) are already implemented in `register_printer()`; the diff for this ticket is focused on test automation rather than code changes. This discrepancy between diff (tests only) and implementation (fix present) is noted as an open question rather than a conflict.

## 3. Applicable Business Rules

1. Rule 11 — Claiming & Ownership — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - This rule directly governs GOAR-5: the Jira description reports that re-registration wiped `owner_user_id` and reset CLAIMED status to REGISTERED. The current implementation avoids touching `owner_user_id` in `register_printer()` and does not downgrade status from CLAIMED to REGISTERED on successful re-registration, thereby preventing silent loss of ownership.

2. Rule 9 — Claiming & Ownership — "A printer becomes visible to a user's applications only after a successful claim."
   - This rule explains the impact described in the ticket: when re-registration unclaimed the printer, it became invisible in HP Smart and subscriptions stopped functioning. Ensuring re-registration preserves CLAIMED status and `owner_user_id` maintains the visibility guaranteed by this rule.

3. Rule 2 — Registration — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - This rule is relevant for the rollback behaviour when `simulate_welcome_page_failure=True` or `WelcomePagePrintError` occurs. `_rollback_registration()` deletes printer data and indices, which satisfies the "no partial data" requirement. Generated tests (e.g., TC_GOAR_5_03, TC_GOAR_5_06, TC_GOAR_5_17–TC_GOAR_5_19) assert that after such failures, ownership and claimed status are unchanged at the API surface.

4. Rule 3 — Registration — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - This rule bears on Cloud ID behaviour during re-registration. `register_printer()` assigns a newly generated Cloud ID on every registration call, including re-registration of claimed printers, and tests such as TC_GOAR_5_01, TC_GOAR_5_02, TC_GOAR_5_15, and TC_GOAR_5_16 confirm that Cloud IDs change across re-registrations while ownership remains intact.

5. Rule 6 — Cloud ID, Printer Email ID & Claim Code — "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - This rule reinforces Rule 3’s Cloud ID regeneration requirement. Tests validate uniqueness across multiple re-registrations for the same printer (TC_GOAR_5_16) and verify that Cloud IDs conform to the expected `CID-[A-F0-9]{12}` pattern.

6. Rule 7 — Cloud ID, Printer Email ID & Claim Code — "Printer Email ID: must be globally unique; used for Email-to-Print."
   - This rule is relevant because re-registration regenerates printer email IDs. Generated tests treat uniqueness and format as required behaviour (e.g., TC_GOAR_5_09, TC_GOAR_5_15, TC_GOAR_5_16, TC_GOAR_5_21–TC_GOAR_5_23), checking that each email fits the expected pattern and differs across registrations.

7. Rule 8 — Cloud ID, Printer Email ID & Claim Code — "Claim Code: a **temporary** security token printed on the Welcome Page.
   - Expired or invalid claim codes must be rejected.
   - A claim code can only be used once."
   - This rule supports the requirement that claim codes should not be regenerated for already-claimed printers. The implementation generates claim codes only when `status != CLAIMED`, and tests ensure that re-registration of claimed printers keeps the original claim code unchanged (TC_GOAR_5_12–TC_GOAR_5_14).

8. Rule 14 — Non-Functional Expectations — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - This rule underpins the need for audit and logging behaviour referenced by skipped tests TC_GOAR_5_24–TC_GOAR_5_26. While `register_printer()` logs progress via `printer.log(...)` and propagates `RegistrationError` messages, the audit log schema and sinks are not exposed in this repo; requirements based on them are treated as proposed or open questions.

## 4. Original Acceptance Criteria

Re-registering an already-claimed printer does not clear owner_user_id.
Re-registering an already-claimed printer does not reset status away
from CLAIMED.
Registration history is preserved (appended to, not replaced).
First-time registration of a genuinely new serial number is unaffected.

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Re-registering an already-claimed printer must not generate a new Claim Code or modify the existing claim code state.
   - Justification: Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." and Rule 8 — "Claim Code: a **temporary** security token printed on the Welcome Page.
   - Expired or invalid claim codes must be rejected.
   - A claim code can only be used once." Generating and printing a new claim code for a CLAIMED printer during re-registration could enable a second user to claim the same device or otherwise interfere with the existing owner’s claim. The implementation’s guard `if printer.status != PrinterStatus.CLAIMED: printer.claim_code = _generate_claim_code()` should be treated as required behaviour and explicitly tested.

2. Re-registering an already-claimed printer must still generate a new Cloud ID and Printer Email ID, without affecting ownership.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." The implementation already regenerates Cloud ID and printer email ID on every registration call. This requirement makes explicit that this must hold for CLAIMED printers, while `owner_user_id` and CLAIMED status remain unchanged, so that identity refresh does not disturb ownership.

3. If re-registration of a claimed printer fails before the Welcome Page prints (e.g., due to `WelcomePagePrintError`), the system must not leave the printer in any partially updated state; from the client/API perspective, `owner_user_id`, status, serial number, Cloud ID, Printer Email ID, and claim code for that printer ID must remain exactly as they were before the attempted re-registration.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." combined with Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Even though `_rollback_registration()` deletes the printer record and indices, tests for GOAR-5 assert that failures during re-registration do not result in ownership or identity changes at the API surface; this behaviour should be preserved and treated as required.

4. Re-registering a printer that is not claimed (status != CLAIMED) must behave as a normal registration: generate a new Cloud ID, Printer Email ID, and Claim Code, assign an XMPP node if needed, and end with status REGISTERED on successful completion.
   - Justification: Rule 3 — "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." and Rule 7/8 — "Printer Email ID: must be globally unique; used for Email-to-Print." / "Claim Code: a **temporary** security token printed on the Welcome Page.
   - Expired or invalid claim codes must be rejected.
   - A claim code can only be used once." This requirement clarifies that the special-casing for CLAIMED printers (no new claim code and no status reset) must not alter the expected onboarding behaviour for non-claimed printers, ensuring that first-time and subsequent non-claimed registrations produce new identities and claim codes as normal.

5. Multiple successful re-registrations of the same claimed printer must produce distinct Cloud IDs and Printer Email IDs over time while preserving `owner_user_id` and CLAIMED status.
   - Justification: Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." and Rule 7 — "Printer Email ID: must be globally unique; used for Email-to-Print." This is a repeated-operation and boundary-value edge case: regenerating identifiers must not only produce values different from the immediately previous ones, but must ensure uniqueness across multiple re-registrations for the same printer, with ownership unaffected.

6. Failed re-registration attempts (for both claimed and non-claimed printers) must not persist any newly generated Cloud ID or Printer Email ID; subsequent successful registrations must still generate fresh identifiers.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This requirement clarifies that any identifiers generated during a failed registration attempt must be rolled back along with the printer record and indices, and must not be reused or left attached to the printer in store.

7. First-time registration of a genuinely new serial number must follow the standard registration flow and outcomes: new printer_id, Cloud ID, Printer Email ID, Claim Code with correct TTL, XMPP node assignment, status REGISTERED, and appropriate history entries indicating registration start and completion.
   - Justification: Rule 1 — "Registration is successful **only if** the Welcome/Info Page prints." together with Rules 3, 4, 5, 6, 7, and 8, which collectively define the expected identity, capability, connectivity, and claim-code behaviour for a successful first-time registration. GOAR-5 explicitly requires that this behaviour be unaffected by the fix for claimed-printer re-registration.

8. Audit or operational logs for re-registration of claimed printers should include structured fields indicating the printer was already claimed (status prior to re-registration) and that ownership was preserved (same `owner_user_id` before and after), and should record any registration failures affecting claimed printers.
   - Justification: Rule 14 — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." While Rule 14 is framed around failures, re-registration of CLAIMED printers has high customer-impact risk; structured logging of these events (including ownership metadata) improves observability and supports incident investigation.

## 6. Flagged Conflicts

None identified. As currently written, the acceptance criteria and the cited business rules can both hold:
- The implementation preserves CLAIMED status and `owner_user_id` during successful re-registration, satisfying the first two acceptance criteria and Rule 11.
- It generates new Cloud IDs and Printer Email IDs for all registrations, including re-registrations, as required by Rules 3, 6, and 7.
- Claim codes are not regenerated for CLAIMED printers, which is consistent with Rule 8’s one-time-use semantics and the intent of preserving ownership.

The acceptance criterion that "Registration history is preserved (appended to, not replaced)" cannot be fully validated from `app/registration.py` alone, because history persistence appears to depend on `printer.log(...)` and the underlying `store` implementation, which is not visible here. This is treated as an open question rather than a conflict.

## 7. Open Questions

1. How is "registration history" defined and persisted, and does re-registration of a claimed printer append to history rather than replacing or truncating existing entries?
   - Why it is unresolvable: The Jira ticket requires that "Registration history is preserved (appended to, not replaced)," but `app/registration.py` only shows `printer.log(...)` calls and does not reveal how logs/history are stored or whether prior entries are retained. The `store` implementation and any persistent audit/history layer are not in scope for this analysis, and generated tests TC_GOAR_5_07 and TC_GOAR_5_08 are explicitly skipped because history semantics cannot be asserted.
   - Downstream agents to exclude from scoring: Scenario designers and test generators (Agents 2–4) and automated test validators (Agents 5–6) must not treat specific registration-history semantics as verified; they should avoid failing tests based solely on assumptions about history append vs. replace behaviour.

2. What precise behaviour is expected when a printer transitions through first-time registration (unclaimed) → claim → one or more re-registrations, particularly regarding claim-code retention and visibility across that lifecycle?
   - Why it is unresolvable: The acceptance criteria state that first-time registration of a new serial number is unaffected and that re-registration must preserve ownership, but do not spell out claim-code lifecycle semantics beyond Rule 8’s one-time-use guarantee. The implementation retains the original claim code for claimed printers and continues to expose it via the registration and lookup responses in tests; whether this is the long-term intended behaviour (e.g., claim code remaining visible in GET responses after claim) is not explicitly documented.
   - Downstream agents to exclude from scoring: Agents designing lifecycle and repeated-operation scenarios must avoid assuming additional claim-code behaviours (such as hiding claim codes after claim, or rotating claim codes on re-registration) beyond what is explicitly specified.

3. Should rollback during re-registration of an already-claimed printer behave differently from rollback during first-time registration (e.g., by restoring the prior claimed record instead of deleting it)?
   - Why it is unresolvable: Rule 2 mandates that failed registrations must not retain partial data, and `_rollback_registration()` deletes the printer record and indices regardless of prior status. However, GOAR-5’s ownership-focused intent suggests that deleting a previously claimed printer record might be undesirable if a re-registration handshake fails after a printer has been in use. The Jira ticket does not describe expected behaviour for this specific scenario, and the store/audit layers are not visible.
   - Downstream agents to exclude from scoring: Agents modelling rollback behaviour (especially for claimed printers) must not assume that prior claimed records are preserved or restored; they should confine tests to the observable behaviour described by existing tests and business rules.

4. Are there any additional audit or compliance requirements (e.g., GDPR-related audit trails, subscription linkage logs) that must be satisfied when ownership is preserved or changed during re-registration of claimed printers?
   - Why it is unresolvable: Business rules mention GDPR compliance in the context of deregistration (Rule 12) and observability of failures (Rule 14), but do not define specific audit fields or retention policies for ownership changes during re-registration. The Jira ticket focuses on avoiding silent loss of ownership, not on audit trail details.
   - Downstream agents to exclude from scoring: Agents responsible for compliance and audit-test generation must not infer unvalidated audit-field requirements (such as mandatory recording of `owner_user_id` in every audit event) from these rules alone.
