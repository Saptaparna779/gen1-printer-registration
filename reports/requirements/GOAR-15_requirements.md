# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an already-registered serial number previously allowed `register_printer()` to overwrite the stored `model_number` and `firmware_version` with whatever the incoming request supplied, with no validation that this represented the same physical device. This created a spoofing/takeover risk: a different printer could reuse the same serial number and silently change the recorded model identity tied to that serial.

GOAR-15 adds model-number change detection on re-registration, structured warning logs, and a model-family gate that rejects re-registrations which appear to come from a materially different model family. Legitimate re-registrations (same model or same-family updates, including for claimed printers) must continue to succeed, while rejected attempts must leave no partial side effects, in line with the rollback business rules.

## 2. Affected Components

- `app/registration.py`
  - `register_printer()`
    - Validates that `serial_number`, `model_number`, and `firmware_version` are non-empty (post-`strip()`) and raises `RegistrationError` if any are missing.
    - Looks up an existing printer via `store.get_printer_by_serial(serial_number)` and branches between new registration vs re-registration.
    - On re-registration (`existing` is not `None`):
      - Uses the persisted `Printer` object (`printer = existing`).
      - GOAR-15 logic:
        - Compares existing vs incoming `model_number` using normalized (`strip().upper()`) values.
        - If the normalized `model_number` differs:
          - Calls `printer.log("GOAR-15: model_number changed on re-registration (old=..., new=...) -- flagged for review")`, adding a history entry that records the old and new model numbers and that the change is "flagged for review".
          - Emits a `WARNING` log via the module-level `logger` with a message mentioning the serial number and the old/new models.
          - Attaches `serial_number`, `old_model`, and `new_model` as structured fields via the `extra` parameter on the log call.
          - Computes `_model_family(printer.model_number)` and `_model_family(model_number)`; if they differ, raises `RegistrationError` with a detail string that includes both model numbers and states that re-registration is rejected due to model family mismatch and looks like a different physical device reusing the same serial number.
        - If the normalized `model_number` is the same, no GOAR-15 logging or rejection occurs.
      - After any GOAR-15 checks pass, updates `printer.model_number` and `printer.firmware_version` to the incoming values.
    - On first-time registration (`existing` is `None`):
      - Creates a new `Printer` with a fresh `printer_id`, `serial_number`, `model_number`, `firmware_version`, and `status=PrinterStatus.PENDING`.
    - Logs either "Registration started" or "Re-registration started" via `printer.log`.
    - **Cloud identity block** (unchanged by GOAR-15 but in scope for tests):
      - Generates a new Cloud ID on every registration call via `_generate_cloud_id()` and assigns it to `printer.cloud_id`.
      - Generates a globally unique printer email via `_generate_printer_email_id()`, assigns it to `printer.printer_email_id`, and indexes it via `store.index_email(...)`.
      - If the printer is not `CLAIMED`, generates a new claim code via `_generate_claim_code()` and assigns it to `printer.claim_code`.
      - Logs `"Cloud identity created: {printer.cloud_id}"`.
      - Persists the printer via `store.save_printer(printer)`.
    - **Capabilities block**:
      - If `store.get_capabilities(printer_id)` returns nothing, calls `_capture_capabilities(printer_id, model_number)`, saves the result via `store.save_capabilities(...)`, and logs "Capabilities captured".
      - Otherwise logs "Capabilities already on record; skipped recapture".
    - **XMPP block**:
      - If `printer.xmpp_node` is falsy, assigns an XMPP node via `assign_xmpp_node(printer_id)`, logs `"XMPP node assigned: {printer.xmpp_node}"`, and saves the printer.
    - **Welcome page / rollback block**:
      - Calls `generate_and_print_welcome_page(...)` with `simulate_welcome_page_failure` possibly forcing failure.
      - On `WelcomePagePrintError`, calls `_rollback_registration(printer)` and raises `RegistrationError`.
      - On success, if `printer.status` is not `CLAIMED`, sets `printer.status = PrinterStatus.REGISTERED`, logs "Welcome page printed successfully; registration complete", saves the printer, and indexes the serial via `store.index_serial(serial_number, printer_id)`.

  - `_model_family(model_number: str) -> str`
    - New helper introduced for GOAR-15.
    - Trims whitespace from `model_number`, uppercases it, splits on `"-"`, and returns:
      - All segments except the last (joined with `"-"`) if the split yields more than one segment (e.g., `"HP-LJ-4200"` → `"HP-LJ"`, `"HP-C-MFP-9500"` → `"HP-C-MFP"`).
      - The single segment otherwise (e.g., `"LASERJET"` → `"LASERJET"`).
    - Used only in GOAR-15 logic to distinguish same-family (accepted) vs different-family (rejected) re-registrations.

  - Other helpers and flows (`_generate_cloud_id()`, `_generate_printer_email_id()`, `_generate_claim_code()`, `_capture_capabilities()`, `_rollback_registration()`, `claim_printer()`, `deregister_printer()`) remain as previously specified in the business rules and are indirectly exercised by the GOAR-15 tests (e.g., Cloud ID regeneration, claim code usage, deregistration).

