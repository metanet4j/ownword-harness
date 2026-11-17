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

## 3. 主要 Use Case

| Use Case | 输入/前置条件 | 成功结果 | 未成功与未知结果 |
| --- | --- | --- | --- |
| `ResolveMyIdentity` | 当前 Wallet 的 BapId、网络、公共来源观测 | 已验证发布身份 + Profile，或覆盖充分的未发布结果 | coverage 缺失/失败返回 UNKNOWN |
| `PublishIdentity` | 冻结 Review、操作 BAP ID、有效签名/已广播交易 | 根据公开链上证据更新 Identity | 取消未提交操作；已提交但结果未知先查询原 TxID |
| `UpdateBapProfile` | 已发布身份、冻结资料、逐笔签名交易 | 公开资料更新并有来源追溯 | 头像与 ALIAS 多笔操作保留部分成功 |
| `RotateIdentityKey` | 已发布身份、旧路径授权、新路径的证据 | BAP ID 不变，新增有效密钥历史 | 待验证不得凭本地请求覆盖签名历史 |
| `GetPublicIdentity` | BapId | 公开身份/资料/Proof/coverage | 未覆盖和服务不可用不得变成“未找到” |
| `ResolveIdentityByNumber` | Inscription Number 十进制标识 | Artifact → Origin → 有效 Binding → BapId | 未关联只展示资产，不推断 creator/owner 是身份 |

## 4. 战术模型与聚合

~~~text
Identity Context
└── BapIdentity (Aggregate Root)
    ├── BapId (Value Object, immutable)
    ├── IdentityStatus
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

本节只定义规则在 DDD 模型中的**责任归属**；权威内容和例外仍见[核心认知 §4](../../核心认知.md#4-全局不变量)、[§6.4](../../核心认知.md#64-全部链上交易的身份归属)、[§7.7](../../核心认知.md#77-identitynftbinding)、[§9.4](../../核心认知.md#94-artifact-与-binding)。

## 6. 状态与领域结果

身份**产品状态**沿用[核心认知 §9.2](../../核心认知.md#92-identity)：

~~~mermaid
stateDiagram-v2
  [*] --> NOT_PUBLISHED
  NOT_PUBLISHED --> PUBLISHING
  PUBLISHING --> ACTIVE: 已验证公开身份声明
  ACTIVE --> ROTATING
  ROTATING --> ACTIVE: 已验证 Key Rotation
  ACTIVE --> REVOKED: 后续协议能力
~~~

另一维度是身份**查询结果**，至少包含：

~~~text
published(identity, proof, observation)
not-published(bapId, coverageEvidence)
unknown(bapId, reason, lastObservation?)
~~~

`NOT_PUBLISHED` 只在公开查询已证明覆盖充分且明确无有效身份时使用；`UNKNOWN` 是查询证据不足，不将它塞入 Identity 生命周期作为已确认业务事实。隔离模拟的 `stored/empty` 只在测试 scope 中有效。

另一维度是**操作和链上交易状态**：Review、钱包签名、准备、广播、网络接收、公共索引、入块及重组需要独立表达。任何 HTTP 同步成功或 Wallet 回执都不能直接等于最终链上事实。前端操作过程和后端证据验证分别由实现设计负责。

## 7. 领域事件及其可信度

| 事件 | 何时产生 | 能否直接证明链上已生效 |
| --- | --- | --- |
| `IdentityPublicationRequested` | 用户确认发布意图 | 否 |
| `WalletTransactionPrepared` | 原交易已签名并保存 | 否 |
| `BroadcastResultObserved` | Wallet/网络返回可追溯回执 | 需要独立核实 |
| `IdentityPublicationVerified` | 验签及公开 BAP 事实充分 | 是，附网络和来源 |
| `ProfileUpdateVerified` | 有效资料交易被核实 | 是，附交易与版本 |
| `IdentityKeyRotatedVerified` | 轮换与历史路径核实 | 是，附旧/新路径引用 |
| `ArtifactBindingVerified` | Artifact 上下文按公开契约验证 | 取决于待验证的 Binding 协议 |

领域事件携带来源范围、交易标识、签名验证结果及观测时点；不以本地布尔值替代原始证据。跨上下文消费需幂等、可重放。

## 8. 跨端协作与数据所有权

- **前端 Application**：钱包连接、用户 Review、冻结业务快照、签名与广播、持久化恢复日志、同步后查询公开状态；不能决定公共身份是否存在。
- **后端 Application/Domain**：验证 rawTx、TxID、BAP 签名归属及历史密钥，核对真实网络来源和查询覆盖；维护可重建投影。
- **Artifact**：处理 Current Binding、Origin、ownership 和编号；Identity 只读其结果。
- **Explorer**：聚合跨上下文公共查询，不通过用户路由参数赋予编辑权限。
- **契约**：使用[Contracts](../../contracts/README.md)的 API/BDD 入口，签名与索引缺口仍见[核心认知 §12](../../核心认知.md#12-待确认)。

## 9. 验收映射（供前后端分别实现）

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
| BAP 公共索引覆盖足以证明未发布的条件 | Identity / Indexer | coverage 定义、服务异常和全历史样例 |
| Binding 创建、替换、撤销、双向唯一及转让后重验协议 | Artifact / Indexer | 可重放链上事件与冲突/重组实验 |
| Inscription Number、Origin、主链/重组相关 API | Indexer | 真实输出和重组样例 |
| Rotation 历史签名生效顺序 | BAP 实现 | 历史交易与密钥路径验证 |

以上属于开发前待关闭的技术契约，不能因为本领域设计完成就记为生产可用。
