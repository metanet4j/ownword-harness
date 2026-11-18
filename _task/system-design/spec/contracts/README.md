# 跨端契约（Contracts）

本目录保存前后端对接、可自动检查的契约资产。**产品领域事实由[核心认知](../核心认知.md)定义**；契约给出 API/数据/错误/验收的具体接口形状，不独立定义另一套领域规则。

| 目录 | 当前入口 | 状态 |
| --- | --- | --- |
| OpenAPI | [ownword.yaml](openapi/ownword.yaml) | **needs-review**：当前包含 Identity 查询、TransactionSync、交易与操作恢复的五条已核实 Java 路由；类型与错误 Schema 为候选，仍需响应 fixture 验证 |
| Acceptance | [BDD 入口](acceptance/README.md) | **needs-review**：Identity 18 个场景（Outline 含 8 行映射）、支撑域 16 个、Artifact 2 个；均尚未接入执行框架 |
| Upstream | [Yours 与 1sat 接入依据](upstream/接入依据-Yours与1sat-20261118-164032.md) | **needs-review**：外部接口、鉴权与固定版本源码证据；不等同于 OwnWord 已批准 HTTP 契约 |

开发规则：

1. 业务结果以[核心认知](../核心认知.md)为准，用例协作见 [Domain](../domain/README.md)；API 请求响应以确认后的 OpenAPI 为准；生成的 DTO 必须映射为各端领域结果模型。
2. 对 API 新增字段、错误、状态变化先检查现有前端 `lib/domain/types.ts`、Java `IdentityApi.java / TransactionSyncApi.java` 和相关测试样本，不按猜测填入正式 Schema。
3. `identitySignature=valid`、`networkAccepted`、`indexCoverage` 必须保留各自证据语义，不能合并为成功布尔值。
4. 用户授权、签名、广播、同步、公共链上可发现性是不同阶段；测试和合同不把模拟成功当成主网事实。
5. 本人身份动作与授权委托 Wallet/SDK；公共 `IdentityResolution=unknown` 不单独否决钱包已有动作。已知冲突、钱包能力不明和原执行未决先恢复；不新增 OwnWord Root 控制型初始化许可 API。
6. Artifact Binding 的公开链上协议、签名封装与数字 ID 解析端点，在[核心认知 §12](../核心认知.md#12-待确认)关闭之前不创建虚构的生产 API。

业务约束统一引用[核心认知](../核心认知.md)；用例与责任映射见 [Identity 领域设计](../domain/identity/README.md)、[支撑域设计](../domain/supporting/README.md)，目标状态见[统一版本基线](../versions/v0.4.0.yaml)。链/Ordinal 逻辑端口需经实际 fixtures 确认后再定义 HTTP 契约。
