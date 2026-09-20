# 当前进度

## Current State

[实施前审查](doc/实施前审查-20260920-115837.md)完成，结论为可以进入 P0。五个 Java 仓库和固定 TS 源码状态正常，任务工具与全局默认保持隔离；目标为同级独立工程 metanet4j-bsv-sdk。

本轮五仓构建通过（跳过执行测试）；新 SDK 基础测试 1/1、业务 SDK 离线回归 3/3、TS 九文件冒烟 191/191、检查器自测 23/23 通过。TS 构建、JAR 安装及环境自检通过，共享五个容器 healthy。

完整范围仍为 207 个源码/测试/辅助文件、92 个测试文件、4275 个注册用例及 4856 个 AST 复核位置。Java 功能映射为 0；正式 check 如期拒绝未迁移用例。完整 TS 基线（含 manual）、输入重放、真实结果采集与运行断言完整性验证尚未完成。

## Last Updated

2026-09-20，实施前审查完成，P0 功能项及后续阶段验收依赖已登记。

## Current Objective

本轮只完成审查和功能排期。feature_list.json 中七个 P0 功能项均保持 not-started；migration-map 是它们完成后的联合验收，P1 必须依赖该验收。activeItem 为空，下一项由 nextItem 指向 migration-scope-review。

## Recommended Next Step

读取规则和[模块迁移计划](doc/模块迁移计划-20260920-103547.md)，执行 ./init.sh；将 migration-scope-review 设为进行中，开始完整模块及依赖范围复核。按 feature_list.json 的步骤、产物和验收条件推进，一次只处理一个事项。

审查证据在 .cache/evidence/readiness-*。现有基础测试、冒烟和检查器自测不计入 TS 功能复刻。根仓既有无关改动保留；本次只修改任务计划、状态与审查文档，五个 Java 仓库无源码改动，未推送。
