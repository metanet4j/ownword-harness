# Sources: 核心认知.md §6.1/§6.4/§7.2-7.3/§10.8/§11.10/§11.17
# Review: R-01~R-06. All scenarios are design assertions; not executable tests.
# @requires-indexer and @requires-mainnet are pending external evidence, not pass status.
@identity @v0_4_0 @draft
Feature: Consistent BAP identity language and verifiable publication

  @R01 @wallet
  Scenario: Wallet identity action can be requested while public history is unknown
    Given the wallet explicitly provides the initial identity action for the current account
    And the public identity resolution is UNKNOWN
    And no known public conflict or unresolved original execution exists
    When the user confirms the frozen business review
    Then the application requests the wallet identity action under wallet authorization
    And the public identity resolution remains UNKNOWN until independent readback

  @R01
  Scenario: Wallet local absence is not public absence
    Given the wallet has no local identity output for the computed BAP ID
    And public history coverage is insufficient
    When the application maps wallet and public observations
    Then the wallet state and the public UNKNOWN result remain separate
    And the application does not create an independent root-control initialization protocol

  @R01 @wallet
  Scenario: Unknown wallet capability preserves the draft
    Given the wallet identity read fails or the current action permission is unresolved
    When the user requests identity publication
    Then the application preserves the draft and requests wallet recovery or authorization
    And it does not treat the wallet read failure as a new identity

  @R01
  Scenario: Known public identity conflict requires recovery before initialization
    Given public evidence verifies the identity already exists
    And the wallet lacks the corresponding identity tracking record
    When the user requests identity publication
    Then the application requests matching or recovery of the existing wallet identity
    And it does not automatically request another initialization transaction

  @R01 @recovery
  Scenario: Unknown broadcast outcome must be recovered by the original transaction
    Given an identity action has an unresolved original wallet reference or txid
    And its final transaction materials may still require recovery
    When the user resumes the operation
    Then the application recovers the original wallet execution and queries its txid when known
    And it reuses the original operationId
    And the application does not create or broadcast a different initialization transaction

  @R02
  Scenario Outline: Transport identity result maps to the correct public domain meaning
    Given the identity API returns scope "<scope>" and kind "<kind>"
    And the source evidence has the verification classification "<evidence>"
    When the frontend maps the transport result
    Then its public identity conclusion is "<conclusion>"
    And it never promotes mock-only data to mainnet evidence

    Examples:
      | scope          | kind          | evidence           | conclusion  |
      | mainnet        | published     | verified-public    | PUBLISHED   |
      | mainnet        | not-published | sufficient-history | NOT_PUBLISHED |
      | mainnet        | not-published | unknown-history    | UNKNOWN     |
      | mainnet        | unknown       | unknown-history    | UNKNOWN     |
      | mainnet        | incomplete    | missing-proof      | UNKNOWN     |
      | broadcast-mock | stored        | isolated-mock      | UNKNOWN     |
      | broadcast-mock | incomplete    | isolated-mock      | UNKNOWN     |
      | broadcast-mock | empty         | isolated-mock      | UNKNOWN     |

  @R02
  Scenario: Incomplete public profile is not the same as an unpublished identity
    Given a valid public BAP ID declaration exists
    And the public profile has missing required fields
    When the visitor reads the identity
    Then the public identity remains PUBLISHED
    And profile completeness is INCOMPLETE

  @R03
  Scenario: Profile DTO fields map to one domain profile without changing identity type
    Given the transport profile contains name, bio, imageUrl and type
    When the profile mapper reads the transport object
    Then bio maps to BapProfile.description
    And imageUrl maps to BapProfile.image
    And the BapIdentity.type declaration is not silently changed

  @R03 @requires-protocol
  Scenario: Changing profile type requires an explicit identity declaration policy
    Given a published BAP identity has an existing identity type and profile type
    When the user requests a different profile type
    Then the implementation follows the reviewed identity and profile type consistency policy
    And it must not claim a new identity declaration without verifiable on-chain evidence

  @R04 @requires-indexer
  Scenario: Historical signatures remain attributed after a valid key rotation
    Given a published BAP identity signed a transaction using its previous valid key
    And a later valid key rotation is recorded in verifiable chain history
    When the old transaction is verified after the rotation
    Then the original BAP ID is retained
    And verification uses the signing path valid at that transaction's chain position

  @R04
  Scenario: Missing signing-time history leaves attribution unresolved
    Given the key rotation history is incomplete or its chain order is conflicting
    When the application verifies a historical signed transaction
    Then the BAP attribution is UNKNOWN or CONFLICT
    And the frontend does not display a verified identity attribution

  @R05 @sync
  Scenario: Re-synchronizing identical operation and transaction is idempotent
    Given a transaction has already been synchronized with an operationId and txid
    When the same raw transaction and expected BAP ID are synchronized again
    Then synchronization returns the existing verified or pending receipt
    And no duplicate verified publication fact is created

  @R05 @sync
  Scenario: Reusing an operation ID with a different transaction is rejected
    Given an operationId already refers to a specific txid
    When the client synchronizes a different txid with the same operationId
    Then the backend returns an OPERATION_CONFLICT
    And the original raw transaction evidence remains unchanged

  @R05 @sync
  Scenario: UTXO spending proof alone does not establish BAP authorship
    Given a transaction has only a valid UTXO spending signature
    And the transaction lacks a valid BAP identity signature for the business payload
    When the backend verifies BAP attribution
    Then the transaction cannot produce verified BAP identity attribution

  @R05 @sync
  Scenario: Modified signed business payload fails identity signature validation
    Given a raw transaction contains an identity signature covering its business payload
    When a covered field is changed without a valid new identity signature
    Then the backend rejects verified attribution for the modified transaction

  @R06 @recovery
  Scenario: Cancelling a later profile transaction does not undo previous transactions
    Given the identity initialization and avatar transactions are already independently submitted
    And the profile alias signing is cancelled
    When the user resumes the identity creation flow
    Then previously submitted transactions keep their original txid and evidence
    And the application does not describe all steps as rolled back

  @R06 @recovery
  Scenario: Switching wallet identity invalidates unsubmitted authorization
    Given a profile review is open for BAP ID A
    And the user switches the wallet account to BAP ID B
    When a delayed response from the original review arrives
    Then the original unsubmitted authorization is invalid
    And any already submitted transaction remains attributed to BAP ID A

  @R06 @requires-mainnet
  Scenario: A successful mock broadcast is not a verified mainnet publication
    Given an identity initialization was simulated in broadcast-mock scope
    When the user switches the application to mainnet
    Then the simulated receipt cannot be shown as confirmed mainnet publication
    And the public BAP identity must be independently resolved and verified
