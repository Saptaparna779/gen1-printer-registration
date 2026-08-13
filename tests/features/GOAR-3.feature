# Sanity coverage for GOAR-3. Every test case in
# reports/testcases/GOAR-3_test_cases.md (TC-GOAR-3-01 through
# TC-GOAR-3-09) has a corresponding Scenario below -- none were skipped.
# All nine test cases use a valid auth token, so no scenario overrides
# the Authorization header.

Feature: Printer re-registration always issues a fresh Cloud ID
  Re-registering a printer (for example after a factory reset) must
  always produce a brand-new Cloud ID rather than reusing the old one,
  since downstream billing and subscription systems key off Cloud ID.
  This also sanity-checks that Printer Email ID and Claim Code keep
  regenerating on re-registration, that a claimed printer's status and
  owner survive re-registration untouched, and that a failed
  re-registration attempt is fully rolled back rather than leaving a
  stale Cloud ID behind.

  Scenario: Re-registering a printer generates a new Cloud ID
    Given a printer has been registered with serial number "SN-1001"
    When the printer is re-registered with the same serial number "SN-1001"
    Then the re-registration succeeds with status "REGISTERED"
    And the new Cloud ID is different from the original Cloud ID

  Scenario: Re-registering a printer regenerates the printer email and claim code
    Given a printer has been registered with serial number "SN-1002"
    When the printer is re-registered with the same serial number "SN-1002" and an updated firmware version "1.0.1"
    Then the printer email address is different from the original and follows the expected format
    And the claim code is different from the original and follows the expected format

  Scenario: Re-registering a claimed printer gets a new Cloud ID but keeps its claimed status
    Given a printer has been registered with serial number "SN-1003" and claimed by user "user-alpha"
    When the printer is re-registered with the same serial number "SN-1003"
    Then the re-registration succeeds with status "CLAIMED"
    And the new Cloud ID is different from the original Cloud ID

  Scenario: Re-registering a claimed printer preserves its owner
    Given a printer has been registered with serial number "SN-1004b" and claimed by user "user-beta"
    When the printer is re-registered with the same serial number "SN-1004b"
    Then looking up the printer shows its owner is still "user-beta" and its status is still "CLAIMED"

  Scenario: Three consecutive registrations produce three distinct Cloud IDs
    Given no printer is registered yet for serial number "SN-1005"
    When the printer is registered three times in succession with serial number "SN-1005"
    Then all three Cloud IDs returned are different from one another

  Scenario: The second re-registration's Cloud ID differs from the very first Cloud ID
    Given no printer is registered yet for serial number "SN-1006"
    When the printer is registered three times in succession with serial number "SN-1006"
    Then the Cloud ID from the second re-registration is different from the very first Cloud ID

  Scenario: Recovery after a failed re-registration still gets a fresh Cloud ID
    Given a printer has been registered with serial number "SN-1007", and a re-registration attempt for it failed and was rolled back
    When the printer is re-registered with the same serial number "SN-1007"
    Then the new Cloud ID is different from the original Cloud ID
    And a new printer ID is issued, different from the original

  Scenario: A failed re-registration is fully rolled back
    Given a printer has been registered with serial number "SN-1008"
    When the printer for serial number "SN-1008" is re-registered with a simulated Welcome Page failure
    Then the re-registration fails with a Welcome Page print error and the printer record is fully removed

  Scenario: Re-registration after deregistration generates a new Cloud ID
    Given a printer has been registered with serial number "SN-1009" and then deregistered
    When the printer is re-registered with the same serial number "SN-1009"
    Then the new Cloud ID is different from the original Cloud ID
