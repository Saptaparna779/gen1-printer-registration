# Requirements Report — GOAR-15

## 1. Summary

Re-registration currently allows an existing printer record (matched by serial number) to have its `model_number` and `firmware_version` overwritten without any validation that the incoming data represents the same physical device. This creates a spoofing risk: a different printer can reuse a serial number and silently replace the original device’s identity.

GOAR-15 introduces validation and observability around model changes on re-registration. Any change to `model_number` on re-registration is flagged in the printer’s registration history and logged as a warning for review. If the incoming `model_number` appears to belong to a materially different model family than the existing one, the re-registration is rejected outright so a serial number cannot be quietly reused by a different physical printer. Legitimate re-registrations, where model/firmware data is unchanged or compatible, must continue to succeed and follow the normal registration flow.

## 2. Affected Components

Based on reports/GOAR-15_diff.txt, the diff touches the following files and logical components:

- tests/features/GOAR-15.feature
  - New Gherkin feature file: "Feature: Re-registration flags and gates model number changes".
  - Contains scenarios that exercise:
    - Re-registration with changed model numbers being logged and flagged.
    - Authorization and authentication checks for registration, claim, and lookup (missing Authorization header, invalid bearer token).
    - Re-registration outcomes for unchanged, same-family, and different-family model numbers.
    - Re-registration behavior for claimed printers (unchanged and same-family changed models) preserving ownership and claim status.
    - Structured warning log records carrying discrete fields for serial number, old model, and new model.
    - Rejection behavior with no partial side effects (Cloud ID, printer email, XMPP node, and capability-related history unchanged).

- tests/steps/test_GOAR-15_steps.py
  - New pytest-bdd step definitions module that binds the Gherkin scenarios to actual HTTP calls.
  - Affects the following logical flows via TestClient against app.main:
    - Registration endpoint: `POST /printers/register`.
    - Claim endpoint: `POST /printers/claim`.
    - Lookup endpoint: `GET /printers/{printer_id}`.
  - Helper functions:
    - `_no_auth_client()` — constructs a TestClient without a pre-attached Authorization header.
    - `_register(client, serial_number, model_number, firmware_version)` — thin wrapper around `POST /printers/register`.
    - `_claim(client, claim_code, user_id)` — thin wrapper around `POST /printers/claim`.
  - Given steps:
    - "a printer has been registered with serial number …" — registers a printer and stores response fields (`printer_id`, `cloud_id`, `printer_email_id`, `claim_code`, `xmpp_node`, `history`).
    - "a printer has been registered and claimed: serial number … claimed by user …" — registers then claims a printer, ensuring status `CLAIMED` and owner id are set, and storing registration context.
  - When steps:
    - Re-registration with specific serial, model, and firmware, capturing HTTP response, updated status, Cloud ID, printer email, XMPP node, and warning log records (`caplog` at WARNING level for logger `app.registration`).
    - Registration, claim, and lookup requests with no Authorization header or invalid bearer tokens.
    - Lookup of existing printers using context-stored `printer_id`.
  - Then steps:
    - Assertions that:
      - Re-registrations succeed or are rejected as appropriate (200 for accepted, 422 for model family mismatch, 401 for invalid tokens, 422 for missing Authorization header).
      - Registration history includes or omits model-number-change and review-flag entries as specified.
      - Warning logs mention serial number, old model, new model, and/or expose discrete structured fields (`serial_number`, `old_model`, `new_model`).
      - Cloud ID, printer email, XMPP node, and history entries behave correctly on successful re-registration and on rejected re-registration (no partial side effects; history only extended with review-flag entries).
      - Ownership and claim status remain unchanged for claimed printers after certain re-registrations.

Note: The app-level implementation (e.g., app/registration.py) is not directly shown in reports/GOAR-15_diff.txt, but these tests clearly exercise and assert behavior of the registration, claim, and lookup endpoints consistent with the Jira ticket.

## 3. Applicable Business Rules

From docs/business_rules.md, the following rules apply directly to GOAR-15:

### Rule 1 — Registration success depends on Welcome Page print

Exact sentence:
> "Registration is successful **only if** the Welcome/Info Page prints."

Relation to this ticket:
- GOAR-15 affects re-registration behavior and outcomes (accepted vs rejected). For accepted re-registrations, the registration flow must still culminate in a successful Welcome Page print for the registration to be considered successful. The tests reference registration history entries including "Welcome page printed successfully; registration complete" to confirm that the end-to-end success criteria are maintained.

