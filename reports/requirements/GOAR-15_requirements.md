# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an already-registered serial number previously allowed `register_printer()` to overwrite the stored `model_number` and `firmware_version` with whatever the incoming request supplied, with no validation that this represented the same physical device. This created a spoofing/takeover risk: a different printer could reuse the same serial number and silently change the recorded model identity tied to that serial.

GOAR-15 introduces model-number change detection in the re-registration path, logs such changes as notable events, and rejects re-registrations where the incoming `model_number` appears to belong to a materially different model family. Legitimate re-registrations (same model or same-family updates, including claimed printers) must continue to succeed and obey rollback and Cloud ID business rules, while rejected attempts should leave no partial side effects beyond logging.

## 2. Affected Components

- `app/registration.py`
  - `register_printer()`
    - Validates that `serial_number`, `model_number`, and `firmware_version` are non-empty after `strip()`, raising `RegistrationError` if any are missing.
    - Looks up an existing printer via `store.get_printer_by_serial(serial_number)` and branches between first-time registration and re-registration.
    - On re-registration (`existing` is not `None`):
      - Uses the persisted `Printer` object (`printer = existing`).
      - GOAR-15-specific behaviour:
        - Compares existing vs incoming `model_number` using normalized values (`printer.model_number.strip().upper()` vs `model_number.strip().upper()`).
        - If the normalized `model_number` differs:
          - Calls `printer.log("GOAR-15: model_number changed on re-registration (old={printer.model_number}, new={model_number}) -- flagged for review")`, adding a history entry that records the old and new model numbers and marks the event as "flagged for review".
          - Emits a `WARNING` log via the module-level `logger` with a message including the serial number and old/new models, and passes structured fields via `extra={"serial_number": serial_number, "old_model": printer.model_number, "new_model": model_number}`.
          - Computes `_model_family(printer.model_number)` and `_model_family(model_number)`; if they differ, raises `RegistrationError` with a message that the re-registration is rejected due to model family mismatch and appears to be a different physical device reusing the same serial number.
        - If the normalized `model_number` is the same, no GOAR-15 logging or rejection occurs.
      - After any GOAR-15 checks pass, updates `printer.model_number` and `printer.firmware_version` to the incoming values.
    - On first-time registration (`existing` is `None`):
      - Creates a new `Printer` with a fresh `printer_id`, the provided `serial_number`, `model_number`, `firmware_version`, and `status=PrinterStatus.PENDING`.
    - Logs either "Re-registration started" or "Registration started" via `printer.log`.
    - **Cloud identity block**:
      - Generates a new Cloud ID via `_generate_cloud_id()` on every registration call (first-time or re-registration) and assigns it to `printer.cloud_id`.
      - Generates a globally unique printer email via `_generate_printer_email_id()`, assigns it to `printer.printer_email_id`, and indexes it via `store.index_email(...)`.
      - If the printer is not `CLAIMED`, generates a new claim code via `_generate_claim_code()` and assigns it to `printer.claim_code`.
      - Logs `"Cloud identity created: {printer.cloud_id}"`.
      - Persists the printer via `store.save_printer(printer)`.
    - **Capabilities block**:
      - If `store.get_capabilities(printer_id)` returns nothing, calls `_capture_capabilities(printer_id, model_number)`, saves the result via `store.save_capabilities(...)`, and logs "Capabilities captured".
      - Otherwise logs "Capabilities already on record; skipped recapture".
    - **XMPP connectivity block**:
      - If `printer.xmpp_node` is falsy, assigns an XMPP node via `assign_xmpp_node(printer_id)`, logs `"XMPP node assigned: {printer.xmpp_node}"`, and saves the printer.
    - **Welcome page / rollback block**:
      - Calls `generate_and_print_welcome_page(...)` with `simulate_welcome_page_failure` possibly forcing failure.
      - On `WelcomePagePrintError`, calls `_rollback_registration(printer)` and raises `RegistrationError`.
      - On success, if `printer.status` is not `CLAIMED`, sets `printer.status = PrinterStatus.REGISTERED`, logs "Welcome page printed successfully; registration complete", saves the printer, and indexes the serial via `store.index_serial(serial_number, printer_id)`.

  - `_model_family(model_number: str) -> str`
    - GOAR-15 helper for model-family extraction.
    - Trims whitespace, uppercases the string, splits on `"-"`, and returns:
      - All segments except the last (joined with `"-"`) if there are multiple segments (e.g., `"HP-LJ-4200"` → `"HP-LJ"`, `"HP-C-MFP-9500"` → `"HP-C-MFP"`).
      - The single segment otherwise.
    - Used only in GOAR-15 logic to distinguish firmware/revision-level changes (same family) from materially different devices (different family).

  - `_capture_capabilities(printer_id, model_number)`
    - Unchanged in logic but relevant because GOAR-15 must not trigger recapture on re-registration when capabilities already exist.
    - Uses simple model-prefix heuristics to set `supports_color`, `supports_scan`, and `max_dpi`.

  - `_rollback_registration(printer)`
    - Deletes the printer, serial index, and capabilities for a failed registration.
    - GOAR-15 relies on this to ensure failures after the Welcome Page stage leave no partial data.

  - `claim_printer()`
    - Links a printer to a user via a Claim Code, enforcing single-use and expiry rules.
    - Indirectly relevant: GOAR-15 must preserve `owner_user_id` and `status` for claimed printers when re-registration succeeds.

  - `deregister_printer()`
    - Removes printer data and indices for deregistration.
    - Not modified by GOAR-15, but interacts with Rule 13 and Cloud ID behaviour for future registrations.

