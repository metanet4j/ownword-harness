# BSV 依赖替换任务交接

## 当前状态

胡先生已于 2026-10-10 授权“开始按照计划执行，先拆feature，记录执行进度和状态”，并在本次会话明确“目标是计划完全执行完成”。[feature_list.json](feature_list.json) 是执行状态的唯一来源；七个阶段汇总和 28 个执行项已拆分，当前无 activeItem，下一项 bsv-r0-gate；R0 进度 5/6，已完成来源冻结、任务入口、方法级 API 映射、逐用例迁移清单和 V01—V14 独立样本。既有升级与测试事项保持原样，不计为本次验收。

重启先读 ../AGENTS.md、../mvn-command.md、本目录 AGENTS.md、feature_list.json.planDoc、feature_list.json 与 progress.md，运行不带参数的 ./init.sh。授权在既定计划范围持续有效，无需重复请求。一次只做一个执行项，验证及提交齐全后更新状态。

## Blockers

- 无开工授权阻塞；R0 离线准备可执行。
- 沙箱缓存只读且本机网络受限，Maven／本地 HTTP／中间件测试使用宿主权限。
- SDK 制品接入待 R1；五个共享设施停止、资源隔离待集成前处理，不阻塞 R0。
- 原 SDK 裸 clean test 缺少重放变量时有 4 例 HTTP 失败；复用正确来源校验与打包入口，不修改只读原任务消解缺口。

## Files

拆分已提交；来源冻结新增 baseline.json，原始证据在 evidence/bsv-replace/r0-source-20261010-1130。bsv-r0-api 新增任务根目录 bsv-replace-api-map.json 与可复用入口 bsv-api-audit.py（`check` 核对映射，`--require-clean` 供 R5/R6 清零门禁）；取证与复核证据在 evidence/bsv-replace/r0-api-work（该目录被任务 .gitignore 忽略，属本地证据，不随提交）。bsv-r0-tests 新增 bsv-replace-test-map.json，并扩展 bsv-api-audit.py 的 `test-map` 子命令（核对测试映射与清单双向一致）。bsv-r0-vectors 新增 bsv-replace-vectors.json 与纯 Python 独立复算脚本 check-vectors.py 及复核脚本 verify-vectors.py。R0 仅剩阶段门禁。四子仓库均在 feature/bsv-sdk-replace；base/pom.xml 既有 diff 必须保存，不还原、不提前提交孤立改动。原 SDK 固定 3dd8bebe4e465625f2930179bb3c5fcf71b637a2。

主仓 AGENTS.md、infra、其他任务数据删除及 .opencode 的既有无关改动保留，不混入提交。子仓库独立提交，Maven 和共享 target 串行运行；不推送、不广播交易、不读 Archive。

## Next Session

唯一下一步是 bsv-r0-gate：复核 R0 完整性与阶段门禁（来源、自检、API 映射、逐用例映射、14 组样本齐全；无遗漏旧调用与未决能力缺口；产物来源与检查输出可复查），通过后才进入 R1。持续实施授权已记录。API 映射见 bsv-replace-api-map.json，测试映射见 bsv-replace-test-map.json，向量见 bsv-replace-vectors.json；自检证据在 evidence/bsv-replace/r0-harness-20261010/。
