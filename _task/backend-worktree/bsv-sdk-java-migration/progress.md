# 当前进度

## Current State

P0 完整模块范围复核与 TS 完整基线已完成。六模块为 primitives/compat/script/transaction/wallet/auth；范围与依赖依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。完整范围保持 292 文件、133 测试文件、5329 注册用例及 7554 AST 位置。

[TS 完整基线](doc/TS完整基线-20260920-124400.md)实际 5329/5329 通过，逐文件/用例名/重复次数与冻结清单一致，零失败/跳过/todo，1 个快照通过。manual 保留原 536870928 字节输入，耗时 37:16.72，峰值 RSS 2000384 KiB；普通部分在宿主运行，含内存内 WalletWire 集成，最终 5328/5328 通过，零未登记网络调用。

检查器自测 31/31 通过，所有新增行为保留 RED/GREEN；环境自检通过。目标 Java 工程基础测试最近一次 1/1 通过；Java 功能映射仍为 0，生产移植、实际输入重放和逐断言结果采集未完成，正式 check 仍应拒绝 5329 个未映射用例。

## Last Updated

2026-09-20，范围复核与完整 TS 参考基线通过。

## Current Objective

feature_list.json 的 15 项中 7 项 done、8 项 not-started；activeItem 为空，nextItem 为 migration-api-contract。P0 联合门禁仍未完成，scopeReview 保持 pending。P1 按模块逐行为 TDD 后六模块联合验收，P2 交付独立 SDK。

## Recommended Next Step

完成 migration-api-contract：为六模块全部 API/行为建立 Java 对应关系，明确类型/异常、异步、可变状态、内部断言和浏览器/Node 环境适配；不能根据当前上游测试已通过就认定 API 完整。随后按依赖推进用例映射、输入重放和真实结果采集。

证据批次为 .cache/evidence/ts-baseline-20260920-123124，联合核对日志 ts-baseline-final.log；其他新工具测试日志见 ts-*-red/green.log。scope-* 保存范围复核证据。只修改 metanet4j-bsv-sdk 工程及任务资料/工具；其他四工程和固定 TS 源码只读，根仓既有无关改动保留，未推送。
