# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Same-serial re-registration where the normalized model_number changes within the same model family succeeds and records both a GOAR-15 history entry and a structured WARNING log with serial_number, old_model, and new_model fields.
           Requirement: AC1

[BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading or trailing whitespace is treated as unchanged after normalization and therefore does not append a GOAR-15 history entry or emit a model-change WARNING log.
           Requirement: AC1

[ROLLBACK] Re-registration where the normalized model_number change leads to a different model family is rejected, appends a GOAR-15 history entry and WARNING log, and leaves all persisted printer identity fields unchanged.
           Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[INVALID INPUT] Re-registration attempt for an already-registered serial_number with a clearly different-family normalized model_number is rejected with a RegistrationError and translated to HTTP 422 by POST /printers/register, with no registration-side effects.
           Requirement: AC2

[BOUNDARY VALUE] Re-registration where the new normalized model_number differs only in the last dash-separated segment (same-family prefix) is classified as same-family and accepted, whereas a change in the prefix segments is classified as different-family and rejected.
           Requirement: AC2

[ROLLBACK] Different-family re-registration rejection path leaves Cloud ID, printer email ID, capabilities, XMPP node, serial index, and ownership state identical to the pre-attempt state, confirming full rollback for the GOAR-15 gate.
           Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-registration with identical normalized model_number and unchanged firmware_version succeeds and generates a new Cloud ID, printer email ID, and (if unclaimed) claim code while preserving ownership and visibility semantics.
           Requirement: AC3

[HAPPY PATH] Re-registration with identical normalized model_number but updated firmware_version succeeds, regenerates Cloud ID and printer email ID, updates stored firmware_version, and does not introduce additional firmware-specific validation or logging.
           Requirement: AC3

[ROLLBACK] Failed re-registration due to a non–Welcome-Page error after Cloud identity creation invokes rollback and leaves prior Cloud ID, printer email ID, XMPP node, capabilities, serial index, and ownership state unchanged.
           Requirement: AC3

### AR1 — Zero side effects on model-family mismatch rejection

[ROLLBACK] Different-family re-registration rejected by the model-family gate leaves the existing printer record, capabilities, serial index, Cloud ID, printer email ID, firmware_version, status, owner_user_id, and XMPP node exactly as before the attempt, aside from GOAR-15 history and WARNING log entries.
           Requirement: AR1

[ROLLBACK] Rejected re-registration for a serial_number that was not previously registered does not create any new printer record, capabilities, serial index, Cloud ID, printer email ID, or XMPP node.
           Requirement: AR1

### AR2 — Auth failures for registration, claim, and lookup endpoints

[AUTH] Registration request to POST /printers/register with no Authorization header is rejected by FastAPI header validation and leaves registration state unchanged.
           Requirement: AR2

[AUTH] Registration request to POST /printers/register with an invalid or expired bearer token is rejected with HTTP 401 and leaves printer registration state unchanged.
           Requirement: AR2

[AUTH] Claim and lookup requests to POST /printers/claim and GET /printers/{printer_id} with no Authorization header are rejected by FastAPI header validation and leave ownership and visibility unchanged.
           Requirement: AR2

[AUTH] Claim and lookup requests to POST /printers/claim and GET /printers/{printer_id} with an invalid or expired bearer token are rejected with HTTP 401 and leave printer ownership, visibility, and registration state unchanged.
           Requirement: AR2

### AR3 — Re-registration of claimed printers preserves ownership

[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged normalized model_number succeeds, regenerates Cloud ID and printer email ID, and preserves owner_user_id and CLAIMED status.
           Requirement: AR3

[HAPPY PATH] Re-registration of a CLAIMED printer with a same-family normalized model_number change succeeds, logs the model change, and still preserves owner_user_id and CLAIMED status.
           Requirement: AR3

[OWNERSHIP] Any successful re-registration of a CLAIMED printer, regardless of model_number or firmware_version updates accepted by GOAR-15, preserves owner_user_id and CLAIMED status.
           Requirement: AR3

### AR4 — Model-number normalization for change detection

[BOUNDARY VALUE] Re-registration where the only differences in model_number are whitespace and case confirms that normalization using strip().upper() causes the comparison to treat the values as equal and skip GOAR-15 logging.
           Requirement: AR4

[BOUNDARY VALUE] Re-registration where normalization is not applied symmetrically (e.g., one side normalized, the other not) would incorrectly log a model-number change; this scenario guards against regressions by asserting consistent normalization on both existing and incoming values.
           Requirement: AR4

### AR5 — Structured logging field stability

[HAPPY PATH] Accepted same-family model_number change on re-registration emits a WARNING log whose structured extra fields consistently expose serial_number, old_model, and new_model for downstream telemetry.
           Requirement: AR5

[BOUNDARY VALUE] Multiple successive re-registrations that change model_number within the same family verify that every model-change event produces a structured WARNING log with stable field names and types.
           Requirement: AR5

## Coverage Summary

Total scenarios: 24

Happy path: 7 | Invalid input: 1 | Boundary: 6 | Auth: 4 | Ownership: 1 | Rollback: 5
