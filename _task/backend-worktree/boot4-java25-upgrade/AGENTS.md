# AGENTS.md — boot4-java25-upgrade（任务 harness）

任务目标、版本矩阵、阶段、改动清单和验证门禁见计划文档；共享工程与环境规则见 `../AGENTS.md`。以下相对路径以本目录为起点。

## 1. Startup Workflow（开工前读什么，按顺序）

Before writing code：

1. `pwd` 确认在本目录。
2. 读 `../AGENTS.md`（工程与环境共享规则）与 `../mvn-command.md`（Maven 命令固定模板）。
3. 读 `doc/升级计划-Boot4-Java25.md`——本任务执行与验收依据，不覆盖核心认知。
4. 读本目录的 `feature_list.json` 与 `session-handoff.md`——阶段状态与唯一下一步。
5. 运行 `./init.sh` 检查环境与仓库状态；异常先诊断，修复仍须遵守代码、环境及共享设施的授权边界。
6. 需要改代码时**先取得用户明确批准**，再动手。**选方案 ≠ 批准开工。**

批准在已授权事项内持续有效；换文件、常规验证或续接会话不重复申请，阶段批准不自动延伸到其他阶段。

**One feature at a time（一次只做一项）**：从 `feature_list.json` 只取一项做完再取下一项。

**Stay in scope（不越界）**：只动该项相关的文件；不顺手重构、不提前做后续阶段、不改无关模块。

## 2. Definition of Done

一项只有**同时**满足以下四条才算完成：

- [ ] 计划文档中该阶段的产物已产出
- [ ] 该阶段要求的验证**真的跑过**，命令与输出留存（`./init.sh --full` 或阶段门禁命令）
- [ ] 证据写入 `feature_list.json` 的 `evidence` 与 `progress.md`
- [ ] `./init.sh` 通过，本任务改动已提交、临时文件已处理；既有无关改动保留并报告，不作为完成阻塞，不清理或混入提交

任一条件不满足，不得标记 `done`。

## 3. End of Session

Before ending a session：

1. 更新 `progress.md`：`Current State` / `Last Updated` / `Current Objective` / `Recommended Next Step`。
2. 更新 `feature_list.json`：该项 `status` 与 `evidence`。
3. 更新 `session-handoff.md`：`Blockers` / `Files` / `Next Session`。
4. 仅在有本任务改动的仓库各自 commit（中文 Conventional Commits），不空提交；本任务**不推送远端**。
5. 留下可 restartable 的工作区：`./init.sh` 能直接跑，无本任务残留临时文件。

## 4. 本任务特有的红线

- **工具链与仓库**：本任务用 JDK 25 + Maven 3.9.16 的绝对路径，并固定 `-s ~/.m2/metanet4j-settings.xml`
  （本地仓库 `~/.m2/metanet4j`，与默认仓库隔离）；全局默认（JDK 8 / Maven 3.9.9）**不得改动**。
  命令模板见 `../mvn-command.md`，`./init.sh` 每次校验全局是否被污染。
- **测试一律 `clean test`**，且验收按**模块**给执行数，不接受"总数 > 0"。
- **共享中间件**用工作区根目录的 `infra/`，不要自起容器；**不要 `down -v`**（会清掉跨任务数据）。

## 5. Escalation

- 计划文档没覆盖的架构决策 → 问用户。
- 版本兼容性有争议 → **以官方文档为准**，把链接与结论写回计划文档。
- 发现计划与实际不符 → **先改计划文档，再改代码**，并在 `progress.md` 记录偏差。
- 同一阻塞连续超过两轮诊断仍无新证据时，停止重复尝试，说明阻塞条件并求助；仅暂停依赖该阻塞的工作，继续其他已授权事项。正常取证不计作失败重试。
