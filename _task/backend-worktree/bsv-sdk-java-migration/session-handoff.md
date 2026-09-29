# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源（22 done／6 in-progress／15 not-started，`nextItem=migration-impl-transaction-base`），[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。最近一次目标 Java 宿主无过滤 `clean test` 绑定提交 `1da225e`（来源摘要 `0a119349…`）：167 份 Surefire 报告为 5437／5437、无失败／错误／跳过，同次覆盖全部 5329 个映射身份且无重复，另有 108 个 Java 回归。报告封存于 `.cache/evidence/wallet-keys-full-surefire-20260929/`，日志 `.cache/evidence/wallet-keys-full-java-20260929.log`；该来源与 wallet-keys 六个局部一致，后续源码变更仍须新一轮无过滤回归。对称加密 52／387、Compat 122／281、交易完整功能 745／1390、交易验证 53／162、认证会话 85／160、认证传输 183／968、DRBG 29／30 已有固定原用例／逐断言任务级对照；AuthFetch 属性 300 组固定 TS 实际输入与 Java 消费一致。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3576／3576 且已复核，21 个 API 批次均完成；原用例映射 5329／5329，测试站点映射 7554／7554。固定 TS 标准／manual Jest 原始报告合计 5329／5329，并通过 `audit-tests.py compare-ts`。Spend 的第二组 455 个独立注册已由新 Java 类和新映射收口。对称模块 fixed TS 原 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过，连同当次 Java 原始轨迹和逐字节摘要的专用桥接见 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`。API 总审计见 `doc/API跨任务接口复核-20260927-000100.md`；Transaction 非阻塞、三个异步异常入口和 PATCH 状态说明修复已合入当前累计回归。

## 并行工作

- AuthFetch 固定原测试 134／890 与 Transport 合批 183／968 已在 `c0d9fdd` 对照；属性测试 300 组 fast-check 实际输入已封存并由 Java 同批重放，600 条断言精确一致。
- Hex＋BigNumber 构造 36 例、Base58 六例、BRC100 属性两例 600 组、WERR 32 例、JSON 字节 10 例、BRC100 字节 23 例、WalletError 39 例已有局部同输入核验。ValidationHelpers 严格区分 `undefined`／`null` 后，147 个固定原例的 149 组输入、203 条断言一致，另有 6 个 null 边界回归。证书五文件 50／50、128／128 已分批局部核验；其中 ValidateCertificates 严格重采 8／8 原例、21 组实际输入、16 条断言通过。Script／Spend 共用向量 1940 例、Transaction 向量 659 例、Chronicle 74 例亦有局部核验。Wallet Contracts 的 253／1003 当前值对照已通过，其余输入账本继续补齐。AuthFetch.additional 已完成两批共 41 例局部输入采集；WalletWire.integration 82 例正在重采；通用断言 helper 的真实调用历史审计仍在继续。
- DRBG 原 29 例已在 `c23c6f6` 完成双端正式采集并登记：72 条真实入口（含 15 个 NIST 守卫分支）与 30 条断言双端逐值一致，30 条未执行断言按 `drbg-nist-invalid-input-v1` 与分支样本有据，输入／断言／分支三类篡改均被拒；该登记绑定 `c23c6f6`，在当前 Java 版本下被来源复核拒绝，须随最终全量运行重采。计划冻结与探针见 `drbg-input-plan.json`、`capture-drbg-inputs.cjs`、`prepare-drbg-inputs.py`，证据见 `doc/DRBG原输入验收-20260928-181254.md`。
- knownTxids 付款原 6 例已在 `79c4b3b` 通过局部门禁：6 条真实输入、8 次付款调用与 25 条断言双端一致，付款输入与断言篡改被拒；Java 侧按语料重建 `Response` 且不伪造宿主 `bodyUsed`。证据见 `.cache/evidence/known-payment-local-20260928-03/`，文档 `doc/knownTxids付款输入验收-20260928-201034.md`。
- knownTxids 真实 Peer 原例已在 `b7acbb4` 通过局部门禁：随机源、两次 fetch 入口、Peer 前置状态、交付帧、发送载荷与结果、监听器编号逐字段一致，6 条断言一致；入口探针与 Peer 探针分两次 Jest 运行后合并语料，文档 `doc/knownTxids真实Peer输入验收-20260928-210831.md`。该文件 17 例输入重放已全部落地。
- 八个局部已在 Java 来源 `382ac6c6` 重采并通过 `local-evidence-gate.py`：钱包契约六文件（wallet-property 2/600/600、brc100-byte-encoding 23/57/62、werr-constructors 32/32/40、wallet-error 39/54/79、validation-helpers 147/149/203、json-byte-encoding 10/26/19）、HTTPWalletJSON 53/214/73、toOriginHeader 5/5/5。`migration-impl-wallet-contracts` 与 `migration-impl-wallet-json` 已按依赖顺序标记 `done`，`nextItem` 改为 `migration-impl-wallet-keys`。刷新记录见 `doc/钱包契约与钱包JSON证据刷新-20260929-020724.md`。
- `migration-impl-wallet-keys` 六个文件全部完成：KeyDeriver（17／49／37，子类覆写 + 深度守卫）、ProtoWallet.additional（11／22／11，记录 keyDeriver 前置状态，`WalletKeysEntropy` 与 TS 固定熵流对齐）、CachedKeyDeriver（13／49／44，循环站点样本 + `timing-ms-v1` 耗时规则，账本改为用例结束落盘以免采集开销进入耗时断言）、ProtoWallet（19／111／44，深度守卫 + 原 helper 的 undefined originator 形状 + 固定系统时间对齐 revelationTime）、ProtoWallet.native-hash（6／19／18）、ProtoWallet.async-backend（5／21／8，从桶文件出口替换两个类并记录后端注册）。六个文件合计 71 例、271 条入口、162 条断言，已在来源 `0a119349` 统一重采并通过 `full-evidence-preflight` 来源复核（`currentCaptureVerifiedCases=71`），同来源全量回归 5437／5437 通过，`migration-impl-wallet-keys` 已标记 `done`。三者都是标准双侧局部并通过 verify／tamper。
- 认证证书六文件已在来源 `0a119349`（提交 `1da225e`）统一重采并通过 `full-evidence-preflight` 来源复核：50 例、278 条入口、128 条断言，六项门禁 verify 与 tamper 通过；任务级同来源报告 `.cache/evidence/auth-certificates-same-source-20260929/task-parity.json` 为 50／50、128／128，`migration-impl-auth-certificates` 已 `done`。
- Java 侧提交会推进来源摘要（`382ac6c6`→`f16b01df`→`8cf69655`→`0a119349`），已完成的局部随即变为过期；钱包契约六文件（253 例）与钱包 JSON 两文件（58 例）仍绑定 `382ac6c6`，DRBG 29 例绑定 `c23c6f6`，都须在后续统一重采。
- P0 采集来源门禁的语义规则 10／10、bundle 18／18、关联 3／3、宿主审计 41／41 自测通过。最新 `full-evidence-preflight.py` 结构计划覆盖 4099／5329，仍缺 1230 例，来源复核覆盖 121 例、12 个局部（`.cache/evidence/full-preflight-round13.json`：wallet-keys 六文件 71 例、认证证书六文件 50 例，均为当前来源 `0a119349`）；其余 68 个局部绑定旧执行器或旧 Java 版本，须在最终单次全量运行中重采。`ParityRecorder.errorName` 现按异常公共 `name` 字段记录 JS 可见错误名，WERR 系列不再被记成 `Error`。旧 Java 完整回归和 TS 原始报告不能代替单次完整双侧来源。通用断言 helper 已修复一批 null/undefined 伪记录，余下的完整调用历史和对象匹配语义正在修复并重新核对受影响局部证据。完整 `audit-tests.py check` 仍须全量真实输入和断言采集。

