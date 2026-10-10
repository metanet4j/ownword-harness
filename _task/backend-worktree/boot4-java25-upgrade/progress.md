# BSV 依赖替换任务进度

## Current State

- **Last Updated**：2026-10-10T19:05:00+08:00。
- **Current Objective**：按 [实施计划](doc/BSV依赖替换计划-20261010-103802.md) 串行执行 R0—R6，已完成 feature 拆分、基线冻结、任务入口和方法级 API 映射，继续逐用例迁移清单。
- **Active Item**：无；R0 已完成 3/6，下一项 `bsv-r0-tests`。实时状态唯一来源为 [feature_list.json](feature_list.json)。
- **授权范围**：胡先生已明确指令“开始按照计划执行，先拆feature，记录执行进度和状态”。授权覆盖既定 R0—R6，原 SDK 输入、共享设施配置及远端边界继续适用。
- 七阶段汇总与 28 个执行项已拆分；每项记录依赖、产物、完成条件、验证证据及提交，一次只推进一个执行项。

## 已有基线与验收依据

四仓库分支均为 `feature/bsv-sdk-replace`；HEAD 为 parent `7302e1b`、base `53ed9ad`、sdk `670ee3d`、component `3ce773b`。base/pom.xml 的既有未提交修改保留，R0 单独冻结，R2 与适配共同提交。指定 SDK 固定 `3dd8beb`，源码、测试、POM 及原迁移证据只读。

原单元证据 `evidence/20260930T125355Z/` 记录 25 POM、23 模块、841 例、零失败／错误／跳过、gaps=0；原 component 集成证据 `evidence/20260930T130119Z-integration/` 为 18 类／124 例。SDK 另有 5 例本地 HTTP 集成，需单独验收。以上不代表本次替换通过。SFTP 成功连接 2 行继续保留已批准精确覆盖例外。

## 验证与限制

- 工具链 JDK 25.0.4.1／Maven 3.9.16 可用，全局默认不变。
- 宿主目标 Maven 缓存可写；沙箱缓存只读且本机网络受限，构建与相关测试使用宿主执行环境。
- 新 SDK 尚未安装至目标缓存，按 R1 接入。五个共享中间件停止，集成前使用已有 infra/up.sh 并先确认测试资源隔离。
- init.sh 已校正当前计划、替换分支、唯一当前项、依赖、完成证据和阶段汇总；--full 明确退出 2，构建采用计划严格入口。
- 旧来源复核证据见 `evidence/bsv-replace/plan-20261010-103802/`；本次执行证据按 feature 单独记录。

## 本次执行证据

- feature 拆分提交：`1439448`；结构、依赖及状态检查 PASS。
- 来源冻结提交：`b0db12c`。
- [baseline.json](baseline.json)：五仓库与 25 POM 指纹、67 个生产／69 个测试直接旧引用、base 既有 diff 已冻结。
- `evidence/bsv-replace/r0-source-20261010-1130/`：来源 revision、full-evidence verify 和 ./init.sh 均退出 0。原验收证据复核 PASS，未重跑测试体。

- 任务入口及状态门禁提交：`fa59f4b`；实施执行项已完成 **3/28**，R0 为 **3/6**，其余阶段尚未开始。
- `evidence/bsv-replace/r0-harness-20261010/`：自检正常状态退出 0，12 项真实进程门禁检查通过，异常返回非零；子仓库及既有 base diff 保持。

### bsv-r0-api 方法级 API 与调用映射

- 产物 [bsv-replace-api-map.json](bsv-replace-api-map.json)：62 个旧类型决议（replace 30／adapt 13／delete 15／gap 4），逐条含旧 FQN、实际调用方法、callerFiles、目标类型与目标方法、行为编号、阶段与说明；sha256 `032c91c0…`。
- 独立复核 11 项 PASS：映射覆盖 67/67 生产文件、逐文件回读旧 import 全部被认领、目标类型与成员真实存在于新 SDK 公开面、决议与行为挂接完整；配置与反射结论与取证产物一致。
- 能力缺口 7 项全部有结论：新增最小网络值类型 `BsvNetwork`、哈希值类型 `HashBytes`、地址 `BsvAddress`、金额 `BsvAmount`、业务异常基线；删除 KeyBag／RedeemData／TxHelper 抽象改为解锁模板；脚本地址与类型判定按需自建。6 个业务新类型落点写入映射的 `businessNewTypes`。
- 复用入口 [bsv-api-audit.py](bsv-api-audit.py)：核对映射与四仓库源码，`--require-clean` 供 R5/R6 作为旧引用清零门禁；当前 status=PASS，生产旧 import 残留基线 308、测试 358。
- 取证与复核产物在 `evidence/bsv-replace/r0-api-work/`（summary.json、api-map-verify.json、api-audit.json、四份子代理取证与 api-resolution.json）。

## Recommended Next Step

执行 `bsv-r0-tests`：以 `unit-test-inventory.json`（22 个模块、205 个测试类、841 个 unit 方法）和 69 个旧引用测试文件为基线，逐类逐方法登记目标、处理方式与行为编号，分开列出业务 SDK 5 例本地 HTTP 集成与 component 18 类／124 例集成，并标明计数口径（源码静态计数 vs 既有报告）。R1—R6 均待前置阶段门禁。
