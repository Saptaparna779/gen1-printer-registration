# Test Cases: GOAR-15

## TC-GOAR-15-01

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-01 |
| Jira Story | GOAR-15 |
| Maps to AC # | 1 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register an existing printer with a changed `model_number` and verify the change is recorded in registration history and flagged for review. |
| Preconditions | A printer is already registered: `serial_number = "SN-15001"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (via a prior successful `POST /printers/register` call). A valid JWT has been obtained via `POST /auth/token`. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15001", "model_number": "HP-LJ-4250", "firmware_version": "1.0.0"}` (same family, different revision -- see AC #2 for family-mismatch cases; this case isolates AC #1's flag/log behavior). |
| Expected Status | 200 |
| Expected Response | Registration succeeds. Response `history` (list of `printer.log()` entries) contains an entry mentioning `"GOAR-15: model_number changed on re-registration"`, `"old=HP-LJ-4200"`, and `"new=HP-LJ-4250"`, plus a `"flagged for review"` phrase. Server-side application log (via `app.registration` logger) emits a `WARNING`-level record containing the same old/new model values and the serial number (see TC-GOAR-15-17 for structured-field verification specific to AC #7). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-02

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-02 |
| Jira Story | GOAR-15 |
| Maps to AC # | 1 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `POST /printers/register` with no `Authorization` header at all and verify the request is rejected before reaching registration logic. |
| Preconditions | None required (the request should fail on header validation before any printer lookup occurs). |
| Auth | Missing token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15002", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0"}`, sent with no `Authorization` header. |
| Expected Status | 422 |
| Expected Response | FastAPI request-validation error body indicating the required `authorization` header field is missing (e.g. `detail` array with `"loc": ["header", "authorization"]`, `"msg": "Field required"`). No printer record is created. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-03

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-03 |
| Jira Story | GOAR-15 |
| Maps to AC # | 1 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `POST /printers/register` with a syntactically-present but invalid/garbage bearer token and verify it is rejected as unauthorized. |
| Preconditions | None required. |
| Auth | Invalid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15003", "model_number": "HP-LJ-4200", "firmware_version": "1.0.0"}`, sent with header `Authorization: Bearer not-a-real-jwt-token`. |
| Expected Status | 401 |
| Expected Response | `{"detail": "Invalid or expired token"}`. No printer record is created. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-04

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-04 |
| Jira Story | GOAR-15 |
| Maps to AC # | 1 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | Re-register an existing printer with `model_number` unchanged and verify no "flagged for review" log entry is produced. |
| Preconditions | A printer is already registered: `serial_number = "SN-15004"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15004", "model_number": "HP-LJ-4200", "firmware_version": "1.0.1"}` (only firmware differs). |
| Expected Status | 200 |
| Expected Response | Registration succeeds. Response `history` contains no entry mentioning `"model_number changed"` or `"flagged for review"`; only the standard re-registration entries (`"Re-registration started"`, cloud identity/capabilities/XMPP/welcome-page entries) are present. No corresponding `WARNING` log record is emitted. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-05

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-05 |
| Jira Story | GOAR-15 |
| Maps to AC # | 2 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register an existing printer with a `model_number` from a materially different model family and verify the request is rejected with a `RegistrationError`. |
| Preconditions | A printer is already registered: `serial_number = "SN-15005"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15005", "model_number": "HP-C-MFP-9500", "firmware_version": "1.0.0"}` (family `HP-LJ` -> `HP-C-MFP`). |
| Expected Status | 422 |
| Expected Response | `{"detail": "Re-registration rejected: model family mismatch (existing='HP-LJ-4200', incoming='HP-C-MFP-9500'). This looks like a different physical device reusing the same serial number."}` (message contains "model family mismatch"). No new `cloud_id`, `printer_email_id`, or `xmpp_node` is assigned (see TC-GOAR-15-20 for full zero-side-effects verification). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-06

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-06 |
| Jira Story | GOAR-15 |
| Maps to AC # | 2 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | Re-register with a `model_number` in the same family but a different specific revision and verify it is accepted, not rejected. |
| Preconditions | A printer is already registered: `serial_number = "SN-15006"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15006", "model_number": "HP-LJ-4250", "firmware_version": "1.0.0"}` (family `HP-LJ` unchanged). |
| Expected Status | 200 |
| Expected Response | Registration succeeds; no `RegistrationError`. Response `status` is `"REGISTERED"` (or `"CLAIMED"` if previously claimed), `history` contains the "flagged for review" entry from AC #1 (since `model_number` did change), and a new `cloud_id` is present. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-07

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-07 |
| Jira Story | GOAR-15 |
| Maps to AC # | 3 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register an existing printer with matching `model_number` and an updated `firmware_version` and verify registration completes end-to-end as before. |
| Preconditions | A printer is already registered: `serial_number = "SN-15007"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (capture `cloud_id_1`, `printer_email_id_1`, `claim_code_1` from that response). A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15007", "model_number": "HP-LJ-4200", "firmware_version": "2.1.0"}`. |
| Expected Status | 200 |
| Expected Response | Registration succeeds end-to-end: response contains a new `cloud_id` (!= `cloud_id_1`, matches `CID-[A-F0-9]{12}`), a new `printer_email_id` (!= `printer_email_id_1`), a non-null `xmpp_node`, `status: "REGISTERED"`, and `history` shows capability capture, XMPP assignment, and "Welcome page printed successfully; registration complete" entries. No "flagged for review" entry (model_number unchanged). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-08

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-08 |
| Jira Story | GOAR-15 |
| Maps to AC # | 3 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | Re-register with a same-family but differently-formatted compatible `model_number` and verify it completes successfully rather than being rejected. |
| Preconditions | A printer is already registered: `serial_number = "SN-15008"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15008", "model_number": "hp-lj-4250", "firmware_version": "1.0.0"}` (lower-case, same family after `.strip().upper()` normalization inside `_model_family()`). |
| Expected Status | 200 |
| Expected Response | Registration succeeds (not rejected). Response `status` reflects success and `history` contains the AC #1 "flagged for review" entry (raw string comparison `printer.model_number != model_number` still differs even though the family matches), consistent with the current implementation. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-09

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-09 |
| Jira Story | GOAR-15 |
| Maps to AC # | 4 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | Re-register with a `model_number` that differs from the recorded value only in whitespace or letter case and verify it is treated as unchanged (no "flagged for review" log). |
| Preconditions | A printer is already registered: `serial_number = "SN-15009"`, `model_number = "HP-LJ-2055"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15009", "model_number": " hp-lj-2055", "firmware_version": "1.0.0"}` (leading whitespace + lower-case vs. recorded `"HP-LJ-2055"`). |
| Expected Status | 200 |
| Expected Response | Registration succeeds. Per AC #4 (Proposed Addition #4, approved 2026-08-14, implemented in `app/registration.py` via `.strip().upper()` normalization on the model_number comparison), response `history` contains **no** "model_number changed" / "flagged for review" entry, since the values are equivalent once normalized. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-10

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-10 |
| Jira Story | GOAR-15 |
| Maps to AC # | 5 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Verify model-family classification (observed via re-registration accept/reject behavior) matches an authoritative model-family source for a representative sample of real model numbers spanning multiple product lines. |
| Preconditions | An authoritative model-family catalog/lookup has been defined (per Proposed Addition #5 / Open Question #4 -- **not yet present in this repo as of 2026-08-14**). For each sample pair below, a printer is first registered with the "existing" `model_number`, then re-registered with the "incoming" `model_number`, using a valid JWT. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | Sample pairs (existing -> incoming): (1) `HP-LJ-4200` -> `HP-LJ-4250` [same family, expect accept]; (2) `HP-C-MFP-9500` -> `HP-C-MFP-9999` [same family, expect accept]; (3) `HP-OJ-6975` -> `HP-OJ-9015` [same family, expect accept]; (4) `HP-LJ-4200` -> `HP-OJ-6975` [different family, expect reject]; (5) `HP-C-MFP-9500` -> `HP-LJ-4200` [different family, expect reject]; (6) single-segment model `LASERJET` -> `LASERJET2` [tests the `len(parts) == 1` branch of `_model_family()`]. |
| Expected Status | 200 for accept cases, 422 for reject cases |
| Expected Response | Each pair's outcome (accepted vs. `RegistrationError`) matches the authoritative catalog's grouping. **Caveat:** since no authoritative catalog currently exists in this repo, this test case can only be executed against the current crude `_model_family()` heuristic (split on `"-"`, family = all segments but the last) as an interim proxy; it must be re-baselined once an authoritative source is defined. See Notes. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-11

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-11 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register a `CLAIMED` printer with unchanged `model_number`/family and verify claim/ownership fields (`owner_user_id`, `status`) are preserved unaffected. |
| Preconditions | A printer is registered with `serial_number = "SN-15011"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (capture `printer_id` and `claim_code`), then claimed via `POST /printers/claim` with that `claim_code` and `user_id = "user-goar15-a"` (claim response confirms `status: "CLAIMED"`, `owner_user_id: "user-goar15-a"`). A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register (re-registration), then GET /printers/{printer_id} (verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-15011", "model_number": "HP-LJ-4200", "firmware_version": "1.1.0"}` (model_number unchanged). GET: no body; path param `printer_id` = the captured `printer_id`. |
| Expected Status | 200 on both calls |
| Expected Response | POST response `status` is `"CLAIMED"` (unaffected by re-registration) and contains a new `cloud_id`. Follow-up GET response has `owner_user_id == "user-goar15-a"` and `status == "CLAIMED"`, both unchanged from the claim step. No "flagged for review" entry in `history` (model_number unchanged). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-12

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-12 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `POST /printers/claim` with no `Authorization` header and verify the request is rejected. |
| Preconditions | None required. |
| Auth | Missing token |
| Endpoint | /printers/claim |
| HTTP Method | POST |
| Test Data | `{"claim_code": "ABCD1234", "user_id": "user-goar15-x"}`, sent with no `Authorization` header. |
| Expected Status | 422 |
| Expected Response | FastAPI request-validation error body indicating the required `authorization` header field is missing. No claim is processed. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-13

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-13 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `POST /printers/claim` with an invalid/garbage bearer token and verify it is rejected as unauthorized. |
| Preconditions | None required. |
| Auth | Invalid token |
| Endpoint | /printers/claim |
| HTTP Method | POST |
| Test Data | `{"claim_code": "ABCD1234", "user_id": "user-goar15-x"}`, sent with header `Authorization: Bearer not-a-real-jwt-token`. |
| Expected Status | 401 |
| Expected Response | `{"detail": "Invalid or expired token"}`. No claim is processed. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-14

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-14 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `GET /printers/{printer_id}` with no `Authorization` header and verify the request is rejected. |
| Preconditions | A printer exists (e.g. `printer_id` captured from TC-GOAR-15-11's registration step) so a 404 cannot be mistaken for the auth failure. |
| Auth | Missing token |
| Endpoint | /printers/{printer_id} |
| HTTP Method | GET |
| Test Data | No request body; path param `printer_id` = a valid existing printer id. Sent with no `Authorization` header. |
| Expected Status | 422 |
| Expected Response | FastAPI request-validation error body indicating the required `authorization` header field is missing. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-15

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-15 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Auth-negative |
| Test Type | API |
| Scenario | Call `GET /printers/{printer_id}` with an invalid/garbage bearer token and verify it is rejected as unauthorized. |
| Preconditions | A printer exists (e.g. `printer_id` captured from TC-GOAR-15-11's registration step). |
| Auth | Invalid token |
| Endpoint | /printers/{printer_id} |
| HTTP Method | GET |
| Test Data | No request body; path param `printer_id` = a valid existing printer id. Sent with header `Authorization: Bearer not-a-real-jwt-token`. |
| Expected Status | 401 |
| Expected Response | `{"detail": "Invalid or expired token"}`. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-16

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-16 |
| Jira Story | GOAR-15 |
| Maps to AC # | 6 |
| Scenario Type | Permission/ownership |
| Test Type | API |
| Scenario | Re-register a `CLAIMED` printer where `model_number` changes within the same family, and verify/document current behavior (flag-only, same as an unclaimed printer), pending a decision on whether claimed printers need stricter protection per Business Rule 11. |
| Preconditions | A printer is registered with `serial_number = "SN-15016"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (capture `printer_id` and `claim_code`), then claimed via `POST /printers/claim` with `user_id = "user-goar15-b"` (claim response confirms `status: "CLAIMED"`). A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register (re-registration), then GET /printers/{printer_id} (verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-15016", "model_number": "HP-LJ-4250", "firmware_version": "1.0.0"}` (same family `HP-LJ`, different revision, on a CLAIMED printer). GET: no body; path param `printer_id` = the captured `printer_id`. |
| Expected Status | 200 on both calls |
| Expected Response | **Documents current (as-implemented) behavior, not a validated requirement:** registration succeeds (no additional CLAIMED-specific block), response `history` contains the AC #1 "flagged for review" entry exactly as it would for an unclaimed printer, `status` remains `"CLAIMED"` in both the POST response and the follow-up GET, and `owner_user_id` (visible via GET) is unchanged. This confirms the implementation currently applies identical model-family logic regardless of claim status (Proposed Addition #6 / Open Question #4 flags this as an undecided gap against Business Rule 11, not a defect to fail this test on). |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-17

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-17 |
| Jira Story | GOAR-15 |
| Maps to AC # | 7 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Trigger a `model_number`-change re-registration and verify the resulting log record carries `serial_number`, `old_model`, and `new_model` as discrete structured fields, not only embedded in the interpolated message string. |
| Preconditions | A printer is already registered: `serial_number = "SN-15017"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. The test harness is configured to capture application logs emitted by the `app.registration` logger (e.g. via pytest's `caplog` fixture, or equivalent log-capture tooling attached to the running service) in addition to issuing the HTTP request -- this is necessary because the structured log fields are **not** exposed in the `POST /printers/register` HTTP response body (only the human-readable `history` list is). |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15017", "model_number": "HP-LJ-4250", "firmware_version": "1.0.0"}`. |
| Expected Status | 200 |
| Expected Response | HTTP response is a normal success (per AC #1). In the captured log, the `WARNING`-level record emitted for this event exposes `serial_number = "SN-15017"`, `old_model = "HP-LJ-4200"`, and `new_model = "HP-LJ-4250"` as discrete structured attributes on the log record (per AC #7 / Proposed Addition #7, approved 2026-08-14, implemented in `app/registration.py` via `extra={...}` on the `logger.warning(...)` call), independently queryable/alertable rather than requiring string-parsing of the interpolated message. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-18

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-18 |
| Jira Story | GOAR-15 |
| Maps to AC # | 8 |
| Scenario Type | Happy path |
| Test Type | API |
| Scenario | Re-register with a same-family `model_number` change and verify it is logged (registration history + `logger.warning`) and the registration still succeeds. |
| Preconditions | A printer is already registered: `serial_number = "SN-15018"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"`. A valid JWT has been obtained. Test harness has log capture enabled for the `app.registration` logger. |
| Auth | Valid token |
| Endpoint | /printers/register |
| HTTP Method | POST |
| Test Data | `{"serial_number": "SN-15018", "model_number": "HP-LJ-4250", "firmware_version": "1.0.0"}` (same family `HP-LJ`). |
| Expected Status | 200 |
| Expected Response | Registration succeeds: response `status` is `"REGISTERED"`, a new `cloud_id` is present, and `history` contains the "flagged for review" entry (old=HP-LJ-4200, new=HP-LJ-4250). A corresponding `WARNING`-level log record is captured for the same event. No `RegistrationError` is raised. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-19

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-19 |
| Jira Story | GOAR-15 |
| Maps to AC # | 8 |
| Scenario Type | Negative |
| Test Type | API |
| Scenario | Re-register with a different-family `model_number` change and verify `RegistrationError` is raised and the existing stored record's `model_number`/`firmware_version` remain unchanged. |
| Preconditions | A printer is already registered: `serial_number = "SN-15019"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (capture `printer_id`). A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register (rejected re-registration), then GET /printers/{printer_id} (verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-15019", "model_number": "HP-C-MFP-9500", "firmware_version": "9.9.9"}` (different family). GET: no body; path param `printer_id` = the captured `printer_id`. |
| Expected Status | 422 on POST, 200 on GET |
| Expected Response | POST returns `{"detail": "Re-registration rejected: model family mismatch ..."}`. Follow-up GET does not directly expose `model_number`/`firmware_version` in its response schema (`GET /printers/{printer_id}` returns `printer_id`, `serial_number`, `cloud_id`, `printer_email_id`, `status`, `owner_user_id`, `xmpp_node`, `history` -- no `model_number`/`firmware_version` fields); verify indirectly via the unchanged `cloud_id` (still the value from the original registration, not regenerated) and via `history`, which shows only the original registration entries plus the AC #1 "flagged for review" entry -- no new "Cloud identity created", "Capabilities captured", "XMPP node assigned", or "Welcome page printed" entries beyond the original registration. See Notes re: `model_number`/`firmware_version` not being directly queryable via any current API endpoint. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## TC-GOAR-15-20

| Field | Value |
|---|---|
| Test ID | TC-GOAR-15-20 |
| Jira Story | GOAR-15 |
| Maps to AC # | 8 |
| Scenario Type | Boundary |
| Test Type | API |
| Scenario | On a rejected (different-family) re-registration, verify no Cloud ID is regenerated, no email is (re)indexed, no capabilities are (re)captured, and no XMPP node is (re)assigned -- i.e. zero partial side effects. |
| Preconditions | A printer is already registered: `serial_number = "SN-15020"`, `model_number = "HP-LJ-4200"`, `firmware_version = "1.0.0"` (capture `printer_id`, `cloud_id_1`, `printer_email_id_1`, `xmpp_node_1` from that response). A valid JWT has been obtained. |
| Auth | Valid token |
| Endpoint | /printers/register (rejected re-registration), then GET /printers/{printer_id} (verification) |
| HTTP Method | POST, then GET |
| Test Data | POST: `{"serial_number": "SN-15020", "model_number": "HP-OJ-6975", "firmware_version": "1.0.0"}` (different family). GET: no body; path param `printer_id` = the captured `printer_id`. |
| Expected Status | 422 on POST, 200 on GET |
| Expected Response | POST raises `RegistrationError` (422, model family mismatch). Follow-up GET response has `cloud_id == cloud_id_1` (unchanged, no new Cloud ID generated), `printer_email_id == printer_email_id_1` (unchanged, no new email indexed), and `xmpp_node == xmpp_node_1` (unchanged, no reassignment); `history` contains no new "Cloud identity created", "Capabilities captured"/"Capabilities already on record", "XMPP node assigned", or "Welcome page printed" entries beyond the ones from the original registration (only the AC #1 "flagged for review" entry is newly added, which is expected/by-design, not a side effect of the rejected registration proceeding). **Capabilities are not exposed by any current API response** (no endpoint returns `PrinterCapabilities`), so "no capabilities re-captured" cannot be fully verified via the deployed API surface alone -- see Notes. |
| Automation Framework | pytest |
| Automation Code | TBD |
| Expected Result | Pass |

## Notes

- **AC #5 (TC-GOAR-15-10):** No authoritative model-family catalog/lookup exists anywhere in this repo as of 2026-08-14 (confirmed absent from `docs/business_rules.md`; see Open Question #4 / Proposed Addition #5 in the requirements report). The test case as designed can only be run against the current crude `_model_family()` heuristic as an interim proxy for "authoritative," and must be re-baselined once a real catalog is defined and wired in.
- **AC #7 (TC-GOAR-15-17):** The deployed API surface does not expose the structured log record itself -- `logger.warning(...)` output is only observable via server-side log capture (e.g. `caplog`, log aggregation), not via any HTTP response body. The test case is designed API-first (it triggers the event via `POST /printers/register`) but its assertions necessarily also depend on log-capture tooling outside the HTTP response.
- **AC #8 boundary (TC-GOAR-15-20):** `PrinterCapabilities` records are never returned by any endpoint in `app/main.py` (`GET /printers/{printer_id}` omits them). "No capabilities re-captured" can only be partially verified through the deployed API (by confirming no new capability-related `history` log entries appear); full verification of the underlying `PrinterCapabilities` store record would require access beyond the API surface, which is out of scope per this agent's instructions to test the deployed API only. This gap is flagged for the Test Generation Agent's awareness, not resolved here.
- All other scenarios listed in `reports/scenarios/GOAR-15_scenarios.md` (AC #1 happy path/boundary, AC #2 happy path/boundary, AC #3 happy path/boundary, AC #4 boundary, AC #6 happy path/permission-ownership, AC #8 happy path/negative) were fully expandable into test cases with no gaps. No scenario in the coverage file was marked `[unconfirmed]`, so no such tag needed to be carried forward.
- Every protected endpoint used in this file (`POST /printers/register`, `POST /printers/claim`, `GET /printers/{printer_id}`) has at least one missing-token (422) and one invalid-token (401) auth-negative case: TC-GOAR-15-02/03, TC-GOAR-15-12/13, and TC-GOAR-15-14/15 respectively. `DELETE /printers/{printer_id}` is not exercised by any GOAR-15 scenario and so has no auth-negative case in this file.
