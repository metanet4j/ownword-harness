# OwnWord 设计与设计系统

## 1. 文档定位

本文是 OwnWord 设计工作的总指南，负责组织设计判断、设计系统使用、设计能力协作、原型验证和实现检查。

职责边界：

- `_task/system-design/spec/核心认知.md` 定义跨模块、跨版本稳定的产品事实与设计约束；
- 当前版本设计文档定义该版本的页面、流程、信息架构、状态、视觉方向和验收；
- 本文负责把上述约束组织成可执行的设计方法；
- Spectrum S2 提供组件、Token、交互和 Accessibility 基线；
- design skill 提供具体执行能力，不得建立新的产品事实或第二套设计系统。

设计任务发生冲突时，按以下顺序处理：

1. 核心认知；
2. 本设计指南；
3. 当前版本设计文档；
4. 项目绑定版本的 Spectrum S2；
5. design skill 的通用建议。

当前版本设计文档可以在前述约束内做具体设计选择；不得覆盖核心认知、本文的设计治理规则或更换主设计系统。

## 2. 设计方法

设计 OwnWord 页面时，按以下顺序完成判断：

1. 明确用户任务；
2. 建立信息层级；
3. 判断内容关系；
4. 确定操作顺序；
5. 选择 Spectrum S2 组件、Token 和交互模式；
6. 完成品牌表达、响应式和视觉细节；
7. Preview 并验证实际实现。

不得从组件库、视觉套路或某个 skill 的默认模板反推产品结构。

## 3. 设计原则

核心认知第 10.5.1 节定义四项跨版本稳定原则。本文负责将其用于设计判断：

1. **秩序清晰**：检查同级信息的对齐基准、排列逻辑、页面结构和层级是否一致。
2. **关系可感知**：检查亲密性、相似性、连续性、封闭性、对称性以及主体与背景关系是否准确表达信息关系。
3. **密度适当**：根据任务和阅读节奏控制信息密度；强关联内容保持紧密，不同模块形成清晰分隔。
4. **表达准确**：图片、图标、文字和品牌视觉准确表达内容、状态与功能，并保持构图、层次、风格和视觉品质。

外部 skill 可以提供方法和视觉建议，但不得替换或重新定义这四项原则。

## 4. 主设计系统：Spectrum S2

OwnWord 固定使用 React Spectrum 2（Spectrum S2）作为唯一主设计系统。设计任务不重新选择主设计系统，外部 skill 不得引入 Material、Fluent、Carbon、shadcn/ui、Radix Themes 等体系并行主导页面。

Spectrum S2 负责：

- Design Token；
- 通用组件；
- 组件状态；
- 交互行为；
- Accessibility；
- 通用视觉与行为一致性。

Spectrum S2 不决定：

- 产品事实；
- 页面信息架构；
- 内容关系；
- 业务流程；
- 品牌叙事与页面构图。

OwnWord 特有的 Hero、Identity 表达、Content Showcase、Artifact 表达可以使用自定义布局和视觉组合，但应优先复用 Spectrum S2 Token 和通用组件；自定义组件继续遵守 Spectrum S2 的状态、交互和 Accessibility 基线。

## 5. Spectrum S2 版本与符合性

设计和评审必须以**项目绑定版本**为依据，不自动采用最新版或其他 Spectrum 版本。

开始前：

1. 读取原型的 `_d_meta.json`；
2. 读取绑定的 `_ds/<slug>/_ds_prompt.md` 和来源记录；
3. 确认实际组件包、Token 和版本；
4. 再进行组件、Token、交互和视觉判断。

官方实现优先核对：

`reference/react-spectrum-main/react-spectrum-main/packages/@react-spectrum/s2/`

并使用对应 `package.json` 确认版本。资料不足时再查官方文档，并核对其与项目绑定版本是否适用。

必须区分：

- 官方 Spectrum S2 源码与规范；
- 本地导入的设计资料；
- 原型的设计系统封装；
- 页面实际加载的组件、bundle、CSS 和 Token；
- OwnWord 自定义覆盖。

`designs/react-spectrum-s2/` 和原型内的 `_ds/react-spectrum-s2/` 不因名称包含 S2 就等同于官方生产实现。生成的 bundle、CSS 和消费副本不能反向定义 Spectrum S2。

判断页面是否符合 S2 时：

- 给出绑定版本依据；
- 核实页面实际加载内容；
- 明确 S2、原型封装和 OwnWord 定制的边界；
- 记录与官方实现的实际差异；
- 未核实项标记为“待核实”。

不能仅凭组件名称宣称符合，也不能仅凭原生 HTML、自定义 CSS 或自定义图标宣称不符合。

## 6. 设计能力体系

### 6.1 Design Orchestrator：baoyu-design

`baoyu-design` 是 OwnWord 高保真设计任务的主设计执行框架，负责：

- 理解任务和设计上下文；
- 按本文组织设计判断；
- 使用 Spectrum S2；
- 完成高保真设计和交互原型；
- Preview、验证和迭代。

