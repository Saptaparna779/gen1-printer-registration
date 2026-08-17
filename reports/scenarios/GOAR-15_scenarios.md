# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Re-register an existing printer with a normalized model_number change within the same family and verify the change is logged as a notable event for review.
          Requirement: AC1
[INVALID INPUT] Re-register an existing printer with a blank or whitespace-only model_number and verify that the system treats this as invalid input and does not log a meaningful model change event.
          Requirement: AC1
[BOUNDARY VALUE] Re-register an existing printer where the only difference in model_number is case or surrounding whitespace and verify that normalization prevents a false-positive model change log.
          Requirement: AC1
[AUTH] Re-register an existing printer with a changed model_number without providing an Authorization header and verify the request is rejected for missing auth before any model-change logging occurs.
          Requirement: AC1
[AUTH] Re-register an existing printer with a changed model_number using an invalid or expired bearer token and verify the request is rejected for invalid auth before any model-change logging occurs.
          Requirement: AC1
[ROLLBACK] Attempt to re-register an existing printer with a changed model_number that causes a downstream failure before welcome page print and verify that only the review-flag history entry is persisted and no partial registration data is stored.
          Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[HAPPY PATH] Attempt to re-register an existing printer with a model_number from a clearly different model family and verify that register_printer rejects the request with a RegistrationError.
          Requirement: AC2
[INVALID INPUT] Attempt to re-register an existing printer with a malformed model_number that leads to an ambiguous or invalid model family and verify the system rejects the request rather than accepting an undefined family.
          Requirement: AC2
[BOUNDARY VALUE] Attempt to re-register an existing printer with a model_number that sits exactly on the boundary between two model families and verify that the implemented _model_family heuristic consistently classifies and rejects or accepts according to the current family definition.
          Requirement: AC2
[AUTH] Attempt to re-register an existing printer with a different-family model_number without providing an Authorization header and verify the request is rejected for missing auth before any model-family validation.
          Requirement: AC2
[AUTH] Attempt to re-register an existing printer with a different-family model_number using an invalid or expired bearer token and verify the request is rejected for invalid auth before any model-family validation.
          Requirement: AC2
[ROLLBACK] Attempt to re-register an existing printer with a different-family model_number that is rejected and verify that Cloud ID, printer email ID, XMPP node, capabilities, and serial index remain unchanged.
          Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-register an existing printer with identical model_number and updated firmware_version and verify successful completion with a new Cloud ID and preserved behaviour.
          Requirement: AC3
[HAPPY PATH] Re-register an existing printer with same-family model_number (e.g., minor revision change) and compatible firmware_version and verify that registration succeeds and issues a new Cloud ID and printer email ID.
          Requirement: AC3
[INVALID INPUT] Attempt to re-register an existing printer with missing firmware_version while model_number is unchanged and verify that the request fails due to invalid input rather than model-family logic.
          Requirement: AC3
[BOUNDARY VALUE] Re-register an existing printer using model_number and firmware_version values at documented maximum lengths and verify that the operation still succeeds and behaves as a legitimate re-registration.
          Requirement: AC3
[AUTH] Re-register an existing printer with matching model_number and compatible firmware data without providing an Authorization header and verify the request is rejected for missing auth.
          Requirement: AC3
[AUTH] Re-register an existing printer with matching model_number and compatible firmware data using an invalid or expired bearer token and verify the request is rejected for invalid auth.
          Requirement: AC3
[ROLLBACK] Trigger a failure during a legitimate re-registration after model and firmware validation but before welcome page printing and verify that the system rolls back completely, leaving Cloud ID, printer email ID, capabilities, and XMPP node unchanged from before the attempt.
          Requirement: AC3

### AR1 — Normalized model-number comparison for change detection

[HAPPY PATH] Re-register an existing printer where the only difference in model_number is case or whitespace and verify that normalized comparison treats the model as unchanged and does not flag or log a change.
          Requirement: AR1
