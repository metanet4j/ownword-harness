# Ownword 产品设计文档

状态：`active`

本目录把《设计文档 V6》拆成核心认知、页面风格和 11 个可独立验收的小版本。

## 文档权威层级

1. [`core-cognition.md`](./core-cognition.md) 是稳定产品事实、领域事实和跨版本约束的唯一准确来源。
2. [`visual-style.md`](./visual-style.md) 是页面展示、响应式、i18n 和主题规则的唯一展开位置；涉及领域语义时引用核心认知。
3. [`releases/`](./releases/) 只定义版本目标、范围、流程和验收，不重新定义核心事实或页面风格。
4. [`../设计文档V6.md`](../设计文档V6.md) 原样保留，作为拆分来源和历史设计记录，不再作为后续实现的规范入口。

发生冲突时，领域事实服从核心认知，页面展示服从风格文档，版本是否包含某项能力服从对应版本文档。先修正错误落点，不在多个位置同步复制同一事实。

## DRY 规则

| 信息 | 唯一落点 |
| --- | --- |
| 术语、实体、属性、关系、状态、全局约束 | `core-cognition.md` |
| 页面视觉、布局、组件展示、i18n、主题 | `visual-style.md` |
| 单版本目标、范围、流程、异常、验收、排除项 | 对应版本文档 |
| API、表结构、任务和执行命令 | 后续详细设计或实现计划 |

版本文档需要核心事实时，使用链接，不复制属性表、状态全集或协议定义。

## 版本地图

| 版本 | 主题 | 对外阶段 |
| --- | --- | --- |
| [`v0.1`](./releases/v0.1-product-foundation.md) | 产品壳、i18n、Light/Dark | MVP |
| [`v0.2`](./releases/v0.2-wallet.md) | Wallet | MVP |
| [`v0.3`](./releases/v0.3-identity-resolution.md) | Identity 解析 | MVP |
| [`v0.4`](./releases/v0.4-identity-profile.md) | Identity Profile | MVP |
| [`v0.5`](./releases/v0.5-words-draft.md) | Words Draft | MVP |
| [`v0.6`](./releases/v0.6-words-publish.md) | Words Publish | MVP |
| [`v0.7`](./releases/v0.7-public-identity.md) | Public Identity | MVP |
| [`v0.8`](./releases/v0.8-relationship.md) | BAP ID Lookup、Relationship | 第二阶段 |
| [`v0.9`](./releases/v0.9-artifact-create.md) | Artifact 创建 | 第三阶段 |
| [`v0.10`](./releases/v0.10-artifact-resolve.md) | Artifact 标识、Inscription Number Lookup | 第三阶段 |
| [`v0.11`](./releases/v0.11-artifact-lifecycle.md) | Artifact 生命周期 | 第四阶段 |

首个对外 MVP 为 `v0.1-v0.7` 的合集。它不提供用户输入式 BAP ID Lookup、Inscription Number Lookup 或 Relationship。

## 维护流程

1. 新证据先更新 `core-cognition.md`。
2. 搜索该事实是否出现在其他新文档；除必要 UI 示例外，改成链接。
3. 核心认知影响版本行为时，再更新对应版本文档。
4. 页面展示变化只更新 `visual-style.md`；若变化隐含领域语义，先更新核心认知。
5. 未经确认的协议、endpoint、状态映射统一标记 `待确认`。
