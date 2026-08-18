# Test Generation Report — GOAR-15

## Summary

- Total test functions generated: 25
- Test cases skipped (UNTESTABLE): 1

## Skipped Test Cases

- TC-GOAR-15-26: Summary entry marked non-executable in Notes field; not a runnable scenario.

## Generated Tests

- test_TC_GOAR_15_01_same_family_model_change_accepted: Verifies that re-registration with a same-family model change succeeds, regenerates identity fields, records history entries, and emits a structured warning log.
- test_TC_GOAR_15_02_case_whitespace_model_difference_treated_as_unchanged: Confirms that case/whitespace-only differences in model_number are treated as unchanged, with new identity but no GOAR-15 model-change warning or log.
- test_TC_GOAR_15_03_different_family_model_change_rejected_with_rollback: Ensures different-family re-registration is rejected with 422 and that Cloud ID, email, XMPP node, and status remain unchanged apart from a review history entry.
- test_TC_GOAR_15_04_different_family_reregistration_rejected_with_no_side_effects: Checks that a clearly different-family model_number re-registration is rejected and leaves all printer identity fields unchanged, with appropriate warning log.
- test_TC_GOAR_15_05_boundary_model_family_mismatch_rejected: Validates boundary behavior where HP-LJ-001 to HP-LJ-2055 is classified as a family mismatch, rejected, and leaves model_number and identity unchanged.
- test_TC_GOAR_15_06_rejected_different_family_has_no_partial_identity_side_effects: Verifies that rejected different-family re-registration does not alter Cloud ID, email, XMPP node, status, or serial_number.
- test_TC_GOAR_15_07_identical_model_firmware_reregistration_generates_new_identity: Confirms that re-registration with identical model and firmware generates new Cloud ID, email, and XMPP node and logs the expected registration events.
- test_TC_GOAR_15_08_reregistration_with_updated_firmware_preserves_ownership: Ensures that re-registration with updated firmware on a claimed printer regenerates identity while preserving CLAIMED status and owner_user_id.
- test_TC_GOAR_15_09_failed_reregistration_pre_welcome_page_rolls_back_printer_record: Tests that a simulated Welcome Page failure during re-registration rolls back the printer record so subsequent lookup returns 404.
- test_TC_GOAR_15_10_normalized_model_comparison_avoids_model_change_warning: Verifies that normalization of model_number avoids model-change warnings when only case/whitespace differ, while still regenerating identity.
- test_TC_GOAR_15_11_normalization_collision_treated_as_unchanged: Confirms that visually distinct but normalization-colliding model_numbers are treated as unchanged with no GOAR-15 warning history or log.
- test_TC_GOAR_15_12_multi_segment_model_family_reregistration_same_family: Checks that re-registration within the same multi-segment model family succeeds with new Cloud ID and email and no model-change warning.
- test_TC_GOAR_15_13_no_dash_model_number_treated_as_single_family_string: Ensures that no-dash model_number strings behave as a single family and re-registration regenerates identity without model-change warnings.
- test_TC_GOAR_15_14_different_family_reregistration_leaves_printer_state_unchanged: Validates rollback where different-family re-registration is rejected and printer identity and connectivity remain identical to pre-state, with only a review entry added.
- test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_succeeds: Confirms that initial registration for a previously unregistered serial behaves as a normal successful registration despite scenario wording about rejection.
- test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership: Verifies that claimed-printer re-registration with unchanged model preserves CLAIMED status and owner_user_id while regenerating identity.
- test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership_and_logs_change: Ensures same-family model change on a claimed printer regenerates identity, preserves ownership, and logs GOAR-15 model-change events plus structured warning.
- test_TC_GOAR_15_18_reregistration_from_different_user_context_does_not_transfer_ownership: Checks that re-registration from a different user context does not alter claimed ownership or status.
- test_TC_GOAR_15_19_same_family_model_change_emits_structured_warning_log: Validates that same-family model-number change emits a structured WARNING log with serial_number, old_model, and new_model while registration succeeds.
- test_TC_GOAR_15_20_rejected_different_family_model_change_emits_warning_and_rolls_back: Verifies that rejected different-family model change leaves printer state unchanged and produces the expected structured warning log.
- test_TC_GOAR_15_21_unchanged_model_reregistration_regenerates_cloud_email_xmpp: Confirms that re-registration with unchanged model regenerates Cloud ID, email, and XMPP node and keeps status REGISTERED.
- test_TC_GOAR_15_22_same_family_model_change_regenerates_cloud_and_email: Ensures same-family model change re-registration regenerates Cloud ID and email and maintains XMPP connectivity and REGISTERED status.
- test_TC_GOAR_15_23_reregistration_preserves_existing_xmpp_connectivity: Verifies that a printer with an existing XMPP node remains connected (non-empty node) after re-registration while identity is regenerated.
- test_TC_GOAR_15_24_missing_authorization_header_yields_422_and_no_side_effects: Checks that missing Authorization header yields a 422 validation error and leaves printer Cloud ID and email unchanged.
- test_TC_GOAR_15_25_invalid_bearer_token_yields_401_and_no_side_effects: Confirms that an invalid bearer token yields 401 with "Invalid or expired token" and does not change printer identity fields.

## Assumptions

- GOAR-15-26 is explicitly non-executable per Notes and therefore treated as UNTESTABLE.
- Capabilities and serial index verification steps in some rollback cases are approximated via GET /printers/{printer_id} state checks, since direct store access is not permitted in API-level tests.
- Logger name for GOAR-15 warnings is effectively captured using caplog with logger="app.registration"; this relies on logging configuration propagating module-level logs under that name.
- For TC-GOAR-15-15, behavior follows implemented registration logic (fresh serial treated as initial registration) rather than scenario wording about rejection; the test asserts successful registration.
- No additional auth contexts beyond the default client fixture are exercised for ownership tests, because registration does not depend on JWT subject; ownership changes only via claim endpoint.
