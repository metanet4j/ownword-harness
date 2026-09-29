# 当前进度

## 执行位置

权威任务状态见 [feature_list.json](feature_list.json)：43 个执行事项中 22 个 `done`、6 个 `in-progress`、15 个 `not-started`；`activeItem=nextItem=migration-impl-transaction-base`。API 映射 3576／3576 项已复核，21 个嵌入批次均完成；原用例映射 5329／5329 个、源码测试站点映射 7554／7554 个。六模块完整门禁尚未通过。

目标 Java 工程在提交 `1da225e` 的宿主无过滤 `clean test` 通过 5437／5437，失败／错误／跳过均为 0；167 份 Surefire 报告覆盖全部 5329 个映射身份且无重复，另有 108 个 Java 回归，报告封存于 `.cache/evidence/wallet-keys-full-surefire-20260929/`，日志 `.cache/evidence/wallet-keys-full-java-20260929.log`，Java 来源摘要 `0a119349…`（与 wallet-keys 六个局部采集同一来源）。此前绑定 `382ac6c6` 的快照已过期。固定 TypeScript 仓库及其他四个 Java 工程只读；目标工程 `metanet4j-bsv-sdk` 是唯一可改代码仓库。工作区根仓的既有无关改动保留。

## 已取得的任务级验收

