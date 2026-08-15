# React Spectrum 3 Design System

React Spectrum 3 is Adobe Spectrum’s accessible React component system. This imported design source captures its public visual API, verified Spectrum tokens, component illustrations, and compact review cards for design-agent use.

## 术语与命名

- **React Spectrum 3 / RSP3：** 本目录描述的经典 Spectrum React 实现；版本来自 `@adobe/react-spectrum@3.47.3`。
- **Spectrum 2 / S2：** 源仓库中的新系统；本次明确排除。
- **Design component：** 面向原型的轻量视觉复刻；不是上游生产实现。
- **Provider：** 主题、色彩模式、缩放、locale 与上下文属性的根控制器。

## 目标

让后续设计只从本目录读取 React Spectrum 3 的视觉语言、token、组件名和内容规则。生产代码继续使用上游包，保留其完整可访问性、状态管理与国际化行为。

## 结构

- `styles.css`：唯一 CSS 入口，只含 `@import`。
- `tokens/`：上游全局、明暗模式、medium/large 缩放 token；`semantic.css` 只定义本导入层语义别名。
- `components/`：101 个公共可视导出的原型组件、props 契约、使用提示与分组预览卡。
- `guidelines/`：颜色、字体、间距、动效、图标、插图等基础卡。
- `assets/`：上游 UI SVG 与组件说明插图，保持原文件不改。
- `tools/regenerate.mjs`：组件清单与机械生成内容的唯一事实源。

## 实体、属性

- **Token：** 名称唯一；原始值来自上游 Spectrum CSS。明暗色与 medium/large 缩放通过 class 作用域切换。
- **Component：** PascalCase 公共名唯一；每个组件具备 `.jsx`、`.d.ts`、`.prompt.md`。
- **Card：** 首行 `@dsCard` 决定分组、名称与预览 viewport。
- **Asset：** 保留上游文件名；不从记忆重画 Adobe 标志或 Spectrum 图标。

## 关系

`styles.css` 导入 token 和共享组件样式；组件只消费这些变量。分组卡从 `_ds_bundle.js` 读取同一组件实现。`preview.html` 由编译器从 README、cards、manifest 生成。

## 状态

- Theme：`spectrum--light` 或 `spectrum--darkest`。
- Scale：`spectrum--medium` 或 `spectrum--large`。
- Interaction：default、hover、focus-visible、selected、disabled、negative、progress。
- Motion：0–2000 ms 上游 duration；常用原型过渡为 130–250 ms，遵守 `prefers-reduced-motion`。

## 界限

- 本目录是设计与原型约束，不替代 `@adobe/react-spectrum` 生产包。
- 不包含 Spectrum 2、React Aria 无样式组件、hooks、formatter 或 drag/drop 常量。
- 源快照未包含 Adobe Clean 字体文件。预览先请求 Adobe Clean，再回退 Source Sans 3 与系统 sans；正式品牌交付需补合法字体文件。
- 源仓库是组件库，不含可确认的产品应用界面，因此没有凭空创建 UI kit。
- 组件卡验证视觉结构；复杂键盘导航、screen reader 语义、virtualization 和 locale 逻辑仍以上游实现为准。

## Content fundamentals

使用直接、任务导向、sentence case 文案。控件保留可见标签；帮助文案解释下一步，不复述标签。按钮用短动词，如 “Save”“Cancel”“Share”。生产文案通过 `children` 或 `aria-label` 国际化。Emoji 可出现在项目说明，但不充当控制图标。

## Visual foundations

Spectrum 3 使用中性灰层级、清晰边界、蓝色 accent、状态色与小半径表面。控件在 medium scale 通常高 32 px；触摸 scale 提升到 40 px。按钮常用胶囊轮廓，字段与卡面保持 4–6 px 半径。默认阴影克制，仅 overlay 提升。背景不使用装饰渐变；渐变仅服务 ColorArea、ColorSlider、ColorWheel 等颜色工具。Hover 改变语义颜色，press 保持稳定，不用夸张缩放。Focus ring 必须可见。布局用 Flex/Grid 与显式 gap。完整数值以 `tokens/*.css` 为准。

## Iconography

生产组件使用 `@spectrum-icons/ui` 和 `@spectrum-icons/workflow`。本快照仅含 11 个 UI SVG 原文件，已复制到 `assets/ui-icons/`；workflow 图标在源中以生成式 TSX 提供，未复制成伪 SVG。组件说明插图 92 个，原样保存在 `assets/component-illustrations/`。未提供独立经典 Adobe 品牌 logo，因此本系统不造 logo。

## Component inventory

公共可视导出以 `packages/@adobe/react-spectrum/exports/index.ts` 为唯一清单，共 101 个：

- **Actions:** ActionBar, ActionBarContainer, ActionButton, ActionGroup, ActionMenu, Button, ButtonGroup, FileTrigger, LogicButton, ToggleButton
- **Forms:** Checkbox, CheckboxGroup, ComboBox, DropZone, Form, NumberField, Picker, Radio, RadioGroup, RangeSlider, SearchField, Slider, Switch, TextArea, TextField
- **Date and time:** Calendar, DateField, DatePicker, DateRangePicker, RangeCalendar, TimeField
- **Color:** ColorArea, ColorEditor, ColorField, ColorPicker, ColorSlider, ColorSwatch, ColorSwatchPicker, ColorWheel
- **Content and layout:** Avatar, Badge, Content, Divider, Flex, Footer, Grid, Header, Heading, Icon, IllustratedMessage, Image, Keyboard, LabeledValue, Link, Provider, SSRProvider, StatusLight, Text, View, VisuallyHidden, Well
- **Collections and navigation:** Accordion, Breadcrumbs, Cell, Collection, Column, Disclosure, DisclosurePanel, DisclosureTitle, Item, ListBox, ListView, Row, Section, TabList, TabPanels, Tabs, TableBody, TableHeader, TableView, TagGroup, TreeView, TreeViewItem, TreeViewItemContent
- **Feedback and overlays:** AlertDialog, ContextualHelp, ContextualHelpTrigger, Dialog, DialogContainer, DialogTrigger, InlineAlert, Menu, MenuTrigger, Meter, ProgressBar, ProgressCircle, SubmenuTrigger, ToastContainer, ToastQueue, Tooltip, TooltipTrigger

## Intentional addition

`components/shared/spectrumPrimitive.jsx` 是导入层唯一新增 helper，用于 DRY 地生成轻量视觉预览；它不是 React Spectrum 公共 API。

## 索引与验证

- 单文件总览：`preview.html`
- 机器清单：`_ds_manifest.json`
- 运行时 bundle：`_ds_bundle.js`
- Adherence 规则：`_adherence.oxlintrc.json`
- 再生成：`node tools/regenerate.mjs`，随后运行 compiler、checker 与 preview builder。

## 参考文档与引用

- 本地源：`C:\haodev\ownword\reference\react-spectrum-main\react-spectrum-main`
- 公共导出：`C:\haodev\ownword\reference\react-spectrum-main\react-spectrum-main\packages\@adobe\react-spectrum\exports\index.ts`
- 上游仓库：https://github.com/adobe/react-spectrum
- 上游文档：https://react-spectrum.adobe.com/react-spectrum/index.html
- 包版本：`@adobe/react-spectrum@3.47.3`
- Token 来源：`@adobe/spectrum-css-temp`
- 许可：Apache-2.0；见 `LICENSE.source.txt` 与 `NOTICE.source.txt`。
- 上游 Git commit 不在此解压快照中，无法可靠记录。
