# Validation Report: GOAR-12
## Acceptance Criteria Check
- A printer that already has an assigned XMPP node does not get reassigned on re-registration: met. The diff guards assignment with `if not printer.xmpp_node`, and the new test `test_xmpp_node_not_reassigned_on_reregistration` verifies the original node remains unchanged.
- First-time registration continues to assign a node as before: met. New-printer registration still executes `assign_xmpp_node` when `printer.xmpp_node` is unset, and existing coverage in `test_register_new_printer_success` confirms a node is assigned.

## Root Cause Assessment
The fix addresses the root cause in `register_printer()` by preserving an already-assigned `xmpp_node` rather than always overwriting it during re-registration. This is a registration-flow change rather than a single-case symptom patch.

## Regression Risk
Low. The change is localized to XMPP node assignment logic. One minor risk is that `if not printer.xmpp_node` treats falsey values like an empty string as "no node assigned," which may behave differently if such invalid stored state exists.

## Confidence Score
Score: 95/100
Justification: The diff satisfies the ticket acceptance criteria and fixes the underlying re-registration behavior while preserving first-time assignment; a small edge-case test gap prevents a perfect score.

## Path to 100/100
Add a concrete regression test covering an existing printer whose `xmpp_node` is already set before re-registration, including any valid re-registration path where the node should remain unchanged. Optionally add coverage for the falsey-value case if the store can persist `xmpp_node` as an empty string.
