# 当前进度

## Current State

P0 完整模块范围复核与 TS 完整基线已完成，migration-api-contract 正在进行。六模块仍为 primitives/compat/script/transaction/wallet/auth；冻结测试范围保持 292 文件、133 测试文件、5329 注册用例及 7554 AST 位置。

API 清点已建立：133 个 API 源文件、3576 个声明、1016 个导出入口，包含根入口及公开导出的 CompletedProtoWallet。详情和行为设计统一见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。api-map.json 已复核 hex 的 3 项设计映射，其余 3573 项未映射；API check 应失败，不能进入 P1。

检查器自测 35/35 通过；API 的重新扫描、根入口和漏项反例已验证。Reader 小输入探针确认 undefined/NaN、默认读取后的游标及共享视图语义；8 组 AES 探针两条 TS/Node 路径输出一致，只代表这 8 组实际输入。探针均不计入 SDK 用例。

[完整 TS 基线](doc/TS完整基线-20260920-124400.md)此前已实际 5329/5329 通过，含原规模 manual；本轮源码未变，没有重复耗时 37 分钟的 manual。目标 Java 工程基础测试最近一次 1/1 通过，本轮没有 Java 代码变更。Java 测试映射仍为 0，生产移植、输入重放和逐断言结果采集尚未完成。

## Last Updated

2026-09-20，API 源码清点和检查入口已建立；API 行为映射继续进行。

## Current Objective

feature_list.json 共 15 项：7 项 done、1 项 in-progress、7 项 not-started。activeItem 和 nextItem 均为 migration-api-contract。scopeReview 保持 pending；P1 必须等待 P0 联合门禁。

## Recommended Next Step

继续复核 primitives 的数值/缺失值和字节视图公共类型，再逐项完成全部六模块的 Java API、默认值、状态、异常、异步和宿主适配。已完成的源码分母可直接复用；不得自动生成 reviewed 或提前批量创建 Java 测试。

本轮证据位于 .cache/evidence/api-*；此前完整 TS 基线在 .cache/evidence/ts-baseline-20260920-123124。只修改任务资料和验证工具，五个 Java 仓库及固定 TS 上游无本轮改动；根仓既有无关修改保留，未推送。
