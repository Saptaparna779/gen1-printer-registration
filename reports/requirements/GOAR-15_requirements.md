# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an already-registered serial number previously allowed `register_printer()` to overwrite the stored `model_number` and `firmware_version` with whatever the incoming request supplied, with no validation that the request came from the same physical device. This created a spoofing/takeover risk: a different printer could reuse the same serial number and silently change the recorded model identity tied to that serial. 

GOAR-15 introduces model-number change detection on re-registration, structured warning logs, and a model-family gate that rejects re-registrations which appear to come from a materially different model family. Legitimate re-registrations (same model or same-family updates, including for claimed printers) must continue to succeed, while rejected attempts must leave no partial side effects, in line with the rollback business rules.

## 2. Affected Components

- `app/registration.py`
  - `register_printer()`
    - Adds comparison of existing vs incoming `model_number` on re-registration.
    - Logs a GOAR-15-specific history entry when `model_number` changes.
    - Emits a structured `logger.warning` with discrete `serial_number`, `old_model`, and `new_model` fields when `model_number` changes.
    - Calls `_model_family()` on existing and incoming `model_number` values and raises `RegistrationError` when families differ.
    - Continues to update `printer.model_number` and `printer.firmware_version` after passing the family check.
  - `_model_family(model_number: str) -> str`
    - New helper that derives a "crude" model-family identifier by uppercasing, trimming, splitting on `-`, and dropping the last segment (e.g. `"HP-LJ-4200"` → `"HP-LJ"`).
  - `CLAIM_CODE_TTL_MINUTES`, `_generate_cloud_id()`, `_generate_printer_email_id()`, `_generate_claim_code()`, `_capture_capabilities()`, `claim_printer()`, `_rollback_registration()`, `deregister_printer()`
    - No functional changes for GOAR-15 (only referenced here to make clear they remain in their prior behavior).

- `tests/features/GOAR-15.feature`
  - New BDD feature file containing 20 Scenarios (including one Scenario Outline) that map 1:1 to `reports/testcases/GOAR-15_test_cases.md` (TC-GOAR-15-01 through TC-GOAR-15-20). These scenarios exercise:
    - Model-number change detection and logging on re-registration.
    - Acceptance vs rejection based on model-family classification.
    - Case- and whitespace-insensitive handling of model numbers.
    - Authorization failures for registration, claim, and lookup endpoints.
    - Behavior for claimed printers undergoing re-registration.
    - Zero-side-effect guarantees for rejected re-registrations.

- `tests/steps/test_GOAR-15_steps.py`
  - New pytest-bdd step definitions backing `tests/features/GOAR-15.feature`.
  - Uses `fastapi.testclient.TestClient` and the app’s public HTTP API (`/printers/register`, `/printers/claim`, `/printers/{id}`) via the shared `client` fixture and a no-auth helper.
  - Captures `logging.WARNING` records from the `app.registration` logger to validate warning logs and their structured fields.
  - Asserts on HTTP status codes, response bodies, history entries, ownership, and absence/presence of side effects.

## 3. Applicable Business Rules

1. **Rule 1 — Registration only successful if Welcome Page prints**
   - Exact sentence: "Registration is successful **only if** the Welcome/Info Page prints."
   - Relation: For GOAR-15, rejected re-registrations must fail before the Welcome Page stage and thus never be considered successful registrations. The new model-family mismatch `RegistrationError` is raised before welcome-page generation, ensuring these spoofing attempts do not reach the final success checkpoint.

2. **Rule 2 — Rollback on failure / no partial data**
   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - Relation: GOAR-15 requires that a re-registration rejected due to model-family mismatch or authorization failure leaves no partial side effects (e.g., no new Cloud ID, email ID, capabilities, or XMPP node). The new tests explicitly assert that on rejection:
     - The stored `cloud_id`, `printer_email_id`, and `xmpp_node` remain unchanged.
     - No new capability or XMPP-related history entries are added.
     - Only a review-flag entry is present. 
     This enforces the no-partial-data requirement for rejected re-registrations that fail before the Welcome Page.

3. **Rule 3 — New Cloud ID on every re-registration**
   - Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - Relation: GOAR-15 tests verify that accepted re-registrations (same or same-family model numbers) still produce a new Cloud ID distinct from the prior one. For rejections due to model-family mismatch, the checks ensure that a new Cloud ID is not issued, implicitly respecting that only successful re-registrations should consume new Cloud IDs.

