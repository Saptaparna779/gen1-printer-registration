# Test Cases: GOAR-3

## TC-GOAR-3-01

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-01 |
| Jira Story | GOAR-3 |
| Maps to AC # | 1 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Register a printer, then re-register the same serial number, and confirm the second call's `cloud_id` differs from the first. |
| Preconditions | No printer record exists yet for `serial_number = "SN-1001"` (clean/unused serial). |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Call 1: `{"serial_number": "SN-1001", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. Call 2 (re-registration, identical body): `{"serial_number": "SN-1001", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. |
| Expected Status | 200 on both calls |
| Expected Response | Call 1 returns a `cloud_id` matching pattern `CID-[A-F0-9]{12}` (capture as `cloud_id_1`). Call 2 returns a `cloud_id` matching the same pattern (capture as `cloud_id_2`), with `cloud_id_2 != cloud_id_1`. Both responses have `status: "REGISTERED"`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-02

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-02 |
| Jira Story | GOAR-3 |
| Maps to AC # | 2 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register a printer and confirm both `printer_email_id` and `claim_code` in the response differ from their values prior to re-registration. |
| Preconditions | A printer has already been registered once with `serial_number = "SN-1002"`; the first response's `printer_email_id` and `claim_code` have been captured. |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Re-registration call (same serial, same identity fields): `{"serial_number": "SN-1002", "model_number": "HP-M404", "firmware_version": "1.0.1"}`. |
| Expected Status | 200 |
| Expected Response | Response `printer_email_id` != the `printer_email_id` captured from the first registration, and matches pattern `[a-z0-9]{10}@print.hpeprint.com`. Response `claim_code` != the `claim_code` captured from the first registration, and matches pattern `[A-Z0-9]{8}`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-03

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-03 |
| Jira Story | GOAR-3 |
| Maps to AC # | 3 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Claim a registered printer, then re-register the same serial number, and confirm the response has a new `cloud_id` while `status` remains `CLAIMED`. |
| Preconditions | A printer has been registered with `serial_number = "SN-1003"` (capture `cloud_id_1` and `claim_code_1` from the response), and then claimed via `POST /printers/claim` using `claim_code_1` and `user_id = "user-alpha"` (claim response confirms `status: "CLAIMED"`). |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Re-registration call: `{"serial_number": "SN-1003", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. |
| Expected Status | 200 |
| Expected Response | Response `cloud_id` != `cloud_id_1`. Response `status` == `"CLAIMED"` (unchanged by re-registration). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-04

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-04 |
| Jira Story | GOAR-3 |
| Maps to AC # | 3 |
| Scenario Type | Permission/ownership |
| Test Type | API |
| Scenario | Re-register an already-claimed printer and confirm `owner_user_id` is unchanged after re-registration. |
| Preconditions | A printer has been registered with `serial_number = "SN-1004b"` and claimed via `POST /printers/claim` using `user_id = "user-beta"` (claim response confirms `owner_user_id: "user-beta"`; capture `printer_id` from the registration response). |
| Endpoint | /printers/register (re-registration), then GET /printers/{printer_id} (verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-1004b", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. GET: no body, path param `printer_id` = the captured printer_id. |
| Expected Status | 200 on both calls |
| Expected Response | The `POST /printers/register` response is 200 (note: this endpoint does not return `owner_user_id`, so ownership is verified via the follow-up GET). The `GET /printers/{printer_id}` response has `owner_user_id == "user-beta"` (unchanged) and `status == "CLAIMED"`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-05

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-05 |
| Jira Story | GOAR-3 |
| Maps to AC # | 4 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Register a printer and re-register it twice in succession, confirming all three returned Cloud IDs are distinct from one another. |
| Preconditions | No printer record exists yet for `serial_number = "SN-1005"`. |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Three sequential calls with identical body: `{"serial_number": "SN-1005", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. |
| Expected Status | 200 on all three calls |
| Expected Response | `cloud_id` values captured as `cloud_id_1`, `cloud_id_2`, `cloud_id_3` respectively. Assert all three are pairwise distinct: `cloud_id_1 != cloud_id_2`, `cloud_id_2 != cloud_id_3`, `cloud_id_1 != cloud_id_3`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-06

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-06 |
| Jira Story | GOAR-3 |
| Maps to AC # | 4 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | Confirm the Cloud ID from the second re-registration is not equal to the very first Cloud ID (not merely different from the immediately preceding one). |
| Preconditions | No printer record exists yet for `serial_number = "SN-1006"`. |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Three sequential calls with identical body: `{"serial_number": "SN-1006", "model_number": "HP-M404", "firmware_version": "1.0.0"}` (call 1 = initial registration, call 2 = first re-registration, call 3 = second re-registration). |
| Expected Status | 200 on all three calls |
| Expected Response | `cloud_id` values captured as `cloud_id_1` (call 1) and `cloud_id_3` (call 3, the second re-registration). Assert `cloud_id_3 != cloud_id_1` specifically — this guards against an implementation that only avoids reusing the immediately-preceding value (e.g. alternating between two IDs) rather than generating a truly fresh one each time. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-07

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-07 |
| Jira Story | GOAR-3 |
| Maps to AC # | 5 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | After a failed re-registration attempt is rolled back, confirm the next successful re-registration for the same serial number returns a new Cloud ID that was not the one generated during the failed attempt. |
| Preconditions | A printer has been registered successfully with `serial_number = "SN-1007"` (capture `cloud_id_1`). A subsequent re-registration call for the same serial with `simulate_welcome_page_failure: true` has been made and returned a 422 error (rollback deletes the printer record entirely, including its serial-number index, so the failed attempt's `cloud_id` is never exposed via the API). |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Recovery call: `{"serial_number": "SN-1007", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": false}`. |
| Expected Status | 200 |
| Expected Response | Response `cloud_id` (capture as `cloud_id_recovery`) is a valid `CID-` value and `cloud_id_recovery != cloud_id_1`. Since the rollback deletes the printer record outright, this call is served as a fresh registration and returns a new `printer_id` (different from the one issued for the original successful registration) — note this as expected rollback behavior, not a defect. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-08

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-08 |
| Jira Story | GOAR-3 |
| Maps to AC # | 5 |
| Scenario Type | Negative |
| Test Type | API |
| Scenario | Trigger a re-registration failure (simulated Welcome Page print failure) and confirm the printer record is rolled back rather than left with a partially-updated Cloud ID. |
| Preconditions | A printer has been registered successfully with `serial_number = "SN-1008"` (capture `printer_id_1` and `cloud_id_1` from the response). |
| Endpoint | /printers/register (failure trigger), then GET /printers/{printer_id} (rollback verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-1008", "model_number": "HP-M404", "firmware_version": "1.0.0", "simulate_welcome_page_failure": true}`. GET: no body, path param `printer_id` = `printer_id_1`. |
| Expected Status | POST: 422. GET: 404. |
| Expected Response | POST response body: `{"detail": "Welcome page failed to print for printer_id=<printer_id_1>"}`. Follow-up `GET /printers/{printer_id_1}` returns `{"detail": "Printer not found"}` with 404, confirming the record (and its Cloud ID) was fully removed rather than left with a partially-updated `cloud_id`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-3-09

| Field | Value |
|---|---|
| Test ID | TC-GOAR-3-09 |
| Jira Story | GOAR-3 |
| Maps to AC # | 6 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Register a printer, deregister it, then register again with the same serial number, and confirm the new `cloud_id` differs from the original. |
| Preconditions | No printer record exists yet for `serial_number = "SN-1009"`. |
| Endpoint | /printers/register (x2), and DELETE /printers/{printer_id} in between |
| HTTP Method | POST, DELETE, POST |
| Test Data | POST 1: `{"serial_number": "SN-1009", "model_number": "HP-M404", "firmware_version": "1.0.0"}` (capture `printer_id_1`, `cloud_id_1`). DELETE: path param `printer_id` = `printer_id_1`, no body. POST 2 (after deregistration): `{"serial_number": "SN-1009", "model_number": "HP-M404", "firmware_version": "1.0.0"}`. |
| Expected Status | 200 on both POST calls; 200 on DELETE. |
| Expected Response | DELETE response: `{"status": "DEREGISTERED", "printer_id": "<printer_id_1>"}`. POST 2 response: 200 with a valid `cloud_id` (capture as `cloud_id_2`), and `cloud_id_2 != cloud_id_1`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## Notes
None. Every scenario listed in reports/scenarios/GOAR-3_scenarios.md (AC #1 through AC #6, 9 scenarios total) has a corresponding fully-specified test case above.

One implementation detail worth flagging for the Test Generation Agent: the `POST /printers/register` response does not include `owner_user_id`, so TC-GOAR-3-04 (AC #3 permission/ownership) verifies it via a follow-up `GET /printers/{printer_id}` call rather than from the register response directly. Similarly, TC-GOAR-3-07 (AC #5 happy path) cannot directly observe the Cloud ID generated during the failed/rolled-back attempt, since `RegistrationError` is raised before any Printer data is returned to the caller and the rollback deletes the record outright — the test instead asserts the recovery call's Cloud ID differs from the *last known-good* Cloud ID, which is the strongest check the API surface allows.
