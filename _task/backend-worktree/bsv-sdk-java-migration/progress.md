# 当前进度

## 当前成果

用户已授权已完成 API 设计且依赖闭合的部分先编码，执行规则见 feature_list.json 的 implementationPolicy。完整模块范围和最终门禁保持不变。

已完成两个内部项：Hex（目标仓提交 0ecb8d1）和 BigNumber 构造基础（9c22ba1）。本项完整复刻 BigNumber.constructor.test.ts 的 28 个原用例，保留 45 个静态断言的 52 次实际执行，以及 8 个非法字符串循环样本；12 组真实 RED→GREEN，其余 16 个原用例由此前行为直接满足。

提交后通过 `python3 run-hex-parity.py --bn-constructor` 重新执行：BigNumber 两端 28/28、52 次断言和 92 次 API 调用轨迹的实际输入/返回/异常及断言实参均一致。累计 Hex 后，原用例 36/36、71 次断言结果、101 个 AST 位置全部核对通过。目标 Java 工程累计 37/37（含基础测试 1），零失败/错误/跳过。

最新证据：`.cache/evidence/hex-parity-20260920-153441-zd037qhq/`。manifest 绑定源码、工具、Java 提交/工作树、原始报告哈希和命令；Jest JSON、全部 Surefire XML、两端实际记录及比较结果已独立保存。旧批次在 Java 版本变化后不用于当前验收，不改写旧证据版本。

采集比较工具自测 14/14，通过真实证据和漏采循环样本、重复、调用缺失、输入位变化、断言值/异常消息变化、报告篡改等反例，不计 SDK 用例。具体步骤见[模块迁移计划](doc/模块迁移计划-20260920-103547.md)的 Hex/BigNumber 实施入口。

## 尚未完成

六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 用例、7554 AST 位置。Java 原用例已映射 36/5329，剩余 5293。BigNumber 仅完成原构造测试涉及的基础实现，完整 API、参数分支及其他原测试尚未完成；暂无整类/完整模块验收通过。

API 设计仍为 371/3576，剩余 3205；21 个设计批次只有 values 完成。P0 通用输入重放、随机/属性轨迹采集、API 总验收和联合门禁仍未完成，scopeReview 保持 pending。此前 TS 完整基线为 5329/5329（含原规模 manual），本轮只累计重跑两个已实现原文件，没有重复 37 分钟 AES manual。

WUA-ZERO-CAPACITY 的最小修复授权保留，尚未实现；后续仅在旧容量 0 时从 1 开始扩容，额外回归单列，不改变 TS 或冒充一致。其他契约和已知特殊行为见 API 文档。

收尾环境自检和 API 批次覆盖/状态检查通过。正式 audit-tests.py check 重扫完整冻结清单后按预期退出 1：缺失 5293 个 Java 映射，多余 0。证据为 `.cache/evidence/bn-init-final.log`、`bn-api-batches-final.log`、`bn-formal-gate-final.log`。

## 下一步

feature_list.json 共 39 项：10 done、0 in-progress、29 not-started；activeItem=null，nextItem=migration-impl-bignumber-serializers。继续完整 BigNumber.serializers.test.ts 的 16 个原用例，补齐所需构造/转换分支、协议编码和 Utils 编解码，并累计回归当前 36 个原用例。

工程代码/测试/POM 只修改 metanet4j-bsv-sdk；Jackson 仅测试采集依赖，沿用父工程管理，未改其他工程。任务根目录维护工具、映射和状态；固定 TS 只读，根仓既有无关修改保留，未推送。
