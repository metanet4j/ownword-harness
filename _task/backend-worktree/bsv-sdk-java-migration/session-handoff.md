# 会话交接

## 状态

P0 的 migration-scope-review、migration-ts-baseline 已完成；migration-api-contract 是唯一进行中项，不能标记 done。15 项中 7 done、1 in-progress、7 not-started；activeItem/nextItem 均为 migration-api-contract，scopeReview 仍 pending。

六模块及范围依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)。冻结测试范围未变：292 文件、133 测试文件、5329 用例、7554 AST 位置；TS 完整基线此前 5329/5329 通过，含原规模 manual，零跳过。本轮不改 TS 或 Java 源码，未重复完整基线和 Java 基础测试。

## Files

- api-catalog.json：133 个 API 源文件、3576 个声明、1016 个导出入口（模块内 750、根 mod.ts 266）；含私有/辅助成员、重载，不是公开方法数。
- audit-api.cjs：inventory 只解析源码；check 重新扫描固定源码后核对冻结清单与映射，拒绝同时删除清单/映射的漏项。默认必须覆盖全部六模块；没有 Java 实现/语义证明能力。
- api-map.json：仅 hex 的 3 项声明完成设计映射，剩余 3573 项未映射；不要批量自动填 reviewed。
- doc/完整模块与API映射-20260920-122800.md：API 数据格式、已确定约束、hex 契约、实际源码/探针发现和剩余设计工作。是 API 设计的当前入口。
- .cache/evidence/api-*-red/green.log、api-check-host-*、api-current-check.log：工具 RED/GREEN 和实际未完成门禁证据。test-audit.test.cjs 当前 35 项工具自测。
- .cache/evidence/api-reader-observations.json、api-hex-observations.json、api-aes-observations.json：固定 TS 构建产物的小输入探针，不是上游新增用例或 Java 对照结果。
- module-scope.json、module-tests.json、test-map.json：范围、上游用例和后续 Java 测试映射；test-map 仍为空。
- run-ts-baseline.py、ts-offline-guard.cjs 和 .cache/evidence/ts-baseline-20260920-123124：此前完整 TS 基线工具与实际报告，具体限制见 TS 完整基线文档。

## 当前发现

CompletedProtoWallet 虽位于 __tests，实际由 auth/certificates/index.ts 公开导出，因此必须纳入 API 和最终 JAR；不能当普通测试辅助删除。其未实现操作的失败也是原行为，不能扩展成真实钱包调用。

Reader 的 TS number 声明不保证运行结果为数值：空 readUInt8 返回 undefined；空 readUInt32BE 返回 NaN；默认 read() 的长度为总长而非剩余长度，可产生 pos 超界、remaining 为负。readView 与 read 的别名/复制语义不同。Java 返回类型和底层字节视图需要先解决。

AESGCM 的注释声称 padding 不兼容，但本轮 12/32 字节 IV × 0/1/16/17 字节明文的 8 组实测密文/tag 与 Node 原生一致。只陈述这些样本，不推断全输入兼容。SymmetricKey 使用 32 字节 IV；nativeDecrypt 实际 catch 返回 null，不按注释推断总能回退。

其他已核实的默认值、BigNumber 状态、可选后端、钱包选择优先级、BRC-100 字节身份和宿主事件边界详见 API 文档；尚未完成逐项 Java 类型映射。

## 验证与限制

工具自测 35/35 通过。沙箱中嵌套 Node spawnSync 曾返回 EPERM 且吞掉输出，后续工具自测和 API 清点在宿主运行。check 的初次 RED 因环境原因无效，已回到未实现版本，在宿主取得明确行为缺失的 RED 后恢复实现取得 GREEN；错误上游版本拒绝也有单独 RED/GREEN。

API check 当前必须退出 1，未映射 3573；正式 audit-tests.py check 仍应拒绝未映射的 5329 个 Java 用例。API 检查器尚未接入联合门禁，后续 migration-evidence-gate 处理。不要把清点、设计、探针、工具测试或 TS PASS 当成 Java 迁移通过。

此前完整普通基线在宿主运行 5328/5328，manual 保留 536870928 字节输入并通过，耗时 37:16.72、峰值 RSS 2000384 KiB。首次 manual 的网络记录边界见 TS 完整基线文档；以后实际采集和阶段验收仍要完整运行。无源码变化的会话切换不重复 37 分钟基线。

## Next Session

读取规则、状态和计划，执行 ./init.sh；保留 migration-api-contract 为唯一进行中项。下一步解决 primitives 的数值/undefined、字节视图及内部状态类型，然后按完整文件清单逐项登记 Java 接口与契约。全部 API 设计和复核结束后再进入逐用例映射、输入重放、真实采集和 P0 联合验收，不提前启动 P1。

工程实现只允许 metanet4j-bsv-sdk；本轮没有工程代码改动。目标仓 HEAD 仍为 72d2007，最近基础测试 1/1；其他四工程只读，固定 TS 上游保持干净。根仓无关修改保留，仅提交本任务资料与工具，未推送。
