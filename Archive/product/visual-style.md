# Ownword 页面风格规范

状态：`canonical-presentation`

本文是页面风格、组件展示、响应式、i18n 和主题的唯一展开位置。领域含义、标识语义和状态全集以 [`core-cognition.md`](./core-cognition.md) 为准；发生冲突时，先服从核心认知。

## 设计方向

核心感受：

```text
Weight
New Territory
```

视觉词汇：

```text
Identity
Signature
Proof
Metal
Artifact
Ledger
Territory
Steel
Titanium
Graphite
Silver
Engraving
Stamp
Seal
```

避免：

```text
Crypto Casino
Cyberpunk
Neon
NFT Marketplace Card
```

页面应安静、稳定、可扫描。金属感表达分量、责任、稳定和可验证性，不依赖高饱和渐变或装饰光效。

## 信息层级

Identity 页面首屏先回答“这是谁”：

```text
Name
BAP ID                             Copy
Profile type
Description
Primary action
```

Artifact 页面首屏先回答“编号是什么、关联谁”：

```text
Inscription Number                 Copy
Associated Identity
BAP ID                             Copy
Artifact content
Status
```

Content 页面先展示正文与作者，再渐进展示 Proof。协议字段不应抢占普通阅读路径。

`Identity Artifact` 使用 Seal、Badge、Metal Card、Medal 或 Artifact 视觉隐喻，不使用交易市场商品卡作为默认隐喻。

## 主标识展示

