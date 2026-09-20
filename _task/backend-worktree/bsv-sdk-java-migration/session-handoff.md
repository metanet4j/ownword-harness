# 会话交接

## 执行入口

用户已明确要求先编码已完成设计且能够进行的部分。不要再以全量 P0/API 设计尚未完成阻止这些内部实施项开工；同时保留六个完整模块、5329 个原用例及最终联合门禁。授权与范围唯一入口：feature_list.json 的 implementationPolicy/scope。

读取沿途规则和任务计划，执行 `./init.sh`，核对各仓状态。当前无进行中项，唯一下一步为 migration-impl-bignumber-constructor：先审查 BigNumber.constructor.test.ts 全部 28 用例，从构造与解析按单行为 TDD 实施，补齐实际采集与对照。不要为后续行为批量生成占位 API；内部步骤不缩小完整 BigNumber 范围。

## 已完成并可复验

目标 Java 提交 `0ecb8d1`：Hex 完整实现，8 个原用例/19 断言，Undefined 和错误类型支撑。5 组真实 RED→GREEN；3 个原用例依赖已实现行为直接通过。上游许可随 META-INF 资源保留。

`python3 run-hex-parity.py` 会执行原始 TS Hex 测试与目标工程全部 clean test，再逐条比较实际输入/返回/异常。最新提交后证据 `.cache/evidence/hex-parity-20260920-150144-mgrmta7b/`：TS 8/8、Java 原测试 8/8、19/19 比较、27 AST 位置，目标工程总计 9/9（基础测试另计）。工具自身 `python3 test-hex-parity.py <批次目录> -v` 为 7/7，不算 SDK 用例。

`--verify <批次目录>` 只接受相同源码/映射/工具/Java 提交及工作树摘要。版本变化就重新采集，不改旧报告版本。局部临时 catalog/mapping 只供 compare；formalAcceptance=false。正式 audit-tests.py check 仍重扫全六模块，应拒绝剩余 5321 个 Java 映射，不得用局部片段冒充正式冻结清单。

收尾已执行 ./init.sh、audit-api.cjs batches，均通过；正式 audit-tests.py check 重扫完整冻结清单后按预期拒绝缺失的 5321 个 Java 映射（多余 0）。证据分别为 .cache/evidence/hex-init-final.log、hex-api-batches.log、hex-formal-gate.log。

## 设计与剩余工作

API 设计 21 批仅 values 完成，9 个完整文件共 371 项设计，其余 3205/3576 未完成。values 包含 hex、utils、ReaderUint8Array、WriterUint8Array、BigNumber、ReductionContext、MontgomoryMethod、Mersenne、K256；“设计完成”不表示已实现。完整契约入口为 doc/完整模块与API映射-20260920-122800.md；分批入口 `node audit-api.cjs batches` 和 `--batch migration-api-values`，正式 API check 不允许按批过滤。

BigNumber/模运算实现须保留 nominal length、red 对象身份及失败前副作用；TS number 用 double，bigint 用 BigInteger。Undefined 与 null、列表空洞分别表示，ByteView 保留 backing/offset/length。MontgomoryMethod.imul 零值分支原 TypeError 未授权修复；Reader 的 not.toThrow('指定消息') 不等同 assertDoesNotThrow。已确定细节均在 API 契约，继续按源码和原测试核对。

用户已授权 WUA-ZERO-CAPACITY：未来 Java WriterUint8Array 仅在旧容量 0 时把扩容起点设为 1；其他容量仍按原方式。单列额外回归，不计 5329 原用例，也不声称该输入和 TS 一致。尚未实施，不再询问同一授权。

P0 的通用输入重放、随机/属性测试轨迹采集、全量映射和联合门禁尚未完成。此前完整 TS 基线 `.cache/evidence/ts-baseline-20260920-123124/` 为 5329/5329，manual 保留 536870928 字节，耗时 37:16.72；无相关源码变化时不为会话切换重跑，但完整阶段最终采集/验收仍须覆盖。

## 边界与工具

只允许修改 metanet4j-bsv-sdk 的工程代码/测试/POM/配置；其他四工程只读，TS 固定 f999e0c1aad9a7afd0cbadaaf23841d049af9d5a。Maven/pnpm 仅经任务包装脚本。Node 嵌套 spawnSync 清点自测在沙箱有 EPERM 记录，应宿主执行；Maven 单元测试不需跨工程构建。

feature_list 38 项，9 done、0 in-progress、29 not-started。API 检查器原有 39 项自测已通过，本次未修改旧检查器。根仓无关修改保留；仅提交任务资料和目标 Java 仓，不推送、不接入其他工程。
