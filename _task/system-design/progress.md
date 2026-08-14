# 任务进度

## 当前状态

- 最后更新：2026-08-13
- 当前事项：`design-004`（`in-progress`），待下一位 Agent 从零执行
- 状态：前三套原型已交付并验证，均为对比候选；第四套已立项，等待执行

## 已完成

- [x] 建立任务级工作规则与开工门禁。
- [x] 建立事项状态与跨会话交接机制。
- [x] 明确本目录只保存设计文档，不承担编码任务。
- [x] 初始化 `feature_list.json`，保留一个待开始设计事项。

## 下一步

1. 接收具体 PRD 或实现设计目标。
2. 将 `design-001` 替换为具体事项，并设为唯一 `in-progress` 项。
3. 查阅相关 `spec`、`reference`、代码、日志和数据后开始设计。

## 阻塞与风险

- 当前无具体业务目标，不能录入业务事实或产出设计结论。

## 决策

- 不维护核心认知模板、PRD 模板、实现设计模板或独立评审清单。
- 同时只推进一个事项，完成必须附验证证据。

## 本次文件

- `AGENTS.md`：任务规则。
- `feature_list.json`：事项状态。
- `progress.md`、`session-handoff.md`：进度与交接。

## 验证证据

- [x] 保留文档存在且非空；`feature_list.json` 可解析；最多一个 `in-progress` 事项。
- [x] `init.sh` 已删除；目录无启动或测试脚本。

## 2026-08-13 · design-002