## 并行路线（20260929）

`python3 item-readiness.py` 给出各事项的冻结用例／已计划／当前来源复核与缺计划文件；据此排的后续分工：

| 子代理 | 当前 | 下一步（依赖满足后） |
| --- | --- | --- |
| SA2 | HTTPWalletWire 46 + window.CWI 31 | wallet-client 100（3 文件全无计划） |
| SA3 | transaction-beef 83 | script-templates 17 → script-spend 缺 91 |
| SA4 | Signature 36 + AESGCM 30 + ReductionContext 29 | transaction-verification 53 或 auth-sessions 85 |
| SA5 | HD 49 + Script 39 + Hash 17 | script-vectors 缺 26 → transaction-complete 缺 86 |
| 主代理 | 协调、验收、提交、统一重采 | auth-transport 缺 49；最终全量门禁 |

依赖链：beef → script-templates → script-spend → script-vectors → transaction-complete → transaction-verification；wallet-wire + wallet-hosts → wallet-client → auth-sessions → auth-transport。

已知残留风险：`prepare-transaction-local.py` 的 `loopSamples` 采用“该用例入口样本”做结构覆盖（与 bn-arithmetic 登记方式一致），最终全量门禁若对循环样本有更严要求，需要按站点补真实循环样本。

## 本轮交付（20260929 晚）

- `http-wallet-wire` 已完成：46 例／126 输入／51 断言，recapture／tamper（两个 true）／gate verify 全绿，带冻结语料的聚焦 Java 测试 46/46 逐字段一致。钱包宿主与 WalletWire 事项的冻结用例已全部有标准局部（wallet-wire 82 + http-wallet-wire 46 = 128），待静默窗口统一重采后出任务级对照并结项。
- `window-cwi` 的 TS 探针、冻结（31 例／60 输入／61 断言）与带语料聚焦测试 31/31 已通过，仅剩正式双侧采集。
- `hd` 49 例／227 样本／92 断言、`script` 39/99/96、`hash` 30/150/92 计划已冻结并登记，正在采集。
- 编译阻塞已清除：`ScriptInputReplay`（6 处 `List.of` 包成 `Arguments` lambda + 2 处 `action.run()`）、`HDInputReplay`、`HashInputReplay`（泛型放宽为 `List<?>` 并保留 Number 校验）修复后 `test-compile` 5437 源文件编译成功。

## 证据完整性复查（20260929）

对 13 个已登记标准局部逐个复跑 `local-evidence-gate.py verify`，全部与登记时一致、无损坏：交易基础五局部 74 例/150 输入/115 断言、广播器四局部 68/231/169、钱包宿主与 WalletWire 三局部 177/542/526，合计 319 个用例的既有证据可用。

## 全量运行接口

最终 `audit-tests.py check` 需要 `full-evidence-locals.json` 的 `fullRun.tsCommand/javaCommand/tsReports/javaReports`：TS 侧由一个按 `testPath` 分派探针的 `capture-full-dispatch.cjs` 在一次 Jest 运行里覆盖全部原文件，Java 侧用无过滤 `clean test` 并把全部 `MIGRATION_*_TS_INPUTS` 指向本轮汇总输入。该接口由基础设施子代理实现，完成后 `full-evidence-preflight.py` 的 `missingFullRunInterfaces` 应为空；覆盖率补齐后再跑单次双侧全量采集。

## 第三波（已派发）

SA9：`locking-unlocking-script` 12 例、`script-additional` 14 例、`binary-fetch-client` 12 例、`bignumber-additional` 19 例（合计 57 例），用独立登记表 `misc-locals.py` + `prepare-misc-local.py` + `capture-misc-local.py`，避免与在跑的四个登记表冲突。

## 第二波分工（待第一波交付后派发）

各子代理完成后**不要闲置**：按下列批次用 `send_message` 续派（保持同一子代理的管线上下文最省事）。

