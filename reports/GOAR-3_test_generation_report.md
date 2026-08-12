# Test Generation Report: GOAR-3

## Test Cases Covered
- TC-GOAR-3-01 — covered
- TC-GOAR-3-02 — covered
- TC-GOAR-3-03 — covered
- TC-GOAR-3-04 — covered
- TC-GOAR-3-05 — covered
- TC-GOAR-3-06 — covered
- TC-GOAR-3-07 — covered
- TC-GOAR-3-08 — covered
- TC-GOAR-3-09 — covered

All 9 approved test cases have a corresponding automated test function.

## Generated Tests

- **test_TC_GOAR_3_01_reregistration_generates_new_cloud_id** — Registers a printer, then re-registers it with the same serial number, and checks that the Cloud ID returned the second time is different from the first. Automates TC-GOAR-3-01.

- **test_TC_GOAR_3_02_reregistration_regenerates_email_and_claim_code** — Registers a printer, then re-registers it, and checks that the Printer Email ID and Claim Code returned the second time are both different from the values returned the first time. Automates TC-GOAR-3-02.

- **test_TC_GOAR_3_03_reregistration_of_claimed_printer_gets_new_cloud_id_keeps_claimed_status** — Registers a printer, claims it for a user, then re-registers it, and checks that the Cloud ID changes while the printer's status stays "CLAIMED". Automates TC-GOAR-3-03.

- **test_TC_GOAR_3_04_reregistration_of_claimed_printer_preserves_owner** — Registers and claims a printer for a specific user, re-registers it, then looks the printer up again and checks that it's still owned by the same user and still shows as "CLAIMED". Automates TC-GOAR-3-04.

- **test_TC_GOAR_3_05_three_consecutive_registrations_produce_three_distinct_cloud_ids** — Registers the same printer three times in a row and checks that all three Cloud IDs returned are different from each other, not just different from the immediately previous one. Automates TC-GOAR-3-05.

- **test_TC_GOAR_3_06_second_reregistration_cloud_id_differs_from_very_first** — Registers the same printer three times in a row and specifically checks that the third Cloud ID is different from the very first one, guarding against a bug where the system might cycle between only two values. Automates TC-GOAR-3-06.

- **test_TC_GOAR_3_07_recovery_after_failed_reregistration_gets_fresh_cloud_id** — Registers a printer successfully, then triggers a simulated failure on a re-registration attempt (expecting it to be rejected), then re-registers successfully afterward and checks that the recovered Cloud ID is different from the original one and was not affected by the failed attempt. Automates TC-GOAR-3-07.

- **test_TC_GOAR_3_08_failed_reregistration_rolls_back_printer_record** — Registers a printer successfully, then triggers a simulated Welcome Page print failure during re-registration, and checks both that the request is rejected with the expected error message and that looking the printer back up afterward returns "not found" — confirming the failed attempt left no partially-updated record behind. Automates TC-GOAR-3-08.

- **test_TC_GOAR_3_09_reregistration_after_deregistration_generates_new_cloud_id** — Registers a printer, deregisters it, then registers it again using the same serial number, and checks that the new Cloud ID is different from the original one. Automates TC-GOAR-3-09.

## File Created
tests/test_GOAR-3_generated.py

## Smoke Test Awareness
`tests/smoke_test_health.py` only exercises `GET /health` as a basic "is the app up" liveness gate, run as a separate real-subprocess check before the functional suite. GOAR-3 does not introduce any new endpoint — it changes internal behavior of the existing `POST /printers/register` handler (always generating a new Cloud ID) inside `app/registration.py`. Since no new route was added, the existing smoke test remains sufficient for this ticket; no suggested changes to it.

## Notes
All 9 test cases from reports/testcases/GOAR-3_test_cases.md were automatable directly against the HTTP API using the `client` TestClient fixture, with one caveat carried over from the test case design itself (already flagged in reports/testcases/GOAR-3_test_cases.md and reflected here for completeness):

- TC-GOAR-3-07 cannot directly observe the Cloud ID generated during the failed/rolled-back re-registration attempt, because `RegistrationError` is raised before any Printer data is returned to the caller, and the rollback deletes the record outright (confirmed separately by TC-GOAR-3-08). The generated test instead asserts that the recovery call's Cloud ID differs from the last known-good Cloud ID captured before the failure — the strongest check the API surface allows.
