# progress.md — boot4-java25-upgrade 进度

本文件只记录当前状态；单元与集成测试的范围、模块清单和验收标准见 [测试计划](doc/单元测试全覆盖计划-20260920-090603.md)。阶段状态见 `feature_list.json`。

## Current State（当前状态）

- **Last Updated**：2026-09-26。
- **Current Objective**：为四个子仓库建立完整的单元测试、集成测试和逐模块覆盖率证据。
- **Active Item**：`unit-u0-baseline`。用户已明确要求实施 U0—U9；目前在梳理测试接口、现有用例分类与资源隔离，尚未编写新测试。
- **Recommended Next Step**：公开接口边界确认后，完成 U0 清单、JaCoCo 配置、统一验收入口和基线。
- **本轮验证**：`./init.sh` 退出 0；宿主环境 `infra/status.sh` 确认五服务 healthy、端口可达。base 使用 JDK 25、Maven 3.9.16 执行 `-Punit-coverage clean test jacoco:report`，2/0/0/0；JaCoCo 行 35/225、分支 6/78、方法 6/55。`jacoco:check` 如预期返回 1。其余模块尚未重新测试。

## 当前证据

静态规模、逐模块测试文件数量、旧测试报告与已识别缺口统一记录在 [测试计划 §2、§5](doc/单元测试全覆盖计划-20260920-090603.md)，本文件不重复维护。

`unit-test-inventory.json` 已列入 25 个 POM、369 个生产 Java 文件与 52 个测试文件；目前只有 parent/base 分类复核完成。parent JaCoCo 配置已提交为 `4112a48`。统一入口端到端运行的 base 原始日志、Surefire XML、JaCoCo 报告与执行文件保存在本地 `evidence/20260926T061230Z/`；五种临时证据反例保存在 `evidence/20260926-u0-pilot/`，均返回 1。其余模块分类完成后再进入自动基线。

旧报告的 `component-file` 为 tests=8、skipped=8，实际通过为 0；此前文档写成“8 通过”不准确。`BitailsProviderTest` 未标记公网依赖，`EsTest#recreateIndex` 会删除固定索引；必须先分类和隔离。`init.sh --full` 未排除外部测试，不能作为新验收入口。

## 已完成的升级基线

原 Boot 4 / Java 25 升级及交付后修复已经完成，范围与证据见 [升级计划](doc/升级计划-Boot4-Java25.md)、[升级验收报告](doc/验收报告-Boot4-Java25-20260916-1320.md) 和 `feature_list.json` 的原阶段记录。历史升级验收不代表新增单元测试目标已完成。

四子仓库继续使用 `feature/java25`；当前尚未修改其代码、POM、测试或分支，也未推送。

## 评审结论与未满足的完成条件

U0 正在实施，U1—U9 尚未开始；尚未得到当前覆盖率、完整单元和集成执行结果及最终验收报告。集成测试必须提权在宿主环境执行，先核对连接配置、容器与应用日志、Surefire XML，使用独立资源并清理；自动测试不得向主网广播。

## 既有无关改动

ownword 主仓已有 `AGENTS.md`、三份 standard 规范的修改，以及 caveman、writing-clearly-and-concisely 技能文件的删除。本轮保留，不纳入测试计划提交。