- `app/main.py`
  - `POST /printers/register`
    - Accepts `serial_number`, `model_number`, `firmware_version`, and optional `simulate_welcome_page_failure` in `RegisterRequest`.
    - Requires a valid bearer token via `verify_token`; missing headers or invalid tokens cause 401/422 responses depending on FastAPI's dependency behaviour.
    - Calls `registration.register_printer(...)`.
    - On `RegistrationError`, returns HTTP 422 with an error detail.
    - On success, returns printer identity, Cloud ID, email, claim code (if applicable), XMPP node, status, and registration history.

  - Other endpoints (`/printers/claim`, `/printers/{printer_id}`, `/printers/{printer_id}` DELETE)
    - Not changed by GOAR-15, but used in tests to validate ownership and status behaviour across re-registration.

Where diff and implementation disagree:

- `reports/GOAR-15_diff.txt` is empty, providing no view of code changes. However, `app/registration.py` clearly contains GOAR-15-specific logic for model-number change detection and model-family checks. For this report, the implementation in `app/registration.py` is treated as authoritative, and the absence of diff content is noted as an Open Question rather than a source of requirement.

## 3. Applicable Business Rules

1. **Rule 2 — Rollback on failure / no partial data**  
   Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."  
   Application: GOAR-15’s rejection path for model-family mismatches and any other pre–Welcome Page failures must not leave partial registration state (printer records, capabilities, serial index). `_rollback_registration()` enforces this after Welcome Page failures; for pre–Welcome Page errors in GOAR-15, the logic must ensure that side effects such as Cloud ID, email indexing, capabilities, and XMPP node assignment are either not performed or are rolled back.

2. **Rule 3 — New Cloud ID on every re-registration**  
   Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."  
   Application: GOAR-15 must preserve the behaviour that any successful re-registration generates a new Cloud ID distinct from the previous one, regardless of model-number change, as long as the re-registration is accepted (same model or same-family). Tests should verify that the Cloud ID is regenerated on every accepted re-registration.

3. **Rule 4 — Capabilities captured once**  
   Exact sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."  
   Application: GOAR-15 must ensure that re-registration does not trigger capability recapture when capabilities already exist. The existing logic that logs "Capabilities already on record; skipped recapture" must continue to be exercised on re-registration.

4. **Rule 6 — Cloud ID uniqueness & regeneration**  
   Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."  
   Application: In conjunction with Rule 3, this rule ensures that successful re-registrations produce a new, unique Cloud ID. GOAR-15 must not introduce any path that reuses a previous Cloud ID, nor any path that generates but fails to persist a Cloud ID for a successful registration.

