# OwnWord 设计与设计系统

本文定义 OwnWord 的设计体系、设计原则、设计系统使用规则和设计能力协作方式。

## 1. 设计定位

OwnWord 设计遵循：

- 先明确用户任务；
- 再确定信息层级、内容关系和操作顺序；
- 最后使用设计系统和设计能力完成界面实现。

设计判断遵循核心认知中的产品事实和设计原则。

## 2. 设计原则

OwnWord 页面设计遵循：

1. **秩序清晰**：同级信息使用一致的对齐基准、排列逻辑和页面结构。
2. **关系可感知**：通过亲密性、相似性、连续性、封闭性、对称性以及主体与背景关系表达信息关系。
3. **密度适当**：根据用户任务和阅读节奏控制信息密度。
4. **表达准确**：图片、图标、文字和品牌视觉准确表达内容、状态与功能，并保持构图、层次、风格和视觉品质。

## 3. 设计系统

OwnWord 固定使用 React Spectrum 2（Spectrum S2）作为主设计系统。

Spectrum S2 负责：

- Design Token；
- 通用组件；
- 组件状态；
- 交互行为；
- Accessibility；
- 通用视觉一致性。

Spectrum S2 不定义：

- 产品事实；
- 页面信息架构；
- 内容关系；
- 品牌表达。

页面结构、信息关系和产品状态依据核心认知与当前版本设计文档。

## 4. 设计能力体系

### Design Orchestrator

`baoyu-design`

负责组织设计任务：

- 理解设计上下文；
- 组合设计能力；
- 生成高保真设计和原型；
- Preview 与验证。

### Design Specialist

`design-taste-frontend`

用于提升：

- 页面视觉质量；
- 排版、布局和密度；
- 响应式表现；
- 前端设计检查。

`high-end-visual-design`

用于需要强品牌视觉表达的页面或局部区域。

不得改变 Spectrum S2、信息架构、业务流程和状态语义。

### Implementation Guardrail

`react-spectrum`

用于检查：

- Spectrum S2 组件使用；
- Token 使用；
- 交互状态；
- Accessibility。

不负责定义产品设计方向。

## 5. 设计决策顺序

设计冲突按照以下顺序处理：

1. 核心认知；
2. 当前版本设计文档；
3. OwnWord 设计与设计系统规范；
4. Spectrum S2 规范；
5. Specialist skill 建议。

## 6. 设计流程

核心认知
↓
当前版本设计文档
↓
OwnWord 设计与设计系统
↓
Design Skill
↓
Prototype / Preview / Verify

新增设计规则、组件或 skill 前，需要确认不会形成第二套设计系统，不会改变产品事实、信息层级或状态语义。
