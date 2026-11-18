# Identity 领域设计（OwnWord 统一目标 v0.4.0）

> **状态：needs-review。** 本文为前后端共用的 DDD 领域模型，不代表 v0.4.0 Identity 新功能已在生产实现。业务事实遵循[核心认知](../../核心认知.md)；本文件从历史[Identity 后端设计草案](../../backend/领域设计-Identity-v0.1.0-20261117-165000.md)、[v0.1.0 身份 PRD](../../prd/v0.1/设计文档v0.1.md)、[v0.3.0 Artifact PRD](../../prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)整理跨端共同语义。技术细节见[前端](../../frontend/identity/README.md)、[后端](../../backend/identity/README.md)。

## 1. 领域目标与上下文边界

Identity 解决稳定身份的发现、发布、资料维护、当前签名路径与历史签名归属。BAP ID 是跨上下文的稳定主键。Wallet 提供当前会话及签名权能；Profile 是可修改展示资料；Artifact 是独立可转移资产；Binding 属于 Artifact 的关联模型。

公共内容和关系只将经过核实的 BAP ID 作为作者或端点。公共主页的多模块内容由 Explorer 读取组合，不应把 Content/Artifact/Relationship 聚合塞入 Identity 聚合。上下文对应见[Context Map](../上下文映射-v0.4.0-20261117-175100.md)。

## 2. 通用语言

| 领域术语 | 模型中的含义 | 不变量/证据 |
| --- | --- | --- |
| `BapId` | 稳定公开身份标识；不可编辑 | 确定性派生不证明已在公共链上发布 |
| `BapIdentity` | 身份生命周期与签名密钥归属的聚合根 | 发布和轮换必须有可验证交易 |
| `BapProfile` | 公共展示资料，随有效链上声明演进 | Profile 的更新不能改变 BapId |
| `IdentityKeyHistory` | 对历史签名地址/路径及生效记录的可验证引用 | 旧交易按签名时有效历史验证 |
| `IdentitySignatureProof` | 本笔业务交易和关键目标的身份签名证据 | 钱包连接/花费签名不可代替 |
| `IdentityResolution` | 查询是否已发布及可信度的领域结果 | unknown 与 not-published 必须区分 |
| `IdentityNFTBinding` | BAP ID 和 Ordinal Origin 的独立关联 | 属于 Artifact，双向唯一且可被重验 |
| `ChainObservation` | 指向原交易/公共索引的来源、覆盖与时点 | 不以本地缓存判定全网不存在 |

