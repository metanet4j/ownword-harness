# React Spectrum 2 (S2) Design System

React Spectrum 2 是 Adobe Spectrum 的新一代 React 组件系统，构建在 react-aria-components 之上。本目录收录其公开视觉语言：已验证的 S2 token、39 个核心组件原型、props 契约、说明与分组预览卡，供设计代理生成 Spectrum 2 风格界面。

## 术语与命名

- **Spectrum 2 / S2：** 本目录描述的组件系统；上游包为 `@react-spectrum/s2`，token 包为 `@adobe/spectrum-tokens`。
- **React Spectrum 3 / RSP3：** 经典 Spectrum React 实现；收录于 `designs/react-spectrum3`，本次明确排除。
- **Design component：** 面向原型的轻量视觉复刻；不是上游生产实现。
- **Provider：** colorScheme（light/dark/darkest/lightest）、scale（medium/large）、background 与 locale 的根控制器。

## 目标

后续设计只从本目录读取 S2 的视觉语言、token、组件名与内容规则。生产代码继续使用上游包，保留其完整可访问性、状态管理与国际化行为。

## 结构

- `styles.css`：唯一 CSS 入口，只含 `@import`。
- `tokens/`：上游编译后的全局、四套配色与 medium/large 缩放 token；`semantic.css` 只定义本导入层的 `--s2-*` 语义别名。
- `components/`：39 个核心组件原型（`.jsx` + `.d.ts` + `.prompt.md`）与 5 张分组预览卡；`shared/spectrumPrimitive.jsx` 是统一的视觉派发器。
- `guidelines/`：颜色、字体、间距、动效、密度、主题与图标基础卡。
- `assets/ui-icons/`：上游 S2 工作流图标（20px），保持原文件不改。
- `_ds_bundle.js`、`_ds_manifest.json`、`preview.html`：编译器生成物，勿手改。

## 实体、属性

- **Token：** 名称唯一；原始值来自上游编译 CSS（Spectrum CSS，global-color-version 5.1.0）。配色与缩放通过 class 作用域切换。
- **Component：** PascalCase 公共名唯一；每个组件具备 `.jsx`、`.d.ts`、`.prompt.md`，`.d.ts` 描述 props 契约。
- **Card：** 首行 `@dsCard` 决定分组、名称与预览 viewport。
- **Asset：** 保留上游文件名；不从记忆重画 Adobe 标志或 Spectrum 图标。

## 关系

`styles.css` 导入 token 与共享组件样式；组件只消费这些变量。分组卡从 `_ds_bundle.js` 读取同一组件实现。`preview.html` 由编译器从 README、cards、manifest 生成。

## 状态

- Theme：`spectrum--light`、`spectrum--dark`、`spectrum--darkest`、`spectrum--lightest`。
- Scale：`spectrum--medium`、`spectrum--large`。
- Interaction：default、hover、focus-visible、selected、disabled、invalid、pending。
- Motion：130–500 ms 上游 duration；原型过渡用 130 ms，遵守 `prefers-reduced-motion`。

## 界限

- 本目录是设计与原型约束，不替代 `@react-spectrum/s2` 生产包。
- 只收录核心组件；完整 S2 清单（约 90 个公共导出）与 React Aria hooks、formatter、drag/drop 常量不在此列。
- 源快照未包含 Adobe Clean 字体文件。预览先请求 Adobe Clean，再回退 Source Sans Pro 与系统 sans；正式品牌交付需补合法字体文件。
- 源仓库是组件库，不含可确认的产品应用界面，因此没有创建 UI kit。
- 圆角与少量几何值为原型近似（字段 8px、按钮胶囊、卡片 8px、对话框 16px）；精确值以上游组件 CSS 与 `@adobe/spectrum-tokens` 为准。
- 组件卡验证视觉结构；键盘导航、screen reader 语义、virtualization 与 locale 逻辑仍以上游实现为准。

## Content fundamentals

使用直接、任务导向、sentence case 文案。控件保留可见标签；帮助文案解释下一步，不复述标签。按钮用短动词，如 “Save”“Cancel”“Share”。生产文案通过 `children` 或 `aria-label` 国际化。Emoji 可出现在项目说明，但不充当控制图标。

## Visual foundations

S2 使用中性灰层级（gray-50 白面到 gray-900 文本）、蓝色 accent（blue-900 `#0265DC`）、语义状态色与胶囊按钮。控件 medium scale 高 32px，字段圆角 8px，按钮为胶囊形。卡片白面、1px 边框、轻投影。背景不使用装饰渐变；渐变只服务 ColorArea 等颜色工具与 premium/genai 按钮。Hover 加深语义色，press 不缩放。Focus ring 必须可见（2px blue-900）。布局用 Flex/Grid 与显式 gap。完整数值以 `tokens/*.css` 为准。

## Iconography

图标来自上游 S2 工作流图标集（20px SVG，`s2wf-icons`），只复制不重画。图标默认继承 `--s2-text` 颜色；选中态用白色或 accent。无内置图标字体；emoji 不充当控制图标。完整图标集见源仓库 `packages/@react-spectrum/s2/s2wf-icons` 与 `@adobe/spectrum-tokens`。

## 来源

- adobe/react-spectrum（本地快照 `reference/react-spectrum-main`，commit `0feb87a`，2026-08-15），S2 实现见 `packages/@react-spectrum/s2`。
- `@adobe/spectrum-tokens@14.15.0`（tgz 存于 `designs/_sources/s2-tokens`）。
- 编译 token CSS 取自 `packages/@adobe/spectrum-css-temp/vars`（Spectrum CSS，global-color-version 5.1.0）。
- 图标取自 `packages/@react-spectrum/s2/s2wf-icons`。

## 索引

- 组件：`components/actions`、`components/forms`、`components/content`、`components/containers`、`components/overlays`
- 基础卡：`guidelines/`（Colors、Type、Spacing、Motion、Density、Themes、Iconography）
- 总览：`preview.html`
