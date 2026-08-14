# Scenario Coverage: GOAR-15

## AC #1
- Happy path: Re-register an existing printer with a changed `model_number` and verify the change is recorded via `printer.log(...)` and emits a `logger.warning(...)` flagging it for review.
- Boundary: Re-register an existing printer with the `model_number` unchanged and verify no "flagged for review" log entry is produced.

## AC #2
- Happy path: Re-register an existing printer with a `model_number` from a materially different model family (e.g. `HP-LJ-*` → `HP-C-MFP-*`) and verify a `RegistrationError` is raised.
- Boundary: Re-register with a `model_number` in the same family but a different specific revision (e.g. `HP-LJ-4200` → `HP-LJ-4250`) and verify it is accepted, not rejected.

## AC #3
- Happy path: Re-register an existing printer with matching `model_number` and an updated `firmware_version` and verify registration completes end-to-end as before (new Cloud ID, capabilities/XMPP handling, Welcome Page).
- Boundary: Re-register with a same-family but differently-formatted compatible `model_number` and verify it completes successfully rather than being rejected.

## AC #4
- Boundary: Re-register with a `model_number` that differs from the recorded value only in whitespace or letter case (e.g. `"HP-LJ-2055"` vs `" hp-lj-2055"`) and verify it is treated as unchanged (no "flagged for review" log) rather than triggering AC #1's flag.

## AC #5
- Happy path: Once an authoritative model-family source (catalog/lookup) is defined, verify `_model_family()`'s classification matches it for a representative sample of real model numbers spanning multiple product lines.

## AC #6
- Happy path: Re-register a printer with `status == CLAIMED` and an unchanged `model_number`/family, and verify claim/ownership fields (`owner_user_id`, `status`) are preserved unaffected.
- Permission/ownership: Re-register a printer with `status == CLAIMED` where `model_number` changes within the same family, and verify/document current behavior (flag-only, same as an unclaimed printer) pending a decision on whether claimed printers need stricter protection per Business Rule 11.

## AC #7
- Happy path: Trigger a `model_number`-change re-registration and verify the resulting log record carries `serial_number`, `old_model`, and `new_model` as discrete structured fields, not only embedded in the interpolated message string.

## AC #8
- Happy path: Re-register with a same-family `model_number` change and verify it is logged (registration history + `logger.warning`) and the registration still succeeds.
- Negative: Re-register with a different-family `model_number` change and verify `RegistrationError` is raised and the existing stored record's `model_number`/`firmware_version` remain unchanged.
- Boundary: On a rejected (different-family) re-registration, verify no Cloud ID is regenerated, no email is indexed, no capabilities are (re)captured, and no XMPP node is (re)assigned -- i.e. zero partial side effects.
