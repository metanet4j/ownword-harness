# progress.md

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
- 风格探索阶段页面用静态 HTML + 设计系统 token（未挂 React bundle），符合“html 文件即可，可预览”要求；后续高保真交互原型（design-001）再按 bundle 组合组件。

### 待办
- 用户审阅三版后选择方向，反馈进入 design-001 高保真原型。

### 风险 / 待确认
- 字体 `adobe-clean-*` 来自 Adobe Typekit 远程，离线时回退系统字体（设计系统 readme 已知边界）。
- 页面文案（立言者、铭文内容等）为演示性样例，非产品既定文案，需用户确认后进入正式原型。
