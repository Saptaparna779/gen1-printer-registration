# Scenario Coverage — GOAR-3

## Scenarios by Requirement

### AC1 — Every call to register a printer generates a brand new Cloud ID

[HAPPY PATH] Initial registration of a new printer followed by re-registration of the same serial_number both succeed and the second response returns a Cloud ID different from the first.
             Requirement: AC1

[BOUNDARY VALUE] Three consecutive successful registration calls for the same serial_number (initial + two re-registrations) each return a Cloud ID that is unique across the entire sequence.
             Requirement: AC1

[ROLLBACK] A registration or re-registration attempt that fails before the Welcome Page prints does not persist any new Cloud ID and leaves existing printer records and indexes unchanged.
             Requirement: AC1


### AC2 — Printer Email ID and Claim Code continue to be regenerated on re-registration

[HAPPY PATH] Re-registering an already-registered printer succeeds and the new response contains a printer_email_id and claim_code that both differ from those returned by the previous successful registration.
             Requirement: AC2

[BOUNDARY VALUE] Multiple successful re-registrations for the same serial_number each return a printer_email_id and claim_code that are unique relative to all prior values for that printer.
             Requirement: AC2

[ROLLBACK] A failed re-registration that occurs before the Welcome Page prints does not change the persisted printer_email_id or claim_code and leaves all indexes consistent.
             Requirement: AC2


### AR1 — Re-registration of a CLAIMED printer preserves ownership while issuing a new Cloud ID

[HAPPY PATH] Re-registering a printer that is already in CLAIMED status succeeds, returns a new Cloud ID, and the printer’s owner_user_id and CLAIMED status remain unchanged.
             Requirement: AR1

[OWNERSHIP] Re-registration of a CLAIMED printer is verified to preserve owner_user_id and CLAIMED status even as Cloud ID and other registration identifiers are regenerated.
             Requirement: AR1

[ROLLBACK] A failed re-registration of a CLAIMED printer before the Welcome Page prints leaves owner_user_id, CLAIMED status, and prior Cloud ID unchanged with no partial updates.
             Requirement: AR1


### AR2 — Two consecutive re-registrations of the same serial yield three distinct Cloud IDs

[HAPPY PATH] Initial registration followed by two successful re-registrations of the same serial_number produces three responses whose Cloud IDs are all distinct from one another.
             Requirement: AR2

[BOUNDARY VALUE] The Cloud ID from the second re-registration is explicitly verified to differ from both the initial registration’s Cloud ID and the first re-registration’s Cloud ID, ensuring no reuse of earlier values.
             Requirement: AR2


### AR3 — Failed re-registration Cloud ID is rolled back and never reused

[HAPPY PATH] After a failed re-registration attempt that triggers rollback, a subsequent successful registration or re-registration for the same serial_number returns a Cloud ID that is new and distinct from both the original Cloud ID and any Cloud ID generated during the failed attempt.
             Requirement: AR3

[ROLLBACK] A re-registration attempt that fails before the Welcome Page prints leaves the stored printer record, including Cloud ID and all indexes, exactly as before the attempt with no partial changes.
             Requirement: AR3


### AR4 — Re-registration after deregistration generates a new Cloud ID

[HAPPY PATH] Registering, then deregistering, and then re-registering the same serial_number all succeed and the Cloud ID assigned after re-registration differs from the Cloud ID that existed before deregistration.
             Requirement: AR4

[BOUNDARY VALUE] Multiple deregister-then-re-register cycles for the same serial_number each produce a new Cloud ID that has never been used before for that serial_number.
             Requirement: AR4


### AR5 — Failed re-registration rollback fully removes records so next registration is fresh

[ROLLBACK] A re-registration attempt that fails before the Welcome Page prints removes the printer record and all associated indexes so that a subsequent registration of the same serial_number behaves as a fresh first-time registration.
             Requirement: AR5

[HAPPY PATH] After a failed re-registration has been fully rolled back, a new registration for the same serial_number succeeds and behaves identically to registering a completely new printer, including assignment of a new Cloud ID and indexes.
             Requirement: AR5


### AR6 — Registration and re-registration failures emit structured logs

[HAPPY PATH] A failed registration or re-registration due to a Welcome Page print error emits a structured log entry containing at least serial_number, printer_id (when available), and a machine-parseable failure reason.
             Requirement: AR6

[BOUNDARY VALUE] A failed registration or re-registration due to a model-family mismatch emits a structured log entry that also includes serial_number, printer_id (when available), and a machine-parseable failure reason.
             Requirement: AR6


## Coverage Summary

Total scenarios: 19

Happy path: 8 | Invalid input: 0 | Boundary: 5 | Auth: 0 | Ownership: 1 | Rollback: 5
