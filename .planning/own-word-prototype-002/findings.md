# 发现与决策：OwnWord 原型 002

## 需求

- UI 以 `designs/own-word-prototype-002` 为准。
- 架构和技术栈参考 `reference/xLog-dev`。
- 完成原型覆盖的 UI、交互逻辑和前端业务逻辑。
- 钱包连接与实际 API 全部先 Mock。
- 先提交计划；用户评审通过后开始实现。

## 研究发现

- 原型目录共约 1022 个文件；大量文件属于 `_ds/react-spectrum-s2` 设计系统素材，不应逐项重写。
- 原型业务源码已列全并完整读取；共 7 个顶层文件。
- `reference/xLog-dev` 共约 448 个文件；依赖、App Router、根 Provider、Theme、i18n、Query、Wallet 组织已核对。
- `_task/system-design` 规定：核心认知优先于 PRD 和代码，禁止读取 `spec/draft`；架构结论需引用 `spec` 或 `reference`。
- `feature_list.json` 当前唯一活动事项为 `design-002`；用户已选定“穹顶与地平线”为最终视觉方向，其他原型封存。
- 原型目标覆盖 PRD v0.1 全部可见流程和关键状态；现有证据记录 React/Babel、HTTP、jsdom 与真实 Chrome 验证。
- `xLog-dev` 基线：Next.js 14.2.3、React 18.3.1、TypeScript 5.4.5、Tailwind CSS 3.4.3、Zustand、TanStack Query、React Hook Form、next-intl、next-themes、Playwright。
- `xLog-dev` 依赖面很大；本项目只应借鉴结构与必要依赖，不复制链上、编辑器、数据库等无关能力。
- 原型业务源码仅 7 个顶层文件：`index.html`、`app.jsx`、`data.jsx`、`icons.jsx`、三个 `screens-*.jsx`；其余为图标与设计系统资产。
- 工作区尚无现成前端应用目录；只有 `backend`、`designs`、`reference`。目标工程位置需在评审方案中明确。
- `xLog-dev` 采用 Next.js App Router，按 `src/app`、`src/components`、`src/hooks`、`src/lib`、`src/models`、`src/queries` 分层。
- 核心认知 489 行，PRD v0.1 347 行；将完整读取后再冻结状态模型与验收范围。
- v0.1 唯一功能闭环：Connect Wallet、Resolve Identity、Setup/Review/Create、My/Public Identity、Edit Profile、BAP ID Copy、Account Switch/Disconnect、Locale、Theme。
- 明确排除：Content、Artifact、Explorer、Relationship、Attestation、Messaging；Key Rotation 已下放 v0.1.1。
- 原型采用单一 `App` 状态机持有全部应用状态，`screens-*` 只接收 props/callbacks；这是可保留的最小 DRY 结构。
- Wallet 状态：`not-connected | connecting | connected | cancelled | failed`；Identity 分流：`none | active | incomplete`；页面：Welcome、Setup、Review、Create Flow、My Identity、Edit Profile、Public Identity。
- 高影响 Mock 操作均有 Wallet 授权：connect、create、save；拒绝映射 Cancelled，处理异常映射 Failed。
- Demo 面板可切换 Identity 三态，单次注入连接/解析/创建/保存的拒绝或失败，并触发 Account Switch/Reset；可作为开发验收工具保留。
- Welcome 的 7 条穹顶线包含 6 条 SVG 弦波弧线加 1 条容器外圈；鼠标扫过触发阻尼波动，`prefers-reduced-motion` 时静态降级。
- 原型未使用 URL 路由；所有页面由内存状态切换。正式实现若目标仅为当前闭环，可保持单页状态机，避免引入无收益路由复杂度。
- Profile 表单：本地 PNG/JPG/WebP，最大 2 MB；Name 必填且最多 100 字符；Bio 最多 1000 字符；Person/Organization 必选。
- 原型 `validate()` 只检查 Name 必填，长度超限只显示错误但未阻止 Review；正式实现必须由同一校验函数同时驱动错误展示和提交门禁。
- Edit 复用同一 ProfileForm；离开脏表单需 Discard 对话框；保存拒绝/失败均保留编辑值。
- My Identity 首屏展示完整 BAP ID，详情可缩略；Copy 必须使用完整值且反馈不引发布局位移。
- Public Identity 包含自动旋转、拖拽、停止/恢复、重置；正反面与四条厚度边；Proof 面板展示完整 BAP ID、完整 TxID、产品化链状态及复制。
- 原型图标以内联 S2 SVG 解决 Dark 模式继承问题。正式工程可用现有 SVG 资产加 CSS mask，避免复制约百行 SVG 字符串和 `dangerouslySetInnerHTML`。
- 原型对 `incomplete` Identity 复用“Create Identity”文案/动作，可能重复表达发布；实现时必须按 SSOT 将已发布 Identity 的补全动作映射为 Profile 更新 Mock。
- 原型视觉全部集中在 `index.html` 内嵌 CSS；正式工程可原样迁移选择器到单个 `globals.css`，再删除 Babel/UMD/设计系统 bundle 运行时。
- 原型只使用少量 S2 组件（Button、StatusLight、Divider）和语义 token；正式实现用原生可访问组件复刻即可，不引入整套 React Spectrum 运行时。
- 主题通过 `<html data-color-scheme="light|dark">` 与语义变量切换；默认 Light，Locale 默认 English；两者持久化到浏览器存储。
- 响应式断点为 960px 与 720px；验收必须覆盖原型基准 1440×900 和 PRD 最窄 320px。
- 动效已有 `prefers-reduced-motion` 降级；正式实现还需让 3D 自动旋转遵守同一偏好。
- `_d_meta.json` 当前仍为 `needs-review`，但用户本次明确指定 002 为实现基准，可作为本任务的视觉范围授权；不修改原型状态。
- `xLog-dev` 在 App Router 根部组合 `NextIntlClientProvider`、`ThemeProvider`、`QueryClientProvider` 和 Wallet Provider；本任务只需保留相同“应用级能力从根注入”的思路。
- Mock 阶段无缓存同步、服务端请求或复杂共享消费者，不需要 TanStack Query、Zustand、next-intl、next-themes；React Context/useReducer 与静态字典足够。
- 原型 CSS 已完整覆盖 Welcome、状态页、表单、Review、My Identity、Public 3D、Toast、Dialog、Demo、响应式；迁移时以选择器级复用为主，不重新设计。
- `reference/xLog-dev` 为 AGPL-3.0；方案只参考目录和技术选择，不复制其业务代码。
- xLog 组件模式值得保留：根 Provider 管横切能力，UI 控件保持原生语义，Clipboard API 失败时提供 `execCommand` fallback。
- xLog 的 Tailwind/Mantine/Headless UI/Framer Motion 组合对本任务过重；原型已有完整 CSS 与原生交互，不继承这些依赖。
- 当前 Node.js 为 v24.14.0，可用内建 `node:test` 验证纯 TypeScript/状态逻辑，避免新增单元测试框架。
- `pnpm -v` 首次探测失败：Corepack 尝试写只读 `/home/haodev/.cache`。实现阶段把 `COREPACK_HOME` 指向工作区或 `/tmp`。
- 原型 002 是独立 Git 仓库；`backend` 与 `reference/xLog-dev` 当前解析到根 Git。根仓库存在与任务无关的 `.agents/skills/baoyu-design` 修改，必须排除在提交之外。
- 根 `.gitignore` 当前只忽略 `backend/*`、`designs/*`、`reference/*`；若按计划新建独立 `frontend` 仓库，需同步增加 `frontend/*`，避免根仓库误跟踪。
- `xLog-dev` 当前没有 `node_modules`，不能复用其安装结果。
- 当前官方 React 主版本为 19，Vite 官方模板支持 React + TypeScript；Node 24 满足 Vite 的 Node 版本门槛。正式应用采用当前稳定 React 19/Vite，并以 lockfile 固定解析版本。
- 不选 Next.js：当前只有一个客户端状态机，无 SSR、SEO 数据页、API Route 或分享 URL；Vite 更小，仍复用 xLog 的 React/TypeScript 与能力边界思路。
- 工作区全部字体只有 xLog 的 SN Pro；`fc-scan` 确认其语言覆盖不含中文，宿主 `fc-list :lang=zh` 为空。
- `@fontsource-variable/noto-sans-sc` 提供自托管、OFL-1.1、零传递依赖的简体中文 variable font；是计划中唯一因现有环境缺口新增的视觉依赖。

