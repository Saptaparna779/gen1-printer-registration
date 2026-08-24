# Requirements Report — GOAR-3



## 1. Summary

Re-registering a printer with the same serial number after events such as a factory reset was incorrectly reusing the existing Cloud ID instead of generating a new one. This violated the GEN 1 business rule that every re-registration must receive a fresh Cloud ID and caused stale identifiers in downstream billing/subscription systems that key off Cloud ID. The fix ensures that every successful registration call, whether first-time or re-registration (including after deregistration), always assigns a brand-new Cloud ID while preserving other identity and ownership behaviours.



## 2. Affected Components

- app/main.py — register_printer() endpoint handler, reached via POST /printers/register.
  - Constructs RegisterRequest objects and delegates to app.registration.register_printer().
  - Returns the printer_id, cloud_id, printer_email_id, claim_code, claim_code_expires_at, xmpp_node, status, and history fields from the Printer domain object.

- app/registration.py — register_printer() core registration logic, reached indirectly via POST /printers/register.
  - Handles both first-time registrations and re-registrations based on serial_number lookup via store.get_printer_by_serial().
  - For existing printers, updates model_number and firmware_version (including GOAR-15 model-family checks) and then always assigns a new Cloud ID by calling _generate_cloud_id(), per the inline GOAR-3 comment.
  - Generates a new printer_email_id via _generate_printer_email_id() and indexes it via store.index_email().
  - Generates a new claim_code via _generate_claim_code() when the printer is not in PrinterStatus.CLAIMED.
  - Persists changes via store.save_printer(), captures capabilities, assigns an XMPP node, prints the Welcome Page, and indexes the serial-to-printer_id mapping.

- tests/features/GOAR-3.feature — pytest-bdd feature file, exercised via tests/steps/test_GOAR-3_steps.py.
  - Defines Gherkin scenarios covering first-time registration, re-registration, claimed-printer re-registration, multiple re-registrations, re-registration after a failed attempt, and re-registration after deregistration, all focused on Cloud ID, Printer Email ID, Claim Code, ownership, and rollback behaviours.

- tests/steps/test_GOAR-3_steps.py — pytest-bdd step definitions, calling the live HTTP API via the TestClient fixture.
  - Uses POST /printers/register, POST /printers/claim, GET /printers/{printer_id}, and DELETE /printers/{printer_id} to validate Cloud ID regeneration, printer_email_id and claim_code regeneration, claimed-printer status/ownership preservation, rollback on Welcome Page failure, and re-registration after deregistration.
  - All steps are executed with a valid auth token provided by tests/conftest.py, so no unauthenticated behaviour is in scope for this ticket.

There is no disagreement between the diff and the implementation: the diff for GOAR-3 only adds tests, while the app/registration.py file already contains the GOAR-3 comment and behaviour (always generating a new Cloud ID for every registration call) in the Cloud identity block.



## 3. Applicable Business Rules

1. Rule 3 — Registration / Cloud ID
   - Exact sentence: "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused."
   - Applicability: Directly governs the core bug: re-registration with the same serial number must never reuse the previous Cloud ID. The ticket’s bug description and acceptance criteria restate this rule.

2. Rule 6 — Cloud ID semantics
   - Exact sentence: "Cloud ID: system-generated, unique, regenerated on every re-registration."
   - Applicability: Defines Cloud ID properties and explicitly ties uniqueness and regeneration to every re-registration, which the implementation enforces by always calling _generate_cloud_id() in the Cloud identity block for both first-time registration and re-registration.

3. Rule 7 — Printer Email ID uniqueness
   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print."
   - Applicability: Supports the acceptance criterion that Printer Email ID regeneration on re-registration must remain correct and unaffected by the Cloud ID fix. The implementation’s _generate_printer_email_id() loop ensures uniqueness before assigning a new printer_email_id.

4. Rule 8 — Claim Code semantics
   - Exact sentence: "Claim Code: a **temporary** security token printed on the Welcome Page.\n   - Expired or invalid claim codes must be rejected.\n   - A claim code can only be used once."
   - Applicability: Governs Claim Code behaviour, which must remain correct when re-registration regenerates claim_code for unclaimed printers. Tests validate that claim_code is regenerated and follows the expected format without regressing the one-time-use semantics enforced in claim_printer().

5. Rule 11 — Claiming & Ownership
   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer."
   - Applicability: Governs the requirement that re-registration of a claimed printer must not alter its claimed status or owner_user_id, even though a new Cloud ID is issued. The tests for claimed-printer re-registration explicitly exercise this scenario.

6. Rule 12 — Deregistration data removal
   - Exact sentence: "Deregistration must remove all cloud associations and printer data (GDPR compliance)."
   - Applicability: Governs the behaviour of deregister_printer() and the test scenarios where re-registration after deregistration must start from a clean slate.

