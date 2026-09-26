# 当前进度

## 执行位置

权威任务状态见 [feature_list.json](feature_list.json)：43 个执行事项中 18 个 `done`、10 个 `in-progress`、15 个 `not-started`；`activeItem=nextItem=migration-impl-wallet-contracts`。API 映射 3576／3576 项已复核，21 个嵌入批次均完成；原用例映射 5329／5329 个、源码测试站点映射 7554／7554 个。六模块完整门禁尚未通过。

目标 Java 工程主分支当前提交 `b9f5eb8`。本提交宿主无过滤 `clean test` 的 159 份 Surefire 报告包含 5378／5378 个通过的测试，失败／错误／跳过均为 0；同一次运行覆盖全部 5329 个唯一映射身份，另有 49 个 Java 回归，原始报告及核对摘要位于 `.cache/evidence/java-full-b9f5eb8-20260927/`。固定 TypeScript 仓库及其他四个 Java 工程只读；目标工程 `metanet4j-bsv-sdk` 是唯一可改代码仓库。工作区根仓的既有无关改动保留。

## 已取得的任务级验收

- 对称加密：固定 TS 原规模 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过；独立 Java `c0d9fdd` 工作树 manual 1／1，逐字节比较 536,870,928 次。普通原始 TS／该版 Java 轨迹 51／51、384／384 逐字段一致；合计 52／52、387／387，报告 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`，篡改反例 7／7 通过。
- Compat：主目标 `c0d9fdd` 的原始 Java 轨迹与固定 TS 五文件重新比较，122／122 个用例、281／281 条断言一致，报告 `.cache/evidence/java-full-after-auth-property-20260926/compat-task-parity-current.json`；依赖满足后已标记 `done`。
- 交易完整功能：目标提交 `f1b5752`；固定 TS／Java 745／745 个原用例、1390／1390 条实际断言一致，报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。
- 交易验证与证据：目标提交 `dfacef7`；固定 TS／Java 53／53、162／162 条实际断言一致，报告 `.cache/evidence/transaction-verification-parity-main-20260926.json`。交易模型 API-09 的 126 项与证据 API-10 的 176 项均通过单批审计。
- 认证会话：目标提交 `94d5bc0`，异步存储修复 `7c382f6`，公开异步存储入口 `3e58d02`；固定 TS／Java 85／85、160／160 条实际断言一致，另有两例延迟 Future 回归，报告 `.cache/evidence/auth-sessions-parity-main-7c382f6.json`。API-19 的 101 项通过单批审计。
- 认证传输：固定 TS／Java 的 Transport＋AuthFetch 183／183 个原用例、968／968 条实际断言已在 `c0d9fdd` 对照通过，报告 `.cache/evidence/java-full-after-auth-property-20260926/auth-transport-task-parity-replayed.json`；两条运行时间戳与堆栈按固定字段语义核验。AuthFetch 属性测试固定 TS 300 组实际生成输入已由 Java 同批重放，600／600 条断言精确一致，语料 SHA-256 为 `b0cf9d142fed85b2a9a82b85ac4b254ae6408da60ffa6457f98e757825818392`。本任务 taskAcceptance 已通过，排期状态仍等待依赖。

固定 TS 原始标准／manual Jest 报告合计 5329／5329，通过 `audit-tests.py compare-ts`；当前 Java 完整回归也已通过。但这两套原始报告没有同一次完整采集的输入计划、双侧输入与断言 manifest，不能代替最终 `audit-tests.py check`。部分已通过任务的排期状态仍非 `done`，待逐项核对依赖、当前接口行为及同输入证据。

## 全量证据与后续门禁

API 总验收发现的 `Transaction.verifyQueued`／`completeWithWallet` 同步等待、三个公开异步入口同步抛错及 PATCH 默认传输丢失状态说明均已修复并合入；对应隔离回归分别为 802／802、22／22、54／54，当前主提交累计回归通过。Wallet Contracts 在 `c0d9fdd` 的原始 Java 轨迹与固定 TS 253／253、1003／1003 逐断言一致，报告 `.cache/evidence/java-full-after-auth-property-20260926/wallet-contracts-task-parity-current.json`；BRC100ByteEncoding 两个属性用例有 600／600 组真实同输入与断言局部证据。WERR 原文件 32／32 个用例、32／32 组真实构造输入、40／40 条原断言在 `ef41db2` 的双侧正式局部门禁通过，输入与断言篡改均被拒绝；证据为 `.cache/evidence/werr-local-report-20260927.json`。证书构造首批 2／50 例有 7／7 组真实输入、6／6 条断言局部证据，Java 改动已合入 `b9f5eb8`。这些局部来源随 Java 提交变化需在最终完整运行中重新采集。

P0 采集来源门禁已修复旧版本、同源伪轨迹、缺失断言等误放行；语义规则自测 7／7、bundle 自测 18／18、宿主审计自测 41／41、关联自测 3／3 通过。Hex＋BigNumber 构造的局部输入重放为 36／36 用例、71／71 样本和断言一致，AuthFetch 属性 300 组实际输入由 Java 重放；byte-codecs 的 Base58 六例在 `75a3dc1` 双侧正式 capture 通过，固定 TS 全文件 Jest 62／62、Java 聚焦 6／6。Wallet BRC100 两个属性用例在 `e2f4814` 双侧 capture 通过，600 组输入与原断言精确一致。Spend 两个固定 TS 文件共用的 455 个向量此前复用了同一 Java 测试身份；`6647525` 新增独立 JUnit 类，`59c41ff` 将第二组 455 项改映射，隔离 455／455 条原断言通过，当前完整回归也各执行一次。`full-evidence-preflight.py` 当前仅有 47／5329 例的结构计划，其余局部采集尚未接入；全量同输入计划及单次双侧采集适配器仍需实施，见 `doc/全量证据采集前置-20260927-005500.md`。完整 `audit-tests.py check` 还需两端输入账本、逐断言实例、随机／耗时语义和条件分支证据。
