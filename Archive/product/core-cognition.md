# Ownword 核心认知

状态：`canonical`

本文是 Ownword 稳定产品事实、领域事实和跨版本约束的唯一准确来源。版本文档与页面风格文档只能引用，不得建立平行定义。

## 结构

Ownword 是以 BAP Identity 为中心的内容、关系与 Identity Artifact 平台。

```text
Wallet
  controls
Identity
  publishes Content
  relates to Identity
  associates with Identity Artifact
Bitcoin
  records published facts
```

系统分四层：

| 层 | 职责 | 事实归属 |
| --- | --- | --- |
| 展示层 | 页面、编辑、预览、复制、Proof、i18n、主题 | 不产生链上事实 |
| 产品层 | 用户流程、产品状态、Binding 业务规则 | 本文定义稳定规则 |
| 集成层 | `WalletProvider`、`IdentityProvider`、`ContentProtocol`、`RelationshipProtocol`、`OrdinalProvider`、`BlockchainIndexer`、`IdentifierResolver` | 适配外部能力 |
| 外部事实层 | Wallet、BAP、BitcoinSchema、1Sat Ordinals、Bitcoin | 对协议和链上事实负责 |

业务组件依赖集成接口，不直接依赖 Yours Wallet API。Yours Wallet 是首个 Wallet 实现，不是产品领域边界。

Bitcoin 是已发布 Identity、已发布 Content、签名、Ordinal 所有权和 Transaction 的最终事实来源。Indexer 解析 Inscription Number、Ordinal Number、Origin、Current Outpoint 和 MAP 合并结果。数据库保存 Draft、索引、缓存、查询材料、UI 偏好与交易跟踪信息；缓存不是链上最终事实。

本文是设计知识的唯一事实源；Bitcoin 与协议实现仍是运行时事实源。二者职责不同。

证据：[`设计文档 V6`](../设计文档V6.md)、[`Yours Wallet Provider API`](../../reference/yours-wallet-main/yours-wallet-main/docs/provider-api.md)。

## 术语与命名

| 术语 | 准确定义 | 命名规则 |
| --- | --- | --- |
| Wallet | 管理密钥、资产、权限和交易能力的非托管钱包 | 不称为 User Account |
| BAP Identity | 由 BAP 标识并由 Wallet 控制的主权身份 | UI 简称 `Identity` |
| BAP ID | 从稳定 Identity 根确定性派生的公开身份标识 | 主身份标识；不可编辑 |
| BAP Profile | Identity 对外展示的信息 | UI 使用 `Profile` |
| Content | Identity 签署并发布的内容 | UI 入口使用 `Words` |
| Draft | 尚未发布的本地内容 | 可修改、可恢复 |
| Published Content | 已发布到 Bitcoin 的内容版本 | 不通过普通编辑覆盖 |
| Relationship | 两个 BAP Identity 之间的协议关系 | 双方始终用 BAP ID 标识 |
| Follow | Identity 到 Identity 的单向关系 | 使用 BitcoinSchema 语义 |
| Friend | 两个 Identity 之间的双向关系 | 使用 BitcoinSchema 语义 |
| 1Sat Ordinal | 由 1-satoshi output 承载和转移的链上资产 | Artifact 底层模型 |
| Identity Artifact | 与 BAP Identity 关联的 1Sat Ordinal | 用户侧名称；领域实体名为 `BapNFT` |
| Binding | Identity 与 Identity Artifact 的产品关联 | 不等同于创建者、签名者或所有者 |
| Inscription ID | 一次 Inscription 所在的 `txid_vout` | 定位具体 Inscription |
| Inscription Number | Inscription 确认后按链上顺序获得的十进制编号 | Artifact 主要记忆入口；可能受 reorg 影响 |
| Ordinal Number | 目标 satoshi 的精确十进制编号 | 使用字符串保存 |
| Origin | 当前 1-satoshi 转移链的起点 Outpoint | 当前有效链的定位依据，不是永久全球 ID |
| Current Outpoint | Ordinal 当前所在交易输出 | Transfer 后变化 |
| Transaction | Bitcoin 交易记录 | 与产品状态分开表达 |
| Proof | 支持独立验证的签名、协议和交易信息 | 不等于现实身份认证 |

