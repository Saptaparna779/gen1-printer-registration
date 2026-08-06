Context Summary: GOAR-8
Summary
This ticket describes a bug in the claiming flow where a claim attempt can still succeed even when the target printer is already claimed by a different owner. The issue is framed as a defense-in-depth gap that could enable printer takeover, and the change is intended to prevent an existing ownership claim from being overwritten by a new claim attempt.

Systems/Endpoints Touched
registration.py
Printer registration and claiming state handling in the registration flow
Business Rules Implicated
Rule 8: Claim Code is a temporary security token and must be rejected when invalid or expired; this ticket concerns preventing a claim flow from allowing an already-claimed printer to be overwritten.
Rule 11: Registration/re-registration logic must never silently overwrite or wipe out an existing owner’s claim on a printer.

Open Questions
None identified.