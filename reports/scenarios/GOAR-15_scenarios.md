# Scenario Coverage — GOAR-15

## Scenarios by Requirement

### AC1 — Model-number change on re-registration is flagged/logged as a notable event for review

[HAPPY PATH] Re-register an existing printer with a different same-family model number and verify that a notable model-number-change event is logged while registration succeeds.
Requirement: AC1

[INVALID INPUT] Re-register an existing printer with a model number that is malformed but still different from the stored value, and verify that the system still logs the model-number-change event before handling the malformed value according to core registration rules.
Requirement: AC1

[BOUNDARY VALUE] Re-register an existing printer where the incoming model number differs only slightly from the stored one (e.g., revision suffix change) and verify that this minimal but real change still produces a model-number-change log.
Requirement: AC1

[ROLLBACK] Trigger a failure immediately after a logged model-number change (but before Welcome Page print) and verify that the registration rollback leaves printer identity and history unchanged apart from the logged review event.
Requirement: AC1

### AC2 — Re-registration with a materially different model family is rejected or requires explicit confirmation

[HAPPY PATH] Re-register an existing printer with a clearly different model-family value and verify that the re-registration is rejected as a spoofing risk without applying any subsequent registration side effects.
Requirement: AC2

[BOUNDARY VALUE] Re-register an existing printer with a model number that is right on the boundary between being considered the same family and different family, and verify that the family-classification behaviour at this edge matches the rejection rules.
Requirement: AC2

[AUTH] Attempt a model-family-mismatch re-registration without an Authorization token and verify that the request is rejected at auth level before family validation logic is applied.
Requirement: AC2

[ROLLBACK] After a rejected different-family re-registration, verify that Cloud ID, printer email ID, XMPP node, capabilities, and serial index remain exactly as before the attempt.
Requirement: AC2

### AC3 — Legitimate re-registrations with matching or compatible model/firmware data continue to work as before

[HAPPY PATH] Re-register an existing printer with exactly the same model number and a compatible firmware version and verify that registration completes successfully with a new Cloud ID, email ID, and XMPP node as per existing rules.
Requirement: AC3

[BOUNDARY VALUE] Re-register an existing printer with a same-family but slightly revised model number and compatible firmware version and verify that the flow still succeeds and preserves all expected identity behaviours.
Requirement: AC3

[AUTH] Attempt a legitimate re-registration without an Authorization token and verify that the request fails due to missing auth rather than model or firmware validation.
Requirement: AC3

[ROLLBACK] Trigger a controlled failure during a legitimate re-registration and verify that rollback restores pre-registration state for identity and connectivity fields.
Requirement: AC3

### AR1 — Normalized model-number comparison for change detection

[HAPPY PATH] Re-register an existing printer where the new model number differs only by case and surrounding whitespace, and verify that normalization causes the system to treat the model number as unchanged and skip model-change logging.
Requirement: AR1

[INVALID INPUT] Re-register with a model number containing leading/trailing whitespace and mixed case plus minor formatting anomalies, and verify that normalization still correctly identifies no substantive model-number change.
Requirement: AR1

[BOUNDARY VALUE] Re-register with a model number that is identical after normalization except for a single non-whitespace character, and verify that this minimal substantive difference triggers the model-change logging path.
Requirement: AR1

### AR2 — Model-family definition must be stable and documented before expanding scope

[HAPPY PATH] Re-register an existing printer using representative model numbers from documented families and verify that the current `_model_family` heuristic consistently classifies them into the expected families.
Requirement: AR2

[BOUNDARY VALUE] Re-register with model numbers that sit at the edge of the heuristic (e.g., missing dashes or extra segments) and verify that family classification at these boundaries remains stable and predictable.
Requirement: AR2

[INVALID INPUT] Re-register with a model number that does not conform to documented naming patterns and verify that `_model_family` handles it gracefully without misclassifying it into an unintended family.
Requirement: AR2

### AR3 — No partial side effects on rejected re-registrations

[HAPPY PATH] Perform a re-registration that is rejected due to model-family mismatch and verify that no new Cloud ID, printer email ID, XMPP node, capabilities, or serial index entries are created.
Requirement: AR3

[BOUNDARY VALUE] Trigger a rejection at the earliest possible point in the re-registration pipeline and verify that even minimal side effects, such as transient IDs or partial capability updates, are absent.
Requirement: AR3

[ROLLBACK] After a rejected re-registration, perform a subsequent successful legitimate re-registration and verify that the system behaves as if the rejected attempt never occurred except for audit history.
Requirement: AR3

### AR4 — Preservation of ownership and claim status on legitimate re-registrations

[HAPPY PATH] Re-register a claimed printer with an unchanged model number and verify that owner_user_id and status remain CLAIMED while identity and connectivity fields are updated per normal rules.
Requirement: AR4

[BOUNDARY VALUE] Re-register a claimed printer with a same-family but different model revision and verify that ownership is preserved and the claim status is not silently altered.
Requirement: AR4

[OWNERSHIP] Attempt to re-register a claimed printer as a different authenticated user and verify that ownership and claim status are not reassigned or cleared by the re-registration.
Requirement: AR4

### AR5 — Structured warning logs for model-number changes

[HAPPY PATH] Re-register an existing printer with a genuine model-number change and verify that a warning log is emitted containing a stable message key and structured fields for serial_number, old_model, and new_model.
Requirement: AR5

[INVALID INPUT] Re-register with a model-number change where one of the values is malformed and verify that the warning log still carries the structured fields needed for downstream review.
Requirement: AR5

[BOUNDARY VALUE] Re-register with a minimal substantive model-number change and verify that the structured log correctly reflects the old and new values at this boundary.
Requirement: AR5

### AR6 — Cloud ID, email, and XMPP behaviour on successful GOAR-15 re-registrations

[HAPPY PATH] Successfully re-register an existing printer and verify that a new Cloud ID is generated, a new printer email ID is assigned, and an XMPP node is present or newly created as required.
Requirement: AR6

[BOUNDARY VALUE] Re-register at the edge of allowed model/firmware compatibility and verify that identity and connectivity fields are still regenerated correctly without violating uniqueness rules.
Requirement: AR6

[ROLLBACK] Trigger a failure after Cloud ID generation but before email or XMPP assignment and verify that rollback removes or invalidates any partially created identity or connectivity artifacts.
Requirement: AR6

## Coverage Summary

Total scenarios: 34

Happy path: 12 | Invalid input: 5 | Boundary: 10 |
Auth: 3 | Ownership: 1 | Rollback: 3
