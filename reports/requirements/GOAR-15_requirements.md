# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an existing printer serial number was previously allowed to overwrite `model_number` and `firmware_version` on the stored printer record with no validation, which created a spoofing risk: a completely different physical device could re-use the same serial number and silently replace the original printer identity. This ticket adds protections so that any `model_number` change on re-registration is logged and flagged for review, and re-registration with a materially different model family is rejected outright. Legitimate same-model and same-family re-registrations, including for already-claimed printers, must still behave as before (Cloud ID regeneration, email/XMPP assignment, ownership preserved) and rejected re-registrations must leave no partial side effects.

## 2. Affected Components

From the diff and implementation:

- `tests/features/GOAR-15.feature`
  - New Gherkin feature file describing end-to-end scenarios for GOAR-15.
  - Covers re-registration behavior for model-number changes, model-family rejection, claimed printer behavior, auth failures, lookup behavior, logging structure, and side-effect rollback.

- `tests/steps/test_GOAR-15_steps.py`
  - New pytest-bdd step definitions implementing the scenarios in `tests/features/GOAR-15.feature`.
  - Interacts with the service via HTTP through `app.main.app` using `TestClient`, exercising `/printers/register`, `/printers/claim`, and `/printers/{printer_id}`.

- `app/registration.py`
  - `register_printer()`
    - Adds GOAR-15 logic in the `if existing:` (re-registration) branch:
      - Detects `model_number` change on re-registration.
      - Logs a history entry and flags the event for review.
      - Emits a structured `logger.warning` with discrete fields `serial_number`, `old_model`, `new_model`.
      - Rejects re-registration with `RegistrationError` if `_model_family(existing_model)` and `_model_family(incoming_model)` differ.
    - Leaves existing Cloud ID regeneration, email ID generation, claim code handling, capabilities capture, XMPP assignment, and rollback unchanged.
  - Adds `_model_family()` helper to classify model numbers into families.
  - Configures module-level `logger = logging.getLogger(__name__)` to support structured warnings.

## 3. Applicable Business Rules

### Rule 1 — Registration success depends on Welcome/Info Page

> "Registration is successful **only if** the Welcome/Info Page prints."  
> (docs/business_rules.md, Registration section)

Relation to this ticket:
- Rejected re-registrations due to model-family mismatch must occur before the Welcome Page prints, and must be treated as failed registrations. The scenarios "A rejected re-registration produces zero partial side effects" and related steps verify that such failures do not proceed to the Welcome Page or create inconsistent success indications.

### Rule 2 — Rollback on failure before Welcome Page

> "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."  
> (docs/business_rules.md, Registration section)

Relation to this ticket:
- GOAR-15 requires that a rejected re-registration (model-family mismatch) leaves no partial side effects. The implementation raises `RegistrationError` in `register_printer()` before Cloud ID creation and persistence steps, and the scenarios "A rejected re-registration produces zero partial side effects" and "A different-family model number change is rejected and the stored record is left unchanged" assert that Cloud ID, email, XMPP node, and history side-effect entries are unchanged except for the review flag.

### Rule 3 — Re-registration always generates a new Cloud ID

> "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."  
> (docs/business_rules.md, Registration section)

Relation to this ticket:
- Accepted re-registrations (same model or same-family model changes) must continue to generate a new Cloud ID. The implementation retains `_generate_cloud_id()` assignment on every call and the scenarios "Re-registering with a same-family but different revision is accepted" and "Re-registering with matching model number and updated firmware completes end-to-end" assert the presence of a new Cloud ID and that it differs from the original.

### Rule 4 — Capabilities capture once at registration

> "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."  
> (docs/business_rules.md, Registration section)

Relation to this ticket:
- GOAR-15’s rejection behavior must not inadvertently trigger capabilities recapture for rejected re-registrations, and accepted re-registrations should preserve the intended behavior around capabilities history. The scenarios for full re-registration success and for rejected re-registration with zero side effects validate capability-related history entries.

### Rule 5 — XMPP node assignment

> "A printer is assigned an XMPP node as part of registration, enabling persistent cloud connectivity."  
> (docs/business_rules.md, Registration section)

Relation to this ticket:
- Accepted, legitimate re-registrations must continue to assign (or retain) XMPP nodes, while rejected re-registrations must not alter XMPP assignment. The scenarios "Re-registering with matching model number and updated firmware completes end-to-end" and "A rejected re-registration produces zero partial side effects" check both positive and negative expectations for XMPP assignment.

### Rule 6 — Cloud ID uniqueness & regeneration

> "Cloud ID: system-generated, unique, regenerated on every re-registration."  
> (docs/business_rules.md, Cloud ID, Printer Email ID & Claim Code section)

Relation to this ticket:
- GOAR-15 adds extra logic before Cloud ID generation for spoofing detection. It must not violate the requirement that accepted re-registrations produce new Cloud IDs. Several scenarios explicitly assert new Cloud IDs that differ from prior values, and rejection scenarios confirm that Cloud IDs remain unchanged when re-registration is rejected.

