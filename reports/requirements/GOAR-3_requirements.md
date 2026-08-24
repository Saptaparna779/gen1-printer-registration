# Requirements Report — GOAR-3

## 1. Summary

Re-registering a printer with the same serial number after events such as a factory reset was incorrectly reusing the existing Cloud ID instead of generating a new one. This violated the GEN 1 business rule that every re-registration must receive a fresh Cloud ID and caused stale identifiers in downstream billing/subscription systems that key off Cloud ID. The fix ensures that every successful registration call, whether first-time or re-registration (including after deregistration), always assigns a brand-new Cloud ID while preserving other identity, ownership, and rollback behaviours defined in the business rules.

## 2. Affected Components

- app/registration.py — register_printer(), core registration logic reached via POST /printers/register (through the FastAPI routing layer in app/main.py).
  - Handles both first-time registrations and re-registrations based on serial_number lookup via store.get_printer_by_serial().
  - For existing printers, applies the GOAR-15 model-family checks and then updates model_number and firmware_version.
  - Always assigns a new Cloud ID by calling _generate_cloud_id() in the "Step 1: Cloud identity" block for every registration call, regardless of whether the printer is new or existing.
  - Always assigns a new printer_email_id via _generate_printer_email_id() and indexes it via store.index_email().
  - Assigns a new claim_code via _generate_claim_code() when the printer is not in PrinterStatus.CLAIMED.
  - Persists changes via store.save_printer(), captures capabilities (once per printer_id), assigns an XMPP node, prints the Welcome Page, and indexes the serial-to-printer_id mapping.

- tests/features/GOAR-3.feature — pytest-bdd feature file.
  - Defines Gherkin scenarios that exercise Cloud ID regeneration on re-registration, Printer Email ID and Claim Code regeneration, behaviour when re-registering claimed printers, repeated registrations, rollback after failed re-registration (Welcome Page failure), and re-registration after deregistration.

- tests/steps/test_GOAR-3_steps.py — pytest-bdd step definitions.
  - Uses POST /printers/register, POST /printers/claim, GET /printers/{printer_id}, and DELETE /printers/{printer_id} to validate the behaviours described in tests/features/GOAR-3.feature.
  - All steps run with a valid auth token provided by the shared client fixture; no unauthenticated or invalid-JWT scenarios are introduced by this ticket.

The GOAR-3 diff itself introduces only tests (feature file and step definitions). The implementation change to always regenerate Cloud IDs is already present in app/registration.py and is consistent with the ticket description and inline GOAR-3 comment in the Cloud identity block.

## 3. Applicable Business Rules

1. Rule 3 — Registration / Cloud ID behaviour
   - Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - Applicability: Directly governs the bug described in the ticket and the required behaviour of register_printer() on re-registration with the same serial_number.

2. Rule 6 — Cloud ID semantics
   - Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - Applicability: Defines Cloud ID properties and explicitly requires regeneration for every re-registration. The GOAR-3 change in register_printer() (always calling _generate_cloud_id()) enforces this.

3. Rule 7 — Printer Email ID uniqueness
   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."
   - Applicability: Supports the acceptance criterion that Printer Email ID regeneration on re-registration must remain correct and unaffected by the Cloud ID fix. The implementation’s _generate_printer_email_id() loop ensures a unique email is chosen before assignment.

4. Rule 8 — Claim Code semantics
   - Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."
   - Applicability: Governs Claim Code behaviour. GOAR-3 must not regress Claim Code generation, one-time use, or rejection semantics when changing Cloud ID behaviour.

5. Rule 11 — Claiming & Ownership guarantees
   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Applicability: Governs behaviour when re-registering already-claimed printers, ensuring that owner_user_id and claimed status are preserved even as Cloud IDs change.

6. Rule 2 — Registration rollback
   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - Applicability: Governs rollback when Welcome Page printing fails (including simulated failures in tests), ensuring that no stale Cloud IDs, printer records, or indexes remain after a failed registration or re-registration attempt.

7. Rule 13 — Re-registration after deregistration
   - Exact sentence: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)."
   - Applicability: Extends the Cloud ID regeneration requirement to the deregister-then-re-register path, which is explicitly covered by GOAR-3’s test scenarios.

## 4. Original Acceptance Criteria

Verbatim from jira_context/GOAR-3_live.md:

1. "Every call to register a printer -- first-time or re-registration -- generates a brand new Cloud ID."

2. "Printer Email ID and Claim Code continue to be regenerated on re-registration (unaffected, do not regress)."

## 5. Proposed Additional Requirements [PROPOSED -- NOT IN ORIGINAL TICKET]

1. Re-registration of a printer that is currently in status "CLAIMED" must issue a new Cloud ID while preserving the printer's status and owner_user_id.
   - Justification: Rule 11 — "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." Edge case category: ownership conflicts (re-registration of claimed printers).