| 批次 | 事项 | 文件（未计划例数） | 备注 |
| --- | --- | --- | --- |
| B1 | wallet-client（100） | WalletClient.substrate(38)、WalletClient.additional(61)、WalletClient(1) | 依赖 wallet-wire／wallet-hosts 结项 |
| B2 | auth-sessions（85） | Peer(30)、Peer.certificatePolicy(15)、Peer.boundary(2)、SessionManager(11)、build(20)、cryptononce(7) | 依赖 wallet-client |
| B3 | auth-transport（49） | SimplifiedFetchTransport.additional(46)、SimplifiedFetchTransport(3) | 依赖 auth-sessions |
| B4 | script-spend（91） | Spend.additional(69)、Spend(20)、SpendComplex(1)、Spend.codeseparator(1) | 455 例已有旧局部 |
| B5 | script-vectors（26） | NormativeVectors(9)、Spend.verifier(9)、lrshiftnum(4)、Chronicle(3)、SpendValildVectors(1) | 529 例已计划 |
| B6 | transaction-complete（86） | Transaction.test(61)、Transaction.performance(25) | 659 例已计划 |
| B7 | script-model（65） | Script.test(39，进行中)、Script.additional(14)、LockingUnlockingScript(12) | — |
| B8 | curve（38）／bignumber（50）／keys-signatures（73）／symmetric（22）／hash-random（39）／compat（9） | Curve.unit(18)、Curve.additional(20)、BigNumber.additional(19)、ReductionContext(29，进行中)、PublicKey(14)、PublicKey.additional(32)、ECDSA(15)、Schnorr(12)、SymmetricKey(15)、Hash(17，进行中)、ECIES(9) | 已完成事项的补强 |

## 全量探针映射的三类权威来源（20260929 核实）

`build-full-run-probes.py` 生成 `full-run-probes.json` 后仍有 46 个局部未解析，来源如下：

1. **直写型 16 个**（`auth-fetch-additional-*`／`auth-fetch-primary-*`，`specialized-local` + `deriveCatalogFromPlan`）：探针与局部同名 `capture-<局部名>.cjs`，自己写 `EVIDENCE_*` 最终行，无需额外变量；原文件由该局部 `input_plan` 的 caseId 反查。
2. **适配器 replay 型 17 个**（arc-*、broadcaster、cached-keyderiver、fee-model、http-wallet-json、keyderiver、protowallet*、mnemonic*、wallet-property、werr-constructors、三类字节编码、validation-helpers、origin-header5、drbg29 等）：探针与语料变量都在适配器 TS 分支的 `env[...] = ...` 里；raw 型还需复用适配器里的 `prepare-*-inputs.py emit-ts` 转换。
3. **命名不规则的 13 个**：权威来源是该局部的 `*-local-gate.py`（含探针、catalog／plan 与期望报告），逐个取用；确实没有可复用探针的必须在严格模式下报错，不得猜测。

`run-full-ts-capture.py` 需要采集后校验：所有原始轨迹存在且非空、raw 型转换成功，任一缺失即整轮非零退出（防止“跑完但没有输入”的假绿）。

### 统一窗口待执行清单（代理已交付）

- **window-cwi**（代码侧就绪，已证明 TS 探针 31/31、带语料 Java 31/31 且输入逐字段一致）：`./lock.sh python3 recapture-local.py --name window-cwi --run .cache/evidence/window-cwi-standard-<新目录> --update` → `./lock.sh python3 local-evidence-gate.py tamper --name window-cwi` → 聚焦 `clean test -Dtest=WindowCWISubstrateTest,HTTPWalletWireTest` → `full-evidence-preflight.py`。可选反向验证：改冻结语料里 `getVersion` 的返回值应立刻报“Java 实际 window.CWI 入口或结果与固定 TS 不同”。
- **http-wallet-wire**：四项已绿（46/126/51、tamper 两个 true、verify 退出 0）；统一窗口会一并刷新。
- **transaction-signature-additional**：`ParityRecorder` 修复后重采被他人编译错误挡住，留待统一窗口（修复本身已在聚焦运行中验证 65/65）。

### 本轮修复验证

`324d3c3`（SDK）：恢复普通对象浅表示 + 新增 `recordJsMapDefined`/`assertDefinedJsMap`；聚焦运行 `RecordingAssertionsSemanticsTest` 21/21、`TransactionSignatureAdditionalTest` 24/24、`TransactionAdditionalTest` 20/20，合计 65/65 BUILD SUCCESS。

### 本轮进展（20260929 深夜）

- **已采集并通过 verify+tamper 的局部**：`hd` 49/227/92、`push-drop` 6/151/85、`transaction-evidence` 4/12/12、`transaction-verifier` 15/35/30、`script` 39/99/96、`beef-party-additional` 3/73/7、`merkle-path` 25/125/63、`merkle-path-safe-offsets` 21/87/70、`merkle-path-bench` 13/2643/1290。
- **已交付但待采**：`window-cwi` 31/60/61、`hash` 30/150/92、`p2pkh-async-backend` 2/10/2、`r-puzzle` 9/17/9、`aesgcm` 30/457/334、`signature` 36/51/46、`reduction-context` 29/38/70、keys 六局部 97/223/134、misc 四局部 57/134/106、`chronicle-opcodes` 74/154/77、`simplified-fetch-transport-additional` 46/89/68；上一批失败均为**他人编译错误**或“采集期间源码变化”，不是内容不符。
- **两个生产缺陷已修**（SDK 仓 `d5c3f42` + 前一提交 `Signature.toCompact`）：① `Utils.toArray` 缺 BigNumber 类数组分支、② `Hash.bytes` 把 BigNumber 当空输入（此前 `sha256(BigNumber)` == `sha256("")`，使 RFC6979 签名与固定 TS 不同）。新增 `UtilsBigNumberArrayRegressionTest`（2 例，额外 Java 回归）。聚焦验证 97/97。
- **唯一在跑的代码缺口**：`beef`（Beef.test.ts，21 例）已派新代理接手；`BeefTest` 同时承载 `Transaction.test.ts` 用例，要求先出探针与计划、再一次性重写并保持既有断言与映射身份。

