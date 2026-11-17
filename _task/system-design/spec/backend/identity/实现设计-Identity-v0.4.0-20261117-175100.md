# Backend / Identity 实现设计（OwnWord v0.4.0 目标）

> **状态：needs-review。** 对应[Identity 跨端领域设计](../../domain/identity/README.md)。本文件从已核实 Java 实现及[原后端 DDD 草案](../领域设计-Identity-v0.1.0-20261117-165000.md)提取后端职责，不以本次文档整理宣称 Java 重构已经完成。

## 1. 代码基线与职责

仓库：[metanet4j/metanet4j-component](https://github.com/metanet4j/metanet4j-component/tree/dev)，核实 `dev` HEAD 为 `fbb048eab9ff565ea2f4aff1bd01720b9240d407`；其 Maven `0.2.0` 是组件构建版本，不随 OwnWord v0.4.0 目标自动修改。

现有模块 `metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/`：

| 类 | 已观察到的职责 | 后续领域分层建议 |
| --- | --- | --- |
| `IdentityApi` | `GET /api/v1/identities/{bapId}`、操作查询、来源与 Mongo 投影 | HTTP/Query Adapter；公共 IdentityResolution 不由 Controller 发明 |
| `TransactionSyncApi` | 原交易四字段校验、TxID、协议分派、幂等与同步 | TransactionSync Application + Adapter；交易协议规则通过 Verifier Port |
| `IdentityProtocol` | BAP 声明与签名解析/校验 | IdentitySignatureVerifier / BapProtocol Adapter |
| `AvatarProtocol` | 图片交易解析 | Profile 图片证据及缓存适配 |
| `ContentApi / PostProtocol` | 公开 Post/Revision 读写验证 | Content Context，复用通用交易同步与身份签名归属 |
| Mongo 集合与源模式 | 操作日志、原交易、身份与图片投影；simulated/live 隔离 | Projection Repositories + Blockchain Observation Ports |

本节是**只读代码审阅**，尚未检查当前全部运行服务与真实网络表现；不要假设新建的 Java Domain 包已经存在。

## 2. 后端领域应用服务

| Use Case / Port | 后端行为 | 核心不变量 |
| --- | --- | --- |
| `ResolvePublicIdentity` | 公共 BAP 来源 + 链上观测 + 覆盖，派生 published/not-published/unknown | 覆盖不足不能声称不存在 |
| `SyncSignedTransaction` | 校验原交易、重新计算 TxID、精确幂等、逐笔身份签名与 BAP 归属 | 前端传入 `bapId` 只是期望值，不是作者证据 |
| `BuildIdentityProjection` | 从已验证 ID/ALIAS/图片与密钥历史派生当前 Identity/Profile | 本地存储不是公共链真相 |
| `VerifyKeyRotation` | 依据签名发生时有效路径核验并保留历史 | BAP ID 稳定，不能只按当前地址判旧交易 |
| `ResolveCurrentBinding` | 通过 Artifact 公开证据查询 Current Binding | Identity 不维护第二套 Binding 写模型 |
| `ReplayObservedTransactions` | 幂等重放 rawTx 与可靠观测，修正投影 | 支持历史回放、重组与升级 |

设计建议是将端口和领域策略逐步从现有 Controller 拆出，保持已通过的测试、运行约束和外部 API 兼容；并不要求一次性更换模块、Mongo 或 Spring 配置。

## 3. Java 层边界

~~~text
HTTP Controller / Request Mapping
    ↓
Application Use Case（事务编排、幂等、恢复）
    ↓
Domain（BapIdentity、身份归属、不可变规则、事件）
    ↑
Ports ← Infrastructure (BAP/Bitcoin Verifier, Mongo, Indexer)
~~~

建议端口：`IdentityProjectionRepository`、`IdentitySignatureVerifier`、`PublicBapResolver`、`BlockchainObservationPort`、`TransactionSyncRepository`、`BindingQueryPort`。

`BapId / TransactionId / IdentitySignatureProof / ChainObservation` 采用不可混淆的值对象；格式检查不等于验证签名、所有权或公共存在性。私钥、Seed Phrase、WIF 永不进入后端。

## 4. HTTP 合同与原交易处理

现有 `POST /api/v1/transactions/sync` 请求体必须**恰有** `operationId`（UUID）、`bapId`、`txid`（小写 64 位 hex）、`rawTx`（完整交易 hex），Header `Idempotency-Key` 与 TxID 一致。重复同步同一交易是幂等；同 operationId 换 TxID 或同 TxID 换 rawTx/BAP 返回冲突。

建议明确执行顺序：

~~~text
Validate request
→ Parse rawTx and recompute TxID
→ Check operationId/txid idempotency
→ Decode exactly one expected protocol branch
→ Verify identity signature and signed coverage
→ Verify signing-time BAP key history
→ Verify network/source/coverage
→ Persist raw evidence / observation
→ Rebuild Identity/Profile projection
→ Return source-aware result
~~~

实际代码中部分验证与网络观测尚有 `unverified/sync-pending` 分支：不能把“已收到同步请求”误写成“公共 BAP 已发布”。协议不符不得尝试猜测另一种数据格式来降级通过。

**原有接口兼容**：`GET /api/v1/identities/{bapId}`、`GET /api/v1/transactions/{txid}`、`GET /api/v1/operations/{id}` 等由现有 Controller 提供。目标 Contract 草案见 [OpenAPI](../../contracts/openapi/ownword.yaml)，但真实返回字段、错误 code 必须以实际 Java/测试向量逐项确定后才能冻结。

## 5. 数据模型与一致性

Mongo 在此阶段承担已同步原交易、日志与可重建读投影；仓储/集合现状以真实代码为准，后续抽取 Repository 时不得自行改写语义。

| 逻辑数据 | 唯一性/定位原则 | 说明 |
| --- | --- | --- |
| 同步操作 | operationId 与 txid 的幂等关系 | 防止重复同步与不同交易覆盖 |
| BAP 身份投影 | BapId + 已核实来源/环境范围 | Profile 是由有效链上声明派生 |
| 交易及身份签名证据 | network/scope/txid/输出 | 验证器版本、来源和观测时点要可追溯 |
| 身份签名路径历史 | BapId + 可验证轮换记录 | 不能仅缓存当前 signer |
| Current Binding 查询 | Artifact 公开关联和 Origin | 不在 Identity 再保存第二份当前关系 |

对现有 Mongo 实际键、部分唯一索引、scope 实现有任何修改前先写迁移与回放测试；本表是**目标逻辑约束**而不是声明已经部署了同名集合或复合键。

## 6. 验收与恢复

- 本地无 Identity 投影时查询公共来源；覆盖不足返回 UNKNOWN，不以 404/超时当不存在。
- 原始交易可重放、幂等，不重复生成资料和内容投影。
- 缺身份签名、签名覆盖被篡改或 BAP 归属不匹配，不得产生 verified 作者身份。
- Rotation 后旧交易按历史密钥继续得到相同 BAP ID。
- 模拟广播、隔离 Mongo、真实主网分别有来源标记；不能把隔离模拟的成功当作生产发布。
- 断网、索引失败和 reorg 只改变证据可信度/投影，不能擦除原始事件。
- Binding 的双向唯一、转移后失效、公开验证协议待实际 Indexer 和 Wallet Adapter 完成，不依据本地布尔标志直接生效。

验收来源：[Identity 领域 BDD](../../contracts/acceptance/identity.feature)、[v0.1 集成设计](../../frontend/设计文档v0.1.0-真实集成-20261013-183000.md)、[v0.2 验收报告](../../../../../知识库/前端/ownword-v0.2.0/README.md)。

## 7. 实施次序与未关闭项目

1. 对照现有 `IdentityApi / TransactionSyncApi / IdentityProtocol` 与已批准 HTTP 设计，补接口样例和验证覆盖证据。
2. 把领域策略与传输层分离，先抽 `IdentitySignatureVerifier`、`PublicBapResolver` 和投影查询接口，不破坏 API。
3. 补 Key Rotation 历史回放、原交易保存/重建和 Indexer 覆盖失败用例。
4. 在 Artifact 的公开 Binding 与编号契约经过实测后接入只读 `BindingQueryPort`。
5. 真实钱包扩展、公共历史和主网资金/广播门禁单独验收，不用模拟或本地测试结果代替。

**待确认**：Binding 公开协议、Ordinals 编号 API、普通 Transfer 身份签名、签名历史验证、公共 BAP 覆盖度、现有部署运行态。详细清单见[核心认知 §12](../../核心认知.md#12-待确认)。