主标识语义见[核心认知：术语与命名](./core-cognition.md#术语与命名)。

### BAP ID

- Identity Detail、My Identity、Public Identity 默认展示完整值。
- 窄屏和紧凑列表允许中间省略，例如 `8F3a...91Bc`。
- Copy 始终复制完整原值，不复制缩略字符串。
- BAP ID 使用主信息层级，不隐藏在菜单、Proof 或折叠区。

### Inscription Number

- 已分配时显示 `#<number>`，例如 `#165`。
- Copy 复制原始十进制字符串，例如 `165`。
- 未确认时显示 `Pending confirmation`，不显示 `#0`、本地编号或预测值。
- reorg 导致变化时使用 Warning 状态，并提供刷新或重新验证入口。

### Proof 标识

Inscription ID、Ordinal Number、Origin、Current Outpoint 和 TxID 放入 Details / Proof。列表可缩略，详情可展开完整值，Copy 始终使用原值。

复制成功显示轻量 `Copied`，不改变组件尺寸。复制失败保留原值并显示 `Couldn't copy`。仅图标按钮必须有可访问名称；陌生图标提供 Tooltip。

## 组件体系

| 领域 | 组件 | 展示职责 |
| --- | --- | --- |
| Wallet | `WalletConnect`、`WalletStatus` | 连接入口、当前状态、Wallet 与 Account |
| Identity | `IdentityReference`、`IdentityCard`、`BapIdDisplay`、`IdentityLookup` | 身份引用、完整资料、主标识、精确查找 |
| Content | `MarkdownEditor`、`MarkdownPreview`、`ContentCard`、`ContentStatus`、`ContentProof` | 编辑、预览、摘要、产品状态、证明 |
| Artifact | `ArtifactCard`、`ArtifactStatus`、`InscriptionNumberDisplay`、`ArtifactIdentifierDetails` | Artifact、关联状态、主编号、验证标识 |
| Blockchain | `TransactionStatus`、`TransactionReference`、`SignatureBadge` | 链上状态、交易引用、签名结果 |

`IdentityReference` 是全站统一身份引用：

```text
[Avatar] Alice
         BAP ID  8F3a...91Bc  Copy
```

Post 作者、Publish Review、Relationship 和交易详情复用同一结构。

`SignatureBadge` 使用 `Signed` 或 `Signature valid`。禁止使用含义过宽的 `Verified` 或 `Verified Identity`。

`ContentStatus` 与 `TransactionStatus` 必须是两个组件。例如 Content 可以是 `Published`，同时 Transaction 仍为 `Confirmation pending`。

组件组合：

```text
ContentCard
  IdentityReference
  ContentStatus
  SignatureBadge

ContentProof
  IdentityReference
  BapIdDisplay
  SignatureBadge
  TransactionReference
  TransactionStatus
```

## 页面结构

### App Shell

Header 承载 Wallet 状态、Language、Theme，以及版本开放后才出现的查找入口。Header 不展示底层 provider discovery、协议状态机或完整交易信息。

### Identity

```text
Identity header
  Avatar
  Name
  BAP ID + Copy
  Type
  Description

Primary navigation
  Words
  Artifacts
  Relationships
```

未进入当前版本的导航项不显示空入口。

### Write

```text
Signing as + IdentityReference
Write / Preview tabs
Markdown editor or preview
Draft status
Import Markdown
Review
```

编辑页面使用 `Write`、`Preview`、`Draft`、`Review`。不显示 `Broadcast`、`Push TX` 或 `Submit Transaction`。

### Public Post

正文是主区域。作者信息紧邻正文；Proof 默认可折叠，但签名摘要保持可见。高影响发布动作进入独立 Review。

### Identity Artifact

Artifact 内容、Inscription Number、Associated Identity 和状态构成主区域。Inscription ID、Ordinal Number、Origin、Current Outpoint 放入 Details / Proof。

## 响应式

Desktop 可并列：

```text
Content | Identity | Proof
```

Mobile 默认纵向：

```text
Identity
Content
View Proof
```

规则：

- 固定格式控件使用稳定尺寸和响应式约束，动态状态不得推动相邻布局跳动。
- 长 BAP ID、TxID、Origin、Outpoint 允许中间省略，但必须提供完整查看和 Copy。
- 中英文、最长错误文案、窄屏和 Wallet 弹回状态都不得造成重叠。
- 详情页优先换行或缩略协议值，不能缩小到无法阅读。

## 交互与文案

高影响链上操作统一：

```text
User Intent
Review
Wallet Confirmation
Progress
Result
```

Wallet Confirmation 属于 Wallet，不设计成站内伪页面。

主要动作统一使用：

| 行为 | 文案 |
| --- | --- |
| 连接 Wallet | `Connect Wallet` |
| 创建 Identity | `Set Up Identity` / `Create Identity` |
| 修改 Profile | `Edit Profile` / `Save Changes` |
| 写内容 | `Write` |
| 进入发布确认 | `Review` |
| 发布 | `Sign & Publish` |
| 创建 Artifact | `Create Artifact` |
| 设置当前 Artifact | `Set as Current` |
| 更换 Artifact | `Change Artifact` |
| 重试 | `Try Again` |
| 复制 | `Copy` |

结果文案分三类：

```text
Success: Connected / Identity ready / Saved / Published / Artifact created / Copied
Cancelled: Connection cancelled / Publishing cancelled / Creation cancelled
Failed: Connection failed / Couldn't publish / Couldn't create artifact / Couldn't copy
```

异常必须包含：发生了什么、影响什么、下一步做什么。状态不能只靠颜色表达。

## 国际化

默认语言：

```text
en       English
zh-CN    中文
```

规则：

- 产品文案全部使用 i18n key，组件中不散落硬编码英文或中文。
- 没有已保存偏好时使用 English；不根据浏览器语言覆盖默认语言。
- Header 与 Settings 共享同一语言偏好；用户显式选择持久化。
- BAP ID、Inscription Number、Inscription ID、Ordinal Number、Origin、Outpoint、TxID、签名和用户内容不翻译。
- 协议数字不加本地化千位分隔符。
- 日期与相对时间使用当前 locale；Proof 可查看 ISO/UTC 原值。
- 用户 Markdown、Profile 名称和链上协议字段不自动翻译。

## 主题

提供：

```text
light
dark
```

组件只使用语义 Token：

| Token | Light | Dark | 用途 |
| --- | --- | --- | --- |
| `canvas` | `#F4F5F6` | `#101213` | 页面背景 |
| `surface` | `#FFFFFF` | `#1A1D1F` | 主要内容面 |
| `surface-raised` | `#E9ECEF` | `#252A2D` | 菜单、浮层、工具面 |
| `text-primary` | `#171A1C` | `#F3F5F6` | 标题、主标识 |
| `text-secondary` | `#5D6870` | `#ADB7BD` | 辅助信息 |
| `border` | `#C7CDD1` | `#41484D` | 分隔和输入边界 |
| `metal-accent` | `#66747C` | `#BCC6CB` | 金属刻印和 Proof |
| `action` | `#006B5F` | `#46C7B4` | 主操作和焦点关联 |
| `status-success` | `#18794E` | `#4CC38A` | 成功 |
| `status-warning` | `#8A6100` | `#F2C14E` | 待确认和 reorg |
| `status-error` | `#B42318` | `#FF7068` | 失败 |
| `focus-ring` | `#005FCC` | `#7CB7FF` | 键盘焦点 |

Header 使用 Sun / Moon 图标切换并提供可访问名称与 Tooltip；Settings 提供相同选项。两处共享偏好并即时生效。

首次访问可跟随 `prefers-color-scheme`；用户显式选择优先并持久化。无法读取系统偏好时回退 Light。

## 验收基线

- Light 与 Dark 正文和交互文字达到 WCAG AA；图标与非文字控件按对应标准验证。
- BAP ID、Inscription Number 和 Copy 在两套主题中同等突出。
- English 与中文覆盖 Desktop、Mobile、长文案、错误、Pending 和空状态。
- 主题、语言和复制反馈不改变用户内容、协议字段、实体 ID、查询结果或交易。
- 键盘可到达所有交互控件；焦点可见；图标按钮有可访问名称。
- Copy、Pending、Failed 等动态内容不改变固定控件尺寸，不造成页面跳动或文字重叠。

排版字体、字号比例、间距比例、圆角和动效参数尚未在 V6 中形成稳定规范，进入原型前另行确认；不得在版本文档中各自定义。

