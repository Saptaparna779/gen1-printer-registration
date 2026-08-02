# GOAR-11: Whitespace-only serial number, model number, or firmware version passes validation

**Type:** Bug  
**Priority:** Low  
**Status:** Ready for QA  

## Description
register_printer()'s validation only checks for falsy/empty strings
(if not serial_number ...), which does not catch strings that are just
whitespace (e.g. " "). This allows garbage records to be created.
Steps to Reproduce:
Call register_printer() with serial_number=" " (a single space).
Actual: registration proceeds as if this were a valid serial number.
Expected: this should be rejected as invalid input.
Acceptance Criteria:
serial_number, model_number, and firmware_version are rejected if they
are empty OR contain only whitespace.
Valid non-empty values continue to work as before.