4. **Rule 6 — Cloud ID uniqueness & regeneration**
   - Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - Relation: Scenario "Re-registering with matching model number and updated firmware completes end-to-end" asserts that a new Cloud ID is present and different from the original when re-registration succeeds, aligning with the "regenerated on every re-registration" requirement.

5. **Rule 7 — Printer Email ID uniqueness**
   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."
   - Relation: GOAR-15 does not alter email ID generation logic but includes a scenario where re-registration results in a new printer email ID different from the original. This ensures that the new checks around model-family mismatch do not break the expectation that successful re-registrations issue a new unique printer email ID.

6. **Rule 8 — Claim Code behavior**
   - Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page."
     - Sub-bullets:
       - "Expired or invalid claim codes must be rejected."
       - "A claim code can only be used once."
   - Relation: GOAR-15 tests around re-registering already claimed printers rely on the existing claim-code lifecycle. They confirm that claim codes continue to behave correctly when re-registration occurs, and that rejection paths for model-family mismatches do not inadvertently reset or reissue claim codes in violation of the "only be used once" rule.

7. **Rule 9 — Visibility only after claim**
   - Exact sentence: "A printer becomes visible to a user's applications only after a successful claim."
   - Relation: Scenarios involving claimed printers (e.g., re-registering a claimed printer with an unchanged model number) ensure that claim status is preserved and that the new re-registration behavior does not accidentally unclaim the printer or make it visible to another user.

8. **Rule 11 — Do not overwrite ownership**
   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Relation: GOAR-15’s model-family gate is primarily motivated by this rule. The tests confirm that:
     - Same-family model-number changes for claimed printers succeed but preserve `owner_user_id` and `status == "CLAIMED"`.
     - Different-family model-number changes are rejected and the stored record (including ownership) is left unchanged.
     This prevents a different physical device from using the same serial number to silently take over a claimed printer’s identity.

9. **Rule 13 — Cloud ID after deregistration**
   - Exact sentence: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)."
   - Relation: While GOAR-15 does not explicitly cover deregistration, any accepted re-registrations after a prior deregistration must still align with this rule. The existing `register_printer()` logic continues to generate a new Cloud ID whenever registration occurs, and the new gate does not interfere with this behavior.

10. **Rule 14 — Observability via logging/telemetry**
    - Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
    - Relation: GOAR-15 implements and tests structured logging of model-number changes on re-registration. In `register_printer()`, the warning log is emitted with an `extra` dict containing `serial_number`, `old_model`, and `new_model`. BDD scenarios assert both that a warning is logged mentioning these values and that a warning log record exposes them as discrete fields. This aligns the implementation with the structured logging requirement and ensures that suspicious re-registrations are observable.

## 4. Original Acceptance Criteria

Copied from `jira_context/GOAR-15_live.md`:

1. "At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review."
2. "(Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation."
3. "Legitimate re-registrations with matching or compatible model/firmware data continue to work as before."

## 5. Adopted Additional Requirements

### Requirement 5.1 — Case- and Whitespace-Insensitive Model-Number Comparison

- **Requirement statement**: On re-registration, `model_number` comparisons used to decide whether a change has occurred and whether to flag/log the event MUST treat case and leading/trailing whitespace as insignificant. For example, `"HP-LJ-2055"` and `" hp-lj-2055"` MUST be treated as the same model number for purposes of determining whether a model-number change occurred.
- **Justification**: Edge case category: boundary value / normalization. The implementation (`register_printer()`) uses `strip().upper()` when comparing existing and incoming model numbers. Tests in `tests/features/GOAR-15.feature` (e.g., "Re-registering with only whitespace/case differences in model number is treated as unchanged") codify this behavior and ensure that trivial formatting differences do not generate false-positive flags or rejections.

### Requirement 5.2 — Zero Side Effects on Model-Family Mismatch Rejection

- **Requirement statement**: When a re-registration attempt is rejected due to a model-family mismatch, the system MUST:
  - Not change the stored `cloud_id`, `printer_email_id`, or `xmpp_node`.
  - Not create or update any capability records.
  - Not update the serial index.
  - Only append a single review-flag history entry, with no additional history entries indicating capabilities, XMPP assignment, or welcome-page printing.
- **Justification**: [Exact rule sentence] "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2). Rejections triggered by model-family mismatch occur before welcome-page generation and therefore fall under this rollback rule. BDD scenarios "A rejected re-registration produces zero partial side effects" and "A different-family model number change is rejected and the stored record is left unchanged" enforce this requirement.

### Requirement 5.3 — Structured Warning Logs for Model-Number Changes