- 当前事项：`design-002`，状态 `in-progress`；`design-001` 暂停为 `blocked`，保证唯一进行项。
- 从零建立 `designs/own-word-prototype-002`；未读取、复制或借鉴 `designs/own-word-prototype`。
- 设计方向：以“身份文档/公开凭证”为主视觉，避免常规卡片后台；使用 React Spectrum 中性色、边框、紧凑控件、语义状态与焦点规范。
- 覆盖：Welcome、Wallet 请求/取消/失败、Identity 解析、Setup、表单校验、Review、创建中、成功、My Identity、完整 BAP ID Copy、Edit Profile、保存/取消、未保存离开保护、Account Switch、Disconnect、中文/英文、Light/Dark、解析失败。
- Key Rotation 依据 PRD 待确认结论下放到 v0.1.1，本原型不包含。
- HTTP：`http://127.0.0.1:4311/own-word-prototype-002/index.html` 返回 200。
- 浏览器：主流程可操作；React Spectrum bundle error 为空；console error 为 0。
- 响应式：1440px 桌面通过；320×740 移动视口 `scrollWidth <= innerWidth`，无横向溢出；移动端隐藏内部“Prototype states”入口，避免遮挡正文。
- 偏好：切换中文和 Dark 后刷新，`lang=zh-CN`、`data-theme=dark` 保留；协议值与用户内容不变。
- 资产：`designs/own-word-prototype-002/_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 待办：用户对比复核后，记录选择结果；复核通过才将 `design-002` 标记 `done`。

## 2026-08-13 · design-003 启动

- 当前唯一事项：`design-003`（`in-progress`）；`design-002` 改为 `blocked`，作为等待对比评审的候选。
- 执行者：下一位 Agent。
- 输出：`designs/own-word-prototype-003`；当前不预建目录，保证下一位 Agent 从零开始。
- 输入只限核心认知、PRD v0.1、React Spectrum；禁止读取两套既有原型的代码、截图、资产、元数据和设计方向。
- 第三套必须独立形成视觉层级、布局结构和交互表达；不得覆盖前两套原型。
- 唯一下一步：下一位 Agent 按门禁读取任务文件，再使用 Baoyu Design 与 React Spectrum 创建、验证第三套原型。

## 2026-08-13 · design-003 实现与验证

- 当前唯一事项：`design-003`（`in-progress`）；`design-002` 保持 `blocked`。
- 输出：`designs/own-word-prototype-003`；从零建立，未读取、复制或借鉴 `designs/own-word-prototype` 与 `designs/own-word-prototype-002` 的代码、截图、资产、元数据或设计方向。
- 方法：按门禁先读 `AGENTS.md`、`feature_list.json`、`progress.md`、`session-handoff.md`，再读核心认知与 PRD v0.1；使用 Baoyu Design 技能，导入脚本绑定 React Spectrum S2 到 `_ds/react-spectrum/`，按 `_ds_prompt.md` 绑定规则用 `--rs-*` 与 `--spectrum-*` 令牌、官方图标资产。
- 第三套视觉与交互独立：工作台应用壳（顶栏 + 状态侧轨 + 右侧身份旅程时间线），BAP ID 用等宽大字号 ledger 展示；不沿用“身份文档/公开凭证”隐喻；Setup 为两步 Profile→Review 向导。
- 覆盖：Welcome、连接取消/失败、解析中/失败、Setup（新建/资料不全）、表单校验、Review、创建中/成功/取消/失败、My Identity、Public Identity、Edit Profile 保存/取消/失败、未保存离开保护、Account Switch、Disconnect、EN/zh-CN、Light/Dark。Key Rotation 不进入本原型（PRD 已下放 v0.1.1）。
- 术语与不变量遵守核心认知：BAP ID 不可编辑、缩略显示但 Copy 返回完整值、取消显示 Cancelled、异常显示 Failed、Wallet 连接不称注册/登录、Locale/Theme 不影响链上值。
- 验证：本地 HTTP `http://127.0.0.1:4311/own-word-prototype-003/index.html` 返回 200；无头 Chrome CDP 自动化 `_verify.mjs` 37/37 通过；React Spectrum bundle `__errors` 为 0；浏览器 console/runtime error 为 0；1440px 桌面 BAP ID 首屏可见；320px 视口 `scrollWidth <= innerWidth` 无横向溢出；语言与主题刷新后持久，BAP ID 跨语言主题不变；复制完整 BAP ID 断言通过。截图：`preview-desktop.png`、`preview-mobile.png`。视觉像素复核跳过（本会话不支持读取图片），以 DOM 几何与计算样式检查替代。
- 资产：`_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 待办：用户并排对比三套方案后反馈选择；复核通过前 `design-003` 不标记 `done`。

## 2026-08-13 · design-004 启动

- 当前唯一事项：`design-004`（`in-progress`）；`design-003` 改为 `blocked`，作为等待对比评审的候选。
- 执行者：下一位 Agent。
- 输出：`designs/own-word-prototype-004`；当前不预建目录，保证下一位 Agent 从零开始。
- 输入只限核心认知、PRD v0.1、React Spectrum；必须使用 Baoyu Design 技能。
- 隔离：禁止读取、复制、导入或借鉴 `designs/own-word-prototype`、`designs/own-word-prototype-002`、`designs/own-word-prototype-003` 的代码、截图、资产、元数据和设计方向；只能写入 `-004` 目录。
- 第四套必须独立形成视觉层级、布局结构和交互表达；不得覆盖前三套原型。
- 验证：HTTP 桌面与 320px 移动视口、主流程、异常状态、语言/主题持久化、浏览器 console；证据写回 `feature_list.json` 与 `progress.md`。
- 状态：用户人工复核前保持 `needs-review`，不得标记 `done`。
- 唯一下一步：下一位 Agent 按门禁读取任务文件，再使用 Baoyu Design 与 React Spectrum 创建、验证第四套原型。

## 2026-08-13 · design-003 修订（按用户反馈）

- 用户反馈：第三套应突出“话语的重量感 + 平台的新大陆感”；上链成功动作后强化印象，可用动效。
- 话语重量感：Hero 标题分两层放大，`Own your identity.` 副级、`Own your words.` 主级大字号；My/Public Identity 姓名大字号粗体，简介加重为陈述体；Review 加“认领”宣言。
- 新大陆感：Hero 加地平线分隔与 `Sovereign identity on Bitcoin` 等宽铭文；身份页加 `bap:0 · Bitcoin` 账本标注。
- 上链成功动效：Create Identity 成功页改为“印章落地”动画（圆环缩放 + 对勾 + PUBLISHED 印章字），随后 Broadcast/Seen/Accepted/Mined 链上状态逐帧出现，Mined 空心待确认，附 `Published · Confirmation pending`；`prefers-reduced-motion` 时关闭动画并直接呈现终态。
- 验证：无头 Chrome CDP `_verify.mjs` 41/41 通过；console/runtime error 0；320px 无横向溢出；语言主题持久、完整 BAP ID 复制等原 37 项不回归；预览图 `preview-desktop.png`、`preview-mobile.png` 已更新。
- 状态：`design-003` 保持 `blocked`（对比候选）；待用户最终挑选。
- 再修订（用户反馈“没有动效”）：Welcome 加进场动效（品牌、标题、副文、地平线、原则、按钮逐层升起），一打开即动；动效默认开启（`data-motion="on"`），Prototype 面板加 Motion 开关可关；OS `prefers-reduced-motion` 下仍可显式开启，关闭后动画全停。验证升至 45/45 通过，含“欢迎进场动画激活、OS 减动效下强制开启、关闭后动画停止”三项断言，console/runtime error 0。
- 三修订（用户反馈“向右箭头进入新大陆”）：首页底部右侧加带 nudge 动效的向右箭头（ChevronRight + Enter 标签）；点击播放 1.2s 航行过渡——地平线扫过、圆点前行、“正在进入新大陆”文案，随后落到 Yours Wallet 连接确认。验证升至 48/48，含“箭头动画激活、voyage 出现、落点钱包确认”三项断言，console/runtime error 0。

## 2026-08-13 · design-004 实现与验证

- 当前唯一事项：`design-004`（`in-progress`）；前三套保持 `blocked` 候选。
- 输出：`designs/own-word-prototype-004`；从零建立，全程未读取、复制或借鉴前三套原型的代码、截图、资产、元数据或设计方向。
- 方法：按门禁读 `AGENTS.md`、`feature_list.json`、`progress.md`、`session-handoff.md`，再读核心认知与 PRD v0.1；Baoyu Design `import-design-system.mjs` 绑定 React Spectrum S2（primary），遵循 `_ds_prompt.md` 的 `--rs-*`/`--spectrum-*` 令牌约束与官方图标资产。
- 第四套视觉与交互独立：单列引导式聚焦舞台——每步只有一个居中面板，钱包驻留顶栏胶囊与下拉菜单；Yours Wallet 以深色标题栏模拟窗口弹层呈现授权；BAP ID 用带边框 ID 铭牌（等宽、整值换行、右上 Copy）表达。Setup 为单页表单 + 独立 Review 面板；不使用步骤轨、时间线或身份文档隐喻。
- 覆盖：Welcome、连接取消/失败、解析中/失败、Setup（新建/资料不全）、表单校验（必填名、100/1000 字数上限、本地图片头像）、Review、创建中/取消/失败/成功、My Identity、Public Identity、Edit Profile 保存/取消/失败恢复、未保存离开保护、Account Switch（终止敏感操作后重新解析）、Disconnect、EN/zh-CN、Light/Dark。Key Rotation 不进入本原型（PRD 已下放 v0.1.1）。
- 术语与不变量遵守核心认知：Wallet 连接不称注册/登录；BAP ID 不可编辑、Copy 返回完整值；用户拒绝为 Cancelled，系统异常为 Failed；Locale/Theme 不影响协议值；状态含文字不只靠颜色。
- 环境备注：unpkg CDN 不可达，React 18.3.1 UMD 从 npmmirror 下载 vendored 至 `vendor/`；Babel standalone 用技能自带 vendor 副本。
- 验证：本地 HTTP `http://127.0.0.1:4311/own-word-prototype-004/index.html` 返回 200；无头 Chrome CDP `_verify.mjs` 49/49 通过；console/runtime error 0；Copy 断言传入完整 BAP ID；复制失败时 BAP ID 仍可见；语言与主题刷新后持久；BAP ID 跨语言主题不变；1440px BAP ID 首屏可见；320×740 各关键页 `scrollWidth <= 320` 无横向溢出。截图：`preview-desktop.png`、`preview-mobile.png`。视觉像素复核以 vision probe 结果为准，DOM 几何与计算样式检查已完成。
- 资产：`_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 待办：用户并排对比四套方案后反馈选择；复核通过前 `design-004` 不标记 `done`。

## 2026-08-13 · design-003 再迭代（首页进入流）

- 用户反馈：首页不保留 Connect Wallet 按钮；右箭头点击或右滑进入新页；连接钱包居中并带动效，点击后进入区块链新大陆。
- 状态：`design-003` 转为唯一 `in-progress`；`design-004` 转为 `blocked`，保持交付候选。
- 实现：Welcome 移除 Connect Wallet CTA，只留右箭头与“点击箭头或向右滑动”提示；箭头点击或右滑（pointer 横移 > 60px）进入新页 Wallet gateway；连接钱包居中，带脉冲光环动效；点击连接播放 1.2s 航行过渡后落到 Yours Wallet 确认；连接取消按 BDD 返回 Welcome；连接失败场景落在 gateway 显示失败与 Try Again；修复无钱包时 `stage` 残留 272px 空列导致内容左偏，空壳下单列铺满。
- 文案：`gatewayTitle`、`gatewaySub`、`walletGateNote`、`swipeHint` 写入 `strings.jsx`，EN/zh-CN 双语。
- 验证：无头 Chrome CDP `_verify.mjs` 53/53 通过：Welcome 无连接按钮、箭头进 gateway、连接按钮居中且 `::after` 动画 `gateway-pulse`、返回按钮回 Welcome、右滑进 gateway、航行出现、落点钱包确认；原连接/创建/复制/主题语言/切换断开等不回归；320px 无横向溢出；console/runtime error 0。截图新增 `01b-gateway-desktop-light.png`、`06b-gateway-320-dark-zh.png`；`preview-desktop.png` 更新为 gateway，`preview-mobile.png` 更新为 320 首页。
- 资产：`_d_meta.json` 保持 `index.html` 状态 `needs-review`。
- 待办：用户复核首页进入流与整体厚重感方向；复核通过前 `design-003` 不标记 `done`。

## 2026-08-13 · design-003 又修订（金属配色 + 偏好合并）

- 用户反馈：配色要有金属感；语言与主题切换合并，不再在顶栏并排两段，太丑。
- 实现：`styles.css` 调语义令牌为冷钢中性色——Light 画布 `#e9ebee`、表面 `#f7f8fa`，Dark 画布 `#17181b`、表面 `#202226`；卡片、顶栏、对话框、弹层等表面加顶部高光渐变（`--rs-metal-hi`），accent 按钮与 gateway 连接按钮加轻高光，形成拉丝金属感；保留单一 accent 与语义色，不加彩色镀铬。
- 合并：新增 `PreferencesMenu`，顶栏只留一个偏好胶囊（当前语言 · 当前主题），点开弹层内含 Language、Theme 两行 segmented 控件；`strings.jsx` 加 `preferences` 文案，EN/zh-CN 双语。
- 验证：无头 Chrome CDP `_verify.mjs` 56/56 通过：语言+主题合并为一控件、偏好弹层打开、Dark/zh-CN 在弹层内切换并持久、金属表面高光存在、Light/Dark 画布令牌色值正确；原 53 项不回归，console/runtime error 0，320px 无横向溢出。`preview-desktop.png` 更新为 My Identity 浅色，`preview-mobile.png` 更新为 My Identity 320 深色中文。
- 资产：`_d_meta.json` 保持 `index.html` 状态 `needs-review`。
- 待办：用户复核金属质感强度与偏好弹层交互；复核通过前 `design-003` 不标记 `done`。

