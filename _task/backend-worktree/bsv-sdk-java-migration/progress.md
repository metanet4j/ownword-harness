# 当前进度

## Current State

P0 完整模块范围复核与 TS 完整基线已完成。API 设计拆为 21 批：migration-api-values 已完成设计，migration-api-hash-random 为唯一进行中项，其余 19 批未开始；migration-api-contract 等待全部批次完成后总验收。六模块仍为 primitives/compat/script/transaction/wallet/auth；冻结测试范围保持 292 文件、133 测试文件、5329 注册用例及 7554 AST 位置。

API 清点已建立：133 个 API 源文件、3576 个声明、1016 个导出入口，包含根入口及公开导出的 CompletedProtoWallet。详情和行为设计统一见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。api-map.json 已复核 9 个完整文件的 371 项设计映射，其余 3205 项未映射；API check 应失败，不能进入 P1。

已确定 number/BigInteger、Undefined/null、列表/空洞和 ByteView 的表示，以及 BigNumber/模运算的状态、编码、身份和错误契约。api-values-probe.mjs 此前在 Buffer 有/无两种环境各运行 26 组输入；这些观察不代表全输入或 Java 等价。

本轮完成分批清单与门禁：node audit-api.cjs batches 核对 21 批恰好覆盖全部 133 个 API 文件/3576 项声明，含零声明导出文件。工具自测 39/39 通过，含漏文件、重复归属、伪造 done、未知依赖/循环、缺少证据与状态不一致反例。实际单批检查 values 通过，hash-random 拒绝未映射的 292 项；全量 check 仍拒绝 3205 项。单批检查和分批覆盖通过不代替完整 API 或 SDK 验收。

用户已授权 WUA-ZERO-CAPACITY：Java 零容量首次扩容从 1 开始，单列差异与额外回归，不改固定 TS；授权、最小范围和验证要求见 API 文档对应章节。当前仅完成设计，尚未实施修复。其他源码异常按原行为保留，不扩大本次授权。

[完整 TS 基线](doc/TS完整基线-20260920-124400.md)此前已实际 5329/5329 通过，含原规模 manual；本轮源码未变，没有重复耗时 37 分钟的 manual。目标 Java 工程基础测试最近一次 1/1 通过，本轮没有 Java 代码变更。Java 测试映射仍为 0，生产移植、输入重放和逐断言结果采集尚未完成。

## Last Updated

2026-09-20，按完整文件拆分 API 设计批次并验证覆盖、状态和依赖门禁。

## Current Objective

feature_list.json 共 36 项：8 项 done、1 项 in-progress、27 项 not-started。activeItem 和 nextItem 均为 migration-api-hash-random。scopeReview 保持 pending；P1 必须等待 P0 联合门禁。原 API 总项保留为 gate，不与当前批次同时进行。

## Recommended Next Step

按 feature_list.apiBatchPolicy 推进 migration-api-hash-random：完整复核 Hash（含 HMAC/PBKDF2）、DRBG、Random 三个文件的 292 项声明及相关原测试，沿用 API-VALUES 的公共类型。完成后执行 batches --batch migration-api-hash-random 并单独提交，再按依赖选择下一批；不得自动生成 reviewed 或提前批量创建 Java 测试。

本轮证据位于 .cache/evidence/api-batches-*、api-batch-status-*、api-batch-dependencies-*、api-batch-values-current.log、api-batch-hash-current.log、api-current-check.log；此前完整 TS 基线在 .cache/evidence/ts-baseline-20260920-123124。只修改任务计划、状态和检查器，五个 Java 仓库及固定 TS 上游无本轮改动；根仓既有无关修改保留，未推送。
