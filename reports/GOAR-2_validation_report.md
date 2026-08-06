# Validation Report: GOAR-2
## Acceptance Criteria Check
- Claim codes expire exactly 15 minutes after created_at: Met. The implementation sets `CLAIM_CODE_TTL_MINUTES = 15` and `_generate_claim_code()` uses `now + timedelta(minutes=CLAIM_CODE_TTL_MINUTES)` to populate `expires_at`.
- Attempting to claim a printer with an expired claim code returns a clear error (HTTP 400) and does NOT change printer ownership or status: Met. `registration.claim_printer()` now raises `InvalidClaimCodeError("Claim code has expired")` and `app/main.py` maps that exception to HTTP 400. The new unit test `test_claim_printer_rejects_expired_claim_code()` verifies the expired code is rejected and the printer status is not set to `CLAIMED`.
- Attempting to claim with a valid, unexpired code still works as before: Met. The existing `test_claim_printer_success()` covers the successful claim path and no changes were made to that flow.
- Attempting to reuse an already-used claim code is still rejected: Met. The `target.claim_code.used` check remains and continues to raise `InvalidClaimCodeError` for reused codes.
## Root Cause Assessment
The reported root cause was that `claim_printer()` never validated `claim_code.expires_at` before accepting a claim. The diff fixes that root cause by adding an expiry check (`if datetime.utcnow() > target.claim_code.expires_at: raise InvalidClaimCodeError("Claim code has expired")`) in `app/registration.py` and by adding a unit test that verifies expired codes are rejected.
## Regression Risk
Low. The change is localized to `registration.claim_printer()` and adds a single validation guard. The main behavioral difference is ordering: the expiry check now runs before the "already used" check, so an expired-and-used code will surface the "expired" error instead of "already been used". This is a minor semantic change (not a functional regression) but could affect clients or error-message expectations.
## Confidence Score
Score: 90/100
Justification: The diff addresses the root cause, satisfies the ticket's acceptance criteria in code, and includes a unit test that verifies rejection of expired claim codes. Coverage gaps remain (see Path to 100/100) so I do not rate this 100.
## Path to 100/100
Specific actions to reach 100/100:
- Add a unit test `test_claim_code_ttl_is_15_minutes()` in `tests/test_registration.py` asserting: `claim_code.expires_at == claim_code.created_at + timedelta(minutes=15)` immediately after `register_printer(...)` returns. This verifies the TTL is exactly 15 minutes.
- Add an endpoint-level regression test `test_claim_printer_endpoint_returns_400_for_expired_claim_code()` that uses the FastAPI test client to POST `/printers/claim` with an expired code and asserts the response `status_code == 400` and the response `detail` contains "expired". This verifies the HTTP contract from `app/main.py`.
- (Optional) If API error semantics for reused-but-expired codes must be preserved as "already used", add a test documenting the desired behavior and reorder the checks in `claim_printer()` accordingly; otherwise document the changed semantics in release notes.
