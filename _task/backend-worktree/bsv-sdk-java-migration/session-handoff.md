# 会话交接

## 状态

P0 的 migration-scope-review、migration-ts-baseline 已完成；migration-api-contract 是唯一进行中项，不能标记 done。15 项中 7 done、1 in-progress、7 not-started；activeItem/nextItem 均为 migration-api-contract，scopeReview 仍 pending。

六模块及范围依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。冻结测试范围未变：292 文件、133 测试文件、5329 用例、7554 AST 位置；TS 完整基线此前 5329/5329 通过，含原规模 manual，零跳过。本轮不改 TS 或 Java 源码，未重复完整基线和 Java 基础测试。

## Files

- api-catalog.json：133 个 API 源文件、3576 个声明、1016 个导出入口（模块内 750、根 mod.ts 266）；含私有/辅助成员、重载，不是公开方法数。
- audit-api.cjs：inventory 只解析源码；check 重新扫描固定源码后核对冻结清单与映射，拒绝同时删除清单/映射的漏项。默认必须覆盖全部六模块；没有 Java 实现/语义证明能力。
- api-map.json：9 个完整文件的 371 项声明完成设计映射，剩余 3205 项未映射；不要批量自动填 reviewed。完成文件为 hex、BigNumber、utils、ReaderUint8Array、WriterUint8Array、ReductionContext、MontgomoryMethod、Mersenne、K256。
- doc/完整模块与API映射-20260920-122800.md：API 数据格式、数值/容器共同约束、已复核文件契约、实际源码/探针和剩余设计工作。是 API 设计的当前入口。
- api-values-probe.mjs：可重复运行的固定 TS 小输入探针，26 组输入分别在 Buffer 存在/缺失进程中运行；原始值记录于 .cache/evidence/api-values*-observations.json，不运行 Java、不产生测试通过报告。
- .cache/evidence/api-*-red/green.log、api-check-host-*、api-current-check.log：工具 RED/GREEN 和实际未完成门禁证据。test-audit.test.cjs 当前 35 项工具自测。
- .cache/evidence/api-reader-observations.json、api-hex-observations.json、api-aes-observations.json：固定 TS 构建产物的小输入探针，不是上游新增用例或 Java 对照结果。
- module-scope.json、module-tests.json、test-map.json：范围、上游用例和后续 Java 测试映射；test-map 仍为空。
- run-ts-baseline.py、ts-offline-guard.cjs 和 .cache/evidence/ts-baseline-20260920-123124：此前完整 TS 基线工具与实际报告，具体限制见 TS 完整基线文档。

## 当前发现

CompletedProtoWallet 虽位于 __tests，实际由 auth/certificates/index.ts 公开导出，因此必须纳入 API 和最终 JAR；不能当普通测试辅助删除。其未实现操作的失败也是原行为，不能扩展成真实钱包调用。

已确定 number 用 double、bigint 用 BigInteger、Undefined/null/空洞分开表示，number[] 保留列表和元素，Uint8Array 用具有 backing/offset/length 的 ByteView。Reader 的 readUInt8/readInt8/readVarIntNum 可返回 Undefined，用 Object；读副本与共享视图、越界后的 NaN/零/游标分别保留。具体类型和省略参数重载规范见 API-VALUES。

用户明确授权 WUA-ZERO-CAPACITY：未来 Java ensureCapacity 仅将旧容量为 0 的扩容起点设为 1；固定 TS 保持原样，额外回归单列，不能计入 5329 个原测试或声称该输入与 TS 一致。完整决定及测试要求见 API-WRITER-ZERO-CAPACITY，api-map.approvedDifferences 保留授权引用；尚未创建 Java 修复/测试，不再重复询问授权。

旧 Writer 与 WriterUint8Array 的 -1 UInt64 编码、复制时机不同；Base64 解码接受非零 padding bits。BigNumber 的 nominal length、red 引用、strip 后失败的副作用不能省略。ReductionContext.sqrt 的确定根、verify1/2 不检查 this 的事实均已映射；K256.split/imulK 保留多余零词。MontgomoryMethod.imul 的零分支实际抛只读 length 的 TypeError，此项未授权修复，保留错误及失败前状态。详见 API 文档和 26 组探针。

原 Reader 的 `.not.toThrow('指定消息')` 不能改写成 assertDoesNotThrow；2^53 输入实际抛另一条精度错误。这一断言差异必须在后续逐用例映射中落实。

AESGCM 的注释声称 padding 不兼容，但本轮 12/32 字节 IV × 0/1/16/17 字节明文的 8 组实测密文/tag 与 Node 原生一致。只陈述这些样本，不推断全输入兼容。SymmetricKey 使用 32 字节 IV；nativeDecrypt 实际 catch 返回 null，不按注释推断总能回退。

其他可选后端、钱包选择优先级、BRC-100 字节身份和宿主事件边界详见 API 文档；这些文件尚未完成逐项 Java 类型映射。

## 验证与限制

工具自测 35/35 通过。沙箱中嵌套 Node spawnSync 曾返回 EPERM 且吞掉输出，后续工具自测和 API 清点在宿主运行。check 的初次 RED 因环境原因无效，已回到未实现版本，在宿主取得明确行为缺失的 RED 后恢复实现取得 GREEN；错误上游版本拒绝也有单独 RED/GREEN。

API check 当前必须退出 1，未映射 3205；正式 audit-tests.py check 仍应拒绝未映射的 5329 个 Java 用例。API 检查器尚未接入联合门禁，后续 migration-evidence-gate 处理，并精确登记授权差异。不要把清点、设计、探针、工具测试或 TS PASS 当成 Java 迁移通过。

此前完整普通基线在宿主运行 5328/5328，manual 保留 536870928 字节输入并通过，耗时 37:16.72、峰值 RSS 2000384 KiB。首次 manual 的网络记录边界见 TS 完整基线文档；以后实际采集和阶段验收仍要完整运行。无源码变化的会话切换不重复 37 分钟基线。

## Next Session

读取规则、状态和计划，执行 ./init.sh；保留 migration-api-contract 为唯一进行中项。下一步复核 Hash、HMAC/DRBG、Random、AESGCM 等基础密码学文件，沿用已确定的公共表示，按完整文件清单逐项登记接口与契约。全部 API 设计和复核结束后再进入逐用例映射、输入重放、真实采集和 P0 联合验收，不提前启动 P1。

工程实现只允许 metanet4j-bsv-sdk；本轮没有工程代码改动。目标仓 HEAD 仍为 72d2007，最近基础测试 1/1；其他四工程只读，固定 TS 上游保持干净。根仓无关修改保留，仅提交本任务资料与工具，未推送。
