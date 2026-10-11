# BSV 依赖替换任务进度

## Current State

- **Last Updated**：2026-10-16T02:00:00+08:00。
- **Current Objective**：按 [实施计划](doc/BSV依赖替换计划-20261010-103802.md) 串行执行 R0—R6，已完成 feature 拆分、基线冻结、任务入口、方法级 API 映射、逐用例迁移清单和 V01—V14 独立样本，R0、R1、R2 三个阶段已完成，进入 R3 业务 SDK 适配（5 个执行项）。
- **Active Item**：`bsv-r3-keys`（in-progress）；**R0（6/6）、R1（3/3）、R2（2/2）阶段完成**，R3 进行中。实时状态唯一来源为 [feature_list.json](feature_list.json)。实时状态唯一来源为 [feature_list.json](feature_list.json)。
- **授权范围**：胡先生已明确指令“开始按照计划执行，先拆feature，记录执行进度和状态”。授权覆盖既定 R0—R6，原 SDK 输入、共享设施配置及远端边界继续适用。
- 七阶段汇总与 28 个执行项已拆分；每项记录依赖、产物、完成条件、验证证据及提交，一次只推进一个执行项。

## 已有基线与验收依据

四仓库分支均为 `feature/bsv-sdk-replace`；HEAD 为 parent `7302e1b`、base `53ed9ad`、sdk `670ee3d`、component `3ce773b`。base/pom.xml 的既有未提交修改保留，R0 单独冻结，R2 与适配共同提交。指定 SDK 固定 `3dd8beb`，源码、测试、POM 及原迁移证据只读。

原单元证据 `evidence/20260930T125355Z/` 记录 25 POM、23 模块、841 例、零失败／错误／跳过、gaps=0；原 component 集成证据 `evidence/20260930T130119Z-integration/` 为 18 类／124 例。SDK 另有 5 例本地 HTTP 集成，需单独验收。以上不代表本次替换通过。SFTP 成功连接 2 行继续保留已批准精确覆盖例外。

## 验证与限制

- 工具链 JDK 25.0.4.1／Maven 3.9.16 可用，全局默认不变。
- 宿主目标 Maven 缓存可写；沙箱缓存只读且本机网络受限，构建与相关测试使用宿主执行环境。
- 新 SDK 尚未安装至目标缓存，按 R1 接入。五个共享中间件停止，集成前使用已有 infra/up.sh 并先确认测试资源隔离。
- init.sh 已校正当前计划、替换分支、唯一当前项、依赖、完成证据和阶段汇总；--full 明确退出 2，构建采用计划严格入口。
- 旧来源复核证据见 `evidence/bsv-replace/plan-20261010-103802/`；本次执行证据按 feature 单独记录。

## 本次执行证据

- feature 拆分提交：`1439448`；结构、依赖及状态检查 PASS。
- 来源冻结提交：`b0db12c`。
- [baseline.json](baseline.json)：五仓库与 25 POM 指纹、67 个生产／69 个测试直接旧引用、base 既有 diff 已冻结。
- `evidence/bsv-replace/r0-source-20261010-1130/`：来源 revision、full-evidence verify 和 ./init.sh 均退出 0。原验收证据复核 PASS，未重跑测试体。

- 任务入口及状态门禁提交：`fa59f4b`；实施执行项已完成 **11/28**，**R0、R1、R2 阶段 done**；R3 首组（`bsv-r3-keys`）已开始，base 侧共享值类型基座完成。
- `evidence/bsv-replace/r0-harness-20261010/`：自检正常状态退出 0，12 项真实进程门禁检查通过，异常返回非零；子仓库及既有 base diff 保持。

### bsv-r0-api 方法级 API 与调用映射

