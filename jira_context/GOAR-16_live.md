# GOAR-16: Raw internal exception text is exposed to API callers

**Type:** Bug  
**Priority:** Low  
**Status:** Ready for QA  

## Description
In app/main.py, RegistrationError exceptions are passed straight through
to the HTTP response via detail=str(exc). This risks leaking internal
implementation details (e.g. internal function names, state) to external
callers rather than returning a sanitized, business-facing error message.
Acceptance Criteria:
API error responses return a generic, sanitized error message for
callers.
The original detailed exception is still logged server-side for
debugging purposes.
HTTP status codes for existing error cases remain unchanged.

