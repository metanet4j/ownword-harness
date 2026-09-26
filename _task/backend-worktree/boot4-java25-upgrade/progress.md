# progress.md — boot4-java25-upgrade 进度

本文件只记录当前状态；范围和验收标准见[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)，逐模块状态见 `feature_list.json`。

## 当前状态

- **更新时间**：2026-09-26。
- **当前目标**：为四个子仓库建立完整单元测试、集成测试与逐模块覆盖率证据。
- **当前阶段**：`unit-u2-sdk` 正在实施；U0 测试基线及 U1 base 已完成，U3—U9 待实施。
- **下一步**：从 sdk 的公开密钥、交易、脚本、UTXO 和 HTTP API 补有效断言；HTTP 外部协议使用本地服务，自动测试不广播主网。

## 已验证结果

U0 [四仓测试基线](doc/测试基线与障碍-20260926-145423.md)列出 25 POM、369 个生产 Java 文件、最初 52 个测试文件，以及 19 项集成边界的隔离和观测方式。当前 `unit-test-inventory.json` 已增至 57 个测试文件。U0 全仓基线有 56 个旧用例通过、8 个跳过；17 个含可执行代码的 component 模块零本地单元测试。`component-core` 仅定义接口，按 N/A 处理。宿主五项共享服务健康，但集成测试尚未执行。

U1 base 提交 `bae7eb6` 与 `77ad9fd`：UTXO 相等性缺陷先红后绿；AIP 坏签名返回 false；BAP 固定身份向量、协议枚举、DTO 与 Jackson 行为均有断言。最终提交后，`python3 verify-unit.py --mode accept --scope metanet4j-base` 退出 0；19 个测试全部通过，零失败/错误/跳过，JaCoCo LINE 208/208、BRANCH 76/76、METHOD 51/51，`jacoco:check` 通过。证据在本地 `evidence/20260926T072220Z/`；同一提交的 base 0.2.0 构件已安装至隔离 Maven 仓库。

sdk 的 U0 离线基线为 24 个测试通过，行 307/1990、分支 24/505、方法 91/454。公网 Bitails 历史用例已隔离为 `external`；其替代本地 HTTP 集成测试尚未实施。component 的 17 个零测试模块、文件模块 8 个禁用测试、固定 ES 索引与交易主网广播风险仍未消解，不能宣布整体验收完成。

## 仓库与工作区

四子仓库沿用 `feature/java25`，不推送。parent JaCoCo 配置提交 `4112a48`，sdk 测试分类提交 `2577406`，component 测试分类提交 `de1f59f`。ownword 主仓既有 `AGENTS.md`、standard 规范及技能文件的无关改动保留，不纳入本任务提交。
