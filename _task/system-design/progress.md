# progress.md
## 2026-09-01 design-002 美学 P1b+P1c：字阶/图标/FAB + 页面减负（commit 167dc31）

### 完成项
- P1b 零碎打磨：字号全部对齐 S2 阶（10/11/12/14/16/18/20/22/25/28/32/36），清掉半档；`.kicker`/`.auth-kicker` 字距 0.22→0.18em；`.hero-zh` 0.09→0.05em、hero-sub 行高 2→1.8；Public 返回按钮换 S2 ChevronLeft（新增源图标资产并暴露 `IconChevronLeft`）；Demo FAB 改 40×40 icon-only，保留 aria-label/title。
- P1c 页面减负：`.panel` 去掉 inset 受光边、padding 26→24、只保留 S2 阴影；首页 hero 底部 52→64、welcome-band 底部 64→80、三问 gap 44→48（`--q-gap` 同步，焦点公式自动对齐）、原则行 padding 22→24；review/public 两栏 gap 22/26→24；My 页 hero 不再使用 panel，BAP ID + Bio + Details 合并进单个 `my-identity-panel`（内部 hairline 分区），去掉重复的 ACTIVE 状态胶囊。

### 验证结果
- 真实 Chrome 1440×900 Light：三问焦点 397/720/1043 与列心逐一相等；hero-sub 16px/1.8、hero-zh 22px/0.05em、q-title 22px/q-zh 14px 均符合 S2 阶；Demo FAB 40×40 无文字。
- My 页：面板数由 3 个降为 1 个（`.my-identity-panel`），hero 无 panel 类，无 ACTIVE 胶囊，BAP ID/Bio/Details 同面板内 hairline 分区。
- 320×568：en CTA top=442、zh CTA top=335，均首屏可见；My 页 panel 284px、无横向溢出。
- 性能：1440 下 120 帧 p50=16.7ms / p95=16.9ms / max=17.1ms，0 帧>34ms。
- Babel/ds errors 为空；HTTP 全资源 200（含 ChevronLeft SVG）。
- 提交 167dc31（PRD v0.1_20260901-104821），独立子仓库。

### 待办
- 用户视觉复核“干净清爽”这一版；如对 My 页合并/去状态胶囊不满意，可单独回退或微调。
- 尚未动：顶栏/Footer 重排、Review 页信息减负、首页穹顶透明度等可选优化。

## 2026-08-31 design-002 美学 P1a：仅按钮统一 + 动效 + 阴影（commit 3b6d77f）

### 完成项
- 按用户要求只落“按钮统一 + 动效 + 阴影”这一组，不动字阶/返回图标/Demo FAB/输入框圆角，也不动首页穹顶。
- 按钮统一：删除 `index.html` 的 `.btn/.btn-primary/.btn-secondary/.btn-negative/.btn-quiet/.btn-sm` 整套自定义样式，新增全局 `.s2d-button { min-height:40px; padding:0 22px; gap:8px; font-size:14px; border-radius:999px }`；`app.jsx` 弹窗与授权弹窗、`screens-identity.jsx` 6 处、`screens-public.jsx` 返回按钮全部改 `<S2Button variant=… onPress=…>`；删除 `.hero-actions/.form-actions` 对 S2Button 的 8px 圆角与 padding 覆盖；`.bapid-box/.bapid-line` 选择器迁移到 `.s2d-button`；`.avatar-actions` 加 `align-items:flex-start`。
- 阴影回 S2：`--shadow-card` 保留 1px 接触阴影 + `0 8px 24px .16`（elevated）；dialog/demo-panel `0 12px 28px .22`（dragged）；toast `0 8px 24px .16`。
- 动效：`.view` 0.38s→0.18s 并加 8px 上移；dialog/demo-panel `dialog-in 0.2s→0.18s`。

### 验证结果
- 真实 Chrome 1440×900 Light：首页 CTA、授权弹窗、Setup、My、Public 全部按钮 40px/999px/14px/700；无 `.btn` 类或选择器残留。
- 卡片计算阴影含 `0 8px 24px .16` + 1px 接触边；demo-panel 阴影 `0 12px 28px .22`、动画 0.18s；`.view` 动画 0.18s。
- 320×568：CTA top=442 首屏可见、无横向溢出。
- 性能：1440 下 120 帧采样 p50=16.7ms / p95=17.1ms / max=24ms，0 帧>34ms。
- Babel/ds errors 为空；HTTP 全资源 200。
- 提交 3b6d77f（PRD v0.1_20260831-235334），独立子仓库。

