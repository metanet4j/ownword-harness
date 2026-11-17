# Source: spec/prd/v0.3.0/设计文档v0.3.0-20260918-215142.md
# Status: needs-review; no proof that public Binding protocol is implemented.
@artifact @contract @draft
Feature: Identity Artifact current binding eligibility
  As an OwnWord identity holder
  I can set an Artifact as Current only with sufficient verifiable evidence

  Scenario: Inscription number has not been assigned
    Given the Wallet controls an Artifact with no verified Inscription Number
    When the user attempts to set that Artifact as Current
    Then the application must not create a new active binding
    And the user can see that the number is pending verification

  Scenario: Current binding cannot be inferred from asset ownership alone
    Given an Artifact has a known current owner
    And no valid IdentityNFTBinding can be verified
    When a visitor resolves the Artifact's associated BAP identity
    Then the application must not infer a BAP ID from the owner
    And the Artifact can still be displayed without a current associated identity
