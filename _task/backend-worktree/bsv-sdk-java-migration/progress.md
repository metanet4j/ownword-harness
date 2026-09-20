# 当前进度

## Current State

P0 完整模块范围复核已完成，依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。发现类型及真实测试辅助依赖，完整纳入 wallet/auth；15 个候选模块均有结论，六模块依赖闭合，九模块排除依据齐全。

冻结清单为 292 文件、133 测试文件、5329 注册用例及 7554 AST 位置；原 207 文件和 4275 用例对象全部保留。源码类型/测试依赖形成六模块闭环，P1 按模块逐行为实施，六模块联合验收；P2 为独立 SDK 最终交付。

本轮依赖扫描修复遵循 TDD：23 通过/1 失败 → 24/24 通过；目标工程 clean test 基础测试 1/1 通过，零失败/错误/跳过。init 通过，正式 check 重新清点一致后预期拒绝缺失的 5329 个 Java 映射。原始证据在 .cache/evidence/scope-*。完整 TS 基线和 Java 生产迁移均未完成。

## Last Updated

2026-09-20，完整模块与测试依赖范围复核完成。

## Current Objective

feature_list.json 中 migration-scope-review 已完成，activeItem 为空，nextItem 为 migration-ts-baseline。先执行已满足依赖的完整 TS 基线，尽早验证参考测试和 manual 资源边界，再继续 API/用例映射；一次只推进一个事项。

## Recommended Next Step

按 migration-ts-baseline 的步骤实现读取冻结清单的 TS 运行入口，审查网络模拟和 manual 内存预算，实际执行六模块全部测试并保存每次运行的独立报告。未通过完整基线不能完成 P0。

本次唯一工程为 metanet4j-bsv-sdk；新增 wallet/auth 包目录已提交 72d2007，基础测试不计入 TS 移植数量。其他四工程只读，固定 TS 源码无改动；根仓既有无关改动保留，未推送。
