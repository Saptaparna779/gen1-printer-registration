# Scenario Coverage — GOAR-4

## Scenarios by Requirement

### AC1 — When Welcome Page printing fails, no printer record remains.

[HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a printer record present.
           Requirement: AC1
[ROLLBACK] Registration where Welcome Page printing fails removes the printer record so no printer remains for that printer_id.
           Requirement: AC1

### AC2 — When Welcome Page printing fails, no capability record remains for that printer_id.

[HAPPY PATH] Successful registration with Welcome Page printing completes and leaves a capability record associated with the printer_id.
           Requirement: AC2
[ROLLBACK] Registration where Welcome Page printing fails removes any capability record associated with the printer_id so none remain.
           Requirement: AC2

### AC3 — When Welcome Page printing fails, the serial number is free to be registered again from scratch.

[HAPPY PATH] Successful registration with Welcome Page printing completes and allows lookup of the printer via its serial number.
           Requirement: AC3
[ROLLBACK] Registration where Welcome Page printing fails removes the serial index so a subsequent registration using the same serial number behaves like a fresh registration.
           Requirement: AC3

### AC4 — Successful registrations are unaffected (do not regress).

[HAPPY PATH] Successful registration with Welcome Page printing persists printer, capabilities, and serial index and is not impacted by rollback changes.
           Requirement: AC4

### AR1 — Rollback must be invoked for any failure before Welcome Page prints, not only simulated failures.

[HAPPY PATH] A non-simulated failure before the Welcome Page prints triggers rollback that removes printer record, capability record, and serial index.
           Requirement: AR1
[ROLLBACK] Simulated Welcome Page print failure and a real WelcomePagePrintError both invoke rollback so that no partial printer, capability, or serial index data remains afterward.
           Requirement: AR1

### AR2 — Rollback must remove capabilities even if they were pre-existing for that printer_id.

[ROLLBACK] A failed registration where capabilities were created during the current attempt leaves no capability record for the printer_id after rollback, avoiding orphans.
           Requirement: AR2

### AR3 — Serial index removal must ensure no stale serial mapping remains.

[ROLLBACK] After rollback from a failed registration, lookups by the failed serial number do not return any stale printer_id mapping.
           Requirement: AR3
[BOUNDARY VALUE] Repeated failed registrations using the same serial number each roll back cleanly without leaving any serial index mapping that could link to prior attempts.
           Requirement: AR3

### AR4 — Rollback behaviour must be identical for first-time registration and re-registration failures.

[HAPPY PATH] A first-time registration failure before the Welcome Page prints rolls back printer record, capabilities, and serial index completely.
           Requirement: AR4
[ROLLBACK] A re-registration failure before the Welcome Page prints rolls back printer record, capabilities, and serial index in the same way as a first-time registration failure.
           Requirement: AR4

### AR5 — Rollback must be idempotent for a given failed registration attempt.

[ROLLBACK] Invoking rollback multiple times for the same failed registration attempt leaves the system in a clean state with no printer record, capability record, or serial index.
           Requirement: AR5
[BOUNDARY VALUE] Concurrent or rapid repeated rollback invocations for the same printer_id do not leave partial data or cause inconsistent state.
           Requirement: AR5

## Coverage Summary

Total scenarios: 17

Happy path: 6 | Invalid input: 0 | Boundary: 2 |
Auth: 0 | Ownership: 0 | Rollback: 9
