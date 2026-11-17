# OwnWord OpenAPI

- [ownword.yaml](ownword.yaml)：**v0.4.0 产品设计目标下的待评审契约草案**，目前仅覆盖两条已经核实 Java 处理器的接口。
- 核对来源：[IdentityApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java)、[TransactionSyncApi.java](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/TransactionSyncApi.java)。
- 对照前端：[ownword-web/lib/domain/types.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts)、[publish.ts](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/publish.ts)。

目前 `Envelope.data` 仍采用宽松 Schema：字段完整性、错误代码、当前索引覆盖与 API 行为须通过运行样例/契约测试进一步核实。不要把这份子集当作全部 v0.4.0 API，也不能据此生成宣称稳定的生产 SDK。

产品版本的统一不改变已有 `/api/v1` HTTP 主版本路径，后续破坏性变更需单独兼容性评审。