### Rule 7 — Printer Email ID uniqueness

> "Printer Email ID: must be globally unique; used for Email-to-Print."  
> (docs/business_rules.md, Cloud ID, Printer Email ID & Claim Code section)

Relation to this ticket:
- Legitimate re-registrations must continue to receive new, unique email IDs; rejected re-registrations must not alter email IDs. The scenario "Re-registering with matching model number and updated firmware completes end-to-end" asserts a new printer email address different from the original, and the side-effect rollback scenario asserts email address unchanged for rejected re-registrations.

### Rule 8 — Claim Code as temporary, single-use token

> "Claim Code: a **temporary** security token printed on the Welcome Page.  
> - Expired or invalid claim codes must be rejected.  
> - A claim code can only be used once."  
> (docs/business_rules.md, Cloud ID, Printer Email ID & Claim Code section)

Relation to this ticket:
- GOAR-15’s scenarios include registering and claiming printers, and then re-registering them. The fix must not violate claim code semantics, and must preserve claim behavior on re-registration, particularly for already-claimed printers. Scenarios for claimed printers validate that ownership and claimed status remain intact.

### Rule 9–11 — Claiming & Ownership

> "A printer becomes visible to a user's applications only after a successful claim." (Rule 9)

> "Claiming enables subscriptions (e.g. Instant Ink) and remote management." (Rule 10)

> "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)

Relation to this ticket:
- GOAR-15 directly enforces Rule 11 in the spoofing context by rejecting re-registrations that appear to come from a different physical device (different model family) sharing a serial number. Scenarios "Re-registering a claimed printer with an unchanged model number preserves ownership" and "Re-registering a claimed printer with a same-family model change still flags it for review" verify that claimed printers retain their owner identity and status through legitimate re-registrations.

### Rule 12–13 — Deregistration

> "Deregistration must remove all cloud associations and printer data (GDPR compliance)." (Rule 12)

> "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." (Rule 13)

Relation to this ticket:
- These rules are not directly exercised by the GOAR-15 diff (no changes in `deregister_printer()`), but they constrain expectations for re-registration behavior. The new re-registration protections must not interfere with post-deregistration re-registration semantics; however, this ticket’s tests do not explicitly cover that path.

### Rule 14 — Observability

> "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, 'Limited observability' as a known platform risk."  
> (docs/business_rules.md, Non-Functional Expectations section)

Relation to this ticket:
- GOAR-15 explicitly implements structured logging for model-number changes on re-registration: history entries flagged for review and `logger.warning` records with discrete fields. Scenarios verify that warnings are logged, that they include serial/model information, and that discrete structured fields are present on the log record.

## 4. Original Acceptance Criteria

From `jira_context/GOAR-15_live.md`:

> At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review.
>
> (Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation.
>
> Legitimate re-registrations with matching or compatible model/firmware data continue to work as before.

## 5. Adopted Additional Requirements

### 5.1 Structured logging fields for observability

**Requirement statement:**  
For any re-registration where `model_number` changes, the warning log entry must include discrete structured fields `serial_number`, `old_model`, and `new_model` so downstream systems can reliably filter and analyze suspicious events.

**Justification:**  
- [exact rule sentence] "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, 'Limited observability' as a known platform risk." (docs/business_rules.md, Rule 14)

The diff and tests already implement and assert this behavior (Scenario "The model-number-change warning log carries discrete structured fields"), so it is adopted as explicit AC.

### 5.2 No partial side effects on rejected re-registration

**Requirement statement:**  
When a re-registration is rejected due to a model-family mismatch, the printer's `cloud_id`, `printer_email_id`, and `xmpp_node` must remain unchanged, and the only new history entry added must be the review-flag entry; no Cloud identity creation, capability capture, XMPP assignment, or welcome page print may be recorded for the rejected attempt.

**Justification:**  
- [exact rule sentence] "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (docs/business_rules.md, Rule 2)

Scenarios "A different-family model number change is rejected and the stored record is left unchanged" and "A rejected re-registration produces zero partial side effects" already encode this requirement and confirm the implementation.

### 5.3 Cloud ID must not change on rejected re-registration

**Requirement statement:**  
For re-registration attempts that are rejected as model-family mismatches, no new Cloud ID must be generated, and the existing `cloud_id` must remain in place for the printer.

**Justification:**  
- [exact rule sentence] "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." (docs/business_rules.md, Rule 3)
- [exact rule sentence] "Cloud ID: system-generated, unique, regenerated on every re-registration." (docs/business_rules.md, Rule 6)

Combined with Rule 2’s rollback constraint, these rules imply that failed re-registrations must not consume Cloud IDs; the diff and tests validate that rejected re-registrations leave `cloud_id` unchanged.

### 5.4 Claimed printers preserve ownership on accepted re-registration

**Requirement statement:**  
When a claimed printer is re-registered with either an unchanged `model_number` or a same-family `model_number` change, the re-registration must succeed without altering `owner_user_id` or changing status away from `CLAIMED`.

**Justification:**  
- [exact rule sentence] "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (docs/business_rules.md, Rule 11)

Scenarios "Re-registering a claimed printer with an unchanged model number preserves ownership" and "Re-registering a claimed printer with a same-family model change still flags it for review" encode this requirement.

### 5.5 Model-family determination must be case- and whitespace-insensitive

**Requirement statement:**  
Model-family comparison for re-registration must treat variations in case and leading/trailing whitespace as non-material. A `model_number` differing only by case or surrounding spaces must not be treated as a model-family mismatch.

**Justification:**  
- [edge case category: boundary] Variations in case and whitespace represent boundary/format edge cases for model classification; misclassifying them as different families would create false rejection of legitimate re-registrations.

The `_model_family()` helper already normalizes `model_number` with `.strip().upper()`, and the scenarios "Re-registering with a differently-cased same-family model number still succeeds" and "Re-registering with only whitespace/case differences in model number is treated as unchanged" validate this requirement.

### 5.6 Authorization enforcement for register, claim, and lookup

**Requirement statement:**  
All registration, claim, and printer lookup endpoints must enforce Authorization headers, rejecting requests that either omit the `Authorization` header or present an invalid bearer token.

**Justification:**  
- [edge case category: auth] Missing or invalid tokens are standard authorization failure edge cases; ensuring consistent rejection across endpoints is necessary for secure registration and ownership management.

Scenarios "Registering a printer with no Authorization header is rejected", "Registering a printer with an invalid bearer token is rejected", "Claiming a printer with no Authorization header is rejected", "Claiming a printer with an invalid bearer token is rejected", "Looking up a printer with no Authorization header is rejected", and "Looking up a printer with an invalid bearer token is rejected" already require this behavior and exercise it via HTTP.

## 6. Open Questions

### 6.1 Firmware version validation for spoofing

**The question:**  
Should re-registration also flag or gate changes in `firmware_version` as part of spoofing detection (e.g., a radically different firmware version that may indicate a different physical device), or is the model-family check sufficient?

**Why it cannot be resolved:**  
- The Jira description explicitly notes that `firmware_version` is overwritten without validation on re-registration, but the ACs only mention `model_number`.  
- The diff and tests implement only model-number-based detection and do not mention firmware-based rules.

**Downstream exclusion:**  
- Test design and scoring must not treat firmware-change validation as required behavior for GOAR-15. Any tests around firmware spoofing should be marked exploratory or out of scope.

### 6.2 Explicit confirmation vs outright rejection for materially different model families

**The question:**  
The AC states that materially different model-family re-registrations are "rejected or require explicit confirmation." Is outright rejection the intended behavior, or should there be a confirmation mechanism (e.g., user/admin override) in a future iteration?

**Why it cannot be resolved:**  
- The current implementation and tests only cover outright rejection; no confirmation flow exists.  
- The AC uses "or", leaving room for interpretation.

**Downstream exclusion:**  
- Downstream agents must not assume any confirmation mechanism exists. Scoring must only evaluate the rejection behavior that is present in code and tests.

### 6.3 Model-family catalog accuracy and future changes

**The question:**  
Is the current `_model_family()` heuristic (`strip().upper().split("-")` and dropping the last component) considered acceptable long-term, or is a formal model catalog planned that could alter family boundaries and, therefore, rejection behavior?

**Why it cannot be resolved:**  
- The helper’s docstring admits it is "Intentionally simple for now; a real implementation would use a proper model catalog/lookup."  
- No business rule defines authoritative model-family mapping.

**Downstream exclusion:**  
- Until a formal catalog is introduced, agents must score only the heuristic behavior currently implemented; they cannot assume more accurate classification or different family definitions.

### 6.4 Interaction between deregistration and GOAR-15 safeguards

**The question:**  
After deregistration and subsequent re-registration of the same serial number, should GOAR-15’s model-family detection still apply in exactly the same way (i.e., reject different-family registrations), or is there any intended difference when the prior registration has been fully removed per Rule 12?

**Why it cannot be resolved:**  
- Business Rule 13 requires a new Cloud ID after deregistration, but does not discuss model-family checks.  
- GOAR-15 tests do not exercise the deregister-then-reregister path.

**Downstream exclusion:**  
- Tests and scoring must not infer any special handling for post-deregistration re-registration beyond existing business rules; GOAR-15’s behavior for that path remains unspecified.

### 6.5 Review workflow for flagged model-number changes

**The question:**  
What is the expected operational workflow for "flagged for review" model-number changes (e.g., alerting, dashboards, manual investigation queues), and are there any SLAs for handling such flags?

**Why it cannot be resolved:**  
- Business Rule 14 mandates observability via logging but does not define operational processes or SLAs.  
- The Jira ticket mentions "flagged/logged as a notable event for review" but does not specify downstream systems.

**Downstream exclusion:**  
- Agents must limit scoring to the presence and content of logs and history; they must not attempt to validate or assume any operational review processes.
