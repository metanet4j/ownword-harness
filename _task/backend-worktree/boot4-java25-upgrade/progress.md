# BSV 依赖替换任务进度

## Current State

- **Last Updated**：2026-10-10。
- **Current Objective**：已交付可落地、可验收的 [BSV 依赖替换计划](doc/BSV依赖替换计划-20261010-103802.md)。
- **Active Item**：无。`bsv-replace-plan` 已完成，R0—R6 均未开工。
- **授权范围**：本轮仅文档。代码实施仍按本任务 AGENTS.md 的明确批准要求执行。
- 四仓库当前均为 `feature/bsv-sdk-replace`；提交仍是 parent `7302e1b`、base `53ed9ad`、sdk `670ee3d`、component `3ce773b`。base 的 `pom.xml` 已有未提交的新 SDK 接入修改，保留作为实施输入。
- 指定 SDK 在原任务工作区，固定提交 `3dd8beb`。其生产源码及 POM 与原完整验收绑定提交 `ce6b50d` 无差异；原 SDK 输入保持只读。

## 已有验收依据

既有升级与单元测试事项已完成，报告见 [验收报告](doc/验收报告-单元测试全覆盖-20260929-232313.md)。已有单元证据 `evidence/20260930T125355Z/` 为 25 个 POM、23 个模块、841 例、0 failures／errors／skipped、全部 gaps=0；已有 component 集成证据 `evidence/20260930T130119Z-integration/` 为 18 类／124 例。另从源码与清单查到 SDK 的 5 例本地 HTTP 集成，本次纳入独立验收。上述均不代表依赖替换已通过。

SFTP 成功连接的 2 行继续按胡先生 2026-09-30 的决定保留为精确覆盖例外，不作为本次新待办。其他既有精确例外仍由清单双向核对，不扩大排除范围。

## 验证与限制

- 计划静态复核通过：6 个本地链接、10 个 Bash 命令块及嵌入 Python 语法检查有效；25 个 POM 与清单一致，23 个既有事项完整保留，7 个新阶段依赖齐全。证据：`evidence/bsv-replace/plan-20261010-103802/static-check.json`。
- 任务 harness 结构检查通过，结果只代表入口和交接结构有效。
- 本轮 `./init.sh` 退出 0，JDK 25／Maven 3.9.16 及全局工具链隔离检查通过。
- 原自检仍预期 `feature/java25`，当前分支告警已在计划 R0 中安排处理；原 `--full` 不能替代严格构建验收。
- 当前执行环境未能访问共享中间件，宿主状态尚需在实施时复核；这不阻塞计划交付及离线工作。
- 本轮未执行 Maven 构建、单元或集成测试，未修改子仓库源码、POM、测试、新 SDK 输入或任务验证脚本。

## Recommended Next Step

胡先生明确批准实施后，按 [计划 R0](doc/BSV依赖替换计划-20261010-103802.md) 固定来源、收口方法级 API／测试映射和验收向量，随后依次推进 R1—R6。
