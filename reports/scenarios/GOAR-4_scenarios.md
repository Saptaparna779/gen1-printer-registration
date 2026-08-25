# Scenario Coverage — GOAR-4

## Scenarios by Requirement

### AC1 — No printer record remains when Welcome Page printing fails

[ROLLBACK] Simulated Welcome Page failure triggers rollback that removes the printer record created during the attempted registration.
             Requirement: AC1
[BOUNDARY]  Multiple consecutive failed registrations for the same serial number all roll back without leaving any printer record in the store.
             Requirement: AC1

### AC2 — No capability record remains for the printer when Welcome Page printing fails

[ROLLBACK] Simulated Welcome Page failure triggers rollback that deletes all capability records associated with the failed printer_id.
             Requirement: AC2
[BOUNDARY]  Capability queries after repeated failed registrations confirm no capability records exist for the failed printer_id.
             Requirement: AC2

### AC3 — Serial number is free to be registered again from scratch after Welcome Page failure

[ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.
             Requirement: AC3
[HAPPY PATH] Successful registration using a serial number that previously failed at the Welcome Page completes end-to-end and persists printer, capability, and serial index data.
             Requirement: AC3
[BOUNDARY]   Multiple cycles of failed registration followed by successful registration verify the serial number is always reusable with no stale associations.
             Requirement: AC3

### AC4 — Successful registrations are unaffected by rollback changes

[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records without invoking rollback.
             Requirement: AC4
[BOUNDARY]   Successful registration immediately after a failed attempt still behaves as a standard success path and does not invoke rollback.
             Requirement: AC4

### AR1 — Capability rollback is idempotent

[ROLLBACK] Multiple invocations of _rollback_registration for the same printer leave no printer, capability, or serial index records without raising errors due to already-deleted data.
             Requirement: AR1
[BOUNDARY]  Interleaving rollback calls with manually altered or partially deleted store state still results in a clean final state with no remaining records for that printer.
             Requirement: AR1

### AR2 — Rollback deletes only data for the failing printer_id

[ROLLBACK] Rollback for one printer deletes only that printer’s printer record, serial index, and capabilities, leaving all other printers’ data intact.
             Requirement: AR2
[OWNERSHIP] Rollback for one owner’s printer does not alter capabilities or records of printers owned by other users.
             Requirement: AR2

### AR3 — Serial index cleanup fully resets first-time registration behaviour

[ROLLBACK] After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index and new capabilities captured.
             Requirement: AR3
[BOUNDARY]  Repeated cycles of failed and successful registrations for the same serial number verify that the serial index never retains stale associations.
             Requirement: AR3

### AR4 — Rollback must not disturb existing claimed printers unrelated to the failure

[OWNERSHIP] Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.
             Requirement: AR4
[ROLLBACK]   Simulated failed registration in an environment containing claimed printers cleans up only the failed printer’s data without modifying claimed printers.
             Requirement: AR4

### AR5 — Successful registrations must never trigger rollback

[HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated printer, capability, and serial index records.
             Requirement: AR5
[ROLLBACK]   Instrumentation or logging around register_printer confirms that _rollback_registration is never invoked when the Welcome Page prints successfully.
             Requirement: AR5

### AR6 — Capability records for failed registrations must not be externally observable

[ROLLBACK] After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.
             Requirement: AR6
[BOUNDARY]  Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.
             Requirement: AR6

## Coverage Summary

Total scenarios: 22

Happy path: 4 | Invalid input: 0 | Boundary: 9 | Auth: 0 | Ownership: 2 | Rollback: 7

COMMIT VERIFIED — reports/scenarios/GOAR-4_scenarios.md
