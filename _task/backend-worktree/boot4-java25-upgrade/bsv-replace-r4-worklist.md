# R4（component 适配）逐文件施工清单

> **状态**：**施工前的清单**。依据 §110—§113 的勘察。**R4 待 R3 收口后启动**（§110.4）。
> **标记**：`M` = 生产文件、`T` = 测试文件。**路径省略 `metanet4j-component/<模块>/src/{main|test}/java/com/metanet4j/` 前缀。**

## 批次 1：`metanet4j-component-common`（2 M ＋ 2 T）

| 文件 | 旧 import | 施工要点 |
| --- | --- | --- |
| **M** `component/common/transaction/BitcoinSchemaTransaction.java` | **9** | **R4 唯一"需设计"处**：① 8 处机械替换（`AddressLite`→`BsvAddress`、`UTXO`→`BsvUtxo`、`Coin`→`BsvAmount`、`Address`→`BsvAddress`、`MainNetParams`→`BsvNetwork`、`Transaction*`→`bsv.transaction.*`）；② **`:78—79` 的 `correctlySpends` 需实现并注册 `SpendVerifierInterface`**（§113） |
| M `component/common/transaction/LocalTestUtxoProvider.java` | 4 | 机械替换（`AddressLite`／`UTXO` 泛型等） |
| T `component/common/transaction/BitcoinSchemaTransactionContractTest.java` | — | 随被测类同步 |
| T `component/common/transaction/LocalTestUtxoProviderContractTest.java` | — | 随被测类同步 |

## 批次 2：`tx-convertor`（1 M ＋ 3 T）＋ `tx-filter`（3 M ＋ 2 T）

| 文件 | 旧 import | 施工要点 |
| --- | --- | --- |
| M `tx/convertor/impl/UtxoConvertor.java` | 6 | 机械替换（**注意 `Utils` 需逐处判断**，§111） |
| T `tx/convertor/impl/UtxoConvertorContractTest.java` 等 3 个 | — | 随被测类同步 |
| M `tx/filter/MetaIdProtocolTxFilter.java` | 2 | 机械替换 |
| M `tx/filter/SourceDataFilterChain.java`／`RepeatSourceDataFilter.java` | 各 1 | 机械替换 |
| T `tx/filter/SourceDataFiltersContractTest.java`／`SourceDataFilterChainContractTest.java` | — | 随被测类同步 |

## 批次 3：`component-bap`（1 M ＋ 2 T）＋ **`component-tx`（9 M ＋ 7 T）**

| 文件 | 旧 import | 施工要点 |
| --- | --- | --- |
| M `component/bap/validator/DefaultBapValidator.java` | 1 | 机械替换 |
| **M** `component/tx/DefaultPrepareOnchainTxResolver.java` | **6** | **需读上下文**（API 形状变化） |
| **M** `component/tx/BschemaCustomTransactionSigner.java` | **5** | **需读上下文**（与 R3 的签名器相关） |
| M `component/tx/core/PrepareOnchainTxResolver.java` | 5 | 同上 |
| M `component/tx/core/UtxoResolver.java`／`DefaultUtxoResolver.java`／`DefaultCompleteTxFactory.java` | 各 3 | 机械替换＋少量上下文 |
| M `component/tx/core/CompleteTxFactory.java`／`BapBaseFactory.java`／`DefaultBapBaseFactory.java` | 各 1 | 机械替换 |
| T `component/tx/` 下 7 个（含 `TxTestFixture`／`StubBapBaseFactory` 两个夹具） | — | 随被测类同步 |
| T `component/bap/BapTestFixture.java`／`manager/BapManagerContractTest.java` | — | 随被测类同步 |

## 批次 4：**纯测试文件**（0 M ＋ 11 T）

| 模块 | 文件 |
| --- | --- |
| `component-bsocial` | `BsocialManagerContractTest`、`BsocialTestFixture`、`chain/MongoBusinessChainIntegrationTest`、`chain/MysqlBusinessChainIntegrationTest` |
| `component-test` | `utxo/TxUtxoServiceTest`、`transaction/LocalTestUtxoProvider`、`transaction/BitcoinschemaTransactionTest`、`transaction/CommonTest`、`convertor/TxoBobConverterTest`、`convertor/MetaIdConvertorTest` |
| `store-mongo` | `bap/repository/bapid/CustomizedBapIdRepositoryImplContractTest` |

**注**：`component-test` 与 `store-mongo` 下有**集成测试**（`MongoBusinessChainIntegrationTest`／`MysqlBusinessChainIntegrationTest`）——
**按任务约束"共享中间件不 `down -v`"**，R4 运行它们时**只启动、不清库**。

## 汇总

| 批次 | 模块 | M | T | 合计 |
| --- | --- | --- | --- | --- |
| 1 | `component-common` | 2 | 2 | 4 |
| 2 | `tx-convertor` ＋ `tx-filter` | 4 | 5 | 9 |
| 3 | `component-bap` ＋ `component-tx` | 10 | 9 | 19 |
| 4 | `bsocial` ＋ `component-test` ＋ `store-mongo` | 0 | 11 | 11 |
| **合计** | | **16** | **27** | **43** ✓ |

## 施工纪律（沿用 R3 已验证的做法）

1. **逐批进行、每批编译**（§59.4）；
2. **改完一批立即 `mvn clean test`**，不攒到最后；
3. **优先"改调用点"而非"改签名"**——若某个公开方法的签名涉及旧类型，**先看调用面**（`grep -rc`、不用 `head`）；
4. **遇到"无对应概念"（`BitcoinObject`／`TxActor`）时停下来记录**（§111 已指出这是唯一需设计类）；
5. **每个子模块单独提交**（component 仓内）。