[INVALID INPUT] Re-register an existing printer with a model_number containing only whitespace characters and verify that normalization detects this as invalid rather than a legitimate unchanged model.
          Requirement: AR1
[BOUNDARY VALUE] Re-register an existing printer with a model_number containing leading and trailing whitespace plus minimal internal variation and verify that normalization correctly identifies whether a true change exists.
          Requirement: AR1
[AUTH] Re-register an existing printer relying on normalized model-number comparison without providing an Authorization header and verify the request is rejected for missing auth before normalization logic is applied.
          Requirement: AR1
[AUTH] Re-register an existing printer relying on normalized model-number comparison using an invalid or expired bearer token and verify the request is rejected for invalid auth before normalization logic is applied.
[ROLLBACK] Attempt a re-registration that would be accepted under normalized comparison but fails later in the flow and verify that no partial state change occurs even though normalization treated the model_number as unchanged.
          Requirement: AR1

### AR2 — Model-family definition must be stable and documented before expanding scope

[HAPPY PATH] Re-register printers across several known model_number patterns and verify that _model_family consistently classifies families according to the documented heuristic.
          Requirement: AR2
[INVALID INPUT] Provide a model_number with unexpected delimiters or missing dashes during re-registration and verify that _model_family handles the input without crashing and returns a deterministic family value.
          Requirement: AR2
[BOUNDARY VALUE] Use a model_number lacking any dash separator during re-registration and verify that _model_family treats the entire normalized string as the family and behaves consistently with documented scope.
          Requirement: AR2
[AUTH] Re-register a printer where _model_family is exercised without providing an Authorization header and verify the request is rejected for missing auth.
          Requirement: AR2
[AUTH] Re-register a printer where _model_family is exercised using an invalid or expired bearer token and verify the request is rejected for invalid auth.
          Requirement: AR2
[ROLLBACK] Attempt a re-registration that triggers a model-family-based rejection at the edge of documented scope and verify that rollback prevents any partial updates to printer identity or connectivity data.
          Requirement: AR2

### AR3 — No partial side effects on rejected re-registrations

[HAPPY PATH] Perform a re-registration that is rejected due to model-family mismatch and verify that the only state change is a history entry flagging the attempted model-number change.
          Requirement: AR3
[INVALID INPUT] Submit a re-registration with invalid model_number data that causes an early validation failure and verify that no Cloud ID, email ID, XMPP node, or capabilities are created or modified.
          Requirement: AR3
[BOUNDARY VALUE] Trigger a rejection at the last possible pre-welcome-page step and verify that rollback still removes all tentative changes, leaving the printer record identical to its prior state.
          Requirement: AR3
[AUTH] Attempt a re-registration that would be rejected but omit the Authorization header and verify that auth failure prevents any review-flag history entry or partial side effects.
          Requirement: AR3
[AUTH] Attempt a re-registration that would be rejected but use an invalid or expired bearer token and verify that auth failure prevents any review-flag history entry or partial side effects.
          Requirement: AR3
[ROLLBACK] Simulate multiple successive rejected re-registrations and verify that each rejection leaves Cloud ID, printer email, XMPP node, capabilities, and serial index unchanged across attempts.
          Requirement: AR3

### AR4 — Preservation of ownership and claim status on legitimate re-registrations

[HAPPY PATH] Re-register a claimed printer with unchanged model_number and compatible firmware data and verify that owner_user_id and status remain CLAIMED while new Cloud ID and email ID are issued.
          Requirement: AR4
[HAPPY PATH] Re-register a claimed printer with same-family model_number change and compatible firmware data and verify that ownership and CLAIMED status are preserved while the model update and new Cloud ID are applied.
          Requirement: AR4
[INVALID INPUT] Attempt to re-register a claimed printer with missing or malformed model_number while preserving firmware data and verify that the request is rejected without altering ownership.
          Requirement: AR4
