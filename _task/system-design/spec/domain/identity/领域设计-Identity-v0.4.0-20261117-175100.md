# Identity 领域设计（OwnWord 统一目标 v0.4.0）

> 状态：needs-review。本文负责用例编排、上下文责任、领域端口与验收映射；术语、实体/属性、关系、业务状态、事件和不变量统一由[核心认知](../../核心认知.md)定义。具体接口与代码映射见[前端](../../frontend/identity/README.md)、[后端](../../backend/identity/README.md)和[Contracts](../../contracts/README.md)。本文件不作为第二份产品事实来源。

## 1. 领域目标与上下文边界

Identity Application 组合 Wallet 本人身份管理、用户 Review、公共核验和原执行恢复。Wallet/Transaction/Chain Query 的协作见[支撑域](../supporting/README.md)；稳定责任见[核心认知 §5.4](../../核心认知.md#54-支撑能力与产品领域的责任)。

Identity 负责自身资料和签名归属用例，消费 Artifact 的关联摘要；公共主页由 Explorer 组合多领域查询。依赖方向见 [Context Map](../上下文映射-v0.4.0-20261117-175100.md)，本文件不把 Content/Artifact/Relationship 放入 Identity 聚合。

## 2. 通用语言

本文件直接使用核心认知中的命名，通过下表定位定义；不再维护同名释义表。

| 所用概念 | 唯一权威 |
| --- | --- |
| BapId、BapIdentity、BapProfile | [核心认知 §2、§7.2–7.3](../../核心认知.md#72-bapidentity) |
| IdentityKeyHistory、IdentitySignatureProof、IdentityResolution、WalletIdentityState | [核心认知 §7.10](../../核心认知.md#710-identity-证明与查询模型) |
| ProfileCompleteness、业务生命周期及公共查询 | [核心认知 §9.2](../../核心认知.md#92-identity) |
| Binding、Origin 与 Artifact | [核心认知 §7.6–7.7](../../核心认知.md#77-identitynftbinding) |

## 3. 主要 Use Case（跨端共用）

功能定义与输入/业务结果以[核心认知 F-ID-01~05](../../核心认知.md#61-mvp)为准；下表只映射应用编排。

| 功能引用 | 应用用例 | 主要协作 |
| --- | --- | --- |
| F-ID-01 | ResolveMyIdentity | 并行读取 WalletIdentityPort 与 PublicIdentityResolver，组合资料映射；按核心认知 §9.2.4 分流 |
| F-ID-02 | PublishIdentity | Review → WalletExecutionPort → 执行记录/同步 → 公共回读 |
| F-ID-03 | UpdateBapProfile | Profile Mapper → Review → Wallet 资料能力 → 子交易记录/回读 |
| F-ID-04 | RotateIdentityKey | Wallet 轮换能力 → 原执行跟踪 → PublicBapHistoryResolver 核验 |
| F-ID-05 | GetPublicIdentity | 公共解析与来源覆盖 → Profile/Proof 读模型 |
| Explorer 组合用例 | ResolveByInscriptionNumber | Artifact 编号/Origin/Current Binding 查询 → F-ID-05；不作为 Identity 内部命令 |

上述是逻辑协作，不要求前后端复制同名聚合或钱包内部状态机。

## 4. 战术模型与聚合

模型分类、聚合根、属性和事实源统一见[核心认知 §7](../../核心认知.md#7-实体与属性)，关系基数/唯一定位统一见[§8](../../核心认知.md#8-关系)。本应用通过端口使用 E-ID-01/E-ID-02、V-ID-02/03 与 Q-ID-01/02，不根据数据库或 DTO 新建同名业务定义。

命令侧调用 Wallet 管理能力；查询侧构建 Identity/Profile/Proof 视图。交易支撑负责执行和证据关联，Artifact 负责 Binding；Identity 不双写另一个 Current 关系。是否同库或同事务由实现设计决定，不能改变核心模型。

### 4.1 Identity 与 Profile 字段归属

字段定义以[核心认知 ID-A01~08、PR-A01~06](../../核心认知.md#72-bapidentity)为准；DTO/Schema.org 命名转换分别见[前端资料映射](../../frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md#21-资料映射)与[Java 字段映射](../../backend/identity/实现设计-Identity-v0.4.0-20261117-175100.md#32-identity-与-profile-的类型字段边界r-03)。类型声明的待确认策略统一见核心认知 §12.7。

## 5. 领域行为与业务不变量

[核心认知 §10.2](../../核心认知.md#102-identity)保存 ID-01~12 的规则索引，本节只分配执行责任。

| 核心规则引用 | 执行责任 |
| --- | --- |
| ID-01/02/03/12 | Identity Application、Profile Mapper 与公共查询 |
| ID-04/05 | Identity Proof / 历史归属验证，业务用例消费结果 |
| ID-06/07/08 | Artifact 验证与查询端口，Identity 仅读取 |
| ID-09 | 全部公共查询 Adapter 与读模型 |
| ID-10/11 | Wallet Adapter、业务 Review 和原执行恢复 |

## 6. 状态、钱包管理与公共查询

### 6.1 业务生命周期

状态集合、转换、初始/异常/未来能力以[核心认知 §9.2](../../核心认知.md#92-identity)及其 PlantUML 为准；领域文件不维护独立状态机。

### 6.2 状态的责任与使用

WalletIdentityPort 提供 Q-ID-02，PublicIdentityResolver 提供 Q-ID-01，Profile Mapper 派生 V-ID-04；Application 按核心认知 §9.2 组合，UI 只消费结果。传输 scope/kind 的具体转换归[前端公共查询映射](../../frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md#22-公共查询映射)，JSON/错误字段归 Contracts 与后端 Adapter，不在 Domain 重列 DTO 状态。

### 6.3 本人身份操作分流

分流条件与边界统一见[核心认知 §9.2.4](../../核心认知.md#924-本人操作与异常边界)。本用例先读取钱包和未决执行，再形成可供 Review 的应用结果；对所选 Wallet Action 的实际接口限制由[钱包实现设计](../../frontend/supporting/实现设计-钱包与交易执行-v0.4.0-20261118-164032.md)验证。

### 6.4 执行与恢复

~~~plantuml
@startuml
actor User
participant "Identity Application" as App
participant "Backend Transaction" as Tx
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

具体钱包调用、材料与恢复限制见[钱包实现设计](../../frontend/supporting/实现设计-钱包与交易执行-v0.4.0-20261118-164032.md)；原交易校验与查询接入见[Java 实现设计](../../backend/supporting/实现设计-链与Ordinal查询-v0.4.0-20261118-164032.md)。本序列是用例协作，不另定义业务生命周期或钱包状态。

## 7. 领域事件及其可信度

事件定义、触发条件和证据级别统一见[核心认知 EV-ID-01~08](../../核心认知.md#711-identity-相关领域事件)。本用例仅映射生产与消费职责。

| 事件引用 | 生产方 | 主要消费方 |
| --- | --- | --- |
| EV-ID-01 | Wallet Adapter | Identity Application / Review |
| EV-ID-02 | Identity Application | Backend Transaction |
| EV-ID-03/04 | Wallet / Transaction Adapter | 执行日志与恢复服务 |
| EV-ID-05/06/07 | 公共解析与历史验证 | Identity/Profile 投影及业务回读 |
| EV-ID-08 | Artifact | Identity / Explorer 查询组合 |

## 8. 跨端协作与数据所有权

### 8.1 领域端口（逻辑接口，不等于新增 HTTP API）

| 端口 | 用途与失败语义 |
| --- | --- |
| `WalletIdentityPort` | 读取本人身份，委托发布、资料更新和轮换；由 Frontend Wallet 适配，不持有私钥 |
| `WalletExecutionPort` | 委托高层 Action 或支持的两阶段执行，并恢复原 reference / TxID，见支撑域 |
| `PublicIdentityResolver` | 返回公共身份及来源/覆盖；上游 404 不能直接变为 NOT_PUBLISHED |
| `PublicBapHistoryResolver` | 读取初始化、Rotation、冲突与重组证据，服务历史签名归属；不承担本人首次发布许可 |
| `OperationRecoveryRepository` | 保存和恢复同一身份、scope、操作意图及实际交易；不是新的身份权威存储 |
| `SigningPathAt / RotationHistoryResolver` | 验证签名发生时的有效密钥和链序；历史不足或冲突返回 UNKNOWN / CONFLICT |
| `CurrentBindingQuery` | 只读 Artifact 的有效关联摘要，不双写 Binding |

历史归属端口消费[核心认知 §7.10](../../核心认知.md#710-identity-证明与查询模型)的证据要求；实际生效编码与交易向量关闭条件见其 §12.8，不在本文件另定验签状态。

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

待确认产品/协议事实统一见[核心认知 §12](../../核心认知.md#12-待确认)，下表仅记录实施映射；详细参数和 fixtures 进入各端设计/Contracts。

| 核心依据 | 实施拥有方 | 所需证据 |
| --- | --- | --- |
| §12.2 全交易身份签名 | Wallet Adapter / metanet4j | 各类原交易与独立验证向量 |
| §12.7 类型声明 | 产品 / Protocol / Wallet Adapter | 类型映射、授权与实际声明样例 |
| §12.8 公共覆盖与历史归属 | Identity / Indexer / Verifier | 覆盖定义、轮换、同块顺序、未确认与 reorg 样例 |
| §12.1/§12.4 编号与 Binding | Artifact / Indexer | 公开关联、Origin、编号与重组 fixtures |
| §9.2.4 原执行恢复 | Frontend Wallet / Backend Transaction | 固定版本的拒绝、中断、丢回执与重启恢复样例 |

上述实施门禁保持开放；文档收敛不代表技术契约、真实钱包或主网已经验收。
