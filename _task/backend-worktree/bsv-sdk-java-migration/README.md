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
./verify.sh ts-modules   # 六模块真实完整基线，含原规模 manual，耗时较长
python3 inventory-tests.py  # 重建上游测试文件及辅助向量清单
node test-audit.test.cjs    # 检查器自身正常与反例测试
node audit-api.cjs check    # 重新扫描源码并检查完整 Java API 映射
node audit-api.cjs batches  # 核对编码任务分配、依赖和嵌入 API 复核清单
node api-hash-random-probe.cjs # 哈希/DRBG/随机宿主行为观察，非 Java 验收
node api-values-probe.mjs  # 观察固定 TS 的数值/容器/模运算边界；输出不是测试报告
python3 run-hex-parity.py --bn-constructor # 累计 Hex + BigNumber 构造；逐项比较实际输入/结果，仅内部实施项
python3 audit-tests.py check # 整模块用例、映射、执行报告及实际结果验收
```

Maven 和 pnpm 分别使用 `./mvn.sh`、`./pnpm.sh`；这两个入口固定工具版本并隔离缓存。对 TS 仅安装 SDK 所需依赖：

```bash
./pnpm.sh --dir ../../../reference/ts-stack --filter @bsv/sdk... install --frozen-lockfile --ignore-scripts
```

本地 `.cache/` 可重新生成，但清空后需重新安装任务 pnpm、依赖并构建，不可将缺失环境视为检查通过。任务 pnpm 版本来自 workspace.json 的 tools.pnpmVersion，安装到 `.cache/tools/pnpm`，不更改全局默认。

环境已验收，见[环境检查报告](doc/环境检查报告-20260920-101559.md)。迁移按[模块迁移计划](doc/模块迁移计划-20260920-103547.md)分阶段推进，遵循[测试迁移契约](doc/测试迁移契约-20260920-101559.md)：逐项复刻上游测试，按 TDD 执行，对照每个用例的 TS/Java 实际结果；每阶段验收包含此前已完成模块的累计回归。

迁移单位是完整模块，范围复核确认 `primitives`、`compat`、`script`、`transaction`、`wallet`、`auth` 六模块，含 133 个测试文件、5,329 个注册用例（含 manual）。范围依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)，完整性脚本和数据格式见[检查器说明](doc/测试完整性脚本-20260920-104440.md)。

本轮修复及正式全量验收已完成：`full-run-repaired-20261012` 四阶段全 exit=0，133 原文件、5329 原用例、38092 输入样本、56744 实际断言逐项一致，`formalAcceptance=true`。六例重放缺口与 25 例输入差异已修复，缺口/输入替换/无序豁免均为 0；32 条原本不可达站点按用户确认保留证明，独立有效 DRBG 分支 3/3 通过。

当前 Java 完整测试 5451/5451 通过，JAR 与 sources 已安装任务缓存。43 个事项全部 done，28 个实施事项的当前来源报告已逐项刷新。三项独立终审复核均通过，命令和明确口径见 [session-handoff.md](session-handoff.md)；当前证据及交付见 [progress.md](progress.md)。