## 2026-08-13 · design-003 三改（阴影与光泽立体感）

- 用户反馈：整体加阴影，要金属散发光泽或宝石光泽的立体感。
- 实现：`styles.css` 加 `--rs-shadow-soft`、`--rs-glow`、`--rs-edge-hi/lo`、`--rs-accent-glow` 令牌，Light/Dark 同步。表面改双层高光（顶部高光 + 左上径向镜面光斑）+ 底部内阴影；卡片、顶栏、芯片等加环境软阴影与内边缘高光，浮层用加深阴影；accent 按钮与 gateway 连接按钮加珠宝式径向光泽 + 蓝色辉光阴影 + 内高光；品牌标与头像加光泽。修复 hover 时 `background` 简写吞掉光泽的问题，改 `background-color`。
- 验证：无头 Chrome CDP `_verify.mjs` 57/57 通过：新增“3d shadow + luster on surfaces/buttons”断言，Light/Dark 画布色值不变；原 56 项不回归，console/runtime error 0，320px 无横向溢出。`preview-desktop.png`、`preview-mobile.png` 已更新。
- 资产：`_d_meta.json` 保持 `index.html` 状态 `needs-review`。
- 待办：用户复核阴影与光泽强度；复核通过前 `design-003` 不标记 `done`。

## 2026-08-13 · design-003 四改（去后台感，单列聚焦）

