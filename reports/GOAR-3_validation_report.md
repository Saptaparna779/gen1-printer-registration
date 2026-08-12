# Validation Report: GOAR-3

## Acceptance Criteria Check
1. Every call to register a printer — first-time or re-registration — generates a brand new Cloud ID: **met**. `app/registration.py:108` calls `printer.cloud_id = _generate_cloud_id()` unconditionally on every call to `register_printer()`, with no branch that reuses `existing.cloud_id`. Confirmed by direct read of the current file (not diff inference alone). TC-GOAR-3-01 passed.
2. Printer Email ID and Claim Code continue to be regenerated on re-registration (unaffected, do not regress): **met**, with a caveat. `printer_email_id` is unconditionally regenerated (`registration.py:110`). `claim_code` is regenerated only `if printer.status != PrinterStatus.CLAIMED` (`registration.py:112`) — this conditional predates this diff and was not introduced or altered by it. TC-GOAR-3-02 exercises this on a non-claimed printer and passed. The CLAIMED-printer case is not exercised against the literal AC2 wording (see Requirements Open Question 2, still unresolved by human sign-off) — see Path to 100/100.
3. Re-registering a `CLAIMED` printer still gets a new Cloud ID without changing `CLAIMED` status or `owner_user_id`: **met**. Cloud ID regeneration at line 108 runs regardless of status; status is only forced to `REGISTERED` `if printer.status != PrinterStatus.CLAIMED` (`registration.py:146`), so `CLAIMED` is preserved; `owner_user_id` is never touched in `register_printer()`. TC-GOAR-3-03 and TC-GOAR-3-04 passed.
4. Two consecutive re-registrations produce three distinct Cloud IDs overall (not just different-from-previous): **met**. Each call independently generates `CID-{uuid4().hex[:12]}`, so pairwise distinctness across all three holds (not just adjacent-pair distinctness). TC-GOAR-3-05 and TC-GOAR-3-06 (the specific `cloud_id_3 != cloud_id_1` boundary check) passed.
5. A failed/rolled-back re-registration's Cloud ID is not retained or reused; the next successful attempt gets a fresh one: **met**. `_rollback_registration()` (`registration.py:155-162`) deletes the printer record, serial index, and capabilities entirely on `WelcomePagePrintError`, so the failed attempt's `cloud_id` cannot be retained or observed. TC-GOAR-3-07 and TC-GOAR-3-08 passed.
6. Re-registration after deregistration generates a new Cloud ID, distinct from any prior one: **met**. `deregister_printer()` fully removes the printer record and serial index, so a subsequent registration follows the same fresh-generation path as item 1. TC-GOAR-3-09 passed.

No AC items are marked "[unconfirmed]" in `reports/requirements/GOAR-3_requirements.md`; all 6 were scored.

## Scenario Coverage Cross-Check
- AC #1 — Happy path: TC-GOAR-3-01 ✓. No gaps.
- AC #2 — Happy path: TC-GOAR-3-02 ✓. No gaps against the scenarios file. (Note: the scenarios file lists only "Happy path" for AC #2 — it does not specify a claimed-printer variant, so the untested CLAIMED-printer claim-code question noted above is not a scenario-checklist gap, but is a residual ambiguity from Requirements Open Question 2.)
- AC #3 — Happy path: TC-GOAR-3-03 ✓. Permission/ownership: TC-GOAR-3-04 ✓. No gaps.
- AC #4 — Happy path: TC-GOAR-3-05 ✓. Boundary: TC-GOAR-3-06 ✓. No gaps.
- AC #5 — Happy path: TC-GOAR-3-07 ✓. Negative: TC-GOAR-3-08 ✓. No gaps.
- AC #6 — Happy path: TC-GOAR-3-09 ✓. No gaps.

Every scenario type listed in `reports/scenarios/GOAR-3_scenarios.md` for every AC item has a corresponding test case. No scenario type is unaddressed.

## Test Coverage Cross-Check
| AC # | Test Case(s) | Result |
|---|---|---|
| 1 | TC-GOAR-3-01 | PASSED |
| 2 | TC-GOAR-3-02 | PASSED |
| 3 | TC-GOAR-3-03, TC-GOAR-3-04 | PASSED, PASSED |
| 4 | TC-GOAR-3-05, TC-GOAR-3-06 | PASSED, PASSED |
| 5 | TC-GOAR-3-07, TC-GOAR-3-08 | PASSED, PASSED |
| 6 | TC-GOAR-3-09 | PASSED |

