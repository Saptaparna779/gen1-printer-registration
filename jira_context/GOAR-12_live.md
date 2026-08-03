# GOAR-12: XMPP node reassigned unnecessarily on every re-registration

**Type:** Bug  
**Priority:** Medium  
**Status:** Ready for QA  

## Description
Business context: XMPP connectivity is called out as an operational risk
area -- server restarts already cause mass reconnections at scale
(BUD Section 10 / 11.4). Currently, register_printer() reassigns a printer
to a new random XMPP node on every call, including re-registrations where
the previous connection was perfectly healthy -- adding avoidable
reconnection load with no business justification.
Acceptance Criteria:
A printer that already has an assigned XMPP node does not get
reassigned to a new one on re-registration, unless there is a specific
reason to (e.g. node failure -- out of scope for this fix).
First-time registration continues to assign a node as before.