### 待办
- 用户视觉复核本组；确认后再决定是否继续“字阶/字距”“返回图标”“Demo FAB”等第 5 项零碎打磨。

## 2026-08-31 design-002 美学 P0 落地（commit 9182ade）

### 完成项
- 按用户确认落地美学建议第 1/2/3 项（仅 designs/own-word-prototype-002，独立子仓库提交 9182ade）：
  - PageHead 增加 52px 地平线 + 5px 焦点；StateView 由三圈圆环改为“双穹顶弧 + 地平线 + 焦点核心”，图标反白；三原则账目行加 hairline 分隔；3D 卡正面由 1 弧补为 3 弧（透明度 0.55/0.38/0.24）。
  - `.hero-title .dim` 由 ink-strong 改为 ink-dim；zh 态隐藏与 h1 同文的 `.hero-zh`；My Identity 页 PageHead 由姓名改为 `my.title`（en Your identity is live / zh 你的身份已发布），serif 姓名只出现一次。
  - 三问地平线焦点与列心对齐：`.questions-band` 定义 `--q-gap`，`.questions-horizon` 计算 `--q-col-edge`，焦点 left 用该值；≤960px 单列隐藏两侧焦点，保留中间焦点。
- 数据字典新增 en/zh `my.title`。

### 验证结果
- 真实 Chrome（agent-browser）1440×900 Light：三焦点圆心 x=399/720/1041，与三列圆心完全相等（改动前外侧各偏 111px）；hero-title 第二行计算色 light rgb(80,80,80) / dark rgb(175,175,175)，与第一行分层。
- 状态页（连接取消）：state-emblem 结构 arc/arc.r2/horizon-line/core/icon 齐全，88×88 盒内 arc 78×46 与 50×33，地平线 y=52，icon path fill=#fff。
- PageHead line 52×1 + focal 在 Setup/My 均渲染；My 页姓名仅在 `.my-name` 出现一次。
- Public 3D 卡正面 `.dome-arc` 3 条，inset/opacity 符合预期。
- 响应式：960×800 与 320×568 无横向溢出；≤960 可见焦点数 1；320×568 Connect CTA top=442 首屏可见。
- HTTP 200；Babel 全脚本渲染无错误（home/setup/my/public 与取消状态均走通）。

### 待办
- 用户视觉复核本轮改动；确认后再决定是否继续第 4/5 项（S2 一致性按钮/圆角/阴影/动效与零碎打磨）。

## 2026-08-29 design-002 穹顶恢复到 V6（commit bcd886e）

### 完成项
- 用户确认按 V6 恢复。仅回滚首页穹顶区域：
  - `theme.jsx`：移除 Canvas 潮汐实现（Canvas/rAF/ResizeObserver/MutationObserver/DOME_* 参数），改回 V6 的 6 个 `<div class="arc">`，inset 8% 起每条 +6%、opacity 0.70 起每条 -0.05；外圈由 `.dome-hero` border 提供，共 7 条线。
  - `index.html`：`.dome-hero` 背景/边框恢复 V6 写法；`.dome-canvas` 删除；地平线恢复 1px 实线 opacity 0.6；焦点恢复 16px 静态，删除 `focal-breathe` 动画。
- 保留范围外修改：纸纹（无 mix-blend-mode）、字体/材质/三问三原则、3D 停驻旋转、以及全部交互修复；320px 下仍保留穹顶高度 112px 的响应式优化。

### 验证结果
- 真实 Chrome（本地 vendor React/Babel 测试，最终 HTML 已恢复 unpkg 引用）：穹顶 6 个 `.arc`、无 `.dome-canvas`、`focal animationName=none`。
- 性能：360 帧 rAF 采样 p95=16.8ms、0 帧超过 34ms（纯静态，无动画循环）。
- 320×568：无横向溢出、Connect CTA top=442 首屏可见；弧线宽度 207/177/148/118/89/59 等比排列。
- axe home 0 violations；Dark 下弧线 border 计算为 `rgb(68,68,68)`、地平线 opacity 0.6。

### 决策
- 穹顶线条最终回到 V6 静态版；不保留任何线条动画。
- 后续不再对穹顶线条增加逐帧动画；如需要动效，只允许 CSS 过渡/淡入这类低成本方案。

### 待办
- 用户复核静态七线观感；继续整体视觉复核，定稿后 flip `_d_meta.json`。

