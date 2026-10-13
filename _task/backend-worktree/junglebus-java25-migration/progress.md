# 当前进展

## Current State

J00–J05 完成。JS 基线 77 项通过；Java ProtocolTest 7、RestTest 6、SubscriptionTest 8、LifecycleTest 16，合计 37 项全部通过。

## Next Steps

当前 J06：使用用户提供的订阅 ID，从 720000 开始接收真实交易，合计输出 100 条后停止；完成示例、文档和三类 JAR 打包。

## Blockers and Risks

真实部署验证进行中。getResumeFromBlock 保持原始高度，允许重放重复，不宣称 exactly-once。
