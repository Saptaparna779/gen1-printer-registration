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

### AR1 — Capability rollback must be idempotent

[ROLLBACK] Calling rollback multiple times for the same failed registration leaves no printer record, capability record, or serial index for that serial number.
           Requirement: AR1
[BOUNDARY VALUE] A second rollback call after records are already deleted completes without raising errors caused by missing printer, capability, or serial index data.
           Requirement: AR1

### AR2 — Capability rollback must be scoped to the failing registration’s printer_id

[HAPPY PATH] Rollback for a failed registration deletes capabilities only for the failing printer_id and leaves capabilities for other printer_ids intact.
           Requirement: AR2
[OWNERSHIP] Rollback for a failed registration of one printer_id does not delete or modify capability records belonging to other printers or owners.
           Requirement: AR2

### AR3 — Serial index rollback must fully free the serial for reuse

[HAPPY PATH] After rollback from a failed registration, a subsequent registration with the same serial_number behaves exactly like a first-time registration.
           Requirement: AR3
[ROLLBACK] After rollback, lookups by the failed serial_number show no residual serial index or printer mapping that would block reuse.
           Requirement: AR3

### AR4 — Rollback must not change the state of already-claimed printers unrelated to the failing registration

[HAPPY PATH] Rollback for a failed registration of a new printer_id does not alter the records or claim state of any already-claimed printers.
           Requirement: AR4
[OWNERSHIP] Rollback invoked for a failed registration does not delete or modify printer, capability, or serial index data for any other CLAIMED printer.
           Requirement: AR4

### AR5 — Successful registration must never invoke rollback

[HAPPY PATH] A successful registration where the Welcome Page prints does not call rollback and preserves printer, capability, and serial index data.
           Requirement: AR5
[ROLLBACK] Failed registration attempts that invoke rollback do not trigger rollback during later successful registrations for the same serial_number.
           Requirement: AR5

### AR6 — Capability records for failed registrations must not be externally visible

[ROLLBACK] After rollback of a failed registration, no capability records for that printer_id are returned by downstream capability or device list queries.
           Requirement: AR6
[BOUNDARY VALUE] Capability records created during a failed registration are deleted by rollback before any subsequent external query can observe them.
           Requirement: AR6

## Coverage Summary

Total scenarios: 22

Happy path: 9 | Invalid input: 0 | Boundary: 3 |
Auth: 2 | Ownership: 3 | Rollback: 5
