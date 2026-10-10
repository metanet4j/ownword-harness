# BSV 依赖替换任务进度

## Current State

- **Last Updated**：2026-10-10T11:27:30+08:00。
- **Current Objective**：按 [实施计划](doc/BSV依赖替换计划-20261010-103802.md) 串行执行 R0—R6，已完成 feature 拆分与基线冻结，继续校正任务入口。
- **Active Item**：无；`bsv-r0-source` 已完成，下一项 `bsv-r0-harness`。实时状态唯一来源为 [feature_list.json](feature_list.json)。
- **授权范围**：胡先生已明确指令“开始按照计划执行，先拆feature，记录执行进度和状态”。授权覆盖既定 R0—R6，原 SDK 输入、共享设施配置及远端边界继续适用。
- 七阶段汇总与 28 个执行项已拆分；每项记录依赖、产物、完成条件、验证证据及提交，一次只推进一个执行项。

## 已有基线与验收依据

四仓库分支均为 `feature/bsv-sdk-replace`；HEAD 为 parent `7302e1b`、base `53ed9ad`、sdk `670ee3d`、component `3ce773b`。base/pom.xml 的既有未提交修改保留，R0 单独冻结，R2 与适配共同提交。指定 SDK 固定 `3dd8beb`，源码、测试、POM 及原迁移证据只读。

原单元证据 `evidence/20260930T125355Z/` 记录 25 POM、23 模块、841 例、零失败／错误／跳过、gaps=0；原 component 集成证据 `evidence/20260930T130119Z-integration/` 为 18 类／124 例。SDK 另有 5 例本地 HTTP 集成，需单独验收。以上不代表本次替换通过。SFTP 成功连接 2 行继续保留已批准精确覆盖例外。

## 验证与限制

- 工具链 JDK 25.0.4.1／Maven 3.9.16 可用，全局默认不变。
- 宿主目标 Maven 缓存可写；沙箱缓存只读且本机网络受限，构建与相关测试使用宿主执行环境。
- 新 SDK 尚未安装至目标缓存，按 R1 接入。五个共享中间件停止，集成前使用已有 infra/up.sh 并先确认测试资源隔离。
- init.sh 的旧分支预期和 --full 判定在 `bsv-r0-harness` 修正。
- 旧来源复核证据见 `evidence/bsv-replace/plan-20261010-103802/`；本次执行证据按 feature 单独记录。

## 本次执行证据

- feature 拆分提交：`1439448`；结构、依赖及状态检查 PASS。
- [baseline.json](baseline.json)：五仓库与 25 POM 指纹、67 个生产／69 个测试直接旧引用、base 既有 diff 已冻结。
- `evidence/bsv-replace/r0-source-20261010-1130/`：来源 revision、full-evidence verify 和 ./init.sh 均退出 0。原验收证据复核 PASS，未重跑测试体。

## Recommended Next Step

执行 `bsv-r0-harness`，校正当前计划加载、分支检查、feature 状态及失败退出；移除自检承担构建验收的旧入口，再进入方法级 API 映射。