UI 优先使用 `Identity`、`Profile`、`Words`、`Identity Artifact`、`Publish`、`Signature`、`Transaction`。`BAP`、`B/MAP/AIP`、`Ordinal`、`Outpoint`、`BEEF` 放入 Details 或 Proof。`BAP ID` 与 `Inscription Number` 是主标识，不降级为隐藏协议细节。

禁止把密码学签名状态命名为 `Verified Identity`。签名验证只证明指定 Identity 对内容或行为签名，不证明现实人物身份。

证据：[`BAP README`](../../reference/bap-master/bap-master/README.md)、[`BAP Protocol`](../../reference/bap-master/bap-master/PROTOCOL.md)、[`BitcoinSchema Social Schema`](../../reference/schema-master/schema-master/docs/social_schema.md)、[`1Sat Ordinals`](../../reference/1sat-ordinals-master/1sat-ordinals-master/README.md)。

## 持久化数据模型

### BAPIdentity

| 属性 | 类型 | 唯一 | 可变 | 必填条件 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `bapId` | string | 是 | 否 | 始终 | 稳定 BAP ID |
| `rootPath` | string | 条件唯一 | 否 | 始终 | Identity 根路径 |
| `currentPath` | string | 否 | 是 | 始终 | 当前签名路径 |
| `previousPath` | string | 否 | 是 | Rotation 后 | 上一签名路径 |
| `type` | enum | 否 | 是 | 始终 | `PERSON` / `ORGANIZATION` |
| `status` | enum | 否 | 是 | 始终 | 见“持久化状态” |
| `publishTxid` | string | 是 | 否 | 发布后 | Genesis Transaction |
| `createdAt` | datetime | 否 | 否 | 始终 | 创建时间 |

### BAPProfile

| 属性 | 类型 | 唯一 | 可变 | 必填条件 | 产品限制 |
| --- | --- | --- | --- | --- | --- |
| `bapId` | string | 是 | 否 | 始终 | 关联 Identity |
| `name` | string | 否 | 是 | 始终 | 最长 100 字符 |
| `image` | URI | 否 | 是 | 可选 | 最长 2048 字符 |
| `description` | string | 否 | 是 | 可选 | 最长 1000 字符 |
| `type` | enum | 否 | 是 | 始终 | `Person` / `Organization` |
| `updatedAt` | datetime | 否 | 是 | 始终 | 更新时间 |

### Content

| 属性 | 类型 | 唯一 | 可变 | 必填条件 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `id` | UUID | 是 | 否 | 始终 | 本地 ID |
| `txid` | string | 是 | 否 | 发布后 | Transaction |
| `authorBapId` | string | 否 | 否 | 始终 | Author |
| `type` | enum | 否 | 发布后不可变 | 始终 | 首期为 `POST` |
| `content` | text | 否 | 发布后不可变 | 始终 | 首期为 Markdown |
| `mediaType` | string | 否 | 发布后不可变 | 始终 | 首期为 `text/markdown` |
| `encoding` | string | 否 | 发布后不可变 | 始终 | 首期为 `UTF-8` |
| `status` | enum | 否 | 是 | 始终 | 产品状态 |
| `publishedAt` | datetime | 否 | 否 | 发布后 | 发布时间 |

### ContentRevision

| 属性 | 类型 | 必填条件 | 说明 |
| --- | --- | --- | --- |
| `contentId` | UUID | 始终 | 当前版本 |
| `rootContentId` | UUID | 始终 | 原始 Content |
| `previousContentId` | UUID | 非首版 | 上一版本 |
| `revisionNo` | int | 始终 | 版本号 |
| `txid` | string | 发布后 | 链上交易 |

### Relationship