- `app/main.py`
  - `POST /printers/register`
    - Accepts `RegisterRequest` (`serial_number`, `model_number`, `firmware_version`, optional `simulate_welcome_page_failure`).
    - Requires a valid bearer token via `verify_token` (`user_id: str = Depends(verify_token)`); missing or invalid tokens result in FastAPI’s standard 422 (missing header) or 401 (invalid/expired token) responses.
    - Calls `registration.register_printer(...)`.
    - On `RegistrationError`, logs an error and raises `HTTPException` with `status_code=422` and a generic detail string.
    - On success, returns a JSON body including `printer_id`, `cloud_id`, `printer_email_id`, `claim_code`, `claim_code_expires_at`, `xmpp_node`, `status`, and `history`.

  - `POST /printers/claim`
    - Requires valid bearer token; calls `registration.claim_printer(...)`.
    - Returns `printer_id`, `status`, and `owner_user_id`.

  - `GET /printers/{printer_id}`
    - Requires valid bearer token; returns full printer details, including `owner_user_id` and `registration_history`.

  - `DELETE /printers/{printer_id}`
    - Requires valid bearer token; delegates to `registration.deregister_printer(...)` and returns `{ "status": "DEREGISTERED", "printer_id": ... }` on success.

- `tests/features/GOAR-15.feature`
  - New Gherkin feature that defines scenarios for:
    - Model-number change detection, logging, and review flagging on re-registration.
    - Acceptance vs rejection of re-registrations based on `_model_family()` classification (same-family accepted, different-family rejected).
    - Case and whitespace normalization for `model_number`.
    - Successful re-registration with updated firmware and unchanged model.
    - Re-registration for already claimed printers, ensuring status and ownership preservation.
    - Authorization failures for registration, claim, and lookup when Authorization headers are missing or invalid.
    - Structured logging of model-number change warnings with discrete fields.
    - Ensuring rejected re-registrations produce no Cloud ID, printer email, or XMPP node changes and no additional side-effect entries beyond a review flag.

- `tests/steps/test_GOAR-15_steps.py`
  - New pytest-bdd step definitions that:
    - Use `TestClient` to call HTTP endpoints rather than internal functions.
    - Provide `Given` steps to register and optionally claim printers, capturing initial Cloud ID, email, XMPP node, and history.
    - Provide `When` steps to re-register, claim, or look up printers under various auth and model-number conditions, capturing responses and warning logs via `caplog`.
    - Provide `Then` steps that assert:
      - Success vs failure of re-registration.
      - Presence or absence of model-number-change history entries and flags.
      - Warning log messages and structured fields for GOAR-15 events.
      - Correct HTTP error responses for missing/invalid Authorization headers on register, claim, and lookup.
      - Preservation of ownership and status on acceptable re-registrations of claimed printers.
      - Lack of side effects on rejected re-registrations (unchanged Cloud ID, printer email, XMPP node, and only an added review-flag history entry).

Where the diff and implementation disagree:

- The diff (`reports/GOAR-15_diff.txt`) shows only the addition of the BDD feature file and its pytest-bdd step definitions under `tests/`. It does not show the GOAR-15 logic changes in `app/registration.py`, even though those are clearly present in the current source. For this report, `app/registration.py` is treated as authoritative, and the diff is understood to be incomplete.

## 3. Applicable Business Rules

1. **Rule 2 — Rollback on failure / no partial data**
   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - Application: GOAR-15’s model-family mismatch rejection path must behave like any other pre–Welcome Page failure: the registration attempt fails and must not commit partial state such as new capabilities, serial index entries, Cloud ID, printer email, or XMPP node. Tests that assert zero side effects and unchanged Cloud ID/email/XMPP on rejected re-registrations are enforcing this rule.

2. **Rule 3 — New Cloud ID on every re-registration**
   - Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - Application: Accepted re-registrations (same model or same-family model changes) must still generate a new Cloud ID distinct from the previous one. GOAR-15’s scenarios that assert a new Cloud ID on successful re-registration validate this rule remains true despite the new model-family checks.

