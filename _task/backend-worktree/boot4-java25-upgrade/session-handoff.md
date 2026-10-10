# BSV 依赖替换任务交接

## 当前状态

胡先生已于 2026-10-10 授权“开始按照计划执行，先拆feature，记录执行进度和状态”，并在本次会话明确“目标是计划完全执行完成”。[feature_list.json](feature_list.json) 是执行状态的唯一来源；七个阶段汇总和 28 个执行项已拆分，当前无 activeItem，下一项 bsv-r2-behavior；**R0（6/6）与 R1（3/3）阶段全部完成、门禁 PASS**，进入 R2 base 适配。既有升级与测试事项保持原样，不计为本次验收。

重启先读 ../AGENTS.md、../mvn-command.md、本目录 AGENTS.md、feature_list.json.planDoc、feature_list.json 与 progress.md，运行不带参数的 ./init.sh。授权在既定计划范围持续有效，无需重复请求。一次只做一个执行项，验证及提交齐全后更新状态。

## Blockers

- 无开工授权阻塞；R0 离线准备可执行。
- 沙箱缓存只读且本机网络受限，Maven／本地 HTTP／中间件测试使用宿主权限。
- SDK 制品接入待 R1；五个共享设施停止、资源隔离待集成前处理，不阻塞 R0。
- 原 SDK 裸 clean test 缺少重放变量时有 4 例 HTTP 失败；复用正确来源校验与打包入口，不修改只读原任务消解缺口。

## Files

拆分已提交；来源冻结新增 baseline.json，原始证据在 evidence/bsv-replace/r0-source-20261010-1130。bsv-r0-api 新增任务根目录 bsv-replace-api-map.json 与可复用入口 bsv-api-audit.py（`check` 核对映射，`--require-clean` 供 R5/R6 清零门禁）；取证与复核证据在 evidence/bsv-replace/r0-api-work（该目录被任务 .gitignore 忽略，属本地证据，不随提交）。bsv-r0-tests 新增 bsv-replace-test-map.json，并扩展 bsv-api-audit.py 的 `test-map` 子命令（核对测试映射与清单双向一致）。bsv-r0-vectors 新增 bsv-replace-vectors.json 与纯 Python 独立复算脚本 check-vectors.py 及复核脚本 verify-vectors.py。bsv-r0-gate 新增可重跑阶段门禁 bsv-task-gate.py（按阶段检查允许的未提交改动）与证据刷新入口 refresh-r0-api-evidence.sh；R1 新增 bsv-replace-artifact.json、bsv-replace-dependencies.json、bsv-replace-fingerprint.json，并改造 verify-unit.py 绑定 SDK 制品指纹。四子仓库均在 feature/bsv-sdk-replace；base/pom.xml 既有 diff 必须保存，不还原、不提前提交孤立改动。原 SDK 固定 3dd8bebe4e465625f2930179bb3c5fcf71b637a2。

主仓 AGENTS.md、infra、其他任务数据删除及 .opencode 的既有无关改动保留，不混入提交。子仓库独立提交，Maven 和共享 target 串行运行；不推送、不广播交易、不读 Archive。

## Next Session

唯一下一步是 bsv-r2-behavior：按 API 映射在 metanet4j-base 建立最小业务类型（BsvNetwork／HashBytes／BsvAddress／BsvAmount）并迁移 BapHelper、AipHelper 与测试，替换公开接口中的旧类型；随后 bsv-r2-accept 跑 `verify-unit.py --mode accept --scope metanet4j-base` 并安装 base 制品。注意 base 既有 POM 改动要与本次实现共同提交，不还原、不孤立提交。持续实施授权已记录。R0／R1 产物：API 映射、测试映射、向量、制品记录、依赖路径与指纹绑定文件均在任务根目录；门禁用法 `python3 bsv-task-gate.py --stage r0|r1|...`。

阶段门禁用法：`python3 bsv-task-gate.py --stage r0|r1|...`；证据刷新：`./refresh-r0-api-evidence.sh`。
