# Scenario Coverage — GOAR-5

## Scenarios by Requirement

### AC1 — Re-registering an already-claimed printer does not clear owner_user_id

[HAPPY PATH] Successful re-registration of a claimed printer preserves owner_user_id while updating other registration fields as required.
             Requirement: AC1
[INVALID INPUT] Re-registration attempt for a claimed printer with missing or malformed serial_number is rejected without altering stored owner_user_id.
             Requirement: AC1
[OWNERSHIP] Re-registration of a claimed printer does not clear, change, or reassign owner_user_id to a different user.
             Requirement: AC1

### AC2 — Re-registering an already-claimed printer does not reset status away from CLAIMED

[HAPPY PATH] Successful re-registration of a claimed printer leaves status as CLAIMED and does not downgrade it to REGISTERED or any non-claimed state.
             Requirement: AC2
[INVALID INPUT] Re-registration attempt for a claimed printer with an invalid status value in the request is rejected with no change to stored status.
             Requirement: AC2
[OWNERSHIP] Re-registration of a claimed printer preserves CLAIMED status so the device remains visible and owned by the same user.
             Requirement: AC2

### AC3 — Registration history is preserved (appended to, not replaced)

[HAPPY PATH] Successful re-registration of a claimed printer results in an additional registration event being logged without deleting prior history entries.
             Requirement: AC3
[ROLLBACK] Failed re-registration of a claimed printer does not truncate or overwrite existing registration history; prior events remain observable.
             Requirement: AC3

### AC4 — First-time registration of a genuinely new serial number is unaffected

[HAPPY PATH] First-time registration of a new serial_number follows the standard flow, creating a new printer record with Cloud ID, Printer Email ID, Claim Code, and status REGISTERED.
             Requirement: AC4
[INVALID INPUT] First-time registration attempt with an invalid or duplicate serial_number is rejected without creating or modifying any printer record.
             Requirement: AC4
[BOUNDARY VALUE] First-time registration with a serial_number at the edge of allowed format or length behaves as a normal successful registration.
             Requirement: AC4

### AR1 — Already-claimed printer must not get a new Claim Code on re-registration

[HAPPY PATH] Successful re-registration of a claimed printer does not generate a new Claim Code and leaves the existing claim_code value unchanged.
             Requirement: AR1
[OWNERSHIP] Re-registration of a claimed printer never associates multiple claim codes with the same device; the original one-time-use claim_code remains authoritative.
             Requirement: AR1

### AR2 — Claimed printers still get new Cloud ID and Printer Email ID on re-registration

[HAPPY PATH] Successful re-registration of a claimed printer generates a new Cloud ID and Printer Email ID while preserving owner_user_id and CLAIMED status.
             Requirement: AR2
[BOUNDARY VALUE] Multiple successive re-registrations of the same claimed printer each produce distinct Cloud ID and Printer Email ID values.
             Requirement: AR2

### AR3 — Failed re-registration of a claimed printer must not leave partial updates

[ROLLBACK] Failed re-registration of a claimed printer leaves owner_user_id, status, serial_number, Cloud ID, Printer Email ID, and claim_code exactly as they were before the attempt from the API client’s perspective.
             Requirement: AR3
[ROLLBACK] Repeated failed re-registration attempts for a claimed printer never result in mixed or partially updated identity or ownership data at the API surface.
             Requirement: AR3

### AR4 — Normal registration behaviour for non-claimed printers remains intact

[HAPPY PATH] Re-registration of a non-claimed printer behaves like standard registration, generating new Cloud ID, Printer Email ID, and Claim Code and ending with status REGISTERED.
             Requirement: AR4
[INVALID INPUT] Re-registration attempt for a non-claimed printer with invalid required fields fails and leaves existing printer identity and status unchanged.
             Requirement: AR4
[BOUNDARY VALUE] Multiple re-registrations of a non-claimed printer continue to generate new identifiers while keeping status REGISTERED.
             Requirement: AR4

### AR5 — Failed re-registration must not persist new identifiers

[ROLLBACK] Failed re-registration of a claimed printer does not persist any newly generated Cloud ID or Printer Email ID; subsequent reads show only pre-existing identifiers.
             Requirement: AR5
[ROLLBACK] Failed re-registration of a non-claimed printer discards all new identifiers, and a later successful registration generates fresh values.
             Requirement: AR5

### AR6 — Audit logging for re-registration of claimed printers

[ROLLBACK] Failed re-registration of a claimed printer produces observable log or telemetry entries indicating the failure and preserving ownership metadata, without relying on specific history storage semantics.
             Requirement: AR6

## Coverage Summary

Total scenarios: 24

Happy path: 8 | Invalid input: 4 | Boundary: 4 | Auth: 0 | Ownership: 5 | Rollback: 3