- 对称加密：固定 TS 原规模 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过；独立 Java `c0d9fdd` 工作树 manual 1／1，逐字节比较 536,870,928 次。普通原始 TS／该版 Java 轨迹 51／51、384／384 逐字段一致；合计 52／52、387／387，报告 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`，篡改反例 7／7 通过。
- Compat：主目标 `c0d9fdd` 的原始 Java 轨迹与固定 TS 五文件重新比较，122／122 个用例、281／281 条断言一致，报告 `.cache/evidence/java-full-after-auth-property-20260926/compat-task-parity-current.json`；依赖满足后已标记 `done`。
- 交易完整功能：目标提交 `f1b5752`；固定 TS／Java 745／745 个原用例、1390／1390 条实际断言一致，报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。
- 交易验证与证据：目标提交 `dfacef7`；固定 TS／Java 53／53、162／162 条实际断言一致，报告 `.cache/evidence/transaction-verification-parity-main-20260926.json`。交易模型 API-09 的 126 项与证据 API-10 的 176 项均通过单批审计。
- 认证会话：目标提交 `94d5bc0`，异步存储修复 `7c382f6`，公开异步存储入口 `3e58d02`；固定 TS／Java 85／85、160／160 条实际断言一致，另有两例延迟 Future 回归，报告 `.cache/evidence/auth-sessions-parity-main-7c382f6.json`。API-19 的 101 项通过单批审计。
- 认证传输：固定 TS／Java 的 Transport＋AuthFetch 183／183 个原用例、968／968 条实际断言已在 `c0d9fdd` 对照通过，报告 `.cache/evidence/java-full-after-auth-property-20260926/auth-transport-task-parity-replayed.json`；两条运行时间戳与堆栈按固定字段语义核验。AuthFetch 属性测试固定 TS 300 组实际生成输入已由 Java 同批重放，600／600 条断言精确一致，语料 SHA-256 为 `b0cf9d142fed85b2a9a82b85ac4b254ae6408da60ffa6457f98e757825818392`。本任务 taskAcceptance 已通过，排期状态仍等待依赖。
- DRBG：目标提交 `c23c6f6`；固定 TS／Java 原例 29／29、实际断言 30／30 逐值一致，72 条真实入口（57 个构造／生成入口＋15 个 NIST 守卫分支）双端一致，30 条未执行断言按固定规则与分支样本有据，审计摘要 `{"status": "PASS", "comparedAssertions": 30, "justifiedUnexecutedAssertions": 30}`，报告 `.cache/evidence/drbg-parity2-20260928.json`，文档 [DRBG原输入验收](doc/DRBG原输入验收-20260928-181254.md)；输入、断言与分支三类篡改均被拒。
- knownTxids 付款：目标提交 `79c4b3b`；该文件固定 TS 17／17、Java 17／17，6 个付款用例的 6 条真实输入与 8 次付款调用逐字段一致、25 条断言一致，付款输入与断言两类篡改被拒，文档 [knownTxids付款输入验收](doc/knownTxids付款输入验收-20260928-201034.md)。
- knownTxids 真实 Peer：目标提交 `b7acbb4`；同一文件 17／17 原例，真实 Peer 付款例的随机源、两次 fetch 入口、Peer 前置状态、交付帧与发送载荷逐字段一致，6 条断言一致，输入与断言两类篡改被拒，文档 [knownTxids真实Peer输入验收](doc/knownTxids真实Peer输入验收-20260928-210831.md)。至此该文件 17 例的输入重放全部落地。
- Wallet Contracts：六个原测试文件在当前 Java 来源 `382ac6c6` 全部重采为标准双侧同输入局部（253 例、918 输入样本、1003 断言），local-evidence-gate 的 verify／tamper 均通过，full-evidence-preflight 记为 `currentCaptureVerified`；任务级对照 `.cache/evidence/wallet-contracts-clean-parity.json`，刷新记录见 [钱包契约与钱包JSON证据刷新](doc/钱包契约与钱包JSON证据刷新-20260929-020724.md)。
- Wallet JSON：HTTPWalletJSON 53 例与 toOriginHeader 5 例在同一来源 `382ac6c6` 重采为标准双侧同输入局部，输入与断言两类篡改被拒；文档 [HTTPWalletJSON原输入验收](doc/HTTPWalletJSON原输入验收-20260929-004232.md)。两项前置完成后已按依赖顺序标记 `done`。
- 认证证书：目标提交 `fa67ce4`、`58a8f73`；固定 TS 五个原测试 50／50 例、128 条断言。当前 Java 来源 `0a119349`（提交 `1da225e`）下六个文件已全部升级为标准双侧同输入局部（MasterCertificate 构造 2 例、MasterCertificate 其余 13 例、getVerifiableCertificates 5 例、validateCertificates 8 例、Certificate 15 例、VerifiableCertificate 7 例，合计 278 条入口），`local-evidence-gate.py` 的 verify 与 tamper 六项全通过；任务级同来源报告 `.cache/evidence/auth-certificates-same-source-20260929/task-parity.json` 为 50／50、128／128，改写实际值与缺少局部两类反例均被拒。`migration-impl-auth-certificates` 已标记 `done`。
- HTTPWalletJSON：目标提交 `c88a04e`、断言记录对齐 `1c979fa`，同一来源的宿主无过滤 `clean test` 5437／5437；固定 TS／Java 53／53 原例，214／214 条真实入口（构造、公开 api、fetch 请求／响应／拒绝）与 73／73 条原断言逐值一致，53 条线上请求体解析后一致，输入与断言两类篡改被拒，文档 [HTTPWalletJSON原输入验收](doc/HTTPWalletJSON原输入验收-20260929-004232.md)。该局部经 `full-evidence-preflight.py` 来源复核，使 `currentCaptureVerifiedCases` 首次非零（53）。

固定 TS 原始标准／manual Jest 报告合计 5329／5329，通过 `audit-tests.py compare-ts`。Java 当前轮的 5437 条通过记录也不能代替双端同一次完整采集；原始报告还没有覆盖全部用例的输入计划、双侧输入与断言 manifest，最终 `audit-tests.py check` 尚未通过。部分已通过任务的排期状态仍非 `done`，待逐项核对依赖、当前接口行为及同输入证据。

## 全量证据与后续门禁

API 总验收发现的 `Transaction.verifyQueued`／`completeWithWallet` 同步等待、三个公开异步入口同步抛错及 PATCH 默认传输丢失状态说明均已修复并合入；对应隔离回归分别为 802／802、22／22、54／54，当前主提交累计回归通过。Wallet Contracts 在 `c0d9fdd` 的原始 Java 轨迹与固定 TS 253／253、1003／1003 逐断言一致，报告 `.cache/evidence/java-full-after-auth-property-20260926/wallet-contracts-task-parity-current.json`。BRC100ByteEncoding 两个属性用例的 600 组、WERR 32 例的 32 次输入／40 条断言、JSON 字节 10 例的 26 次输入／19 条断言、BRC100 字节 23 例的 57 次输入／62 条断言，以及 WalletError 39 例的 54 次输入／79 条断言，均有双侧局部同输入核验。ValidationHelpers 严格保留 `undefined`／`null` 后，固定原 147 例的 149 组样本／203 条断言一致，另有 6 个显式 `null` 回归；三类篡改反例被拒绝。证书五文件 50／50 原例、128／128 原断言已在当前来源取得标准双侧局部与任务级同来源对照。

P0 采集来源门禁已修复旧版本、同源伪轨迹、缺失断言及跨文件站点归属等误放行；语义规则自测 10／10、bundle 自测 18／18、宿主审计自测 43／43、关联自测 3／3 通过。Hex＋BigNumber 构造的局部输入重放为 36／36 用例、71／71 样本和断言一致，AuthFetch 属性 300 组实际输入由 Java 重放；byte-codecs 的 Base58 六例在 `75a3dc1` 双侧正式 capture 通过，固定 TS 全文件 Jest 62／62、Java 聚焦 6／6。Spend 两个固定 TS 文件的 455 个向量分别绑定独立 Java 测试身份，隔离 455／455 条原断言通过。Script／Spend 共用向量已有 1940 例的 8286 次输入／5030 条断言局部核验；Transaction 向量 659 例的 1159 次输入／1159 条断言、Chronicle 74 例的 77 次输入／77 条断言也完成局部核验。PBKDF2 的 13 个向量、AuthFetch 等待 5 例及支付响应头 8 例已有独立双侧采集。DRBG 29 例已完成双端正式采集并登记（`drbg29`），但其运行绑定 `c23c6f6`，在当前 Java 版本下被来源复核拒绝，须在最终单次全量运行中重采。最新预检（`.cache/evidence/full-preflight-round13.json`）把来源复核记为 121 例、12 个局部：wallet-keys 六文件 71 例与认证证书六文件 50 例，全部绑定 Java 来源 `0a119349`；其余 68 个局部绑定旧执行器或旧版本，须在最终单次全量运行中重采。结构计划仍为 4099／5329，缺 1230 例、75 个文件，`readyForFullCapture=false`。

- 交易基础（transaction-base，三批 API 前检 177／126／30 声明已通过）：当前来源聚焦 `clean test` 74／74 通过（TransactionSignature.additional 24、Transaction.additional 20、Transaction.ef-cache 4、LivePolicy 8、SatoshisPerKilobyte 18），失败／错误／跳过均为 0。两个局部已升级为标准双侧同输入采集并绑定 Java 提交 `45d19e5`（来源 `f971ee13`）：`fee-model-satoshis-per-kilobyte` 18 例／35 输入／21 断言、`live-policy` 8 例／25 输入／17 断言，verify 与 tamper 均通过，当前来源复核 26 例。其余 48 例（Transaction.ef-cache 4、Transaction.additional 20、TransactionSignature.additional 24）尚无输入计划，须新建探针、计划、适配器与 Java 重放入口；见 [交易基础证据推进](doc/交易基础证据推进-20260929-162058.md)。
ProtoWallet.native-hash 已完成标准双侧局部：6 例、19 条入口、18 条断言（65536 字节载荷按字面量登记，describe 级构造按计划归位），verify 与 tamper 通过。
ProtoWallet.async-backend 已完成标准双侧局部：5 例、21 条入口、8 条断言（从桶文件出口替换 ProtoWallet／KeyDeriver，注册与注销按后端支持的操作集记录），verify 与 tamper 通过。

wallet-keys 已完成四个文件的标准双侧同输入局部：KeyDeriver 17 例、49 条入口、37 条断言；ProtoWallet 19 例、111 条入口、44 条断言（深度守卫、原 helper 的 undefined originator 与固定系统时间对齐）；CachedKeyDeriver 13 例、49 条入口、44 条断言（含 LRU／最近使用循环站点样本与 `timing-ms-v1` 耗时语义规则）；ProtoWallet.additional 11 例、22 条入口、11 条断言（记录 keyDeriver 前置状态，测试侧用 `WalletKeysEntropy` 与 TS 探针的固定熵流对齐，双方消费同一把随机密钥 `40919c65…`）。两者均通过局部门禁 verify 与 tamper。KeyDeriver `local-evidence-gate.py` 的 verify 与 tamper 通过，TS 探针按“立即调用者是原测试”判定边界，Java 侧重放用子类覆写加深度守卫实现同一规则。Java 侧每次提交都会推进来源摘要（`382ac6c6`→`f16b01df`→`8cf69655`），因此已完成的局部会在下一次 Java 改动后变为过期；按计划在 wallet-keys 的 Java 侧改动全部落地后统一重采全部受影响局部。最新预检（20260929）的结构计划为 4099／5329，仍缺 1230 例；wallet-keys 六个局部（71 例）与认证证书六个局部（50 例）已在同一来源 `0a119349` 统一重采并通过来源复核，分别是两项的结项依据；其余局部待各自收尾后统一重采；现有局部运行不能拼接为正式全量来源，见 `doc/全量证据采集前置-20260927-005500.md`。完整 `audit-tests.py check` 还需当前源码下单次双侧全量输入、逐断言实例、随机／耗时语义和条件分支证据。