### Rule 2 — Rollback on failure, no partial data retained

Exact sentence:
> "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."

Relation to this ticket:
- GOAR-15 introduces re-registration rejections (e.g., model family mismatch). Those rejections must behave like registration failures under Rule 2: they must not leave partial side effects such as new Cloud IDs, printer emails, capabilities, or XMPP nodes.
- The feature file includes scenarios "A different-family model number change is rejected and the stored record is left unchanged" and "A rejected re-registration produces zero partial side effects", and the step definitions assert that Cloud ID, printer email, XMPP node, and history side-effects are unchanged except for a review-flag entry. These tests are designed to validate compliance with Rule 2.

### Rule 3 — Cloud ID regeneration on re-registration

Exact sentence:
> "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."

Relation to this ticket:
- GOAR-15 must not break Cloud ID regeneration semantics for successful re-registrations. The feature file includes scenarios where re-registration with matching or same-family model numbers and updated firmware produces a "new Cloud ID different from the original".
- For rejected re-registrations, no new Cloud ID should be generated, and the existing Cloud ID must remain unchanged. The scenario "A different-family model number change is rejected and the stored record is left unchanged" confirms that Cloud ID is unchanged in the lookup.

### Rule 4 — One-time capability capture

Exact sentence:
> "Printer capabilities are captured once at registration time so downstream services never need to re-query the device."

Relation to this ticket:
- GOAR-15 should not cause capabilities to be recaptured or modified on re-registration except as already allowed by existing behavior. The feature file notes (for TC-GOAR-15-20) that "no capabilities re-captured" can only be verified indirectly via history entries, and the scenario "A rejected re-registration produces zero partial side effects" asserts that capability-related history entries are not added on rejection.

### Rule 5 — XMPP node assignment on registration

Exact sentence:
> "A printer is assigned an XMPP node as part of registration, enabling persistent cloud connectivity."

Relation to this ticket:
- GOAR-15 scenarios assert that successful re-registrations still assign or preserve XMPP nodes appropriately, and that rejected re-registrations do not cause new XMPP node assignments or changes. This ensures that the registration flow’s XMPP behavior remains correct and that rejections do not violate Rule 2.

### Rule 6 — Cloud ID uniqueness and regeneration

Exact sentence:
> "Cloud ID: system-generated, unique, regenerated on every re-registration."

Relation to this ticket:
- GOAR-15 must preserve the guarantees of Cloud ID regeneration on successful re-registration. Scenarios explicitly assert that re-registration succeeds "with a new Cloud ID different from the original" and that a "new Cloud ID is present" in several success cases. For rejected re-registrations, the tests confirm that Cloud ID remains unchanged and no new Cloud IDs are generated.

### Rule 7 — Printer Email ID uniqueness

Exact sentence:
> "Printer Email ID: must be globally unique; used for Email-to-Print."

Relation to this ticket:
- GOAR-15 must not break Printer Email uniqueness. A scenario checks that re-registration with matching model and updated firmware issues "a new printer email address … different from the original", while another rejection scenario ensures the printer email remains unchanged. This combination preserves uniqueness semantics for successful registrations and ensures that rejections do not inadvertently create or modify email IDs.

### Rule 8 — Claim Code behavior

Exact sentence:
> "Claim Code: a **temporary** security token printed on the Welcome Page.
> - Expired or invalid claim codes must be rejected.
> - A claim code can only be used once."

Relation to this ticket:
- GOAR-15 includes scenarios that exercise claiming behavior and test authentication (Authorization header) independently of claim code validity. While the diff does not change claim code semantics, the ticket’s focus on spoofing and ownership makes the claim code a relevant part of the overall ownership and security story.

### Rule 9 — Visibility after claim

Exact sentence:
> "A printer becomes visible to a user's applications only after a successful claim."

Relation to this ticket:
- Scenarios involving claimed printers verify that re-registration with unchanged or same-family model numbers preserves claim status (`CLAIMED`) and owner identity, so that visibility to user applications remains governed by successful claiming. The logic added for GOAR-15 must not silently unclaim or change visibility.

### Rule 10 — Claiming enables subscriptions and remote management

Exact sentence:
> "Claiming enables subscriptions (e.g. Instant Ink) and remote management."

Relation to this ticket:
- Spoofing a claimed printer’s identity could affect subscriptions and remote management. GOAR-15’s rejection of model family mismatches and preservation of ownership on accepted re-registrations mitigates this risk by preventing silent takeover of subscription-linked printers.

