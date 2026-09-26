# 当前进度

## 执行位置

权威任务状态见 [feature_list.json](feature_list.json)：43 个执行事项中 17 个 `done`、11 个 `in-progress`、15 个 `not-started`；`activeItem=nextItem=migration-impl-compat`。API 映射 3576／3576 项已复核，21 个嵌入批次均完成；原用例映射 5329／5329 个、源码测试站点映射 7554／7554 个。六模块完整门禁尚未通过。

目标 Java 工程主分支当前提交 `75a3dc1`，正在增加 byte-codecs 的真实输入采集；最近一次宿主完整 clean test 绑定前一提交 `c0d9fdd`。固定 TypeScript 仓库及其他四个 Java 工程只读；目标工程 `metanet4j-bsv-sdk` 是唯一可改代码仓库。工作区根仓的既有无关改动保留。

## 已取得的任务级验收

- 对称加密：固定 TS 原规模 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过；当前独立 Java `c0d9fdd` 工作树 manual 1／1，逐字节比较 536,870,928 次。普通原始 TS／当前 Java 轨迹 51／51、384／384 逐字段一致；合计 52／52、387／387，报告 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`，篡改反例 7／7 通过。
- 交易完整功能：目标提交 `f1b5752`；固定 TS／Java 745／745 个原用例、1390／1390 条实际断言一致，报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。
- 交易验证与证据：目标提交 `dfacef7`；固定 TS／Java 53／53、162／162 条实际断言一致，报告 `.cache/evidence/transaction-verification-parity-main-20260926.json`。交易模型 API-09 的 126 项与证据 API-10 的 176 项均通过单批审计。
- 认证会话：目标提交 `94d5bc0`，异步存储修复 `7c382f6`，公开异步存储入口 `3e58d02`；固定 TS／Java 85／85、160／160 条实际断言一致，另有两例延迟 Future 回归，报告 `.cache/evidence/auth-sessions-parity-main-7c382f6.json`。API-19 的 101 项通过单批审计。
- 认证传输：固定 TS／Java 的 Transport＋AuthFetch 183／183 个原用例、968／968 条实际断言已在当前 Java 提交对照通过，报告 `.cache/evidence/java-full-after-auth-property-20260926/auth-transport-task-parity-replayed.json`；两条运行时间戳与堆栈按固定字段语义核验。AuthFetch 属性测试固定 TS 300 组实际生成输入已由 Java 同批重放，600／600 条断言精确一致，语料 SHA-256 为 `b0cf9d142fed85b2a9a82b85ac4b254ae6408da60ffa6457f98e757825818392`。本任务 taskAcceptance 已通过，排期状态仍等待依赖。

主工程前一提交 `c0d9fdd` 的宿主完整 clean test 为 4916／4916、失败／错误／跳过均为 0；原始 Java 断言轨迹及 AuthFetch 属性消费输入在 `.cache/evidence/java-full-after-auth-property-20260926/`。当前主提交与后续 API 修复整合后须重新执行完整回归。部分已通过任务的排期状态仍非 `done`，待逐项核对依赖和当前接口行为。

## 当前阻塞与后续门禁

API 总验收发现 `Transaction.verifyQueued` 和 `completeWithWallet` 可能在返回 `Future` 前同步等待下游结果；隔离探针和修复正在进行。结构映射通过不代表公开异步行为已通过。

P0 采集来源门禁已修复旧版本、同源伪轨迹、缺失断言等误放行；语义规则自测 7／7、bundle 自测 18／18、宿主审计自测 41／41、关联自测 3／3 通过。Hex＋BigNumber 构造的局部输入重放为 36／36 用例、71／71 样本和断言一致，AuthFetch 属性 300 组实际输入由 Java 重放，byte-codecs 正扩展局部采集。已做的局部对照不代替完整 5329 例；完整 `audit-tests.py check` 仍需当前 Java 版本的全量原始报告、两端输入账本、逐断言实例、随机／耗时语义和条件分支证据。