### 本轮批量采集结果（13 个局部 / 270 例 / 785 断言，来源 `00f91838`）

aesgcm 30/457/334、signature 36/51/46、reduction-context 29/38/70、hash 30/150/92、window-cwi 31/60/61、public-key 14/34/18、public-key-additional 32/48/47、locking-unlocking-script 12/29/14、script-additional 14/37/30、binary-fetch-client 12/13/25、bignumber-additional 19/55/37、r-puzzle 9/17/9、p2pkh-async-backend 2/10/2 —— 全部 verify + tamper 通过。

修掉两处适配器缺陷：`capture-keys-local.py`／`capture-gap-local.py` 误调 `prepare-transaction-local.py`（改用各自登记表的 prepare），以及 `sfta` 计划目录名不含局部名导致反查失败（已重命名为 `<局部>-plan-<日期>` 并重新登记）。

**仍待采集 6 个**：ecdsa、schnorr、symmetric-key、ecies、chronicle-opcodes、simplified-fetch-transport-additional —— 本轮失败均因 `beef` 代理正在书写 `BeefInputReplay.java` 导致模块编译中断（非内容问题），随最终窗口一并重采。

### 结项映射与剩余缺口（`item-locals.json`）

由登记表与冻结用例自动算出“事项 → 覆盖它的局部”。**计划覆盖已完整、可在最终窗口后直接结项的**：`wallet-wire` 128 例／2 局部、`wallet-hosts` 126／3、`transaction-verification` 53／3、`script-templates` 17／3。

**仍有未计划用例的事项（共约 565 例，交给下一波代理）**：wallet-client 100、script-spend 91、transaction-complete 86、auth-sessions 85、http-chain 47、curve 38、keys-signatures 37、script-vectors 26、hash-random 22、transaction-beef 21（beef 在做）、symmetric 7、auth-transport 3、bignumber 2。

### 证据完整性复检（20260930 凌晨）

对 24 个最近采集的标准局部逐个复跑 `local-evidence-gate.py verify`（不跑 Maven、不占共享锁）：**24/24 通过**，覆盖 hash、window-cwi、r-puzzle、p2pkh-async-backend、aesgcm、signature、reduction-context、public-key、public-key-additional、locking-unlocking-script、script-additional、binary-fetch-client、bignumber-additional、ecdsa、schnorr、hd、script、push-drop、transaction-evidence、transaction-verifier、beef-party-additional、merkle-path、merkle-path-safe-offsets、merkle-path-bench。它们绑定不同 Java 来源（并行改动所致），最终窗口统一重采后即可全部 `currentCaptureVerified=true`。

### hex-bn 收尾（方案①，20260930 02:20）

- 给 `build-full-run-probes.py` 增加 **`full-run-overrides.json` 覆盖机制**（合并 files 探针、把 resolvedLocals 从 unresolved 移除）；
- 新增 `full-run-overrides.json`：为 `hex.test.ts`（探针 `capture-hex.cjs`）与 `BigNumber.constructor.test.ts`（`capture-bn-constructor.cjs`）登记输出环境变量，并在 hex 探针上挂 emit：`prepare-hex-bn-inputs.py emit-ts --kind both --raw-hex {runDir}/hex.raw.jsonl --raw-bn {runDir}/bn.raw.jsonl --inputs {output} --assertions {runDir}/ts-assertions.jsonl`（断言由 legacy 转换器直接写入本轮断言文件；这些探针不加载 `capture-parity`，标准断言发射器会因“没有原始断言轨迹”跳过，不会互相覆盖）；
- `prepare-hex-bn-inputs.py` 的 `--run-id` 改为可缺省（回退 `EVIDENCE_RUN_ID`），因为全量分派表只替换 `{runDir}`／`{local}`／`{output}`；
- **分派表现状：110 原文件／125 探针／90 环境变量，`unresolved=0`，无探针原文件 23 个（均为尚未计划的代理在飞范围）**。
- 待办：在锁空闲时用 `run-full-ts-capture.py` 做一次只含这两个文件的子集自测（`--files` + `--allow-unresolved`），确认 emit 与断言落地格式正确。

### 全量分派表收敛（20260930 02:10）

- `public-key`／`public-key-additional` 两个局部此前不在全量分派表里（探针用变量索引读 `process.env[...]`，静态扫描识别不到）。按既有约定在各自探针头部加了一行字面量声明（`process.env.MIGRATION_PUBLIC_KEY[_ADDITIONAL]_TS_OBSERVATIONS`）后已正确解析。
- 分派表现状：**108 个原文件／123 个探针／90 个环境变量，未解析仅剩 `hex-bn`**；无探针原文件 25 个（286 例）。
- **关键风险清单**：无探针原文件里只有 **36 例是“已计划但全量运行拿不到输入”**——即 `hex-bn` 旧管线覆盖的 `BigNumber.constructor.test.ts` 28 例 + `hex.test.ts` 8 例；其余 250 例尚未计划（正在收口的代理会补）。
- `hex-bn` 收尾两选一：①给 `build-full-run-probes.py` 加 `full-run-overrides.json` 覆盖机制，并让该局部的探针改为同时喂 `capture-parity`（断言交给标准发射器），legacy 转换器只产输入；②在分派表里为该局部登记“direct 模式 + 自定义 emit”，并让 run-full-ts-capture 支持 emit 写 sidecar 断言后合并。二者都要在锁空闲时实测。

### 缺口收敛到 94 例（20260930 03:30）