### Rule 11 — Ownership must not be silently overwritten

Exact sentence:
> "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."

Relation to this ticket:
- This rule is central to GOAR-15. Re-registration with a materially different model family is rejected so that an existing owner’s claim cannot be silently replaced by a different device reusing the same serial number.
- Scenarios for claimed printers (same-family and unchanged models) show that re-registration preserves status `CLAIMED` and `owner_user_id`, and that any notable model-number changes are logged and flagged for review.

### Rule 12 — Deregistration removes cloud associations

Exact sentence:
> "Deregistration must remove all cloud associations and printer data (GDPR compliance)."

Relation to this ticket:
- GOAR-15 does not explicitly change deregistration behavior. However, the rejection of spoofed re-registrations and preservation of identity on invalid attempts reinforces that deregistration remains the primary mechanism for intentionally removing cloud associations; model-family mismatch rejection does not bypass or emulate deregistration.

### Rule 13 — Cloud ID after deregistration

Exact sentence:
> "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)."

Relation to this ticket:
- While GOAR-15 focuses on re-registration of existing records, its Cloud ID behavior must remain compatible with re-registration after deregistration. Tests asserting new Cloud IDs on successful re-registration should continue to pass for post-deregistration cases (though these are not explicitly covered in the GOAR-15 feature file).

### Rule 14 — Observability / structured logging

Exact sentence:
> "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."

Relation to this ticket:
- GOAR-15’s notable events (model-number changes) and rejection paths must be logged in a way that is observable. The feature includes scenarios checking for warning logs and discrete structured fields (serial_number, old_model, new_model), directly targeting this rule.

## 4. Original Acceptance Criteria

Copied exactly from jira_context/GOAR-15_live.md:

> When re-registering an existing serial number, register_printer() updates
> model_number and firmware_version on the existing record with no
> validation that this looks like the same physical device. A completely
> different model_number could silently overwrite the original identity
> tied to that serial number, with no protection against serial-number
> reuse or spoofing across different physical printers.
> Acceptance Criteria:
> At minimum, a re-registration that changes model_number from what was
> previously recorded is flagged/logged as a notable event for review.
> (Stretch) Re-registration with a materially different model family is
> rejected or requires explicit confirmation.
> Legitimate re-registrations with matching or compatible model/firmware
> data continue to work as before.

## 5. Adopted Additional Requirements

Each requirement below is either justified by a specific sentence from docs/business_rules.md or by a named edge case category (boundary/auth/ownership/rollback).

### 5.1. Authorization and Authentication for Registration, Claim, and Lookup

Requirement statement:
- Registration, claim, and lookup endpoints must reject requests that are missing the Authorization header or that present an invalid bearer token, with clear error semantics. Specifically:
  - Requests with no Authorization header must be rejected with a 422 error, indicating a required header is missing.
  - Requests with an invalid bearer token must be rejected with a 401 error and a response body `{"detail": "Invalid or expired token"}`.

Justification:
- Edge case category: auth.
- These behaviors are exercised by GOAR-15.feature scenarios:
  - "Registering a printer with no Authorization header is rejected".
  - "Registering a printer with an invalid bearer token is rejected".
  - "Claiming a printer with no Authorization header is rejected".
  - "Claiming a printer with an invalid bearer token is rejected".
  - "Looking up a printer with no Authorization header is rejected".
  - "Looking up a printer with an invalid bearer token is rejected".
- While docs/business_rules.md does not explicitly call out Authorization headers, secure onboarding and ownership semantics (Rule 11) imply that unauthenticated or improperly authenticated requests must not alter or reveal printer state. Treating missing/invalid Authorization as an auth edge case ensures consistent rejection behavior.

### 5.2. Cloud ID, Email, and XMPP Node Must Not Change on Rejected Re-Registration

Requirement statement:
- When a re-registration attempt is rejected (e.g., due to model family mismatch), the following must hold:
  - The printer's existing Cloud ID remains unchanged.
  - The printer's existing printer email ID remains unchanged.
  - The printer's existing XMPP node remains unchanged.
  - No new capability-related history entries are added.

Justification:
- Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
- Edge case category: rollback.
- Scenarios "A different-family model number change is rejected and the stored record is left unchanged" and "A rejected re-registration produces zero partial side effects" assert that lookups show Cloud ID, printer email, XMPP node, and history unchanged except for a single review-flag entry. This enforces full rollback of registration side effects on failure.

