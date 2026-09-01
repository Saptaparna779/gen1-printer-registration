# Scenario Coverage — GOAR-5

## Scenarios by Requirement

### AC1 — Re-registering an already-claimed printer does not clear owner_user_id

[HAPPY PATH] Re-register a claimed printer and confirm owner_user_id remains unchanged while other registration fields update as expected.
             Requirement: AC1
[INVALID INPUT] Attempt re-registration of a claimed printer with a missing or null owner_user_id in the payload and confirm the request is rejected without altering stored ownership.
             Requirement: AC1
[OWNERSHIP] Re-register a claimed printer and confirm no ownership fields (owner_user_id, claim status) are cleared, reassigned, or replaced.
             Requirement: AC1
[ROLLBACK] Trigger a controlled failure during re-registration of a claimed printer and confirm owner_user_id in persistent storage is unchanged after rollback.
             Requirement: AC1

### AC2 — Re-registering an already-claimed printer does not reset status away from CLAIMED

[HAPPY PATH] Re-register a claimed printer and confirm its status remains CLAIMED after successful re-registration.
             Requirement: AC2
[INVALID INPUT] Attempt re-registration of a claimed printer with an invalid status value in the request and confirm the request is rejected with no change to stored status.
             Requirement: AC2
[OWNERSHIP] Re-register a claimed printer and confirm its CLAIMED status is not changed to REGISTERED or any non-claimed state during the flow.
             Requirement: AC2
[ROLLBACK] Cause re-registration of a claimed printer to fail before the Welcome Page prints and confirm its status remains CLAIMED after rollback.
             Requirement: AC2

### AC3 — Registration history is preserved (appended to, not replaced)

[HAPPY PATH] Re-register a claimed printer and confirm observable registration history shows a new entry appended while prior entries remain intact.
             Requirement: AC3
[INVALID INPUT] Attempt an invalid re-registration and confirm registration history does not gain a new successful-entry record for the failed attempt.
             Requirement: AC3
[ROLLBACK] Trigger a failed re-registration attempt and confirm any transient history or log entries do not replace or truncate existing registration history.
             Requirement: AC3

### AC4 — First-time registration of a genuinely new serial number is unaffected

[HAPPY PATH] Perform first-time registration for a new serial number and confirm it follows the standard registration flow and outcomes (status REGISTERED, new Cloud ID, email, and claim code).
             Requirement: AC4
[INVALID INPUT] Attempt first-time registration with an invalid or malformed serial_number and confirm registration is rejected without creating a printer record.
             Requirement: AC4
[BOUNDARY VALUE] Perform first-time registration using a serial_number at the boundary of validity (e.g., shortest or longest allowed) and confirm behavior matches standard registration.
             Requirement: AC4

### AR1 — Already-claimed printer must not get a new Claim Code on re-registration

[HAPPY PATH] Re-register an already-claimed printer and confirm no new Claim Code is generated and the existing claim_code remains unchanged.
             Requirement: AR1
[OWNERSHIP] Re-register a claimed printer and confirm claim_code state is preserved and no additional claim codes are associated with the device.
             Requirement: AR1
[ROLLBACK] Force a failure during re-registration of a claimed printer and confirm claim_code state is unchanged after rollback.
             Requirement: AR1

### AR2 — Claimed printers still get new Cloud ID and Printer Email ID on re-registration

[HAPPY PATH] Re-register an already-claimed printer and confirm a new Cloud ID and Printer Email ID are generated while owner_user_id and CLAIMED status remain unchanged.
             Requirement: AR2
[BOUNDARY VALUE] Re-register the same claimed printer multiple times in succession and confirm each registration generates distinct Cloud ID and Printer Email ID values.
             Requirement: AR2
[ROLLBACK] Trigger a failed re-registration of a claimed printer and confirm no newly generated Cloud ID or Printer Email ID is persisted after rollback.
             Requirement: AR2

### AR3 — Rollback for claimed printers restores or preserves prior claimed state

[ROLLBACK] Cause re-registration of a claimed printer to fail before the Welcome Page prints and confirm owner_user_id, status, and any observable registration-related data remain unchanged.
             Requirement: AR3
[ROLLBACK] Simulate repeated failures during re-registration of a claimed printer and confirm each failure leaves the printer in the same claimed state with no partial updates.
             Requirement: AR3
[OWNERSHIP] Verify that rollback after a failed re-registration does not affect the printer’s visibility or ownership in client applications that rely on CLAIMED status.
             Requirement: AR3

### AR4 — Normal registration behaviour for non-claimed printers remains intact

[HAPPY PATH] Re-register a non-claimed printer and confirm it behaves as a normal registration, generating new Cloud ID, Printer Email ID, and Claim Code, and ending with status REGISTERED.
             Requirement: AR4
[INVALID INPUT] Attempt re-registration of a non-claimed printer with invalid required fields and confirm registration fails without changing existing records.
             Requirement: AR4
[BOUNDARY VALUE] Perform repeated re-registrations of a non-claimed printer and confirm each registration produces new identifiers while maintaining status REGISTERED.
             Requirement: AR4

### AR5 — Failed re-registration must not persist new identifiers

[ROLLBACK] Trigger a failed re-registration for a claimed printer and confirm any newly generated Cloud ID and Printer Email ID are discarded and not present in subsequent reads.
             Requirement: AR5
[ROLLBACK] Trigger a failed re-registration for a non-claimed printer and confirm no new identifiers are persisted and a subsequent successful registration generates fresh values.
             Requirement: AR5
[BOUNDARY VALUE] Perform multiple failed re-registrations followed by a successful one and confirm none of the identifiers from failed attempts are reused.
             Requirement: AR5

### AR6 — Audit logging for re-registration of claimed printers

[HAPPY PATH] Re-register a claimed printer and confirm audit logs include structured fields indicating it was already claimed and that owner_user_id and status were preserved.
             Requirement: AR6
[INVALID INPUT] Perform a re-registration attempt for a claimed printer with invalid input and confirm audit logs capture the failure details without logging misleading ownership changes.
             Requirement: AR6
[ROLLBACK] Trigger a rollback during re-registration of a claimed printer and confirm audit logs clearly record the rollback event and that claimed ownership was preserved.
             Requirement: AR6

## Coverage Summary

Total scenarios: 30

Happy path: 8 | Invalid input: 6 | Boundary: 4 | Auth: 0 | Ownership: 6 | Rollback: 6