## 2026-08-29 design-002 穹顶动画卡顿排查与修复（commit 598bc6a）

### 现象与排查
- 用户反馈：首页穹顶线条动画无律动美感，且导致页面卡顿。
- 实测（1440×900 真实 Chrome，rAF 间隔采样 360 帧）：
  - 修复前静止状态 p50=16.7ms / p95=50.0ms / max=66.7ms，20/360 帧超过 34ms；
  - 模拟鼠标扫过穹顶时 max=116.6ms，长期任务出现；DevTools trace 5s 内 Paint 160.9ms、UpdateLayoutTree 162.7ms、Layerize 86.2ms、FunctionCall 279.7ms。
- 根因（两个叠加）：
  1. `theme.jsx` 的 SVG 实现每帧用字符串重建 6 条 path 的 `d` 并 `setAttribute`，且 `.arc-glow` 带 `filter: blur(2px)`，即使静止也在 60fps 全量重绘；鼠标拨弦模型每条弦按最近点独立激励 + 端点反射，相位互相干扰，视觉上“乱”而不是“律动”。
  2. `body::before` 纸纹使用 `mix-blend-mode: multiply`（dark 为 overlay），固定层与动画层叠加时强制全视口重合成；实验：仅把 blend 改为 normal，同样动画 p95 立即降到 16.8ms。

### 修复
- `theme.jsx` 改为 **Canvas 潮汐节律**：6 条弧线共享单一时间相位，内圈先起、按 `DOME_PHASE_STEP=0.62` 向外依次错开；每条弧线叠加两端固定（sin 包络）的 2 波数行进横波；accent 光晕用更宽描边替代 blur。
- 主题切换：MutationObserver 监听 `data-color-scheme`，Canvas 描边颜色从 CSS 变量（`--line` / `--accent`）重新读取；resize 用 ResizeObserver。
- `prefers-reduced-motion`：Canvas 只画一次静态弧线，不再启动 rAF。
- `index.html`：纸纹去色（feColorMatrix saturate=0）、去掉 `mix-blend-mode`，只保留 0.04（dark 0.05）透明度。

### 验证结果
- 修复后（1440×900 真实 Chrome，预热后连续 3 轮 360 帧采样）：p95=16.7 / 16.8 / 16.8ms，0 帧超过 34ms；3s PerformanceObserver（非 buffered）0 个 long task。
- 动画确实变化：Canvas `toDataURL` 间隔 700ms 前后不一致；reduced-motion 下 800ms 前后完全一致（静态）。
- Dark 主题：切到 dark 后 Canvas 非透明像素 25,546 且平均 RGB 偏向 accent 蓝，说明颜色监听生效。
- 320×568：Canvas 尺寸 246×111、无横向溢出、Connect CTA top=442 首屏可见；axe home 0 violations。
- HTTP 全资源 200。

### 决策
- 放弃“鼠标拨弦 + SVG path 逐帧变形”方案：交互不可预期、相位互相干扰，且 DOM 逐帧 path 更新 + blur 无法在满幅穹顶上稳定 60fps。
- Canvas 只负责穹顶装饰层，不参与 DOM/无障碍语义（父级 `aria-hidden`）；主题/尺寸变化通过观察器同步，不重挂载 React。
- 纸纹今后禁用 `mix-blend-mode`，纹理只允许低透明度普通 alpha 合成。

### 待办
- 用户复核新“潮汐”节律的幅度/速度/方向（可调参数：`DOME_OMEGA / DOME_PHASE_STEP / DOME_WAVES / amp`）。
- 继续视觉复核整体质感；定稿后 flip `_d_meta.json`。

## 2026-08-29 design-002 质感与交互打磨（commit bedc658）