7. Rule 13 — Re-registration after deregistration
   - Exact sentence: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)."
   - Applicability: Extends the Cloud ID regeneration requirement to the deregister-then-re-register path, which is explicitly covered by the GOAR-3 test scenarios.

8. Rule 2 — Registration rollback
   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained."
   - Applicability: Governs behaviour under simulated Welcome Page failure, requiring that failed re-registrations not leave stale Cloud IDs or printer records behind. The GOAR-3 tests validate rollback by verifying that the printer record is removed and that Cloud ID from the failed attempt is not retained.



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

5. A failed re-registration attempt that is rolled back due to a simulated Welcome Page failure must fully remove the printer record and all indexes (printer_id, serial index, and email index), so that a subsequent registration behaves as a fresh registration.
   - Justification: Rule 2 — "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." Edge case category: rollback/partial-failure behaviour.

6. All Cloud ID generation, re-registration, rollback, and deregistration events must be logged in a way that supports structured telemetry and post-incident analysis.
   - Justification: Rule 14 — "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." Edge case category: non-functional logging/observability.



## 6. Flagged Conflicts

None identified. The original acceptance criteria are fully consistent with the cited business rules:

- Rule 3 and Rule 6 explicitly require new Cloud IDs on every re-registration, which aligns with AC1.
- Rule 7 and Rule 8 require uniqueness and correct behaviour for Printer Email ID and Claim Code, which aligns with AC2’s requirement that their regeneration not regress.
- Rule 11 constrains re-registration behaviour around existing owners but does not contradict Cloud ID regeneration; instead, it adds a requirement to preserve ownership across Cloud ID changes.



## 7. Open Questions

1. Should Cloud ID regeneration occur for re-registration attempts on printers that are already in status "CLAIMED," or should some re-registrations of claimed printers be rejected outright to protect ownership semantics?
   - Why unresolvable: The business rules require that ownership not be silently overwritten (Rule 11), but do not explicitly state whether re-registration of a claimed printer should be allowed, disallowed, or conditioned on additional checks. The GOAR-3 ticket and tests assume that claimed printers can be re-registered and still receive a new Cloud ID while preserving ownership, but this is an assumption rather than a clearly stated rule.
   - Downstream exclusion: Scenario-design, test-generation, and scoring agents (agents 3–7) must not treat the precise handling of re-registration for claimed printers (allowed vs. rejected) as a scored requirement beyond what is explicitly tested in GOAR-3.

2. After re-registration generates a new Cloud ID, what should be the lifecycle of the old Cloud ID with respect to downstream systems that may still hold references to it (e.g., should it immediately become invalid, or should there be a grace period)?
   - Why unresolvable: The business rules state that "the old identity is not reused" but do not specify whether lookups by the old Cloud ID should return a specific error, redirect to the new Cloud ID, or be silently dropped. The Jira ticket mentions stale references in downstream billing/subscription systems but does not specify the desired downstream behaviour.
   - Downstream exclusion: Agents responsible for cross-service integration tests and end-to-end subscription/billing flows must exclude assumptions about old Cloud ID handling from scoring.

3. For printers that have been deregistered and then re-registered, should any historical linkage between the old and new Cloud IDs be retained for audit or analytics purposes, or must all such links be removed to satisfy GDPR and related data-minimization principles?
   - Why unresolvable: Rule 12 requires removal of all cloud associations and printer data on deregistration, which may imply that historical linkages should also be removed, but it does not explicitly mention analytical/audit archives or anonymized metrics. The Jira ticket and current implementation do not cover this.
   - Downstream exclusion: Compliance/audit-focused agents and any analytics-related test generation must not assume a particular historical-link behaviour when scoring.

4. How should concurrent or near-simultaneous re-registration requests for the same serial_number be handled, and what guarantees (if any) are required about the uniqueness and ordering of Cloud IDs in such race conditions?
   - Why unresolvable: The business rules require uniqueness and regeneration but do not discuss concurrency or race conditions. The current implementation and tests assume sequential operations; the Jira ticket does not mention concurrent flows.
   - Downstream exclusion: Performance/concurrency-focused agents must not score behaviour under concurrent re-registration beyond basic uniqueness guarantees, which are already enforced by the Cloud ID format.

5. Should a failed re-registration attempt that is rolled back log a distinct error code or structured field indicating that the failure was due to a simulated or real Welcome Page print error, versus other types of registration failures?
   - Why unresolvable: Rule 14 requires observability and structured logging/telemetry, but does not prescribe specific log schemas or error codes. The Jira ticket and current implementation include logging but do not define a standard schema for differentiating failure causes.
   - Downstream exclusion: Logging/observability scoring agents must not assume specific log field names or error codes for Welcome Page failures when scoring.