- **Requirement statement**: Whenever a re-registration changes the `model_number` (after normalization), the system MUST emit a `WARNING` log from the `app.registration` logger that:
  - Includes a human-readable message indicating the serial number and the old and new `model_number` values; and
  - Attaches `serial_number`, `old_model`, and `new_model` as structured log fields (e.g., via the `extra` dict), so they can be consumed as discrete attributes by logging/telemetry pipelines.
- **Justification**: [Exact rule sentence] "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." (Rule 14). Model-number changes on re-registration are security-significant events even when the re-registration succeeds; structured warning logs ensure they are observable and queryable by operations and security tooling.

### Requirement 5.4 — Model-Family Gate Applies to Claimed and Unclaimed Printers

- **Requirement statement**: The model-family mismatch gate MUST be applied uniformly to all re-registrations, regardless of whether the printer is currently in `REGISTERED` or `CLAIMED` status. A re-registration that attempts to change the `model_number` to a different model family MUST be rejected even if the printer is already claimed, and this rejection MUST preserve the existing owner and status.
- **Justification**: [Exact rule sentence] "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11). Applying the same gate to claimed printers ensures that a different physical device cannot use the same serial number to replace the model identity of a claimed printer, thereby protecting existing ownership.

### Requirement 5.5 — Claim Preservation on Accepted Re-registrations

- **Requirement statement**: On successful re-registration of a claimed printer (whether the `model_number` is unchanged or changes within the same model family), the system MUST:
  - Preserve `owner_user_id` and `status == "CLAIMED"`.
  - Not issue a new claim code or reset the claim state.
  - Generate a new Cloud ID and, if appropriate, new printer email ID and XMPP node, without altering ownership.
- **Justification**: [Exact rule sentence] "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11). Re-registration changes around model numbers and Cloud IDs must coexist with stable ownership semantics; tests explicitly verify that ownership is preserved across such re-registrations.

### Requirement 5.6 — Auth Failures for Registration, Claim, and Lookup

- **Requirement statement**: The system MUST enforce the following for all relevant endpoints:
  - Registration (`POST /printers/register`):
    - Requests with no `Authorization` header MUST be rejected with a validation error indicating that the header field is required.
    - Requests with an invalid bearer token MUST be rejected with HTTP 401 and a response body `{ "detail": "Invalid or expired token" }`.
  - Claim (`POST /printers/claim`):
    - Requests with no `Authorization` header MUST be rejected with a validation error indicating that the header field is required.
    - Requests with an invalid bearer token MUST be rejected with HTTP 401 and a response body `{ "detail": "Invalid or expired token" }`.
  - Lookup (`GET /printers/{printer_id}`):
    - Requests with no `Authorization` header MUST be rejected with a validation error indicating that the header field is required.
    - Requests with an invalid bearer token MUST be rejected with HTTP 401 and a response body `{ "detail": "Invalid or expired token" }`.
- **Justification**: Edge case category: auth failures. While business_rules.md does not spell out authentication behavior, ensuring consistent rejection semantics for missing/invalid auth headers is a standard boundary/auth edge case for any registration/ownership-related API. The new GOAR-15 BDD scenarios codify and verify this behavior.

### Requirement 5.7 — Model-Family Heuristic is a Stand-in for a Future Catalog

- **Requirement statement**: The `_model_family()` helper MUST:
  - Normalize `model_number` by trimming whitespace and uppercasing; and
  - Derive the family identifier by splitting on `-` and dropping the last segment when more than one segment is present, or using the single segment otherwise.
  This heuristic is accepted as the current source of truth for determining "materially different" model families but is explicitly recognized as a placeholder to be replaced by an authoritative catalog in future work.
- **Justification**: Edge case category: boundary value / classification heuristic. The jira diff comment and the helper’s docstring both state that `_model_family()` is "crude" and "intentionally simple". By fixing its behavior in a requirement, we ensure tests can rely on consistent family classification across representative pairs (as in the Scenario Outline) while leaving room for later enhancement.

### Requirement 5.8 — No Capability Recapture on Re-registration When Capabilities Already Exist

- **Requirement statement**: On re-registration, if capabilities already exist for the printer (`store.get_capabilities(printer_id)` returns a record), the system MUST NOT recapture or overwrite capabilities and MUST instead log a history entry indicating that capabilities were already on record and recapture was skipped.
- **Justification**: [Exact rule sentence] "Printer capabilities are captured once at registration time so downstream services never need to re-query the device." (Rule 4). GOAR-15’s tests (including TC-GOAR-15-20 as referenced in the feature file header) rely on this behavior when verifying that rejected re-registrations do not recapture capabilities and that accepted re-registrations respect the "capture once" rule.

