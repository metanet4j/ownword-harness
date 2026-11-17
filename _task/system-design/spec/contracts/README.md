# 跨端契约（Contracts）

本目录保存前后端对接、可自动检查的契约资产。**产品领域事实由[核心认知](../核心认知.md)定义**；契约给出 API/数据/错误/验收的具体接口形状，不独立定义另一套领域规则。

| 目录 | 当前入口 | 状态 |
| --- | --- | --- |
| OpenAPI | [ownword.yaml](openapi/ownword.yaml) | **needs-review**：当前只列出经 Java 源码核实的 Identity 查询与 TransactionSync 子集；不是整个 v0.4.0 API 的完整定义 |
| Acceptance | [BDD 入口](acceptance/README.md) | **needs-review**：派生自已有 PRD 的最小跨端行为场景，尚未接入执行框架 |

开发规则：

1. Use Case 与业务结果以 [Domain](../domain/README.md) 为准；API 请求响应以确认后的 OpenAPI 为准；生成的 DTO 必须映射为各端领域结果模型。
2. 对 API 新增字段、错误、状态变化先检查现有前端 `lib/domain/types.ts`、Java `IdentityApi.java / TransactionSyncApi.java` 和相关测试样本，不按猜测填入正式 Schema。
3. `identitySignature=valid`、`networkAccepted`、`indexCoverage` 必须保留各自证据语义，不能合并为成功布尔值。
4. 用户授权、签名、广播、同步、公共链上可发现性是不同阶段；测试和合同不把模拟成功当成主网事实。
5. Artifact Binding 的公开链上协议、签名封装与数字 ID 解析端点，在[核心认知 §12](../核心认知.md#12-待确认)关闭之前不创建虚构的生产 API。

更多约束见 [Identity 领域设计](../domain/identity/README.md)与[统一版本基线](../versions/v0.4.0.yaml)。
