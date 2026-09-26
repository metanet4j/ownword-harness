# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 的实施范围及公开 API 测试。当前只实施 `unit-u2-sdk`；U0 和 U1 已完成，U3—U9 尚未开始。先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK `target` 只允许串行运行 Maven；集成测试须在宿主环境提权执行。不要读取 Archive、推送远端、广播主网或清理共享中间件数据。

SDK HEAD `18124c8`：宿主全量 `python3 verify-unit.py --mode baseline --scope metanet4j-sdk` 退出 0，199/0/0/0，LINE 1948/1961、BRANCH 506/506、METHOD 441/452；报告 `evidence/20260926T164453Z/`。U1 base 严格验收 19/0/0/0，证据 `evidence/20260926T072220Z/`。SDK HTTP 本地集成 5/0/0/0，证据 `evidence/20260926-u2-http/integration/`。八组历史 Ordinal 交易固定向量与 Sigma 验签定向 8/0/0/0，证据 `evidence/20260927-u2-ord-fixtures-sigma-targeted/`。31 个旧 `external` 用例均有真实替代测试，47 条引用已逐个核实方法存在；涉及实时主网的差异另记人工原因。

## Blockers

1. 远程 Ordinal 公开 `sendOrdinal(RemoteBapBase, …)` 调用时 `KeyBag=null` 导致异常，红测及原测试补丁存于 `evidence/20260927-u2-remote-send-red/`。胡先生已收到设计选择：保留旧 `Transaction` 返回类型并新增 `prepareSendOrdinal(...)` 返回待签构建器，或直接改旧入口返回类型。收到选择前不要改依赖该决定的 API。
2. 严格验收尚差 13 行：上述远程入口 1 行、10 个无业务行为的隐式构造器、`SigHashExtend` 固定内存流中不可触达的 `IOException` 包装 2 行。胡先生已收到后 12 行的验收口径选择。`verify-unit.py --mode accept --scope metanet4j-sdk --evidence evidence/20260926T164453Z` 退出 1，仅余 22 条覆盖率检查项；不能标记 U2 完成。
3. `./init.sh` 已退出 0，但共享中间件当前没有运行容器。启动下一阶段的数据库、搜索、消息及缓存集成测试前，按 `infra/README-*.md` 核对连接、服务日志和资源隔离。

## Files

本任务主仓待提交的状态文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`。SDK 工作树当前无待提交改动；HEAD 以 `git -C metanet4j-sdk rev-parse --short HEAD` 为准。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。各证据目录为本地运行产物，不代替 Git 提交。

## Next Session

按胡先生的两项决定处理远程入口和剩余覆盖缺口。达到 SDK 严格验收后安装验证产物，再依计划顺序推进 U3—U9。收尾前更新状态文件、运行 `./init.sh` 并只提交本任务文件。
