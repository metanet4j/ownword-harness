# progress.md

## 2026-08-18 design-003 新大陆（Territory，全新设计，完成）

### 完成项
- 在 `designs/own-word-prototype-003/` 上全新设计第三版，不复制 design-001/002 的 HTML/CSS/JSX 结构：
  - `index.html`：全新 CSS，几何母题「新大陆/制图」贯穿全站（疆域轮廓 + 边界线 + 坐标网格 + 地标 + 等高线，抽象、克制、无具象建筑）。
  - `screens-wallet.jsx`（Welcome 疆域图 hero + 三问三疆域卡 + 三原则 + 连接/解析状态 + TerritoryMap/BrandMark 单一权威定义）、`screens-identity.jsx`（Setup/Review/Create/My/Edit，面板 map-card 坐标角标 + 虚线边界）、`screens-public.jsx`（疆域 3D 身份卡：正面=迷你疆域图、背面=Proof）、`app.jsx`（状态机 + 顶栏疆域品牌标记 + toast + 对话框 + Demo）。
  - 复用共享事实 `data.jsx`（i18n 字典 + 演示数据）、`icons.jsx`（S2 图标 + bundle 组件解构），未改动。
- 视觉方向（新大陆）：
  - 疆域轮廓：Welcome hero 抽象大陆 SVG（`T_LAND` 疆域轮廓 + `T_CLAIM` 被标注疆域 + 等高线 `T_CONTOUR*` + 坐标网格 graticule + 地标点），隐喻 Identity=被标注的疆域。
  - 边界线：面板 map-card 四角坐标角标 + 虚线边框（chain-panel、detail-list、proof-list、banner 均用 dashed），隐喻 Proof=边界可验证。
  - 坐标：BAP ID 视为可验证坐标，mono 展示；全站 faint graticule 网格背景。
  - 地标：疆域图上的 accent 地标点（带同心环）；三问卡用 Q{n}·A/B/C 坐标号。
  - 品牌标记 BrandMark 为小疆域轮廓（替换 design-001 的「W」与 design-002 的几何弧线 Mark）。
  - 颜色/圆角/字体全部来自 S2 token allowlist（:root 级）。
- 3D 身份卡保留：正面=疆域图（轮廓 + 等高线 + 被标注疆域 + 地标）+ 名称/类型/签名/BAP ID，背面=Proof（边界与标注）；preserve-3d 拖拽旋转 + 自动旋转。

### 验证结果
- HTTP 200：index.html / 6 jsx / _ds bundle / semantic.css / s2-tokens.css / components.css 等全资源。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 经 jsdom 解析零错误（无标签闭合问题）。
- Token 合规：页面 26 个 `var(--s2*)` 引用全部可解析（`:root` 级 token：`--s2d-surface-*`/`--s2d-content-*`/`--s2d-action-*`/`--s2d-status-*`/`--s2d-radius-*`/`--s2d-font-*` 与 `--s2-gray-*`/`--s2-accent-color-*`/`--s2-focus-indicator-color`）。
- jsdom 冒烟（React UMD + 设计系统 bundle + Babel 真实加载）：31 项断言全 PASS——主流程（Welcome 疆域图、Connect→Resolving→Setup、表单校验、Review、Create 成功、My Identity、Public 3D 疆域卡、Edit Save、Discard 对话框、语言、主题、Disconnect）+ 故障注入（连接拒绝/失败、解析失败、重置流程）。

### 决策
- 复用 `data.jsx`/`icons.jsx`（共享事实层，非视觉），只重写视觉与展示层。
- token 用 `semantic.css` 与 `s2-tokens.css` 的 `:root` 级 token（同 design-002 结论，规避 `.s2{}` 作用域别名在 `:root` 不解析的问题）。
- 状态语义、边界、术语严格遵循核心认知与 PRD v0.1；Key Rotation 已下放 v0.1.1，本版不含。
- 疆域路径 `T_LAND`/`T_CLAIM`/`T_CONTOUR1`/`T_CONTOUR2` 在 screens-wallet.jsx 单一权威定义，screens-public.jsx 复用（DRY）。