- 产物 [bsv-replace-api-map.json](bsv-replace-api-map.json)：62 个旧类型决议（replace 30／adapt 13／delete 15／gap 4），逐条含旧 FQN、实际调用方法、callerFiles、目标类型与目标方法、行为编号、阶段与说明；sha256 `032c91c0…`。
- 独立复核 11 项 PASS：映射覆盖 67/67 生产文件、逐文件回读旧 import 全部被认领、目标类型与成员真实存在于新 SDK 公开面、决议与行为挂接完整；配置与反射结论与取证产物一致。
- 能力缺口 7 项全部有结论：新增最小网络值类型 `BsvNetwork`、哈希值类型 `HashBytes`、地址 `BsvAddress`、金额 `BsvAmount`、业务异常基线；删除 KeyBag／RedeemData／TxHelper 抽象改为解锁模板；脚本地址与类型判定按需自建。6 个业务新类型落点写入映射的 `businessNewTypes`。
- 复用入口 [bsv-api-audit.py](bsv-api-audit.py)：核对映射与四仓库源码，`--require-clean` 供 R5/R6 作为旧引用清零门禁；当前 status=PASS，生产旧 import 残留基线 308、测试 358。
- 取证与复核产物在 `evidence/bsv-replace/r0-api-work/`（summary.json、api-map-verify.json、api-audit.json、四份子代理取证与 api-resolution.json）。

### bsv-r0-tests 逐用例迁移清单

- 产物 [bsv-replace-test-map.json](bsv-replace-test-map.json)：221 个测试源文件、1016 个方法逐条登记（unit 841／integration 121／external 54），含处理方式、目标、行为编号、标签与继承、计数口径；sha256 `9fd4dc09…`。
- 处置分布：68 个文件改写旧库调用、1 个文件（`RedeemDataExtendContractTest`）因旧实现删除失去意义并登记承接验证、152 个保持不变；9 个受删除实现影响的类逐个给出承接阶段与新验证内容。
- 两个集成集合单列：业务 SDK 本地 HTTP 集成 1 类 5 例；component 集成 18 类／实测 124 例（声明 116，差值来自继承的 `contextLoads` 与类级标签继承）。
- 口径一致：静态源码计数 = `unit-test-inventory.json` = 既有验收报告，三方 841 且逐模块零差异；`bsv-api-audit.py test-map` 9 项检查 PASS。
- 已登记两个陷阱：`TxUtxoServiceTest` 类级 external + 继承 integration 会被两组同时排除；JUnit 5 类级 `@Tag` 会被子类继承，禁止用声明数冒充执行数。

### bsv-r0-vectors 冻结 V01—V14 独立样本

- 产物 [bsv-replace-vectors.json](bsv-replace-vectors.json)：14 组全部冻结，134 条样本、126 项独立预期值、19 项指纹；sha256 `ec4f2831…`。
- 独立复算 24 项 PASS：secp256k1 标量乘法与压缩公钥、Base58Check 地址（主网／测试网）、Hash160、四组 WIF、BSM 前缀、CompactSize 七个边界、BIP39→BIP32 根 xprv（正向复算 + 反向解码）、BAP 标识、6 个历史交易 txid 双 SHA-256 与显示序；全部为纯 Python 实现，不使用被测 Java 代码。
- 独立复核 14 项 PASS：组齐全、场景与计划第 5 节逐字一致、样本文件／类名／方法真实存在、每组均有独立预期值、指纹可复现、长字面量回读命中。
- 自洽断言 55 条单独标注，不作为兼容性证据；ECIES 与固定 DER 签名字面量缺失、V08 pushdata 边界与 V10 负数／越界／溢出无既有用例，均登记 notFound 并转入 R3／R4 补充验证。

### bsv-r0-gate R0 阶段门禁

