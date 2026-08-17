# Requirements Report — GOAR-15

## 1. Summary

Re-registration of an existing printer (same serial number) was previously allowed to overwrite the stored `model_number` and `firmware_version` with no spoofing protection. This meant a completely different physical device could reuse a serial number, silently changing the printer identity tied to that serial and potentially impacting ownership and downstream systems.

GOAR-15 introduces validation and observability to this path: any change to `model_number` on re-registration is logged and flagged for review, and a change to a materially different model family is rejected outright. Legitimate re-registrations with matching or compatible model/firmware data (including for already-claimed printers) must continue to succeed and behave consistently with the core registration business rules.

## 2. Affected Components

From the diff and implementation:

- `tests/features/GOAR-15.feature`
  - New Gherkin feature file defining scenarios for GOAR-15 behaviour, including model change logging, model-family rejection, auth failures, claimed-printer re-registration, structured logging, and rollback behaviour.

- `tests/steps/test_GOAR-15_steps.py`
  - New pytest-bdd step definitions implementing the GOAR-15 feature scenarios via real HTTP calls to the FastAPI app.

- `app/registration.py`
  - `logger = logging.getLogger(__name__)` — module-level logger for structured warning logs (GOAR-15 observability).
  - `_model_family(model_number: str) -> str` — new helper that normalizes the `model_number` via `strip().upper()` and extracts a crude "model family" (everything except the last dash-separated segment, or the whole string if no dash).
  - `register_printer()` — updated re-registration logic for existing printers:
    - Compares normalized existing vs incoming `model_number` using `strip().upper()`.
    - Logs a history entry and `logger.warning` when the normalized model changes, including structured fields `serial_number`, `old_model`, and `new_model` via the `extra` dict.
    - Uses `_model_family()` to detect materially different model families and raises `RegistrationError` with a specific detail message when families differ.
    - Preserves subsequent registration steps (Cloud ID, email, capabilities, XMPP, welcome page, rollback) unchanged.

## 3. Applicable Business Rules

The following rules from `docs/business_rules.md` clearly apply to GOAR-15:

1. **Registration Rollback and Completeness**

   - Exact sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)

   - Relation to this ticket:
     - GOAR-15’s rejection of a materially different model family must behave like a pre-Welcome-Page failure: it must not leave partial state (new Cloud ID, capabilities, email, XMPP, or serial index) in the system. The new tests explicitly assert that rejected re-registrations leave Cloud ID, printer email, XMPP node, and history unchanged apart from the review-flag entry, aligning with this rollback requirement.

2. **Cloud ID on Re-registration**

   - Exact sentences:
     - "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." (Rule 3)
     - "Cloud ID: system-generated, unique, regenerated on every re-registration." (Rule 6)

   - Relation to this ticket:
     - GOAR-15 introduces additional checks before registration succeeds. For legitimate re-registrations that pass the new spoofing protection, these rules still require that a new Cloud ID be generated. The scenarios like "Re-registering with a same-family but different revision is accepted" and "Re-registering with matching model number and updated firmware completes end-to-end" assert that a new Cloud ID is present and different from the original, ensuring the existing Cloud ID behaviour is preserved.

3. **Printer Email ID Uniqueness and Behaviour**

   - Exact sentence: "Printer Email ID: must be globally unique; used for Email-to-Print." (Rule 7)

   - Relation to this ticket:
     - GOAR-15 does not change email generation logic, but its scenarios assert that successful re-registrations issue a new printer email address different from the original. Rejected re-registrations must not accidentally issue or change printer email IDs, preserving uniqueness and avoiding partial side effects.

4. **Claim Code Semantics and Single-Use Behaviour**

   - Exact sentences:
     - "Claim Code: a **temporary** security token printed on the Welcome Page." (Rule 8)
     - "Expired or invalid claim codes must be rejected." (Rule 8)
     - "A claim code can only be used once." (Rule 8)

   - Relation to this ticket:
     - GOAR-15 introduces tests around claiming behaviour and auth, including claimed printers that are re-registered. While the core claim-code logic is not changed in this diff, scenarios like "Re-registering a claimed printer with an unchanged model number preserves ownership" rely on claim-code semantics being honoured and on the fact that only successful registrations that reach the welcome page print should produce usable claim codes.

5. **Claiming & Ownership Protections**

   - Exact sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)

   - Relation to this ticket:
     - GOAR-15 explicitly tests the re-registration behaviour for claimed printers, ensuring that:
       - When an already-claimed printer is re-registered with an unchanged model number or a same-family change, ownership and status remain "CLAIMED".
       - Model-family mismatch re-registrations are rejected, and their side effects are limited to review-flag history entries, leaving ownership untouched.
     - This aligns with the rule’s requirement that re-registration must not silently disrupt existing claims.