OwnWord 已固定 Spectrum S2。若其通用流程要求选择设计系统，直接采用项目绑定的 Spectrum S2。

`baoyu-design` 不能定义 OwnWord 产品事实，也不能覆盖核心认知、本文或当前版本已经确定的设计约束。

### 6.2 Design Specialist：design-taste-frontend

`design-taste-frontend` 用于强化：

- 页面设计语言判断；
- anti-slop / anti-template；
- Typography、spacing、layout；
- Visual density；
- Motion intensity；
- Responsive mechanics；
- 前端设计 pre-flight check。

其“选择设计系统”能力在 OwnWord 中不适用。

| 页面类型 | 使用方式 |
| --- | --- |
| Public Personal Homepage、Landing、Content Showcase、公开展示页 | 强使用，强化构图、密度、排版、动效和 anti-slop |
| Public Post Reader、内容阅读页 | 中等使用，强化排版、密度、响应式和细节质量 |
| Identity Setup、Wallet Connect | 选择性使用，只采用排版、响应式、anti-slop 和检查规则 |
| Publish Review、Wallet Confirmation、Settings、Proof / Transaction Details | 轻量使用，以清晰度、状态完整性、响应式和实现质量为主 |

任何情况下，不得为了视觉变化改写业务流程、状态机、信息优先级或 Spectrum S2。

### 6.3 Design Specialist：high-end-visual-design

`high-end-visual-design` 只在页面目标明确需要强品牌、premium、agency 或 cinematic 表达时使用，例如品牌型 Hero 或展示型页面的局部视觉探索。

其 typography、macro whitespace、非对称布局、复杂 motion、卡片、按钮、阴影、圆角等建议只有在与 OwnWord 设计原则、当前版本设计文档和 Spectrum S2 相容时才能采用。

不得把其固定视觉套路全局应用到 Wallet、Publish、Settings、Proof 等任务型 UI。

### 6.4 Implementation Guardrail：react-spectrum

`react-spectrum` skill 用于实现和验收阶段的 Spectrum S2 检查：

- 是否优先使用合适的官方组件；
- 是否优先使用绑定版本的 Token；
- 组件状态和交互是否一致；
- keyboard、focus、semantic、screen reader 等 Accessibility 是否满足；
- 自定义组件是否确有 OwnWord 特有表达需求；
- 自定义实现是否仍满足 Spectrum S2 基线。

它不决定产品定位、页面信息架构或产品视觉主题。

## 7. 与原型实现配合

继续遵循 `baoyu-design` 的设计系统导入、组件组合、预览和验证流程，并遵守以下规则：

- 符合性以项目绑定版本的官方 S2 为准，导入 bundle 只是原型实现载体；
- 绑定文件或封装与官方实现有差异时，记录差异及影响，不能以封装行为反向定义 S2；
- 修复应修改导入来源中的可维护源文件，再编译和重新导入，不直接修改生成 bundle 或消费副本；
- 源文件不完整时，明确记录缺少的资料；完成 bundle 接入不代表已经符合 S2；
- OwnWord 基础 UI 使用绑定版本的 S2 Token，不采用与项目约束冲突的自由扩色规则；
- 品牌表达不得覆盖组件必要的交互状态和 Accessibility 行为。

## 8. 设计执行流程

```text
核心认知（产品事实与稳定约束）
        ↓
OwnWord 设计与设计系统（设计总指南）
        ↓
当前版本设计文档（版本设计契约）
        ↓
确认项目绑定 Spectrum S2
        ↓
baoyu-design
   ├─ design-taste-frontend（按页面类型加载）
   └─ high-end-visual-design（按视觉目标加载）
        ↓
Prototype / Preview
        ↓
react-spectrum 实现检查
        ↓
Verify
```

执行时：

1. 读取核心认知；
2. 读取本文；
3. 定位当前版本相关设计文档；
4. 明确用户任务、信息层级、内容关系和操作顺序；
5. 确认 Spectrum S2 绑定版本和实际实现来源；
6. 使用 `baoyu-design` 组织设计；
7. 按页面需要加载 specialist；
8. Preview；
9. 使用 `react-spectrum` 检查组件、Token、交互与 Accessibility；
10. 验证页面同时满足核心认知、本文、版本设计文档和绑定版本 S2。

## 9. 变更门禁

新增设计规则、视觉 skill 或组件前必须确认：

- 是否属于产品事实；属于时先处理核心认知；
- 是否属于跨版本设计规则；属于时更新本文；
- 是否只是当前版本的页面决策；属于时写入版本设计文档；
- Spectrum S2 是否已有对应 Token、组件或模式；
- 新能力属于 Orchestrator、Specialist 还是 Implementation Guardrail；
- 是否与现有设计能力重复；
- 是否会形成第二套设计系统；
- 是否会改变既定业务流程、信息层级、状态语义或 Accessibility 基线。

设计知识只保留一个权威定义；其他位置使用引用或描述其应用方式。
