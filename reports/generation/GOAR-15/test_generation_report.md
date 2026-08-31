# Test Generation Report — GOAR-15

## Summary

- Total test functions generated: 22 (including skip-stubs)
- Test cases skipped as UNTESTABLE: 1

## Skipped Test Cases

- TC-GOAR-15-11: UNTESTABLE: Current implementation normalizes only strip().upper(); testing a normalization collision would require assumptions about additional normalization behavior not present in app.registration._model_family.

## Generated Tests

- test_TC_GOAR_15_01_same_family_model_change_accepted_with_full_registration_outputs: Verifies same-family model change on re-registration succeeds, regenerates Cloud identity, and records GOAR-15 history and structured WARNING log.
- test_TC_GOAR_15_02_case_whitespace_only_model_difference_treated_as_unchanged: Ensures case/whitespace-only model_number differences are treated as unchanged, emitting no GOAR-15 warning or history entry.
- test_TC_GOAR_15_03_different_family_model_change_rejected_with_unchanged_identity_and_capabilities: Confirms different-family model change is rejected with model-family mismatch error and leaves identity fields unchanged apart from GOAR-15 history/logging.
- test_TC_GOAR_15_04_different_family_reregistration_rejected_with_unchanged_state: Validates that different-family re-registration is rejected with RegistrationError translated to 422 and does not alter stored identity.
- test_TC_GOAR_15_05_same_family_last_segment_change_accepted_with_warning: Checks that same-family model changes differing only in the last segment are accepted while emitting GOAR-15 warning and history entries.
- test_TC_GOAR_15_06_rejected_different_family_reregistration_leaves_identity_intact: Ensures rejected different-family re-registration leaves Cloud ID, printer email ID, XMPP node, and status unchanged.
- test_TC_GOAR_15_07_reregistration_with_identical_identity_regenerates_cloud_id_and_email: Verifies re-registration with identical identity regenerates Cloud ID and printer email ID while keeping printer_id constant.
- test_TC_GOAR_15_08_reregistration_of_claimed_printer_with_firmware_update_preserves_ownership: Confirms re-registration of a claimed printer with firmware update regenerates identities but preserves ownership and CLAIMED status.
- test_TC_GOAR_15_09_welcome_page_failure_during_reregistration_rolls_back_completely: Asserts welcome-page failure during re-registration triggers rollback, removing the printer record and returning 404 on subsequent lookup.
- test_TC_GOAR_15_10_normalized_model_equality_avoids_goar15_warning_and_history: Ensures normalized-equal model_numbers avoid GOAR-15 warnings and history entries while still regenerating Cloud identity.
- test_TC_GOAR_15_11_normalization_collision_treated_consistently_as_unchanged: Skip-stub documenting an untestable normalization-collision scenario that would require assumptions beyond strip().upper().
- test_TC_GOAR_15_12_cloud_id_generation_only_on_accepted_model_family_checks: Verifies that rejected model-family mismatches do not persist a new Cloud ID, leaving the original Cloud ID unchanged.
- test_TC_GOAR_15_13_accepted_reregistration_never_reuses_old_cloud_id: Confirms successful re-registrations always persist a new Cloud ID distinct from previous values.
- test_TC_GOAR_15_14_structured_warning_log_with_serial_old_model_new_model: Checks that GOAR-15 WARNING logs carry structured fields serial_number, old_model, and new_model for same-family model changes.
- test_TC_GOAR_15_15_multiple_same_family_model_changes_emit_structured_warning_logs: Ensures multiple same-family model changes each emit structured WARNING logs with consistent field names and values.
- test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership: Verifies re-registration of a CLAIMED printer with unchanged model preserves owner_user_id and CLAIMED status while regenerating identities.
- test_TC_GOAR_15_17_reregistration_of_claimed_printer_with_same_family_model_change_preserves_ownership: Confirms same-family model change on a CLAIMED printer logs GOAR-15 warning and maintains ownership and CLAIMED status.
- test_TC_GOAR_15_18_reregistration_of_claimed_printer_with_invalid_token_does_not_change_ownership: Validates that re-registration of a CLAIMED printer with an invalid token is rejected with 401 and leaves ownership unchanged.
- test_TC_GOAR_15_19_missing_authorization_header_rejected_on_registration: Ensures missing Authorization header on registration yields 422 header validation errors and does not create a printer.
- test_TC_GOAR_15_20_invalid_token_rejected_on_registration_with_no_side_effects: Confirms invalid-token registration requests are rejected with 401 and perform no registration side effects.
- test_TC_GOAR_15_21_missing_authorization_header_rejected_on_claim_and_lookup: Verifies missing Authorization header on claim and lookup endpoints yields 422 and leaves printer ownership and status unchanged.
- test_TC_GOAR_15_22_invalid_token_rejected_on_claim_lookup_and_deregister: Ensures claim, lookup, and deregister requests with invalid token are rejected with 401 and do not change printer state.

## Assumptions

- TC-GOAR-15-11 is marked UNTESTABLE because app.registration._model_family applies only strip().upper(), and there is no internal-space normalization; constructing a true normalization collision would require assumptions about additional normalization behavior not present in the implementation.
- For all model-family mismatch cases (TC-GOAR-15-03, 04, 06, 12), the expected HTTP 422 detail string is taken directly from app.registration.register_printer, which raises RegistrationError with a fixed message that app.main translates into HTTP 422. The tests assert this exact message.
- Cloud ID, printer email ID, and claim code patterns are enforced via regexes derived from existing GOAR-3 tests and app.registration helper implementations, ensuring no placeholder values or vague assertions are used.
- Auth behavior for missing and invalid tokens (422 for missing Authorization header, 401 with detail "Invalid or expired token" for invalid tokens) is derived from app.main and app.auth.verify_token behavior as exercised by the tests; no additional auth flows are assumed.
- Rollback behavior for welcome-page failures (TC-GOAR-15-09) is treated as identical to GOAR-3: a failed welcome-page print results in deletion of the printer and serial index, verified via subsequent 404 on GET /printers/{printer_id}.
