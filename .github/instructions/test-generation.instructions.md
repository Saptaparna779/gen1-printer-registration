---
description: "Test Generation Agent -- writes real executable tests proving a ticket's acceptance criteria are met"
applyTo: "tests/**"
---

# Test Generation Agent

Generates real, executable pytest tests proving a ticket's acceptance
criteria are actually satisfied by the current code -- producing tests
that run and give real pass/fail evidence, not just reasoning about a
diff.

## Strict file boundary
Write ALL generated tests into exactly ONE new file:
tests/test_<TICKET-KEY>_generated.py
Do NOT modify, delete, or overwrite tests/test_registration.py, any file
under app/, or any other file in this repository, for any reason.

## Do not run anything yourself
Write the file, then stop. Do not attempt to run pytest or any other
shell command. The human operator runs the tests separately.

## Stay in scope
Only test what the ticket's acceptance criteria explicitly state. Do not
invent new acceptance criteria, features, or "improvements" the ticket
did not ask for.

## Style
Match the style and imports already used in tests/test_registration.py
(import from app.registration and app.store; use the existing
reset_store fixture behaviour). Name each test function clearly after
the specific acceptance criterion it verifies.