- `spend-core` 修复成功并采集成 20 例／20 输入／34 断言（`verify` 通过）——首采暴露的断言差异由修复代理解决。
- `item-locals.json` 刷新：**22/28 个实现事项计划完整**；未计划 94 例，全部落在在跑代理范围内（auth-sessions 30 由 peer 接线、hash-random 22／keys-signatures 8／symmetric 7／bignumber 2 由原语剩余批、transaction-complete 25 见下）。
- **补派最后一处无人认领的缺口**：`Transaction.performance.test.ts`（25 例）→ 局部 `transaction-performance`，并明确性能类口径：耗时阈值按“布尔是否满足 + 规模计数”记录，确定性字节/哈希/txid 仍逐值比较，跨语言毫秒不逐值比较。

### 分派表解析缺陷修复（20260930 03:40，主代理）

**现象**：spend（9）与 http-chain（5）等 14 个局部登记后**没有进入全量分派表**（`unresolved`），最终单次全量运行会拿不到它们的输入。

**根因**（两步定位）：①驱动里 `env[entry['ts_observations_env']] = str(evidence / 'ts-calls.raw.jsonl')` 的右值先按字面量求值，`existing()` 会到**计划目录**里找同名文件；这些代理的探针把 `ts-calls.raw.jsonl` 残留在了计划目录，于是被判成“冻结语料”（`file`）而不是“本轮产物”（`output`）；②`Div` 分支里 `('run_dir',)` 与判成 `file` 的右值组合没有兜底，最终 `plan['outputs']` 为空 → 该局部 unresolved。

**修法**（`build-full-run-probes.py`，两处最小改动）：`Div` 分支的语料直取规则排除 `run_dir`；`run_dir / x` 分支在右值被判成 `file` 时按 `output` 处理（取 basename）。
（先试过“按文件名过滤计划目录”，但会误伤 ARC 的合法语料 `MIGRATION_ARC_RANDOM_REPLAY`，已回退。）

**结果**：分派表 **123 原文件／141 探针／105 环境变量，`unresolved=0`**；无探针原文件 23→10，且其中**已计划却拿不到输入的用例为 0**——剩余 10 个原文件（Peer 30、Transaction.performance 25、PrivateKey 系列、Random 系列、Hash.additional、AESGCM.man、AsyncCryptoBackend、SymmetricKeyCompatibility、BigNumber.dhGroup，共 94 例）正是三路在跑代理的范围。

### beef 投影二次收敛与更实质的差异（20260930 03:20）

- 第一次采集失败在 `constructor-01`：探针的 `MerklePath` 构造投影仍带 `txid`，Java 侧对应站点也带。已把**构造投影**两侧一并收敛为只比较 `{offset, hash}`，重跑探针（21/21、390 输入、123 断言，注意轨迹文件是**追加写**，重跑前必须先删）后重新冻结，计划不变。
- 第二次采集：`constructor-01` 差异消失，只剩 `batchProvenMergeEqualsSequentialBytes`（caseId `cb017c09…`）的 **`toHex-194` 结果字节不同**——即同一输入下 TS 与 Java 生成的 BEEF 字节不一致。这已超出“投影/别名副作用”范畴，指向 Java 侧 `combineCompatibleBumps`／`MerklePath.combine`／`trim` 的合并语义差异。
- 已派诊断代理：先定位首个差异字节与长度差，对照 TS `Beef.mergeProvenTxs` + `MerklePath.combine/trim` 与 Java 同名实现，确认是否生产缺陷；是则最小改动修复并重新采集+门禁，否则给出可复现证据与可选处置。

### transaction 局部交付

`transaction`（`Transaction.test.ts` 61 例／233 输入／161 断言）代码侧完成并登记，离线自检：JUnit Launcher 61/61、java-inputs 233/233 全等、`compare_actuals` 零不一致。其冻结副本按登记的 8 个 Java 类裁剪用例（同文件另有 659 例向量局部），并把 8 份 Surefire 合并成一个 `<testsuites>`。

### 首采暴露内容问题与定点修复（20260930 03:00）

对**风险最高**的已交付局部先做小窗口采集，结果：`lrshiftnum` 4/28/29、`default-http-client-additional` 6/10/14 通过（含篡改门禁）；5 个局部失败——`spend-core`（断言实际结果不一致 `Spend.test.ts:580:7`）、`spend-verifier`（Java 缺一个输入用例 `db11cbc5…`）、`chronicle` 与 `normative-vectors`（同一族：`TransactionSignature.formatOTDA-02` 的入口/参数投影不一致）、`default-http-client`（`defaultHttpClient-01` 参数一致但 Java 返回 null）。均为**重放接线/投影问题**，非生产算法差异。

已派两路修复代理定点处理（一路修 chronicle+normative-vectors 的 format/formatOTDA 投影，一路修 spend-core/spend-verifier/default-http-client），要求改投影而不放宽断言、不改生产源码，修好后重采 + 篡改门禁 + preflight。

### beef 投影收敛（主代理亲自完成）

TS 的 `mergeProvenTxs` 会就地改写**调用方传入的** MerklePath（`group.paths[0]`），从而给其叶子补 `txid` 标志；Java 为新路径建新列表、不改调用方对象。这属别名副作用、非 API 结果（上游用例只断言批量与顺序合并的字节相等与 `isValid`，两侧皆过）。已把探针与 Java 重放的**输入侧**叶子投影收敛为 `{offset, hash}`，Beef 自身 bumps 的叶子仍逐值比较 `txid`；重跑探针（21/21、390 输入、123 断言）后重新冻结，**新计划与旧计划逐用例完全相同**，已重新登记。

### 代码优先策略见效（20260930 02:30）

切换后已有两路交回**代码侧完成**的简报，且都附了无锁离线证据：

| 代理 | 局部 | 用例/输入/断言 | 离线证据 |
| --- | --- | --- | --- |
| wallet-client | wallet-client／-additional／-substrate | 1/3/6、61/107/108、38/38/70 | javac 子集编译 0 error；JUnit launcher 100 全绿；Java 写出输入与样本 ID 完全对齐；复用 `evidence-bundle.build` 比对三局部全部 ok；篡改模拟两条路径均被拒；清空输入环境变量后行为不变 |
| curve | curve-unit／curve-additional | 18/82/61、20/23/40 | 隔离 javac 0 error；JUnit 38/38；输入同 ID 同序；`audit-tests.compare_actuals` 逐断言 **0 处不符** |

