# progress.md

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
