# Test Generation Report — GOAR-15

## Summary

- Total test functions generated: 25
- Test cases skipped (UNTESTABLE): 0

## Skipped Test Cases

- None — TC-GOAR-15-26 is a non-executable summary by design and was not converted into a test.

## Generated Tests

- test_TC_GOAR_15_01_same_family_model_change_accepted: Verifies that a same-family model change on re-registration succeeds, regenerates cloud ID and email, updates history, and emits a structured WARNING log.
- test_TC_GOAR_15_02_case_whitespace_model_difference_treated_as_unchanged: Checks that case/whitespace-only model differences are normalized and do not produce a GOAR-15 model-change warning or history entry while still regenerating identity.
- test_TC_GOAR_15_03_different_family_model_change_rejected_with_rollback: Ensures different-family model changes are rejected with 422 and that cloud ID, email, XMPP node, and status remain unchanged apart from an added review entry.
- test_TC_GOAR_15_04_different_family_reregistration_rejected_no_side_effects: Confirms that a clearly different-family re-registration is rejected via RegistrationError and leaves all identity fields unchanged while logging the review entry.
- test_TC_GOAR_15_05_boundary_model_family_mismatch_rejected: Validates the heuristic edge case where HP-LJ-001 vs HP-LJ-2055 is treated as a mismatch, rejecting the re-registration and preserving original model and identity.
- test_TC_GOAR_15_06_rejected_different_family_has_no_partial_identity_side_effects: Verifies that different-family re-registration failures do not alter cloud ID, email, XMPP node, serial number, or capabilities.
- test_TC_GOAR_15_07_identical_identity_reregistration_generates_new_cloud_email_xmpp: Confirms that re-registration with identical model and firmware regenerates cloud ID, printer email, and XMPP node while keeping status REGISTERED.
- test_TC_GOAR_15_08_reregistration_with_updated_firmware_preserves_ownership: Ensures that re-registration with updated firmware regenerates identity but preserves CLAIMED status and owner_user_id.
- test_TC_GOAR_15_09_non_goar15_pre_welcome_page_failure_rolls_back_printer_record: Tests that simulate_welcome_page_failure causes a 422 error and a full rollback such that the printer record disappears.
- test_TC_GOAR_15_10_normalized_case_whitespace_comparison_avoids_model_change_warning: Verifies that normalization of case and whitespace avoids GOAR-15 model-change warnings for effectively identical model strings.
- test_TC_GOAR_15_11_normalization_collision_treated_as_unchanged: Checks that normalization collisions where two visually distinct strings normalize identically are treated as unchanged, with no GOAR-15 warning.
- test_TC_GOAR_15_12_multi_segment_model_family_same_model_reregistration_behaves_normally: Confirms that re-registration with identical multi-segment model HP-C-MFP-9999 behaves as a normal re-registration, regenerating identity and keeping status REGISTERED.
- test_TC_GOAR_15_13_no_dash_model_number_treated_as_single_family_string: Ensures that a no-dash model string is treated as a single family and that same-model re-registration regenerates identity without GOAR-15 warnings.
- test_TC_GOAR_15_14_rejected_different_family_leaves_printer_state_exactly_unchanged: Verifies that different-family re-registration rejection leaves all printer fields unchanged compared to pre-state except for an added review history entry.
- test_TC_GOAR_15_15_initial_registration_for_unregistered_serial_succeeds_normally: Confirms that an unregistered serial behaves as initial registration, creating a new printer with valid cloud ID, email, claim code, and REGISTERED status.
- test_TC_GOAR_15_16_reregistration_of_claimed_printer_with_unchanged_model_preserves_ownership: Checks that CLAIMED printers re-registered with unchanged model regenerate cloud/email but keep owner_user_id and CLAIMED status intact.
- test_TC_GOAR_15_17_same_family_model_change_on_claimed_printer_preserves_ownership_and_logs_history: Ensures that a same-family model change on a CLAIMED printer preserves ownership, keeps CLAIMED status, and logs GOAR-15 review and WARNING entries.
- test_TC_GOAR_15_18_reregistration_from_different_user_context_does_not_transfer_ownership: Verifies that re-registering a CLAIMED printer from a different user context does not transfer or clear ownership and leaves status CLAIMED.
- test_TC_GOAR_15_19_same_family_model_change_emits_structured_warning_log: Confirms that same-family model changes emit a structured WARNING log containing serial_number, old_model, and new_model while the registration succeeds.
- test_TC_GOAR_15_20_rejected_different_family_model_change_emits_structured_warning_log: Checks that different-family model changes emit structured WARNING logs and are rejected with 422 while leaving printer state unchanged.
- test_TC_GOAR_15_21_unchanged_model_successful_reregeneration_of_cloud_email_xmpp: Ensures that unchanged-model re-registration regenerates cloud ID, printer email, and XMPP connectivity as per GOAR-3 behavior.
- test_TC_GOAR_15_22_same_family_model_change_successful_reregeneration_of_cloud_email: Verifies that same-family model changes regenerate cloud ID and printer email while keeping XMPP node non-empty and status REGISTERED.
- test_TC_GOAR_15_23_reregistration_for_printer_with_existing_xmpp_node_preserves_connectivity: Confirms that re-registration of a printer with an existing XMPP node keeps connectivity while regenerating cloud ID and email.
- test_TC_GOAR_15_24_missing_authorization_header_yields_422_and_no_side_effects: Tests that missing Authorization header yields 422 validation error and leaves printer identity unchanged.
- test_TC_GOAR_15_25_invalid_bearer_token_yields_401_and_no_side_effects: Verifies that an invalid bearer token yields 401 with "Invalid or expired token" and does not change printer identity.

## Assumptions

- All 25 executable test cases in the Summary Table are testable; none are marked UNTESTABLE in the Notes field, so no @pytest.mark.skip placeholders were needed.
- TC-GOAR-15-26 is explicitly documented as a non-executable summary and was intentionally not converted into a test function; this aligns with the Notes and does not count as UNTESTABLE.
- The structured logging for GOAR-15 is emitted by the logger name "app.registration" and includes extra fields serial_number, old_model, and new_model as shown in app/registration.py.
- History assertions use substring matching (e.g., checking for "GOAR-15: model_number changed on re-registration", "Cloud identity created", and "Welcome page printed successfully; registration complete") rather than exact string equality to remain robust against minor formatting changes.
- Auth behavior for missing and invalid tokens relies on FastAPI's dependency injection with verify_token: missing Authorization header yields 422, while invalid/expired token yields 401 with body {"detail": "Invalid or expired token"}, as specified in the test case document and app/main.py.
- No placeholder tokens like "<valid_token_from_conftest>" were used in code; valid-token scenarios rely on the client fixture's default header, missing-token scenarios explicitly pass headers={}, and invalid-token scenarios use headers={"Authorization": "Bearer invalid_token"}.
- Capability and serial index side-effect checks are performed indirectly via the HTTP API (GET /printers/{printer_id}) rather than direct store access, in line with the project guideline that tests should not call store directly.