主代理独立核验（不占锁）：`validate-plans.py` **114 个标准局部通过、0 失败**；分派表 **110 原文件／126 探针／91 环境变量，`unresolved=0`**；上述五个局部均已登记且各自的原文件都已接入探针。

当前唯一编译阻塞：`transaction/TransactionInputReplay.java:356`（transaction 代理在飞）。其余代理继续代码收口。

### 死锁诊断与第二次策略切换（20260930 02:20）

**诊断**：最近 45 分钟全队 **0 个采集落地**。锁并非卡死（持有者是 480% CPU 的 Maven 运行），真正原因是**8 路代理并行编辑同一测试模块**：任何一个 2–4 分钟的捕获窗口内都会有别人的文件在飞，于是捕获必然以 `BUILD FAILURE`（他人在飞文件）或“采集期间源码发生变化”收场——互相等待形成死锁。

**切换**：已通知全部 8 路代理**停止一切采集**（recapture／tamper／聚焦 clean test 都不再执行，编译自检最多一次 `test-compile`），改为把代码侧做到“一编译就过”并用不占锁手段自检（javac 单编、`offline-*-check.sh`、`audit-tests.compare_actuals` 离线比对），然后交简报（用例/输入/断言数、文件清单、是否已登记、还差哪一步）。

**后续**：等所有人交完代码侧，主代理确认 `test-compile` 干净、提交在飞文件，再**独占**运行统一采集窗口（`recapture-all.sh final-<日期>`，含篡改门禁与 preflight）。期间不再允许任何并行 Maven 操作。

### 采集队列瓶颈（20260930 02:00）

各代理已进入采集阶段，但**共享 `run.lock` 成为唯一瓶颈**：现场有 5 个 flock 等待者 + 1 个 java 进程，多个局部已完成 TS 侧（01:32–01:54）却还在排队等 Java 侧 `clean test`。按每个局部 2–4 分钟估算，仅当前排队的采集就需要 1–2 小时；主代理因此**完全不占锁**（连编译复检都停掉），只做只读校验与登记。

推论：最终统一窗口（65+ 个局部）必须在**所有代理停止采集之后**独占运行，否则队列会互相拖延；窗口期间也不要并行做任何 Maven 操作。

### 结构覆盖率跃升（20260930 02:00）

- **已计划 4998/5329（93%）**，未计划降到 **331 例**；113 个标准局部的计划全部通过结构校验，且**没有任何用例被两个局部同时登记**（无冲突）。
- **计划已完整的事项 18 个**（上轮仅 4 个）：script-model 1104、wallet-contracts 253、byte-codecs 192、auth-transport 183、curve 144、wallet-wire 128、wallet-hosts 126、compat 122、wallet-client 100、transaction-base 74、wallet-keys 71、broadcasters 68 等。
- 仍有缺口：script-spend 91、transaction-complete 86、auth-sessions 45（代理登记中）、script-vectors 25、hash-random 22、transaction-beef 21（beef 在做）、http-chain 17、keys-signatures 15。
- `item-locals.json` 已按最新登记刷新，可用于最终窗口后逐事项出任务级对照。

### 编译恢复与本轮协调（20260930 01:30）

- 我修掉最后一个阻塞：`auth/SessionManagerInputReplay.describeOptional` 的返回类型从 `Map<String,Object>` 改为 `Object`（原语义是 `value ?? undefined()`，非空时可能是字符串），整模块恢复可编译。
- spend 代理确认 `clean test-compile` **exit=0、零错误**；http-chain 代理按我的提示把 10 处 `MockFetch` 改成 `new FetchHttpClient(fetch)` 后其文件零错误。
- 四路代理（wallet-client、curve、auth、http-chain）与 spend、beef、transaction、keys-small 已陆续进入采集阶段；`run.lock` 队列饱和（我的编译复检排队 600 秒超时），因此主代理暂停一切会占锁的操作，把窗口让给采集。
- 局部登记数 125（89 个有运行产物，正在快速增加）。

### 并发阻塞与协调（20260930 01:06）

- `script` 包在飞文件出现实参表**尾随逗号**语法错误（`ChronicleTest:27`、`LrShiftNumTest:23`、`NormativeVectorsTest:35/59`、`SpendAdditionalTest:94`、`SpendCoreTest:51`、`SpendVerifierTest:34`），导致整个测试模块编译失败，wallet-client／curve／auth 等代理的采集全部被拒；已定向通知 spend 代理优先修复。
- wallet-client 代理代码侧已完成并冻结计划：主 1 例／3 输入／6 断言、additional 61／107／108、substrate 38／38／70（合计 100 例／148 输入／184 断言），只等编译恢复。
- 局部登记数 118（89 个有运行产物）。

### 第八波待派（并发已满，等一路空闲立即派发）

**并发上限 8 个活跃子代理**（超出时报 `subagent limit reached`）。当前 8 路在跑，因此最后一批 46 例待有空位再派，范围已核准：

| 文件 | 缺口 | 局部名 |
| --- | --- | --- |
| `src/primitives/__tests/PrivateKey.test.ts` | 7 | `private-key` |
| `src/primitives/__tests/PrivateKey.split.test.ts` | 8 | `private-key-split` |
| `src/primitives/__tests/Random.test.ts` | 5 | `random` |
| `src/primitives/__tests/Random.additional.test.ts` | 8 | `random-additional` |
| `src/primitives/__tests/Hash.additional.test.ts` | 9 | `hash-additional` |
| `src/primitives/__tests/AESGCM.man.test.ts` | 1 | `aesgcm-man` |
| `src/primitives/__tests/AsyncCryptoBackend.test.ts` | 3 | `async-crypto-backend` |
| `src/primitives/__tests/SymmetricKeyCompatibility.test.ts` | 3 | `symmetric-key-compatibility` |
| `src/primitives/__tests/BigNumber.dhGroup.test.ts` | 2 | `bignumber-dh-group` |

