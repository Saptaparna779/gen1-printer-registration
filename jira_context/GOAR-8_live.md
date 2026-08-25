# GOAR-8: claim_printer() does not check if the target printer is already claimed

**Type:** Bug  
**Priority:** Highest  
**Status:** Ready for QA  

## Description
claim_printer() only checks whether the claim_code itself has already been
used -- it never checks whether the target printer's status is already
CLAIMED by a different owner. Combined with GOAR-7, this is the concrete
exploit path for hijacking an already-owned printer.
Steps to Reproduce:
Register and claim a printer with user_id="user-abc".
Obtain any valid, unused claim code associated with that printer_id
(e.g. via GOAR-7's regeneration bug).
Call claim_printer() with that code and a different user_id.
Actual: the claim succeeds, overwriting owner_user_id.
Expected: claiming should be rejected if the printer is already
CLAIMED.
Acceptance Criteria:
claim_printer() raises InvalidClaimCodeError if the target printer's
status is already CLAIMED.
Claiming an unclaimed printer with a valid, unused code still succeeds
(do not regress).
Impact: Critical -- defense-in-depth gap enabling printer takeover.

## Comments
- **Saptaparna Dasgupta:** QA prep is ready. Pull the latest changes, open VS Code, and run the Copilot Agent validation for this ticket (see reports/GOAR-8_diff.txt and jira_context/GOAR-8_live.md).
- **Saptaparna Dasgupta:** # Validation Report: GOAR-8
## Files Investigated
- `jira_context/GOAR-8_live.md` — ticket summary, description, and acceptance criteria.
- `docs/business_rules.md` — business rules around claiming, ownership, and no silent ownership overwrite.
- `docs/confidence_rubric.md` — scoring rubric used for validation.
- `app/registration.py` — core claim handling logic, including `claim_printer()`.
- `app/models.py` — `PrinterStatus` enum and ownership state used by `claim_printer()`.
- `app/store.py` — in-memory printer lookup and iteration for claim resolution.
- `tests/test_registration.py` — existing regression coverage for claim success and already-claimed rejection.
## Acceptance Criteria Check
1. `claim_printer()` raises `InvalidClaimCodeError` if the target printer's status is already `CLAIMED`.
   - Verified in `app/registration.py`: `claim_printer()` explicitly checks `if target.status == PrinterStatus.CLAIMED:` and raises `InvalidClaimCodeError("Printer is already claimed")`.
   - This satisfies the ticket's required rejection behaviour.
2. Claiming an unclaimed printer with a valid, unused code still succeeds (do not regress).
   - Verified in `app/registration.py`: when a target printer is not already claimed, the method validates the claim code and then sets `owner_user_id`, `status = PrinterStatus.CLAIMED`, and saves the printer.
   - Existing test `test_claim_printer_success()` confirms this happy-path behaviour.
## Root Cause Assessment
- The root cause described by the ticket is missing ownership-state validation in `claim_printer()`.
- The current code already implements the proper guard at the decision point, so the root cause is addressed in the active codebase rather than only as a symptom fix.
## Regression Risk
- Regression risk is low in the current code, because the change is isolated to `claim_printer()` and the relevant behaviour is supported by existing tests.
- There is no indication from the code read that the claim path has been altered outside the guard logic.
## Confidence Score
Score: 100/100
Justification: The current implementation satisfies both acceptance criteria. The fix is present at the root-cause location in `app/registration.py`, and existing test coverage already covers the claimed-printer rejection behaviour.
## Path to 100/100
- No gaps were identified in the ticket's specific acceptance criteria for GOAR-8.
- The current code already includes the required `CLAIMED` rejection and preserves valid claims on unclaimed printers.
- **Saptaparna Dasgupta:** # Validation Report: GOAR-8
## Acceptance Criteria Check
1. Likely met, but not directly confirmed from the diff provided. The diff shown only modifies `register_printer()`, not `claim_printer()` — the function AC #1 concerns. Confirmed only indirectly, via TC-GOAR-8-01's passing execution.
2. Met. TC-GOAR-8-02 confirms a valid, unused claim code on an unclaimed printer still succeeds — no regression.
3. Met, and directly supported by the diff. Preventing `register_printer()` from generating a new claim code when `printer.status == CLAIMED` closes a specific path that could otherwise let a re-registration silently issue a fresh, valid code for an already-owned printer. TC-GOAR-8-03 confirms ownership is preserved.
4. Met. TC-GOAR-8-04 confirms a valid, unused code is still rejected for an already-claimed printer.
5. Met. TC-GOAR-8-05 confirms rejection is identical for both the original owner and a different user.
## Test Coverage Cross-Check
- AC #1 → TC-GOAR-8-01 → PASSED (per reports/GOAR-8_test_results.txt)
- AC #2 → TC-GOAR-8-02 → PASSED
- AC #3 → TC-GOAR-8-03 → PASSED
- AC #4 → TC-GOAR-8-04 → PASSED
- AC #5 → TC-GOAR-8-05 → PASSED
All 5 in-scope AC items have a corresponding test case, and all 5 test cases passed. No coverage gaps.
## Test Execution Evidence
`reports/GOAR-8_test_results.txt` shows: `5 passed, 46 warnings in 0.15s`. All five named tests (`test_TC_GOAR_8_01` through `test_TC_GOAR_8_05`) are individually listed as PASSED. This is real, executed evidence, not inferred from test source code.
## Root Cause Assessment
The visible diff addresses a genuine root-cause path: it stops `register_printer()` from reissuing a claim code when a printer is already `CLAIMED`, which is exactly the kind of defense-in-depth fix the ticket describes (a re-registration side door that could otherwise hand an attacker a fresh, valid claim code for an owned printer). This is not a symptom-level patch — it changes the general rule for all re-registrations of claimed printers, not one hardcoded case.
That said, this diff alone doesn't show the primary rejection guard in `claim_printer()` (AC #1). Either that guard already existed before this ticket and this diff is a *secondary* hardening measure, or the diff I reviewed is incomplete. I can't tell which from what's in front of me.
## Regression Risk
Low. The change is a single conditional guard scoped to claim-code generation during re-registration; it doesn't touch unrelated registration, deregistration, or claiming logic as shown.
## Confidence Score
Score: 90/100
Justification: All 5 AC items pass with real, executed test evidence and no coverage gaps — but the diff provided doesn't let me directly confirm AC #1's core mechanism (`claim_printer()`'s rejection logic), so I'm relying on test results rather than code inspection for that one item.
## Path to 100/100
- Provide the diff or current source for `claim_printer()` so AC #1's rejection logic can be verified directly, not just inferred from test outcomes.
- Once confirmed, no further gaps are expected — all other criteria are both tested and directly traceable to a visible code change.
- **Saptaparna Dasgupta:** # Validation Report: GOAR-8
## Acceptance Criteria Check
1. Likely met, but not directly confirmed from the diff provided. The diff shown only modifies `register_printer()`, not `claim_printer()` — the function AC #1 concerns. Confirmed only indirectly, via TC-GOAR-8-01's passing execution.
2. Met. TC-GOAR-8-02 confirms a valid, unused claim code on an unclaimed printer still succeeds — no regression.
3. Met, and directly supported by the diff. Preventing `register_printer()` from generating a new claim code when `printer.status == CLAIMED` closes a specific path that could otherwise let a re-registration silently issue a fresh, valid code for an already-owned printer. TC-GOAR-8-03 confirms ownership is preserved.
4. Met. TC-GOAR-8-04 confirms a valid, unused code is still rejected for an already-claimed printer.
5. Met. TC-GOAR-8-05 confirms rejection is identical for both the original owner and a different user.
## Test Coverage Cross-Check
- AC #1 → TC-GOAR-8-01 → PASSED (per reports/GOAR-8_test_results.txt)
- AC #2 → TC-GOAR-8-02 → PASSED
- AC #3 → TC-GOAR-8-03 → PASSED
- AC #4 → TC-GOAR-8-04 → PASSED
- AC #5 → TC-GOAR-8-05 → PASSED
All 5 in-scope AC items have a corresponding test case, and all 5 test cases passed. No coverage gaps.
## Test Execution Evidence
`reports/GOAR-8_test_results.txt` shows: `5 passed, 46 warnings in 0.15s`. All five named tests (`test_TC_GOAR_8_01` through `test_TC_GOAR_8_05`) are individually listed as PASSED. This is real, executed evidence, not inferred from test source code.
## Root Cause Assessment
The visible diff addresses a genuine root-cause path: it stops `register_printer()` from reissuing a claim code when a printer is already `CLAIMED`, which is exactly the kind of defense-in-depth fix the ticket describes (a re-registration side door that could otherwise hand an attacker a fresh, valid claim code for an owned printer). This is not a symptom-level patch — it changes the general rule for all re-registrations of claimed printers, not one hardcoded case.
That said, this diff alone doesn't show the primary rejection guard in `claim_printer()` (AC #1). Either that guard already existed before this ticket and this diff is a *secondary* hardening measure, or the diff I reviewed is incomplete. I can't tell which from what's in front of me.
## Regression Risk
Low. The change is a single conditional guard scoped to claim-code generation during re-registration; it doesn't touch unrelated registration, deregistration, or claiming logic as shown.
## Confidence Score
Score: 90/100
Justification: All 5 AC items pass with real, executed test evidence and no coverage gaps — but the diff provided doesn't let me directly confirm AC #1's core mechanism (`claim_printer()`'s rejection logic), so I'm relying on test results rather than code inspection for that one item.
## Path to 100/100
- Provide the diff or current source for `claim_printer()` so AC #1's rejection logic can be verified directly, not just inferred from test outcomes.
- Once confirmed, no further gaps are expected — all other criteria are both tested and directly traceable to a visible code change.
- **Saptaparna Dasgupta:** Validation Report: GOAR-8
Acceptance Criteria Check
1. Likely met, but not directly confirmed from the diff provided. The diff shown only modifies 
register_printer()
, not 
claim_printer()
 — the function AC #1 concerns. Confirmed only indirectly, via TC-GOAR-8-01's passing execution.
2. Met. TC-GOAR-8-02 confirms a valid, unused claim code on an unclaimed printer still succeeds — no regression.
3. Met, and directly supported by the diff. Preventing 
register_printer()
 from generating a new claim code when 
printer.status == CLAIMED
 closes a specific path that could otherwise let a re-registration silently issue a fresh, valid code for an already-owned printer. TC-GOAR-8-03 confirms ownership is preserved.
4. Met. TC-GOAR-8-04 confirms a valid, unused code is still rejected for an already-claimed printer.
5. Met. TC-GOAR-8-05 confirms rejection is identical for both the original owner and a different user.
Test Coverage Cross-Check
AC #1 → TC-GOAR-8-01 → PASSED (per reports/GOAR-8_test_results.txt)
AC #2 → TC-GOAR-8-02 → PASSED
AC #3 → TC-GOAR-8-03 → PASSED
AC #4 → TC-GOAR-8-04 → PASSED
AC #5 → TC-GOAR-8-05 → PASSED
All 5 in-scope AC items have a corresponding test case, and all 5 test cases passed. No coverage gaps.
Test Execution Evidence
reports/GOAR-8_test_results.txt
 shows: 
5 passed, 46 warnings in 0.15s
. All five named tests (
test_TC_GOAR_8_01
 through 
test_TC_GOAR_8_05
) are individually listed as PASSED. This is real, executed evidence, not inferred from test source code.
Root Cause Assessment
The visible diff addresses a genuine root-cause path: it stops 
register_printer()
 from reissuing a claim code when a printer is already 
CLAIMED
, which is exactly the kind of defense-in-depth fix the ticket describes (a re-registration side door that could otherwise hand an attacker a fresh, valid claim code for an owned printer). This is not a symptom-level patch — it changes the general rule for all re-registrations of claimed printers, not one hardcoded case.
That said, this diff alone doesn't show the primary rejection guard in 
claim_printer()
 (AC #1). Either that guard already existed before this ticket and this diff is a *secondary* hardening measure, or the diff I reviewed is incomplete. I can't tell which from what's in front of me.
Regression Risk
Low. The change is a single conditional guard scoped to claim-code generation during re-registration; it doesn't touch unrelated registration, deregistration, or claiming logic as shown.
Confidence Score
Score: 90/100
Justification: All 5 AC items pass with real, executed test evidence and no coverage gaps — but the diff provided doesn't let me directly confirm AC #1's core mechanism (
claim_printer()
's rejection logic), so I'm relying on test results rather than code inspection for that one item.
Path to 100/100
Provide the diff or current source for 
claim_printer()
 so AC #1's rejection logic can be verified directly, not just inferred from test outcomes.
Once confirmed, no further gaps are expected — all other criteria are both tested and directly traceable to a visible code change.
- **Saptaparna Dasgupta:** Validation Report: GOAR-8
Acceptance Criteria Check
1. Likely met, but not directly confirmed from the diff provided. The diff shown only modifies 
register_printer()
, not 
claim_printer()
 — the function AC #1 concerns. Confirmed only indirectly, via TC-GOAR-8-01's passing execution.
2. Met. TC-GOAR-8-02 confirms a valid, unused claim code on an unclaimed printer still succeeds — no regression.
3. Met, and directly supported by the diff. Preventing 
register_printer()
 from generating a new claim code when 
printer.status == CLAIMED
 closes a specific path that could otherwise let a re-registration silently issue a fresh, valid code for an already-owned printer. TC-GOAR-8-03 confirms ownership is preserved.
4. Met. TC-GOAR-8-04 confirms a valid, unused code is still rejected for an already-claimed printer.
5. Met. TC-GOAR-8-05 confirms rejection is identical for both the original owner and a different user.
Test Coverage Cross-Check
AC #1 → TC-GOAR-8-01 → PASSED (per reports/GOAR-8_test_results.txt)
AC #2 → TC-GOAR-8-02 → PASSED
AC #3 → TC-GOAR-8-03 → PASSED
AC #4 → TC-GOAR-8-04 → PASSED
AC #5 → TC-GOAR-8-05 → PASSED
All 5 in-scope AC items have a corresponding test case, and all 5 test cases passed. No coverage gaps.
Test Execution Evidence
reports/GOAR-8_test_results.txt
 shows: 
5 passed, 46 warnings in 0.15s
. All five named tests (
test_TC_GOAR_8_01
 through 
test_TC_GOAR_8_05
) are individually listed as PASSED. This is real, executed evidence, not inferred from test source code.
Root Cause Assessment
The visible diff addresses a genuine root-cause path: it stops 
register_printer()
 from reissuing a claim code when a printer is already 
CLAIMED
, which is exactly the kind of defense-in-depth fix the ticket describes (a re-registration side door that could otherwise hand an attacker a fresh, valid claim code for an owned printer). This is not a symptom-level patch — it changes the general rule for all re-registrations of claimed printers, not one hardcoded case.
That said, this diff alone doesn't show the primary rejection guard in 
claim_printer()
 (AC #1). Either that guard already existed before this ticket and this diff is a *secondary* hardening measure, or the diff I reviewed is incomplete. I can't tell which from what's in front of me.
Regression Risk
Low. The change is a single conditional guard scoped to claim-code generation during re-registration; it doesn't touch unrelated registration, deregistration, or claiming logic as shown.
Confidence Score
Score: 90/100
Justification: All 5 AC items pass with real, executed test evidence and no coverage gaps — but the diff provided doesn't let me directly confirm AC #1's core mechanism (
claim_printer()
's rejection logic), so I'm relying on test results rather than code inspection for that one item.
Path to 100/100
Provide the diff or current source for 
claim_printer()
 so AC #1's rejection logic can be verified directly, not just inferred from test outcomes.
Once confirmed, no further gaps are expected — all other criteria are both tested and directly traceable to a visible code change.
