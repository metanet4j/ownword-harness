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
| `QueryTransaction / OrdinalEvidence` | 通过链与 Ordinal 查询支撑读取原交易、Proof、主链、输出及花费证据 | 钱包资产列表不是公共历史；字段缺失保持未知 |
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

建议端口：`IdentityProjectionRepository`、`IdentitySignatureVerifier`、`PublicBapResolver`、`PublicBapHistoryResolver`、`BlockchainObservationPort`、`RotationHistoryResolver`、`SigningPathAt`、`TransactionSyncRepository`、`BindingQueryPort`。端口是**目标架构**，不表示已存在同名 Java 接口。

`BapId / TransactionId / IdentitySignatureProof / ChainObservation` 采用不可混淆的值对象；格式检查不等于验证签名、所有权或公共存在性。私钥、Seed Phrase、WIF 永不进入后端。

### 3.1 钱包操作与公共查询的边界

本人身份发布、Profile 和 Rotation 执行由 Yours Wallet/SDK 管理。后端不新增 Root 控制型初始化许可接口，也不决定钱包内部授权。`GET /api/v1/identities/{bapId}` 继续只返回公共事实；unknown 不单独否决钱包已有动作，404/无投影也不能转换为公共未发布。

公共已核实身份与钱包记录不一致时，应用先恢复/匹配原身份；未决执行按原引用和 TxID 恢复，不能重复初始化。后端负责保留可查询的同步记录与链证据，前端负责钱包执行关联。

**当前缺口**：本地 `IdentityApi` 无投影时，对 BAP 上游使用 `BodyHandlers.discarding()`，随后返回 unknown；`TransactionSyncApi` 写入 chain_events，本模块未发现生成 identity_projection 的写入管线。应接通公共响应解析、原事件重放和身份/资料投影，再用真实 fixtures 验收。不能把同步 receipt 当公共身份投影。

交易执行与查询的完整分工见[支撑域](../../domain/supporting/README.md)。逻辑端口不代表已部署同名 Java 接口或 HTTP 路由。

### 3.2 Identity 与 Profile 的类型/字段边界（R-03）

| 领域字段 | Java 当前输入/输出 | 映射 |
| --- | --- | --- |
| `BapProfile.name` | `name` | 同名，按核心认知长度验证 |
| `BapProfile.description` | `bio`，BAP ALIAS 原交易 `description` | 有效声明 → DTO `bio`；写入时相反 |
| `BapProfile.image` | `imageUrl`，BAP ALIAS 原交易 `image` | 保留原交易 URI 和图片资产证据 |
| `BapProfile.type` | `Person/Organization` | 可变展示资料，不能自动等于 Identity.type |
| `BapIdentity.type` | Java API 当前无明确独立 DTO | 身份声明 `PERSON/ORGANIZATION`；如何随 Profile 改动待协议实证 |
| `BapProfile.updatedAt` | Java Profile DTO 当前未给出 | 使用链上有效资料时点与可信链序；缺失表达 unknown，不制造时间 |

Identity 领域与 DTO 的双向映射放在 Adapter/Assembler；Domain 不直接依赖 BSON `Document`。真实 Java `IdentityProtocol.profile()` 的输入校验已经实现部分字段，但**现有代码 ≠ 所有产品不变量均满足**。

### 3.3 历史签名归属验证（R-04）

~~~text
TransactionEvidence(network, rawTx, txid, minedPosition?, observedSource)
     ↓
Verify cryptographic signature + signed payload coverage
     ↓
RotationHistoryResolver(root, verified BAP history, chainOrder)
     ↓
SigningPathAt(bapId, txEvidence) = ValidPath | UNKNOWN | CONFLICT
     ↓
Verify signer belongs to valid path AT that transaction's chain position
     ↓
VerifiedBapAttribution | PendingProof | Rejected
~~~

- Root 的确定性 BAP ID、轮换事件的旧→新授权链、链序与历史来源完整性分别检查；任何一步缺证据不能得出 `VerifiedBapAttribution`。
- 同块交易顺序、未确认交易、索引乱序和 reorg 不以本地 `updatedAt` 推断；对没有确定链序的情形保持待核实。
- 重组后重放受影响历史，从原始 `rawTx`/可靠 Indexer 事实重新派生签名归属。原证明证据保留供审计。
- 当前 `IdentityApi.currentAddress()` 与 `IdentityProtocol.verify(..., currentAddress)` 并未独立实现上述历史时点查询；这属于新增验证能力的开发事项。
- 关闭需要旧签名、Rotation、新签名、不同到达顺序、冲突路径和 reorg 的真实交易向量。

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

**原有接口兼容**：`GET /api/v1/identities/{bapId}`、`GET /api/v1/transactions/{txid}`、`GET /api/v1/operations/{id}`、`GET /api/v1/identity-operations/{id}` 等由现有 Controller 提供。目标 Contract 草案见 [OpenAPI](../../contracts/openapi/ownword.yaml)，请求与错误 code 以实际 Java/测试向量核对；DTO 字段仍保留待校验的可选属性，不将草案认定为已批准 SDK。

### 4.1 公共 Identity 查询 DTO 的权威转换（R-02 / R-05）

`IdentityApi` 的 `data.kind` 可能是 `published / incomplete / not-published / unknown / stored / empty` 中的一个兼容值，但不可单独决定授权和事实。转换时必须先验证 `scope`、`meta.source`、`indexCoverage` 与实际签名/网络来源；`broadcast-mock` 的 `stored/incomplete/empty` 是隔离查询。