6. **Deregistration and Re-registration Cloud Behaviour**

   - Exact sentence: "Re-registration after deregistration always generates a new Cloud ID (per rule 3/6)." (Rule 13)

   - Relation to this ticket:
     - GOAR-15 scopes its tests to re-registration of existing printers, including claimed ones, but does not directly address the deregister-then-reregister path. However, the unchanged `register_printer()` logic for successful re-registrations still complies with this rule: any re-registration, including after a prior deregistration, will generate a new Cloud ID as long as it passes the spoofing protection.

7. **Non-Functional Expectations / Observability**

   - Exact sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." (Rule 14)

   - Relation to this ticket:
     - GOAR-15 is primarily about observability and detection of suspicious re-registrations. The diff introduces a module-level logger and warning logs for model number changes, including structured fields. The Gherkin scenarios and step definitions verify that these logs are emitted and carry discrete attributes (`serial_number`, `old_model`, `new_model`), fulfilling the structured logging requirement.

## 4. Original Acceptance Criteria

Copied from `jira_context/GOAR-15_live.md`:

> When re-registering an existing serial number, register_printer() updates
> model_number and firmware_version on the existing record with no
> validation that this looks like the same physical device. A completely
> different model_number could silently overwrite the original identity
> tied to that serial number, with no protection against serial-number
> reuse or spoofing across different physical printers.
> Acceptance Criteria:
> At minimum, a re-registration that changes model_number from what was
> previously recorded is flagged/logged as a notable event for review.
> (Stretch) Re-registration with a materially different model family is
> rejected or requires explicit confirmation.
> Legitimate re-registrations with matching or compatible model/firmware
> data continue to work as before.

## 5. Adopted Additional Requirements

The following additions are derived strictly from `docs/business_rules.md` or from recognised edge case categories. They are to be treated as in-scope acceptance criteria for GOAR-15.

1. **Normalized Model-Number Comparison for Change Detection**

   - Requirement statement:
     - The model-number change check in `register_printer()` must compare normalized model numbers (e.g., both values passed through `.strip().upper()`) so that case- or whitespace-only differences (e.g., `"HP-LJ-2055"` vs `" hp-lj-2055"`) do not trigger a model-change flag or warning log.

   - Justification:
     - Edge case category: boundary values / input normalization.
     - This requirement ensures that GOAR-15’s behaviour aligns with its own intent and tests (e.g., scenarios that treat case/whitespace-only differences as unchanged). It prevents spurious "model changed" events for purely presentational differences, which would undermine the value of the review flag.

2. **Model-Family Definition Must Be Stable and Documented Before Expanding Scope**

   - Requirement statement:
     - For GOAR-15, the `_model_family()` helper may use a crude `strip().upper().split("-")` heuristic, but any decision to broaden or harden rejection behaviour based on model families (beyond the scenarios explicitly covered in `tests/features/GOAR-15.feature`) must be accompanied by a documented, stable definition of "model family" (e.g., a catalog lookup or configuration file) so that QA can validate expected mappings.

   - Justification:
     - Edge case category: boundary values / classification consistency.
     - While not mandated by a specific business rule sentence, this requirement constrains future use of `_model_family()` to avoid arbitrary or inconsistent rejections. The existing scenarios already note that the heuristic is crude and that a real implementation would use a proper catalog.

3. **No Partial Side Effects on Rejected Re-registrations**

   - Requirement statement:
     - When a re-registration is rejected due to a model-family mismatch, the system must not create or alter any Cloud ID, printer email ID, XMPP node, capabilities record, or serial index for that printer; the only allowed state change is a history entry flagging the attempted model-number change for review.

   - Justification:
     - Exact rule sentence: "If any step fails **before** the Welcome Page prints, the entire registration must roll back — no partial data (printer record, capability record, serial index, etc.) may be retained." (Rule 2)
     - This requirement makes explicit that GOAR-15’s rejection path is a pre-Welcome-Page failure and must honour the rollback semantics by avoiding partial side effects.

4. **Preservation of Ownership and Claim Status on Legitimate Re-registrations**

   - Requirement statement:
     - For printers with status `CLAIMED`, legitimate re-registrations (unchanged or same-family `model_number`) must preserve `owner_user_id` and `status` as `CLAIMED`. No re-registration path may silently clear, reassign, or downgrade ownership.

   - Justification:
     - Exact rule sentence: "Registration/re-registration logic must never silently overwrite or wipe out an existing owner's claim on a printer." (Rule 11)
     - GOAR-15’s scenarios around claimed-printer re-registration embody this rule; this requirement formalizes it as acceptance criteria.

5. **Structured Warning Logs for Model-Number Changes**

   - Requirement statement:
     - Each model-number change on re-registration must emit at least one warning log record that:
       - Has a stable message key (e.g., includes "GOAR-15: model_number changed on re-registration"), and
       - Carries discrete attributes `serial_number`, `old_model`, and `new_model` (attached via the logging `extra` mechanism) so that downstream systems can query and aggregate these events.

   - Justification:
     - Exact rule sentence: "Registration failures should be observable (structured logging / telemetry), not silent — see BUD Section 10, \"Limited observability\" as a known platform risk." (Rule 14)
     - While a model-number change is not itself a failure, it is a suspicious event that must be observable. Structured logging with discrete fields enables telemetry and monitoring in line with Rule 14.

