# React Spectrum 2 / S2 Design System

Spectrum 2（S2）是 Adobe 新一代设计语言和 React 组件系统。本目录独立导入 `@react-spectrum/s2@1.6.0` 的公共视觉 API、`@adobe/spectrum-tokens@14.15.0`、图标与插画，供设计代理和原型使用。

## 术语与命名

- **Spectrum 2 / S2：** 本目录描述的新设计系统；包名 `@react-spectrum/s2`。
- **React Spectrum 3 / RSP3：** 经典 React Spectrum 系统；保存在相邻 `designs/react-spectrum3`，不混入本目录。
- **Design component：** 面向原型的轻量视觉复刻；不是上游生产实现。
- **Provider：** locale、color scheme、background layer、router 与自适应缩放的根容器。
- **Style macro：** S2 生产源码的类型化样式入口；本导入把可验证 token 映射为 CSS custom properties，便于静态原型消费。

## 目标

让后续设计只从本目录读取 S2 的视觉语言、token、组件名和资产；让 S2 与 RSP3 能并排审阅。生产代码继续使用上游包，保留完整可访问性、状态管理、国际化和 style macro 编译行为。

## 结构

- `styles.css`：唯一 CSS 入口，只含 `@import`。
- `tokens/`：2469 个固定版本源 token、S2 page/theme 变量、官方远程字体声明和语义别名。
- `components/`：137 个公共视觉导出，含原型组件、props 契约、提示和 9 张分组卡。
- `guidelines/`：16 张颜色、字体、间距、效果、图标和插画基础卡。
- `assets/`：48 个 UI SVG、410 个 workflow SVG、518 个公开插画家族的 96 px SVG。
- `sources/`：固定版本 token JSON、包元数据和公共组件清单。
- `tools/regenerate.mjs`：清单、token 转换和机械生成内容的唯一事实源。

## 功能

- 提供可加载的 S2 token、组件、卡片和单文件总览。
- 支持 light、dark 与系统色彩模式。
- 按输入能力切换 desktop/touch 字号和几何缩放。
- 提供 accent、negative、premium、gen-AI 等源定义视觉角色。
- 让设计代理按公共 API 名称组合 S2 原型。

## 实体、属性

- **Token：** 名称唯一；值来自 `variables.json`。light/dark 用 `light-dark()`；desktop/mobile 用源 media query 覆盖。
- **Component：** PascalCase 公共名唯一；每个组件具备 `.jsx`、`.d.ts`、`.prompt.md`。
- **Card：** 首行 `@dsCard` 决定分组、名称和 viewport。
- **Asset：** 保留上游文件名；图标不从记忆重画。
- **Illustration family：** linear、gradient/generic1、gradient/generic2；本目录保留每个公共家族的 M/96 px 原文件。

## 关系

`styles.css` 导入 source token、Provider page 变量和共享原型样式；组件只消费这些变量。分组卡从 `_ds_bundle.js` 读取同一实现。`preview.html` 由 compiler 从 README、cards 和 manifest 生成。

## 状态

- Color scheme：system、light、dark。
- Background：base、layer-1、layer-2。
- Scale：desktop `--s2-scale: 1`；touch `1.25`。
- Interaction：default、hover、focus-visible、pressed、selected、disabled、invalid。
- Variant：primary、secondary、accent、negative、premium、gen-AI、quiet。
- Motion：默认 150 ms；遵守 `prefers-reduced-motion`。

## 界限

- 本目录是设计与原型约束，不替代 `@react-spectrum/s2` 生产包。
- 不包含 RSP3 视觉 token、React Aria hooks、解析器或 drag/drop 常量。
- 字体 CSS 来自 S2 源码，但字体二进制由 Adobe Typekit 远程提供；离线时回退系统字体。
- 上游是组件库，不是可确认的产品应用，因此不凭空创建 UI kit 或 starting point。
- 组件卡验证视觉结构；复杂键盘导航、screen reader 语义、virtualization、locale 和 style macro 逻辑以上游实现为准。
- 插画每个公共家族只复制 96 px 源文件；生产包仍提供 48/96/160 px。

## Content fundamentals

使用直接、任务导向、sentence case 文案。标签说明对象，按钮使用短动词，如 “Save”“Share”“Generate”。帮助文案解释下一步。错误说明问题并给出修复动作。Emoji 不充当控件图标；生产字符串走国际化资源。

## Visual foundations

S2 使用更亮的 indigo-blue accent、更宽的色阶和 light/dark 原生组合。基础表面从 gray 25、50、75 构建；字段用 2 px 边界和 8 px 圆角；卡片默认 10 px；重点表面可到 16 px；按钮保持 pill。控件尺寸为 20、24、32、40、48 px，触摸设备整体放大 1.25×。卡片和 overlay 比 RSP3 更强调层级和阴影。Premium 与 gen-AI 渐变仅用于明确变体。Hover/press 改变颜色并允许轻微位移；focus ring 始终可见。布局使用 Flex/Grid 与显式 gap。

## Iconography

S2 内置 48 个结构型 UI glyph 和 410 个 20 px workflow SVG。控制图标使用这些源文件，不使用 emoji 或 Unicode 字符替代。518 个公开插画家族分为 linear 与两个 gradient theme；本目录复制所有家族的 96 px SVG。未提供独立 Adobe logo，因此不造 logo。