- 新增可重跑门禁 [bsv-task-gate.py](bsv-task-gate.py)：只读输入（SDK HEAD／工作区／原验收清单指纹）、四仓库基线与既有 diff 保留、阶段产物存在、执行项完成度与证据齐备、能力缺口收口、证据↔产物指纹交叉核对、`./init.sh`。R0 结论 **PASS（28 项检查）**。
- 证据刷新入口 [refresh-r0-api-evidence.sh](refresh-r0-api-evidence.sh)：重跑三份产物生成与全部独立复核后同步指纹；产物内容不变时指纹与 `generatedAt` 均不变，连跑两次已验证可复现。
- 门禁检出一次真实漂移：API 映射在证据冻结后更新（KeyBag／RedeemData／TxHelper 由删除改为适配、追加缺口结论与 `oldTypes`），按门禁要求重跑复核并同步指纹（`032c91c0 → ac803812`），结论未变。
- 证据：`evidence/bsv-replace/r0-gate-20261010/`（gate.json、summary.json）。
- R0 交付物指纹：baseline `10f9679c`、API 映射 `ac803812`、测试映射 `4365a421`、向量 `8179f162`。

### bsv-r1-package／bsv-r1-parent／bsv-r1-fingerprint（R1 阶段，全部完成）

- 制品：[bsv-replace-artifact.json](bsv-replace-artifact.json) 记录来源（HEAD `3dd8beb`、src/main+POM 指纹 `d622c3a0…`）、打包命令与退出码、目标缓存安装与双向哈希；主 JAR 476 条目含 `Transaction.class`、0 个 `.java`、无 test 条目，源与缓存 `d3aaf86d…` 一致。
- parent：[metanet4j-parent/pom.xml](metanet4j-parent/pom.xml) 在 dependencyManagement 接入 `com.metanet4j:metanet4j-bsv-sdk:${metanet4j.version}`（解析 0.2.0），旧管理项保留到 R5；`-N install` 退出 0。
- 依赖路径：[bsv-replace-dependencies.json](bsv-replace-dependencies.json) 记录 5 个模块的 resolved tree 与 JCL 实际引入路径（sdk 直接声明 `jcl-store-levelDB` 并传递 `jcl-tools`／`jcl-store`／`jcl-store-keyValue`），供 R5 清理核对。
- 指纹绑定：[verify-unit.py](verify-unit.py) 运行元数据新增 `sdkArtifact`，严格模式与 R1 绑定清单双向核对；向同坐标 JAR 追加一字节后严格验收退出 1 并报出两条预期问题，恢复后缺 SDK 指纹的旧证据仍被拒（[bsv-replace-fingerprint.json](bsv-replace-fingerprint.json)）。
- R1 门禁 `bsv-task-gate.py --stage r1` 退出 0。

### bsv-r2-behavior／bsv-r2-accept（R2 阶段，全部完成）

- base 旧库清零：`AipHelper` 改用 `PublicKey`／`Hash`／`Utils`／`Writer`，`BapHelper` 改用 `Hash.sha256`／`Hash.ripemd160`／`Utils.toBase58`；新增最小网络值类型 [BsvNetwork](metanet4j-base/src/main/java/com/metanet4j/base/bsv/BsvNetwork.java)（地址头／P2SH 头／WIF 前缀／BIP32 版本／测试网标志／名称解析／版本校验），公开参数 `NetworkParameters` → `BsvNetwork`。
- **新旧实现奇偶校验 110 项 0 差异**：一次性工程 `evidence/bsv-replace/r2-behavior-20261010/parity/`，旧路径 bitcoinj-base 1.0.4、新路径 metanet4j-bsv-sdk 0.2.0，覆盖 BAP 身份标识、BSM 验签 4×3×8 组合、recovery 头 27..34 轮换、主网／测试网地址。过程中修正两处实际缺陷：SDK `BigNumber` 不接受 `byte[]`；恢复公钥取 hash160 必须按 compact 头的压缩标志选择公钥编码。
- 清单同步：[unit-test-inventory.json](unit-test-inventory.json) 新增 `BsvNetwork` 与 `BsvNetworkTest`（7 个 unit 方法），与磁盘逐文件一致。
- 严格验收：`verify-unit.py --mode accept --scope metanet4j-base` 退出 0，**30 例（8 类）0 失败 0 错误 0 跳过，覆盖率未覆盖全为 0，gaps=0**；base 制品安装后源／缓存 JAR 哈希一致（`04a34cf7…`）。
- 证据：[bsv-replace-r2-behavior.json](bsv-replace-r2-behavior.json)、[bsv-replace-r2-accept.json](bsv-replace-r2-accept.json) 与 `evidence/bsv-replace/r2-{behavior,accept}-20261010/`；base 提交 `bf294ef`。R2 门禁 `bsv-task-gate.py --stage r2` **PASS**。

