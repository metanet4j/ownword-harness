# AGENTS.md — boot4-java25-upgrade（任务 harness）

> 本文件只描述**这个任务目录怎么开工**：读什么、怎么验收、怎么收尾。
> **任务目标、版本矩阵、阶段划分、改动清单、验证门禁全部在计划文档里**，本文件不复述。
> 共享的工程与环境规则（仓库布局、Maven 命令、工具链隔离、共享中间件）在上一级
> `../AGENTS.md`（backend-worktree）。

## 1. Startup Workflow（开工前读什么，按顺序）

Before writing code：

1. `pwd` 确认在本目录。
2. 读 `../AGENTS.md`（工程与环境共享规则）与 `../mvn-command.md`（Maven 命令固定模板）。
3. 读 `doc/升级计划-Boot4-Java25.md`——**本任务的唯一事实来源**（目标、版本矩阵、决策 D1–D26、改动清单、门禁）。
4. 读本目录的 `feature_list.json` 与 `session-handoff.md`——阶段状态与唯一下一步。
5. 运行 `./init.sh` 确认环境与仓库状态；有异常先修，不要带病开工。
6. 需要改代码时**先取得用户明确批准**，再动手。**选方案 ≠ 批准开工。**

**One feature at a time（一次只做一项）**：从 `feature_list.json` 只取一项做完再取下一项。

**Stay in scope（不越界）**：只动该项相关的文件；不顺手重构、不提前做后续阶段、不改无关模块。

`doc/` 下另有两份评审记录（首轮 P0/P1、复评的测试门禁 P0-A/P0-B），改动清单以计划文档为准，
评审文档用于追溯"为什么这么改"。

## 2. Definition of Done

一项只有**同时**满足以下四条才算完成：

- [ ] 计划文档中该阶段的产物已产出
- [ ] 该阶段要求的验证**真的跑过**，命令与输出留存（`./init.sh --full` 或阶段门禁命令）
- [ ] 证据写入 `feature_list.json` 的 `evidence` 与 `progress.md`
- [ ] 仓库可从标准启动路径重新开工（`./init.sh` 通过，工作区干净）

任一条件不满足，不得标记 `done`。

## 3. End of Session

Before ending a session：

1. 更新 `progress.md`：`Current State` / `Last Updated` / `Current Objective` / `Recommended Next Step`。
2. 更新 `feature_list.json`：该项 `status` 与 `evidence`。
3. 更新 `session-handoff.md`：`Blockers` / `Files` / `Next Session`。
4. 四个子仓库各自 commit（中文 Conventional Commits）；本任务**不推送远端**。
5. 留下可 restartable 的工作区：`./init.sh` 能直接跑，无残留临时文件。

## 4. 本任务特有的红线

以下是**本任务专属**、未写进共享规则的约束（通用规则见 `../AGENTS.md`）：

- **工具链与仓库**：本任务用 JDK 25 + Maven 3.9.16 的绝对路径，并固定 `-s ~/.m2/metanet4j-settings.xml`
  （本地仓库 `~/.m2/metanet4j`，与默认仓库隔离）；全局默认（JDK 8 / Maven 3.9.9）**不得改动**。
  命令模板见 `../mvn-command.md`，`./init.sh` 每次校验全局是否被污染。
- **测试一律 `clean test`**，且验收按**模块**给执行数，不接受"总数 > 0"。
- **共享中间件**用 `ownword/infra/`，不要自起容器；**不要 `down -v`**（会清掉跨任务数据）。
- **未获批准不改代码**——这条是踩过坑写下来的（曾把"选方案"误当"批准开工"，改了 44 个文件后全部回退）。

## 5. Escalation

- 计划文档没覆盖的架构决策 → 问用户。
- 版本兼容性有争议 → **以官方文档为准**，把链接与结论写回计划文档。
- 发现计划与实际不符 → **先改计划文档，再改代码**，并在 `progress.md` 记录偏差。
- 卡住超过两轮 → 停下来说清阻塞条件再问，不要反复试错。