### 5.3. Cloud ID Regeneration Only on Successful Re-Registration

Requirement statement:
- Cloud ID must be regenerated only for successful re-registrations. Rejected re-registrations must not generate or assign a new Cloud ID.

Justification:
- Exact rule sentences:
  - "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." (Rule 3)
  - "Cloud ID: system-generated, unique, regenerated on every re-registration." (Rule 6)
- Edge case category: rollback.
- For rejected re-registrations, Rule 2 requires rollback and no partial identity changes, meaning Cloud ID must remain unchanged. The feature scenarios confirm that Cloud ID is only new in successful re-registrations and unchanged for rejected ones.

### 5.4. Registration History Must Accurately Record Model-Number Changes and Flags

Requirement statement:
- For re-registrations that succeed with a changed `model_number` within the same model family:
  - Registration history must include an entry indicating that `model_number` changed on re-registration.
  - The entry must include explicit `old=` and `new=` model values and state that the event is "flagged for review".
- For re-registrations with unchanged (or merely whitespace/case-normalized) `model_number`:
  - Registration history must contain no model-number-change marker and no "flagged for review" text; only standard re-registration entries should appear.

Justification:
- Original AC:
  - "At minimum, a re-registration that changes model_number from what was previously recorded is flagged/logged as a notable event for review." (jira_context/GOAR-15_live.md)
- Exact rule sentence:
  - "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." (Rule 14)
- Edge case category: boundary.
- Scenarios assert both model-change logging and non-logging for unchanged/normalized cases, ensuring accurate and non-noisy observability.

### 5.5. Structured Warning Logs for Model-Number Changes

Requirement statement:
- When a re-registration succeeds with a changed `model_number` within the same model family, the service must emit a warning log record that:
  - Includes discrete structured fields: `serial_number`, `old_model`, `new_model`.
  - Optionally includes a human-readable message mentioning those values.
- At least one scenario verifies the presence of a warning record with these discrete fields via log record attributes.

Justification:
- Exact rule sentence:
  - "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." (Rule 14)
- The scenario "The model-number-change warning log carries discrete structured fields" asserts that warning records must have attributes `serial_number`, `old_model`, and `new_model`, not just free-form text.

### 5.6. Ownership Preservation on Re-Registration of Claimed Printers

Requirement statement:
- When a printer is in status `CLAIMED` and re-registration succeeds (whether model is unchanged or changes within the same family):
  - The printer’s status must remain `CLAIMED`.
  - The printer’s `owner_user_id` must remain unchanged.
  - Registration history must show no indication that ownership or claim status was altered.

Justification:
- Exact rule sentence:
  - "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)
- Edge case category: ownership.
- Scenarios "Re-registering a claimed printer with an unchanged model number preserves ownership" and "Re-registering a claimed printer with a same-family model change still flags it for review" assert that lookups show owner and status unchanged after re-registration, satisfying Rule 11.

### 5.7. Authorization Errors Must Not Reveal Sensitive Printer Details

Requirement statement:
- For lookup requests (`GET /printers/{printer_id}`) that lack a valid Authorization header:
  - The response must indicate missing or invalid authorization without returning printer details such as owner_user_id, Cloud ID, printer_email_id, or capabilities.

Justification:
- Exact rule sentences:
  - "A printer becomes visible to a user's applications only after a successful claim." (Rule 9)
  - "Claiming enables subscriptions (e.g. Instant Ink) and remote management." (Rule 10)
- Edge case category: auth / ownership.
- The scenarios around lookup with missing or invalid Authorization headers assert rejection responses. To adhere to Rule 9, such responses must not expose printer details tied to ownership or visibility.

### 5.8. Rejected Re-Registrations Must Add Only a Single Review-Flag History Entry

Requirement statement:
- When a re-registration is rejected (e.g., model family mismatch):
  - The registration history returned by lookup must include exactly one additional entry compared to the pre-existing history.
  - That entry must indicate the model-number change was "flagged for review".
  - The entry must not include markers such as "Cloud identity created", "Capabilities captured", "Capabilities already on record", "XMPP node assigned", or "Welcome page printed".

Justification:
- Exact rule sentence:
  - "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
- Edge case category: rollback.
- The scenarios "A different-family model number change is rejected and the stored record is left unchanged" and "A rejected re-registration produces zero partial side effects" explicitly assert that history is unchanged except for a single review-flag entry without side-effect markers, ensuring rollback semantics.

