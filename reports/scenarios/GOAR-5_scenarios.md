# Scenario Coverage — GOAR-5

## Scenarios by Requirement

### AC1 — Re-registering an already-claimed printer does not clear owner_user_id

[HAPPY PATH] Re-register an already-claimed printer and confirm owner_user_id remains unchanged after re-registration.
             Requirement: AC1
[OWNERSHIP] Re-register a claimed printer that has an existing owner_user_id and confirm no ownership fields are cleared or reassigned.
             Requirement: AC1
[ROLLBACK] Trigger a controlled failure during re-registration of a claimed printer and confirm owner_user_id remains intact after the failure.
             Requirement: AC1

### AC2 — Re-registering an already-claimed printer does not reset status away from CLAIMED

[HAPPY PATH] Re-register an already-claimed printer and confirm its status remains CLAIMED after re-registration.
             Requirement: AC2
[OWNERSHIP] Re-register a claimed printer and confirm its CLAIMED status is not changed to REGISTERED or any non-claimed state.
             Requirement: AC2
[ROLLBACK] Cause re-registration of a claimed printer to fail before completion and confirm its status remains CLAIMED after rollback.
             Requirement: AC2

### AC3 — Registration history is preserved (appended to, not replaced)

[HAPPY PATH] Re-register a claimed printer and confirm registration history entries are appended rather than replacing existing history.
             Requirement: AC3
[ROLLBACK] Trigger a failed re-registration attempt and confirm registration history reflects only successful registrations with no partial or duplicate entries.
             Requirement: AC3

### AC4 — First-time registration of a genuinely new serial number is unaffected

[HAPPY PATH] Perform first-time registration for a new serial number and confirm it follows the standard registration flow and outcomes.
             Requirement: AC4
[INVALID INPUT] Attempt first-time registration with an invalid or malformed serial number and confirm registration is rejected without creating a printer record.
             Requirement: AC4
[BOUNDARY VALUE] Perform first-time registration using a serial number at the boundary of validity (e.g., shortest or longest allowed) and confirm behavior matches standard registration.
             Requirement: AC4

### AR1 — No new claim code for already-claimed printers on re-registration

[HAPPY PATH] Re-register an already-claimed printer and confirm no new claim code is generated or returned.
             Requirement: AR1
[OWNERSHIP] Re-register a claimed printer and confirm the previously issued claim code remains unchanged and no additional claim code is issued.
             Requirement: AR1
[ROLLBACK] Force a failure during re-registration of a claimed printer and confirm claim code state is unchanged after rollback.
             Requirement: AR1

### AR2 — Cloud ID and Printer Email ID regeneration for claimed printers

[HAPPY PATH] Re-register an already-claimed printer and confirm a new Cloud ID and Printer Email ID are generated while ownership details remain unchanged.
             Requirement: AR2
[BOUNDARY VALUE] Re-register a claimed printer multiple times in succession and confirm each registration generates distinct Cloud ID and Printer Email ID values.
             Requirement: AR2
[ROLLBACK] Trigger a failed re-registration of a claimed printer and confirm no new Cloud ID or Printer Email ID is persisted after rollback.
             Requirement: AR2

### AR3 — Rollback preserves claimed state on failure during re-registration

[ROLLBACK] Cause re-registration of a claimed printer to fail before the Welcome Page prints and confirm owner_user_id, status, and prior registration-related data remain unchanged.
             Requirement: AR3
[ROLLBACK] Simulate repeated failures during re-registration of a claimed printer and confirm each failure leaves the printer in the same claimed state with no partial updates.
             Requirement: AR3
[OWNERSHIP] Verify that rollback after a failed re-registration does not affect the printer’s visibility or ownership in client applications.
             Requirement: AR3

### AR4 — Normal registration behaviour for non-claimed printers remains intact

[HAPPY PATH] Re-register a non-claimed printer and confirm it behaves as a normal registration, generating new Cloud ID, Printer Email ID, and Claim Code, and ending with status REGISTERED.
             Requirement: AR4
[INVALID INPUT] Attempt re-registration of a non-claimed printer with invalid required fields and confirm registration fails without changing existing records.
             Requirement: AR4
[BOUNDARY VALUE] Perform repeated re-registrations of a non-claimed printer and confirm each registration produces new identifiers while maintaining status REGISTERED.
             Requirement: AR4

### AR5 — Audit logging of re-registration for claimed printers

[HAPPY PATH] Re-register a claimed printer and confirm audit logs include printer_id, serial_number, previous status, new status, and a flag indicating it was already claimed.
             Requirement: AR5
[INVALID INPUT] Perform a re-registration attempt for a claimed printer with invalid input and confirm audit logs capture the failure details without logging misleading ownership changes.
             Requirement: AR5
[ROLLBACK] Trigger a rollback during re-registration of a claimed printer and confirm audit logs clearly record the rollback event and that claimed ownership was preserved.
             Requirement: AR5

## Coverage Summary

Total scenarios: 27

Happy path: 8 | Invalid input: 3 | Boundary: 3 | Auth: 0 | Ownership: 6 | Rollback: 7