- 用户反馈：当前布局偏管理后台；保持与全新访客首页一致，内容居中，去掉两边区域，干净、整洁、聚焦。
- 实现：`app.jsx` 删除 `Rail`、`Journey` 组件与渲染，应用壳改为主内容区直接居中；`styles.css` 删除 shell/rail/stage/journey 相关规则与响应式分支，`.panel` 加 `margin-inline:auto` 居中；`strings.jsx` 删除导航与旅程相关文案。顶栏（品牌、偏好胶囊、钱包状态）保留。
- 验证：无头 Chrome CDP `_verify.mjs` 58/58 通过：新增“side panels removed + content centered”断言（无 `.rail`、无 `.journey`，面板中心与视口中心差 < 8px）；原 57 项不回归，console/runtime error 0，320px 无横向溢出。`preview-desktop.png`、`preview-mobile.png` 已更新。
- 资产：`_d_meta.json` 保持 `index.html` 状态 `needs-review`。
- 待办：用户复核居中聚焦效果；复核通过前 `design-003` 不标记 `done`。

## 2026-08-13 · design-003 五改（A+B 碑刻航图，去编号步骤）

- 用户反馈：BAP 页面像管理后台；选 A+B 方案（碑刻 + 航图），但不要 1/2/3 编号步骤。
- 实现：`app.jsx` 新增 `Wayline` 组件，细线 + 圆点航点线，无编号。Setup/Review/Creating 用 `Draft → Inscription → On chain` 三航点，当前点发光、已过点亮、未来暗；Ready 用 `Broadcast → Seen → Accepted → Mined` 四航点，Mined 待确认。删除 `.steps`/`.step-num` 与 `.chain` 圆片样式。My/Public Identity 改纪念碑中心件：96px 头像带环、mono kicker、32px 大字姓名，居中排列。钱包确认弹层改 `dialog--sign` 居中签署条。`strings.jsx` 加 `wayAria/wayDraft/wayInscribe/wayChain` 双语文案。
- 验证：无头 Chrome CDP `_verify.mjs` 61/61 通过：Setup/Review/Creating 无 `.step-num` 且航点线三节点、Ready 四航点含 pending、纪念碑中心件存在；原 58 项不回归，console/runtime error 0，320px 无横向溢出。`preview-desktop.png` 更新为 Review 航点线页，`preview-mobile.png` 更新为 My Identity 纪念碑页。
- 资产：`_d_meta.json` 保持 `index.html` 状态 `needs-review`。
- 待办：用户复核 A+B 视觉与航点线效果；复核通过前 `design-003` 不标记 `done`。

