# Sources: 核心认知.md §5.4/§6.4/§9.4/§10.8; Domain/Supporting SUP-01..10
# Design assertions only. No step definitions or runtime pass evidence.
@supporting @v0_4_0 @draft
Feature: Wallet execution and public transaction evidence have explicit support boundaries

  @SUP01 @SUP02
  Scenario: Wallet manages authorization and own identity operations
    Given Yours provides account, permission and identity actions
    When OwnWord requests an identity or profile operation
    Then the adapter delegates the operation under the original site authorization
    And OwnWord does not manage wallet private keys or a parallel identity lifecycle

  @SUP03
  Scenario: Spending signatures do not establish business identity attribution
    Given a transaction has valid funding and ordinal input signatures
    But no verified BAP signature covers its business payload and critical target
    When the transaction evidence is verified
    Then BAP business attribution is not verified

  @SUP03
  Scenario: An arbitrary off-chain message signature is insufficient
    Given signWithBap returns a valid signed message
    But the transaction has no reviewed binding of that message to the business payload
    When the verifier checks identity attribution
    Then it does not accept the message signature alone as transaction identity proof

  @SUP04 @wallet
  Scenario: High-level identity execution has no caller prepare checkpoint
    Given the locked action internally continues from createAction to signAction
    When OwnWord invokes the high-level identity action
    Then OwnWord records its business intent before the call
    And it does not treat an internal unsigned signable BEEF as final signed rawTx
    And it records the actual transaction materials returned after execution

  @SUP04 @SUP05 @SUP07
  Scenario: Final raw transaction is extracted from returned Atomic BEEF or fetched by txid
    Given an identity action returns a txid and optional Atomic BEEF
    When transaction materials are persisted for synchronization
    Then the application extracts the target transaction or fetches its raw bytes by the original txid
    And it recomputes the txid before storing rawTx hex
    And it does not store the whole BEEF hex as rawTx
    And unavailable lookup remains recoverable without creating a replacement transaction

  @SUP04 @SUP05 @recovery
  Scenario: Lost action response is recovered without creating another transaction
    Given the wallet action response was lost after execution started
    When the user resumes the operation
    Then the application uses the original wallet correlation and txid when available
    And unresolved execution remains UNKNOWN
    And it does not automatically invoke a new creation action

  @SUP04 @requires-wallet-fixture
  Scenario: A supported custom two-phase path preserves its original materials
    Given the adapter has verified createAction and signAction options for the locked version
    When a custom transaction reaches its caller-controlled preparation stage
    Then the application stores its original reference and transaction materials before continuation
    And submission continues the same transaction through one selected submitter

  @SUP06
  Scenario: A multi-transaction flow has separate synchronization operation identifiers
    Given two actual transactions belong to the same business flow
    When they are synchronized through the current four-field API
    Then each transaction has a distinct operationId
    And recovery of either transaction reuses its original operationId and txid
    And the client does not add flowId to the existing request body

  @SUP07
  Scenario: Transaction existence is distinct from acceptance and mining
    Given a submitter returns HTTP success and a txid
    When the application derives transaction state
    Then network acceptance and main-chain mining remain independent evidence conclusions
    And business publication waits for its own readback conditions

  @SUP07 @requires-indexer
  Scenario: Reorganization can downgrade current chain conclusions
    Given a transaction was observed in a particular block
    And that block no longer belongs to the verified main chain
    When chain evidence is refreshed
    Then confirmations and affected public projections are recalculated
    And the old observations and original transaction are retained
    And a new-block subscription alone is not accepted as reorganization proof

  @SUP03 @SUP04 @requires-protocol
  Scenario: Unsupported plain transfer identity signing is an explicit capability gap
    Given the locked transfer path rejects BAP signing without an inscription
    When OwnWord requests a plain transfer requiring transaction identity proof
    Then the operation is unsupported until a reviewed signing path is verified
    And the application does not add a re-inscription to bypass the limitation

  @SUP08 @SUP09
  Scenario: Wallet ordinal inventory is not public history
    Given listOrdinals returns outputs managed by the current wallet
    When a visitor queries an ordinal transaction or its transfer history
    Then the application uses public transaction and ordinal query ports
    And wallet tracking identifiers are not used as public origins or global numbers

  @SUP09
  Scenario: An ordinal successor is resolved by continuity across multiple outputs
    Given a spending transaction contains several one-satoshi outputs
    When the query resolves the successor of a particular ordinal
    Then it verifies the relevant input and sat continuity
    And it does not select the first one-satoshi output by position alone

  @SUP09
  Scenario: Missing history or interrupted pagination remains partial
    Given only part of an ordinal spending chain or owner stream is available
    When the query returns the observed records
    Then the result includes PARTIAL coverage and its continuation or missing boundary
    And it does not claim the current owner or a complete history

  @SUP10
  Scenario: OrdFS sequence does not supply a global inscription number
    Given metadata contains sequence, score or blockIdx but no verified global number
    When an artifact summary is assembled
    Then the inscription number remains unresolved
    And the raw metadata fields keep their original meanings

  @SUP01 @SUP07 @SUP09
  Scenario: Simulated evidence is isolated from live chain conclusions
    Given an operation completed in broadcast-mock scope
    When the application switches to mainnet
    Then the simulated wallet and chain receipts cannot establish a live publication or asset fact
    And live observations are queried and verified independently
