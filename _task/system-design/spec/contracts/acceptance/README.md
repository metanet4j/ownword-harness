# 跨端验收（Acceptance）

BDD 文件是将已批准 PRD 行为转换为可执行验收的**派生资产**；**PRD 和[核心认知](../../核心认知.md)仍是规则权威**。

- [identity.feature](identity.feature)：18 个 Identity 设计级场景（另含 Scenario Outline 的 8 行映射样例），覆盖首次初始化资格、DTO 映射、Profile、密钥轮换、同步与恢复，**needs-review、尚未接入自动测试运行器**。
- [artifact.feature](artifact.feature)：编号待确认与 Current Binding 的产品行为草案，**不代表公开 Binding 协议已经落地**。
- 需求来源：[Identity v0.1.0 PRD](../../prd/v0.1/设计文档v0.1.md)、[Artifact v0.3.0 PRD](../../prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)和[Identity 领域设计](../../domain/identity/README.md)。

测试职责：前端验证操作流程、会话切换、持久化恢复与交互；后端验证原交易、协议、BAP 签名/历史归属、查询覆盖、投影和幂等；跨端集成验证同一 BAP ID/TxID/Proof 与错误语义。模拟钱包测试、真实浏览器钱包扩展与主网分别记录结果，禁止混写为“全部通过”。

待补的 Step Definition 和测试执行配置由实施任务完成；`@requires-indexer`、`@requires-mainnet` 等标签表示外部证据门禁，不表示测试已通过。现有 Gherkin 文件属于设计级验收草案。
