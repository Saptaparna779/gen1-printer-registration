# Test Generation Report — GOAR-4

## Summary

- Total test functions generated: 22 (including skip-stubs)
- Test cases skipped as UNTESTABLE: 9

## Skipped Test Cases

- TC-GOAR-4-03: UNTESTABLE: capability records are not exposed via any HTTP endpoint; existence after successful registration must be validated below the API layer
- TC-GOAR-4-04: UNTESTABLE: capability records are not exposed via any HTTP endpoint; deletion after rollback must be validated below the API layer
- TC-GOAR-4-05: UNTESTABLE: there is no serial-number lookup endpoint; serial index behavior must be inferred indirectly or validated via store-level tests
- TC-GOAR-4-10: UNTESTABLE: internal idempotent rollback behavior cannot be exercised via HTTP beyond a single 422 response
- TC-GOAR-4-11: UNTESTABLE: a second internal rollback call after records are deleted is not observable via the HTTP API
- TC-GOAR-4-12: UNTESTABLE: capability scoping per-printer_id is not observable via current HTTP endpoints
- TC-GOAR-4-15: UNTESTABLE: direct serial-index lookup is not available via HTTP; residual serial index can only be inferred indirectly
- TC-GOAR-4-20: UNTESTABLE: there are no capability or device list endpoints; capability records for failed registrations cannot be observed via HTTP
- TC-GOAR-4-21: UNTESTABLE: timing of capability deletion relative to external queries is not observable without additional telemetry or endpoints

## Generated Tests

- test_TC_GOAR_4_01_successful_registration_persists_printer_record: Verifies that a successful registration with Welcome Page printing creates and persists a printer record retrievable via GET /printers/{printer_id}.
- test_TC_GOAR_4_02_failed_registration_removes_printer_record: Verifies that a registration failing at the Welcome Page returns 422 and that GET /printers/{printer_id} subsequently returns 404, confirming rollback of the printer record.
- test_TC_GOAR_4_03_successful_registration_leaves_capabilities_present: Stubbed as skipped because capability records are not visible via HTTP and must be validated with store-level or unit tests.
- test_TC_GOAR_4_04_failed_registration_removes_capabilities: Stubbed as skipped because capability deletion is not observable via HTTP and requires direct store access or additional endpoints.
- test_TC_GOAR_4_05_successful_registration_allows_serial_lookup: Stubbed as skipped since there is no serial-based lookup endpoint; serial index behavior cannot be asserted directly.
- test_TC_GOAR_4_06_failed_registration_frees_serial_for_reuse: Ensures that a failed registration using simulate_welcome_page_failure=True returns 422 and a subsequent registration for the same serial succeeds with status REGISTERED.
- test_TC_GOAR_4_07_successful_registrations_unaffected_by_rollback_changes: Confirms that a standard successful registration remains correct and unaffected even when rollback paths exist in the codebase.
- test_TC_GOAR_4_08_missing_authorization_header_rejected: Validates that omitting the Authorization header yields a 422 validation error with type value_error.missing and does not progress into registration logic.
- test_TC_GOAR_4_09_invalid_token_rejected_with_401: Validates that providing the literal "Bearer invalid_token" results in a 401 response with detail "Invalid or expired token".
- test_TC_GOAR_4_10_idempotent_rollback_leaves_no_records_after_multiple_calls: Stubbed as skipped because multiple internal rollback invocations are not observable via the HTTP API.
- test_TC_GOAR_4_11_second_rollback_call_completes_without_errors: Stubbed as skipped; the second rollback boundary behavior is internal-only and cannot be asserted at API level.
- test_TC_GOAR_4_12_rollback_deletes_only_failing_printers_capabilities: Stubbed as skipped due to lack of capability inspection endpoints; per-printer_id capability scoping is not directly testable via HTTP.
- test_TC_GOAR_4_13_rollback_does_not_delete_other_printers_ownership_state: Demonstrates that a failed registration and rollback for one serial does not alter the CLAIMED status or owner_user_id of an already-claimed printer.
- test_TC_GOAR_4_14_fresh_registration_after_rollback_behaves_like_first_time: Verifies that after a failed registration and rollback, a subsequent registration for the same serial completes successfully with a new cloud_id and REGISTERED status.
- test_TC_GOAR_4_15_after_rollback_serial_lookup_shows_no_residual_mapping: Stubbed as skipped because there is no direct serial-index lookup API; residual mappings can only be inferred indirectly.
- test_TC_GOAR_4_16_rollback_does_not_alter_single_claimed_printer: Confirms that rollback triggered by a failed registration for a different serial leaves an existing claimed printer's status and owner_user_id unchanged.
- test_TC_GOAR_4_17_rollback_does_not_modify_multiple_claimed_printers: Shows that rollback for a failed registration does not modify the CLAIMED status or ownership of any of several already-claimed printers.
- test_TC_GOAR_4_18_successful_registration_does_not_invoke_rollback: Validates normal successful registration behavior with simulate_welcome_page_failure=False and confirms REGISTERED status without inferring rollback.
- test_TC_GOAR_4_19_rollback_failure_does_not_affect_later_successful_registration: Ensures that a failed registration with rollback followed by a second registration for the same serial yields a successful REGISTERED printer.
- test_TC_GOAR_4_20_capabilities_for_failed_registration_not_externally_visible: Stubbed as skipped because downstream capability or device list queries are not available in app/main.py.
- test_TC_GOAR_4_21_capability_records_deleted_before_external_observation: Stubbed as skipped; timing of capability deletion versus external observation cannot be tested via the current API.
- test_TC_GOAR_4_22_model_family_boundary_with_welcome_page_failure: Exercises a Welcome Page failure for the boundary model_number "HP-LJ-001" and asserts a 422 response with a failure detail string.

## Assumptions

- For TC-GOAR-4-02 and related rollback tests, the expected detail string in reports/testcases/GOAR-4_test_cases.md was adjusted from a literal printer_id value to a prefix assertion ("Welcome page failed to print for printer_id=") and dynamic extraction of printer_id from the response, to match the actual RegistrationError behavior implemented in app/registration.py.
- All UNTESTABLE scenarios were implemented as pytest skip-stubs with reasons copied and summarized from the Notes field of the test-case definitions, preserving traceability without inventing store or capability access.
- Serial index behavior (freeing serials for reuse) is inferred via repeated registration calls rather than direct store or index inspection, in line with the constraint that tests must use only the HTTP API.
- No model-family status override was required for TC-GOAR-4-22 because the expected status is 422 due to Welcome Page failure, not due to model-family comparison; _model_family("HP-LJ-001") is respected but does not change the failure semantics in these tests.
- Authentication behavior for missing and invalid tokens is validated strictly through FastAPI's dependency system and verify_token implementation, with no assumptions about underlying token storage or expiry beyond the explicit "Invalid or expired token" detail string.
