# BSV SDK Java 迁移工作区

以本地固定的 `reference/ts-stack/packages/sdk` 为参考。四个既有 Java worktree 基于各自 `feature/java25`；新增同级独立工程 [metanet4j-bsv-sdk](metanet4j-bsv-sdk/README.md) 承载 TS 完整模块，包名为 `com.metanet4j.bsv`。新仓库以骨架提交建立自己的 `feature/java25` 基线，再创建迁移分支。分支、版本与工具路径由 [workspace.json](workspace.json) 维护。

本次唯一实施工程为 `metanet4j-bsv-sdk`；其他 Java 工程只读参考，不修改其源码、测试、POM 或配置，不做业务适配和下游接入。任务范围见 [feature_list.json](feature_list.json) 的 scope。

在本目录运行：

```bash
./init.sh                 # 只读环境检查
./verify.sh bsv-test     # 新 SDK 单元测试，核对实际用例和分包执行数
./verify.sh bsv-build    # 新 SDK 测试通过后打包安装
./verify.sh ts-build     # 上游 SDK 构建
./verify.sh ts-smoke     # 固定九个文件的离线算法测试
python3 inventory-tests.py  # 重建上游测试文件及辅助向量清单
node test-audit.test.cjs    # 检查器自身正常与反例测试
python3 audit-tests.py check # 整模块用例、映射、执行报告及实际结果验收
```

Maven 和 pnpm 分别使用 `./mvn.sh`、`./pnpm.sh`；这两个入口固定工具版本并隔离缓存。对 TS 仅安装 SDK 所需依赖：

```bash
./pnpm.sh --dir ../../../reference/ts-stack --filter @bsv/sdk... install --frozen-lockfile --ignore-scripts
```

本地 `.cache/` 可重新生成，但清空后需重新安装任务 pnpm、依赖并构建，不可将缺失环境视为检查通过。任务 pnpm 版本来自 workspace.json 的 tools.pnpmVersion，安装到 `.cache/tools/pnpm`，不更改全局默认。

环境已验收，见[环境检查报告](doc/环境检查报告-20260920-101559.md)。迁移按[模块迁移计划](doc/模块迁移计划-20260920-103547.md)分阶段推进，遵循[测试迁移契约](doc/测试迁移契约-20260920-101559.md)：逐项复刻上游测试，按 TDD 执行，对照每个用例的 TS/Java 实际结果；每阶段验收包含此前已完成模块的累计回归。

迁移单位是完整模块，已选 `primitives`、`compat`、`script`、`transaction` 全部功能和测试。已清点 92 个文件、4,275 个注册用例（含 manual）；完整性脚本和数据格式见[检查器说明](doc/测试完整性脚本-20260920-104440.md)。

当前检查器自测通过；Java 映射、真实结果采集和生产迁移尚未完成，所以 `audit-tests.py check` 应返回失败并报告缺失。`init.sh`、`verify.sh` 的环境检查与冒烟不能代替迁移验收。

[实施前审查](doc/实施前审查-20260920-115837.md)确认可以进入 P0；七个 P0 功能项及后续完整模块阶段已登记在 [feature_list.json](feature_list.json)，下一项为 `migration-scope-review`。P1 以前必须完成 P0 联合验收。

逐步执行入口：[模块迁移计划](doc/模块迁移计划-20260920-103547.md)中的“文件和脚本的职责”“按顺序执行”和“单行为执行示例”，逐项说明输入、脚本、产物与完成条件；尚未实现的运行/采集入口已明确标记。后续交接：[session-handoff.md](session-handoff.md)。
