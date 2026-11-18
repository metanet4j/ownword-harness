# OwnWord OpenAPI

- [ownword.yaml](ownword.yaml)：**v0.4.0 产品设计目标下的待评审契约草案**，现覆盖五条已有 Java 路由（身份查询、交易同步、交易查询、操作查询和历史兼容操作查询）。
- 核对来源：[IdentityApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java)、[TransactionSyncApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/TransactionSyncApi.java)。
- 对照前端：[ownword-web/lib/domain/types.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts)、[publish.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/publish.ts)。

已为六种 `IdentityResolutionDto.kind`、`Coverage`、`ProfileDto`、`ErrorEnvelope`、`OperationReceipt` 建立类型候选；部分现有 Java 投影仍允许附加字段，真实响应 fixture 尚未逐一核验。`TransactionEnvelope` 暂用 `anyOf` 兼容存储回执与有限链上观测，不代表完整交易/Ordinal 查询已实现。本人身份操作委托 Wallet/SDK，不新增 OwnWord 初始化许可 API；[支撑域](../../domain/supporting/README.md)的逻辑端口也不直接生成 HTTP 路径。严格 OpenAPI 验证及 Java/TypeScript 契约测试完成后才能发布稳定客户端 SDK。

产品版本的统一不改变已有 `/api/v1` HTTP 主版本路径，后续破坏性变更需单独兼容性评审。
