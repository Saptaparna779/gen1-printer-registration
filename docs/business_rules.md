# Business Rules — Printer Onboarding & Registration

Extracted from the GEN 1 Business & Functional Understanding Document,
Section 11.1–11.3. This file exists so the agentic workflow (Copilot /
Claude) has grounded, authoritative context when generating or validating
tests — instead of inferring expected behaviour purely from code.

## Registration

1. Registration is successful **only if** the Welcome/Info Page prints.
2. If any step fails **before** the Welcome Page prints, the entire
   registration must roll back — no partial data (printer record,
   capability record, serial index, etc.) may be retained.
3. Re-registering a printer (same serial number) **always generates a new
   Cloud ID** — the old identity is not reused.
4. Printer capabilities are captured once at registration time so
   downstream services never need to re-query the device.
5. A printer is assigned an XMPP node as part of registration, enabling
   persistent cloud connectivity.

## Cloud ID, Printer Email ID & Claim Code

6. Cloud ID: system-generated, unique, regenerated on every
   re-registration.
7. Printer Email ID: must be globally unique; used for Email-to-Print.
8. Claim Code: a **temporary** security token printed on the Welcome Page.
   - Expired or invalid claim codes must be rejected.
   - A claim code can only be used once.

## Claiming & Ownership

9. A printer becomes visible to a user's applications only after a
   successful claim.
10. Claiming enables subscriptions (e.g. Instant Ink) and remote
    management.
11. Registration/re-registration logic must never silently overwrite or
    wipe out an existing owner's claim on a printer.

## Deregistration

12. Deregistration must remove all cloud associations and printer data
    (GDPR compliance).
13. Re-registration after deregistration always generates a new Cloud ID
    (per rule 3/6).

## Non-Functional Expectations

14. Registration failures should be observable (structured logging /
    telemetry), not silent — see BUD Section 10, "Limited observability"
    as a known platform risk.
