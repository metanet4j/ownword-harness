# progress.md — boot4-java25-upgrade 进度

本文件只记录当前状态；范围和验收标准见[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)，逐模块状态见 `feature_list.json`。

## 当前状态

- **更新时间**：2026-09-26。
- **当前目标**：为四个子仓库建立完整单元测试、集成测试与逐模块覆盖率证据。
- **当前阶段**：`unit-u1-base` 正在实施；U0 基线已完成，U2—U9 待实施。用户已确认测试通过公开入口执行，HTTP 和文件协议使用本地模拟，自动测试不广播主网交易。
- **下一步**：按 JaCoCo 实测缺口为 base 的 AIP/BAP、枚举、DTO、Jackson 工具补有行为断言的单元测试，逐步运行严格验收入口。

## 当前证据与缺口

U0 报告见[四仓测试基线](doc/测试基线与障碍-20260926-145423.md)。`unit-test-inventory.json` 覆盖 25 POM、369 个生产 Java 文件、53 个测试文件，已完成安全分类，并列出 19 项集成边界、隔离及观测方式。`verify-unit.py` 会核对源码清单、Surefire XML、JaCoCo 执行文件与 XML、覆盖率和历史外部测试去向。

宿主全仓 Maven 基线的四个 reactor 都退出 0，测试账目为 56 通过、8 跳过；统一基线及严格入口因真实缺口退出 1。17 个可执行 component 模块零单元测试，`component-core` 仅有接口，按 N/A 处理。base 当前为行 50/222、分支 12/76、方法 10/55；sdk 为行 307/1990、分支 24/505、方法 91/454。原始证据在本地 `evidence/20260926T064228Z/`，五类门禁反例在 `evidence/20260926-u0-pilot/`。宿主 `infra/status.sh` 已确认 MongoDB、ES、Kafka、Redis、MySQL 五服务健康。

现有 `EsTest` 会删除固定索引，不能直接运行集成组；文件模块 8 个历史用例全被禁用；交易完成入口直接调用 Bitails 主网广播。修复和替代测试去向见 U0 报告及 `unit-test-inventory.json`。集成测试须在宿主提权执行，并在运行前确认连接、日志与自有资源清理。

UTXO 相等性缺陷已由红灯用例复现并修复，base 提交 `bae7eb6`；统一入口新基线在 `evidence/20260926T070148Z/`，4 个测试通过、无跳过。U1 仍需覆盖剩余类和分支。

## 仓库与工作区

四个子仓库沿用 `feature/java25`，不推送。parent 的 U0 JaCoCo 配置已提交为 `4112a48`；sdk `2577406` 与 component `de1f59f` 已提交测试分类。ownword 主仓既有 `AGENTS.md`、standard 规范和技能文件的无关改动均保留，不纳入本任务提交。
