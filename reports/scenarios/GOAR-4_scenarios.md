# Scenario Coverage — GOAR-4

## Scenarios by Requirement

### AC1 — When Welcome Page printing fails, no printer record remains

[ROLLBACK] Simulated Welcome Page failure during registration triggers rollback that removes the printer record created for that attempt.
             Requirement: AC1
[BOUNDARY] Simulate two consecutive Welcome Page failures for the same serial and confirm no printer record exists after each rollback.
             Requirement: AC1

### AC2 — When Welcome Page printing fails, no capability record remains for that printer_id

[ROLLBACK] Simulated Welcome Page failure during registration triggers rollback that deletes all capability records associated with the failed printer_id.
             Requirement: AC2
[BOUNDARY] Perform multiple failed registrations for the same printer and verify capability queries always return no capabilities for that printer_id.
             Requirement: AC2

### AC3 — When Welcome Page printing fails, the serial number is free to be registered again from scratch

[ROLLBACK] Registration attempt with simulate_welcome_page_failure=True rolls back and frees the serial so that a subsequent registration behaves like a first-time registration.
             Requirement: AC3
[HAPPY PATH] Successful registration using a serial number that previously failed at the Welcome Page completes and persists printer, capability, and serial index data as for an initial registration.
             Requirement: AC3
[BOUNDARY] Multiple cycles of failed registration followed by successful registration verify the serial number is always reusable with no stale printer, capability, or serial index entries.
             Requirement: AC3

### AC4 — Successful registrations are unaffected (do not regress)

[HAPPY PATH] Successful registration when simulate_welcome_page_failure=False persists printer, capability, and serial index records without invoking rollback.
             Requirement: AC4
[BOUNDARY] Successful registration immediately after a failed attempt still follows the standard success path and does not invoke rollback or lose existing data.
             Requirement: AC4

### AR1 — Capability rollback is idempotent

[ROLLBACK] Multiple invocations of _rollback_registration for the same printer leave no printer, capability, or serial index records and do not raise errors due to already-deleted data.
             Requirement: AR1
[BOUNDARY] Invoke _rollback_registration after manually deleting one or more records in the store and confirm the final state is still clean for that printer.
             Requirement: AR1

### AR2 — Rollback deletes only data for the failing printer_id

[ROLLBACK] Rollback for one printer deletes only that printer’s printer record, serial index, and capabilities, leaving all other printers’ data unchanged.
             Requirement: AR2
[OWNERSHIP] Rollback for one owner’s printer does not alter printer, capability, or serial index records for printers owned by other users.
             Requirement: AR2

### AR3 — Serial index cleanup fully resets first-time registration behaviour

[ROLLBACK] After rollback for a failed registration, registering the same serial number creates a new printer record with a fresh serial index association and new capabilities captured.
             Requirement: AR3
[BOUNDARY] Repeated sequences of failed and successful registrations for the same serial number verify that get_printer_by_serial never returns stale or partially deleted records.
             Requirement: AR3

### AR4 — Rollback must not disturb existing claimed printers unrelated to the failure

[OWNERSHIP] Rollback for a failed registration on an unclaimed printer does not delete or alter records for already-claimed printers.
             Requirement: AR4
[ROLLBACK] Simulated failed registration in an environment containing claimed printers cleans up only the failed printer’s data while leaving claimed printers’ status and associations intact.
             Requirement: AR4

### AR5 — Successful registrations must never trigger rollback

[HAPPY PATH] Registration success path where the Welcome Page prints completes without calling _rollback_registration and preserves all associated printer, capability, and serial index records.
             Requirement: AR5
[ROLLBACK] Instrumentation or call tracking around register_printer confirms that _rollback_registration is never invoked when no WelcomePagePrintError occurs.
             Requirement: AR5

### AR6 — Capability records for failed registrations must not be externally observable

[ROLLBACK] After rollback of a failed registration, downstream capability queries or listings never expose capability data for the failed printer_id.
             Requirement: AR6
[BOUNDARY] Rapid repeated failed registrations for the same serial number do not result in any externally visible capabilities for that printer in list or query APIs.
             Requirement: AR6

## Coverage Summary

Total scenarios: 22

Happy path: 4 | Invalid input: 0 | Boundary: 9 | Auth: 0 | Ownership: 2 | Rollback: 7