### 完成项
- 按“纸上墨线与天光”方向执行 material pass（用户确认按建议执行，方向默认：英文主标保留 sans 800，中文口号与用户话语用 serif；3D 卡 Light=纸页、Dark=墨岩刻字）。
- 材质：body 增加 1–2% SVG 纸纹（light multiply / dark overlay）；面板改为受光边 + 更深纸影；顶栏由玻璃 blur 改为实底纸/墨 + hairline。
- 字体三角色：界面框架 sans；姓名/命题/用户话语 serif（Review/My/3D 姓名加签名线，Bio 改 blockquote 引文块）；BAP ID/TxID/Proof mono。
- 母题重构：三问由三张 qcard 改为“一条两端淡出的地平线 + 三个焦点 + 居中 serif 问题”；三原则改为无卡片账目行（01/02/03）；kicker/q-num/chain-num/demo 标题 accent 蓝收拢为中性，accent 只留给焦点、主行动、品牌签名。
- 穹顶动画调沉：弧线非等距（外疏内密）、透明度指数递减、粗细 0.5→1.4px；波速/幅度下调、阻尼放长、拨动间隔放宽。
- 3D 公共身份卡：自动旋转由连续 360° 改为正面停留 2600ms → 1800ms 转至背面停留 → 转回；`prefers-reduced-motion` 下自动旋转关闭；厚度侧面改为顶部受光/底部落影渐变。
- Proof/卡背改账目式 hairline 分隔；proof-list 由非法 dl 结构改 ul/li（axe definition-list violation 清零），p3d-controls 补 role=group。
- 交互修复（上一轮 P0 一并落地）：phase 变化 scrollTo 顶部；顶栏 cancelled/failed 不再显示 Connected；dialog max-height calc(100dvh-40px)+overflow（568×320 授权可滚动）；name/bio 长度校验进 validate；desktop footer 右侧预留 132px，避免 Demo FAB 遮挡主题按钮。

### 验证结果
- 真实 Chrome（agent-browser）1440/960/720/390/320，Light/Dark：无横向溢出；320×568 Connect CTA top=442 首屏可见；中文 320 body 1840 无重叠。
- 对比度计算：`--ink-faint` 提升到 82%，Light 4.91:1 / Dark 6.02:1；关键文字均 ≥4.5:1（品牌 span 改用 --s2-accent-color-1000 后 Light 4.49→达标）。
- axe：home 0 violations、review 0、public 0（Light/Dark）；仅剩 S2 按钮/oklch 的 incomplete 自动判定项。
- token：104 个 `var(--s2*)` 引用全部解析（含补定义 `--s2-focus-ring-color`）。
- Chrome 冒烟：连接→Setup→Review→Create→My→Public、连接取消顶栏状态、Edit Save、语言/主题、3D 停驻旋转（实测正面/背面各稳定 316px 宽，转场最窄 12px 仅过渡瞬间）、reduced-motion 下 auto-rotate off 且 transform 静止。
- HTTP 全资源 200（index + 6 jsx + bundle + styles）。