3. **Rule 4 — Capabilities captured once**
   - Exact sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."
   - Application: GOAR-15 must not cause capabilities to be recaptured on re-registration when they already exist. The unchanged logic that logs "Capabilities already on record; skipped recapture" and the tests noting no additional capability-related history entries on re-registration are consistent with this rule.

4. **Rule 6 — Cloud ID uniqueness & regeneration**
   - Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - Application: GOAR-15’s tests verifying that successful re-registrations produce a new Cloud ID, and that rejected ones do not produce or persist new Cloud IDs, are aligned with this rule. New Cloud IDs must be unique and must not be reused.

5. **Rule 7 — Printer Email ID must be globally unique**
   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."
   - Application: GOAR-15’s scenarios checking that re-registration issues a new printer email address different from the original confirm that uniqueness and issuance behaviour remain intact under the new model-family checks.

6. **Rule 8 — Claim Code is temporary and single-use**
   - Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."
   - Application: While GOAR-15 does not change claim-code generation or validation logic, scenarios involving claimed printers rely on this behaviour remaining correct, particularly that claim codes are one-time and bound to the printer, so that ownership cannot be silently reassigned via re-registration.

7. **Rule 9 — Visibility only after claim**
   - Exact sentence: "A printer becomes visible to a user's applications only after a successful claim."
   - Application: GOAR-15 scenarios that re-register already claimed printers and then look them up via `/printers/{printer_id}` depend on claim state not being reset or lost by GOAR-15 changes; preserving `owner_user_id` and `status` ensures visibility semantics remain intact.

8. **Rule 11 — Do not overwrite ownership**
   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Application: GOAR-15 directly mitigates a previously possible ownership-takeover path by rejecting re-registrations where the incoming `model_number` appears to represent a different model family. Tests that confirm ownership (`owner_user_id`) and `CLAIMED` status remain unchanged after acceptable re-registrations enforce this rule.

9. **Rule 14 — Registration failures must be observable**
   - Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - Application: GOAR-15’s structured warning logs for model-number changes, including serial and old/new model fields, make these potential spoofing events observable to operations and security teams, satisfying this rule.

## 4. Original Acceptance Criteria

Verbatim from `jira_context/GOAR-15_live.md`:

1. "At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review."
2. "(Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation."
3. "Legitimate re-registrations with matching or compatible model/firmware data continue to work as before."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. **Zero side effects on model-family mismatch rejection**
   - **Requirement (proposed)**: When re-registration is rejected due to a model-family mismatch, the system SHOULD guarantee that no changes are made to persistent state beyond logging and history entries that record the rejection; specifically, Cloud ID, printer email ID, XMPP node, capabilities, and serial index entries MUST remain as they were before the attempted re-registration.
   - **Justification**: Edge case category — rollback/partial-failure behaviour, plus Rule 2: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This proposal makes explicit the rollback expectation for the specific GOAR-15 model-family mismatch path.

2. **Cloud ID allocation and rollback on rejection**
   - **Requirement (proposed)**: The system SHOULD either (a) ensure that `_generate_cloud_id()` is not called until after the model-family check succeeds, or (b) ensure that any Cloud ID generated before a failure in the GOAR-15 checks is not persisted or reused, so that rejected re-registrations do not consume Cloud IDs or leave inconsistent identity traces.
   - **Justification**: Edge case category — rollback/partial-failure behaviour, grounded in Rule 2 and Rule 3/6 ("Cloud ID: system-generated, unique, regenerated on every re-registration."). This avoids wasting Cloud IDs and ensures that only successful registrations produce durable Cloud identities.

3. **Structured logging field stability**
   - **Requirement (proposed)**: The structured warning log for model-number changes SHOULD consistently expose `serial_number`, `old_model`, and `new_model` as discrete fields (e.g., via the `extra` dict) so downstream telemetry/alerting systems can reliably query and filter on these attributes across releases.
   - **Justification**: Rule 14: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." This codifies the specific field-level expectations already exercised by GOAR-15’s logging tests.

4. **Re-registration of claimed printers preserves ownership**
   - **Requirement (proposed)**: For printers with `status == CLAIMED`, any successful re-registration whose GOAR-15 checks pass MUST preserve `owner_user_id` and keep `status` as `CLAIMED` (i.e., re-registration must not de-claim or reassign ownership implicitly).
   - **Justification**: Rule 11: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." GOAR-15 scenarios already assert this behaviour; this requirement formalizes it for future changes.

