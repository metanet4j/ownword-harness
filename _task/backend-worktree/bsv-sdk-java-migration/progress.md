# 当前进度

## 当前成果

用户已授权已完成 API 设计且依赖闭合的部分先编码，执行规则见 feature_list.json 的 implementationPolicy。完整模块范围和最终验收条件保持不变。

migration-impl-hex 已完成：目标工程提交 `0ecb8d1` 实现完整 Hex 两函数、Undefined 和 Error/TypeError 对应类型，完整复刻原 hex.test.ts 的 8 个用例、19 条断言。5 组真实行为 RED→GREEN；另外 3 个原用例由已有行为直接满足，全部保留。

提交后通过 `python3 run-hex-parity.py` 重新执行：TS 8/8，Java 对应 8/8，19 次实际输入、返回值、异常类型及消息一致，27 个 AST 位置完整映射。目标 Java 工程累计 9/9（包含基础测试 1），零失败/错误/跳过。证据：`.cache/evidence/hex-parity-20260920-150144-mgrmta7b/`；原始 Jest/Surefire 报告、两端采集、命令及源码/工具/Java 版本均在其中。

检查器自身 7/7 反例测试通过，覆盖漏采、重复、输入/结果/异常差异及报告篡改，不计 SDK 用例。运行方法和职责见[模块迁移计划](doc/模块迁移计划-20260920-103547.md)的“已就绪实施项：Hex”。

## 尚未完成

六模块仍为 primitives/compat/script/transaction/wallet/auth；冻结范围 292 文件、133 测试文件、5329 用例、7554 AST 位置。Java 原测试已映射 8/5329，其余 5321 未映射。Hex 仅是 primitives 内部实施项，尚无完整模块验收通过。

API 设计为 371/3576，剩余 3205；21 个设计批次中 values 完成，其余未开始。hash-random 不再占用当前事项。P0 通用输入重放/轨迹采集、API 总验收和联合门禁仍未完成，scopeReview 保持 pending。此前 TS 完整基线 5329/5329（含原规模 manual）仍有效，本轮只重跑受影响原文件，没有重复 37 分钟 AES manual。

WUA-ZERO-CAPACITY 的最小修复授权保留，尚未实现；后续只在旧容量为 0 时从 1 开始扩容，独立计数，不改变固定 TS 或冒充两端一致。其余已观察怪异行为仍按原样保留，契约详见 API 文档。

环境自检和 21 个 API 批次覆盖/状态检查通过；正式 audit-tests.py check 重扫 133 文件、5329 用例后按预期退出 1（缺失 5321、多余 0），证明 Hex 局部通过没有放宽全量门禁。日志为 `.cache/evidence/hex-init-final.log`、`hex-api-batches.log`、`hex-formal-gate.log`。

## 下一步

feature_list.json 共 38 项：9 done、0 in-progress、29 not-started；activeItem=null，nextItem=migration-impl-bignumber-constructor。从完整 BigNumber.constructor.test.ts 的 28 个原用例开始 TDD，推进构造、解析及所需编码；完整 BigNumber 其他行为与测试仍保留在后续范围。

工程改动仅限 metanet4j-bsv-sdk，其他四工程及固定 TS 只读。任务根目录维护对照工具、映射和状态；既有根仓无关修改保留，未推送。
