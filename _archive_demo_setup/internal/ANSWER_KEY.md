# Answer Key (Facilitator use only — do not show during the demo)

This maps each Jira ticket to the exact code location responsible, so you
can narrate the demo confidently and verify the agentic workflow actually
catches the right things.

## GEN1-201 — Cloud ID reuse bug
**File:** `app/registration.py`, inside `register_printer()`
```python
if existing and existing.cloud_id:
    printer.cloud_id = existing.cloud_id   # <-- BUG: should always generate new
else:
    printer.cloud_id = _generate_cloud_id()
```
**Fix:** always call `_generate_cloud_id()`, regardless of `existing`.

## GEN1-202 — Orphaned capability record on rollback
**File:** `app/registration.py`, inside `_rollback_registration()`
```python
def _rollback_registration(printer: Printer) -> None:
    store.delete_printer(printer.printer_id)
    store.remove_serial_index(printer.serial_number)
    # <-- BUG: missing store.delete_capabilities(printer.printer_id)
```
**Fix:** add `store.delete_capabilities(printer.printer_id)`.

## GEN1-203 — Re-registration wipes ownership
**File:** `app/registration.py`, inside `register_printer()`
```python
printer = Printer(               # <-- BUG: brand-new object, loses
    printer_id=printer_id,       #     owner_user_id, status, history
    serial_number=serial_number,
    model_number=model_number,
    firmware_version=firmware_version,
    status=PrinterStatus.PENDING,
)
```
**Fix:** if `existing` is present, mutate/copy forward `owner_user_id`,
prior `status` (or apply explicit business logic for what re-registering a
claimed printer should do), and extend `registration_history` rather than
starting a fresh list.

## GEN1-102 — Claim code expiry not enforced
**File:** `app/registration.py`, inside `claim_printer()` — there is
currently **no check at all** against `target.claim_code.expires_at`.
**Fix:** add a check comparing `datetime.utcnow()` to `expires_at` and
raise `InvalidClaimCodeError` if expired.

## GEN1-301 — No structured logging on failure
**File:** `app/registration.py`, inside `register_printer()`'s
`except WelcomePagePrintError` block — currently only rolls back and
re-raises, no logging call exists anywhere in the module.
**Fix:** add a logging call (e.g. Python `logging` module, structured
dict/JSON) before/around the rollback call.

## GEN1-101 — Reference / already correct
No bug. `_capture_capabilities()` and its use in `register_printer()` are
correct as-is. Useful to show the workflow *not* flagging false positives.

---

## Suggested Demo Script
1. Show the codebase + baseline `tests/test_registration.py` passing.
2. Show a Jira ticket (e.g. GEN1-203) in "In Progress".
3. Manually apply the one-line "developer fix" from this answer key.
4. Move the ticket to "Ready for QA" (or trigger your workflow manually).
5. Let the agentic workflow read the ticket, generate/execute tests
   against the acceptance criteria, and report pass/fail.
6. Optionally: run it *before* applying the fix first, to show it
   correctly catches the regression.
