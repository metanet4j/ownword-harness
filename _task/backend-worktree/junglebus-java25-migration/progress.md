# 当前进展

## Current State

J00–J04 完成。JS 基线 77 项通过；Java ProtocolTest 7、RestTest 6、SubscriptionTest 8，合计 21 项均通过。双格式与三通道已可用。

## Next Steps

当前 J05：背压、容量、异步回调、断线恢复、取消与关闭竞态专项验证。

## Blockers and Risks

真实部署未验；getResumeFromBlock 保持原始高度，允许重放重复，不宣称 exactly-once。