## 核心认知

- Wallet、Identity、Profile 是三个独立对象；不得用钱包连接状态代替身份状态。
- v0.1 是“连接 → 解析 → 创建/补全 → 查看/编辑/公开”的单一闭环；外围模块不进入本次实现。
- 高影响动作必须显式展示意图、钱包确认、处理中、业务结果和链上详情。
- Cancelled 与 Failed 语义不同；Account Switch 必须中止旧敏感动作并清空旧身份上下文。
- BAP ID/TxID 是不可翻译、不可截断的数据；显示可缩略，复制必须保留完整原值。
- Locale 默认 English、Theme 默认 Light，并持久化；Wallet/Identity 状态不持久化。
- 核心认知是唯一事实源；同一状态、校验、文案和常量只保留一个权威定义。

## 技术决策

| 决策 | 理由 |
|------|------|
| 仅新增最小运行依赖 | React/Vite/TypeScript 构成工程；Fontsource 解决已证实的中文字体缺口 |
| 不直接基于完整 `xLog-dev` 开发 | 其业务与依赖远超原型范围；应建立最小目标应用并按需复用模式 |
| 保留集中状态机与纯展示屏幕 | 已覆盖全部分流和故障态，文件少，方便 Mock 替换与测试 |
| 原生组件复刻少量 S2 控件 | 保留样式和无障碍，避免搬入无关 bundle 与依赖 |
| 不引入 Query/Store/i18n/Theme 库 | 当前单页 Mock 状态和两套静态文案由 React 原生能力足够承载 |
| 测试使用 Node 内建 runner + 浏览器验收 | 覆盖状态规则与真实交互，不增加测试框架依赖 |
| 使用 Vite SPA，不用 Next.js | 当前无服务端和路由需求；静态产物足够 |
| `frontend` 建独立 Git 仓库 | 符合根仓库只跟踪文档/任务的现有边界 |

