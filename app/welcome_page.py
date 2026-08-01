"""
Mock of the Welcome / Information Page print job — see BUD section 11.1.

Per business rule: "Registration is successful only if the Welcome Page
prints." This module simulates that final checkpoint. In this demo, callers
can force a failure via `force_failure` to exercise rollback behaviour.
"""


class WelcomePagePrintError(Exception):
    """Raised when the Welcome / Info page fails to print."""


def generate_and_print_welcome_page(
    printer_id: str,
    cloud_id: str,
    printer_email_id: str,
    claim_code: str,
    force_failure: bool = False,
) -> bool:
    """
    Simulate rendering + printing the Welcome/Info page.

    Returns True on success. Raises WelcomePagePrintError on failure so
    callers are forced to handle the rollback path explicitly.
    """
    if force_failure:
        raise WelcomePagePrintError(
            f"Welcome page failed to print for printer_id={printer_id}"
        )
    # In a real system this would render the page (with cloud_id,
    # printer_email_id, claim_code) and send it as a print job over XMPP.
    return True
