# BSV 依赖替换任务交接

## 当前状态

当前交付是 [BSV 依赖替换实施与验收计划](doc/BSV依赖替换计划-20261010-103802.md)。计划已完成并通过静态复核；代码实施尚未批准，R0—R6 均为 `not-started`。既有升级与测试验收仍保持完成状态，不能将其当作本次替换验收。

重启先读 `../AGENTS.md`、`../mvn-command.md`、本目录 `AGENTS.md`、新计划、`feature_list.json` 和 `progress.md`，运行不带 `--full` 的 `./init.sh`。新计划由 `feature_list.json.planDoc` 指向，原升级计划保存在 `upgradePlanDoc`。不新建或切换分支、不推送、不广播真实交易、不读取 Archive。

## Blockers

- 本轮仅授权计划文档；实施按任务 AGENTS.md 要求取得明确批准。
- 宿主已确认五个共享容器均 exited、五端口拒绝连接；集成前使用已有 infra/up.sh 启动并检查 healthy、认证握手及资源隔离。
- 目标 Maven 缓存在宿主可写、在沙箱只读；构建及本地网络测试使用宿主执行环境。新 SDK 尚未安装到目标缓存，R1 重新打包校验后接入。
- 新 SDK 的裸 `clean test` 缺少重放环境变量时有 4 例 HTTP 测试失败，正确来源验收和制品接入方法见新计划及 [原 SDK 任务交接](../bsv-sdk-java-migration/session-handoff.md)。不修改原迁移工具或冻结证据来绕过门禁。

## Files

本轮主仓范围：新计划、`feature_list.json`、`progress.md`、`session-handoff.md`。四子仓库当前分支均为 `feature/bsv-sdk-replace`，HEAD 为 parent `7302e1b`、base `53ed9ad`、sdk `670ee3d`、component `3ce773b`；base/pom.xml 的既有未提交替换改动必须保留。

新 SDK 固定提交 `3dd8bebe4e465625f2930179bb3c5fcf71b637a2`，来源为相邻 `bsv-sdk-java-migration/metanet4j-bsv-sdk`；原验收 `javaRevision` 是全部 Java 工作树的 SHA-256 摘要，不是 Git 提交；当前重新计算与冻结摘要一致，完整证据只读复核 PASS。该任务 SDK 输入和其他工作树只读。Maven 缓存分别为源任务 `.cache/maven` 与目标 `~/.m2/metanet4j`。

本轮只运行环境自检、宿主只读核查和原 SDK 证据复核；证据见 `evidence/bsv-replace/plan-20261010-103802/static-check.json` 及 `environment-check.json`；不把已有 841 例单元、component 124 例集成及 SDK 源码中的 5 例本地 HTTP 集成表述为本次通过。SFTP 成功连接 2 行继续保留已批准例外；源码／测试清单与覆盖例外只能按实际迁移及检查结果调整。

主仓既有 AGENTS.md、infra 文件、其他任务数据删除及 .opencode 改动须保留，不混入本任务提交。共享 target 和 Maven 验证串行运行；最终单元与集成须保存独立报告，集成先隔离资源。

## Next Session

唯一下一步是取得明确实施指令后推进 R0：重查来源与已有改动，建立方法级 API／测试映射、固定向量和自检门禁，再按依赖顺序执行后续阶段。具体工作与验收以新计划为准。
