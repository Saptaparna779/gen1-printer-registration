# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an already-registered serial number previously allowed `register_printer()` to overwrite the stored `model_number` and `firmware_version` with whatever the incoming request supplied, with no validation that the request came from the same physical device. This created a spoofing/takeover risk: a different printer could reuse the same serial number and silently change the recorded model identity tied to that serial.

GOAR-15 adds model-number change detection on re-registration, structured warning logs, and a model-family gate that rejects re-registrations which appear to come from a materially different model family. Legitimate re-registrations (same model or same-family updates, including for claimed printers) must continue to succeed, while rejected attempts must leave no partial side effects, in line with the rollback business rules.

## 2. Affected Components

- `app/registration.py`
  - `register_printer()`
    - Compares existing vs incoming `model_number` on re-registration using normalized (`strip().upper()`) values.
    - When the normalized `model_number` changes:
      - Appends a GOAR-15-specific history entry to the printer’s `registration_history` indicating the old and new model numbers and that the change is "flagged for review".
      - Emits a `WARNING` log via the module-level `logger` with a message mentioning the serial number and the old/new models.
      - Attaches `serial_number`, `old_model`, and `new_model` as structured fields via the `extra` parameter.
      - Calls `_model_family()` on both the existing `printer.model_number` and the incoming `model_number` and, if they differ, raises `RegistrationError` with a detail string indicating a model family mismatch and suggesting serial-number reuse by a different physical device.
    - After any checks pass, updates `printer.model_number` and `printer.firmware_version` to the incoming values.
    - Continues to generate a new Cloud ID, printer email ID, and (if unclaimed) claim code on every registration call, and to log and persist Cloud identity, capabilities, XMPP node, and welcome-page events as before.
  - `_model_family(model_number: str) -> str`
    - New helper that derives a "crude" model-family identifier by:
      - Trimming whitespace and uppercasing the `model_number`.
      - Splitting the string on `-`.
      - Returning all segments except the last joined by `-` when there is more than one segment (e.g., `"HP-LJ-4200"` → `"HP-LJ"`), or the single segment otherwise.
  - Other helpers and flows
    - `_generate_cloud_id()`, `_generate_printer_email_id()`, `_generate_claim_code()`, `_capture_capabilities()`, `_rollback_registration()`, `claim_printer()`, and `deregister_printer()` are unchanged in behavior, but they are exercised by the GOAR-15 tests and must continue to comply with existing business rules.

- `app/main.py`
  - `POST /printers/register`
    - Continues to call `registration.register_printer()` and to translate `RegistrationError` into HTTP 422 with a generic error message.
    - Along with `verify_token`, underpins the auth behavior validated by GOAR-15’s BDD scenarios (missing/invalid Authorization header handling).
  - `POST /printers/claim`, `GET /printers/{printer_id}`, `DELETE /printers/{printer_id}`
    - No GOAR-15-specific logic, but used by tests to verify claim preservation and auth failures.

- `tests/features/GOAR-15.feature`
  - New BDD feature file that defines 20 Scenarios (including a Scenario Outline) providing end-to-end coverage for GOAR-15 via HTTP-level tests.
  - Key behaviors exercised:
    - Model-number change detection and logging on re-registration.
    - Acceptance vs rejection based on `_model_family()` classification.
    - Case and whitespace handling for `model_number`.
    - Authorization failures for registration, claim, and lookup endpoints.
    - Preservation of claim ownership during acceptable re-registrations.
    - Zero side effects on rejected re-registrations.

- `tests/steps/test_GOAR-15_steps.py`
  - New pytest-bdd step definitions that:
    - Use `fastapi.testclient.TestClient` and the app’s HTTP API (no direct calls into `register_printer()`) via the `client` fixture and a no-auth helper.
    - Capture `logging.WARNING` records for logger `app.registration` via `caplog`.
    - Assert on HTTP status codes, response bodies, registration histories, ownership, and absence/presence of side effects in accordance with the GOAR-15 scenarios.

Where the diff and implementation disagree:

- The diff includes only test-layer changes (`tests/features/GOAR-15.feature` and `tests/steps/test_GOAR-15_steps.py`), while `app/registration.py` also contains the GOAR-15 logic. This indicates that the diff file is not a complete representation of all changes for GOAR-15. For requirements purposes, `app/registration.py` is treated as authoritative.

## 3. Applicable Business Rules

1. **Rule 2 — Rollback on failure / no partial data**
   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - Application: GOAR-15’s model-family mismatch rejection path must not introduce any partial side effects. The registration attempt must fail before the Welcome Page is printed and must leave the stored printer, capabilities, serial index, Cloud ID, printer email ID, and XMPP node unchanged, apart from any history/log entries that record the attempted (but rejected) re-registration.

