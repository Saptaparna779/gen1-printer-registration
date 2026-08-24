# Scenario Coverage — GOAR-4

## Scenarios by Requirement

### AC1 — No printer record remains when Welcome Page printing fails

[HAPPY PATH] Welcome Page prints successfully and printer record is persisted without invoking rollback.
             Requirement: AC4
[ROLLBACK]   Simulated Welcome Page failure triggers rollback that removes the printer record created during registration.
             Requirement: AC1
[ROLLBACK]   Failed registration leaves no printer record and allows subsequent inspection to confirm absence of printer data.
             Requirement: AC1

### AC2 — No capability record remains for the printer when Welcome Page printing fails

[HAPPY PATH] Successful registration persists capability records for the printer_id and they remain after completion.
             Requirement: AC4
[ROLLBACK]   Simulated Welcome Page failure triggers rollback that deletes capability records associated with the failed printer_id.
             Requirement: AC2
[ROLLBACK]   After a failed registration, capability queries for the failed printer_id return no capability data.
             Requirement: AC2

### AC3 — Serial number is free to be registered again after Welcome Page failure

[HAPPY PATH] First-time successful registration with a given serial number completes and reserves that serial.
             Requirement: AC4
[ROLLBACK]   Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.
             Requirement: AC3
[BOUNDARY]   Multiple consecutive failed registrations with the same serial number all roll back cleanly, leaving the serial reusable each time.
             Requirement: AC3

### AC4 — Successful registrations remain unaffected (no regression)

[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records unchanged by rollback.
             Requirement: AC4
[ROLLBACK]   Verify that no rollback operations (deletion of printer, capabilities, or serial index) are invoked during a fully successful registration.
             Requirement: AC4

### AR1 — Capability rollback must be idempotent

[ROLLBACK]   Multiple invocations of _rollback_registration for the same printer_id leave no printer, capability, or serial index records without raising additional errors.
             Requirement: AR1
[BOUNDARY]   Interleave rollback calls with partial store deletions (e.g., capabilities already deleted) and confirm final state still has no remaining records.
             Requirement: AR1

### AR2 — Capability rollback must be scoped to the failing registration’s printer_id

[ROLLBACK]   Rollback for one printer_id deletes only that printer’s capabilities and leaves capabilities for other printers intact.
             Requirement: AR2
[OWNERSHIP]  Rollback for an unclaimed printer does not alter capabilities or records of other printers, including those with different owners.
             Requirement: AR2

### AR3 — Serial index rollback must fully free the serial for reuse

[ROLLBACK]   After rollback, registering the same serial number creates a new printer record with a fresh association in the serial index.
             Requirement: AR3
[BOUNDARY]   Repeated cycles of failed registration followed by successful registration for the same serial verify that the serial index never retains stale associations.
             Requirement: AR3

### AR4 — Rollback must not change the state of already-claimed printers unrelated to the failing registration

[OWNERSHIP]  Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.
             Requirement: AR4
[ROLLBACK]   Simulate a failed registration in an environment containing claimed printers and verify only the failed printer’s data is cleaned up.
             Requirement: AR4

### AR5 — Successful registration must never invoke rollback

[HAPPY PATH] Registration success path completes without calling _rollback_registration and preserves all associated records.
             Requirement: AR5
[ROLLBACK]   Instrumentation or logging confirms that rollback is never invoked when the Welcome Page prints successfully.
             Requirement: AR5

### AR6 — Capability records for failed registrations must not be externally visible

[ROLLBACK]   After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.
             Requirement: AR6
[BOUNDARY]   Rapid repeated failed registrations do not result in any transiently visible capabilities in external-facing queries.
             Requirement: AR6

## Coverage Summary

Total scenarios: 20

Happy path: 6 | Invalid input: 0 | Boundary: 4 | Auth: 0 | Ownership: 2 | Rollback: 8