### 决策
- 方向 B：英文主标 sans、中文口号/用户话语 serif；比全衬线更贴合 S2 且不会退回 design-001。
- Demo FAB 保留右下；footer 在 ≥721px 视口加右侧安全区，主题按钮实测与 FAB 重叠面积 0。
- 纸纹用 body::before 固定层，不改 token 色板；卡片背面颜色问题（light-dark 在 background 多层列表被解析为 none）用 background-color 单独声明解决。
- design-002 继续 in-progress，等待用户视觉复核后再决定是否 flip `_d_meta.json` 状态。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-002/index.html`（重点：纸纹颗粒浓度、三问地平线构图、serif 签名块、3D 卡正/背停驻节奏、Dark 墨岩质感）。
- 复核后按反馈迭代；定稿后 flip `_d_meta.json` assets 状态并更新 feature_list doneCriteria 证据。


## 2026-08-18 选定 design-002 为最终视觉方向（其他封存）

### 决策
- 用户选定 design-002「穹顶与地平线」为最终视觉方向，design-001（碑铭/印章）、design-003（新大陆/Territory）、styles-001（三版风格探索）暂封存（`feature_list.json` status=archived，目录保留不删）。
- `feature_list.json`：`activeItem` = design-002，design-002 status=in-progress（继续按用户要求迭代，直到定稿版本）；allowedStatuses 新增 `archived`。
- 后续所有视觉迭代只落在 `designs/own-word-prototype-002/`，不再动 -001/-003/styles。

### 待办
- 用户逐条提出 design-002 修改要求，逐条实现、验证、提交，直至定稿。

## 2026-08-18 design-002 迭代：钱包授权 + 穹顶点击动画（commit 6d1058f）

### 完成项
- 钱包授权弹窗（核心认知不变量 11 + §6.3 统一高影响操作流）：所有需钱包签名的操作先经 Wallet 确认，覆盖 v0.1 三个操作：
  - Connect Wallet → 授权连接（Approve → connecting → resolve；Reject → Connection cancelled）
  - Create Identity → 授权身份发布（Approve → creating；Reject → Creation cancelled，保留 profile 值）
  - Save Profile → 授权 Profile 更新（Approve → saving；Reject → Saving cancelled，保留编辑值）
- 新增 `WalletAuthDialog` 组件（app.jsx）：模拟 Yours Wallet 请求，展示操作标题 + Identity（name + 完整 BAP ID 可复制，仅 create/save）+ 影响说明 + Approve/Reject；点 backdrop = Reject（模拟关闭钱包请求）。
- 三个入口改走 `requestAuth('create'|'connect'|'save')`；cancelled/failed 的 Try Again 重试同样重新走授权。
- Demo 注入语义：`fail` = Approve 后处理失败；`reject` = Approve 后钱包层拒绝（保住故障注入测试能力）。
- 首页穹顶点击操作性动画：`.hero-sky` 由纯装饰改为可点击（role=button + tabindex + 键盘 Enter/Space + focus-visible），点击触发「弧线依次点亮（arc-lit，stagger）+ 焦点脉冲（focal-pulse）+ 地平线扫光（horizon-scan）」动画并同时触发连接授权；760ms 后动画归位，可重复点击；`prefers-reduced-motion` 降级。

### 验证结果
- jsdom 冒烟 30/30 PASS（穹顶 role/点击→授权、连接 approve/reject、Create 授权 approve、Save 授权 approve/reject 保留值）。
- HTTP 全资源 200（index + 6 jsx + bundle + 3 css）。
- Token 66 个 `var()` 引用全解析（`--icon` 为注释 `--iconPrimary` 的正则误报，实际已定义）。
- Babel 6 文件转译通过（jsdom 加载时真实转译）。
- 真实 Chrome：授权弹窗亮色（Approve accent 蓝 `rgb(59,99,251)` 白字、居中 480×296、connect 无 BAP ID 块）/ 暗色（Approve `rgb(86,129,255)` 白字、Reject 深灰 `rgb(27,27,27)` 底浅字可见）；穹顶点击后 `rippling` class + `arc-lit`/`focal-pulse` 动画同步触发、800ms 后移除。

### 决策
- 授权范围仅 Connect/Create/Save 三个签名操作；Disconnect、Account Switch、Copy 不需签名授权（PRD 待确认 3 结论：Disconnect 只断开会话）。
- 授权弹窗复用现有 `.dialog` 视觉 + 穹顶 Mark，不引入新设计系统组件（S2 无现成 wallet 授权组件）。

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

### 缺陷修复（第三次提交 5d68566）
- 浏览器复核发现：S2Button 按钮（Connect/Review/Create 等）在亮色模式下看不到——`components.css` 的 `--s2d-accent`/`--s2d-text`/`--s2d-border-strong`/`--s2d-layer` 等别名只定义在 `.s2{}` 作用域内，而 bundle 渲染的按钮（`s2d-button s2d-button-accent`）未挂 `.s2` 类，导致 `var(--s2d-accent)` 无法解析、按钮 background 透明 + `color:white` → 白底白字不可见。
- 修复：在 `index.html` 的 `:root` 层补定义这组 `--s2d-*` 别名，值引用 `s2-tokens.css` 的 `:root` 级 token。
- 验证（真实 Chrome）：accent 按钮亮色 `rgb(59,99,251)` 底白字、暗色 `rgb(86,129,255)` 底白字；secondary 按钮暗色 `rgb(27,27,27)` 底 + 边框 `rgb(57,57,57)`；StatusLight 圆点 `rgb(5,131,78)` 正常；37 个 `var(--s2*)` 引用全部解析；jsdom 冒烟 34/34 仍全过。
- 注：此缺陷为 design-001/002/003 三版共有（design-001 的 `--accent: var(--s2d-accent)` 同样失效），本任务仅修复 design-003，未回改 001/002。

### 图标暗黑不可见修复（第四次提交 b70a15f）
- 浏览器暗黑复核发现：26 个 S2 图标（语言/主题/复制/编辑/锁定/旋转/提示等）在暗黑下不可见。根因：图标 SVG 文件内 `fill="var(--iconPrimary, #222)"`，而 `icons.jsx` 用 `<img src>` 加载 SVG，`<img>` 加载的 SVG 是独立文档、CSS 变量不跨 img 边界继承，恒 fallback 深灰 `#222`；且 `--iconPrimary` 在设计系统里根本未定义（它本意配合内联 SVG）。亮色可看，暗黑 `#222` 图标在深底上几乎同色。
- 修复（用户选方案 B）：① `icons.jsx` 由 `<img>` 改为内联 SVG（26 个 SVG 内容生成进 `ICON_SVGS`，`Icon` 组件用 `dangerouslySetInnerHTML` 渲染 `<span class="icon">`，fill 继承页面变量）；② `index.html` `:root` 定义 `--iconPrimary: var(--s2-neutral-content-color-default)`；③ 清理 CSS 图标 `img` 尺寸选择器（改为 `.icon`，保留 `.avatar-preview img` 真实头像图与 `.demo-note/.banner` 间距）。
- 验证（真实 Chrome）：暗黑图标 `path` 计算 fill=`rgb(219,219,219)` 浅灰可见、亮色 `rgb(41,41,41)` 深灰正常；Babel 6 文件通过；37 个 `var(--s2*)` 解析；jsdom 冒烟 34/34 连跑 3 次全过。

