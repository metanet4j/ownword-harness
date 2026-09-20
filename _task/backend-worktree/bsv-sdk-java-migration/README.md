# BSV SDK Java 迁移工作区

以本地固定的 `reference/ts-stack/packages/sdk` 为参考。四个 Java worktree 基于各自 `feature/java25`，分支、版本与工具路径由 [workspace.json](workspace.json) 维护。

在本目录运行：

```bash
./init.sh                 # 只读环境检查
./verify.sh java-build   # 四仓构建，跳过测试执行
./verify.sh java-smoke   # 现有 SDK 离线回归
./verify.sh ts-build     # 上游 SDK 构建
./verify.sh ts-smoke     # 固定九个文件的离线算法测试
python3 inventory-tests.py  # 重建上游测试文件及辅助向量清单
```

Maven 和 pnpm 分别使用 `./mvn.sh`、`./pnpm.sh`；这两个入口固定工具版本并隔离缓存。对 TS 仅安装 SDK 所需依赖：

```bash
./pnpm.sh --dir ../../../reference/ts-stack --filter @bsv/sdk... install --frozen-lockfile --ignore-scripts
```

本地 `.cache/` 可重新生成，但清空后需重新安装任务 pnpm、依赖并构建，不可将缺失环境视为检查通过。任务 pnpm 版本来自 workspace.json 的 tools.pnpmVersion，安装到 `.cache/tools/pnpm`，不更改全局默认。

环境已验收，见[环境检查报告](doc/环境检查报告-20260920-101559.md)。迁移按[模块迁移计划](doc/模块迁移计划-20260920-103547.md)分阶段推进，遵循[测试迁移契约](doc/测试迁移契约-20260920-101559.md)：逐项复刻上游测试，按 TDD 执行，对照每个用例的 TS/Java 实际结果；每阶段验收包含此前已完成模块的累计回归。

当前仅完成环境、计划与契约，逐用例映射、结果采集/比较工具及 Java 迁移仍待执行。`init.sh`、`verify.sh` 的环境检查与冒烟不能代替迁移验收。

后续入口：[session-handoff.md](session-handoff.md)。
