# Source: spec/prd/v0.1/设计文档v0.1.md and spec/核心认知.md
# Status: needs-review; no executable step definitions or production pass claims.
@identity @contract @draft
Feature: BAP identity resolution and publication evidence
  As an OwnWord client
  I need to distinguish verified public identity facts from unknown observations

  Scenario: Wallet can compute BAP ID but public coverage is insufficient
    Given the Wallet can compute the current BAP ID
    And the public BAP indexer has not supplied sufficient coverage evidence
    When the application resolves that identity
    Then the identity resolution is unknown
    And the application must not classify the identity as verified not-published

  Scenario: A publicly published BAP identity can be resolved with proof
    Given a BAP identity has a verifiable public publication record
    When a visitor resolves that BAP ID
    Then the result refers to the same full BAP ID
    And the identity has traceable publication and signature evidence

  Scenario: A signed transaction is synchronized again with the same operation identifier
    Given a transaction has already been synchronized with its operationId and txid
    When the same raw transaction and expected BAP ID are synchronized again
    Then synchronization is idempotent
    And no duplicate verified publication fact is created

  Scenario: A transaction without valid BAP identity signature is rejected as identity proof
    Given a transaction has only a valid UTXO spending signature
    And it does not contain a valid BAP identity signature for the business payload
    When the transaction is checked for verified identity attribution
    Then the transaction must not produce a verified BAP identity attribution
