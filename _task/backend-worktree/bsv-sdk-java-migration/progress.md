# 当前进度

## Current State

P0 完整模块范围复核与 TS 完整基线已完成，migration-api-contract 正在进行。六模块仍为 primitives/compat/script/transaction/wallet/auth；冻结测试范围保持 292 文件、133 测试文件、5329 注册用例及 7554 AST 位置。

API 清点已建立：133 个 API 源文件、3576 个声明、1016 个导出入口，包含根入口及公开导出的 CompletedProtoWallet。详情和行为设计统一见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。api-map.json 已复核 9 个完整文件的 371 项设计映射，其余 3205 项未映射；API check 应失败，不能进入 P1。

已确定 number/BigInteger、Undefined/null、列表/空洞和 ByteView 的表示，以及 BigNumber/模运算的状态、编码、身份和错误契约。api-values-probe.mjs 在 Buffer 有/无两种环境各运行 26 组输入；这 26 组观察相同，不代表全输入或 Java 等价。检查器自测最近一次 35/35 通过，本轮未修改检查器，不重复执行；所有探针均不计入 SDK 用例。

用户已授权 WUA-ZERO-CAPACITY：Java 零容量首次扩容从 1 开始，单列差异与额外回归，不改固定 TS；授权、最小范围和验证要求见 API 文档对应章节。当前仅完成设计，尚未实施修复。其他源码异常按原行为保留，不扩大本次授权。

[完整 TS 基线](doc/TS完整基线-20260920-124400.md)此前已实际 5329/5329 通过，含原规模 manual；本轮源码未变，没有重复耗时 37 分钟的 manual。目标 Java 工程基础测试最近一次 1/1 通过，本轮没有 Java 代码变更。Java 测试映射仍为 0，生产移植、输入重放和逐断言结果采集尚未完成。

## Last Updated

2026-09-20，完成数值/容器公共表示及 9 个完整文件的 API 设计；API 行为映射继续进行。

## Current Objective

feature_list.json 共 15 项：7 项 done、1 项 in-progress、7 项 not-started。activeItem 和 nextItem 均为 migration-api-contract。scopeReview 保持 pending；P1 必须等待 P0 联合门禁。

## Recommended Next Step

继续复核 Hash、HMAC/DRBG、Random、AESGCM 等基础密码学文件，沿用 API-VALUES 的公共类型，逐项完成其余六模块接口、默认值、状态、异常、异步和宿主适配。已完成的源码分母可直接复用；不得自动生成 reviewed 或提前批量创建 Java 测试。

本轮证据位于 .cache/evidence/api-values*-observations.json、api-writer-zero-capacity-observation.json、api-value-mapping-check.json、api-current-check.log；此前完整 TS 基线在 .cache/evidence/ts-baseline-20260920-123124。只修改任务资料和独立源码探针，五个 Java 仓库及固定 TS 上游无本轮改动；根仓既有无关修改保留，未推送。