### bsv-r3-keys 进行中：共享值类型基座已完成

- 新增 [BsvHashBytes](metanet4j-base/src/main/java/com/metanet4j/base/bsv/BsvHashBytes.java)（32 字节哈希，显式内部序／显示序）、[BsvAddress](metanet4j-base/src/main/java/com/metanet4j/base/bsv/BsvAddress.java)（base58 地址与网络校验）、[BsvAmount](metanet4j-base/src/main/java/com/metanet4j/base/bsv/BsvAmount.java)（long satoshi 与边界校验），作为 SDK／component 迁移的统一值类型载体。
- [BsvValueTypesTest](metanet4j-base/src/test/java/com/metanet4j/base/bsv/BsvValueTypesTest.java) 13 例覆盖 V01（字节序）、V02（双网络地址与跨网络拒绝）、V10（金额边界）相关判定。
- 清单与例外同步：[unit-test-inventory.json](unit-test-inventory.json) 登记 3 个生产类与 1 个测试类；[unit-coverage-exceptions.json](unit-coverage-exceptions.json) 新增 metanet4j-base 两处经核对的纯分支例外（行覆盖 100%、无未覆盖方法，仅 javac 短路字节码的合成分支无法标记）。
- 验收：`verify-unit.py --mode accept --scope metanet4j-base` 退出 0，**43 例 0 失败／错误／跳过，行与指令未覆盖为 0，gaps=0**；base 提交 `caaeb8b`。
- SDK 侧待迁移面：`metanet4j-sdk` 生产 49 个文件、测试 41 个文件仍含旧引用（生产 246 处、测试 242 处 import），按密钥／脚本／交易／协议四组推进，五组全部通过才算 R3 完成。

### bsv-r3-keys 进行中（第二批）

