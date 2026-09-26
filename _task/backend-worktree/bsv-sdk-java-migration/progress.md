# 当前进度

## 执行位置

权威任务状态见 [feature_list.json](feature_list.json)：43 个执行事项中 16 个 `done`、12 个 `in-progress`、15 个 `not-started`。API 映射 3093／3576 项，原用例映射 4956／5329 个，源码测试站点映射 6405 个。六模块完整门禁尚未通过；`activeItem=nextItem=migration-impl-symmetric`。

## 已通过的任务验收

- 交易完整功能：目标提交 `f1b5752`，隔离干净提交 `9bcb650`；固定 TS／Java 745／745 个原用例、1390／1390 条实际断言精确一致。连同 BEEF 回归，清洁 Maven 共 769／769 个用例通过，失败／错误／跳过均为 0。报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。`Transaction.performance.test.ts` 的 25 个规模、缓存、视图与变异用例均已覆盖。
- API-06 兼容模块：七个完整源文件的 96 项声明已复核，`Utxo` 六项 API 与完整交易实现对齐；`node audit-api.cjs batches --batch migration-api-compat` 通过。行为依据见 `doc/完整模块与API映射-20260920-122800.md#api-compat`。
- 钱包客户端：目标提交 `0472fc0`，固定 100／100 个原用例、184／184 条断言精确一致；与三类浏览器宿主联合运行的 Java 226 个用例通过。钱包 Wire 128／128、浏览器宿主 126／126、脚本向量 555／555 的干净逐断言证据及其他已验收任务见 [feature_list.json](feature_list.json)。

交易完整功能已取得任务级 `taskAcceptance=passed`。其排期状态仍为 `not-started`，因为现有任务图要求前置项先转为 `done`；前置项的部分原测试已通过，但对称模块阻止依赖链完成。任务状态没有用局部验收代替完整模块门禁。

## 当前工作

认证会话、认证传输和交易证据分别在 `/tmp/bsv-auth-sessions-0472fc0`、`/tmp/bsv-auth-transport-0472fc0`、`/tmp/bsv-transaction-evidence-0472fc0` 独立工作树继续实施；它们尚未完成固定原测试的全量验收，不能标记完成。交易证据工作树已纳入交易完整功能提交，原 Evidence 4／4 用例通过，Coordinator 和异步脚本后端仍在实施。认证传输 49 个 Java 用例已通过，仍在核对逐断言实际值。

对称模块普通四文件固定 TS／Java 51／51、384／384 条断言一致；Java 536,870,928 字节原 manual 1／1 与 Node 原生流式 oracle 一致。固定 TS 原 manual 在 90 分钟上限退出 124，未产生完整 Jest 结果及断言轨迹。胡先生已明确要求维持 90 分钟上限；此项不能据 Java 与 oracle 的结果标记为通过。证据 `.cache/evidence/symmetric-manual-ts-timeout.json`。

固定 TypeScript 仓库及其他四个 Java 工程只读；目标工程 `metanet4j-bsv-sdk` 为唯一可改代码仓库。工作区根仓的既有无关改动保留。