5. **Rule 7 — Printer Email ID uniqueness**  
   Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."  
   Application: GOAR-15 does not alter email-generation logic; tests should confirm that printer email IDs remain unique and correctly indexed via `store.index_email(...)` on registration and re-registration.

6. **Rule 8 — Claim Code behaviour**  
   Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."  
   Application: GOAR-15 changes must not violate single-use and expiry semantics. Re-registration must not reset or invalidate claim codes in ways that allow ownership to bypass Claim Code rules.

7. **Rule 9 — Visibility after claim**  
   Exact sentence: "A printer becomes visible to a user's applications only after a successful claim."  
   Application: GOAR-15 behaviour for claimed printers on re-registration must preserve visibility rules; re-registration should not unclaim a printer or change `owner_user_id`.

8. **Rule 11 — Ownership must not be overwritten**  
   Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."  
   Application: GOAR-15 directly mitigates a possible silent takeover path by rejecting re-registrations where the incoming `model_number` appears to belong to a different model family. Accepted re-registrations must preserve `owner_user_id` and `CLAIMED` status.

9. **Rule 14 — Observability of registration failures**  
   Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."  
   Application: GOAR-15 adds explicit logging and structured fields for model-number change events, making spoofing-like behaviours observable to operations and security teams.

## 4. Original Acceptance Criteria

Verbatim from `jira_context/GOAR-15_live.md`:

1. "At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review."
2. "(Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation."
3. "Legitimate re-registrations with matching or compatible model/firmware data continue to work as before."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. **Zero side effects on model-family mismatch rejection**  
   - **Requirement (proposed)**: When re-registration is rejected due to a model-family mismatch, the system SHOULD guarantee that no changes are made to persistent state beyond logging and history entries that record the rejection; specifically, Cloud ID, printer email ID, XMPP node, capabilities, serial index entries, and the existing printer's `model_number`, `firmware_version`, `status`, and `owner_user_id` MUST remain unchanged.
   - **Justification**: Edge case category — rollback/partial-failure behaviour, plus Rule 2: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This clarifies expected behaviour for the specific GOAR-15 rejection path.

2. **Auth failures for registration, claim, and lookup endpoints**  
   - **Requirement (proposed)**: Requests to `/printers/register`, `/printers/claim`, and `/printers/{printer_id}` with a missing `Authorization` header MUST be rejected according to FastAPI's validation rules (header required), and requests with an invalid bearer token MUST be rejected with HTTP 401 and an error body indicating an invalid or expired token.
   - **Justification**: Edge case category — auth failures (missing or invalid JWT). These behaviours are critical for printer identity and ownership protection but are not explicitly covered by the GOAR-15 ACs.

3. **Re-registration of claimed printers preserves ownership**  
   - **Requirement (proposed)**: For printers with `status == CLAIMED`, any successful re-registration whose GOAR-15 checks pass MUST preserve `owner_user_id` and keep `status` as `CLAIMED`; re-registration must not implicitly de-claim or reassign ownership.
   - **Justification**: Rule 11: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." This requirement makes explicit what the rule implies for GOAR-15 scenarios.

4. **Model-number normalization for change detection**  
   - **Requirement (proposed)**: The comparison used to detect a model-number change on re-registration SHOULD consistently apply the same normalization (e.g., `strip().upper()`) to both existing and incoming `model_number` values, to avoid false positives caused purely by case or whitespace differences.
   - **Justification**: Edge case category — boundary values and repeated operations. While the current implementation already uses `strip().upper()`, this requirement ensures future changes cannot introduce inconsistent comparisons.

5. **Structured logging field stability**  
   - **Requirement (proposed)**: The warning log for GOAR-15 model-number change events SHOULD consistently include discrete fields for `serial_number`, `old_model`, and `new_model` via the logging framework (e.g., the `extra` parameter), so telemetry pipelines can reliably query and alert on these events.
   - **Justification**: Rule 14: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." This formalizes the structured logging expectations.