- SDK 密钥／地址层已迁移（metanet4j-sdk 提交 `56058b4`）：`EcKeyLiteExtend` 不再继承旧 `ECKeyLite`（改用 `ECDSA.sign` + `Signature.toCompact` 与 `compat.BSM`）；`PublicKey`／`PrivateKey` 包装新 SDK 密钥，网络类型 `NetworkParameters` → `BsvNetwork`；`AddressEnhance` 组合 base 的 `BsvAddress`；`Ecies` 改用新 SDK 密钥且**报文结构与 ecdh 顺序不变**（兼容既有密文）；BAP 密钥访问器返回业务 `PrivateKey`。
- 迁移参考已固化：`evidence/bsv-replace/r3-keys-20261010/migration-rules.md`（四组统一改写规则、类型对应表、硬性约定、验证命令）与 `old-api-reference.md`（36 个旧类型的 javap 权威签名 × 新 SDK 入口，43 KB）。
- **SDK BIP39／BIP32 层已迁移**（sdk 提交 `5424b34`）：`MasterPrivateKey` 改用 `compat.HD`／`compat.Mnemonic`／`Bip39WordlistEn`，助记词→seed→主密钥链与 xprv／xpub 语义不变。
- **SDK BAP 结构改写完成**（sdk 提交 `c9df398`）：新增 `BapPath` 值类型（解析 `M/44H/236H` 与 `m/44'/236'`、硬化位、前缀／追加／派生）与 `SigningKeyProvider` 接口（取代 `KeyBag` 反查）；`BapBase`／`MasterKeyBapBase` 的密钥派生全部改走 `compat.HD`，`BapProviderKeyBag`／`SpecifyProviderKeyBag` 不再实现旧 `KeyBag`；`RemoteBapBase` 地址字段统一 `AddressEnhance`。新增 `BapPathTest`（8 例）与独立核验 14 项 0 差异。
- **签名流程重构进入原子模式**（用户决策）：R3 剩余 27 个生产文件全部落在同一耦合团（18 文件／2080 行／20 个测试依赖），单点改动只能在 26～48 间搬运错误。胡先生选择「允许长时间原子重构」，**R3 收口期间工作区接受编译未通过的中间态，不再中途还原**。
- **去 TransactionExtend 残留引用**（sdk 提交 `37247f3`）：三处调用改直传新 SDK `Transaction`；显式错误 6 → 86（移除中间层后暴露调用方真实依赖，属预期）。剩余错误集中在 `OrdinalsTransactionSigner` 26、`RemoteTransactionSigner` 14、`OrdTransactionBuilder` 14、`TransactionBuilder` 12、`RemoteTransactionBuilder` 12、`RemoteOrdTransactionBuilder` 8。
- **签名载体改造 + 删除 TransactionExtend**（sdk 提交 `78a4813`，原子重构第三步）：`ExtendForSignTransaction` 改为普通业务载体（持有新 SDK `Transaction` + `signatureScope()`），`TransactionExtend` 按 R0 判定删除。**编译错误 56 → 6，生产旧引用文件数 23 → 21**。
- **BobHelper 已迁移**（sdk 提交 `11112b9`，原子重构第二步）：改新交易与脚本模型，chunk 访问走 `ScriptHelper.getPushData`、操作码 `OP.OP_*`（`OP_FALSE` 按新 SDK 实际常量改 `OP_0`）、地址走 `BsvAddress`；**BobHelper 自身错误清零**。生产旧引用文件数 **24 → 23**。
- **脚本工具层落地**（sdk 提交 `c8f9079`）：`ScriptExtend` 改工具类（重建脚本判定、签名位填充、花费尺寸估算，`SIG_SIZE=75`）；`TxHelperExtend` 去 `TxHelper` 继承、Ordinals 判定改新 `ScriptChunk`、新增**显式派生版** `getConnectedRedeemDataExtend`；`RedeemDataExtend` 重写为业务值类型；`TransactionBuilder.getUnLockScriptSize` 切为无赎回数据的费用估算。生产旧引用文件数 **27 → 24**。批内错误数曾降到 **6**（证明脚本层切口有效），补回赎回数据入口后升至 60（调用方待迁）。
- **SigHashExtend 已迁移**（sdk 提交 `fe273b5`）：按 §8 自下而上第一层——`hashForForkIdSignature` 参数改 `(Transaction,int,byte[],BsvAmount,int,boolean)`、内部适配新 SDK 的 `TransactionSignature.formatBip143` + 双 SHA-256、返回 `BsvHashBytes`、不再继承旧 `SigHash`；等价性逐字段核对见 `evidence/bsv-replace/r3-keys-20261010/sighash-extend-equivalence.json`（**独立前像计算器 `referenceDigest` 保留未替换**）。生产旧引用文件数 **28 → 27**。
- **UnSpendableDataLockBuilder 已迁移**（sdk 提交见提交历史）：`Sha256Hash` → `BsvHashBytes`（6 处），与 `PreSignHashContext.preSignHash` 新类型对齐；编译错误 22 → 18。
- **Sigma 与 pre-sign 上下文已迁移**（sdk 提交 `8d6269f`）：`Sigma` 改用 `BsvHashBytes` 与新 SDK `Transaction`／`Script`（公开字段 `outputs`／`inputs`、`lockingScript`、`satoshis`、`Script.writeBin`、`OP.OP_RETURN`、`ScriptHelper.getPushData`、`BsvAddress`），`SignResponse`／`PreSignHashContext`／`PreSignHashUtils`／`Sig` 同步；`getMessageHash` 等三个公开方法返回类型改 `BsvHashBytes`。生产旧引用文件数 **33 → 28**。
- **TxoHelper 已迁移**（sdk 提交 `8706eb9`）：改用新交易模型与 `BsvAddress`／`OP`；**新旧实现同输入对照 6 个历史交易夹具，txid 全部一致、1 个全文一致**；其余 5 个仅 `out[].e.a` 不同（旧库 `getToAddress` 对部分 Ordinals 铭文脚本返回 ASM 文本，新实现回退脚本 hex），已登记为可评审偏差。生产旧引用文件数 **34 → 33**，编译错误 14 → 10（仅剩 Sigma 8、BobHelper 2）。
- **CryptoHelper 已迁移**（sdk 提交 `a3746c5`）：改走 `compat.HD`／`compat.Mnemonic`／`BapPath`，根派生路径 `m/44'/236'/0'/0/0` 与旧实现逐段一致；`CryptoBase.deterministicKey` 类型改为 `HD`（对应测试断言待测试迁移时同步）。生产旧引用文件数 **35 → 34**。
- **脚本工具已迁移**（sdk 提交 `171ab43`）：`UtilsExtend` 不再继承旧 `Utils`（自持 BSM 前缀 + `Writer` VarInt + `BsvHashBytes`），`ScriptHelper` 改用新 SDK `ScriptChunk`／`Script` 与 `BsvAddress`。生产旧引用文件数 **37 → 35**。
- **口径修正（重要）**：SDK 生产编译错误曾从 24 降到 4，但这**不代表接近完成**——`metanet4j-sdk/pom.xml` 仍声明旧 `bitcoinj-base`／`bitcoinj-legacy`，编译期可解析旧类，因此 **36 个生产文件 + 41 个测试文件仍引用 `io.bitcoinsv`**，R5 移除依赖时才会集中暴露。真实进度以「旧引用文件数」衡量，不以编译错误数衡量。
因此 `bsv-r3-keys` **未完成**，不标记 done。
- `init.sh` 阶段状态判定已扩展为支持「阶段内首项开工即 in-progress」，自检恢复通过。

