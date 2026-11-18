# Identity 领域设计（OwnWord 统一目标 v0.4.0）

> **状态：needs-review。** 本文为前后端共用的 DDD 领域模型，不代表 v0.4.0 Identity 新功能已在生产实现。业务事实遵循[核心认知](../../核心认知.md)；本文件从历史[Identity 后端设计草案](../../backend/领域设计-Identity-v0.1.0-20261117-165000.md)、[v0.1.0 身份 PRD](../../prd/v0.1/设计文档v0.1.md)、[v0.3.0 Artifact PRD](../../prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)整理跨端共同语义。技术细节见[前端](../../frontend/identity/README.md)、[后端](../../backend/identity/README.md)。

## 1. 领域目标与上下文边界

Identity 解决稳定身份的业务语义、资料映射、公开发现与历史签名归属。BAP ID 是跨上下文的稳定主键。本人 BAP ID 派生、发布、Profile 更新、当前签名路径与轮换执行委托 Yours Wallet/SDK；OwnWord 组合业务 Review、钱包结果、公共核验及操作恢复，具体边界见[支撑域设计](../supporting/README.md)。Profile 是可修改展示资料；Artifact 是独立可转移资产；Binding 属于 Artifact 的关联模型。

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
| `ResolveMyIdentity` | Identity Application / Query | Wallet 本人身份状态与独立公共查询 | 钱包会话、钱包身份/资料、公共发布证据分别表达；不能互相覆盖 |
| `PublishIdentity` | Identity Application → Wallet | 钱包提供的发布能力、冻结 Review、无未决原操作及已知冲突 | 调用钱包现有身份 Action；OwnWord 跟踪执行、同步、公共回读 |
| `UpdateBapProfile` | Identity Application → Wallet | 钱包当前身份与资料能力、字段映射、冻结资料 | 委托钱包资料 Action；首次更新可由 Action 同时产生 ID 与 ALIAS，逐笔记录结果 |
| `RotateIdentityKey` | Identity Application → Wallet | 钱包当前身份及轮换能力 | 钱包执行旧密钥签署的新声明；OwnWord 验证稳定 BapId 与历史链序，不自行管理密钥序号 |
| `GetPublicIdentity` | Identity Query | BapId | 公开 Identity/Profile/Proof 与来源覆盖；异常和未知明确 |
| `ResolveByInscriptionNumber` | **Explorer Application** | 十进制编号或 #前缀 | Artifact 编号→Origin→有效 Current Binding→Identity；**不是 Identity 内部命令** |

用例可以跨前后端协作，但不要求两端复制同名聚合对象或钱包内部状态机。钱包操作能力与公共存在性分离的判定见 §6。编号解析由 Explorer 组合 Artifact + Identity 的公开读取端口。

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

`BapIdentity` 表达身份稳定标识、已验证状态和历史约束，是 OwnWord 的业务模型；它不复制钱包密钥管理聚合或本人的发布判定。`BapProfile` 可作为链上 ALIAS/图片的可重建资料投影，不要求与聚合在同一数据库事务中保存。

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

