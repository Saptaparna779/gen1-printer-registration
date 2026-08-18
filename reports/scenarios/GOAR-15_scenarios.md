# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Successful re-registration where model_number changes within the same family is accepted and produces the expected registration outputs.
Requirement: AC1

[BOUNDARY VALUE] Re-registration where model_number differs only by case/whitespace is treated as unchanged after normalization and does not trigger a model-change flag.
Requirement: AC1

[ROLLBACK] Re-registration with a different-family model_number is rejected and leaves Cloud ID, email, XMPP node, and capabilities unchanged apart from the review history entry.
Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[HAPPY PATH] Re-registration attempt with a clearly different-family model_number is rejected with a RegistrationError and no registration-side effects occur.
Requirement: AC2

[BOUNDARY VALUE] Re-registration where the new model_number sits on the edge of the same-family vs different-family heuristic (last dash-separated segment) is correctly classified and either accepted or rejected.
Requirement: AC2

[ROLLBACK] Rejected different-family re-registration does not create or alter any Cloud ID, printer email, XMPP node, capabilities record, or serial index.
Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-registration with identical model_number and firmware_version succeeds and generates a new Cloud ID, email ID, and XMPP node as per existing rules.
Requirement: AC3

[HAPPY PATH] Re-registration with identical model_number but updated firmware_version succeeds and regenerates Cloud ID and printer email while preserving ownership.
Requirement: AC3

[ROLLBACK] Failed re-registration due to a non-GOAR-15 pre-Welcome-Page error rolls back fully and leaves prior Cloud ID, email, and XMPP state unchanged.
Requirement: AC3

### AR1 — Normalized model-number comparison for change detection

[HAPPY PATH] Re-registration where old and new model_number differ only in case/whitespace does not trigger a model-change warning and is treated as the same model.
Requirement: AR1

[BOUNDARY VALUE] Re-registration where normalization causes two visually distinct model_number strings to collide is still treated consistently as unchanged.
Requirement: AR1

### AR2 — Model-family definition must be stable and documented before expanding scope

[BOUNDARY VALUE] Re-registration with multiple dash-separated segments in model_number verifies that _model_family() consistently extracts the family and classifies same-family vs different-family.
Requirement: AR2

[BOUNDARY VALUE] Re-registration for a model_number with no dash separator verifies that the entire string is treated as the family and behaves consistently.
Requirement: AR2

### AR3 — No partial side effects on rejected re-registrations

[ROLLBACK] Different-family re-registration that is rejected leaves the printer record, capabilities, serial index, Cloud ID, email, and XMPP node exactly as before the attempt.
Requirement: AR3

[ROLLBACK] Rejected re-registration for a previously unregistered serial_number does not create any new printer record, capabilities, serial index, Cloud ID, email, or XMPP node.
Requirement: AR3

### AR4 — Preservation of ownership and claim status on legitimate re-registrations

[HAPPY PATH] Re-registration of a CLAIMED printer with unchanged model_number succeeds while preserving owner_user_id and CLAIMED status.
Requirement: AR4

[HAPPY PATH] Re-registration of a CLAIMED printer with same-family model_number succeeds, logs the model change, and preserves owner_user_id and CLAIMED status.
Requirement: AR4

[OWNERSHIP] Attempted re-registration of a CLAIMED printer from a different user context does not transfer or clear ownership and is either rejected or leaves ownership unchanged.
Requirement: AR4

### AR5 — Structured warning logs for model-number changes

[HAPPY PATH] Same-family model-number change on re-registration emits a structured warning log with serial_number, old_model, and new_model fields while the registration succeeds.
Requirement: AR5

[ROLLBACK] Different-family model-number change that is rejected emits a structured warning log with serial_number, old_model, new_model, and result="rejected" while leaving printer state unchanged.
Requirement: AR5

### AR6 — Cloud ID, email, and XMPP behaviour on successful GOAR-15 re-registrations

[HAPPY PATH] Successful re-registration with unchanged model_number generates a new Cloud ID, a new printer email ID, and assigns an XMPP node if missing, all differing from prior values.
Requirement: AR6

[HAPPY PATH] Successful re-registration with same-family model_number change generates new Cloud ID and printer email while preserving or assigning XMPP connectivity.
Requirement: AR6

[BOUNDARY VALUE] Re-registration of a printer that already has an XMPP node verifies that the node is preserved or correctly reassigned without violating connectivity rules.
Requirement: AR6

### Auth Scenarios (Protected registration endpoint)

[AUTH] Re-registration request to the protected registration endpoint without an Authorization header is rejected with no registration-side effects.
Requirement: AC3

[AUTH] Re-registration request to the protected registration endpoint with an invalid or expired bearer token is rejected with no registration-side effects.
Requirement: AC3

## Coverage Summary

Total scenarios: 26

Happy path: 12 | Invalid input: 0 | Boundary: 7 | Auth: 2 | Ownership: 1 | Rollback: 4
