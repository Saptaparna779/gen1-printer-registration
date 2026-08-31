# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Successful re-registration where the normalized model_number changes within the same model family is accepted and produces new Cloud ID, printer email ID, and claim code as per existing rules.
           Requirement: AC1

[BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading/trailing whitespace is treated as unchanged after normalization and does not trigger a model-change flag or warning log.
           Requirement: AC1

[ROLLBACK] Re-registration where the normalized model_number changes and resolves to a different model family is rejected and leaves Cloud ID, printer email ID, XMPP node, capabilities, and ownership unchanged apart from the review history entry and warning log.
           Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[INVALID INPUT] Re-registration attempt for an already-registered serial_number with a clearly different-family model_number is rejected with RegistrationError and no registration-side effects occur.
           Requirement: AC2

[BOUNDARY VALUE] Re-registration where the new model_number sits on the edge of the same-family vs different-family heuristic (changing only the last dash-separated segment) is correctly classified and either accepted or rejected with appropriate logging.
           Requirement: AC2

[ROLLBACK] Rejected different-family re-registration does not create or alter any Cloud ID, printer email ID, XMPP node, capabilities record, or serial index, confirming full rollback on the GOAR-15 rejection path.
           Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-registration with identical model_number and firmware_version succeeds and generates a new Cloud ID, printer email ID, and claim code while preserving ownership and visibility.
           Requirement: AC3

[HAPPY PATH] Re-registration with identical model_number but updated firmware_version succeeds, regenerates Cloud ID and printer email ID, and updates stored firmware_version without introducing additional validation.
           Requirement: AC3

[ROLLBACK] Failed re-registration due to a non-GOAR-15 pre–Welcome-Page error rolls back fully and leaves prior Cloud ID, printer email ID, XMPP node, capabilities, and ownership state unchanged.
           Requirement: AC3

### AR1 — Case- and whitespace-insensitive model-number comparison

[HAPPY PATH] Re-registration where old and new model_number differ only in case and/or leading/trailing whitespace is treated as the same model after normalization and does not append a GOAR-15 model-change history entry or emit a warning log.
           Requirement: AR1

[BOUNDARY VALUE] Re-registration where normalization causes two visually distinct model_number strings to collide (e.g., extra internal spaces or mixed case) is still treated consistently as unchanged and avoids spurious spoofing flags.
           Requirement: AR1

### AR2 — Explicit codification of zero side effects on model-family mismatch

[ROLLBACK] Different-family re-registration rejected by the model-family gate leaves the existing printer record, capabilities, serial index, Cloud ID, printer email ID, and XMPP node exactly as before the attempt.
           Requirement: AR2

[ROLLBACK] Rejected re-registration for a serial_number that was not previously registered does not create any new printer record, capabilities, serial index, Cloud ID, printer email ID, or XMPP node.
           Requirement: AR2

### AR3 — Clarify whether Cloud ID generation happens before or after the model-family gate

[BOUNDARY VALUE] Re-registration that triggers a model-family mismatch verifies that Cloud ID generation either does not occur or any generated Cloud ID is discarded so that no orphan or partially-used Cloud IDs remain.
           Requirement: AR3

[ROLLBACK] Successful re-registration verifies that Cloud ID generation occurs only on the acceptance path and that rejected attempts never persist or reuse a Cloud ID generated earlier in the flow.
           Requirement: AR3

### AR4 — Stronger protections for claimed printers

[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged normalized model_number succeeds while preserving owner_user_id and CLAIMED status and regenerating Cloud ID and printer email ID.
           Requirement: AR4

[INVALID INPUT] Re-registration of a CLAIMED printer attempting to change model_number, even within the same model family, is either rejected outright or requires explicit confirmation, and in both cases ownership and claim status remain unchanged.
           Requirement: AR4

[OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context does not transfer or clear ownership and is rejected or ignored while preserving owner_user_id and CLAIMED status.
           Requirement: AR4

### AR5 — Explicit handling of firmware-version changes

[HAPPY PATH] Re-registration that changes firmware_version while leaving normalized model_number unchanged succeeds, regenerates Cloud ID and printer email ID, and logs an informational firmware-change event with old and new firmware values.
           Requirement: AR5

[BOUNDARY VALUE] Multiple successive re-registrations that only change firmware_version verify that repeated firmware updates are logged consistently without introducing any compatibility checks or rejection behaviour.
           Requirement: AR5

### AR6 — Align error semantics for missing Authorization headers

[AUTH] Registration endpoint POST /printers/register with no Authorization header is rejected with the documented 422 error shape and leaves printer state unchanged.
           Requirement: AR6

[AUTH] Claim and lookup endpoints (POST /printers/claim and GET /printers/{printer_id}) called without an Authorization header are rejected with the same 422 error structure and have no side effects on ownership or visibility.
           Requirement: AR6

### AR7 — Document `_model_family()` as a temporary heuristic

[BOUNDARY VALUE] Re-registration using unusual or edge-case model_number formats (e.g., multiple dashes, numeric-only segments) confirms that `_model_family()` consistently classifies families but may misclassify corner cases, reinforcing its heuristic nature.
           Requirement: AR7

[BOUNDARY VALUE] Re-registration using a model_number with no dash separator confirms that the single-segment string is treated as the family and behaves consistently across acceptance and rejection paths.
           Requirement: AR7

### Auth Scenarios (Protected registration, claim, and lookup endpoints)

[AUTH] Re-registration request to POST /printers/register with an invalid or expired bearer token is rejected and leaves registration state unchanged.
           Requirement: AC3

[AUTH] Claim and lookup requests to POST /printers/claim and GET /printers/{printer_id} with an invalid or expired bearer token are rejected and leave ownership, visibility, and printer state unchanged.
           Requirement: AC3

## Coverage Summary

Total scenarios: 29

Happy path: 9 | Invalid input: 3 | Boundary: 10 | Auth: 4 | Ownership: 2 | Rollback: 7