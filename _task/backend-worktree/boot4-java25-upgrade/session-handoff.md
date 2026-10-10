# BSV 依赖替换任务交接

## 当前状态

胡先生已于 2026-10-10 授权“开始按照计划执行，先拆feature，记录执行进度和状态”。[feature_list.json](feature_list.json) 是执行状态的唯一来源；七个阶段汇总和 28 个执行项已拆分，拆分项已完成，当前无 activeItem，下一项为 `bsv-r0-source`。既有升级与测试事项保持原样，不计为本次验收。

重启先读 ../AGENTS.md、../mvn-command.md、本目录 AGENTS.md、feature_list.json.planDoc、feature_list.json 与 progress.md，运行不带参数的 ./init.sh。授权在既定计划范围持续有效，无需重复请求。一次只做一个执行项，验证及提交齐全后更新状态。

## Blockers

- 无开工授权阻塞；R0 离线准备可执行。
- 沙箱缓存只读且本机网络受限，Maven／本地 HTTP／中间件测试使用宿主权限。
- SDK 制品接入待 R1；五个共享设施停止、资源隔离待集成前处理，不阻塞 R0。
- 原 SDK 裸 clean test 缺少重放变量时有 4 例 HTTP 失败；复用正确来源校验与打包入口，不修改只读原任务消解缺口。

## Files

当前主仓改动为计划、feature_list.json、progress.md、session-handoff.md。R0 后续增加基线、API／测试／向量清单并修正任务入口。四子仓库均在 feature/bsv-sdk-replace；base/pom.xml 既有 diff 必须保存，不还原、不提前提交孤立改动。原 SDK 固定 3dd8bebe4e465625f2930179bb3c5fcf71b637a2。

主仓 AGENTS.md、infra、其他任务数据删除及 .opencode 的既有无关改动保留，不混入提交。子仓库独立提交，Maven 和共享 target 串行运行；不推送、不广播交易、不读 Archive。

## Next Session

拆分检查及 ./init.sh 通过；执行 bsv-r0-source。完成条件与产物以 feature_list.json 为准，方案及阶段门禁引用 [当前计划](doc/BSV依赖替换计划-20261010-103802.md)。