## 6. Open Questions

The following questions cannot be resolved purely from jira_context/GOAR-15_live.md, reports/GOAR-15_diff.txt, and docs/business_rules.md. Downstream agents must avoid scoring or testing assumptions that depend on these unresolved points.

### 6.1. Firmware Version Validation and Logging

The Jira description states:
> "register_printer() updates model_number and firmware_version on the existing record with no validation that this looks like the same physical device."

However, the acceptance criteria and feature scenarios focus only on `model_number` changes and model-family mismatch detection. There is no explicit requirement or scenario addressing `firmware_version` spoofing or validation.

Open question:
- Should re-registration also validate and/or log significant changes in `firmware_version` as notable events (e.g., unexpected downgrades or changes inconsistent with the model), or is firmware out of scope for GOAR-15?

Why it cannot be resolved:
- docs/business_rules.md does not mention firmware.
- Jira acceptance criteria only refer to model_number and model family.

Downstream exclusion:
- Test design and scoring must not assume specific validation or logging behavior for firmware_version changes under GOAR-15 until clarified.

### 6.2. Definition and Authority for "Model Family"

The acceptance criteria refer to "materially different model family" and the feature file notes that TC-GOAR-15-10 uses a "crude `_model_family()` heuristic" because no authoritative model-family catalog exists in the repo.

Open question:
- What is the authoritative definition of "model family" (e.g., specific product line, prefix pattern, catalog-based classification), and is `_model_family()` intended to be the long-term implementation or only a temporary heuristic?

Why it cannot be resolved:
- docs/business_rules.md does not define "model family".
- There is no model catalog or specification document in the provided inputs.

Downstream exclusion:
- Tests must treat `_model_family()`’s behavior as implementation detail for GOAR-15 but must not assume it is the long-term or canonical definition of model families for future tickets.

### 6.3. Stretch AC Mode: Reject vs Explicit Confirmation

The acceptance criteria state:
> "(Stretch) Re-registration with a materially different model family is rejected or requires explicit confirmation."

The diff and scenarios implement outright rejection with 422 responses for model-family mismatch. There is no mechanism described for "explicit confirmation" (e.g., admin override, owner confirmation flow).

Open question:
- Is rejection the final, intended behavior for GOAR-15, or should the system eventually support explicit confirmation to override model-family mismatch in controlled cases?

Why it cannot be resolved:
- Jira ticket labels this as "Stretch" and does not clarify which path was chosen.
- docs/business_rules.md do not discuss confirmation workflows.

Downstream exclusion:
- Tests and scoring must focus only on rejection behavior as implemented, without assuming any explicit confirmation workflow exists or is required.

### 6.4. Ownership-Specific Strictness for Model Changes

Rule 11 states:
> "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."

GOAR-15’s scenarios for claimed printers show that ownership is preserved when re-registration succeeds. However, it is not clear whether additional strictness (beyond logging/flagging) is required for `CLAIMED` printers when model_number changes within the same family.

Open question:
- Should re-registration of a `CLAIMED` printer with a changed model_number (even within the same family) be:
  - Blocked outright,
  - Allowed only with explicit confirmation,
  - Or treated the same as unclaimed printers (logged and flagged but otherwise accepted)?

Why it cannot be resolved:
- Jira acceptance criteria do not distinguish between claimed and unclaimed printers for model changes.
- docs/business_rules.md emphasize not wiping out ownership but do not prescribe how strict re-registration should be for claimed devices.

Downstream exclusion:
- Tests and scoring must validate that ownership is preserved (status and owner_user_id unchanged) but must not penalize or assume a particular policy for claimed printers beyond what is explicitly implemented in the current scenarios.

### 6.5. Scope of "for review" and Downstream Monitoring

AC1 requires that model-number changes be "flagged/logged as a notable event for review". The feature file verifies that events are logged and history entries include a review flag, but there is no description of how or by whom these events are reviewed.

Open question:
- Does "for review" imply a specific downstream monitoring or triage process (e.g., alerts to operations, dashboards, periodic audits), and if so, what are the expectations (SLA, severity thresholds)?

Why it cannot be resolved:
- docs/business_rules.md mention observability and structured logging but do not specify operational review processes.
- jira_context/GOAR-15_live.md does not elaborate on review mechanics.

Downstream exclusion:
- QA scoring must focus on presence of flags and logs and must not attempt to validate or simulate organizational review processes (alerts, dashboards, manual triage) for GOAR-15.
