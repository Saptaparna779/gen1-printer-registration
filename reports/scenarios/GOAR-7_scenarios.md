# Scenario Coverage — GOAR-7

## Scenarios by Requirement

### AC1 — Re-registering an already-CLAIMED printer does not generate a new claim code

[HAPPY PATH] Re-register an already-CLAIMED printer and confirm no new claim code is generated and the existing claim code value is preserved.
             Requirement: AC1
[BOUNDARY VALUE] Perform two consecutive re-registrations of the same CLAIMED printer and confirm that the claim code remains unchanged across both calls.
                 Requirement: AC1
[OWNERSHIP] Re-register a CLAIMED printer and confirm that ownership-related fields (e.g., owner_user_id and CLAIMED status) remain unchanged when no new claim code is issued.
             Requirement: AC1

### AC2 — First-time registration and re-registration of an unclaimed printer continue to generate a claim code as before

[HAPPY PATH] First-time registration of an unclaimed printer generates a claim code and prints a Welcome Page as expected.
             Requirement: AC2
[HAPPY PATH] Re-register an unclaimed printer and confirm a claim code is generated and associated with the printer on each successful re-registration.
             Requirement: AC2
[BOUNDARY VALUE] Re-register an unclaimed printer twice in succession and confirm each successful call generates a new, distinct claim code.
                 Requirement: AC2

### AR1 — Existing claim code for a CLAIMED printer must not have its TTL or single-use flags silently extended or reset during re-registration

[HAPPY PATH] Re-register a CLAIMED printer with a currently valid, unused claim code and confirm that the claim code’s expiry and used flags remain unchanged after re-registration.
             Requirement: AR1
[BOUNDARY VALUE] Re-register a CLAIMED printer whose claim code is close to expiry and confirm that re-registration does not extend the expiration time.
                 Requirement: AR1
[OWNERSHIP] After successfully claiming a printer and then re-registering it, confirm that the claim code still behaves as single-use (cannot be used again) and that ownership is not weakened.
             Requirement: AR1

### AR2 — Claim codes generated during failed registration/re-registration must not be usable and must be replaced on next successful registration

[ROLLBACK] Trigger a registration failure before Welcome Page printing for an unclaimed printer and confirm that any claim code generated during the failed attempt cannot be used to claim the printer afterwards.
           Requirement: AR2
[ROLLBACK] After a failed registration that invalidated a claim code, perform a subsequent successful registration and confirm a fresh claim code is generated and is the only usable one.
           Requirement: AR2
[BOUNDARY VALUE] Simulate a failure at the last step before Welcome Page printing and confirm that rollback still removes any claim code generated in that attempt.
                 Requirement: AR2

### AR3 — Each successful Welcome Page print for an unclaimed printer must generate a new claim code that has never been issued before for that printer

[HAPPY PATH] Perform two successful registrations (or re-registrations) for the same unclaimed printer and confirm each Welcome Page print uses a new, previously unseen claim code.
             Requirement: AR3
[BOUNDARY VALUE] Perform a third successful registration for the same unclaimed printer and confirm all three claim codes are distinct from each other and from any historical codes.
                 Requirement: AR3
[INVALID INPUT] Attempt to re-use an old claim code from a prior registration for an unclaimed printer and confirm it is rejected as invalid.
                Requirement: AR3

### AR4 — Claim attempts using claim codes from rolled-back registrations must be rejected

[HAPPY PATH] Attempt to claim a printer using a claim code originating from a registration that was rolled back and confirm the claim attempt is rejected.
             Requirement: AR4
[ROLLBACK] After rollback of a failed registration, confirm the printer cannot be claimed by any claim code that was generated during that failed attempt.
           Requirement: AR4
[BOUNDARY VALUE] Attempt to claim with a rolled-back claim code immediately after rollback and again after some time has passed, confirming both attempts are rejected.
                 Requirement: AR4

### AR5 — Multiple concurrent claim codes for the same printer must not allow more than one successful claim

[HAPPY PATH] Issue multiple claim codes for the same unclaimed printer via overlapping registration attempts and confirm that only the first successful claim transitions the printer to CLAIMED.
             Requirement: AR5
[OWNERSHIP] After the printer becomes CLAIMED via one claim code, attempt to claim it using another valid-looking claim code and confirm ownership does not change and the second claim is rejected.
             Requirement: AR5
[BOUNDARY VALUE] Attempt to claim the printer simultaneously with two different claim codes and confirm that at most one claim succeeds and subsequent claims are rejected.
                 Requirement: AR5

## Coverage Summary

Total scenarios: 21

Happy path: 7 | Invalid input: 1 | Boundary: 7 | Auth: 0 | Ownership: 3 | Rollback: 3