[BOUNDARY VALUE] Re-register a claimed printer with model_number at the valid length boundary and verify that ownership is preserved and the claim status is unchanged after successful registration.
          Requirement: AR4
[AUTH] Attempt to re-register a claimed printer without providing an Authorization header and verify that the request is rejected for missing auth and that ownership fields remain unchanged.
          Requirement: AR4
[AUTH] Attempt to re-register a claimed printer using an invalid or expired bearer token and verify that the request is rejected for invalid auth and that ownership fields remain unchanged.
          Requirement: AR4
[OWNERSHIP] Attempt to re-register a claimed printer from a different authenticated user account and verify that the operation is rejected or logged without transferring ownership.
          Requirement: AR4
[ROLLBACK] Trigger a failure during legitimate re-registration of a claimed printer after ownership checks but before welcome page printing and verify that owner_user_id and CLAIMED status remain unchanged.
          Requirement: AR4

### AR5 — Structured warning logs for model-number changes

[HAPPY PATH] Re-register an existing printer with a true model_number change and verify that a warning log is emitted with a stable message key and discrete serial_number, old_model, and new_model attributes.
          Requirement: AR5
[INVALID INPUT] Attempt to re-register with a model_number that fails validation and verify that no misleading structured warning log is emitted for an unaccepted change.
          Requirement: AR5
[BOUNDARY VALUE] Re-register with a borderline model_number change that barely qualifies as a different model and verify that structured logging still correctly captures serial_number, old_model, and new_model.
          Requirement: AR5
[AUTH] Attempt to re-register with a model_number change without providing an Authorization header and verify that no GOAR-15 warning log is emitted because the request fails at auth.
          Requirement: AR5
[AUTH] Attempt to re-register with a model_number change using an invalid or expired bearer token and verify that no GOAR-15 warning log is emitted because the request fails at auth.
          Requirement: AR5
[ROLLBACK] Trigger a later-stage failure after structured warning logging has occurred and verify that logs remain available for review even though registration state is rolled back.
          Requirement: AR5

### AR6 — Cloud ID, email, and XMPP behaviour on successful GOAR-15 re-registrations

[HAPPY PATH] Successfully re-register an existing printer with unchanged model_number and updated firmware data and verify that a new Cloud ID and new printer email ID are generated and an XMPP node is assigned if previously absent.
          Requirement: AR6
[HAPPY PATH] Successfully re-register an existing printer with same-family model_number change and compatible firmware data and verify that Cloud ID, printer email ID, and XMPP node follow the expected regeneration and assignment rules.
          Requirement: AR6
[INVALID INPUT] Attempt to re-register an existing printer with invalid email-related configuration while model_number and firmware data are valid and verify that the operation fails without assigning a new printer email ID or XMPP node.
          Requirement: AR6
[BOUNDARY VALUE] Re-register an existing printer with email and XMPP-related fields at their configuration boundaries and verify that Cloud ID and connectivity behaviour still comply with GOAR-15 requirements.
          Requirement: AR6
[AUTH] Attempt to perform a successful-style re-registration without providing an Authorization header and verify that Cloud ID, printer email ID, and XMPP node remain unchanged because the request is rejected for missing auth.
          Requirement: AR6
[AUTH] Attempt to perform a successful-style re-registration using an invalid or expired bearer token and verify that Cloud ID, printer email ID, and XMPP node remain unchanged because the request is rejected for invalid auth.
          Requirement: AR6
[ROLLBACK] Trigger a failure after Cloud ID generation but before email and XMPP assignment during re-registration and verify that rollback restores the previous Cloud ID and prevents any new email or XMPP details from persisting.
          Requirement: AR6

## Coverage Summary

Total scenarios: 60

Happy path: 20 | Invalid input: 12 | Boundary: 12 |
Auth: 12 | Ownership: 1 | Rollback: 3
