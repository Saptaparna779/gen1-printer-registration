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
[AUTH] Registration attempt without an Authorization header is rejected and does not create any printer, capability, or serial index records.
           Requirement: AC4
[AUTH] Registration attempt with an invalid or expired token is rejected and does not create any printer, capability, or serial index records.
           Requirement: AC4

### AR1 — Rollback must be triggered for any failure prior to successful Welcome Page printing

[HAPPY PATH] A non-simulated failure before the Welcome Page prints triggers rollback that removes printer record, capability record, and serial index.
           Requirement: AR1
[ROLLBACK] Simulated Welcome Page print failure and a real WelcomePagePrintError both invoke rollback so that no partial printer, capability, or serial index data remains afterward.
           Requirement: AR1

### AR2 — Capability deletion in rollback must be idempotent and safe when no capability exists

[ROLLBACK] A failed registration where capabilities were created during the current attempt leaves no capability record for the printer_id after rollback, avoiding orphans.
           Requirement: AR2
[BOUNDARY VALUE] Rollback on a failed registration where no capability record exists for the printer_id completes without error and still deletes any printer record and serial index.
           Requirement: AR2

### AR3 — Serial index removal must succeed even if printer record creation partially failed

[ROLLBACK] After rollback from a failed registration, lookups by the failed serial number do not return any stale printer_id mapping.
           Requirement: AR3
[BOUNDARY VALUE] Failed registration where serial index was created but printer record was never persisted still removes the serial index during rollback so the serial can be reused.
           Requirement: AR3

### AR4 — Rollback must not affect existing printers unrelated to the failed registration

[HAPPY PATH] Failed registration for a new printer rolls back printer, capability, and serial index for that printer_id while leaving existing printers untouched.
           Requirement: AR4
[OWNERSHIP] Rollback for a failed registration of one printer_id does not delete or modify printer records, capabilities, or serial indices belonging to other printers.
           Requirement: AR4

### AR5 — Successful registrations must persist all required data even after intermittent failures

[HAPPY PATH] After one or more failed registration attempts that rolled back fully, a subsequent successful registration for the same serial number persists printer, capability, and serial index data.
           Requirement: AR5
[ROLLBACK] Previous failed registrations that invoked rollback do not remove or corrupt printer, capability, or serial index data created by a later successful registration.
           Requirement: AR5

## Coverage Summary

Total scenarios: 20

Happy path: 7 | Invalid input: 0 | Boundary: 3 |
Auth: 2 | Ownership: 1 | Rollback: 7
