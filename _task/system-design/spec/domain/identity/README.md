# Identity 领域入口

- **技术 Review 依据**：[Identity 跨端设计评审报告](评审报告-Identity-v0.4.0-20261118-103500.md)记录前轮问题；其中自建初始化资格的方案已按 Yours Wallet 管理边界修订，以当前领域文档为准。历史验签、真实钱包集成和主网门禁尚未通过运行验证。
- **当前共享领域草案（v0.4.0 目标，needs-review）**：[Identity 领域设计](领域设计-Identity-v0.4.0-20261117-175100.md)。
- **唯一产品事实**：[核心认知](../../核心认知.md)集中 Identity 术语、功能编号、实体/属性、关系、业务状态、事件与规则索引；不从 TypeScript DTO 或 Java 表结构反推业务规则。
- **前端实现入口**：[Frontend / Identity](../../frontend/identity/README.md)。
- **后端实现入口**：[Backend / Identity](../../backend/identity/README.md)。
- **共享契约**：[Contracts](../../contracts/README.md)。
- **支撑边界**：[Frontend Wallet、Backend Transaction、Backend Chain Query](../supporting/README.md)。本人身份管理委托钱包，公共身份核验与业务验收由 OwnWord 组合完成。
- **历史草案**：[后端 Identity DDD 草案 v0.1.0](../../backend/领域设计-Identity-v0.1.0-20261117-165000.md)，保留供评审追溯；其中模型定义以核心认知为准，当前用例与端口以本目录入口为准，Java/Mongo 依据转到 Backend。

领域文件、API 合同及实现文件均待人工评审；本目录不是产品发布凭据。
