# Requirements Report — GOAR-8

## 1. Summary

claim_printer() previously validated only that a claim code was unused, without checking whether the associated printer was already in a CLAIMED state for another owner, creating an ownership hijack path. This ticket ensures claim_printer() rejects attempts to claim an already-claimed printer and that registration logic does not issue new claim codes for claimed printers, aligning with ownership protection business rules and closing a critical defense-in-depth gap.

## 2. Affected Components

- app/registration.py — claim_printer(): core claim handling logic that links a printer to a user account using a claim code, including ownership and status transitions. Reached via whatever endpoint or RPC triggers claiming in the demo service (not explicitly defined in this repo, but this function is the business-logic entry point for claims).
- app/registration.py — register_printer(): registration and re-registration logic that creates cloud identity (Cloud ID, Printer Email ID, Claim Code) and controls whether a new claim code is generated for an already-CLAIMED printer. Reached via the registration endpoint (not explicitly defined in this repo, but this function is the business-logic entry point for registration).
- app/models.py — PrinterStatus enum and Printer model: defines the CLAIMED state and ownership fields (owner_user_id) used by both register_printer() and claim_printer().
- app/store.py — all_printers(): in-memory iteration over printers used by claim_printer() to resolve the target printer from a claim code.

No discrepancies were identified between the Jira ticket and the current implementation for these components. The diff file reports/GOAR-8_diff.txt is empty in this repo snapshot, but the live code in app/registration.py already includes the CLAIMED-state guard in claim_printer() and the claimed-printer guard around claim-code generation in register_printer(); the absence of a diff here likely reflects prior changes already merged rather than a true mismatch.

## 3. Applicable Business Rules

1. Rule 8 — Claim Code
   - Quoted sentence: "Claim Code: a **temporary** security token printed on the Welcome Page." and its sub-rules: "Expired or invalid claim codes must be rejected." and "A claim code can only be used once."
   - Relevance: Governs the basic validity checks in claim_printer(), including single-use and expiry, and underpins the acceptance criterion that valid, unused claim codes for unclaimed printers must still succeed.

2. Rule 9 — Claiming & Ownership
   - Quoted sentence: "A printer becomes visible to a user's applications only after a successful claim." 
   - Relevance: Establishes that claim_printer() is the gateway to associating printers with users, so its behaviour directly controls visibility and ownership transitions addressed by this ticket.

3. Rule 11 — Claiming & Ownership
   - Quoted sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Relevance: Directly supports the requirement that claiming must not allow hijacking an already-claimed printer and that registration must not issue new claim codes for already-CLAIMED printers, thereby preventing silent ownership overwrite.

## 4. Original Acceptance Criteria

Copied verbatim from jira_context/GOAR-8_live.md:

- "claim_printer() raises InvalidClaimCodeError if the target printer's
status is already CLAIMED."
- "Claiming an unclaimed printer with a valid, unused code still succeeds
(do not regress)."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Rejection of already-claimed printers must not depend on which user_id is provided.
   - Requirement: For a printer whose status is already CLAIMED, any call to claim_printer() with a valid, unused claim code must raise InvalidClaimCodeError regardless of whether the user_id matches the existing owner_user_id or is a different user.
   - Justification: edge case category — ownership conflicts. This ensures there is no path for either the existing owner or another user to re-claim or alter ownership via claim_printer() once the printer is already CLAIMED.

2. Registration must not generate a new claim code for already-CLAIMED printers.
   - Requirement: When register_printer() is called for a printer whose status is CLAIMED, it must not generate or assign a new claim_code; any existing claim_code (if present) remains marked used, and no fresh claim code is issued as part of re-registration.
   - Justification: Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Avoiding new claim code issuance for claimed printers reduces the risk of generating fresh, valid claim tokens that could be used to hijack already-owned printers.

3. Claiming with an expired claim code for an unclaimed printer must fail consistently.
   - Requirement: claim_printer() must always raise InvalidClaimCodeError when the current time is later than claim_code.expires_at, even if the printer is not yet CLAIMED and the claim code has never been used.
   - Justification: Rule 8 — "Expired or invalid claim codes must be rejected." This covers the boundary case where the printer is otherwise eligible for claiming but the claim code is no longer valid.