## 6. Open Questions

### Open Question 6.1 — Firmware Version Validation Scope

- **The question**: The Jira description states that re-registration updates both `model_number` and `firmware_version` with no validation. GOAR-15’s implementation and tests explicitly gate and log changes to `model_number`, but do not introduce any validation or logging specific to `firmware_version`. Is firmware spoofing (e.g., a device reporting a different firmware version that does not match the expected range for the model) intentionally out of scope for GOAR-15, or should additional acceptance criteria be added for firmware validation?
- **Why unresolved**: `docs/business_rules.md` does not mention firmware version semantics, and the diff plus BDD scenarios do not introduce or reference any firmware-specific validation beyond ensuring that firmware changes do not break legitimate re-registrations.
- **Downstream exclusion**: Until clarified, downstream agents MUST NOT introduce tests or scoring criteria that assume any particular behavior for firmware version validation beyond what is already implemented (i.e., accepting any firmware string as long as other conditions are met).

### Open Question 6.2 — "Requires Explicit Confirmation" Path for Model-Family Changes

- **The question**: Original AC #2 states that re-registration with a materially different model family is "rejected or requires explicit confirmation." The current implementation always rejects such re-registrations with a `RegistrationError` and does not provide any explicit confirmation path (e.g., an override flag or an administrative approval mechanism). Is the "explicit confirmation" option deferred to a future ticket, or should GOAR-15 be considered incomplete without an implemented confirmation flow?
- **Why unresolved**: Neither the diff nor `app/registration.py` contains an override mechanism, and `docs/business_rules.md` is silent on confirmation workflows. The Jira ticket does not clarify whether the rejection-only behavior is sufficient.
- **Downstream exclusion**: Until clarified, downstream agents MUST treat the absence of a confirmation path as acceptable for GOAR-15 and MUST NOT fail tests solely because a confirmation override does not exist. Any tests related to confirmation flows should be excluded from scoring.

### Open Question 6.3 — Future Replacement of `_model_family()` with an Authoritative Catalog

- **The question**: The `_model_family()` helper is described as "crude" and a stand-in for a real model catalog/lookup. When an authoritative model-family catalog is introduced, how should discrepancies between the heuristic and the catalog be handled, especially for existing printers whose model-family classification might change? Should historical classifications be updated, or should the catalog apply only to future registrations?
- **Why unresolved**: `docs/business_rules.md` contains no guidance on model-family concepts, and the Jira ticket explicitly acknowledges the lack of an authoritative catalog. There is no existing migration plan in the repo.
- **Downstream exclusion**: Downstream agents MUST restrict tests and scoring to the current heuristic behavior as codified in `_model_family()` and the Scenario Outline examples. Migration/upgrade behavior once a catalog is introduced is out of scope.

### Open Question 6.4 — Interaction with Deregistration and Re-registration

- **The question**: Business Rule 13 states that re-registration after deregistration always generates a new Cloud ID. GOAR-15 focuses on re-registration of existing serial numbers that still have printer records in the store. How should the model-family gate behave when a printer has been deregistered and then re-registered with the same serial number but a different model family? Should deregistration reset any notion of model-family expectations, or should the system still treat a different-family re-registration as suspicious and apply the same rejection/flagging behavior?
- **Why unresolved**: The Jira ticket does not describe any deregistration scenarios, the diff does not modify `deregister_printer()`, and `docs/business_rules.md` does not discuss model-family behavior in a post-deregistration context.
- **Downstream exclusion**: Until clarified, downstream agents MUST NOT create or score tests that depend on specific model-family behavior for re-registration after deregistration; they should limit GOAR-15 validation to re-registrations where an existing printer record remains.

### Open Question 6.5 — Scope of Structured Logging Beyond GOAR-15

- **The question**: GOAR-15 introduces structured warning logs for model-number changes on re-registration, in line with Rule 14’s observability requirement. Should similar structured logging be added for other registration failures (e.g., capability capture failures, XMPP assignment failures, welcome-page print failures), or is GOAR-15’s logging change intended to be narrowly scoped to model-number spoofing only?
- **Why unresolved**: `docs/business_rules.md` calls for structured logging of registration failures in general but does not prioritize specific failure types. The Jira ticket is clearly focused on model-number spoofing, with no mention of broader logging enhancements.
- **Downstream exclusion**: Downstream agents MUST confine structured-logging-related tests to the model-number change scenarios described in GOAR-15 and MUST NOT fail the ticket based on the absence of structured logs for other failure types.