**待明确**：核心认知分别要求 Identity.type 和可修改的 Profile.type，尚未定义二者的变更一致性。现有钱包 `useIdentity.saveProfile` 固定写 `@type: Person`，BAP ID 声明构造不含 PERSON/ORGANIZATION 字段，不能声称组织身份和类型变更已获得钱包支持。由产品/钱包适配负责人通过协议样例确认类型映射与变更策略；不推断 Identity.type 永久不可变，也不自行新增初始化或轮换协议。字段格式与长度唯一权威是[核心认知 §7.2–7.3](../../核心认知.md#72-bapidentity)。

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
| ID-11 | 本人身份动作委托 Wallet/SDK；公共 unknown 不单独否决钱包已知能力；已知冲突及未决原操作先恢复，不重新初始化 | Wallet Integration / Identity Application |
| ID-12 | Identity.type 与 Profile.type 不因字段名相似而默认同步；变更策略需要独立事实证据 | Identity/Profile |

本节只定义规则在 DDD 模型中的**责任归属**；权威内容和例外仍见[核心认知 §4](../../核心认知.md#4-全局不变量)、[§6.4](../../核心认知.md#64-全部链上交易的身份归属)、[§7.7](../../核心认知.md#77-identitynftbinding)、[§9.4](../../核心认知.md#94-artifact-与-binding)。

## 6. 状态、钱包管理与公共查询

### 6.1 业务生命周期

身份产品状态沿用[核心认知 §9.2](../../核心认知.md#92-identity)。`UNKNOWN` 表达查询证据不足，不加入产品生命周期；钱包回执、已提交、已同步和公共身份已核实各自保留。公共 `NOT_PUBLISHED` 需要充分覆盖；本人钱包中的“尚未发布”只表达钱包管理状态。

### 6.2 状态的责任与使用

| 判断 | 数据/规则来源 | OwnWord 使用方式 |
| --- | --- | --- |
| 连接、解锁、站点授权、操作权限 | Yours Wallet 的会话和权限管理 | 适配为可用能力；连接成功不能代替站点或逐笔授权 |
| 本人 BapId、钱包发布状态、当前资料、轮换路径 | Wallet 身份 Actions、钱包 basket 与 `useIdentity` | 使用钱包管理结果；缓存图片等提示不能提升为已验证状态 |
| 资料完整度 | 钱包资料 + 核心认知必填字段 | OwnWord 显式映射后做业务字段校验，不另建本人资料权威副本 |
| 本次操作可执行性 | 钱包 Action 能力/前置条件 + OwnWord Review、scope、会话、冲突及恢复记录 | 提交前重查，调用现有 Action；不另设 Root 控制型初始化协议 |
| 公共身份和历史签名归属 | 原交易、公开 BAP 观测、历史验证 | 返回带来源/覆盖的 PUBLISHED、NOT_PUBLISHED、UNKNOWN 或冲突原因；不反写钱包发布开关 |

现有传输 DTO 是公共查询的兼容输入，领域映射为：

| scope / kind | 公共身份结果 | 资料与使用限制 |
| --- | --- | --- |
| mainnet / published | Proof 和公共证据有效才为 PUBLISHED | 资料按实际字段独立校验 |
| mainnet / not-published | 历史覆盖充分才为 NOT_PUBLISHED，否则 UNKNOWN | 当前 Java 未核实充分覆盖分支 |
| mainnet / unknown | UNKNOWN | 不能改写为未发布或单独阻止钱包现有身份动作 |
| mainnet / incomplete | 只有初始声明已核实才为 PUBLISHED，否则 UNKNOWN | 兼容设计，实际响应 fixture 待验证 |
| broadcast-mock / stored、incomplete、empty | 隔离模拟结果，不形成主网身份结论 | 不提升为主网 Proof 或授权 |
| 超时、5xx、坏响应或 scope 不匹配 | UNKNOWN + 错误原因 | 按失败来源决定重试；钱包能力是否可用独立判断 |

### 6.3 本人身份操作分流

| 已知情况 | 动作 |
| --- | --- |
| 钱包明确提供新建/首次资料 Action，公共查询 UNKNOWN，无已知冲突和未决操作 | 可进入业务 Review 并请求钱包执行；公开状态保持 UNKNOWN，等待交易回读 |
| 钱包身份已发布，资料不全 | 使用资料更新能力，不重新初始化 |
| 公共已核实同一身份存在，但钱包本地无对应记录 | 先恢复钱包跟踪/匹配，避免重复 ID 声明 |
| 钱包读取失败、会话/操作权限未知、BapId 不匹配 | 保留草稿，修复钱包状态后继续 |
| 原 Action 结果未知或已有原 TxID/reference | 先恢复原执行，不能因索引未查到而创建另一笔 |
| 会话或 scope 改变 | 作废未提交 Review；已提交交易继续按原身份和网络追踪 |

SDK `publishIdentity` 在本地身份已存在时返回错误；`updateProfile` 在首次发布路径可同笔构造 ID + ALIAS。这两种能力按各自语义适配，不能都描述为“重复调用自动幂等”。钱包本地身份查询也不证明公共历史不存在。

### 6.4 执行与恢复

~~~plantuml
@startuml
actor User
participant "Identity Application" as App
participant "Transaction Support" as Tx
participant "Wallet / SDK Action" as W
participant "Sync / Public Query" as Q
App -> W: 读取本人身份与操作能力
App -> Tx: 查询未决执行、scope 与业务冲突
User -> App: 确认冻结的业务 Review
App -> Tx: 保存业务意图与 operationId
Tx -> W: 调用已授权的身份 Action
W --> Tx: result / reference / txid / error
Tx -> Tx: 保存原执行和可得交易证据
alt 执行结果已知
  Tx -> Q: 同步可得原交易，查询网络与公开身份
  Q --> App: 分别返回同步、链状态、公共身份观测
else 执行结果未知
  Tx -> W: 按原 reference / 钱包记录恢复
  Tx -> Q: 已知 txid 时查询原交易
  Tx --> App: 保持待恢复，禁止自动重建另一笔
end
@enduml
~~~

已核实的身份 Action 默认路径内部完成构造、签名并尝试提交，返回后才取得最终交易材料；自定义路径需核实 noSend 才能分离最终签名和提交，单独 signAndProcess=false 不足。必须验证钱包在回执丢失时可用的关联与恢复能力；能力不足属于集成门禁。图片/ALIAS 等多笔流程逐笔记账，钱包同笔组合的 ID/ALIAS 只记一笔，详见[支撑域 §4–6](../supporting/领域设计-支撑域-v0.4.0-20261118-141904.md)。

## 7. 领域事件及其可信度

| 事件 | 何时产生 | 能否直接证明链上已生效 |
| --- | --- | --- |
| `WalletIdentityObserved` | 读取本人钱包身份和操作能力，附会话及来源 | 否 |
| `IdentityPublicationRequested` | 用户确认发布意图 | 否 |
| `WalletExecutionRecorded` | 记录 Action/reference/已知交易；自定义两阶段可另有 Prepared 记录 | 否 |
| `BroadcastResultObserved` | Wallet/网络返回可追溯回执 | 需要独立核实 |
| `IdentityPublicationVerified` | 验签及公开 BAP 事实充分 | 是，附网络和来源 |
| `ProfileUpdateVerified` | 有效资料交易被核实 | 是，附交易与版本 |
| `IdentityKeyRotatedVerified` | 轮换与历史路径核实 | 是，附旧/新路径引用 |
| `ArtifactBindingVerified` | Artifact 上下文按公开契约验证 | 取决于待验证的 Binding 协议 |

领域事件携带来源范围、交易标识、签名验证结果及观测时点；不以本地布尔值替代原始证据。跨上下文消费需幂等、可重放。

## 8. 跨端协作与数据所有权

### 8.1 领域端口（逻辑接口，不等于新增 HTTP API）

| 端口 | 用途与失败语义 |
| --- | --- |
| `WalletIdentityPort` | 读取本人身份，委托发布、资料更新和轮换；由 Wallet Integration 适配，不持有私钥 |
| `WalletExecutionPort` | 委托高层 Action 或支持的两阶段执行，并恢复原 reference / TxID，见支撑域 |
| `PublicIdentityResolver` | 返回公共身份及来源/覆盖；上游 404 不能直接变为 NOT_PUBLISHED |
| `PublicBapHistoryResolver` | 读取初始化、Rotation、冲突与重组证据，服务历史签名归属；不承担本人首次发布许可 |
| `OperationRecoveryRepository` | 保存和恢复同一身份、scope、操作意图及实际交易；不是新的身份权威存储 |
| `SigningPathAt / RotationHistoryResolver` | 验证签名发生时的有效密钥和链序；历史不足或冲突返回 UNKNOWN / CONFLICT |
| `CurrentBindingQuery` | 只读 Artifact 的有效关联摘要，不双写 Binding |

**签名归属规则**：先独立验证本笔签名覆盖内容，再由 `SigningPathAt` 判定签名者是否属于该 BAP ID 在该笔交易**有效链序**的路径。历史不完整、重组、冲突及同区块排序不明确时返回 UNKNOWN/CONFLICT；前后端不得显示 `Signature valid` 的 BAP 归属结论。具体 BAP 生效编码与时点仍依赖实际原交易向量关闭。

- **前端 Application**：适配钱包连接与身份动作、用户 Review、冻结业务快照、持久化执行与恢复日志、同步和公共回读；钱包管理会话、权限和签名路径。
- **后端 Application/Domain**：验证 rawTx、TxID、BAP 签名归属及历史密钥，核对真实网络来源和查询覆盖；维护可重建投影。
- **Artifact**：处理 Current Binding、Origin、ownership 和编号；Identity 只读其结果。
- **Explorer**：聚合跨上下文公共查询，不通过用户路由参数赋予编辑权限。
- **契约**：使用[Contracts](../../contracts/README.md)的 API/BDD 入口，签名与索引缺口仍见[核心认知 §12](../../核心认知.md#12-待确认)。

## 9. 验收映射（供前后端分别实现）

| 需求权威 | 领域规则 | Use Case | 契约/行为 | 测试责任 |
| --- | --- | --- | --- | --- |
| 核心认知 §5.4、§6.1、§10.8 | ID-02/09/11 | Resolve + Wallet Identity Action | 钱包状态/IdentityResolution/执行恢复 | 钱包适配、公共 coverage、冲突与回执丢失 |
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
| Wallet 身份 Action 的实际接口、权限、交易材料与丢回执恢复 | Wallet Adapter / Identity | 锁定版本；新建/已有身份、公共未知、冲突、拒绝及原执行恢复 fixtures |
| BAP 公共索引覆盖足以证明未发布的条件 | Identity / Indexer | coverage 定义、服务异常和全历史样例 |
| Binding 创建、替换、撤销、双向唯一及转让后重验协议 | Artifact / Indexer | 可重放链上事件与冲突/重组实验 |
| Inscription Number、Origin、主链/重组相关 API | Indexer | 真实输出和重组样例 |
| Rotation 历史签名生效顺序 | BAP 实现 | 历史交易与密钥路径验证 |
| Identity.type 与 Profile.type 的同步/变更授权 | Identity / 产品 / Protocol | 确认业务规则与真实交易 / Java TS Mapper 样例 |

以上属于开发前待关闭的技术契约，不能因为本领域设计完成就记为生产可用。