### 布局重构（第二次提交 56e8d7c）
- 用户反馈：初始版布局与 design-002 骨架相同（顶栏 + 1080px 居中 wrap + welcome 双栏 + 三卡片网格 + review/my/public 双栏），要求重新布局。
- 改为「测绘图册」布局，脱离 design-002 骨架：
  - 左图例竖栏（rail，sticky，含品牌标记 + Journey 行程步骤高亮 + 语言/主题/钱包置底），替换 design-002 的顶部导航栏。
  - 主内容为全幅画布（faint graticule 网格底），非居中 wrap。
  - Welcome = 全幅疆域画布（大图作背景 + 中央 cartouche 题注卡 + 连接按钮）+ 三问「图例带 legend-band」+ 三原则「边界注记带 boundary-strip」（替换三卡片网格）。
  - 表单/Review/My/Edit 全部改单列「测绘 sheet」（顶部刻度尺 ruler + 底部图例栏），替换双栏卡片。
  - Review 的「接下来」由侧边 sticky 面板改为水平「航路带 route-strip」。
  - My Identity 由双栏 my-grid 改为单列 my-body 堆叠 sheet。
- 验证：Babel 6 文件通过；token 26 项解析通过；jsdom 冒烟 34 项断言全过（新增 rail 步骤/图例带/航路带断言）。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-003/index.html`（桌面 1440px / 移动 320px，重点：测绘图册布局观感、疆域画布、3D 卡旋转、主题/语言切换）。复核后 flip `_d_meta.json` 资产状态（当前 needs-review）。
- 三版原型对照评审：`-001`（碑铭/印章）、`-002`（穹顶/地平线）、`-003`（新大陆）。

### 风险 / 待确认
- 无浏览器环境：320px 重叠、3D 拖拽手感、疆域图 SVG 在窄屏的视觉观感只能 DOM 级验证，需人工确认。

## 2026-08-18 design-003 立项（新大陆，方向已定，未实现）

## 2026-08-18 design-002 穹顶与地平线（全新设计，完成）

### 完成项
- 在 `designs/own-word-prototype-002/` 上全新设计，替换原复制基线，不复制 design-001 的 HTML/CSS/JSX 结构：
  - `index.html`：全新 CSS，几何母题「穹顶 + 地平线 + 焦点」贯穿全站。
  - `screens-wallet.jsx`（Welcome 天穹 hero + 三问三焦点连线 + 三原则 + 连接/解析状态）、`screens-identity.jsx`（Setup/Review/Create/My/Edit）、`screens-public.jsx`（穹顶地平线 3D 身份卡）、`app.jsx`（状态机 + 顶栏 + toast + 对话框 + Demo）。
  - 复用共享事实 `data.jsx`（i18n 字典 + 演示数据）、`icons.jsx`（S2 图标 + bundle 组件解构），未改动。
- 视觉方向（穹顶与地平线）：
  - 穹顶：Welcome 大圆弧天穹（`.dome-hero` + 双层同心弧）；顶栏/页头/页脚/3D 卡背使用纯几何 SVG `Mark`（弧 + 地平线 + 焦点，无字母）。
  - 地平线：hero 天/地分割线、页头 `.horizon-line`、三问「一条地平线上的三个焦点」、3D 卡正面的天（52%）/地分割。
  - 焦点：accent 圆点落在每处地平线上，隐喻「我是谁」= 视野中心的一个点。
  - 克制、抽象、无具象建筑；颜色/圆角/字体全部来自 S2 token allowlist。
- 3D 身份卡保留：正面=天穹天空（弧 + 焦点首字母）+ 地面信息，背面=Proof；preserve-3d 拖拽旋转 + 自动旋转。

### 验证结果
- HTTP 200：index.html / 6 jsx / _ds bundle / semantic.css 等全资源。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 容器标签闭合校验通过。
- Token 合规：页面 24 个 `var(--s2*)` 引用全部可解析（用 `:root` 级 token：`--s2d-surface-*`/`--s2d-content-*`/`--s2d-action-*`/`--s2d-status-*`/`--s2d-radius-*` 与 `--s2-gray-*`/`--s2-accent-color-*`）。
- jsdom 冒烟（React UMD + 设计系统 bundle + Babel 真实加载）：32 项断言全 PASS——主流程 24 项（Welcome/穹顶/三焦点、Connect→Setup、表单校验、Review、Create 成功、My Identity、Edit Save、语言、主题、Public 3D、Disconnect、连接拒绝、解析失败）+ 故障注入 8 项（complete/incomplete 分流、创建拒绝/重试、保存拒绝、Account Switch）。

### 决策
- 复用 `data.jsx`/`icons.jsx`（共享事实层，非视觉），只重写视觉与展示层。
- token 用 `semantic.css` 与 `s2-tokens.css` 的 `:root` 级 token；发现 design-001 使用的 `--s2d-background`/`--s2d-text`/`--s2d-accent` 等别名只在 `components.css` 的 `.s2 {}` 作用域内定义，`<html>`/`<body>` 未挂 `.s2` 类时在 `:root` 层不解析，design-002 改用全局 token 规避此问题（仅记录，未回改 design-001）。
- 状态语义、边界、术语严格遵循核心认知与 PRD v0.1；Key Rotation 已下放 v0.1.1，本版不含。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-002/index.html`（桌面 1440px / 移动 320px，重点：天穹/地平线观感、3D 卡旋转、主题/语言切换）。复核后 flip `_d_meta.json` 资产状态（当前 needs-review）。

