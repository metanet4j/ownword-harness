# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源，[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。最近一次目标 Java 宿主无过滤 `clean test` 绑定提交 `4e656ae`（来源摘要 `382ac6c6…`）：167 份 Surefire 报告为 5437／5437、无失败／错误／跳过，同次覆盖全部 5329 个映射身份且无重复，另有 108 个 Java 回归。报告封存于 `.cache/evidence/wallet-contracts-full-surefire-20260929/`，日志 `.cache/evidence/wallet-contracts-full-java-20260929.log`；该来源与八个当前局部一致，后续源码变更仍须新一轮无过滤回归。对称加密 52／387、Compat 122／281、交易完整功能 745／1390、交易验证 53／162、认证会话 85／160、认证传输 183／968、DRBG 29／30 已有固定原用例／逐断言任务级对照；AuthFetch 属性 300 组固定 TS 实际输入与 Java 消费一致。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3576／3576 且已复核，21 个 API 批次均完成；原用例映射 5329／5329，测试站点映射 7554／7554。固定 TS 标准／manual Jest 原始报告合计 5329／5329，并通过 `audit-tests.py compare-ts`。Spend 的第二组 455 个独立注册已由新 Java 类和新映射收口。对称模块 fixed TS 原 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过，连同当次 Java 原始轨迹和逐字节摘要的专用桥接见 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`。API 总审计见 `doc/API跨任务接口复核-20260927-000100.md`；Transaction 非阻塞、三个异步异常入口和 PATCH 状态说明修复已合入当前累计回归。

## 并行工作

- AuthFetch 固定原测试 134／890 与 Transport 合批 183／968 已在 `c0d9fdd` 对照；属性测试 300 组 fast-check 实际输入已封存并由 Java 同批重放，600 条断言精确一致。
- Hex＋BigNumber 构造 36 例、Base58 六例、BRC100 属性两例 600 组、WERR 32 例、JSON 字节 10 例、BRC100 字节 23 例、WalletError 39 例已有局部同输入核验。ValidationHelpers 严格区分 `undefined`／`null` 后，147 个固定原例的 149 组输入、203 条断言一致，另有 6 个 null 边界回归。证书五文件 50／50、128／128 已分批局部核验；其中 ValidateCertificates 严格重采 8／8 原例、21 组实际输入、16 条断言通过。Script／Spend 共用向量 1940 例、Transaction 向量 659 例、Chronicle 74 例亦有局部核验。Wallet Contracts 的 253／1003 当前值对照已通过，其余输入账本继续补齐。AuthFetch.additional 已完成两批共 41 例局部输入采集；WalletWire.integration 82 例正在重采；通用断言 helper 的真实调用历史审计仍在继续。
- DRBG 原 29 例已在 `c23c6f6` 完成双端正式采集并登记：72 条真实入口（含 15 个 NIST 守卫分支）与 30 条断言双端逐值一致，30 条未执行断言按 `drbg-nist-invalid-input-v1` 与分支样本有据，输入／断言／分支三类篡改均被拒；该登记绑定 `c23c6f6`，在当前 Java 版本下被来源复核拒绝，须随最终全量运行重采。计划冻结与探针见 `drbg-input-plan.json`、`capture-drbg-inputs.cjs`、`prepare-drbg-inputs.py`，证据见 `doc/DRBG原输入验收-20260928-181254.md`。
- knownTxids 付款原 6 例已在 `79c4b3b` 通过局部门禁：6 条真实输入、8 次付款调用与 25 条断言双端一致，付款输入与断言篡改被拒；Java 侧按语料重建 `Response` 且不伪造宿主 `bodyUsed`。证据见 `.cache/evidence/known-payment-local-20260928-03/`，文档 `doc/knownTxids付款输入验收-20260928-201034.md`。
- knownTxids 真实 Peer 原例已在 `b7acbb4` 通过局部门禁：随机源、两次 fetch 入口、Peer 前置状态、交付帧、发送载荷与结果、监听器编号逐字段一致，6 条断言一致；入口探针与 Peer 探针分两次 Jest 运行后合并语料，文档 `doc/knownTxids真实Peer输入验收-20260928-210831.md`。该文件 17 例输入重放已全部落地。
- 八个局部已在 Java 来源 `382ac6c6` 重采并通过 `local-evidence-gate.py`：钱包契约六文件（wallet-property 2/600/600、brc100-byte-encoding 23/57/62、werr-constructors 32/32/40、wallet-error 39/54/79、validation-helpers 147/149/203、json-byte-encoding 10/26/19）、HTTPWalletJSON 53/214/73、toOriginHeader 5/5/5。`migration-impl-wallet-contracts` 与 `migration-impl-wallet-json` 已按依赖顺序标记 `done`，`nextItem` 改为 `migration-impl-wallet-keys`。刷新记录见 `doc/钱包契约与钱包JSON证据刷新-20260929-020724.md`。
- `migration-impl-wallet-keys` 已完成三个文件：KeyDeriver（17／49／37，子类覆写 + 深度守卫）、ProtoWallet.additional（11／22／11，记录 keyDeriver 前置状态，`WalletKeysEntropy` 与 TS 固定熵流对齐）、CachedKeyDeriver（13／49／44，循环站点样本 + `timing-ms-v1` 耗时规则，账本改为用例结束落盘以免采集开销进入耗时断言）。三者都是标准双侧局部并通过 verify／tamper。
- Java 侧提交会推进来源摘要（`382ac6c6`→`f16b01df`→`8cf69655`），已完成的局部随即变为过期；按既定策略在 wallet-keys Java 改动收尾后统一重采 9 个局部（当前预检只覆盖 protowallet-additional）。
- P0 采集来源门禁的语义规则 10／10、bundle 18／18、关联 3／3、宿主审计 41／41 自测通过。最新 `full-evidence-preflight.py` 结构计划覆盖 4069／5329，仍缺 1260 例，来源复核覆盖 13 例（`currentCaptureVerifiedCases`，其余局部待 wallet-keys 收尾后统一重采）；其余 41 个标准局部绑定旧执行器或旧 Java 版本，须在最终单次全量运行中重采。`ParityRecorder.errorName` 现按异常公共 `name` 字段记录 JS 可见错误名，WERR 系列不再被记成 `Error`。旧 Java 完整回归和 TS 原始报告不能代替单次完整双侧来源。通用断言 helper 已修复一批 null/undefined 伪记录，余下的完整调用历史和对象匹配语义正在修复并重新核对受影响局部证据。完整 `audit-tests.py check` 仍须全量真实输入和断言采集。

## 验证与收工

`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。

每个已完成 Java 功能均在目标仓库独立提交。对称与 Compat 功能项状态已更新；继续逐项核对依赖链、当前接口行为和 P0 全量输入证据。新增 Java 变更后重跑完整 clean test 并封存 XML；现有完整回归快照绑定 `c23c6f6`。其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
