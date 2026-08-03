# GOAR-13: Registration history does not distinguish first-time registration from re-registration

**Type:** Bug  
**Priority:** Medium  
**Status:** Ready for QA  

## Description
Every registration call logs the same generic "Registration started"
history entry, regardless of whether this is a brand new printer or a
re-registration of an existing (possibly CLAIMED) one. This makes it hard
to audit ownership-sensitive re-registration events after the fact --
directly relevant following the GOAR-5 ownership-wipe fix, where knowing
exactly when a re-registration happened matters for incident review.
Acceptance Criteria:
The registration history log entry clearly distinguishes a first-time
registration from a re-registration of an existing printer record.
No change to any other registration behavior.