### 风险 / 待确认
- 无浏览器环境：320px 重叠、3D 拖拽手感、穹顶弧线在窄屏的视觉观感只能 DOM 级验证，需人工确认。

## 2026-08-18 design-002 design-001 对照版（复制基线，已由上方全新设计替代）

### 完成项
- 产出 `designs/own-word-prototype-002/`：design-001 内容一致副本（index.html + 6 jsx + _ds/react-spectrum-s2 + assets/icons + _d_meta.json）。
- 独立 Git 子仓库，commit `30d556d`（(PRD v0.1) 格式）。

### 验证结果
- HTTP 200：index / app.jsx / _ds bundle。
- jsdom 主流程冒烟 35 项断言全过（复用 design-001 测试集，仅路径替换）。

### 决策
- 副本仅作对照基线，内容与 design-001 完全一致；差异化迭代在副本上进行，两版可对照评审。
- 对照差异方向（视觉 / 交互 / 文案等）待用户指定。

### 待办
- 用户指定对照差异方向后，在 own-word-prototype-002 上迭代。

## 2026-08-18 design-001 v0.1 高保真可交互原型

### 完成项
- 产出 `designs/own-word-prototype-001/`：`index.html`（入口）+ `data.jsx`（i18n en/zh + 演示数据）+ `icons.jsx`（S2 workflow 图标 + bundle 组件唯一命名）+ `screens-wallet.jsx` + `screens-identity.jsx` + `screens-public.jsx` + `app.jsx`（状态机 + Demo 控制面板）。
- 导入 react-spectrum-s2 到 `_ds/react-spectrum-s2/`（25 个 S2 workflow 图标复制到 `assets/icons/`），`_d_meta.json` 登记 primaryDesignSystem 与资产。
- 覆盖 PRD v0.1 全部 BDD 场景：Connect 成功/取消/失败、Account Switch、Disconnect、Identity 自动分流（无身份/已发布完整/Profile 不完整）、Setup 表单校验（Name 必填≤100、Bio≤1000、Type、本地图片 Avatar）、Review（完整 BAP ID + Copy + "Your wallet controls this identity."）、Create 成功/取消/失败、My Identity（首屏 BAP ID）、Edit Profile（Saving…/Saved/取消/Discard 对话框）、语言 en/zh（默认 en，持久化，协议值不翻译）、主题 Light/Dark（默认 Light，持久化，状态带图标+文字）。
- 个人身份公共查看：3D 立体身份卡（preserve-3d 正反两面 + 18px 厚度层 + 光泽 + 朱印），自动旋转 + 拖拽旋转 + 重置；右侧 Proof 面板渐进披露完整 BAP ID / TxID / 链上状态。
- 视觉方向：应用主体取版三协议（S2 原生 indigo、新体系感），Welcome 印章卡与 Public 3D 卡取版一碑铭（深色、厚重感、serif 铭文、朱印），融合 styles-001 三版。

### 验证结果
- `http://127.0.0.1:4311/own-word-prototype-001/index.html` 全资源 HTTP 200（7 CSS + bundle + 6 jsx + 25 图标）。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 标签闭合校验 0 错误。
- Token 合规：页面引用 22 个 `var(--s2*)` 全部在设计系统 allowlist 内。
- 运行时冒烟（jsdom + React UMD + 设计系统 bundle 真实加载）：56 项断言全部 PASS——主流程 35 项 + 故障注入 21 项（解析失败、创建取消/失败、保存取消/失败、incomplete 分流、published 分流、Discard 对话框）。
- 修复的真实缺陷：① 多个 `<script>` 顶层 `const {Button}` 重名导致浏览器 SyntaxError → 改为 icons.jsx 统一解构为 `S2*` 前缀；② 视图路由顺序 bug：`resolving` 分支排在 `page==='welcome'` 之后导致解析中显示 Welcome → 调整路由顺序。

### 决策
- 无真实 Wallet/Indexer，连接与发布流程用 Demo 控制面板模拟（右下角 "Demo"）：分流结果三态、注入 7 种故障、Account Switch、Reset。注入在下一次对应操作时生效一次。
- 3D 身份卡为静态深色碑铭质感，不随主题切换（厚重感聚焦）；周边 UI 随 Light/Dark。
- 演示 BAP ID/TxID 为虚构占位值，仅原型演示用，非产品事实。