2. **Rule 3 — New Cloud ID on every re-registration**
   - Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - Application: Accepted re-registrations (i.e., those that pass the model-family gate) must still generate a brand-new Cloud ID distinct from the previous one. GOAR-15 must not constrain or bypass the Cloud ID regeneration mandated by this rule.

3. **Rule 4 — Capabilities captured once**
   - Exact sentence: "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."
   - Application: GOAR-15’s new model-number checks and rejection flows must not cause capabilities to be recaptured on re-registration when capabilities already exist. The existing behavior—logging "Capabilities already on record; skipped recapture" when capabilities are present—must remain intact.

4. **Rule 6 — Cloud ID uniqueness & regeneration**
   - Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - Application: GOAR-15’s acceptance-path tests that check for a new Cloud ID on successful re-registration are directly enforcing this rule. The model-family gate must not allow reuse of old Cloud IDs.

5. **Rule 7 — Printer Email ID must be globally unique**
   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."
   - Application: GOAR-15’s regression tests for successful re-registration verify that a new printer email address is issued and that it differs from the original, ensuring that the new model-family checks do not break the uniqueness requirement or the expected issuance behavior.

6. **Rule 8 — Claim Code is temporary and single-use**
   - Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page."
     - "Expired or invalid claim codes must be rejected."
     - "A claim code can only be used once."
   - Application: While GOAR-15 does not change claim-code logic, re-registrations of claimed printers must not result in claim-code reuse or reissuance that would violate these sub-rules. Tests that re-register claimed printers and then re-query their state rely on these behaviors being preserved.

7. **Rule 9 — Visibility only after claim**
   - Exact sentence: "A printer becomes visible to a user's applications only after a successful claim."
   - Application: GOAR-15 scenarios involving claimed printers verify that re-registrations do not remove claims or change ownership in ways that would alter visibility assumptions. Preserving `owner_user_id` and `status` ensures this business rule continues to hold.

8. **Rule 11 — Do not overwrite ownership**
   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Application: The model-family gate and the requirement that successful re-registrations preserve `owner_user_id` and claim status are directly driven by this rule. GOAR-15 addresses the specific spoofing scenario where a different physical device attempts to reuse a serial number and alter the recorded model identity.

9. **Rule 14 — Registration failures must be observable**
   - Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
   - Application: GOAR-15’s warning log for model-number changes, including structured fields via the `extra` dict, is a concrete implementation of this rule for security-relevant re-registrations. Tests assert that the warning log records expose `serial_number`, `old_model`, and `new_model` as discrete attributes.

## 4. Original Acceptance Criteria

Verbatim from `jira_context/GOAR-15_live.md`:

1. "At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review."
2. "(Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation."
3. "Legitimate re-registrations with matching or compatible model/firmware data continue to work as before."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. **Case- and whitespace-insensitive model-number comparison**
   - **Requirement (proposed)**: On re-registration, the comparison that detects `model_number` changes SHOULD treat case and leading/trailing whitespace as insignificant (e.g., `"HP-LJ-2055"` vs `" hp-lj-2055"` should not be considered a change).
   - **Justification**: Edge case category — boundary values / normalization. This reduces spurious flags due to trivial formatting differences while maintaining the intended spoofing protection behavior.

2. **Explicit codification of zero side effects on model-family mismatch**
   - **Requirement (proposed)**: When re-registration is rejected due to a model-family mismatch, the system SHOULD guarantee that no changes are made to persistent state beyond logging and history entries that record the rejection.
   - **Justification**: [Edge case category] rollback / partial-failure behaviour, plus Rule 2: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." This proposal makes the rollback expectation explicit for the specific GOAR-15 rejection path.

3. **Clarify whether Cloud ID generation happens before or after the model-family gate**
   - **Requirement (proposed)**: The system SHOULD either (a) ensure that `_generate_cloud_id()` is not called until after the model-family check succeeds, or (b) ensure that any Cloud ID generated before a failure is not persisted or reused.
   - **Justification**: Edge case category — rollback / partial-failure behaviour, grounded in Rule 2 (no partial data) and Rule 3/6 (Cloud ID regeneration). This avoids consuming Cloud IDs for rejected attempts.

4. **Stronger protections for claimed printers**
   - **Requirement (proposed)**: For printers with `status == CLAIMED`, any attempt to change `model_number` — even within the same model family — SHOULD either require explicit confirmation or be rejected outright.
   - **Justification**: Rule 11: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." This proposal extends the protection beyond different-family changes to all model-number changes for claimed printers.

