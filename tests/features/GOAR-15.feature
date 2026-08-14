# Sanity coverage for GOAR-15. Every test case in
# reports/testcases/GOAR-15_test_cases.md (TC-GOAR-15-01 through
# TC-GOAR-15-20) has a corresponding Scenario below -- none were skipped.
#
# Notes carried forward from the test-case report:
# - TC-GOAR-15-10 (AC #5) can only be checked against the current crude
#   `_model_family()` heuristic, since no authoritative model-family
#   catalog exists in this repo yet; it is expressed as a Scenario Outline
#   so each sample pair is its own single-action Given/When/Then instance.
# - TC-GOAR-15-17 (AC #7) depends on server-side log capture (pytest's
#   caplog) in addition to the HTTP response, since structured log fields
#   are not exposed in any response body.
# - TC-GOAR-15-20 (AC #8 boundary) can only verify "no capabilities
#   re-captured" indirectly, via the absence of new capability-related
#   history entries, since no endpoint returns PrinterCapabilities.

Feature: Re-registration flags and gates model number changes
  Re-registering an existing printer must no longer silently overwrite
  its model number with no validation. Any model number change on
  re-registration is now logged and flagged for review, and a change to
  a materially different model family is rejected outright, so a serial
  number cannot be quietly reused by a different physical device. Legit
  same-model and same-family re-registrations, including for already
  claimed printers, continue to succeed as before, and a rejected
  re-registration leaves no partial side effects behind.

  Scenario: Re-registering with a changed model number flags it for review and logs a warning
    Given a printer has been registered with serial number "SN-15001", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15001", model number "HP-LJ-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the registration history records the model number change from "HP-LJ-4200" to "HP-LJ-4250" and flags it for review
    And a warning is logged mentioning serial number "SN-15001", old model "HP-LJ-4200", and new model "HP-LJ-4250"

  Scenario: Registering a printer with no Authorization header is rejected
    When a registration request for serial number "SN-15002" is submitted with no Authorization header
    Then the request is rejected as missing the authorization header

  Scenario: Registering a printer with an invalid bearer token is rejected
    When a registration request for serial number "SN-15003" is submitted with an invalid Authorization token
    Then the request is rejected as unauthorized due to an invalid token

  Scenario: Re-registering with an unchanged model number is not flagged
    Given a printer has been registered with serial number "SN-15004", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15004", model number "HP-LJ-4200", and firmware version "1.0.1"
    Then the re-registration succeeds
    And the registration history shows no model number change and no flag for review, only the standard re-registration entries
    And no warning is logged

  Scenario: Re-registering with a materially different model family is rejected
    Given a printer has been registered with serial number "SN-15005", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15005", model number "HP-C-MFP-9500", and firmware version "1.0.0"
    Then the re-registration is rejected as a model family mismatch between "HP-LJ-4200" and "HP-C-MFP-9500"

  Scenario: Re-registering with a same-family but different revision is accepted
    Given a printer has been registered with serial number "SN-15006", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15006", model number "HP-LJ-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the printer status is "REGISTERED"
    And a new Cloud ID is present
    And the registration history records the model number change from "HP-LJ-4200" to "HP-LJ-4250" and flags it for review

  Scenario: Re-registering with matching model number and updated firmware completes end-to-end
    Given a printer has been registered with serial number "SN-15007", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15007", model number "HP-LJ-4200", and firmware version "2.1.0"
    Then the re-registration succeeds with a new Cloud ID different from the original
    And a new printer email address is issued, different from the original
    And an XMPP node is assigned
    And the printer status is "REGISTERED"
    And the registration history shows capability capture, XMPP assignment, and a successful welcome page print, with no model-number flag

  Scenario: Re-registering with a differently-cased same-family model number still succeeds
    Given a printer has been registered with serial number "SN-15008", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15008", model number "hp-lj-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the registration history records the model number change from "HP-LJ-4200" to "hp-lj-4250" and flags it for review

  Scenario: Re-registering with only whitespace/case differences in model number is treated as unchanged
    Given a printer has been registered with serial number "SN-15009", model number "HP-LJ-2055", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15009", model number " hp-lj-2055", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the registration history shows no model number change and no flag for review, only the standard re-registration entries

  Scenario Outline: Model-family classification is consistent across representative model number pairs
    Given a printer has been registered with serial number "<serial>", model number "<existing>", and firmware version "1.0.0"
    When the printer is re-registered with serial number "<serial>", model number "<incoming>", and firmware version "1.0.0"
    Then the re-registration outcome is "<outcome>"

    Examples:
      | serial      | existing      | incoming      | outcome  |
      | SN-15010-1  | HP-LJ-4200    | HP-LJ-4250    | accepted |
      | SN-15010-2  | HP-C-MFP-9500 | HP-C-MFP-9999 | accepted |
      | SN-15010-3  | HP-OJ-6975    | HP-OJ-9015    | accepted |
      | SN-15010-4  | HP-LJ-4200    | HP-OJ-6975    | rejected |
      | SN-15010-5  | HP-C-MFP-9500 | HP-LJ-4200    | rejected |
      | SN-15010-6  | LASERJET      | LASERJET2     | rejected |

  Scenario: Re-registering a claimed printer with an unchanged model number preserves ownership
    Given a printer has been registered and claimed: serial number "SN-15011", model number "HP-LJ-4200", and firmware version "1.0.0", claimed by user "user-goar15-a"
    When the printer is re-registered with serial number "SN-15011", model number "HP-LJ-4200", and firmware version "1.1.0"
    Then the re-registration succeeds
    And the printer status is "CLAIMED"
    And a new Cloud ID is present
    And the registration history shows no model number change and no flag for review, only the standard re-registration entries
    And looking up the printer shows its owner is still "user-goar15-a" and status is still "CLAIMED"

  Scenario: Claiming a printer with no Authorization header is rejected
    When a claim request is submitted with no Authorization header
    Then the request is rejected as missing the authorization header

  Scenario: Claiming a printer with an invalid bearer token is rejected
    When a claim request is submitted with an invalid Authorization token
    Then the request is rejected as unauthorized due to an invalid token

  Scenario: Looking up a printer with no Authorization header is rejected
    Given a printer has been registered with serial number "SN-15014", model number "HP-LJ-4200", and firmware version "1.0.0"
    When looking up that printer with no Authorization header
    Then the request is rejected as missing the authorization header

  Scenario: Looking up a printer with an invalid bearer token is rejected
    Given a printer has been registered with serial number "SN-15015", model number "HP-LJ-4200", and firmware version "1.0.0"
    When looking up that printer with an invalid Authorization token
    Then the request is rejected as unauthorized due to an invalid token

  Scenario: Re-registering a claimed printer with a same-family model change still flags it for review
    Given a printer has been registered and claimed: serial number "SN-15016", model number "HP-LJ-4200", and firmware version "1.0.0", claimed by user "user-goar15-b"
    When the printer is re-registered with serial number "SN-15016", model number "HP-LJ-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the printer status is "CLAIMED"
    And the registration history records the model number change from "HP-LJ-4200" to "HP-LJ-4250" and flags it for review
    And looking up the printer shows its owner is still "user-goar15-b" and status is still "CLAIMED"

  Scenario: The model-number-change warning log carries discrete structured fields
    Given a printer has been registered with serial number "SN-15017", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15017", model number "HP-LJ-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And a warning log record has discrete fields serial_number "SN-15017", old_model "HP-LJ-4200", and new_model "HP-LJ-4250"

  Scenario: A same-family model number change succeeds and is logged
    Given a printer has been registered with serial number "SN-15018", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15018", model number "HP-LJ-4250", and firmware version "1.0.0"
    Then the re-registration succeeds
    And the printer status is "REGISTERED"
    And a new Cloud ID is present
    And the registration history records the model number change from "HP-LJ-4200" to "HP-LJ-4250" and flags it for review
    And a warning is logged for this event

  Scenario: A different-family model number change is rejected and the stored record is left unchanged
    Given a printer has been registered with serial number "SN-15019", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15019", model number "HP-C-MFP-9500", and firmware version "9.9.9"
    Then the re-registration is rejected as a model family mismatch between "HP-LJ-4200" and "HP-C-MFP-9500"
    And looking up the printer shows only the review-flag entry was added and the Cloud ID is unchanged

  Scenario: A rejected re-registration produces zero partial side effects
    Given a printer has been registered with serial number "SN-15020", model number "HP-LJ-4200", and firmware version "1.0.0"
    When the printer is re-registered with serial number "SN-15020", model number "HP-OJ-6975", and firmware version "1.0.0"
    Then the re-registration is rejected as a model family mismatch between "HP-LJ-4200" and "HP-OJ-6975"
    And looking up the printer confirms no Cloud ID, printer email, or XMPP node changes occurred and no side-effect entries were added