### 原型对 PRD 与后端设计的影响（需同步事项）
- 无需修改 PRD v0.1：原型严格实现 PRD 范围（Key Rotation 已按待确认结论下放 v0.1.1，不含）。无新增页面、流程或文案禁区违规。
- 后端实现建议（由原型交互揭示，非本任务产出）：
  1. Avatar 本地图片上传：原型为 Data URL 预览；后端需提供上传接口与存储（PRD 待确认已定：本地图片，不支持 URL）。
  2. BAP ID 展示规则：首屏主层级、完整值可复制、缩略 `前4…后8`；后端返回完整原值，展示缩略由前端完成。
  3. 产品状态归一化：原型使用 `Cancelled / Failed / Published / ACTIVE / NOT PUBLISHED` 等产品语义，后端不得直接透出 SDK/Indexer 原始枚举（核心认知 §9）。
  4. 偏好持久化：locale/theme 由前端 localStorage 保存（核心认知不变量 13：不进签名输入、不改链上事实）。
  5. Public Identity 3D 查看依赖 Identity 公开解析数据（BAP ID、Profile、发布交易），与 v0.4 通用 Lookup 解耦，v0.1 仅演示当前钱包身份的公开视图。

### 待办
- 用户视觉复核：桌面/移动视口布局、3D 旋转观感（本环境无浏览器，布局重叠与动画只能 DOM 级验证，视觉观感需人工确认）。
- 用户审阅后按反馈迭代；`_d_meta.json` 资产状态在复核后 flip（approved / changes-requested）。

### 风险 / 待确认
- 无浏览器环境：320px 视口重叠、3D 拖拽手感、主题切换布局位移（CSS 已按断点与固定最小宽度处理，未实机确认）。
- 页面文案为演示性样例（如"立言者"），非产品既定文案。
- Key Rotation 已按 PRD v0.1 待确认结论下放 v0.1.1，原型不含。

## 2026-08-18 styles-001 首页风格探索（三版）

### 完成项
- 产出 `designs/own-word-prototype-styles-001/`：index.html（入口）+ home-ledger.html（版一碑铭）+ home-charter.html（版二宪章）+ home-protocol.html（版三协议）。
- 导入 react-spectrum-s2 设计系统到 `_ds/react-spectrum-s2/`（import-design-system.mjs），并登记 `_d_meta.json`（primaryDesignSystem = react-spectrum-s2，4 个资产）。
- 每版独立自包含 HTML，加载设计系统 7 个 CSS（token 链路），页面仅用 token 变量与页面内定义的局部变量。
- 内容骨架一致：Hero（Own your identity. Own your words.）→ 三问 → 三根原则 → 一段签署话语（BAP ID / TxID / Signature valid / Revision）→ 平台承诺 → Footer。
- 三版视觉方向：
  - 版一 碑铭 The Ledger：暖墨黑底 + 碑金 + serif 铭文 + 印章，深色厚重；
  - 版二 宪章 The Charter：纸色底 + 条款文书 + 签名 + 印泥朱印，浅色信实；
  - 版三 协议 The Protocol：S2 原生 indigo + 卡片 + 等宽协议细节 + 状态徽标，新体系科技感。

### 验证结果
- `python3 -m http.server 4311 --directory designs` 运行中；4 页面 + 7 CSS 均 HTTP 200。
- HTML 标签闭合校验：4 文件全部 OK。
- token 解析检查：页面引用的 `--s2*`/`--s2d*` 系统变量全部存在于 tokens；`--ledger-*`/`--paper` 等为页面内 `:root` 局部变量。
- 修正：`oklch(from ...)` 相对色语法换为 `color-mix`（兼容性）；protocol 版补 `--serif` 局部变量。

### 决策
- 首页指平台 landing page（门户首页），非应用内页面。
- 风格探索阶段页面用静态 HTML + 设计系统 token（未挂 React bundle），符合"html 文件即可，可预览"要求；design-001 高保真交互原型按 bundle 组合组件。

### 待办
- design-001 原型已融合三版方向（见上），styles-001 三版保留供参考。

### 风险 / 待确认
- 字体 `adobe-clean-*` 来自 Adobe Typekit 远程，离线时回退系统字体（设计系统 readme 已知边界）。
- 页面文案（立言者、铭文内容等）为演示性样例，非产品既定文案，需用户确认后进入正式原型。