| 属性 | 类型 | 必填条件 | 说明 |
| --- | --- | --- | --- |
| `fromBapId` | string | 始终 | 发起 Identity |
| `toBapId` | string | 始终 | 目标 Identity |
| `type` | enum | 始终 | `FOLLOW` / `FRIEND` 等协议关系 |
| `txid` | string | 链上关系发布后 | Transaction |
| `status` | enum | 始终 | 精确枚举待 v0.8 详细设计确认 |
| `createdAt` | datetime | 始终 | 创建时间 |

### BapNFT

| 属性 | 类型 | 唯一 | 可变 | 必填条件 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `inscriptionId` | string | 是 | 否 | 始终 | `txid_vout` |
| `inscriptionNumber` | decimal string | 条件唯一 | reorg 时可变 | 确认后 | 确认前为 `null` |
| `ordinalNumber` | decimal string | 是 | 否 | 解析后 | 精确 satoshi 编号 |
| `origin` | string | 条件唯一 | 当前 1Sat 链内不变 | 始终 | Origin Outpoint |
| `currentOutpoint` | string | 是 | 是 | 始终 | Transfer 后更新 |
| `currentSequence` | int | 否 | 是 | 可选 | 当前链位置 |
| `contentType` | string | 否 | 否 | 始终 | Inscription MIME type |
| `contentUri` | string | 否 | 否 | 始终 | 优先可解析的 `1sat://` / OrdFS URI |
| `owner` | string | 否 | 是 | 始终 | 当前 Output 控制者，不是 BAP ID |
| `status` | enum | 否 | 是 | 始终 | Artifact 产品状态 |
| `createdAt` | datetime | 否 | 否 | 始终 | 创建时间 |

### IdentityNFTBinding

| 属性 | 类型 | 必填条件 | 说明 |
| --- | --- | --- | --- |
| `id` | UUID | 始终 | Binding ID |
| `bapId` | string | 始终 | Identity |
| `ordinalOrigin` | string | 始终 | Artifact 当前有效 1Sat 链 |
| `status` | enum | 始终 | `ACTIVE` / `HISTORICAL` / `INVALID` |
| `bindTxid` | string | 取决于 Binding 事实方案 | 待确认 |
| `boundAt` | datetime | 始终 | 建立时间 |
| `unboundAt` | datetime | 解绑后 | 解绑时间 |

### BlockchainTransaction

统一表示 Identity 创建、Profile 更新、Content 发布、Artifact 创建、Artifact 变更和 Key Rotation 对应的链上 Transaction。至少承载 txid、动作类型、关联实体、产品进度与链上进度；物理字段名和 Wallet/Indexer 状态映射待实现前确认。

`WalletConnection` 是运行时会话，不是 User Account，也不是 BAP Identity。Locale、Theme 和 Copy 状态属于 UI 偏好或瞬时状态，不进入上述领域模型。

