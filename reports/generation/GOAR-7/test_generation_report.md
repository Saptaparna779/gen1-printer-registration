# Test Generation Report — GOAR-7

## Summary

- Total test functions generated: 21 (including skip-stubs)
- Test cases skipped as UNTESTABLE: 0

## Skipped Test Cases

- None

## Generated Tests

- test_TC_GOAR_7_01_reregister_claimed_printer_preserves_existing_claim_code: Verifies that re-registering a claimed printer preserves its existing claim code and expiry while updating cloud identity.
- test_TC_GOAR_7_02_consecutive_reregistrations_of_claimed_printer_do_not_change_claim_code: Verifies that two consecutive re-registrations of the same claimed printer keep claim code and expiry unchanged.
- test_TC_GOAR_7_03_ownership_preserved_when_reregistering_claimed_printer: Confirms that ownership and claimed status remain unchanged after re-registering a claimed printer.
- test_TC_GOAR_7_04_first_time_registration_of_unclaimed_printer_issues_claim_code_and_welcome_page: Confirms that first-time registration of an unclaimed printer issues a claim code, sets REGISTERED status, and records welcome page history.
- test_TC_GOAR_7_05_reregistration_of_unclaimed_printer_continues_to_issue_claim_code: Ensures re-registration of an unclaimed printer issues a new claim code while keeping status REGISTERED.
- test_TC_GOAR_7_06_consecutive_reregistrations_of_unclaimed_printer_generate_distinct_claim_codes: Ensures three registrations for an unclaimed printer produce three distinct claim codes.
- test_TC_GOAR_7_07_reregister_claimed_printer_does_not_change_claim_code_ttl_or_used_flag: Confirms that re-registering a claimed printer does not change its claim code expiry and preserves claimed ownership.
- test_TC_GOAR_7_08_reregister_claimed_printer_close_to_expiry_does_not_extend_ttl: Confirms that re-registering a claimed printer near claim-code expiry does not extend the expiry time.
- test_TC_GOAR_7_09_claim_code_remains_single_use_after_claiming_and_reregistering_claimed_printer: Verifies that a claim code remains single-use even after re-registering a claimed printer and ownership stays with the original user.
- test_TC_GOAR_7_10_failed_registration_for_unclaimed_printer_invalidates_claim_code: Verifies that a failed registration returns 422 and that only the subsequent successful registration’s claim code can be used to claim.
- test_TC_GOAR_7_11_new_claim_code_issued_after_failed_registration: Confirms that after a failed registration, a new claim code from a later successful registration can be used to claim the printer.
- test_TC_GOAR_7_12_rollback_removes_claim_code_when_failure_occurs_before_welcome_page: Confirms that a registration failure before welcome page printing results in 422 and any attempted claim using an arbitrary code is rejected.
- test_TC_GOAR_7_13_multiple_successful_registrations_for_unclaimed_printer_produce_unique_claim_codes: Confirms that two successful registrations for an unclaimed printer produce distinct claim codes and record successful welcome page history.
- test_TC_GOAR_7_14_three_registrations_for_unclaimed_printer_yield_pairwise_distinct_claim_codes: Confirms that three registrations for an unclaimed printer yield pairwise-distinct claim codes matching the required pattern.
- test_TC_GOAR_7_15_reusing_old_claim_code_for_unclaimed_printer_is_rejected: Verifies that reusing an old claim code after a newer code has been issued is rejected, while the latest code can successfully claim.
- test_TC_GOAR_7_16_claim_with_rolled_back_claim_code_is_rejected: Verifies that attempting to claim with a claim code from a failed, rolled-back registration is rejected.
- test_TC_GOAR_7_17_printer_cannot_be_claimed_by_any_rolled_back_claim_code_after_rollback: Confirms that after rollback, claim attempts using arbitrary codes are rejected with "Claim code not recognized".
- test_TC_GOAR_7_18_rolled_back_claim_code_cannot_be_used_immediately_or_later: Confirms that claim attempts using an arbitrary rolled-back code are rejected both immediately and after a delay.
- test_TC_GOAR_7_19_multiple_claim_codes_for_unclaimed_printer_allow_only_first_claim: Verifies that when multiple claim codes exist for an unclaimed printer, only the first successful claim transitions it to CLAIMED.
- test_TC_GOAR_7_20_ownership_unchanged_when_attempting_second_claim_with_different_claim_code: Confirms that ownership remains with the first claimer and the second claim attempt with another code is rejected.
- test_TC_GOAR_7_21_concurrent_claim_attempts_with_two_claim_codes_yield_at_most_one_successful_claim: Verifies that of two near-concurrent claim attempts with different claim codes, only one succeeds and the other is rejected as already claimed.

## Assumptions

- No test cases were marked UNTESTABLE in reports/testcases/GOAR-7_test_cases.md, so all 21 scenarios were automated as full tests.
- Time-based boundary conditions ("close to expiry") are asserted via equality of the claim_code_expires_at field rather than explicit clock control.
- Rolled-back claim code values are not exposed via the API; invalid claim attempts are exercised using synthetic codes like "INVALID10", "INVALID12", "INVALID16", "INVALID17", and "INVALID18" to assert rejection behavior.
- Exact error messages for InvalidClaimCodeError and rollback follow the current implementation in app/registration.py and app/main.py; any future changes to these messages may require test updates.