### 视觉微调（第五、六次提交 3be82e0 / d7c1c2a）
- 用户反馈刻度尺（`.sheet-ruler` 整条）气质突兀、与「新大陆」制图主题冲突。先改为 sheet 左上角 9×9 小十字坐标标，用户再次反馈连十字标也去掉，最终 sheet 回归干净图纸（无 ruler、无十字标）。删除 JSX 全部 8 处 `<span class="sheet-ruler">` 与 CSS `.sheet-ruler`/`.sheet::before` 规则。
- 验证：Babel 通过；jsdom 冒烟 34/34；浏览器确认 ruler/十字标均已无；37 个 token 解析。

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

### 缺陷修复（34bf968，与 design-003 同类问题）
- 用户指出暗黑模式下按钮/图标不展示，排查发现与 design-003 相同的两处根因，一并修复：
  1. S2Button 按钮透明：`components.css` 的 `--s2d-accent`/`--s2d-text`/`--s2d-layer`/`--s2d-border-strong` 等别名只在 `.s2{}` 作用域定义，bundle 渲染的按钮未挂 `.s2` 类 → `var(--s2d-accent)` 无法解析、按钮背景透明 + `color:white` → 白底白字不可见。修复：`index.html` `:root` 补定义这组 `--s2d-*` 别名。
  2. 图标暗黑不可见：26 个图标 SVG `fill="var(--iconPrimary, #222)"` 经 `<img>` 加载，`<img>` 的 SVG 是独立文档、CSS 变量不跨边界继承，恒 fallback 深灰 `#222`，暗黑下与深底同色。修复：`icons.jsx` 由 `<img>` 改为内联 SVG + `:root` 定义 `--iconPrimary: var(--s2-neutral-content-color-default)`；清理 CSS 图标 `img` 尺寸选择器改 `.icon`（保留 `.avatar-preview img`/`.dcard-focal img` 真实图片）。
  3. 顺带补 `S2_Icon_Settings_20_N.svg`（此前 25 个图标缺 Settings，Demo fab 图标 404）。
- 验证（真实 Chrome）：暗黑 Connect 按钮 `rgb(86,129,255)` 底白字、secondary 按钮深灰底浅字、图标 fill=`rgb(219,219,219)` 可见；亮色按钮 `rgb(59,99,251)` 正常；Babel 6 文件通过；36 个 `var(--s2*)` 解析。

### 视觉调整（07f1f84 / abb23fc）
- 用户反馈穹顶弧线太少（原 2 条），要求 7 条。将 Welcome hero `.dome-hero` 的弧线由 2 条（`.arc` + `.arc.arc2`）改为 7 条同心弧：`screens-wallet.jsx` 用 `[0..6].map` 循环生成，内联 `inset` 从 4% 起每条 +6%（4%→40%）内缩、`opacity` 从 0.78 起每条 -0.055 递减；`index.html` 删 `.arc.arc2` 规则、`.arc` 只留基础（position/border/圆角），inset/opacity 由内联 style 控制（DRY）。
- 最终定稿：用户要求「恢复到最初那一版，只是加外圈一共 7 条线（原 8 条多了）」。恢复最初弧线样式 `border: 1px solid var(--line)`（淡色），内弧 6 条（`inset` 8%→38% 每条 +6%，`opacity` 0.7→0.45 递减）+ dome-hero 自身 border 作外圈 = **共 7 条线**。
- 验证：浏览器确认 arcCount=6 + dome border 1px = 7 条线；Babel 通过。

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
