# Scenario Coverage: GOAR-3

## AC #1
- Happy path: Register a printer, then re-register the same serial number, and confirm the second call's `cloud_id` differs from the first.

## AC #2
- Happy path: Re-register a printer and confirm both `printer_email_id` and `claim_code` in the response differ from their values prior to re-registration.

## AC #3
- Happy path: Claim a registered printer, then re-register the same serial number, and confirm the response has a new `cloud_id` while `status` remains `CLAIMED`.
- Permission/ownership: Re-register an already-claimed printer and confirm `owner_user_id` is unchanged after re-registration.

## AC #4
- Happy path: Register a printer and re-register it twice in succession, confirming all three returned Cloud IDs are distinct from one another.
- Boundary: Confirm the Cloud ID from the second re-registration is not equal to the very first Cloud ID (not merely different from the immediately preceding one).

## AC #5
- Happy path: After a failed re-registration attempt is rolled back, confirm the next successful re-registration for the same serial number returns a new Cloud ID that was not the one generated during the failed attempt.
- Negative: Trigger a re-registration failure (simulated Welcome Page print failure) and confirm the printer record is rolled back rather than left with a partially-updated Cloud ID.

## AC #6
- Happy path: Register a printer, deregister it, then register again with the same serial number, and confirm the new `cloud_id` differs from the original.
