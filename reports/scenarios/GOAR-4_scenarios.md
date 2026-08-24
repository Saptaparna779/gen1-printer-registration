# Scenario Coverage — GOAR-4

## Scenarios by Requirement

### AC1 — No printer record remains when Welcome Page printing fails

[ROLLBACK] Simulated Welcome Page failure triggers rollback that removes the printer record created during registration.
             Requirement: AC1
[BOUNDARY]  Multiple consecutive failed registrations for the same serial_number all roll back without leaving any printer record.
             Requirement: AC1

### AC2 — No capability record remains for the printer when Welcome Page printing fails

[ROLLBACK] Simulated Welcome Page failure triggers rollback that deletes capability records associated with the failed printer_id.
             Requirement: AC2
[BOUNDARY]  Capability queries after repeated failed registrations confirm no capability records exist for the failed printer_id.
             Requirement: AC2

### AC3 — Serial number is free to be registered again after Welcome Page failure

[HAPPY PATH] First-time successful registration with a given serial_number completes and reserves that serial.
             Requirement: AC3
[ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.
             Requirement: AC3
[BOUNDARY]   Multiple cycles of failed registration followed by successful registration verify the serial_number is always reusable with no stale associations.
             Requirement: AC3

### AC4 — Successful registrations remain unaffected (no regression)

[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records unchanged by rollback logic.
             Requirement: AC4
[BOUNDARY]   Successful registration immediately after a failed attempt still behaves as a standard success and does not invoke rollback.
             Requirement: AC4

### AR1 — Capability rollback must be idempotent

[ROLLBACK] Multiple invocations of _rollback_registration for the same printer_id leave no printer, capability, or serial index records without raising additional errors.
             Requirement: AR1
[BOUNDARY]  Interleave rollback calls with partially deleted store state and confirm the final state still has no remaining records or errors.
             Requirement: AR1

### AR2 — Capability rollback must be scoped to the failing registration’s printer_id

[ROLLBACK] Rollback for one printer_id deletes only that printer’s capabilities and leaves capabilities for other printers intact.
             Requirement: AR2
[OWNERSHIP] Rollback for one owner’s printer does not alter capabilities or records of printers owned by other users.
             Requirement: AR2

### AR3 — Serial index rollback must fully free the serial for reuse

[ROLLBACK] After rollback, registering the same serial_number creates a new printer record with a fresh association in the serial index.
             Requirement: AR3
[BOUNDARY]  Repeated cycles of failed and successful registrations for the same serial_number verify that the serial index never retains stale associations.
             Requirement: AR3

### AR4 — Rollback must not change the state of already-claimed printers unrelated to the failing registration

[OWNERSHIP] Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.
             Requirement: AR4
[ROLLBACK]   Simulated failed registration in an environment containing claimed printers cleans up only the failed printer’s data.
             Requirement: AR4

### AR5 — Successful registration must never invoke rollback

[HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated records.
             Requirement: AR5
[ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.
             Requirement: AR5

### AR6 — Capability records for failed registrations must not be externally visible

[ROLLBACK] After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.
             Requirement: AR6
[BOUNDARY]  Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.
             Requirement: AR6

## Coverage Summary

Total scenarios: 22

Happy path: 3 | Invalid input: 0 | Boundary: 9 | Auth: 0 | Ownership: 3 | Rollback: 7
