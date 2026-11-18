# OwnWord OpenAPI

- [ownword.yaml](ownword.yaml)：**v0.4.0 产品设计目标下的待评审契约草案**，现覆盖五条已有 Java 路由（身份查询、交易同步、交易查询、操作查询和历史兼容操作查询）。
- 核对来源：[IdentityApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java)、[TransactionSyncApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/TransactionSyncApi.java)。
- 对照前端：[ownword-web/lib/domain/types.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts)、[publish.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/publish.ts)。

已为六种 `IdentityResolutionDto.kind`、`Coverage`、`ProfileDto`、`ErrorEnvelope`、`OperationReceipt` 建立类型候选；**部分现有 Java 投影仍允许附加字段**，因为真实响应 fixture 尚未逐一核验。`TransactionEnvelope` 暂用 `anyOf` 兼容存储回执与链上观测，等 Java 样例确定后再细化分流。初始化资格 `AssessIdentityInitialization` 还没有经确认的 HTTP 路径，不能虚构端点。需要完成 OpenAPI 严格校验和 Java/TypeScript 契约测试后才能发布稳定客户端 SDK。

产品版本的统一不改变已有 `/api/v1` HTTP 主版本路径，后续破坏性变更需单独兼容性评审。