No AC item is missing a test case, and no test case failed or was skipped.

## Test Execution Evidence
`reports/GOAR-3_test_results.txt` is present and shows a real pytest run (`tests/test_GOAR-3_generated.py`, 9 items collected):
- `test_TC_GOAR_3_01_reregistration_generates_new_cloud_id` — PASSED
- `test_TC_GOAR_3_02_reregistration_regenerates_email_and_claim_code` — PASSED
- `test_TC_GOAR_3_03_reregistration_of_claimed_printer_gets_new_cloud_id_keeps_claimed_status` — PASSED
- `test_TC_GOAR_3_04_reregistration_of_claimed_printer_preserves_owner` — PASSED
- `test_TC_GOAR_3_05_three_consecutive_registrations_produce_three_distinct_cloud_ids` — PASSED
- `test_TC_GOAR_3_06_second_reregistration_cloud_id_differs_from_very_first` — PASSED
- `test_TC_GOAR_3_07_recovery_after_failed_reregistration_gets_fresh_cloud_id` — PASSED
- `test_TC_GOAR_3_08_failed_reregistration_rolls_back_printer_record` — PASSED
- `test_TC_GOAR_3_09_reregistration_after_deregistration_generates_new_cloud_id` — PASSED

Final summary line: `9 passed, 128 warnings in 0.34s`. All warnings are unrelated `datetime.utcnow()` deprecation notices, not functional failures. This is real, ground-truth execution evidence, not inference from test source alone.

## Root Cause Assessment
The fix addresses the root cause, not just the reported symptom. `register_printer()` (`app/registration.py:73-152`) has a single unconditional Cloud ID assignment (`printer.cloud_id = _generate_cloud_id()`) that runs for every call — whether `existing` is `None` (first-time) or set (re-registration) — with no conditional path anywhere in the current file that reuses a prior `cloud_id`. This matches business rule 3/6 exactly ("re-registration always generates a new Cloud ID... regenerated on every re-registration") rather than special-casing the ticket's specific reported serial number (`SN-1234`) or the no-deregistration path only. The fix also correctly generalizes to the deregister-then-reregister case (rule 13 / AC #6) and the claimed-printer case (rule 11 / AC #3) without extra logic, because Cloud ID regeneration was decoupled from status entirely.

## Regression Risk
Low. The change is a single unconditional assignment plus a comment; it does not touch capability capture, XMPP assignment, welcome-page printing, claim handling, or the rollback path. `printer_email_id` and `claim_code` generation logic is untouched by this diff. The one pre-existing (not newly introduced) nuance worth flagging is that `claim_code` regeneration is skipped for already-`CLAIMED` printers (`registration.py:112`) — this is existing behavior, not a regression caused by this diff, and it plausibly exists to satisfy rule 11 (never overwrite an existing claim), but its correctness against AC2's literal wording is unconfirmed (Requirements Open Question 2, not resolved in the Human Sign-Off).

## Confidence Score
Score: 95/100
Justification: All 6 in-scope AC items are met, every scenario type in the scenario checklist has a passing test case, execution evidence shows 9/9 real pytest passes, and the diff fixes the general rule rather than the specific reported case — but the CLAIMED-printer interaction with claim-code regeneration (Requirements Open Question 2) is a real, unresolved ambiguity that no test case currently probes, so this stops short of a clean 100.

## Path to 100/100
1. Get an explicit human/product decision on Requirements Open Question 2 (`reports/requirements/GOAR-3_requirements.md`, line 33): should `claim_code` be regenerated on re-registration of an already-`CLAIMED` printer, or is skipping it (current behavior, `registration.py:112`) intentional per rule 11? This is currently unresolved by the Human Sign-Off note, which only addresses Open Question 1.
2. Once resolved, add a test case (and corresponding scenario-checklist entry for AC #2) that re-registers an already-`CLAIMED` printer and asserts the correct claim-code behavior per that decision — closing the one AC2 permutation the current scenario list doesn't require but the code's behavior implies.
3. No other gaps: all remaining AC items, scenario types, and test cases are fully covered and passing.