## 与 React Spectrum 3 的差异

| 维度 | Spectrum 2 / S2 | React Spectrum 3 |
| --- | --- | --- |
| 包版本 | `@react-spectrum/s2@1.6.0` | `@adobe/react-spectrum@3.47.3` |
| 公共视觉导出 | 137 | 101 |
| 样式模型 | Type-safe style macro + `light-dark()` | Spectrum CSS classes + theme/scale CSS |
| 基础字号 | Desktop 14；touch 17 | Medium/large scale token 体系 |
| 控件尺寸 | 20/24/32/40/48 px | 经典 medium 常见 32；large 常见 40 px |
| 圆角 | 4/8/10/16 px + pill | 经典字段/表面多为 4–6 px + pill |
| Accent | 更亮的 indigo-blue，900 为 light `rgb(59, 99, 251)` | 经典 Spectrum blue 900 为 `#0265dc` |
| 表面 | 分层更强、卡片阴影更明显 | 边界更克制、表面更紧凑 |
| 表达性 | Premium、gen-AI 渐变为正式变体 | 默认不以表达性渐变为核心 |
| 资产 | 458 个 SVG 图标；518 个插画家族 | 本地经典快照资产较少 |

## Component inventory

公共视觉导出以 `packages/@react-spectrum/s2/exports/index.ts` 为唯一清单，共 137 个：

- **Actions:** ActionBar, ActionButton, ActionButtonGroup, ActionMenu, Button, ButtonGroup, CloseButton, DialogTrigger, DragPreview, FileTrigger, LinkButton, MenuTrigger, SubmenuTrigger, ToggleButton, ToggleButtonGroup, TooltipTrigger, UnavailableMenuItemTrigger
- **Forms and selection:** Autocomplete, Checkbox, CheckboxGroup, ComboBox, ComboBoxItem, ComboBoxSection, DropZone, Form, NumberField, Picker, PickerItem, PickerSection, Radio, RadioGroup, RangeSlider, SearchField, SelectBox, SelectBoxGroup, Slider, Switch, TextArea, TextField
- **Date and time:** Calendar, DateField, DatePicker, DateRangePicker, RangeCalendar, TimeField
- **Color:** ColorArea, ColorField, ColorSlider, ColorSwatch, ColorSwatchPicker, ColorWheel
- **Content and media:** Avatar, AvatarGroup, Badge, CenterBaseline, Content, Divider, Footer, Header, Heading, IllustratedMessage, Image, ImageCoordinator, Keyboard, LabeledValue, Link, NotificationBadge, Provider, Skeleton, SkeletonCollection, StatusLight, Text
- **Cards:** AssetCard, Card, CardPreview, CardView, CollectionCardPreview, ProductCard, UserCard
- **Collections and data:** Cell, Collection, Column, EditableCell, ListView, ListViewItem, Row, TableBody, TableFooter, TableHeader, TableView, TreeView, TreeViewItem, TreeViewItemContent, TreeViewLoadMoreItem
- **Navigation and disclosure:** Accordion, AccordionItem, AccordionItemHeader, AccordionItemPanel, AccordionItemTitle, Breadcrumb, Breadcrumbs, Disclosure, DisclosureHeader, DisclosurePanel, DisclosureTitle, SegmentedControl, SegmentedControlItem, SideNav, SideNavHeader, SideNavItem, SideNavItemContent, SideNavItemLink, SideNavSection, Tab, TabList, TabPanel, Tabs, Tag, TagGroup
- **Feedback and overlays:** AlertDialog, ContextualHelp, ContextualHelpPopover, CustomDialog, Dialog, DialogContainer, FullscreenDialog, InlineAlert, Menu, MenuItem, MenuSection, Meter, Popover, ProgressBar, ProgressCircle, ToastContainer, ToastQueue, Tooltip

## Intentional addition

`components/shared/s2Primitive.jsx` 是导入层唯一 helper，用于 DRY 地生成轻量视觉预览；它不是 S2 公共 API。

## 索引与验证

- 单文件总览：`preview.html`
- 机器清单：`_ds_manifest.json`
- 运行时 bundle：`_ds_bundle.js`
- Adherence 规则：`_adherence.oxlintrc.json`
- 再生成：`node tools/regenerate.mjs`，随后运行 compiler、checker 和 preview builder。

## 参考文档与引用

- 本地源：`C:\haodev\ownword\reference\react-spectrum-main\react-spectrum-main`
- 公共导出：`C:\haodev\ownword\reference\react-spectrum-main\react-spectrum-main\packages\@react-spectrum\s2\exports\index.ts`
- S2 styling：`C:\haodev\ownword\reference\react-spectrum-main\react-spectrum-main\packages\@react-spectrum\s2\style\spectrum-theme.ts`
- 上游仓库：https://github.com/adobe/react-spectrum
- 上游文档：https://react-spectrum.adobe.com/s2/
- 包版本：`@react-spectrum/s2@1.6.0`
- Token 版本：`@adobe/spectrum-tokens@14.15.0`
- 许可：Apache-2.0；见 `LICENSE.source.txt`、`NOTICE.source.txt` 和 `SPECTRUM-TOKENS-LICENSE.source.txt`。
- 上游 Git commit 不在此解压快照中，无法可靠记录。