## 6. Flagged Conflicts

1. **AC2 "rejected or requires explicit confirmation" vs implementation**  
   AC2 allows either rejection or an explicit confirmation mechanism for materially different model families. The current implementation always rejects such re-registrations and does not implement an explicit confirmation flow. This is narrower than AC2's wording but does not conflict with any business rule, as there is no rule requiring a confirmation mechanism.

2. **Interaction with deregistration and Rule 13**  
   Rule 13 states: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." The GOAR-15 logic for model-family checks does not explicitly differentiate between re-registration before or after deregistration; the business rules do not state whether model-family-based spoofing protection should apply post-deregistration. This is a potential interpretation tension but not a direct conflict between the ACs and the rules.

3. **Logging vs rollback semantics**  
   Rule 2 disallows partial data retention for failed registrations; GOAR-15 introduces logging and history entries for rejected re-registrations. Whether such history/log entries are considered "partial data" under Rule 2 is not explicitly defined. This could be considered a minor tension, but given Rule 14's emphasis on observability, retaining logs for failed attempts is likely acceptable.

## 7. Open Questions

1. **Firmware overwrite and validation scope**  
   - **Question**: Should GOAR-15 include any validation, logging, or enforcement around `firmware_version` changes (e.g., rejecting clearly incompatible firmware or logging significant downgrades), or is firmware semantics intentionally out of scope for this ticket?
   - **Why unresolvable**: The Jira description mentions firmware overwrites as part of the problem, but the ACs and business rules say nothing specific about firmware. The implementation simply updates `printer.firmware_version` without additional checks.
   - **Agents to exclude from scoring**: Scenario-design, test-generation, and scoring agents must not assume additional firmware-specific behaviour beyond the current implementation.

2. **Explicit confirmation flow for different-family re-registrations**  
   - **Question**: Is an explicit confirmation mechanism (e.g., administrative override or UI-based confirmation) for materially different model families required to fully satisfy AC2, or is unconditional rejection of such re-registrations acceptable for GOAR-15?
   - **Why unresolvable**: AC2 mentions "rejected or requires explicit confirmation," but there is no implementation or business-rule guidance on confirmation flows.
   - **Agents to exclude from scoring**: Agents must not design or score tests that assume an explicit confirmation or override mechanism exists for GOAR-15.

3. **Model-family semantics after deregistration**  
   - **Question**: After a printer has been fully deregistered in accordance with Rules 12 and 13, should a subsequent registration with the same serial but a different model family be treated as suspicious (subject to GOAR-15 checks) or as a fresh printer with no historical model-family constraint?
   - **Why unresolvable**: Business rules define Cloud ID behaviour for re-registration after deregistration but do not address serial reuse across different devices or model families. The Jira ticket does not mention post-deregistration scenarios.
   - **Agents to exclude from scoring**: Scenario-design and scoring agents must not assume any particular model-family behaviour for post-deregistration registrations as part of GOAR-15.

4. **Scope of structured logging across other failure modes**  
   - **Question**: Should structured logging (with discrete fields) be extended to all registration failures (e.g., capability capture failures, XMPP assignment failures, Welcome Page print failures), or is GOAR-15 intended to apply structured logging only to model-number change events?
   - **Why unresolvable**: Rule 14 calls for observable registration failures broadly, but the Jira ticket focuses only on spoofing-related model-number changes. The current implementation adds structured logs only for GOAR-15 events.
   - **Agents to exclude from scoring**: Agents must not treat the absence of structured logging for non–GOAR-15 failure paths as a defect under this ticket.

5. **Future replacement of `_model_family()` with a catalog and historical data**  
   - **Question**: If a future release replaces `_model_family()` with a catalog-based model-family lookup, should historical decisions and review flags generated under the current heuristic be recalculated or migrated, and how should discrepancies be handled?
   - **Why unresolvable**: Neither Jira nor the business rules mention catalog-based model families or data migration strategies.
   - **Agents to exclude from scoring**: Any behaviour related to catalog-based classification or migration of historical GOAR-15 events is out of scope for this ticket and must not be included in scoring.