## Recommended Next Step

继续 `bsv-r3-keys` 收口 SDK 生产编译（按 `migration-rules.md` §5 配方执行）：

按「旧引用文件数」推进（当前生产 **28**、测试 41），建议顺序：

1. **`ScriptExtend` 契约已冻结**：`ScriptExtendContractTest` 给出 9 条精确断言（P2PKH／裸公钥／多签／P2SH／Ordinals／未支持类型／创建时间），`SIG_SIZE=75`；实现草稿已按该契约核对，见 `migration-rules.md` §11。手续费估算切口的依赖与反推方法见 §12（`getUnLockScriptSize` 只需公钥长度与 P2SH 赎回脚本，且必须用 `TransactionBuilderContractTest:216-222` 反推口径，不能凭结构猜测）。
2. **脚本工具层 + 赎回数据取消（五个文件一批）**：本轮实测——草稿落地后错误 26 → 48，原因是 4 个调用方**都**依赖 `TxHelperExtend.getConnectedRedeemDataExtend`（返回旧 `ECKey`／`RedeemData`）。正确批次是：`RedeemDataExtend` 删除 + `TxHelperExtend` 去继承 + `ScriptExtend` 改工具类 + 三个调用方改「显式派生 + 解锁模板」。建议先单独把 `TransactionBuilder.getUnLockScriptSize` 改成不依赖赎回数据（手续费估算，可独立验证），再处理签名流程。详见 `migration-rules.md` §10。
2. 交易与签名组（`transcation/TransactionBuilder`、`signers/*`、`remote/*`、`ordinals/*`、`utils/TxHelperExtend`、`utils/RedeemDataExtend`）→ 按 migration-rules §3 把 KeyBag／RedeemData 改为 `SigningKeyProvider` + 解锁模板；
4. UTXO（`utxo/*`）与 `context/PreSignHashContext`；
5. 每完成一个文件即重跑 `grep -rl 'io\.bitcoinsv' metanet4j-sdk/src/main/java --include=*.java | wc -l`（当前 35），以文件数单调下降为准；生产清零后再动 41 个测试文件。

R4—R6 待前置阶段门禁。
