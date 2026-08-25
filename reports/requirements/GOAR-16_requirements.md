# Requirements Report — GOAR-16

## 1. Summary

The ticket addresses leakage of raw internal exception text from the registration and deregistration endpoints to API callers. Previously, RegistrationError messages were surfaced directly via HTTPException(detail=str(exc)), exposing internal implementation details. The fix introduces generic, sanitized error messages for clients while logging the detailed exception server-side, preserving observability without compromising information security.

## 2. Affected Components

- app/main.py — register_printer() (POST /printers/register)
  - The `RegistrationError` handling block has been modified to:
    - Log the exception via `logger.error("Registration failed for serial_number=%s: %s", req.serial_number, exc)`.
    - Raise `HTTPException` with status code 422 and a generic error message: `"Registration could not be completed. Please check your request and try again."` instead of `detail=str(exc)`.
- app/main.py — deregister_printer() (DELETE /printers/{printer_id})
  - The `RegistrationError` handling block has been modified to:
    - Log the exception via `logger.error("Deregistration failed for printer_id=%s: %s", printer_id, exc)`.
    - Raise `HTTPException` with status code 404 and a generic error message: `"Printer not found."` instead of `detail=str(exc)`.
- app/main.py — module-level logging configuration
  - A module-level logger is introduced via `import logging` and `logger = logging.getLogger(__name__)`.

No discrepancies were identified between the diff in reports/GOAR-16_diff.txt and the current implementation in app/main.py; the changes to error handling and logging align.

## 3. Applicable Business Rules

- Rule 14 — Non-Functional Expectations
  - Quoted sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk."
  - Relevance: The requirement to log detailed exceptions server-side while sanitizing client-facing messages aligns with the need for failures to be observable without exposing internal details to callers.

No other business rules in docs/business_rules.md explicitly address client-facing error message content or exception sanitization. The remaining rules primarily concern registration semantics (Cloud ID, claim code, deregistration behaviour) and are not directly implicated by this ticket as described.

## 4. Original Acceptance Criteria

Verbatim from jira_context/GOAR-16_live.md:

1. "API error responses return a generic, sanitized error message for callers."
2. "The original detailed exception is still logged server-side for debugging purposes."
3. "HTTP status codes for existing error cases remain unchanged."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. **Consistent sanitization for all RegistrationError paths on registration**
   - Requirement: For POST /printers/register, any `RegistrationError` raised during registration must result in a generic, sanitized error message being returned to the client that does not include internal function names, module names, or stack trace fragments; only the log entry may contain the detailed exception text.
   - Justification: Edge case category — repeated operations and error-path consistency. This ensures that future branches or additional `RegistrationError`-raising code paths do not reintroduce raw exception leakage while maintaining the existing logging behaviour mandated by Rule 14 ("Registration failures should be observable (structured logging / telemetry), not silent").

2. **Consistent sanitization for all RegistrationError paths on deregistration**
   - Requirement: For DELETE /printers/{printer_id}, any `RegistrationError` raised during deregistration must result in a generic, sanitized error message being returned to the client (e.g., "Printer not found.") that does not include raw exception text or internal identifiers.
   - Justification: Edge case category — error-path consistency. While the current implementation sanitizes one `RegistrationError` path, this requirement guards against future changes that might reintroduce raw exception details on other branches; observability remains protected by Rule 14 through logging.

3. **No inclusion of user-supplied free-form text in error detail**
   - Requirement: Sanitized error messages returned to clients for registration and deregistration must not directly embed user-supplied free-form strings (e.g., `str(exc)` where `exc` may contain user-originated content), to avoid echoing potentially sensitive or unvalidated input back to the caller.
   - Justification: Edge case category — boundary values and security-oriented error handling. This prevents error messages from inadvertently exposing or reflecting sensitive user data. There is no explicit business rule sentence governing this, so this remains a proposed security hardening requirement.

## 6. Flagged Conflicts

None identified. The implemented changes are consistent with Rule 14's requirement for observable registration failures and do not contradict any other explicit business rules in docs/business_rules.md. HTTP status codes remain 422 for registration failures and 404 for deregistration failures, matching the original behaviour described in the ticket and diff.

## 7. Open Questions

1. **Scope of sanitization beyond RegistrationError**
   - Question: Should the same sanitization and logging pattern (generic client-facing message, detailed server-side log) be applied to other exception types (e.g., InvalidClaimCodeError in /printers/claim, or generic HTTPException cases), or is GOAR-16 explicitly limited to `RegistrationError` handling in register_printer and deregister_printer?
   - Why unresolved: The Jira ticket text explicitly mentions "RegistrationError exceptions" and the diff only modifies the registration and deregistration handlers; docs/business_rules.md does not address error message sanitization for other exception types.
   - Exclusion guidance: Downstream agents responsible for scenario design, test derivation, and automated test generation must exclude assumptions about sanitization of non-RegistrationError exceptions from scoring; they should treat this as out of scope unless clarified by a human.

2. **Logging format and correlation requirements**
   - Question: Are there any mandated formats, fields (e.g., correlation IDs, user IDs), or logging destinations that must be used for the server-side logs created when a RegistrationError occurs, beyond the simple `logger.error` calls introduced here?
   - Why unresolved: The only relevant business rule (Rule 14) states that failures should be observable via structured logging/telemetry but does not prescribe specific formats or additional metadata; the Jira ticket only requires that detailed exceptions are "logged server-side" without further constraints.
   - Exclusion guidance: Downstream agents must not score or enforce specific logging formats, correlation IDs, or log transport mechanisms; tests should limit themselves to asserting that logging is invoked (where observable) rather than its precise structure.

3. **Client-facing message stability as an API contract**
   - Question: Should the exact text of the sanitized error messages (e.g., "Registration could not be completed. Please check your request and try again." and "Printer not found.") be treated as a stable, contractually significant part of the API, or is any generic, non-leaking message acceptable as long as the HTTP status codes remain unchanged?
   - Why unresolved: The Jira ticket specifies only "generic, sanitized error message" without constraining the exact text; business rules focus on observability and do not cover client-facing copy or localization.
   - Exclusion guidance: Downstream agents must avoid treating the exact error message strings as hard requirements for scoring; they may instead assert high-level properties (generic wording, no internal details, no raw exception text) unless product owners later codify specific messages.
