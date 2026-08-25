# Scenario Coverage — GOAR-8

## Scenarios by Requirement

### AC1 — claim_printer() rejects already-CLAIMED printers

[HAPPY PATH] Claiming an unclaimed printer with a valid, unused claim code succeeds and sets status to CLAIMED with owner_user_id linked to the claimant.
             Requirement: AC2
[INVALID INPUT] Attempting to claim a printer whose status is already CLAIMED with a valid, unused claim code raises InvalidClaimCodeError and does not change ownership.
             Requirement: AC1
[OWNERSHIP] Claiming an already-CLAIMED printer with a user_id matching the existing owner_user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged.
             Requirement: AR1
[OWNERSHIP] Claiming an already-CLAIMED printer with a different user_id is rejected with InvalidClaimCodeError and leaves owner_user_id unchanged.
             Requirement: AR1

### AC2 — Claiming an unclaimed printer with a valid, unused code succeeds

[HAPPY PATH] Claiming an unclaimed printer using a valid, unused claim code succeeds, marks the claim code as used, and associates the printer to the requesting user.
             Requirement: AC2
[BOUNDARY VALUE] Claiming an unclaimed printer just before claim_code.expires_at succeeds, but a call immediately after expiry raises InvalidClaimCodeError.
             Requirement: AR3
[INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is already True fails with InvalidClaimCodeError and does not change owner_user_id or status.
             Requirement: AR4

### AR1 — Rejection of already-claimed printers independent of user_id

[OWNERSHIP] For a printer already in CLAIMED status, claiming with a valid, unused claim code using any user_id (same as or different from owner_user_id) is rejected with InvalidClaimCodeError and leaves ownership unchanged.
             Requirement: AR1

### AR2 — Registration must not generate a new claim code for already-CLAIMED printers

[HAPPY PATH] Re-registering a printer in CLAIMED status does not issue a new claim_code and leaves any existing claim_code marked as used while still allowing other registration outputs (e.g., Cloud ID) per business rules.
             Requirement: AR2
[ROLLBACK] If register_printer() for a CLAIMED printer fails after attempting to manipulate claim_code data, rollback ensures no new claim_code remains usable and the existing owner_user_id is preserved.
             Requirement: AR5

### AR3 — Expired claim code rejection for unclaimed printers

[INVALID INPUT] Claiming an unclaimed printer with an expired claim code raises InvalidClaimCodeError and does not change printer status or ownership.
             Requirement: AR3
[BOUNDARY VALUE] Claiming with a claim code at the exact expiry instant is treated according to the defined comparison (e.g., <= vs <), ensuring consistent InvalidClaimCodeError behavior once current time passes expires_at.
             Requirement: AR3

### AR4 — Reused claim code rejection for unclaimed printers

[INVALID INPUT] Claiming an unclaimed printer with a claim code whose used flag is True raises InvalidClaimCodeError and prevents any update to owner_user_id or status.
             Requirement: AR4
[ROLLBACK] Any failure path when processing a reused claim code leaves claim_code.used unchanged and does not partially update printer ownership or status.
             Requirement: AR4

### AR5 — Registration rollback preserves ownership while removing transient claim data

[ROLLBACK] When register_printer() fails during re-registration of a CLAIMED printer, rollback preserves owner_user_id and CLAIMED status while ensuring any new claim_code generated during the attempt is invalidated or removed.
             Requirement: AR5
[BOUNDARY VALUE] Rollback behavior is verified for failures occurring at different stages of registration (e.g., after claim linkage but before Welcome Page printing) to ensure ownership is always preserved and no usable claim_code leaks.
             Requirement: AR5

## Coverage Summary

Total scenarios: 14

Happy path: 3 | Invalid input: 4 | Boundary: 3 | Auth: 0 | Ownership: 4 | Rollback: 3
