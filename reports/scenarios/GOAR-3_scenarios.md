# Scenario Coverage — GOAR-3

## Scenarios by Requirement

### AC1 — Every registration call generates a brand new Cloud ID

[HAPPY PATH] Initial registration and subsequent re-registration of the same serial number both succeed and the second response returns a Cloud ID different from the first.
             Requirement: AC1

[BOUNDARY VALUE] Multiple sequential registrations for the same serial number (for example, three successful calls in a row) each return a Cloud ID that is unique across the entire sequence.
             Requirement: AC1


### AC2 — Printer Email ID and Claim Code regenerated on re-registration

[HAPPY PATH] Re-registering an already-registered printer succeeds and the new response contains a printer_email_id and claim_code that both differ from those returned by the previous registration.
             Requirement: AC2

[INVALID INPUT] Re-registration with an otherwise valid request that attempts to reuse a previously assigned printer_email_id is rejected without changing any existing identifiers.
             Requirement: AC2

[ROLLBACK] A failed re-registration that attempts to assign a duplicate printer_email_id leaves the persisted printer_email_id and claim_code unchanged from their pre-attempt values.
             Requirement: AC2


### AR1 — Re-registration of a CLAIMED printer preserves ownership while issuing a new Cloud ID

[HAPPY PATH] Re-registering a printer that is already in CLAIMED status succeeds, returns a new Cloud ID, and the printer’s owner_user_id and CLAIMED status remain unchanged.
             Requirement: AR1

[OWNERSHIP] A non-owner actor attempting to re-register a CLAIMED printer cannot change owner_user_id, and the printer remains associated with the original owner even though the Cloud ID is regenerated.
             Requirement: AR1

[ROLLBACK] A failed re-registration of a CLAIMED printer before the Welcome Page prints leaves owner_user_id and CLAIMED status unchanged and does not persist any partial Cloud ID change.
             Requirement: AR1


### AR2 — Two consecutive re-registrations yield three distinct Cloud IDs

[HAPPY PATH] Initial registration followed by two consecutive successful re-registrations for the same serial number produces three responses whose Cloud IDs are all distinct from one another.
             Requirement: AR2

[BOUNDARY VALUE] The Cloud ID from the second re-registration is explicitly verified to be different from both the first registration’s Cloud ID and the first re-registration’s Cloud ID, ensuring no reuse of earlier values.
             Requirement: AR2


### AR3 — Failed re-registration Cloud ID is rolled back and never reused

[HAPPY PATH] After a failed re-registration attempt that triggers rollback, a subsequent successful re-registration for the same serial number returns a Cloud ID that is new and distinct from both the original Cloud ID and any Cloud ID generated during the failed attempt.
             Requirement: AR3

[ROLLBACK] A re-registration attempt that fails before the Welcome Page prints leaves the stored printer record, including Cloud ID and indexes, exactly as before the attempt with no partial changes.
             Requirement: AR3


### AR4 — Re-registration after deregistration generates a new Cloud ID

[HAPPY PATH] Registering, then deregistering, and then re-registering the same serial number all succeed and the Cloud ID assigned after re-registration differs from the Cloud ID that existed before deregistration.
             Requirement: AR4

[BOUNDARY VALUE] Multiple deregister-then-re-register cycles for the same serial number each produce a new Cloud ID that has never been used before for that serial number.
             Requirement: AR4


### AR5 — Full rollback removes all records after failed re-registration

[ROLLBACK] A re-registration attempt that fails before the Welcome Page prints removes the printer record and all associated indexes so that a subsequent registration of the same serial number behaves as a fresh first-time registration.
             Requirement: AR5

[HAPPY PATH] After a failed re-registration has been fully rolled back, a new registration for the same serial number succeeds and behaves identically to registering a completely new printer, including assignment of a new Cloud ID and indexes.
             Requirement: AR5


## Coverage Summary

Total scenarios: 15

Happy path: 7 | Invalid input: 1 | Boundary: 3 | Auth: 0 | Ownership: 1 | Rollback: 3