## 2026-08-14 · design-005 启动与实现

- 用户要求：新增一个原型设计功能点并开始设计。`design-005` 登记为唯一 `in-progress`；`design-003` 改 `blocked`，保留对比候选。
- 输入只限核心认知、PRD v0.1、React Spectrum；必须使用 Baoyu Design 技能；禁止读取、复制、导入或借鉴前四套原型的代码、截图、资产、元数据或设计方向；只能写入 `designs/own-word-prototype-005`。
- 方向五「Signal & Beacon（信号与灯塔）」：无顶栏，底部 Dock 承载品牌、Prototype 面板、语言、主题、钱包状态；Identity 用同心环灯塔件 + 等宽频率读数 BAP ID；链上状态用传输日志行（Broadcast/Seen/Accepted/Mined，Mined 待确认），不用航点线/时间线/步骤编号；钱包请求用请求卡，不用窗口模拟。与前四套视觉层级、布局结构、交互表达均独立。
- 覆盖：Wallet 连接/取消/失败/切换/断开、解析分流（已发布/无身份/资料不全/失败）、Setup 校验（必填名、100/1000 字数、本地图片头像）、Review（含"你的钱包控制这个身份"）、创建处理/取消/失败/成功、My Identity、Public Identity、Edit Profile 保存/取消/未保存离开保护、EN/zh-CN、Light/Dark。Key Rotation 不进入本原型（PRD 已下放 v0.1.1）。
- 术语与不变量遵守核心认知：Wallet 连接不称注册/登录；BAP ID 不可编辑、Copy 返回完整值；用户拒绝为 Cancelled、系统异常为 Failed；Locale/Theme 不影响链上值；状态含文字不只靠颜色。
- 环境备注：unpkg 与 npmmirror 本次均不可达，React 18.3.1/ReactDOM/Babel standalone 使用 Baoyu Design 技能自带 vendor 副本。
- 验证：本地 HTTP `http://127.0.0.1:4311/own-word-prototype-005/index.html` 返回 200；无头 Chrome CDP `_verify.mjs` 46/46 通过（提权宿主环境运行）：HTTP 200、console/runtime error 0、Copy 传完整 70 字符 BAP ID、复制失败值仍可见、语言与主题刷新后持久、1440px BAP ID 首屏可见、320×740 各关键页 `scrollWidth <= 320` 无横向溢出、主操作可用、focus ring 可见。截图：`preview-desktop.png`、`preview-mobile.png`、`shot-12-setup-fresh-1440.png`、`shot-17-my-1440-zh-dark.png`、`shot-24-edit-320.png`。本会话模型不支持读取图片，视觉像素复核以 DOM 几何与计算样式断言替代。
- 资产：`_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 提交：独立 Git 仓库 commit `(PRD v0.1)`；临时探针脚本已从提交中移除。
- 待办：用户并排对比五套方案后反馈选择；复核通过前 `design-005` 不标记 `done`。
