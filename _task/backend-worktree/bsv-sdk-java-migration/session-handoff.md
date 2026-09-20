# 会话交接

## 状态

用户明确本次只修改 metanet4j-bsv-sdk；其他工程源码、测试、POM 和配置只读，不做业务适配或下游接入。完整模块迁移要求不变，不能只迁移业务调用的方法。四个完整模块已清点，检查器及 23 项自测通过。同级独立工程 metanet4j-bsv-sdk 已创建、测试和打包，基础测试 1/1 与既有 SDK 离线回归 3/3 通过。实施前审查确认可进入 P0，功能项已登记；本轮 TS 构建与 191 个冒烟、五仓构建和环境检查通过。Java 映射与生产移植尚未开始，真实结果采集适配器待实现，最终 check 当前应失败。

## Files

- `doc/实施前审查-20260920-115837.md`：本轮复验结果、P0 前置缺口及进入实施的边界。
- `feature_list.json`：七个 P0 功能项、migration-map 联合验收及 P1–P3 的步骤/产物/验收条件；nextItem 为 migration-scope-review。

- `workspace.json`：四个既有 worktree 与新独立仓库的基线、迁移分支、Java 目标工程和包名、TS 固定提交与工具版本。
- `metanet4j-bsv-sdk/README.md`：新工程的包、测试、向量目录及 Git 基线策略；`./verify.sh bsv-test|bsv-build` 为测试与打包入口。
- `README.md`、`init.sh`、`mvn.sh`、`pnpm.sh`、`verify.sh`：环境使用与验证入口。
- `upstream-tests.json`、`inventory-tests.py`：全 SDK 测试文件及辅助向量清单，含校验值。
- `module-scope.json`、`module-tests.json`：完整模块范围、静态依赖、全部文件校验值、4,275 个注册用例与 AST 复核位置。
- `audit-tests.py`、`collect-cases.cjs`、`test-audit.test.cjs`：清点、证据核对及检查器自测。`test-map.json` 当前为空；不得填入伪造映射。
- `doc/测试完整性脚本-20260920-104440.md`：命令、证据格式、实测结果及自动化边界。
- `doc/环境检查报告-20260920-101559.md`：实测命令、结果与未验证范围。
- `doc/测试迁移契约-20260920-101559.md`：TDD、一比一复刻、逐用例运行结果一致和阶段累计验收门禁。
- `doc/模块迁移计划-20260920-103547.md`：P0–P3 的完整模块阶段；primitives/script/transaction 循环依赖需联合验收，随后整模块 compat；状态见 feature_list.json。

## Blockers

开始 P0 无环境阻塞；完整 TS 基线（含 manual 大输入）、API/断言映射和真实采集仍须完成，未通过 P0 联合验收不能进入 P1。用户已明确并确认 Java 目标为任务根目录下的同级 metanet4j-bsv-sdk，不能再次嵌套进 metanet4j-sdk。新仓库建立自己的 feature/java25 基线后创建迁移分支；新 SDK 的公开 Java 类型及行为映射仍在 P0 收敛；P3 为本工程最终验收，不包含对其他工程的修改。

## Next Session

读取本目录 AGENTS.md、README.md、feature_list.json、测试契约、模块计划与脚本说明，运行 ./init.sh。先读模块计划的“文件和脚本的职责”及“按顺序执行”，将 migration-scope-review 设为进行中，并把 activeItem 设为该 ID；先按本项步骤完成范围复核，再按依赖推进其余 P0 项。第 2–4 步对应的 P0 工作包括：核对完整模块的全部 API/行为、建立 Java 用例/断言映射、审查跨目录测试和依赖、实现真实结果采集。完整模块 TS 测试运行入口、输入重放及两端采集尚待实现，不能把现有 check 当作运行器；落实后更新计划与 README 中的实际命令。AESGCM.man.test.ts 已纳入 primitives，必须执行，不可排除。已选模块内的 Schnorr、Secp256r1、BEEF、脚本模板、广播/链追踪等未被业务直接使用的功能也必须完整迁移。

`python3 audit-tests.py check` 会重新清点上游并比对冻结清单；当前预期报 4,275 个未映射项。不要为让门禁变绿删改清单、自动填写 reviewed，或把 `compare` 调试命令当作最终验收。Jest 注册数不覆盖测试体内每条循环/属性样本，需结合 AST 位置人工复核和运行结果采集；原始报告及其校验值必须匹配。

开始新增 Java 测试前，具体接口边界须满足 tdd 技能要求；按用户指定上游测试逐项映射，任何尚未确认的接口差异须先解决。一次只写一个失败测试并实现使其通过，保留 RED/GREEN 与两端实际结果。每阶段重跑已完成模块；全部范围内用例执行通过、逐项结果一致且核对无遗漏之前，不得标记迁移完成。

当前 activeItem 为空；本轮未提前启动迁移功能项，migration-readiness 已完成。四个既有 worktree 保持 feature/java25 起点，未改其 Java/POM；新工程骨架已独立提交，源码版本校验已包含该仓库。新工程的 infrastructure 测试不属于 TS 功能复刻，不能加入上游映射充数。未推送。根仓既有无关规则/技能修改继续保留，不混入本任务提交。
