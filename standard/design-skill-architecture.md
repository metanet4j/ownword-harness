# OwnWord Design Skill Architecture

## Purpose

本文定义 OwnWord 设计事实、版本设计文档、固定设计系统与设计 skill 的协作方式。

OwnWord 产品事实只在核心认知中定义。版本设计文档负责把事实落实到当前版本。按核心认知第 10.5 节，**Spectrum S2 是 OwnWord 固定且唯一的主设计系统。** 本文只说明这一事实如何约束设计执行，不重复建立新的事实来源。

## Architecture

```text
1. Product Truth
   _task/system-design/spec/核心认知.md
            ↓
2. Version Design Contract
   当前版本相关设计文档
            ↓
3. Binding Design System
   Spectrum S2（固定）
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

这里不是固定的 skill 流水线。Core Cognition 和 Version Design Contract 建立产品与版本约束；Spectrum S2 始终提供设计系统约束；`baoyu-design` 作为主设计执行框架；其他视觉 skill 按场景加载。

## 1. Product Truth

`_task/system-design/spec/核心认知.md` 是 OwnWord 产品、设计、原型、代码和测试的唯一事实来源（SSOT）。

它定义跨模块、跨版本必须稳定的：

- 产品定位与目标；
- 术语与命名；
- 领域实体与关系；
- 状态与全局不变量；
- Spectrum S2 固定设计系统；
- 「秩序清晰、关系可感知、密度适当、表达准确」四项设计原则；
- 安全、协议和事实来源边界。

任何设计系统或 skill 都不得修改、补充或重新定义这些事实。缺少新的跨模块事实时，先更新核心认知，再同步下游。

## 2. Version Design Contract

当前版本设计文档把核心认知落实为。设计页面时先明确用户任务、信息层级、内容关系和操作顺序，再将核心认知第 10.5 节的四项设计原则落实到具体页面：

- 页面与信息架构；
- 用户流程；
- 组件与状态；
- 视觉方向；
- 原型范围和验收；
- 对 Spectrum S2 的版本级应用要求。

版本设计文档可以定义当前版本的设计选择，但不得创建与核心认知冲突的产品事实，也不得更换主设计系统。

## 3. Binding Design System: Spectrum S2

按 `_task/system-design/spec/核心认知.md` 第 10.5 节，Spectrum S2 是 OwnWord 固定且唯一的主设计系统。所有设计任务默认绑定，无需询问、选择或重新判断设计系统。

Spectrum S2 负责约束：

- Design Token；
- 通用组件；
- 组件状态；
- 交互行为；
- Accessibility；
- 通用视觉与行为一致性。

### 固定规则

- `baoyu-design` 使用 design-system 能力时直接采用 Spectrum S2。
- `design-taste-frontend` 中关于“根据 brief 选择其他设计系统”的规则对 OwnWord 不适用。
- `high-end-visual-design` 只能在 Spectrum S2 约束范围内提供局部视觉表达，不得建立第二套 Token、组件语言或交互语言。
- 不得混入 Material、Fluent、Carbon、shadcn/ui、Radix Themes 等其他主设计系统来替代或并行主导页面。

项目特有的 Hero、Identity 表达、Content Showcase、Artifact 表达等可以使用自定义布局和视觉组合，但：

- 优先复用 Spectrum S2 Token；
- 通用交互优先复用 Spectrum S2 组件；
- 自定义组件继续遵守 Spectrum S2 的状态、交互和 Accessibility 基线；
- 自定义视觉不得改变核心认知和当前版本设计文档规定的信息层级与语义。

## 4. Design Execution

### baoyu-design

`baoyu-design` 是 OwnWord 高保真设计任务的主设计执行框架。

它负责：

- 理解设计任务和现有上下文；
- 加载并遵循 Spectrum S2；
- 高保真设计和交互原型；
- 设计质量检查；
- Preview、验证和迭代。

OwnWord 已固定 Spectrum S2，因此 `baoyu-design` 不再询问“使用哪个主设计系统”；若其通用流程要求选择设计系统，直接选择 Spectrum S2。

它负责组织设计工作，但不拥有 OwnWord 产品事实，也不能覆盖当前版本已经确定的设计约束。设计判断必须遵循核心认知第 10.5 节的四项设计原则。

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

其“Brief → Design System Map”能力在 OwnWord 中不用于选择主设计系统。Spectrum S2 已固定；只使用其中不与 Spectrum S2、核心认知和版本设计冲突的视觉与工程规则。

| 页面类型 | 使用方式 |
| --- | --- |
| Public Personal Homepage、Landing、Content Showcase、公开展示页 | 强使用，可用于整体构图、密度、排版、动效与 anti-slop |
| Public Post Reader、内容阅读 | 中等使用，以排版、密度、响应式和细节质量为主 |
| Identity Setup、Wallet Connect | 选择性使用，采用 anti-slop、排版、响应式和检查规则，不重写流程、组件体系与设计系统 |
| Publish Review、Wallet Confirmation、Settings、Proof / Transaction Details | 轻量使用，只吸收与清晰度、响应式、状态完整性和实现质量相关的规则 |

任何时候，`design-taste-frontend` 都不得为了视觉变化改变既定业务流程、状态机、信息优先级或 Spectrum S2，也不得用自身审美规则替换核心认知第 10.5 节的四项设计原则。

### high-end-visual-design

`high-end-visual-design` 是强风格视觉 specialist，不是通用质量层。

它具有明确的 premium / agency / cinematic 审美倾向，包括强 typography、macro whitespace、非对称布局、复杂 motion 和特定组件造型。

仅当当前页面目标明确需要这种强视觉表达时使用，例如品牌型 Hero 或展示型页面的局部视觉探索。

使用时只采纳与 OwnWord 品牌方向、核心认知第 10.5 节四项设计原则和 Spectrum S2 相容的规则。其字体、卡片结构、按钮结构、阴影、圆角、布局或动效规则如果与 Spectrum S2 冲突，以 Spectrum S2 为准。

不得把其固定视觉套路全局应用到 Wallet、Publish、Settings、Proof 等任务型产品 UI。

## 5. React Spectrum Skill

`react-spectrum` skill 是 Spectrum S2 的 implementation guardrail，与 Spectrum S2 设计系统本体不是同一层概念。

它负责在实现和验收阶段检查：

- 是否优先使用合适的 Spectrum S2 官方组件；
- 是否优先使用 Spectrum S2 Token；
- 交互状态是否一致；
- keyboard、focus、semantic、screen reader 等 Accessibility 是否满足；
- 自定义组件是否确有 OwnWord 特有表达需求；
- 自定义实现是否仍遵守 Spectrum S2 基线。

它不决定产品定位、页面结构或产品视觉主题。

## Invocation Rules

设计任务执行顺序：

1. 读取 `_task/system-design/spec/核心认知.md`。
2. 定位并读取当前版本相关设计文档。
3. 加载并遵循固定设计系统 Spectrum S2；不得重新选择其他主设计系统。
4. 使用 `baoyu-design` 组织高保真设计、原型、预览和验证。
5. 根据页面类型决定是否加载以及加载多少 `design-taste-frontend`，忽略其更换主设计系统的建议。
6. 只有明确需要强 premium / agency / cinematic 表达时，才加载 `high-end-visual-design`，并限制其作用范围。
7. 实现和验收阶段使用 `react-spectrum` skill 检查组件、Token、交互与 Accessibility。
8. Preview 并验证页面是否同时满足核心认知、版本设计文档和 Spectrum S2。

## Change Guard

新增设计规则、视觉 skill 或组件前必须确认：

- 是否已经在核心认知中定义；
- 是否已经在当前版本设计文档中定义；
- Spectrum S2 是否已有对应 Token、组件或模式；
- 新能力是 Orchestrator、Specialist 还是 Implementation Guardrail；
- 是否会与现有 skill 重复；
- 是否会形成第二套设计系统；
- 是否会改变既定产品流程、信息层级或状态语义。

Spectrum S2 的固定地位属于核心认知；如需变更，必须先修改核心认知，再同步版本设计、架构文档和实现。外部 skill 不得改变该选择。
