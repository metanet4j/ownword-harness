# 会话交接

## 权威状态与当前提交

[feature_list.json](feature_list.json) 是执行状态来源，[核心契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。当前目标 Java 仓库提交 `f1b5752`；交易完整功能的固定 TS／Java 745／745 个用例、1390／1390 条实际断言在隔离干净提交 `9bcb650` 上精确一致，BEEF 累计清洁 Maven 769／769。报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。API-06 的 96 项声明已复核并通过单批结构审计。

43 个执行事项中 16 `done`、12 `in-progress`、15 `not-started`；API 映射 3093／3576，原用例映射 4956／5329。交易完整功能 `taskAcceptance=passed`，排期状态因前置事项未全为 `done` 保持 `not-started`。六模块无过滤正式门禁尚未通过。

## 可继续实施的独立工作树

- `/tmp/bsv-transaction-evidence-0472fc0`：已合入交易提交为隔离提交 `731d62f`，原 Evidence 4／4 通过；Coordinator 的 34 个原用例和 `BdkVerifierInterface` 后端仍在实施。主代理已在该工作树的 `Transaction.java` 写入四参 `verify` 重载与 `EvidenceScriptWork` 作用域接入；需与 Coordinator 新测试一起复验，再提交与合入目标仓库。
- `/tmp/bsv-auth-sessions-0472fc0`：SessionManager、nonce 与 Peer 边界现有 20／20 Java 用例通过；原固定 TS 六文件 85 个用例、160 条断言，Peer 主体和剩余原用例仍需实施。
- `/tmp/bsv-auth-transport-0472fc0`：SimplifiedFetchTransport 的固定 TS 两文件 49 个用例、78 条断言已采集离线基线；Java 49 个原用例通过，子代理继续核对实际值，之后再推进 AuthFetch 依赖项。

三个工作树均有未提交任务改动；目标主仓仍有认证传输原先的未追踪文件及共享断言助手、Evidence 资源文件的未提交改动，合并时保留并按功能选择提交。

## 验证入口与限制

- 交易：`python3 task-parity.py --task migration-impl-transaction-complete --ts .cache/evidence/transaction-complete-ts-parity.jsonl --java .cache/evidence/transaction-complete-java-clean-745.jsonl --java-worktree /tmp/bsv-transaction-complete-f6034bf --output <报告路径>`。
- API-06：`node audit-api.cjs batches --batch migration-api-compat`。完整门禁仍为无过滤 `node audit-api.cjs check` 与 `python3 audit-tests.py check`。
- Maven／pnpm 经任务目录的 `./mvn.sh`、`./pnpm.sh`；集成及接口测试在宿主提权环境运行。固定 TS 与其他四个 Java 工程只读，不读 Archive，不调用真实外部钱包或广播。
- 对称模块 536,870,928 字节固定 TS manual 保持用户指定的 90 分钟上限。原执行超时，不能缩小输入、延长上限或用 oracle 结果冒充原 Jest 通过。

工作区根仓的无关修改不得暂存或提交。每完成一个功能项单独提交目标仓库代码，并将对应任务映射、报告和状态更新提交到工作区根仓。
