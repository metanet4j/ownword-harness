# 当前进度

## Current State

[实施前审查](doc/实施前审查-20260920-115837.md)完成，结论为可以进入 P0。五个 Java 仓库和固定 TS 源码状态正常，任务工具与全局默认保持隔离；本次唯一可修改工程为同级 metanet4j-bsv-sdk；其他工程源码、测试、POM 和配置均只读，工程边界见 feature_list.json 的 scope。

本轮五仓构建通过（跳过执行测试）；新 SDK 基础测试 1/1、业务 SDK 离线回归 3/3、TS 九文件冒烟 191/191、检查器自测 23/23 通过。TS 构建、JAR 安装及环境自检通过，共享五个容器 healthy。

完整范围仍为 207 个源码/测试/辅助文件、92 个测试文件、4275 个注册用例及 4856 个 AST 复核位置。Java 功能映射为 0；正式 check 如期拒绝未迁移用例。完整 TS 基线（含 manual）、输入重放、真实结果采集与运行断言完整性验证尚未完成。

## Last Updated

2026-09-20，独立 SDK 实施范围及 P0–P3 功能项明确。

## Current Objective

feature_list.json 保留七个 P0 功能项和 P0 联合验收，随后执行 P1 三模块联合迁移、P2 完整 compat、P3 独立 SDK 最终验收；本次不含其他工程适配或接入。迁移功能项均为 not-started，activeItem 为空，nextItem 为 migration-scope-review。

## Recommended Next Step

读取规则和[模块迁移计划](doc/模块迁移计划-20260920-103547.md)，执行 ./init.sh；将 migration-scope-review 设为进行中，开始完整模块及依赖范围复核。按 feature_list.json 的步骤、产物和验收条件推进，一次只处理一个事项。

审查证据在 .cache/evidence/readiness-*。现有基础测试、冒烟和检查器自测不计入 TS 功能复刻。根仓既有无关改动保留；当前工程范围明确后只调整任务资料及目标工程 README，未修改任何 Java 源码或 POM；其他四个 Java 工程无本任务改动，未推送。
