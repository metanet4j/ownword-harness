# OwnWord Design Skill Architecture

## Purpose

本文定义 OwnWord 设计事实、版本设计文档、设计系统与设计 skill 的协作方式。

OwnWord 产品事实只在核心认知中定义。版本设计文档负责把事实落实到当前版本。设计系统和 skill 提供约束、方法与执行能力，不建立新的产品事实来源。

## Architecture

```text
1. Product Truth
   _task/system-design/spec/核心认知.md
            ↓
2. Version Design Contract
   当前版本相关设计文档
            ↓
3. Binding Design System
   React Spectrum / Spectrum S2（版本指定时）
            ↓
4. Design Execution
   baoyu-design
      ├─ design-taste-frontend（按页面类型选择）
      └─ high-end-visual-design（按视觉目标选择）
            ↓
   Prototype / Preview / Verify

Implementation Guardrail:
react-spectrum skill
```

这里不是固定的 skill 流水线。Core Cognition、Version Design Contract 和 Binding Design System 先建立约束；`baoyu-design` 作为主设计执行框架；其他视觉 skill 按场景加载。

## 1. Product Truth

`_task/system-design/spec/核心认知.md` 是 OwnWord 产品、设计、原型、代码和测试的唯一事实来源（SSOT）。

它定义跨模块、跨版本必须稳定的：

- 产品定位与目标；
- 术语与命名；
- 领域实体与关系；
- 状态与全局不变量；
- 安全、协议和事实来源边界。

任何设计系统或 skill 都不得修改、补充或重新定义这些事实。缺少新的跨模块事实时，先更新核心认知，再同步下游。

## 2. Version Design Contract

当前版本设计文档把核心认知落实为：

- 页面与信息架构；
- 用户流程；
- 组件与状态；
- 视觉方向；
- 当前版本设计系统要求；
- 原型范围和验收。

版本设计文档可以定义当前版本的设计选择，但不得创建与核心认知冲突的产品事实。

例如 v0.4.0 已明确个人主页以 BAP ID 为身份核心，并继承既有品牌与 React Spectrum S2 设计系统。

## 3. Binding Design System

当当前版本设计文档已经指定 React Spectrum、Spectrum S2 或其他设计系统时，该设计系统在开始设计前即成为 binding constraint。

它约束：

- Design Token；
- 通用组件；
- 交互状态；
- 可访问性；
- 通用视觉和行为一致性。

设计 skill 不得自行重新选择另一个主设计系统，也不得用自己的默认风格覆盖已绑定的设计系统。

项目特有的 Hero、Identity 表达、Content Showcase 等可以自定义，但必须继续服从核心认知、版本设计文档和绑定设计系统的边界。

## 4. Design Execution

### baoyu-design

`baoyu-design` 是 OwnWord 高保真设计任务的主设计执行框架。

它负责：

- 理解设计任务和现有上下文；
- 加载并遵循已有 design system；
- 高保真设计和交互原型；
- 设计质量检查；
- Preview、验证和迭代。

它负责组织设计工作，但不拥有 OwnWord 产品事实，也不能覆盖当前版本已经确定的设计约束。

### design-taste-frontend

`design-taste-frontend` 是前端视觉设计 specialist，不是所有页面必须完整执行的固定步骤。

它适合强化：

- 页面设计语言判断；
- Anti-slop / anti-template；
- Typography、spacing、layout；
- Visual density；
- Motion intensity；
- Responsive mechanics；
- 前端设计 pre-flight check。

其原始定位偏向 landing page、portfolio 和 redesign，并明确不以 multi-step product UI 为主要使用场景。因此 OwnWord 按页面类型控制使用强度。

| 页面类型 | 使用方式 |
| --- | --- |
| Public Personal Homepage、Landing、Content Showcase、公开展示页 | 强使用，可用于整体视觉方向与前端设计质量 |
| Public Post Reader、内容阅读 | 中等使用，以排版、密度、响应式和细节质量为主 |
| Identity Setup、Wallet Connect | 选择性使用，采用 anti-slop、排版、响应式和检查规则，不让其重写流程与设计系统 |
| Publish Review、Wallet Confirmation、Settings、Proof / Transaction Details | 轻量使用，只吸收与清晰度、响应式、状态完整性和实现质量相关的规则 |

任何时候，`design-taste-frontend` 都不得为了视觉变化改变既定业务流程、状态机、信息优先级或已绑定设计系统。

### high-end-visual-design

`high-end-visual-design` 是强风格视觉 specialist，不是通用质量层。

它具有明确的 premium / agency / cinematic 审美倾向，包括强 typography、macro whitespace、非对称布局、复杂 motion 和特定组件造型。

仅当当前页面目标明确需要这种强视觉表达时使用，例如品牌型 Hero 或展示型页面的局部视觉探索。

不得把它的固定视觉套路全局应用到 Wallet、Publish、Settings、Proof 等任务型产品 UI，也不得覆盖 OwnWord 已定义的品牌方向或 Spectrum S2 约束。

## 5. React Spectrum Skill

`react-spectrum` skill 是 implementation guardrail，与 React Spectrum / Spectrum S2 设计系统本体不是同一层概念。

它负责在实现阶段检查：

- 是否优先使用合适的官方组件；
- 是否使用已有 Token；
- 交互状态是否一致；
- keyboard、focus、semantic、screen reader 等 Accessibility 是否满足；
- 自定义组件是否确有 OwnWord 特有表达需求。

它不决定产品定位、页面结构或视觉主题。

## Invocation Rules

设计任务执行顺序：

1. 读取 `_task/system-design/spec/核心认知.md`。
2. 定位并读取当前版本相关设计文档。
3. 确认当前版本是否已经绑定 React Spectrum / Spectrum S2 或其他设计系统。
4. 使用 `baoyu-design` 组织高保真设计、原型、预览和验证。
5. 根据页面类型决定是否加载以及加载多少 `design-taste-frontend`。
6. 只有明确需要强 premium / agency / cinematic 表达时，才加载 `high-end-visual-design`，并限制其作用范围。
7. 实现和验收阶段使用 `react-spectrum` skill 检查组件、Token、交互与 Accessibility。
8. Preview 并验证页面是否同时满足核心认知、版本设计文档和绑定设计系统。

## Change Guard

新增设计规则、设计系统或 skill 前必须确认：

- 是否已经在核心认知中定义；
- 是否已经在当前版本设计文档中定义；
- 是否已有绑定设计系统能够解决；
- 新能力是 Orchestrator、Specialist 还是 Implementation Guardrail；
- 是否会与现有 skill 重复或产生第二个事实来源；
- 是否会改变既定产品流程、信息层级或状态语义。

外部 skill 只提供能力。任何与核心认知、当前版本设计文档或绑定设计系统冲突的规则均不得直接应用。