`ResponseEntity<Document>` 当前以 `data + meta` 返回；错误以 `error.code/retryable/field + meta` 返回。OpenAPI 应覆盖这些现存字段、四字段 Sync、`Idempotency-Key`、回读与恢复接口，并将已确定的字段标强类型，未完成的 JSON 字段**明确标记候选而不扩写现有生产语义**。

### 4.2 交易同步异常与恢复

- 同一 `operationId` 改 TxID：409 `OPERATION_CONFLICT`；同一 TxID 的原交易内容或 BapId 不符：409；不得重签形成第二笔广播。
- 缺签名或身份归属不匹配：422；未验证签名只可进入可恢复未证实状态，不得产生有效公开身份记录。
- HTTP 404 `TRANSACTION_NOT_FOUND`（模拟 scope）或上游异常不能证明该笔交易未广播；客户端先按照原 TxID 及 Wallet 回执恢复。
- 身份流程按实际交易划分：钱包可同笔产生 ID + ALIAS，头像等可另笔提交。多笔流程每笔独立 operationId，flowId 由客户端关联，不能向现有四字段 Sync 添加未支持字段。

## 5. 数据模型与一致性

Mongo 在此阶段承担已同步原交易、日志与可重建读投影；仓储/集合现状以真实代码为准，后续抽取 Repository 时不得自行改写语义。

| 逻辑数据 | 唯一性/定位原则 | 说明 |
| --- | --- | --- |
| 同步操作 | operationId 与 txid 的幂等关系 | 防止重复同步与不同交易覆盖 |
| BAP 身份投影 | BapId + 已核实来源/环境范围 | Profile 是由有效链上声明派生 |
| 交易及身份签名证据 | network/scope/txid/输出 | 验证器版本、来源和观测时点要可追溯 |
| 身份签名路径历史 | BapId + 可验证轮换记录 | 不能仅缓存当前 signer；需支持 `SigningPathAt(tx)`、冲突与重组重放 |
| 提交与链上观测 | network/scope/txid + source + observedAt + 可选块锚 | 接收/接受/入块独立；重组或冲突时重新派生当前结论，保留旧观测 |
| Current Binding 查询 | Artifact 公开关联和 Origin | 不在 Identity 再保存第二份当前关系 |

对现有 Mongo 实际键、部分唯一索引、scope 实现有任何修改前先写迁移与回放测试；本表是**目标逻辑约束**而不是声明已经部署了同名集合或复合键。

## 6. 链与 Ordinal 查询、验收与恢复

优先适配现有 SDK 的 Arcade/Beef/Chaintracks/Txo/Owner/Ordfs 客户端，分别承担提交状态、原交易/BEEF、主链锚、输出/花费、地址资产与内容版本。上游方法不能直接当作 OwnWord 已有 API。`GET /transactions/{txid}` 当前仅提供存储 receipt 或有限链观测；现有 Java 网络接受判断偏向有确认交易，不能充当完整 mempool 状态查询。

Ordinal 交易详情需结合原交易逐输出解析、getByTxid、getSpend 和 Origin/内容读取。多输出追踪按 sat 连续性解析；历史分页/断点返回 PARTIAL/UNKNOWN/CONFLICT。全局编号尚需 metanet4j 补齐；不得用 OrdFS sequence 代替。主链重查与 reorg 恢复为实施项，不能声称 Chaintracks 已实现 reorg 订阅。



- 本地无 Identity 投影时查询公共来源；覆盖不足返回 UNKNOWN，不以 404/超时当不存在。
- 原始交易可重放、幂等，不重复生成资料和内容投影。
- 缺身份签名、签名覆盖被篡改或 BAP 归属不匹配，不得产生 verified 作者身份。
- Rotation 后旧交易按历史密钥继续得到相同 BAP ID。
- 模拟广播、隔离 Mongo、真实主网分别有来源标记；不能把隔离模拟的成功当作生产发布。
- 断网、索引失败和 reorg 只改变证据可信度/投影，不能擦除原始事件。
- Binding 的双向唯一、转移后失效、公开验证协议待实际 Indexer 和 Wallet Adapter 完成，不依据本地布尔标志直接生效。

验收来源：[支撑域 BDD](../../contracts/acceptance/supporting.feature)、[Identity 领域 BDD](../../contracts/acceptance/identity.feature)、[v0.1 集成设计](../../frontend/设计文档v0.1.0-真实集成-20261013-183000.md)、[v0.2 验收报告](../../../../../知识库/前端/ownword-v0.2.0/README.md)。

## 7. 实施次序与未关闭项目

1. 接通 Wallet Adapter 的实际执行材料与公共 Identity 查询/事件投影；确认版本与回执丢失恢复，不新增 OwnWord 初始化协议。公共历史覆盖用于公共事实及历史归属核验。
2. 补 R-02/03/05 的完整 DTO fixtures、Mapper、Error schema、HTTP 契约测试；再从 Controller 抽 `IdentitySignatureVerifier`、`PublicBapResolver` 和投影端口，不破坏已有 API。
3. 依据 R-04 补 Key Rotation 历史路径、原交易回放、来源覆盖不足、链序冲突和 reorg 测试。
4. 在 Artifact 的公开 Binding 与编号契约经过实测后接入只读 `BindingQueryPort`。
5. 真实钱包扩展、公共历史和主网资金/广播门禁单独验收，不用模拟或本地测试结果代替。

**待确认**：Binding 公开协议、Ordinals 编号 API、普通 Transfer 身份签名、签名历史验证、公共 BAP 覆盖度、现有部署运行态。详细清单见[核心认知 §12](../../核心认知.md#12-待确认)。