注意：`Random*`／`AsyncCryptoBackend` 在 `audit-tests.py` 里已有固定语义规则，探针必须按原观察形状记录；`PrivateKey.test.ts` 的 10,000 次循环按既定 1:1 口径（输入样本取代表迭代 + 断言逐执行登记）。

### 第七波（补派，小范围）

- `keys-small` 代理：ECDSA.additional 12 + ECDH 2 + Secp256r1 7 + bug-31 1（22 例，四个小文件）。
- `http-chain` 代理：先核对 http-chain 事项中仍无计划的文件（约 47 例，含 BlockHeadersService 19 等），要求范围偏大时优先收口前 2 个文件并交剩余清单，不留半成品 Java。
- 计划结构校验：96 个标准局部全部通过（并行期仍可用 `validate-plans.py` 体检）。未计划用例仍为 565 例，等各代理登记后下降。

### 第六波（20260930 凌晨）与代理失败情况

- `tx-complete` 与 `curve/keys` 两路代理**中途失败且未留收尾报告**：前者未落任何文件；后者留下 `curve-locals.py`、`prepare-curve-local.py`、`capture-curve-local.py`、`capture-curve-additional-inputs.cjs`、`CurveAdditionalInputReplay.java`（可续用）。
- 因此改为**小范围重派**：`transaction`（Transaction.test.ts 61 例）与 `curve-unit`+`curve-additional`（38 例，续用前任产物）各一路。
- 失败代理提示：范围过大（8 个文件/75 例）时容易中途终止；后续按 1–2 个文件为单位派发。
- **PrivateKey.test.ts 的 10,000 次循环决策**：按 1:1 口径处理——探针记录有代表性的若干次迭代作为输入样本（供 `loopSamples` 结构覆盖），断言实例仍按每次执行登记（`<站点>#<轮次>`），即该用例的计划会达到 4 万级实例；这是原测试真实执行量的忠实反映，不做抽样削减。
- 本轮补采成功：`ecdsa` 15/31/21、`schnorr` 12/63/15（verify + tamper 通过）。`symmetric-key`、`ecies` 因“采集期间源码变化”失败，`chronicle-opcodes`、`simplified-fetch-transport-additional` 因他人在飞编译错误失败——四者代码侧均已就绪，随最终窗口重采。

### 第五波分工（20260930 凌晨已派发，5 路并行）

| 代理 | 范围 | 用例 |
| --- | --- | --- |
| beef 代理 | `Beef.test.ts` 21 例（镜像 `BeefTest`） | 21 |
| wallet-client 代理 | WalletClient 三文件 | 100 |
| auth 代理 | auth-sessions 六文件 + SimplifiedFetchTransport 基础 3 例 | 88 |
| spend 代理 | script-spend 缺口 91 + script-vectors 缺口 26 | 117 |
| tx-complete 代理 | `Transaction.test.ts` 61 + `Transaction.performance.test.ts` 25 | 86 |
| curve/keys 代理 | Curve.unit 18 + Curve.additional 20 + keys-signatures 剩余 37 | 75 |

派完后仍未分配的缺口：hash-random 22、symmetric 7、bignumber 2、http-chain 47（共 78 例），等有代理空闲再派。

### 最终窗口规模与预计耗时（20260930 凌晨）

可重采局部 **65 个**（58 个已有运行产物）；每个局部的 Java 侧都要一次无过滤口径的 `clean test -Dtest=<类>`，模块重编译主导，预计 **2–3 小时**串行。窗口内禁止任何人改 Java 源码，否则来源摘要前移、该批作废。当前唯一在改 Java 的是 `beef` 代理（`BeefInputReplay.java` 还剩 1 处类型错误），其余 10 个代理均已收工。

### 统一窗口顺序（待 beef 落地后执行）

1. `./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml test-compile` 确认编译干净；
2. `./recapture-all.sh final-<日期>`（对所有登记了 capture 的局部逐个重采 + 篡改门禁，目录与来源统一）；
3. `./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-final-<日期>.json`（期望 `planErrors=[]`、大量 `currentCaptureVerified=true`）；
4. 对可结项事项跑 `local-task-parity.py` 出任务级报告并更新 feature_list。

## 协作策略切换：先收口代码，统一窗口再采集（20260929 晚）

`run.lock` 一度积压 12 个等待者（队首约 30 分钟），且测试模块被多份在飞文件反复打断编译。已通知全部在跑代理：**停止重试式采集**，改为①优先修完各自文件的编译错误（当前阻塞项：`HashTest`、`PublicKeyTest`、`PublicKeyAdditionalTest`、`ReductionContextTest`、`SignatureTest`）；②把探针、计划、Java 重放、测试接线、登记等代码侧做完；③需要验证时低频取锁（先 `test-compile`，失败等 5 分钟）；④各自交“待采集清单”。随后由主代理在静默窗口按登记表串行重采（`recapture-all.sh`）并出任务级对照。

### hex-bn 转换器（本轮已完成部分）

- 新增 `prepare-hex-bn-inputs.py`：把旧管线 `replay-legacy-inputs.emit_ts` 包成 CLI（`emit-ts` 子命令），`capture-legacy-side.py` 改为调用它；用既有轨迹验证：输入 71 行、断言 71 行，身份与值与旧输出**逐项一致**。
- 两个旧探针补了“固定原文件：src/...test.ts”声明，分派表因此能把探针唯一对应到原文件（原文件解析数 66→77、探针 80→93）。
- 仍未解析：分派表无法为 `hex-bn` 解析 raw 轨迹的环境变量取值（旧驱动用 `evidence / (kind + '.raw.jsonl')` 计算，解析器不认），且该局部断言来自旧转换器而非 `capture-parity`。**待办**：在 `build-full-run-probes.py` 增加 `full-run-overrides.json` 覆盖机制，或把 hex-bn 升级为标准局部（探针 + `emit-assertion-observations`）。