2. Two consecutive re-registrations of the same serial number must result in three distinct Cloud IDs overall (initial registration + first re-registration + second re-registration), not merely a Cloud ID different from the immediately preceding one.
   - Justification: Rule 6 — "Cloud ID: system-generated, unique, regenerated on every re-registration." Edge case category: boundary values / repeated operations.

3. If a re-registration attempt fails before the Welcome Page prints and triggers rollback, the Cloud ID generated during that failed attempt must not be retained or reused, and any subsequent successful registration for the same serial number must still generate a fresh Cloud ID.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." Edge case category: rollback/partial-failure behaviour.

4. Re-registration after a prior deregistration of the same serial number must generate a new Cloud ID, distinct from any Cloud ID previously associated with that serial number.
   - Justification: Rule 13 — "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." Edge case category: post-deregistration state.

5. A failed re-registration attempt that is rolled back due to a Welcome Page print failure must fully remove the printer record and all indexes (printer_id, serial index, and email index), so that a subsequent registration behaves as a fresh registration.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." Edge case category: rollback/partial-failure behaviour.

## 6. Flagged Conflicts

None identified. The original acceptance criteria are consistent with the cited business rules:

- Rule 3 and Rule 6 explicitly require new Cloud IDs on every re-registration, which aligns with AC1.
- Rule 7 and Rule 8 require uniqueness and correct behaviour for Printer Email ID and Claim Code, which aligns with AC2’s requirement that their regeneration not regress.
- Rule 11 constrains re-registration behaviour around existing owners but does not contradict Cloud ID regeneration; instead, it adds a requirement to preserve ownership across Cloud ID changes.

## 7. Open Questions

1. Should Cloud ID regeneration occur for re-registration attempts on printers that are already in status "CLAIMED," or should some re-registrations of claimed printers be rejected outright to protect ownership semantics?
   - Why unresolvable: The business rules require that ownership not be silently overwritten (Rule 11), but do not explicitly state whether re-registration of a claimed printer should be allowed, disallowed, or conditioned on additional checks. The GOAR-3 ticket and current tests assume that claimed printers can be re-registered and still receive a new Cloud ID while preserving ownership, but this assumption is not explicitly confirmed in the business rules.
   - Downstream exclusion: Scenario-design, test-generation, and scoring agents (agents 3–7) must not treat the precise handling of re-registration for claimed printers (allowed vs. rejected) as a scored requirement beyond what is explicitly tested in GOAR-3.

2. After re-registration generates a new Cloud ID, what should be the lifecycle of the old Cloud ID with respect to downstream systems that may still hold references to it (for example, should it immediately become invalid, or should there be a grace period)?
   - Why unresolvable: The business rules state that "the old identity is not reused" but do not specify whether lookups by the old Cloud ID should return a specific error, redirect to the new Cloud ID, or be silently dropped. The Jira ticket mentions stale references in downstream billing/subscription systems but does not specify the desired downstream behaviour.
   - Downstream exclusion: Agents responsible for cross-service integration tests and end-to-end subscription/billing flows must exclude assumptions about old Cloud ID handling from scoring.

3. For printers that have been deregistered and then re-registered, should any historical linkage between the old and new Cloud IDs be retained for audit or analytics purposes, or must all such links be removed to satisfy GDPR and related data-minimization principles?
   - Why unresolvable: Rule 12 requires removal of all cloud associations and printer data on deregistration, which may imply that historical linkages should also be removed, but it does not explicitly mention analytical or audit archives. The Jira ticket and current implementation do not cover this.
   - Downstream exclusion: Compliance/audit-focused agents and any analytics-related test generation must not assume a particular historical-link behaviour when scoring.

4. How should concurrent or near-simultaneous re-registration requests for the same serial_number be handled, and what guarantees (if any) are required about the uniqueness and ordering of Cloud IDs in such race conditions?
   - Why unresolvable: The business rules require uniqueness and regeneration but do not discuss concurrency or race conditions. The current implementation and tests assume sequential operations; the Jira ticket does not mention concurrent flows.
   - Downstream exclusion: Performance/concurrency-focused agents must not score behaviour under concurrent re-registration beyond basic uniqueness guarantees provided by UUID-based Cloud ID generation.

5. Should a failed registration or re-registration attempt that is rolled back log a distinct error code or structured field indicating that the failure was due to a Welcome Page print error, versus other types of registration failures?
   - Why unresolvable: Rule 14 ("Registration failures should be observable (structured logging / telemetry), not silent") requires observability but does not prescribe specific log schemas or error codes. The Jira ticket and current implementation include logging but do not define a standard schema for differentiating failure causes.
   - Downstream exclusion: Logging/observability scoring agents must not assume specific log field names or error codes for Welcome Page failures when scoring.
