**Key:** GOAR-5
**Type:** Bug
**Priority:** Critical
**Component:** Printer Onboarding & Registration
**Status:** In Progress
**Reported By:** Customer Support escalation

## Summary
Re-registering a serial number silently un-claims an already-claimed printer

## Description
A customer reported their printer suddenly disappeared from HP Smart and
Instant Ink stopped working, despite never removing it. Investigation shows
that when a printer with the same serial number is registered again (e.g.
triggered by a firmware update that re-runs the onboarding handshake), the
system creates a brand-new internal printer record and overwrites the
existing one — **wiping the `owner_user_id`, claim status, and registration
history** of the already-claimed printer in the process.

This directly violates the expectation that claiming enables durable
subscriptions and remote management (BUD Section 11.3) — an already-claimed
printer should not be silently un-claimed by a routine re-registration
event.

## Steps to Reproduce
1. Register printer `SN-9999` and claim it with `user_id="user-abc"`.
2. Confirm `GET /printers/{id}` shows `status: CLAIMED`,
   `owner_user_id: "user-abc"`.
3. Call register again with serial `SN-9999` (simulating a re-onboard
   handshake).
4. **Actual:** the printer's `status` resets to `REGISTERED` and
   `owner_user_id` becomes `null`. Registration history prior to the
   re-registration is lost.
5. **Expected:** re-registering a printer that is already `CLAIMED`
   should refresh its identity/connectivity fields as needed but must
   **preserve** `owner_user_id`, `status`, and prior history — or, at
   minimum, require explicit confirmation before altering ownership.

## Acceptance Criteria
- [ ] Re-registering an already-claimed printer does not clear
      `owner_user_id`.
- [ ] Re-registering an already-claimed printer does not reset `status`
      away from `CLAIMED`.
- [ ] Registration history is preserved (appended to, not replaced).
- [ ] First-time registration of a genuinely new serial number is
      unaffected (do not regress).

## Impact
Critical — direct customer-facing impact, loss of subscription linkage.