4. Claiming with a reused claim code for an unclaimed printer must fail consistently.
   - Requirement: claim_printer() must always raise InvalidClaimCodeError when target.claim_code.used is True, even if the printer's status is not CLAIMED (e.g., REGISTERED), and must not change owner_user_id or status in this case.
   - Justification: Rule 8 — "A claim code can only be used once." This enforces one-time use even if other state transitions (such as deregistration/re-registration) have occurred.

5. Registration rollback must preserve ownership while removing transient claim data.
   - Requirement: If register_printer() fails after a printer has become CLAIMED (e.g., during a re-registration path for a claimed printer) and triggers _rollback_registration(), the rollback process must not clear or alter owner_user_id for already-claimed printers, but must still ensure no new claim code remains usable after rollback.
   - Justification: Combination of Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." and Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Edge case category: rollback/partial-failure behaviour.

## 6. Flagged Conflicts

None identified. The original acceptance criteria are consistent with the cited business rules: rejecting claims on already-CLAIMED printers aligns with Rule 11's prohibition on silent ownership overwrite, and preserving successful claims for unclaimed printers with valid, unused codes aligns with Rule 8 and Rule 9.

## 7. Open Questions

1. Should claim_printer() allow idempotent claims by the existing owner when the printer is already CLAIMED?
   - Issue: The ticket requires claim_printer() to raise InvalidClaimCodeError if the target printer's status is already CLAIMED, but does not specify whether a call by the same owner_user_id should be considered an error or a no-op. The current implementation rejects all CLAIMED cases uniformly.
   - Why unresolvable: Neither jira_context/GOAR-8_live.md nor docs/business_rules.md addresses idempotent claiming semantics; the business rule only prohibits silent overwrite but does not define behaviour for identical-owner reclaims.
   - Exclude from scoring: Downstream agents focused on scenario design, test authoring, and automated validation (Agents 2–6) must exclude assumptions about idempotent same-owner claims.

2. Expected behaviour for claim codes after deregistration and re-registration of a previously claimed printer.
   - Issue: The ticket focuses on preventing hijack via claim_printer() and claim-code regeneration, but does not specify how claim codes should behave if a claimed printer is later deregistered and then re-registered (e.g., whether new claim codes may be issued in that lifecycle).
   - Why unresolvable: docs/business_rules.md Rule 13 addresses Cloud ID behaviour after deregistration but is silent on claim codes; the ticket text does not cover this lifecycle, and no additional documentation in the repo clarifies it.
   - Exclude from scoring: Agents designing extended lifecycle tests or deregistration/claiming interactions (Agents 3–6) must exclude scenarios involving deregistration + re-registration + claiming from scoring for this ticket.

3. Behaviour when claim_printer() is called for a printer whose status is DEREGISTERED but still has a residual claim_code object.
   - Issue: The models and store allow a PrinterStatus.DEREGISTERED state, but neither the ticket nor business_rules.md define whether claim_printer() should ignore or reject claim codes for such printers.
   - Why unresolvable: The current implementation never explicitly checks for PrinterStatus.DEREGISTERED in claim_printer(), and there is no rule text addressing this combination of status and claim code; making a decision here would be speculative.
   - Exclude from scoring: Agents 4–6 (test implementation and automated validation) must not treat any assumed DEREGISTERED-claim semantics as required behaviour for GOAR-8.

4. Observability requirements for claim-printer rejection events.
   - Issue: Business rule 14 requires registration failures to be observable with structured logging/telemetry, but does not explicitly state whether claim failures (e.g., InvalidClaimCodeError for already-CLAIMED) need comparable logging.
   - Why unresolvable: jira_context/GOAR-8_live.md and the current implementation do not mention logging for claim failures, and business rule 14 is scoped to registration; extending it to claiming would be an interpretation, not a stated requirement.
   - Exclude from scoring: Agents responsible for non-functional testing and observability checks (Agents 5–7) must exclude logging/telemetry behaviour for claim_printer() from scoring under this ticket.
