# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Same-serial re-registration where the normalized model_number changes within the same model family succeeds, generates new Cloud identity (Cloud ID, printer email ID, and claim code if applicable), and records a GOAR-15 history entry plus WARNING log.
           Requirement: AC1

[BOUNDARY VALUE] Re-registration where model_number differs only by case and/or leading/trailing whitespace is treated as unchanged after normalization and therefore does not append a GOAR-15 history entry or emit a model-change WARNING log.
           Requirement: AC1

[ROLLBACK] Re-registration where the normalized model_number change leads to a different model family is rejected, appends a GOAR-15 history entry and WARNING log, and leaves all persisted printer identity fields (Cloud ID, printer email ID, firmware_version, capabilities, XMPP node, ownership) unchanged.
           Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[INVALID INPUT] Re-registration attempt for an already-registered serial_number with a clearly different-family normalized model_number is rejected with RegistrationError and translated to HTTP 422 by POST /printers/register, with no registration-side effects.
           Requirement: AC2

[BOUNDARY VALUE] Re-registration where the new normalized model_number differs only in the last dash-separated segment (same prefix family) is classified as same-family and accepted, whereas a change in the prefix segments is classified as different-family and rejected.
           Requirement: AC2

[ROLLBACK] Different-family re-registration rejection path leaves Cloud ID, printer email ID, capabilities, XMPP node, serial index, and ownership state identical to the pre-attempt state, confirming full rollback for the GOAR-15 gate.
           Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-registration with identical normalized model_number and unchanged firmware_version succeeds and generates a new Cloud ID, printer email ID, and (if unclaimed) claim code while preserving ownership and visibility semantics.
           Requirement: AC3

[HAPPY PATH] Re-registration with identical normalized model_number but updated firmware_version succeeds, regenerates Cloud ID and printer email ID, updates stored firmware_version, and does not introduce additional firmware-specific validation or logging.
           Requirement: AC3

[ROLLBACK] Failed re-registration due to a non-GOAR-15 pre–Welcome-Page error (e.g., capability capture or welcome-page print failure) rolls back fully and leaves prior Cloud ID, printer email ID, XMPP node, capabilities, serial index, and ownership state unchanged.
           Requirement: AC3

### AR1 — Zero side effects on model-family mismatch rejection

[ROLLBACK] Different-family re-registration rejected by the model-family gate leaves the existing printer record, capabilities, serial index, Cloud ID, printer email ID, and XMPP node exactly as before the attempt, aside from GOAR-15 history and WARNING log entries.
           Requirement: AR1

[ROLLBACK] Rejected re-registration for a serial_number that was not previously registered does not create any new printer record, capabilities, serial index, Cloud ID, printer email ID, or XMPP node.
           Requirement: AR1

### AR2 — Cloud ID allocation and rollback on rejection

[BOUNDARY VALUE] Re-registration that triggers a model-family mismatch verifies that `_generate_cloud_id()` is invoked only after the model-family check passes, or that any Cloud ID generated before failure is discarded and never persisted or reused.
           Requirement: AR2

[ROLLBACK] Successful re-registration path verifies that Cloud ID generation occurs only on acceptance and that rejected attempts never persist or reuse a Cloud ID produced earlier in the flow.
           Requirement: AR2

### AR3 — Structured logging field stability

[HAPPY PATH] Accepted same-family model_number change on re-registration emits a WARNING log whose structured `extra` fields consistently expose serial_number, old_model, and new_model for downstream telemetry.
           Requirement: AR3

[BOUNDARY VALUE] Multiple successive re-registrations that change model_number within the same family verify that every model-change event produces a structured WARNING log with stable field names and types.
           Requirement: AR3

### AR4 — Re-registration of claimed printers preserves ownership

[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged normalized model_number succeeds, regenerates Cloud ID and printer email ID, and preserves owner_user_id and CLAIMED status.
           Requirement: AR4

[HAPPY PATH] Re-registration of a CLAIMED printer with a same-family normalized model_number change succeeds, logs the model change, and still preserves owner_user_id and CLAIMED status.
           Requirement: AR4

[OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context (different bearer token) does not transfer or clear ownership and is rejected or ignored while keeping owner_user_id and CLAIMED status intact.
           Requirement: AR4

### AR5 — No model-family enforcement after deregistration (clarification needed)

[BOUNDARY VALUE] Printer that has been fully deregistered and then re-registered with the same serial_number but a different model family is treated as a fresh device without historical model-family continuity, provided business confirms this behaviour when implemented.
           Requirement: AR5

[BOUNDARY VALUE] Printer that has been deregistered and re-registered with the same serial_number and same-family model_number behaves identically to a first-time registration, confirming that GOAR-15 checks do not inadvertently block legitimate post-deregistration flows.
           Requirement: AR5

### Auth Scenarios — Protected registration, claim, lookup, and deregistration endpoints

[AUTH] Registration request to POST /printers/register with no Authorization header is rejected with HTTP 422 and leaves registration state unchanged.
           Requirement: AC2

[AUTH] Registration request to POST /printers/register with an invalid or expired bearer token is rejected and leaves printer registration state unchanged.
           Requirement: AC2

[AUTH] Claim and lookup requests to POST /printers/claim and GET /printers/{printer_id} with no Authorization header are rejected with HTTP 422 and leave ownership and visibility unchanged.
           Requirement: AC2

[AUTH] Claim, lookup, and deregister requests with an invalid or expired bearer token are rejected and leave printer ownership, visibility, and registration state unchanged.
           Requirement: AC2

## Coverage Summary

Total scenarios: 26

Happy path: 8 | Invalid input: 2 | Boundary: 7 | Auth: 4 | Ownership: 2 | Rollback: 9