## 遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 宿主和工作区无中文字体 | 自托管 Noto Sans SC，并在中文界面实测 |
| 根工作树已有大量无关修改 | 不清理；只精确暂存 `.gitignore` 与新仓库文件 |

## 资源

- `designs/own-word-prototype-002`
- `reference/xLog-dev`
- `_task/system-design/spec`

## 视觉/浏览器发现

- 1440px Light Welcome：顶栏、7 线穹顶、焦点、Hero、三问、三原则、Footer 布局正常；完整页面无横向溢出。
- 当前浏览器缺少可用中文字体，中文副标题及三问中文显示方框；正式实现必须提供能覆盖中英文的字体栈或本地字体并实测。
- 控制台无业务错误；只有 React DevTools 提示和浏览器 Babel 开发告警。正式工程预编译后两项均消失。
- 初始可交互控件均有可访问名称：语言、主题、Wallet、Connect、Demo；区域和标题层级可被 accessibility tree 识别。
- Success path 实测：Connect Wallet → Wallet 授权弹窗 → Approve → Connecting/Resolving → Create Identity Setup。
- 空 Name 点击 Review 留在 Setup 并显示 `Required`；填写 Name/Bio、切换 Organization 后进入 Review，Profile 值正确保留。
- Review 显示 Wallet 控制说明、完整 BAP ID、Copy、Create Identity、Back；关键动作均可由 role/name 定位。
- Create 实测：Review → 授权弹窗（含当前 Identity、完整 BAP ID、影响说明）→ Approve → Creating → Ready → My Identity。
- My Identity 首屏显示 Profile、状态、完整 BAP ID，并提供 Edit、Public、Copy；Organization 选择贯穿创建结果。
- Public 1440px 两栏布局正常；3D 卡自动旋转确实持续更新 transform，支持暂停和重置；Proof 面板完整展示 BAP ID、TxID、链状态及两个 Copy。
- 3D 卡会在任意旋转角度停留，因此截图可能显示边/背面；视觉验收需分别固定正面、背面和斜角取证。
- Edit 实测：Profile 初值完整带入；修改 Name 后点击 Back 弹出 `Discard changes?`，可选 Keep Editing 或 Discard。
- Copy Toast 仅保留 2.6 秒，浏览器命令切换时两次未捕获；实现验收改为同一脚本内断言 Clipboard 写入和即时 `aria-live` 内容。
- Save Profile 实测：Reject 关闭授权后仍停留 Edit 且保留所有编辑值；再次 Save + Approve 后返回 My Identity 并显示更新后 Profile。
- Locale/Theme 实测：切至 `zh`/`dark` 后，`ow.locale`、`ow.theme`、`html.lang`、`data-color-scheme` 同步；重新打开页面仍保持 `zh`/`dark`。
- Dark 主题层级、边框、按钮和状态可读；中文字体方框问题在 My Identity 同样存在，确认是全局字体覆盖而非单页问题。
- 连接取消与连接失败均可稳定复现，但两页顶栏错误显示 `Connected` 并暴露 `Disconnect`。
- 根因已确认：`walletChip` 只显式处理 `not-connected`、`connecting/resolving`，其余状态全部 fallthrough 到 Connected；`cancelled/failed` 写入和状态页渲染均正确。
- 该非穷尽映射从基线 commit `30d556d` 已存在；`6d1058f` 只把入口改为授权弹窗，不是根因。中英文字典已有 cancelled/failed 顶栏文案但从未使用。
- 正式实现必须让 Wallet 状态到顶栏表现穷尽映射，并用表驱动检查覆盖每个状态；取消/失败时不可提供 Disconnect。
- Resolve Fail 实测：Wallet 保持 Connected，页面说明 indexer/network 解析失败，并提供 Try Again 与 Disconnect；选择 complete 后重试直接进入 My Identity。
- Identity 三态分流实测：none → Create your identity；complete → My Identity；incomplete → Complete your profile，预填 Name/Type 并显示不完整提示。
- Account Switch 实测会按新 Demo Identity 重新解析并进入 incomplete Setup；命令切换耗时超过过渡期，未截到旧 Identity 清空的瞬时画面，正式测试应使用应用状态断言。
- Disconnect 从 Setup 返回 Welcome；Wallet 与 Identity 上下文从可见页面移除。
- Clipboard 受控 stub 实测：My Identity 的 Copy 写入值与完整 BAP ID 严格相等，长度 69；不是缩略展示值。
- Save Fail 实测：批准授权后仍留在 Edit，修改后的 Bio 原样保留；错误反馈由 Toast 路径触发。
- 320×800 Welcome 实测 `scrollWidth === innerWidth === 320`，无溢出；穹顶、Hero、三问、三原则均改单列且主操作可用。
- 320×800 Setup 实测无横向溢出；Avatar、Name、Type、Bio、Review/Cancel 全部可用。
- 移动端 `Demo` 浮钮会进入表单内容区；虽未盖住当前控件，正式实现若保留开发控制台，应改为不遮业务内容的底部停靠/抽屉。
- agent-browser 的 full-page capture 会重复/错位截取 sticky 元素；视觉证据应优先用 viewport screenshot，溢出另用 DOM 尺寸断言。
- 320×800 Public Identity 实测无横向溢出；3D 卡缩为 280px，控制、返回按钮、Proof、完整 BAP ID/TxID 与 Copy 均可用。
- 移动端 Public 从两栏改为卡片在上、Proof 在下；长标识正常换行，不截断原值。
- WCAG A/AA 自动审计：桌面 Welcome 0 violation；Public 有 1 个 serious 结构 violation。
- Public violation 根因：`proof-list` 使用 `<dl><div><dt/><dd/><button/></div></dl>`，Button 不是合法定义列表组内容；正式实现把 Copy 放进 `<dd>` 或改用普通分组结构。
- Public ARIA incomplete 根因：`.p3d-controls` 的普通 `<div>` 带 `aria-label` 但无 role；正式实现加 `role="group"`。
- Wallet chip 的 contrast 被 axe 标为 incomplete（审计引擎无法计算该 `color-mix`），需对 Light/Dark 进行计算值或人工对比验证。
- Create Fail 实测：批准授权后进入 `Couldn't create identity`，保留恢复入口 `Try Again` 与 `Back`。
- Avatar 实测：122,772-byte PNG 成功生成 Data URL 预览；`/etc/hosts` 和 2,097,153-byte PNG 均显示 `Could not read that image`；替换失败时保留原头像。
- Avatar MIME 缺陷可稳定复现：文件选择器声明 PNG/JPG/WebP，但 `readLocalImage()` 仅检查 `file.type.startsWith('image/')`，SVG 可绕过并成功预览。
- MIME 根因是 UI `accept` 与底层校验定义重复且不一致。正式实现以单一 `ALLOWED_AVATAR_TYPES` 白名单同时生成 `accept` 和校验，并覆盖 2 MB 边界测试。
- 键盘 Tab 顺序实测为 Brand → Language → Theme → Wallet → Connect → Demo，主操作可达。
- Language、Theme、Connect 使用 2px 蓝色焦点环；Brand、Wallet、Demo 仅浏览器默认 1px。正式实现统一 `:focus-visible`，避免主题/浏览器差异。
- 实现阶段复核：S2 `s2-tokens.css` 单文件 3398 行；当前页面只用少量语义变量和原生控件。正式工程不复制整包，只保留实际使用的 Light/Dark token 与原型选择器。
- 已从 S2 token 源提取原型实际用到的 Light/Dark RGB 值；可保留视觉基准，同时删除 3000 余行未使用变量。
- 阶段 1 浏览器复现：中文正文正常，但 `.hero-kicker`、`.band-title`、Footer 本地化文案稳定显示方框；Light/Dark、1440/320 均受影响。
- 运行时证据：异常元素计算字体为 `SFMono-Regular, Consolas, monospace`；正常中文标题为 `Noto Sans SC Variable`。数据和 Locale 均正确，故障在 mono 字体回退链。
- 单一假设：把已加载的 `Noto Sans SC Variable` 放到 `--s2d-font-mono` 的 generic `monospace` 之前，可修复全部本地化 mono 文案，同时保持 Latin/BAP ID 首选等宽字体。
- 临时浏览器变量验证通过：方框立即变为中文；根因假设成立。源码只修改共享 `--s2d-font-mono` 一处。
- 新 Wallet 实现浏览器验证：原生连接 Dialog 可键盘识别；Reject 后页面与顶栏都显示 `Connection cancelled`，可见按钮中没有 `Disconnect`。原型 fallthrough 缺陷已关闭。
- 阶段 2 真浏览器闭环：Connect Approve/Reject/Failed、Resolve Failed/Retry、三态分流、Account Switch、Disconnect 均按状态机工作。
- 320×800 `Create your identity` 页实测 `innerWidth = documentElement.scrollWidth = body.scrollWidth = 320`；移动端无横向溢出。
- 阶段 2 新会话 WCAG A/AA 为 0 violation；Wallet chip 仍因 `color-mix` 被 axe 标为 1 个 incomplete，沿用阶段 1 人工对比度证据（Light 7.59、Dark 7.85）。
- 阶段 2 新会话无 console/page error；全部请求均指向 `127.0.0.1:4312`，外部 Wallet/API/CDN 请求为 0。
- 阶段 3 统一校验实测：空 Name 无法进入 Review；SVG 被单一 MIME 白名单拒绝，合法 PNG 成功后错误消失且显示预览。
- Review Copy 经 Clipboard stub 取证：写入值与页面 69 字符完整 BAP ID 严格相等。
- Create 与 Complete Profile 的 Reject/Failed/Retry/Done 均通过；失败和取消后 Name、Bio、Avatar 原值不丢失。
- `incomplete` 分支页面中 `Create Identity` 数量为 0、`Complete Profile` 数量为 1；授权文案为 Profile update，未复用 Identity create。
- 发布处理中切换账户后，旧异步结果未显示 Ready；重新解析仍进入 `Complete your profile`，操作序号同时保护 reducer 与 App 副作用。
- 视觉取证发现 SPA 从长表单进入 Review 会保留滚动位置；统一在 `flow.screen` 变化时回顶，Setup/Review 实测 `scrollY=0`。
- 移动端 `sticky` Demo 仍压住 Review 内容，坐标为 viewport 底部；改为文档流后 `demoTop=1379 > viewport=800`，不再遮挡。
- 阶段 3 Setup/Review 在 320×800、中文、Dark 下宽度均严格为 320px；axe WCAG A/AA 0 violation，仅 Wallet `color-mix` 保留已人工通过的 incomplete。
- My Identity 实测完整 BAP ID 为 69 字符，Clipboard 写入值与原值严格相等；Details 展示为 `1bap…a7b8c9d0`，展示缩略不污染事实值。
- Edit 无改动 Back 不弹窗；有改动时 Keep 保值、Discard 恢复已发布 Profile；合成 `beforeunload` 事件被阻止，刷新离开保护生效。
- Save 直接 Reject、Mock Reject、Failed 的 Draft 均保留；Failed 处理中按钮为 `Saving…` 且 disabled；成功 Toast 后 My 标题更新为 `Saved Name`。
- 2.6 秒 Toast 短于 agent-browser 命令往返，跨命令 Wait 会错过；同一 `eval` 中批准、等待 1.3 秒并读取 DOM 可稳定取证。
- 阶段 4 My/Edit 在 320×800 中文 Dark 下宽度严格为 320px，Demo 入口 `top=1258 > viewport=800`，axe WCAG A/AA 0 violation。
- 移动端长名称在横向头像摘要中被挤压；只在 `max-width:720px` 把 `.my-left` 改为纵向，桌面原型布局不变。
- Public 3D 自动旋转 350ms 内 Y 角从 214.19 变为 217.55；暂停后 283.49 保持不变；方向键从 283.49 变为 292.49。
- 真实 Pointer 拖拽把角度从 `x=-8,y=16` 改为 `x=9.5,y=52`，松开后 `dragging=false`；Reset 恢复 `-8,16`。
- Reduced Motion 模拟下角度 350ms 保持 52、`auto=false`、自动按钮 disabled；用户主动控制仍保留。
- Public Clipboard 依次写入完整 BAP ID（69）与原型 TxID（103）；Proof 分组的直接子元素全部为合法 `DT/DD`，axe 结构 violation 关闭。
- Public 320×800 中文 Dark 下宽度严格为 320px，完整值正常换行，Demo 入口位于 `top=1602 > viewport=800`。
- 3D 焦点中文“立”显示方框：计算字体为 Songti/Noto Serif/SimSun/serif，宿主均无字形；共享 serif 回退加入已加载 `Noto Sans SC Variable` 后截图确认修复。
- Demo 故障按钮现提供 armed Toast；移动端实测“解析失败 · 已设置，将在下一次对应操作生效”，Reset 回到未连接。
- Production dogfood 完整主链路、草稿保护、保存、公开身份和一次性连接失败恢复均通过。
- Welcome 两组卡片沿用原型 H3，造成 H1 后标题跳级；根因在共享语义标签，统一改为 H2 后 axe violations 为 0。
- 未声明 favicon 导致浏览器兜底请求 `/favicon.ico` 返回 404；使用内联 data favicon 后请求列表为空，未增加静态文件。
- 最终 production 无 console/page error；运行时资源仅来自本地 origin，无真实 Wallet/API/CDN 请求。
- 最终保留的限制均为本次明确范围：Wallet/API/链上广播为 Mock，Wallet/Identity 会话不跨刷新，Public 无分享 URL。