证据：[`设计文档 V6：属性`](../设计文档V6.md#8-属性)、[`BAP README`](../../reference/bap-master/bap-master/README.md)、[`Yours Wallet Provider API`](../../reference/yours-wallet-main/yours-wallet-main/docs/provider-api.md)、[`OrdFS`](../../reference/1sat-ordinals-master/1sat-ordinals-master/ordfs.md)。

## 持久化关系

| 主体 | 关系 | 客体 | 基数 | 定位与约束 |
| --- | --- | --- | --- | --- |
| BAPIdentity | Profile | BAPProfile | `1 : 0..1` | 用 `bapId` 定位 |
| BAPIdentity | Publish | Content | `1 : N` | Content 保存 `authorBapId` |
| Content | Revision | Content | `1 : N` | 新版本引用原始与上一版本 |
| BAPIdentity | Relationship | BAPIdentity | `N : N` | 双方只保存 BAP ID |
| BAPIdentity | Artifact | BapNFT | `1 : N` | 通过独立 Binding 关联 |
| BAPIdentity | Current Artifact | BapNFT | `1 : 0..1` | 同一 BAP ID 最多一个 `ACTIVE` Binding |

Relationship 的查找输入可以来自 BAP ID；未来也可先由 Inscription Number 解析出 Identity。但持久化目标只能是 BAP ID，不能用 Inscription Number、名称、owner 或 signer 替代。

Artifact 的 `creator`、签名者、owner 与 Current Binding 是四种不同关系，任何一种都不能自动推出另一种。Identity 可以没有 Artifact；Artifact 也可以没有有效 Binding。

Binding 是产品关系，不是已由 BAP 或 1Sat 协议定义的固有关系。Binding 的最终链上或数据库权威归属仍为 `待确认`；确认前不得把临时实现写成协议事实。

## 持久化状态

### BAPIdentity

```text
NOT_PUBLISHED -> PUBLISHING -> ACTIVE
ACTIVE -> ROTATING -> ACTIVE
ACTIVE -> REVOKED
```

`REVOKED` 属于后续能力。Rotation 改变活动签名路径，不改变 BAP ID。

### Content

```text
DRAFT -> PUBLISHING -> PUBLISHED
PUBLISHING -> CANCELLED
PUBLISHING -> FAILED
```

取消或失败不得删除 Draft。`PUBLISHED` 与 Transaction 是否已出块是不同事实。

### Artifact 与编号解析

```text
DRAFT -> CREATING -> CREATED
NUMBER_PENDING -> NUMBER_ASSIGNED
NUMBER_ASSIGNED -> REORGED -> NUMBER_PENDING | NUMBER_ASSIGNED
```

`REORGED` 表示 Inscription Number 需要重算，不表示 Artifact 被删除。编号重算期间继续保留 Inscription ID、Origin 和 Transaction。

### IdentityNFTBinding

```text
UNBOUND | ACTIVE | HISTORICAL | INVALID
```

用户侧文案映射为 `Not Used`、`Current`、`Historical`、`Unavailable`。内部枚举不直接显示给普通用户。

### BlockchainTransaction

产品层统一语义为：

```text
BROADCAST -> SEEN -> ACCEPTED -> MINED -> IMMUTABLE
```

当前本地资料没有确认 Yours Wallet、1Sat SDK 与 Indexer 共同提供这套稳定枚举。实现必须映射真实返回值；字段名与完成判定为 `待确认`。

Wallet 的 `DETECTING`、`SELECTING`、`CONNECTING` 等是会话状态，不持久化为领域状态。

## 功能

| 功能 | 目的 | 作用对象 |
| --- | --- | --- |
| Connect Wallet | 建立非托管 Wallet 会话并获得授权能力 | WalletConnection |
| Resolve Current Identity | 计算当前 Wallet 的 BAP ID，并判断链上 Identity 是否已发布 | BAPIdentity |
| Create Identity | 发布 BAP Identity | BAPIdentity |
| Manage Profile | 创建、查看和修改公开资料 | BAPProfile |
| Display and Copy BAP ID | 让用户识别、分享和精确引用 Identity | BAPIdentity |
| Create Draft | 编写、导入、预览、保存和恢复 Markdown | Content |
| Publish Words | 由当前 Identity 签名并发布 Post | Content、BlockchainTransaction |
| View Public Identity | 通过分享链接查看 Identity 与公开 Words | BAPIdentity、Content |
| Lookup Identity | 通过完整 BAP ID 精确查找已发布 Identity | BAPIdentity |
| Manage Relationship | 建立或取消 Follow、Friend 等关系 | Relationship |
| Create Artifact | 创建并签名 Identity Artifact | BapNFT、BlockchainTransaction |
| Resolve Artifact | 解析编号、Origin、Outpoint 与关联 Identity | BapNFT、IdentityNFTBinding |
| Manage Artifact Binding | 设置、更换、解绑和验证 Current Artifact | IdentityNFTBinding |
| Transfer Artifact | 使用最新 Wallet Output 转移 1Sat Ordinal | BapNFT、BlockchainTransaction |
| Create Revision | 为已发布 Content 发布新版本并保留历史 | ContentRevision |
| Rotate Key | 更换活动签名路径并保持 BAP ID | BAPIdentity |
| Attest | 建立可验证的身份属性证明 | Attestation，模型待后续补充 |

功能是否进入某个版本，只在 [`releases/`](./releases/) 定义，不改变以上能力语义。

## 全局约束

1. 平台永不获取 Private Key、Seed Phrase 或 WIF。签名和资产操作由 Wallet 授权完成。
2. Wallet Connected 不等于应用可以自动签名。用户拒绝或关闭 Wallet 是 `Cancelled`，不是系统 `Failed`。
3. Account Switch 必须终止待签名、待发布、Artifact 创建和其他身份敏感动作，清空旧 Identity 上下文，再解析新 Identity。
4. BAP ID 不可编辑。Profile 可修改；Rotation 不改变 BAP ID。
5. BAP ID 是 Identity 主标识。对应详情页必须重点显示并支持复制完整原值；没有 Identity Artifact 也不影响身份成立、分享或建立 Relationship。
6. Inscription Number 是 Artifact 主要记忆入口。确认前为 `null`；不得用 txid、Origin 或本地序号预测。显示可加 `#`，复制值必须是无本地化格式的原始十进制字符串。
7. Inscription ID、Ordinal Number、Origin 与 Current Outpoint 含义不同，不能互换。协议标识和哈希不翻译、不加千位分隔符。
8. Identity Artifact 不等于 BAP Identity。Artifact 不是创建 Identity、编写 Words 或发布 Content 的前置条件。
9. 同一 Identity 可关联多个 Artifact，但同时最多一个 Current Artifact。
10. 只有仍可解析的 1-satoshi 链、当前所有权和有效 Binding 共同满足时，Artifact 才能作为 Current Artifact。进入大于 1 satoshi 的 Output 后，旧 Origin 不再沿链携带；重新进入 1-satoshi Output 产生新 Origin，旧 Binding 不得静默复用。
11. Transfer 前必须获取最新 `WalletOutput`。有 BEEF 时显式传入；只有显式 BEEF 与 SDK 自动 ancestry 解析都不可用并返回 `no-beef`，才按缺少 BEEF 失败处理。
12. Artifact 创建写入 1Sat Ordinals `ord` 类型所需 MAP 元数据：`app`、`type=ord`、`name`；字段值均为字符串。
13. Draft 可修改；Published Content 不可覆盖。修改必须发布新 Revision，并保留原版本。
14. 产品状态、Blockchain 状态和 Indexer 状态必须分开。未出块不等于发布失败。
15. Bitcoin 是链上事实来源；数据库缓存必须记录来源与更新时间，并允许重新解析。
16. 默认语言为 English，可切换 `zh-CN`。至少提供 Light 与 Dark。Locale 和 Theme 只改变展示，不改变 URL、实体 ID、查询语义、签名输入或链上交易。
17. 所有异常必须说明发生了什么、影响什么、用户下一步做什么。失败或取消发布不得丢失 Draft。
18. 用户侧 BAP ID Lookup 不属于首个 MVP。此版本边界不改变 BAP ID 作为稳定身份标识的领域事实。

待确认：

- Inscription Number 查询的现行生产 endpoint；旧 `public-apis.md` 已标记 Historical，不能直接作为生产契约。
- Yours Wallet `signWithBAP` 最终生成 AIP 还是 Sigma 封装；产品层暂统一称 `BAP signature`，实现前用 SDK 输出与验证器确认。
- Identity Artifact Binding 的链上或数据库权威事实归属。
- Wallet、Indexer 与 1Sat SDK 到产品 BlockchainTransaction 状态的准确映射。

证据：[`Yours Wallet AI Onboarding`](../../reference/yours-wallet-main/yours-wallet-main/docs/gitbook/ai-onboarding.md)、[`Get Ordinals`](../../reference/yours-wallet-main/yours-wallet-main/docs/gitbook/actions/get-ordinals.md)、[`Inscribe`](../../reference/yours-wallet-main/yours-wallet-main/docs/gitbook/actions/inscribe.md)、[`Transfer Ordinals`](../../reference/yours-wallet-main/yours-wallet-main/docs/gitbook/actions/transfer-ordinals.md)、[`OrdFS`](../../reference/1sat-ordinals-master/1sat-ordinals-master/ordfs.md)、[`Historical Public APIs`](../../reference/1sat-ordinals-master/1sat-ordinals-master/public-apis.md)。
