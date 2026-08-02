# GOAR-7: Re-registration regenerates claim code even for an already-claimed printer, enabling takeover

**Type:** Bug  
**Priority:** Highest  
**Status:** Ready for QA  

## Description
Business rule: "Registration/re-registration logic must never silently
overwrite or wipe out an existing owner's claim on a printer." Currently,
register_printer() unconditionally generates a new Claim Code on every
call, including re-registration of a printer that is already CLAIMED. A
new Welcome Page gets printed with a fresh claim code -- anyone who sees
that reprinted page (e.g. a technician during a firmware update visit)
could use it to claim a printer someone else already owns.
Steps to Reproduce:
Register and claim a printer with user_id="user-abc".
Trigger a re-registration for the same serial number (e.g. firmware
update handshake).
Actual: a brand new claim_code is generated and would be printed on a
new Welcome Page.
Expected: no new claim code should be issued for a printer that is
already CLAIMED.
Acceptance Criteria:
Re-registering an already-CLAIMED printer does not generate a new claim
code.
First-time registration and re-registration of an unclaimed printer
continue to generate a claim code as before (do not regress).
Impact: Critical -- direct security/ownership risk, printer hijack vector.

