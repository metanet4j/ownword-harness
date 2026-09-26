# 会话交接

## 当前状态

执行状态以 [feature_list.json](feature_list.json) 为准，行为依据见[核心契约](doc/完整模块与API映射-20260920-122800.md)。43 个执行事项中 16 done、9 in-progress、18 not-started；API 映射 2777／3576，原用例映射 3302／5329。`node audit-api.cjs batches` 已核对固定 TS 的 133 个文件、3576 项声明与 28 个编码任务分配；完整门禁尚未通过。

证书任务目标提交 `fa67ce4`、`58a8f73`，干净工作树 `/tmp/bsv-auth-accept-58a8f73` 的五类 Maven 原测试 50／50，逐断言报告 `.cache/evidence/auth-certificates-task-parity.json` 为 50／50、128／128、缺失／未比较／额外均为 0。71 项 API、50 用例及 180 个源码站点已映射；API-16 单批结构核对通过。广播器目标 `acd99a2` 的干净报告 `.cache/evidence/broadcasters-task-parity-acd99a2.json` 为 68／68、169／169；45 项 API、68 用例及 290 个站点已映射。

钱包密钥、兼容层及脚本执行任务分别已完成 71／162、122／281、546／568 的干净逐断言验收。脚本向量 555 个原用例和 Wallet Wire 128 个原用例正在并行实施；Wallet Wire 的 HTTP 46 例及完整集成前 45／82 例已通过，28 个 Transceiver 调用与 Processor 内存协议往返含 4 MiB BEEF 已验证。共享工作树中的脚本和钱包文件仍未提交，提交时只选择各自功能文件。

对称普通 51／51、384／384 已逐字段对照；Java 536,870,928 字节 manual 1／1 与 Node 流式 oracle 一致。固定 TS 原 manual 在 90 分钟限制下退出 124，未产生完整 Jest 轨迹；有界 120 分钟重跑已向用户异步请求明确授权，尚无答复，不能标记对称任务完成。自动审批曾拒绝绕过计时器的操作，理由是绕过资源限制，该操作未执行。

## 验证入口

- 证书：`python3 task-parity.py --task migration-impl-auth-certificates --ts .cache/evidence/auth-certificates-ts-20260926/auth-certificates-seeded-ts-parity.jsonl --java .cache/evidence/auth-certificates-ts-20260926/auth-certificates-clean-java-parity.jsonl --java-worktree /tmp/bsv-auth-accept-58a8f73 --output <报告路径>`。
- 广播器：`feature_list.json` 的 `taskAcceptance.compareReport` 指向提交后干净逐断言报告；其余完成任务同理。
- Maven／pnpm 只经 `./mvn.sh`、`./pnpm.sh`；集成及接口测试在宿主提权环境运行。最终门禁为无过滤 `node audit-api.cjs check` 与 `python3 audit-tests.py check`。

只修改 `metanet4j-bsv-sdk` 工程代码、测试及本任务目录映射、状态和文档；固定 TS 与其他四个 Java 工程只读，不读 Archive，不调用真实外部钱包或广播。根仓既有无关改动保留。
