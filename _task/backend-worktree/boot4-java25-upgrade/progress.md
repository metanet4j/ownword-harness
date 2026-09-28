# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-28。
- **Current Objective**：为四个子仓库建立完整单元测试、集成测试与逐模块验收证据。
- **Active Item**：`unit-u2-sdk` 已完成（状态 `done`）；`unit-u3-foundation` 为下一项，尚未开工。
- SDK 提交 `670ee3d`：远程转移公开 `sendOrdinal(RemoteBapBase, …)` 保留 `Transaction` 返回并改走远程构建器，新增 `prepareSendOrdinal(…)` 待签准备入口；严格验收 203/0/0/0，LINE 1965/1977、BRANCH 514/514、METHOD 445/455，证据 `evidence/20260928T093257Z/`（head 670ee3d），产物已从同一提交安装供 component 使用。
- 唯一缺口为用户批准的 12 行精确例外（10 个无行为隐式构造器 + `SigHashExtend` 不可达 `IOException` 包装），记入 `unit-coverage-exceptions.json`：`verify-unit.py` 严格模式双向核对，`jacoco:check` 按 SDK 属性显式排除；反例证据 `evidence/20260928-u2-exception-controls/`（CLI check 通过；篡改清单后拒绝并报 2 条不符）。
- 父 POM 例外机制提交 `metanet4j-parent 7302e1b`；base 回归严格验收 19/0/0/0、LINE 208/208、BRANCH 76/76、METHOD 51/51，证据 `evidence/20260928T092443Z/`。
- SDK 本地 HTTP 集成测试 5/0/0/0，证据 `evidence/20260926-u2-http/integration/`；八组历史 Ordinal 交易固定向量与 Sigma 验签定向 8/0/0/0，证据 `evidence/20260927-u2-ord-fixtures-sigma-targeted/`；31 个旧 `external` 用例均有精确替代测试或人工原因登记。

## 阻塞与剩余工作

- U3—U9 尚未开始；下一项为 `unit-u3-foundation`（component model → common → core，逐模块达到计划 §3）。
- 共享中间件当前没有运行容器；启动下一阶段的数据库、搜索、消息及缓存集成测试前，须按 `infra/README-*.md` 核对连接、服务日志与资源隔离。
- 四仓库分支仍为 `feature/java25`，未推送远端。

## Recommended Next Step

按计划 §5 启动 U3：先做 component-model，逐模块达到行、分支、方法 100%（例外口径沿用精确清单机制：先入 `unit-coverage-exceptions.json` 与仓库属性再验收），完成提交后依次推进 common、core；涉及实连的集成回归先核对共享中间件。