6. **Cloud ID, Email, and XMPP Behaviour on Successful GOAR-15 Re-registrations**

   - Requirement statement:
     - For any successful re-registration (unchanged or same-family `model_number`):
       - A new Cloud ID must be generated and differ from the previous Cloud ID.
       - A new printer email ID must be generated and differ from the previous printer email ID.
       - An XMPP node must be assigned if one was not already present.

   - Justification:
     - Exact rule sentences:
       - "Re-registering a printer (same serial number) **always generates a new Cloud ID** — the old identity is not reused." (Rule 3)
       - "Cloud ID: system-generated, unique, regenerated on every re-registration." (Rule 6)
       - "Printer Email ID: must be globally unique; used for Email-to-Print." (Rule 7)
       - "A printer is assigned an XMPP node as part of registration, enabling persistent cloud connectivity." (Rule 5)
     - GOAR-15 must not weaken these behaviours; this requirement ties the new validation path to the existing identity and connectivity rules.

## 6. Open Questions

The following questions cannot be resolved purely from the Jira ticket, diff, and business rules. Downstream agents (scenario designers, test generators, and scorers) must treat these as out of scope until clarified and must not score behaviours that depend on them.

1. **Firmware-Version Spoofing Protection**

   - Question:
     - Should changes to `firmware_version` on re-registration trigger logging, validation, or rejection similar to `model_number` changes, particularly when the new firmware version appears inconsistent with the model family or previous version?

   - Why it cannot be resolved:
     - The Jira description mentions that both `model_number` and `firmware_version` are updated with no validation, but the acceptance criteria and diff focus exclusively on `model_number`. `docs/business_rules.md` does not mention firmware version at all.

   - Downstream exclusions:
     - Do not design, generate, or score tests that assume specific validation or logging behaviour for `firmware_version` changes beyond existing generic registration behaviour.

2. **Explicit Confirmation vs. Hard Rejection for Different Model Families**

   - Question:
     - The acceptance criteria say that re-registration with a materially different model family is "rejected or requires explicit confirmation." Is the intended long-term behaviour a hard rejection (as implemented) or an interactive confirmation flow (e.g., a separate endpoint, UI, or token-based override), and if the latter, what are its semantics?

   - Why it cannot be resolved:
     - The current implementation only provides hard rejection via `RegistrationError`; there is no confirmation mechanism described in the ticket or present in the codebase. The business rules do not discuss confirmation flows.

   - Downstream exclusions:
     - Do not design or score tests that assume the existence of an explicit confirmation mechanism, nor tests that treat hard rejection as definitively the only allowed behaviour for different-family re-registrations.

3. **Model-Family Catalog and Long-Term Definition**

   - Question:
     - What is the authoritative definition of a "model family" for production use (e.g., HP’s internal catalog, a configuration file, or a naming convention), and how should `_model_family()` be aligned with it?

   - Why it cannot be resolved:
     - The docstring for `_model_family()` explicitly describes it as "crude" and notes that "a real implementation would use a proper model catalog/lookup." No such catalog or mapping is present in this repository, nor described in the business rules.

   - Downstream exclusions:
     - Do not design or score tests that rely on a broader or different interpretation of model families than the specific examples covered in `tests/features/GOAR-15.feature`. Treat `_model_family()`’s current heuristic as the only authoritative mapping for GOAR-15.

4. **Claimed-Printers: Stricter Behaviour on Model-Number Changes**

   - Question:
     - For printers with status `CLAIMED`, should any `model_number` change (even within the same family) be rejected or blocked pending explicit confirmation, given the higher sensitivity around ownership and billing, or is logging and preserving ownership sufficient?

   - Why it cannot be resolved:
     - Business Rule 11 prohibits silently wiping out a claim but does not specify whether claimed printers should be subject to stricter validation than unclaimed ones. The current implementation treats claimed and unclaimed printers identically in the GOAR-15 logic, and the ticket does not mention special handling for claimed printers beyond "legit re-registrations ... continue to work as before."

   - Downstream exclusions:
     - Do not design or score tests that assume stricter rejection or confirmation logic for claimed printers beyond what is explicitly implemented (i.e., same-family changes logged and accepted, different-family changes rejected).

5. **Downstream Review and Alerting Pipeline for Logged Events**

   - Question:
     - Which downstream system (e.g., logging backend, SIEM, ops dashboard) is expected to consume and act on the GOAR-15 warning logs, and are there specific formatting or tagging requirements beyond `serial_number`, `old_model`, and `new_model`?

   - Why it cannot be resolved:
     - Business Rule 14 requires observability via structured logging/telemetry but says nothing about specific consumers or formats. The repository contains no configuration or documentation for log ingestion or alerting.

   - Downstream exclusions:
     - Do not design or score tests that depend on external log-consumer behaviour (alerts, tickets, dashboards). Limit validation to the presence and structure of log records within the application’s own logging framework.