上述术语的**唯一定义**在[核心认知 §2](../../核心认知.md#2-术语与命名)，结构字段与业务状态见其 §7、§9；本表只给出领域设计职责。

## 3. 主要 Use Case（跨端共用）

| Use Case | 所属上下文 | 输入/前置条件 | 成功结果与不确定性 |
| --- | --- | --- | --- |
| `ResolveMyIdentity` | Identity Query | Wallet 当前 `BapId`、受控 scope 与来源观测 | 区分 Published、证据充分的 NotPublished、Unknown；Profile 是否完整另行判断 |
| `AssessIdentityInitialization`（新增设计建议） | Identity Application | 新建意图、Root 控制证明、公共 BAP 历史/未决交易证据 | `ALLOW / BLOCK / NEED_EVIDENCE`，不改写公开身份查询结果 |
| `PublishIdentity` | Identity Application | 初始化资格 ALLOW、冻结 Review、逐笔有效签名、保存的原交易 | 已广播/已同步/公开可读分别跟踪；结果不确定时恢复原 TxID |
| `UpdateBapProfile` | Identity Application | 已核实控制能力、已发布身份、冻结资料 | Profile 的有效链上更新；多笔交易允许部分完成 |
| `RotateIdentityKey` | Identity Application | 旧有效密钥路径的证明、新路径的授权及链序 | `BapId` 不变，新增可验证历史；来源不完整则不提升到 Verified |
| `GetPublicIdentity` | Identity Query | BapId | 公开 Identity/Profile/Proof 与来源覆盖；异常和未知明确 |
| `ResolveByInscriptionNumber` | **Explorer Application** | 十进制编号或 #前缀 | Artifact 编号→Origin→有效 Current Binding→Identity；**不是 Identity 内部命令** |

用例可以跨前后端协作，但不要求两端复制同名聚合对象。初始化资格与公共存在性分离的详细判定见 §6。编号解析由 Explorer 组合 Artifact + Identity 的公开读取端口。

## 4. 战术模型与聚合

~~~text
Identity Context
└── BapIdentity (Aggregate Root)
    ├── BapId (Value Object, immutable)
    ├── IdentityStatus + IdentityType (PERSON | ORGANIZATION)
    ├── IdentitySigningPath / IdentityKeyHistory
    └── VerifiedPublication / KeyRotation Evidence references

Identity Read Model
└── BapProfile (published, evidence-backed projection)

Artifact Context
├── BapNFT (Aggregate Root)
└── IdentityNFTBinding (independent aggregate/association)
    ├── BapId + OrdinalOrigin
    ├── ACTIVE / HISTORICAL / INVALID
    └── evidence reference
~~~

`BapIdentity` 持有身份本身的稳定标识、可验证状态和密钥轮换行为；`BapProfile` 在 MVP 中可作为链上 ALIAS/图片的可重建资料投影，而非强制要求与聚合在同一数据库事务中保存。

`IdentityNFTBinding` 归 Artifact 上下文，Current 约束由该上下文的聚合及证据验证控制；Identity 工作台读取 `CurrentBindingSummary`，不得双写独立 Current 字段形成两个权威来源。仓储实现、Mongo 集合和 HTTP 适配位于后端实现设计中。

### 4.1 Identity 与 Profile 字段归属

| 概念 | 核心认知属性/约束 | 应用 DTO 现状 | 领域行为 |
| --- | --- | --- | --- |
| `BapIdentity.bapId` | 稳定、不可改 | `bapId` | 从 Root 关联派生；从公开证据确认 |
| `BapIdentity.rootPath/currentPath/previousPath` | Root 稳定、Current 可轮换 | `currentAddress` 为现有服务投影字段，不能等价为全部路径 | 通过 BAP 历史验证，轮换后保留历史 |
| `BapIdentity.type` | `PERSON / ORGANIZATION`，身份声明 | 无独立 Identity Type DTO 已核实 | 属于身份声明，不得仅靠修改 Profile 推断已更新 |
| `BapProfile.name` | 必填，可修改，≤100 字符 | `name` | 资料发布前校验，回读后验证生效 |
| `BapProfile.description` | 可修改，≤1000 字符 | `bio` | 领域 ↔ DTO 显式映射，不能同时维护两份资料 |
| `BapProfile.image` | 可修改，≤2048 字符 | `imageUrl` | URI 或受控链上内容引用，关联单独交易的证据 |
| `BapProfile.type` | `Person / Organization`，可修改 | `type` | 展示资料声明；与 Identity.type 的同步/变更协议**待明确** |
| `BapProfile.updatedAt` | 必填，派生有效更新时点 | 现有 Profile DTO 未含 | 必须来自有效资料记录的可信链序/时点，不得用 HTTP 到达时间冒充链上时点 |

**决策门禁**：Identity.type 与 Profile.type 有不同的可变性。现阶段只将 Profile.type 的修改建模为资料变更请求；是否还必须产生身份声明/轮换交易、以及如何解决两者不一致，需由产品/协议验证确认后才能实现。字段格式与长度唯一权威是[核心认知 §7.2–7.3](../../核心认知.md#72-bapidentity)。

## 5. 领域行为与业务不变量

| 规则标识 | 领域决策 | 责任边界 |
| --- | --- | --- |
| ID-01 | BAP ID 创建后不可编辑；轮换不变更 ID | Identity 聚合 |
| ID-02 | Wallet 可计算 BAP ID ≠ 公共身份已发布 | IdentityResolution |
| ID-03 | Profile 修改对应新的链上事实；不得直接将本地编辑称为已公开更新 | Identity/Profile 投影 |
| ID-04 | BAP 密钥历史用于逐笔签名归属验证，不能仅使用当前地址 | Identity Proof 验证 |
| ID-05 | 每笔 OwnWord 链上交易需有覆盖对应业务内容和关键目标的 identityKey 身份签名 | 全部领域应用用例 |
| ID-06 | Creator、Signer、Owner、Current Binding 互不推断 | Identity 与 Artifact ACL |
| ID-07 | 一个 BAP ID 至多有一个当前 Artifact，单个 Origin 至多指向一个有效当前 BAP ID | Artifact Binding |
| ID-08 | Inscription Number 未经确认不能分配，reorg 后可以变更 | Artifact / Indexer |
| ID-09 | 协议/网络读取未知不能当作业务不存在 | 全部查询 Use Case |
| ID-10 | 账户切换使未提交的旧授权失效；已提交交易继续归属旧 BAP ID | Wallet/Application |
| ID-11 | 初始化许可是操作资格，不证明 BAP ID 未公开；疑似旧历史/未决交易不允许新建另一笔身份初始化交易 | Identity Application |
| ID-12 | Identity.type 与 Profile.type 不因字段名相似而默认同步；变更策略需要独立事实证据 | Identity/Profile |

本节只定义规则在 DDD 模型中的**责任归属**；权威内容和例外仍见[核心认知 §4](../../核心认知.md#4-全局不变量)、[§6.4](../../核心认知.md#64-全部链上交易的身份归属)、[§7.7](../../核心认知.md#77-identitynftbinding)、[§9.4](../../核心认知.md#94-artifact-与-binding)。

## 6. 状态、查询事实与初始化资格

### 6.1 业务生命周期

身份**产品状态**沿用[核心认知 §9.2](../../核心认知.md#92-identity)：

~~~mermaid
stateDiagram-v2
  [*] --> NOT_PUBLISHED
  NOT_PUBLISHED --> PUBLISHING: 已授权初始化
  PUBLISHING --> ACTIVE: 已验证公开身份声明
  ACTIVE --> ROTATING
  ROTATING --> ACTIVE: 已验证 Key Rotation
  ACTIVE --> REVOKED: 未来协议能力
~~~

`NOT_PUBLISHED` 是有充分公共覆盖的业务结论；`UNKNOWN` 是查询的认知状态，不直接加入生命周期。前端的 `Review / Prepared / BroadcastUnknown` 属于操作状态，不能把按钮成功当作 `ACTIVE`。

### 6.2 三个彼此独立的判断维度（R-01 / R-02）

| 维度 | 领域结果 | 谁决定 |
| --- | --- | --- |
| **Public Identity Resolution** | `PUBLISHED / NOT_PUBLISHED / UNKNOWN` + `Proof / Coverage / Scope` | Identity 公共来源与独立验证 |
| **Profile Completeness** | `COMPLETE / INCOMPLETE / UNKNOWN` | 有效 Profile 资料及必填字段 |
| **Wallet Capability** | `AVAILABLE / UNAVAILABLE / UNKNOWN`、操作时会话和 Root 证明 | Wallet Adapter 的受控证据 |
| **Initialization Eligibility** | `ALLOW / BLOCK / NEED_EVIDENCE` + reason、过期与证据引用 | Identity Application 决策；发布时重查 |

现有传输 `Resolution.kind` 是历史客户端/模拟结果，不能直接映射到 Identity 状态机。建议的**领域映射**如下（已核实与待验证必须区分）：

| scope 与传输 kind | 公共身份结果 | Profile 结果 | 解释 |
| --- | --- | --- | --- |
| `mainnet/published` | `PUBLISHED`，前提是有效 Proof 与公开观测充分 | 以字段/证据独立判断 | 不能只看 kind 或旧缓存 |
| `mainnet/not-published` | 仅 coverage **充分**才能是 `NOT_PUBLISHED`，否则 `UNKNOWN` | UNKNOWN | 现有 Java 未提供该充分证明分支 |
| `mainnet/unknown` | `UNKNOWN` | UNKNOWN | indexer 无覆盖、响应无记录、来源失败不可合并为“未发布” |
| `mainnet/incomplete`（兼容预留） | 验证到初始声明才可为 `PUBLISHED`；否则 `UNKNOWN` | `INCOMPLETE` 或 `UNKNOWN` | 需具体 DTO 证据 |
| `broadcast-mock/stored` | **测试内已存储**，非主网 PUBLISHED | 通常 COMPLETE，仍按字段判断 | 不能给主网发布资格 |
| `broadcast-mock/incomplete` | **测试内有部分记录** | INCOMPLETE | 只用于隔离模拟 |
| `broadcast-mock/empty` | **模拟内未找到** | UNKNOWN | 不是公开未发布 |
| 任何 scope/超时、5xx、坏响应、scope 不一致 | `UNKNOWN` + 可识别错误 | UNKNOWN | 不得自动转化为 `NOT_PUBLISHED` |

> 注意：`incomplete` 在现有 TypeScript union 中出现于全部 `Resolution`，但 Java 已核实的模拟处理有此分支；不凭类型存在推断主网已经会返回它。上述 `mainnet/incomplete` 为兼容设计分支，待实际 fixture 验证。

### 6.3 首次发布的初始化资格（R-01，待验证的目标设计）

`AssessIdentityInitialization` **不要求预先返回 `NOT_PUBLISHED` 才能开始 Review**。它对同一 `BapId` 的已公开证据、钱包 Root 控制证明、未完成原交易及公共历史判定，给出新的**操作资格**，不修改 `IdentityResolution`。

| 身份观测 | Wallet/历史证据 | 决策 | 可执行范围 |
| --- | --- | --- | --- |
| 已验证 PUBLISHED | 当前有效身份存在 | BLOCK 新的初始化 | 进入 Identity 管理/补全/Rotation |
| 已确认 NOT_PUBLISHED | Root 控制且无未完成初始化 | ALLOW | 冻结 Review、构造和签署初始声明；提交前重查 |
| UNKNOWN（来源可访问但历史覆盖不充分） | Root 证明有效、尚无已知声明，但不能排除历史 | NEED_EVIDENCE | 可保留 Draft/Review；不得直接广播第二笔初始化 |
| UNKNOWN（Indexer 超时/5xx/主链证据不足） | 任意 | NEED_EVIDENCE | 失败可恢复；暂停不可逆广播 |
| 任意 | 已有同一 BAP ID 的签名原交易或广播未知 | BLOCK 新建交易，先恢复 | 按同一 operationId/TxID 查询/同步/回读 |
| 任意 | Wallet 账户已切换、Root/BapId 不匹配、控制权缺失 | BLOCK | 取消旧授权并重建会话 |

**明确未关闭的设计决策**：由于当前公共 Indexer 不足以证明未发布，本表在 UNKNOWN 时采取保守保护，P0 的代码闭环还需要`PublicBapHistoryResolver` 提供充分历史覆盖证据，或者经产品/安全评审批准一套能防冲突的 Root 控制型初始发布协议。不能因为要打通页面就默认将 UNKNOWN 视为可安全发布。**本次只完成目标状态机和责任划分，运行时 P0 仍未关闭。**

### 6.4 初始化与恢复时序

~~~mermaid
sequenceDiagram
  actor User
  participant UI as Identity UI
  participant Use as Identity Application
  participant Wallet as Wallet Adapter
  participant Source as Public BAP/History Resolver
  participant Sync as TransactionSync
  UI->>Use: ResolveMyIdentity(bapId, scope)
  Use->>Source: 公共证据与 coverage
  Source-->>Use: PUBLISHED / NOT_PUBLISHED / UNKNOWN
  User->>UI: 新建身份意图
  UI->>Use: AssessIdentityInitialization
  Use->>Wallet: 证明 Root 与当前会话控制能力
  Use->>Source: 重新核验身份历史、覆盖和未决交易
  alt ALLOW 且提交前重新验证有效
    Use-->>UI: ReviewAllowed
    User->>UI: 冻结 Review 并确认
    UI->>Wallet: 准备/签署同一原交易
    Wallet-->>UI: txid + rawTx
    UI->>UI: 持久化原交易和恢复日志
    UI->>Wallet: 广播同一 rawTx
    Wallet-->>UI: accepted / failed / unknown
    UI->>Sync: 只同步原交易（已获已提交证据时）
    Sync-->>UI: verified / pending / rejected
    UI->>Source: 回读公开身份与 Proof
  else NEED_EVIDENCE/BLOCK
    Use-->>UI: 保留 Draft、显示原因和可恢复的验证操作
  end
~~~

广播结果未知时先核查原 TxID，**不能重新创建不同 TxID**；在恢复期间 Scope/Wallet Account 变化不得将旧事务重新归属新身份。Profile 图片/ALIAS 可跨多笔提交，每笔分别签名与恢复。

## 7. 领域事件及其可信度

| 事件 | 何时产生 | 能否直接证明链上已生效 |
| --- | --- | --- |
| `IdentityInitializationAssessed` | 产生操作资格 ALLOW/BLOCK/NEED_EVIDENCE 的可失效决策 | 否 |
| `IdentityPublicationRequested` | 用户确认发布意图 | 否 |
| `WalletTransactionPrepared` | 原交易已签名并保存 | 否 |
| `BroadcastResultObserved` | Wallet/网络返回可追溯回执 | 需要独立核实 |
| `IdentityPublicationVerified` | 验签及公开 BAP 事实充分 | 是，附网络和来源 |
| `ProfileUpdateVerified` | 有效资料交易被核实 | 是，附交易与版本 |
| `IdentityKeyRotatedVerified` | 轮换与历史路径核实 | 是，附旧/新路径引用 |
| `ArtifactBindingVerified` | Artifact 上下文按公开契约验证 | 取决于待验证的 Binding 协议 |

领域事件携带来源范围、交易标识、签名验证结果及观测时点；不以本地布尔值替代原始证据。跨上下文消费需幂等、可重放。

## 8. 跨端协作与数据所有权

### 8.1 领域端口（接口名称为设计建议）

| 端口 | 用途与失败语义 |
| --- | --- |
| `PublicIdentityResolver.resolve(BapId, Scope)` | 返回身份事实、来源/覆盖/链序；不可把上游 404 直接变为 NOT_PUBLISHED |
| `PublicBapHistoryResolver.history(BapId, checkpoint)` | 独立检查当前/历史初始化、Rotation、冲突与重组；coverage 不充分返回 UNKNOWN |
| `WalletRootControlPort.prove(BapId, session)` | 仅证明与 Root 派生的控制能力，仍不证明链上无现有身份；私钥不出 Wallet |
| `PendingPublicationRepository.find(BapId, Scope)` | 找回同一 BAP ID/Operation/TxID 未决提交；用于防重复初始化 |
| `SigningPathAt.resolve(BapId, TransactionEvidence)` | 按可验证链序返回签名发生时有效路径 / UNKNOWN / CONFLICT |
| `RotationHistoryResolver.replay(BapId, observations)` | 校验 Root、每次 Rotation、重组分支与旧路径有效范围，不使用本地 updatedAt 顺序 |
| `CurrentBindingQuery.get(BapId)` | 从 Artifact 只读有效关联摘要；Identity 不维护 Binding 写模型 |

**签名归属规则**：先独立验证本笔签名覆盖内容，再由 `SigningPathAt` 判定签名者是否属于该 BAP ID 在该笔交易**有效链序**的路径。历史不完整、重组、冲突及同区块排序不明确时返回 UNKNOWN/CONFLICT；前后端不得显示 `Signature valid` 的 BAP 归属结论。具体 BAP 生效编码与时点仍依赖实际原交易向量关闭。

- **前端 Application**：钱包连接、用户 Review、冻结业务快照、签名与广播、持久化恢复日志、同步后查询公开状态；不能决定公共身份是否存在。
- **后端 Application/Domain**：验证 rawTx、TxID、BAP 签名归属及历史密钥，核对真实网络来源和查询覆盖；维护可重建投影。
- **Artifact**：处理 Current Binding、Origin、ownership 和编号；Identity 只读其结果。
- **Explorer**：聚合跨上下文公共查询，不通过用户路由参数赋予编辑权限。
- **契约**：使用[Contracts](../../contracts/README.md)的 API/BDD 入口，签名与索引缺口仍见[核心认知 §12](../../核心认知.md#12-待确认)。

## 9. 验收映射（供前后端分别实现）

| 需求权威 | 领域规则 | Use Case | 契约/行为 | 测试责任 |
| --- | --- | --- | --- | --- |
| 核心认知 §6.1、§10.8 | ID-02/09/11 | Resolve + AssessInitialization | IdentityResolution/PublicationEligibility | 前端状态分流、后端 coverage/Root/重试 |
| 核心认知 §7.2/7.3 | ID-01/03/12 | UpdateBapProfile | Profile DTO Mapper/类型决策 | 前后端字段、长度与修改路径 |
| 核心认知 §6.4、§11.17 | ID-04/05 | VerifyKeyRotation/SigningPathAt | Proof/历史验证向量 | 后端加密验证、前端 Proof 展示 |
| 核心认知 §10.8、§11.10 | ID-10/11 | PublishIdentity | SyncReceipt/Operation Recovery | 前端 IndexedDB/账户切换、后端幂等 |
| 核心认知 §11.2/§11.15 | ID-06/07/08 | Explorer.ResolveByInscriptionNumber | BindingQuery（未来） | Artifact/Explorer Indexer |

场景源文件：[Identity BDD](../../contracts/acceptance/identity.feature)、[Artifact BDD](../../contracts/acceptance/artifact.feature)。以上映射定义**开发应做的验证**，并非宣称已通过。

| 场景 | 应有结果 | 验收来源 |
| --- | --- | --- |
| Wallet 本地计算 BAP ID，公共覆盖不足 | UNKNOWN，不进入已确认未发布分支 | Identity v0.1 PRD；核心认知 §6.1/10.8 |
| 链上已发布且签名归属有效 | 可验证公开身份，BAP ID 可完整查询 | 核心认知 §11.1、§11.17 |
| 交易结果未知/HTTP 404 | 先按原 TxID 查询，不自动重签或重发 | 前端 v0.1 集成设计 |
| Profile 多笔更新中取消 | 保留已经广播和核实的子交易，不伪造整体撤销 | Identity 集成设计 |
| Key Rotation 后读取旧交易 | 按签名发生时有效路径验证，BAP ID 不变 | 核心认知 §11.17 |
| Inscription Number 已分配但没有有效 Binding | 只解析 Artifact，禁止冒充身份 | 核心认知 §11.2/§11.15 |
| 模拟 scope 的成功结果 | 不进入主网公开投影或主网可发现性结论 | 核心认知 §10.8 |

完整 Given/When/Then 以[PRD](../../prd/v0.1/设计文档v0.1.md)为来源；测试衍生物的状态见[Contracts/Acceptance](../../contracts/acceptance/README.md)。

## 10. 待验证事项与影响

| 项 | 拥有方 | 关闭依据 |
| --- | --- | --- |
| 全交易身份签名的实际封装/覆盖，特别是普通 Artifact Transfer | Wallet Adapter / metanet4j | 原交易和独立验证器向量 |
| **P0 初始化门禁**：公开历史覆盖或经审批的 Root 控制型初始化冲突防护 | Identity / Indexer / Wallet / 产品安全 | 新建、旧身份、覆盖未知、网络故障、广播未知的实证与审批 |
| BAP 公共索引覆盖足以证明未发布的条件 | Identity / Indexer | coverage 定义、服务异常和全历史样例 |
| Binding 创建、替换、撤销、双向唯一及转让后重验协议 | Artifact / Indexer | 可重放链上事件与冲突/重组实验 |
| Inscription Number、Origin、主链/重组相关 API | Indexer | 真实输出和重组样例 |
| Rotation 历史签名生效顺序 | BAP 实现 | 历史交易与密钥路径验证 |
| Identity.type 与 Profile.type 的同步/变更授权 | Identity / 产品 / Protocol | 确认业务规则与真实交易 / Java TS Mapper 样例 |

以上属于开发前待关闭的技术契约，不能因为本领域设计完成就记为生产可用。