5. **Auth failures for registration, claim, and lookup endpoints**
   - **Requirement (proposed)**: Requests to `/printers/register`, `/printers/claim`, and `/printers/{printer_id}` with a missing `Authorization` header MUST be rejected with FastAPI’s standard 422 validation error (header field required), and requests with an invalid bearer token MUST be rejected with HTTP 401 and a body `{ "detail": "Invalid or expired token" }`.
   - **Justification**: Edge case category — auth failures (missing or invalid JWT). GOAR-15’s BDD scenarios explicitly test these behaviours; formalizing them as requirements clarifies that they are in-scope expectations rather than incidental framework behaviour.

## 6. Flagged Conflicts

1. **AC2 "rejected or requires explicit confirmation" vs implementation**
   - AC2 allows two acceptable outcomes for materially different model families: rejection or explicit confirmation. The current implementation unconditionally rejects such re-registrations and does not provide any explicit confirmation mechanism. There is no business rule requiring a confirmation flow, so outright rejection is compliant with the rules but narrower than the AC’s wording. This should be clarified, but there is no direct rule conflict.

2. **Deregistration semantics vs model-family checks**
   - Rule 13 states: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." Neither the ticket nor the code clarifies whether the GOAR-15 model-family gate should apply after full deregistration. If deregistration is meant to "reset" history, a strict model-family check on later registrations might be stricter than intended; if spoofing protection must persist, the current behaviour is appropriate. This is a potential interpretation conflict, not a direct violation.

## 7. Open Questions

1. **Firmware validation scope for GOAR-15**
   - **Question**: Should GOAR-15 include any validation, logging, or enforcement specific to `firmware_version` changes (e.g., rejecting obviously incompatible firmware), or is firmware semantics intentionally left undefined for this ticket?
   - **Why it is unresolvable from available inputs**: `docs/business_rules.md` does not mention firmware, and the Jira description only notes firmware overwrites as part of the problem statement without specifying expected behaviour. The implementation accepts any firmware string and simply updates it.
   - **Downstream agents to exclude from scoring**: Scenario-design, test-generation, and scoring agents must not assume any additional firmware-validation behaviour beyond the current implementation.

2. **Explicit confirmation flow for different-family re-registrations**
   - **Question**: Is an explicit confirmation mechanism (e.g., an administrative override or UI prompt) for materially different model families required to fully satisfy AC2, or is outright rejection of such re-registrations considered sufficient for GOAR-15?
   - **Why it is unresolvable from available inputs**: The Jira AC mentions "rejected or requires explicit confirmation," but neither the code nor `docs/business_rules.md` describes any confirmation flow or override mechanism.
   - **Downstream agents to exclude from scoring**: Agents must not design or score tests that assume the presence of a confirmation/override path for GOAR-15.

3. **Model-family semantics after deregistration**
   - **Question**: After a printer has been fully deregistered per Rules 12 and 13, should a subsequent registration with the same serial but a different model family be treated as suspicious (subject to GOAR-15 checks) or as a new device with no historical model-family constraint?
   - **Why it is unresolvable from available inputs**: Business rules define deregistration and Cloud ID behaviour but say nothing about reusing serial numbers across different physical devices post-deregistration. The Jira ticket does not discuss post-deregistration scenarios.
   - **Downstream agents to exclude from scoring**: Scenario-design and scoring agents must not treat any specific post-deregistration model-family behaviour as mandated by GOAR-15.

4. **Scope of structured logging beyond GOAR-15 events**
   - **Question**: Should structured logging (with discrete fields) be extended to all registration failures (e.g., capability capture failures, XMPP assignment failures, welcome-page print failures), or is GOAR-15 intended to cover only model-number change events for now?
   - **Why it is unresolvable from available inputs**: Rule 14 is broad about observability, but the Jira ticket only explicitly addresses logging for model-number-change and spoofing-related events.
   - **Downstream agents to exclude from scoring**: Agents must not score the absence of structured logs on non–GOAR-15 failure paths as defects under this ticket.

5. **Future replacement of `_model_family()` with a catalog**
   - **Question**: When an authoritative model-family catalog is introduced, should historical decisions and flags made using the current heuristic `_model_family()` be recalculated or migrated, and if so, how should discrepancies be handled?
   - **Why it is unresolvable from available inputs**: Neither the Jira ticket nor the business rules mention catalog-based model families or migration strategy.
   - **Downstream agents to exclude from scoring**: Any future migration behaviour or catalog-driven reclassification is out of scope for GOAR-15 and must not be included in scoring.
