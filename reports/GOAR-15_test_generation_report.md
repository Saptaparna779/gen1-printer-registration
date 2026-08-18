# Test Generation Report — GOAR-15

## Summary

- Total test functions generated: 25
- Test cases skipped (UNTESTABLE): 1

## Skipped Test Cases

- TC-GOAR-15-26: Summary-only entry, explicitly marked non-executable in Notes.

## Generated Tests

- test_TC_GOAR_15_01_same_family_model_change_accepted: Verifies that re-registering a printer with a same-family model change succeeds, regenerates identity fields, and logs a GOAR-15 model-change warning with structured fields.
- test_TC_GOAR_15_02_case_whitespace_only_model_difference_treated_as_unchanged: Verifies that a case/whitespace-only difference in model_number is treated as unchanged, with new identity values but no GOAR-15 model-change warning in history or logs.
- test_TC_GOAR_15_03_different_family_model_change_rejected_with_rollback: Confirms that re-registering with a different-family model is rejected with 422 and that printer identity fields remain unchanged except for a review history entry, with a warning log captured.
- test_TC_GOAR_15_04_different_family_reregistration_rejected_no_side_effects: Confirms that a clearly different-family re-registration is rejected, with printer Cloud ID, email, XMPP node, and status unchanged and only a review entry added to history.
- test_TC_GOAR_15_05_boundary_classification_heuristic_edge_HP_LJ_001: Validates that changing from HP-LJ-001 to HP-LJ-2055 is treated as a model-family mismatch, rejected, and leaves model_number and identity fields unchanged apart from the review log.
- test_TC_GOAR_15_06_rejected_different_family_has_no_partial_identity_side_effects: Ensures that a rejected different-family re-registration does not alter Cloud ID, email, XMPP node, or serial_number, focusing on side-effect rollback.
- test_TC_GOAR_15_07_identical_identity_fields_reregistration_succeeds_new_identity: Checks that re-registration with identical model and firmware regenerates Cloud ID, email, and XMPP, preserving REGISTERED status and adding new history entries.
- test_TC_GOAR_15_08_reregistration_with_updated_firmware_preserves_ownership: Verifies that re-registering a claimed printer with updated firmware regenerates identity while preserving claimed status and owner_user_id.
- test_TC_GOAR_15_09_non_goar_15_pre_welcome_page_failure_rolls_back_fully: Ensures that a simulated Welcome Page failure causes registration to fail with 422 and fully removes the printer record so subsequent GET returns 404.
- test_TC_GOAR_15_10_normalized_case_whitespace_comparison_avoids_model_change_warning: Confirms that normalization avoids emitting a GOAR-15 model-change warning when the new model differs only by case/whitespace, while identity regeneration behaves normally.
- test_TC_GOAR_15_11_normalization_collision_treated_consistently_as_unchanged: Ensures that any visually distinct model_number string that normalizes to the same value is treated as unchanged, with no model-change warning and normal identity regeneration.
- test_TC_GOAR_15_12_multi_segment_model_number_family_extraction_behaves_consistently: Verifies that re-registration with a multi-segment model HP-C-MFP-9999 is treated as same-model, regenerates identity, and produces no GOAR-15 model-change warning.
- test_TC_GOAR_15_13_no_dash_model_number_treated_as_single_family_string: Confirms that a no-dash model HPLJMFP9999 behaves as a single family string where same-model re-registration regenerates identity without GOAR-15 warnings.
- test_TC_GOAR_15_14_rejected_different_family_leaves_printer_state_unchanged: Checks that a rejected different-family re-registration leaves all printer fields and indices unchanged except for the added GOAR-15 review history entry and warning log.
- test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_behaves_normally: Verifies that initial registration for a previously unused serial succeeds with full identity creation, reflecting the implementation’s behavior for TC-GOAR-15-15.
- test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership: Confirms that re-registration of a claimed printer with unchanged model preserves owner_user_id and CLAIMED status while regenerating Cloud ID and email.
- test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership: Ensures that same-family model change on a claimed printer succeeds, logs the GOAR-15 model change, and preserves ownership and CLAIMED status.
- test_TC_GOAR_15_18_reregistration_from_different_user_context_does_not_transfer_ownership: Checks that re-registering a claimed printer from a different user context does not change owner_user_id or CLAIMED status.
- test_TC_GOAR_15_19_same_family_model_change_emits_structured_warning_log: Verifies that a same-family model change emits a WARNING log from app.registration with serial_number, old_model, and new_model fields while registration succeeds.
- test_TC_GOAR_15_20_rejected_different_family_model_change_emits_structured_warning_log: Ensures that a rejected different-family model change emits a WARNING log with structured fields and leaves printer identity unchanged.
- test_TC_GOAR_15_21_unchanged_model_successful_reregistration_regenerates_identity: Confirms that unchanged-model re-registration regenerates Cloud ID, printer email, and XMPP node as per AR6 while keeping status REGISTERED.
- test_TC_GOAR_15_22_same_family_model_change_successful_reregistration_regenerates_identity: Verifies that same-family model change re-registration regenerates Cloud ID and email and maintains XMPP connectivity and REGISTERED status.
- test_TC_GOAR_15_23_reregistration_for_printer_with_existing_xmpp_preserves_connectivity: Ensures that re-registration of a printer with an existing XMPP node preserves connectivity while regenerating Cloud ID and email.
- test_TC_GOAR_15_24_missing_authorization_header_yields_422_no_side_effects: Confirms that missing Authorization header causes a 422 validation error and leaves existing printer Cloud ID and email unchanged.
- test_TC_GOAR_15_25_invalid_bearer_token_yields_401_no_side_effects: Confirms that an invalid bearer token results in a 401 with detail "Invalid or expired token" and causes no changes to printer identity.

## Assumptions

- The `app.registration` logger name is derived from the module `__name__` and is visible to `caplog` without additional propagation configuration in tests.
- History entries returned by the API are plain strings and can be matched using `startswith`/`in` without needing structured parsing.
- Capabilities and serial index side effects are adequately validated via the observable printer fields and status returned from `GET /printers/{printer_id}`, so direct store access is not required.
- Initial registration for TC-GOAR-15-15 behaves as a normal registration and cannot express rollback semantics for an unknown serial, aligning with the implementation notes in the test cases.
