# OwnWord Design Skill Architecture

## Purpose

本文说明 OwnWord 设计事实、版本设计文档与外部设计 skill 的协作关系。

OwnWord 产品事实只在核心认知中定义。设计 skill 提供方法和执行能力，不建立新的产品事实来源。

## Source of Truth

`_task/system-design/spec/核心认知.md` 是 OwnWord 产品、设计、原型、代码和测试的唯一事实来源（SSOT）。

设计任务必须先读取核心认知，再读取当前版本相关设计文档。版本设计文档负责把核心认知落到页面、组件、流程和验收，不重复定义跨版本事实。

当内容冲突时，遵循核心认知和当前版本设计文档中已有的优先级规则。

## Capability Flow

```text
Core Cognition (SSOT)
        ↓
Current Version Design Document
        ↓
baoyu-design
        ↓
design-taste-frontend
        ↓
high-end-visual-design (optional)
        ↓
react-spectrum
```

其中 Core Cognition 和 Current Version Design Document 是项目事实与设计依据，不是 skill。

## Responsibility Boundary

### Core Cognition

定义跨模块、跨版本必须稳定的产品事实、术语、目标、实体、关系、状态和全局约束。

任何设计 skill 都不得修改、补充或重新定义这些事实。发现缺失的跨模块事实时，先更新核心认知，再同步下游设计和实现。

### Current Version Design Document

把核心认知落实为当前版本的页面结构、组件、流程、视觉方向和验收要求。

例如个人主页版本已经明确 BAP ID 的页面角色、公开主页信息结构，以及 React Spectrum S2 的设计系统约束。skill 必须在这些既有约束内执行。

### baoyu-design

提供通用设计方法，包括设计分析、设计系统意识、视觉质量判断和原型验证方法。

它用于帮助理解和落实已有设计目标，不定义 OwnWord 产品事实。

### design-taste-frontend

负责页面视觉语言和前端设计执行，包括布局、视觉密度、动效强度和反模板化约束。

它必须服从核心认知与当前版本设计文档，不得为了视觉效果改变信息层级、产品语义或既定交互规则。

### high-end-visual-design

可选的视觉精修能力，用于页面结构和设计方向已经确定后的字体、空间、层次、动效和品牌质感优化。

仅在当前页面目标需要更强视觉表达时使用，不作为默认产品设计规则。

### react-spectrum

负责组件实现规范，包括组件选择、Design Token、交互状态和无障碍要求。

当前版本设计文档已指定 React Spectrum 或 Spectrum S2 时，优先按该设计系统实现通用交互。品牌展示、特殊内容表达和项目特有组件可以在既有设计约束下自定义。

## Invocation Rules

设计任务按以下顺序执行：

1. 读取 `_task/system-design/spec/核心认知.md`。
2. 定位并读取当前版本相关设计文档。
3. 确认已有页面、组件、视觉和设计系统约束。
4. 使用 `baoyu-design` 做设计分析和质量判断。
5. 使用 `design-taste-frontend` 完成视觉与前端设计执行。
6. 需要额外视觉精修时再使用 `high-end-visual-design`。
7. 使用 `react-spectrum` 落实通用组件、Token、交互和无障碍。

## Change Guard

新增设计规则、skill 或标准前必须确认：

- 是否已经在核心认知中定义；
- 是否已经在当前版本设计文档中定义；
- 新内容属于产品事实、版本设计、设计方法、视觉执行还是组件实现；
- 是否会产生第二个事实来源。

外部 skill 只提供能力。任何与核心认知或当前版本设计文档冲突的 skill 规则均不得直接应用。