5. **Explicit handling of firmware-version changes**
   - **Requirement (proposed)**: Re-registration that changes `firmware_version` while leaving `model_number` unchanged SHOULD be logged (at least at `INFO` level) with the old and new firmware versions, and MAY be subject to compatibility checks if/when business rules for firmware are defined.
   - **Justification**: Edge case category — boundary values / repeated operations. The Jira description calls out `firmware_version` overwrites alongside `model_number`, but no business rule currently governs firmware. Logging firmware changes would improve auditability without committing to a validation policy prematurely.

6. **Align error semantics for missing Authorization headers**
   - **Requirement (proposed)**: The registration, claim, and lookup endpoints SHOULD return consistent error shapes for missing Authorization headers (e.g., always a 422 with the same `detail` structure) to make client handling more predictable.
   - **Justification**: Edge case category — auth failures. While this behavior is partly implemented and tested, codifying it as a requirement ensures future changes do not introduce inconsistent error handling.

7. **Document `_model_family()` as a temporary heuristic**
   - **Requirement (proposed)**: The product documentation SHOULD explicitly state that `_model_family()` is a temporary, heuristic-based implementation and that a future enhancement will replace it with a catalog-driven model-family definition.
   - **Justification**: Edge case category — boundary value / classification. This sets expectations for QA and stakeholders about potential classification inaccuracies in rare or edge-case model numbers.

## 6. Flagged Conflicts

1. **AC2 vs. implementation on "requires explicit confirmation"**
   - AC2 allows for re-registration with a materially different model family to be "rejected or [to] require explicit confirmation." The implementation always rejects such re-registrations and does not offer an explicit confirmation path. There is no direct business rule mandating confirmation, but the AC text suggests an alternate acceptable behavior that is not implemented. This is a scope conflict between the literal AC wording and the current implementation.

2. **Rule 3/6 vs. potential Cloud ID generation timing**
   - Rule 3/6 requires a new Cloud ID on every successful re-registration, but does not explicitly forbid generating a Cloud ID before all checks pass. The current implementation generates a Cloud ID before capability capture and welcome-page printing; GOAR-15’s model-family gate occurs before Cloud ID generation. There is no explicit conflict as implemented, but if Cloud ID generation were moved earlier in future refactors, it could conflict with Rule 2’s requirement to avoid retaining partial data on failure.

If these conflicts are resolved in future tickets (e.g., by adding a confirmation flow or clarifying Cloud ID generation timing), this section should be updated accordingly.

## 7. Open Questions

1. **Firmware validation scope for GOAR-15**
   - **Question**: Should GOAR-15 include any validation or logging specific to `firmware_version` changes, or are firmware semantics intentionally left undefined for this ticket?
   - **Why unresolved**: `docs/business_rules.md` does not mention firmware behavior, and the current implementation accepts any firmware string.
   - **Downstream exclusion**: Test-generation and scoring agents must not assume any firmware validation beyond the existing implementation.

2. **Explicit confirmation flow for different-family re-registrations**
   - **Question**: Is an explicit confirmation mechanism for materially different model families planned, or is outright rejection deemed sufficient to meet AC2?
   - **Why unresolved**: The Jira ticket mentions "requires explicit confirmation" as an alternative, but neither the code nor business rules describe such a flow.
   - **Downstream exclusion**: Scenario-design, test-generation, and scoring agents must exclude any assumptions about confirmation flows from scoring.

3. **Model-family semantics after deregistration**
   - **Question**: After a printer is deregistered (per Rule 12/13), does the system still treat re-registration with a different model family as suspicious, or is the previous model-family information considered obsolete?
   - **Why unresolved**: There is no business rule text connecting deregistration with model-family expectations.
   - **Downstream exclusion**: Agents focused on scenario design, execution, and scoring must not rely on any specific behavior for re-registration after deregistration in the context of GOAR-15.

4. **Scope of structured logging beyond GOAR-15-specific events**
   - **Question**: Should structured logging be expanded to other registration failures (e.g., capability capture failure, XMPP assignment failure, welcome-page print failure), or is GOAR-15’s logging change intended to be limited to model-number change events?
   - **Why unresolved**: Rule 14 is broad; GOAR-15 addresses a specific class of events but does not establish a general policy for all failures.
   - **Downstream exclusion**: Downstream agents must not treat the absence of structured logs for unrelated failure paths as a GOAR-15 defect.

5. **Future replacement of `_model_family()` with an authoritative catalog**
   - **Question**: When a catalog-based model-family definition is introduced, how should discrepancies between catalog and heuristic classifications be handled for existing data?
   - **Why unresolved**: Neither the Jira ticket nor business rules discuss migration or catalog behavior.
   - **Downstream exclusion**: Migration behavior is out of scope; downstream agents must restrict their assumptions to the current heuristic.