## 全量运行接口已交付（20260929）

`fullRun` 段已写入 `full-evidence-locals.json`，preflight 的 `missingFullRunInterfaces=[]` 达成。新增：`build-full-run-probes.py`（生成 `full-run-probes.json`：84 局部／66 原文件／80 探针）、`capture-full-dispatch.cjs`（按 testPath 分派探针）、`run-full-ts-capture.py`（全量 TS + raw→emit-ts 转换 + 采集后校验）、`run-full-java-capture.py`（无过滤 `clean test` + 全部 `MIGRATION_*_TS_INPUTS` 指向本轮 ts-inputs + Surefire 汇总）。自测：三类代表子集 Jest 69/69、官方 `evidence-bundle capture` 端到端 EXIT=0（inputs 251 行、assertions 159 行、missing/extra/duplicates 均为 0）。

**严格模式仍会拒绝的三类缺口**（最终全量运行前必须清零或明确处置）：
1. `unresolved` 2 个：`chronicle-opcodes`（无可用探针）、`hex-bn`（跨 2 原文件 2 探针且无 CLI 转换器）；
2. **67 个 catalog 原文件没有任何探针**（auth 8／compat 2／primitives 25／script 13／transaction 14／wallet 5）；
3. **30 个 raw 局部缺 CLI emit-ts 转换器**（auth-fetch-property、bignumber-*、byte-base58、cached-keyderiver、drbg29、http-wallet-json、jacobian、json-byte-encoding、keyderiver、mnemonic-*、origin-header5、point-*、protowallet*、script-spend-shared-vectors、transaction-shared-vectors、utils-property、validation-helpers、wallet-error、wallet-property、wallet-wire、werr-constructors）。

另：Java 侧 35 个 `MIGRATION_*_TS_INPUTS` 可全部共用同一份 `<runDir>/ts-inputs.jsonl`；另有 38 个 `-Dmigration.*` 冻结语料属性仍驱动部分重放（不消费本轮输入），属“局部尚未升级到标准接口”。

## 全量分派策略（已拍板）

`run-full-ts-capture.py` 必须把三类探针都纳入分派：直写型、raw 型（再经 `prepare-*-local.py emit-ts` 转换）、外部语料型（由分派器按适配器 TS 分支的 `env[...]` 设置 `MIGRATION_*_RANDOM`／`_VECTOR_CATALOG`／`_META`／`_TS_CLOCK` 等语料变量）。**默认严格**：无法解析探针或语料的原文件必须让整轮非零退出并打印缺口，同时写 `unmapped-files.jsonl`／`unresolved-probes.json`；`--allow-unresolved` 只允许子集自测使用，不得出现在 `fullRun.tsCommand` 里。全量运行不允许出现“绿但不完整”。

## 计划结构校验（并行期可用）

`python3 validate-plans.py` 只读计划／catalog／mapping，不要求源码稳定，可随时运行；preflight 因并行改源码被拒时用它先做结构体检。当前结果：70 个标准局部计划全部通过（0 失败），16 个 `captureKind=specialized-local`（auth-fetch 系列，`deriveCatalogFromPlan`）走各自专用校验，不在本脚本范围。

## 收尾统一重采

并行子代理的 Java 改动会不断推进来源摘要，因此**收尾时**在所有人停止改源码后执行一次统一重采：`./recapture-all.sh <日期标签> [局部名...]`（不传局部名则重采全部登记了 capture 适配器的标准局部，并逐个跑篡改门禁）。随后 `python3 full-evidence-preflight.py` 应显示这些局部 `currentCaptureVerified=true`；再对每个待结项用 `python3 local-task-parity.py --task <事项> --local ... --output <目录>` 出任务级报告，最后提交。

## 验证与收工

- `migration-impl-transaction-base` 五个文件全部落地标准双侧局部（fee-model 18、live-policy 8、ef-cache 4、transaction-additional 20、signature-additional 24，合计 74 例／150 输入／115 断言），同一 Java 来源下 verify 与 tamper 通过，聚焦 `clean test` 74／74。任务级对照与 `done` 待并行子代理的 Java 改动提交后统一执行。
- 广播器四文件已结项（68/68、169/169，提交 `1f1c660` 记录适配器升级）；xdm-browser-boundary、react-native25、wallet-wire 三局部已验证，钱包宿主与 WalletWire 两项仍缺 HTTPWalletWire 46 例、window.CWI 31 例；transaction-beef 五文件 83 例已派给第三个子代理。
- 并行协作已启用：`lock.sh` 串行化共享目标工程的 Maven／采集，`register-local.py` 带 flock 登记局部，`doc/子代理采集作业说明-20260929-175251.md` 是子代理作业规范；两个后台子代理分别处理广播器五局部与钱包宿主／WalletWire 三局部。
任务级对照用 `python3 local-task-parity.py --task <id> --local <局部> … --output <目录>`（复用 `audit-tests.py` 的比较规则并核对冻结用例覆盖）。`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。本代理 shell 的 PATH 前置 DSH checkout 的 `node_modules/.bin`，`pnpm --version` 会解析到 11.7.0，使 `./init.sh` 报“全局 pnpm 版本未变”失败；去掉该 PATH 项后 `./init.sh` 全绿（全局 pnpm 仍为 11.23.0），任务命令走 `./pnpm.sh`，不受影响。

每个已完成 Java 功能均在目标仓库独立提交。对称与 Compat 功能项状态已更新；继续逐项核对依赖链、当前接口行为和 P0 全量输入证据。新增 Java 变更后重跑完整 clean test 并封存 XML；现有完整回归快照绑定 `c23c6f6`。其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
