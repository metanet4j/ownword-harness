# 进度日志：OwnWord 原型 002

## 会话：2026-08-20

### 阶段 1：需求与现状盘点

- **状态：** completed
- 已读取工作区规则和所需技能。
- 已建立隔离规划目录与执行门禁。
- 已完成首轮目录规模与事实源规则盘点。
- 已确认 design-002 是最终视觉方向及 PRD v0.1 范围。
- 已确认 xLog 技术基线及其大依赖面。
- 已定位原型 7 个顶层业务文件；工作区不存在目标前端工程。
- 已完整读取核心认知、PRD、设计事项与交接记录。
- 已读取应用状态机和 Wallet/Resolve/Welcome 屏幕。
- 已读取 Setup/Review/Create/My/Edit/Public 屏幕与中英文文案。
- 发现原型长度校验门禁缺口及 incomplete 分支语义风险，已记录为实现修正项。
- 已读取样式体系、主题、响应式、3D 卡、设计元数据和图标实现。
- 已补齐样式结构并定位 xLog 根 Provider、App Router、Theme、i18n、Query 与 Wallet 组织方式。
- 已确认 Node 版本、仓库边界和现有脏工作树；后续提交必须按新目录精确暂存。
- 已启动宿主静态预览与隔离浏览器，完成 1440px Welcome 视觉、控制台和可访问结构检查。
- 已实测连接授权、身份解析、必填校验、Profile 输入、类型切换和 Review。
- 已实测创建授权、处理中/成功、My Identity、Public Identity、3D 自动旋转/暂停及 Proof。
- 已实测 Edit 初值与未保存离开保护；Copy 按新取证方式待验证。
- 已实测 Profile 保存拒绝保值、批准成功，以及 Locale/Theme 切换和刷新持久化。
- 已实测 Connect Cancelled/Failed，并按系统化调试完成稳定复现、代码数据流、提交历史和根因确认。
- 已实测 Resolve Failed/Retry、Identity 三态分流、Account Switch 与 Disconnect。
- 已用 Clipboard stub 验证复制完整 BAP ID；已验证 Save Failed 后留页保值。
- 已验证 320px Welcome/Setup 无横向溢出并记录 Demo 浮钮遮挡风险。
- 已验证 320px Public 与完整长标识无横向溢出。
- 已验证 Create Failed；完成 Welcome/Public WCAG A/AA 审计并定位语义根因。
- 已验证 Avatar 成功、非图片、超限与替换保值；定位 SVG 绕过根因。
- 已验证键盘 Tab 顺序和焦点样式；定位 Wallet/Demo 默认焦点环差异。
- 已确认工作区和宿主均无中文字体；SN Pro 不含中文覆盖。
- 已确认 Vite/React 当前官方能力与 Node 24 兼容门槛，冻结最小技术方案。
- 已完成范围、架构、Mock 边界、状态规则、提交切分和验收门禁。

### 阶段 2：方案与评审

- **状态：** completed
- 计划评审稿已完成。
- 胡先生已回复“计划通过”。

### 阶段 3：工程与视觉基座

- **状态：** completed
- 已复读根规则、核心认知、规划文件和所需技能。
- 已创建空的独立 `frontend` Git 仓库。
- 已确认不复制 3398 行 S2 token 包；改用最小语义 token。
- 已迁移原型 657 行页面样式，并用原始 RGB 值补齐最小 Light/Dark token。
- 已复核 Welcome、Dome、Topbar、Footer 的准确组件结构。
- 阶段 1 浏览器发现中文 mono 文案方框；已稳定复现并定位到共享字体回退链，提交暂停。
- 已用运行时单变量实验确认根因，并在共享 mono 字体栈一处修正。
- 提交前 TypeScript、Node test、production build 再次通过。
- 1440/320、Light/Dark、English/中文、刷新持久化通过；WCAG A/AA 为 0 violation。
- Wallet Chip 人工对比度：Light 7.59，Dark 7.85，满足 AA。
- 已提交 `f3498a2 feat(frontend): 建立原型视觉基座与偏好设置 (PRD v0.1)`。

### 阶段 4：Wallet 与 Resolve

- **状态：** completed
- 已建立 reducer、Wallet/Identity Mock 契约、原生 Dialog、Wallet/Resolve 视图和 Demo 故障入口。
- 顶栏 Wallet 展示改为穷尽映射；Cancelled/Failed 不再落入 Connected。
- 浏览器已验证授权 Reject；Cancelled 顶栏准确且不暴露 Disconnect。
- 浏览器已验证连接失败、解析失败/重试、`none / complete / incomplete` 三态、Account Switch 与 Disconnect。
- 新会话复核 320×800 Setup：页面宽度严格为 320px，无横向溢出；WCAG A/AA 0 violation。
- 新会话 Console 与 page errors 均为 0；Network 仅 `127.0.0.1` 工程资源，无真实钱包、API 或 CDN 请求。
- TypeScript、4 个状态规则测试、production build 均通过。
- 已提交 `9a0bdea feat(frontend): 实现钱包与身份解析 Mock 流程 (PRD v0.1)`。

### 阶段 5：Setup、Review 与 Create

- **状态：** completed
- 已迁移 Profile 表单、Avatar、Review、授权 Dialog 与发布状态页。
- Profile 校验单一来源覆盖 Name 必填/100、Bio 1000；Avatar `accept` 与 PNG/JPEG/WebP、2 MiB 底层白名单同源。
- 浏览器已验证空 Name 阻断、SVG 拒绝、PNG 成功且错误清除、Review 与完整 BAP ID Copy。
- 新身份已验证授权 Reject、发布 Failed/Retry、Ready、进入 My；取消/失败均保留 Name、Bio、Avatar。
- `incomplete` 已验证只显示 Complete Profile，不显示 Create Identity；授权、取消保值、失败重试和成功均通过。
- 发布中 Account Switch 已验证旧结果失效，重新 Resolve 后仍进入 Profile 补全。
- 320×800 中英/深色 Setup 与 Review 无横向溢出，完整 69 字符 BAP ID 正常换行；WCAG A/AA 0 violation。
- 视觉复核修复 SPA 切屏未回顶、移动端 Demo 入口遮挡内容；复核 `scrollY=0`，Demo 首屏外位于文档末端。
- TypeScript、7 个规则用例、production build 均通过。
- 已提交 `5a2280a feat(frontend): 实现身份设置与创建流程 (PRD v0.1)`。

### 阶段 6：My Identity 与 Edit

- **状态：** completed
- 已实现 My Identity 全 Profile、完整 BAP ID、缩略详情、Copy、状态与协议信息。
- Clipboard stub 证明 Copy 写入值严格等于页面完整 69 字符 BAP ID；详情只缩略展示。
- Edit 初值、Profile Form 复用、无改动直接返回、脏表单 Keep/Discard 与 `beforeunload` 保护均通过。
- 保存授权直接 Reject、Mock Reject、Failed 均留在 Edit 并保值；Processing 显示 Saving 且按钮禁用；成功返回 My 并更新名称。
- 320×800 中英/深色 My 与 Edit 均无横向溢出；完整 ID 正常换行；WCAG A/AA 0 violation。
- 视觉复核将移动端长名称身份摘要改为纵向堆叠，避免头像横向挤压。
- TypeScript、8 个规则用例、production build 均通过。
- 已提交 `b9ebab7 feat(frontend): 实现身份详情与资料编辑流程 (PRD v0.1)`。

### 阶段 7：Public Identity、3D 与 Demo

- **状态：** completed
- 已实现 My → Public → My、3D 正反面/厚度、Proof、完整 BAP ID/TxID 与 Copy。
- 3D 实测：自动旋转角度变化；暂停后稳定；方向键 +9°；真实 Pointer 拖拽 `(-8,16)→(9.5,52)`；重置为 `(-8,16)`。
- Reduced Motion 下 `auto=false`、角度 350ms 不变、自动按钮 disabled，并保留用户主动拖拽/方向键。
- Clipboard stub 依次收到完整 69 字符 BAP ID 和完整 103 字符原型 TxID；Proof `<dl>` 仅含合法 `dt/dd` 分组。
- 1440×900 与 320×800 Public 均无横向溢出；移动端中文/Dark、69/103 字符换行、WCAG A/AA 0 violation。
- 视觉复核发现 3D 中文首字因 serif 字体栈缺字显示方框；共享 serif 回退补入已加载 Noto Sans SC 后通过。
- Demo 移动端文档流入口、抽屉、故障 armed Toast、Reset 均通过。
- TypeScript、9 个规则用例、production build 均通过。
- 已提交 `56663e7 feat(frontend): 实现公开身份卡与故障演示 (PRD v0.1)`。

### 阶段 8：集成验收与收口

- **状态：** completed
- Production 主链路已通过：Connect → Setup → Review → Create → My → Edit → Public。
- 已验证必填校验、创建/保存授权、未保存草稿保护、一次性连接失败与 Retry 恢复。
- 中文、Dark、390×844 Public 与移动端 Demo drawer 通过；无内容遮挡。
- Dogfood 发现 Welcome H1→H3 跳级和 `/favicon.ico` 404；按系统化调试修复并提交 `533bccd`。
- 全新 production 会话复验：Welcome 标题均为 H2、axe violations 0、favicon 请求 `[]`、console/page errors 0。
- Network 资源仅来自 `127.0.0.1:4313`，真实钱包、API、CDN 请求均为 0。
- 宿主最终检查：TypeScript 0 error、Node test 9/9、Vite production build 成功。
- 根 `.gitignore` 使用 `frontend/` 隔离独立仓库；根状态不再显示 `frontend/`。
- Dogfood 报告：`frontend/artifacts/dogfood/report.md`。

### 阶段 9：xLog 最新技术栈迁移

- **状态：** completed
- 胡先生要求用 xLog 技术栈基线替换 Vite，并使用最新稳定版本。
- 已复读核心认知；领域边界、状态和 Mock 范围不变。
- 已确认本地 xLog 核心基线：Next.js App Router、React、TypeScript、Tailwind CSS、pnpm。
- 已确认现有前端工作树干净，可进行结构迁移。
- 已完整读取 xLog 根布局、Provider、Next、Tailwind、PostCSS 与 TypeScript 配置。
- 已定位迁移风险：`App` 初始化直接读取 `localStorage`，需放入纯客户端渲染边界。
- 已通过官方 npm registry 核验最新版本与兼容约束；宿主 Node 24.14.0 满足 Next.js 16 和 pnpm 11。
- 已替换 Vite 入口与配置，新增 Next.js App Router 根布局、客户端页面和 Tailwind v4 PostCSS 管线。
- 已保留全部领域、Mock、消息、屏幕组件与视觉 CSS；迁移差异检查无空白错误。
- pnpm 11.22.0 已安装 49 个包并生成 `pnpm-lock.yaml`；直接依赖版本与官方 `latest` 一致。
- 宿主 TypeScript strict 检查通过；领域测试 9/9 通过。
- Next.js 16.3.1 Turbopack production build 成功；`/` 与 `/_not-found` 均静态生成。
- Next 自动生成 `next-env.d.ts` 并将 JSX runtime 调整为 `react-jsx`；已接受框架必需配置。
- 标准 Next production 服务在 4313 启动，无 standalone 警告。
- 隔离浏览器已打开 production 首页；标题、H1/H2 层级、Locale、Theme、Wallet 与 Demo 控件均可访问。
- production 首页视觉与原型一致；Mock Wallet Connect 正常打开可访问授权 Dialog，Reject/Approve 均可操作。
- Approve 后完成 Mock Resolve 并进入 `Create your identity`；Wallet、Profile 表单、Person/Organization、Review/Cancel 控件完整。
- Next 客户端边界下受控 Profile 输入正常保值，无 Hydration 重置。
- Review 页正常展示 Profile、完整标识复制入口、Create Identity 与 Back。
- 胡先生新增门禁：UI 必须实际迁移到 Tailwind CSS，不能只接入管线。
- 已停止迁移前 production 服务和浏览器回归；样式迁移后重新执行全部门禁。
- 已建立 Tailwind v4 `@theme inline` 语义颜色、圆角、字体与断点；Base、导航、按钮、状态、Panel、表单、Avatar 已改用 Tailwind `@apply`。
- Tailwind 迁移扩展到 Dialog、Demo、Welcome、状态页、Review、My Identity、Public、Proof 和 960/720px 响应式规则；最终 247 个 `@apply`，CSS 从 738 行降至 689 行。
- Tailwind 修正后 Next.js production build 成功；新增技术栈结构测试，领域与结构测试 10/10 通过。
- Tailwind production 服务启动成功；隔离浏览器加载首页，已获取迁移后视觉截图。
- Tailwind 首页与迁移前截图视觉一致；Connect Wallet 与 Approve 交互正常。
- Tailwind Setup 页面按预期渲染，已获取表单视觉截图。
- Tailwind 表单输入与 Review 页面切换通过；受控状态未受样式迁移影响。
- Mock Create 授权与完成通过；实际标题为 `Your identity is ready`，可进入 My Identity。
- Tailwind My Identity 正常展示名称、Edit、Public、BAP ID Copy、Bio 与 Details。
- Tailwind Public Identity 页面进入成功；已获取 3D Card 与 Proof 视觉截图。
- 桌面 Public 视觉正常，3D 自动旋转与 Proof 双栏保留；已切换 320×800 与中文继续回归。
- 320×800 中文 Public 可访问结构完整；深色主题切换成功，已获取移动端截图。
- 移动端 `innerWidth = documentElement.scrollWidth = body.scrollWidth = 320`，无横向溢出；`lang=zh-CN`、`theme=dark`、`ow.locale=zh` 同步。
- production page errors 与 Console 均为空。
- Network 全部为 `127.0.0.1:4313` 的 Next chunks 与本地字体；真实 Wallet/API/CDN 请求为 0。
- WCAG A/AA 自动审计 0 violation；Wallet chip 因 `color-mix` 留 1 个需人工复核项，与原验收类型一致。
- Dark Wallet chip 计算色为 `rgb(175,175,175)` / `rgb(27,27,27)`，对比度约 7.85:1，满足 AA；已切回 Light 继续复核。
- Light Wallet chip 计算色为 `rgb(80,80,80)` / `rgb(248,248,248)`，对比度约 7.59:1，满足 AA；已刷新页面验证偏好持久化。
- 刷新后 `lang=zh-CN`、`theme=light`、`ow.locale=zh` 保留；Wallet 按设计回到未连接，Page errors 为空。
- 刷新后 Console 仍为空；隔离浏览器与 production 服务已关闭。
- `pnpm list --depth 0` 确认 11 个直接依赖版本与 package 一致；`pnpm outdated` 为空，全部已用技术栈为 registry 最新版。
- 最终前端差异无空白错误；Vite 入口、配置与 npm lockfile 已删除，Next App Router、pnpm lockfile、Tailwind 结构测试已纳入。
- 已提交 `a0b893a refactor(frontend): 迁移至 xLog 最新技术栈 (PRD v0.1)`。

### 阶段 10：Tailwind utilities 组件内迁移

- **状态：** in_progress
- 胡先生确认开始把集中 CSS/`@apply` 迁入 JSX Tailwind utilities。
- 已复读工作区规则、核心认知、规划记录及所需技能。
- 冻结边界：不改视觉、业务状态、Mock 和无障碍语义；CSS 仅保留 Tailwind 基础设施。
- 已完整复核 489 行核心认知与现有迁移记录；本阶段不改领域不变量。
- 已读取 App、共享 UI、Wallet 与 Identity 全部样式消费者；确认迁移只触及 5 个 TSX、`styles.css` 和结构测试。
- 已把共享组件、App Shell、Wallet、Identity、Public/3D 与 960/720px 响应式样式迁入 TSX Tailwind utilities。
- `styles.css` 从 689 行降至 156 行；`@apply` 和组件 class selector 均为 0，只保留 Tailwind 主题、Token、Keyframes 与 Reduced Motion。
- 结构测试已改为禁止 `@apply`/组件选择器，并检查共享 utilities 与 3D Tailwind arbitrary utilities。
- 宿主 TypeScript 0 错误、Node tests 10/10、Next.js 16 production build 成功。
- 已加载当前 agent-browser core/dogfood 工作流；回归使用独立命名会话、production 服务、快照/截图与 Console/Network/axe 取证。
- Next production 服务已在 `127.0.0.1:4313` 启动；隔离会话 `ownword-tailwind-utilities` 加载成功。
- 1440×900 Welcome 视觉、标题层级与全部首屏交互控件正常；Console/Page errors 为空，截图为 `/tmp/ownword-tailwind-utilities/welcome.png`。
- Wallet 授权 Approve、Resolve 与 Setup 进入成功；表单控件和视觉层级正常，截图为 `/tmp/ownword-tailwind-utilities/setup.png`。
- Setup 首张截图疑似顶栏裁切；运行时证据为 `scrollY=0`、Header/Inner `top=0`、高度 `62.25/61.25px`、Sticky 生效，已在稳定帧复截图继续判断。
- 稳定帧截图 `/tmp/ownword-tailwind-utilities/setup-top.png` 顶栏完整；首张为切屏滚动动画中的截图时序，不是布局回归。
- Name/Bio 受控输入、Setup→Review、Profile 预览与操作控件通过；截图为 `/tmp/ownword-tailwind-utilities/review.png`。
- Review 视觉、双栏布局、完整 BAP ID 换行与链流程面板正常。
- Create 授权 Dialog、Approve、Processing 与 `Your identity is ready` 成功状态通过。
- My Identity 的 Profile、状态、完整 BAP ID、Bio、Details 与操作按钮正常；截图为 `/tmp/ownword-tailwind-utilities/my-identity.png`。
- Public 页已进入；3D 自动旋转仍在更新角度，Proof 和完整 BAP ID/TxID 展示正常。
- Public 运行时边界：`scrollY=0`、视口 `1440×900`、Header/Inner `top=0`、文档高 `1025px`；已采集稳定截图 `/tmp/ownword-tailwind-utilities/public-stable.png`。
- Public 稳定截图确认顶栏、双栏、3D Card、Proof 与 Demo 入口视觉正常。
- 3D Pause 后 350ms 角度保持 `71.68` 且 `auto=false`；ArrowRight 后 Y 角增加 9° 至 `80.68`；Reset 可用。
- 320×800 中文/Dark Public：`innerWidth=documentElement.scrollWidth=body.scrollWidth=320`，`lang=zh-CN`、`theme=dark`，无横向溢出；截图为 `/tmp/ownword-tailwind-utilities/public-mobile-dark.png`。
- 移动 Dark 截图发现 Secondary Button 边框疑似缺失；计算样式确认背景/文字正确，但边框为透明。
- 根因：共享 Button Base 含 `border-transparent`，Tailwind 生成顺序不按 `className` 片段顺序覆盖，Secondary 的 `border-line` 未生效；修复必须落在共享 Tone 定义。
- 已以结构测试复现：共享 Base 禁止携带 `border-transparent`，首次运行 9/10 通过并准确失败。
- 共享 Base 仅保留边框宽度，每个 Tone 独立声明边框色；测试恢复 10/10 通过。
- 最终宿主验证：TypeScript 0 错误、Node tests 10/10、Next.js 16.3.1 production build 成功，静态路由 `/` 与 `/_not-found` 生成成功。
- 最终 production 新构建已启动；Welcome 可访问性快照标题层级与全部首屏交互控件正常。
- 最终 production 的 Connect Wallet 可打开可访问 Dialog；Reject/Approve 控件完整。
- Approve 后进入 Setup；Profile 表单、Person/Organization、Review/Cancel 与 Disconnect 控件完整。
- Secondary Button 在 Light production 的计算样式为 `1px rgb(225,225,225)`；边框不再透明。已切换 Dark 继续复验。
- Secondary Button 在 Dark production 的计算样式为 `1px rgb(50,50,50)`；根因修复生效。视口已切到 320×800。
- 320×800 Dark Setup 最终截图：`/tmp/ownword-tailwind-utilities/setup-mobile-dark-final.png`；`innerWidth=rootWidth=bodyWidth=320`，无横向溢出，`lang=en`、`color-scheme=dark`。
- 最终 production Page errors 与 Console 均为空。
- 最终网络请求均为 `127.0.0.1:4313` 的 Document/静态资源/字体，0 外部 API 请求。
- 当前 CLI 正确命令为 `a11y`；WCAG A/AA axe 结果 0 violation、24 pass，1 个颜色对比项需人工确认（`.py-[7px]`）。
- axe 未判定元素为 Connected Wallet Button；Dark 计算色为前景 `rgb(175,175,175)`、背景 `rgb(27,27,27)`、opacity 1，继续计算实际对比度。
- 人工计算 Connected Wallet Button 对比度为 `7.85:1`（AA 普通文字门槛 `4.5:1`）；最终移动截图视觉检查无异常。因此最终为 0 WCAG violation，未判定项人工通过。
- 最终浏览器会话与 production 服务均已停止，进入提交前静态审计。
- 已确认 4313 无监听；frontend `git diff --check` 通过，变更仅 8 个预期文件，共 403 insertions / 851 deletions；`styles.css` 156 行且 0 `@apply`。
- 点号选择器审计无输出：`styles.css` 0 组件 class selector；阶段 10 实现与验收完成，待提交。
- Frontend 已提交：`4bce3de refactor(frontend): 完成 Tailwind utilities 迁移`。

## 创建或修改的文件

- `.planning/.active_plan`
- `.planning/own-word-prototype-002/task_plan.md`
- `.planning/own-word-prototype-002/findings.md`
- `.planning/own-word-prototype-002/progress.md`

## 测试结果

| 测试 | 结果 | 状态 |
|------|------|------|
| 原型桌面/移动浏览器勘察 | 主路径、错误态、响应式、键盘、WCAG 已取证 | passed |
| 阶段 1 TypeScript / Node test / Vite build | 0 错误、1/1 测试、构建成功 | passed |
| 阶段 1 浏览器验收 | 1440/320、双语、双主题、持久化、0 WCAG violation | passed |
| 阶段 2 TypeScript / Node test / Vite build | 0 错误、4 个测试、构建成功 | passed |
| 阶段 2 浏览器验收 | Wallet/Resolve 全分支、三态分流、320px、0 WCAG violation | passed |
| 阶段 3 TypeScript / Node test / Vite build | 0 错误、7 个规则用例、构建成功 | passed |
| 阶段 3 浏览器验收 | 创建/补全全分支、Avatar、Copy、竞态、320px、0 WCAG violation | passed |
| 阶段 4 TypeScript / Node test / Vite build | 0 错误、8 个规则用例、构建成功 | passed |
| 阶段 4 浏览器验收 | My/Copy/Edit/脏保护/保存全状态、320px、0 WCAG violation | passed |
| 阶段 5 TypeScript / Node test / Vite build | 0 错误、9 个规则用例、构建成功 | passed |
| 阶段 5 浏览器验收 | Public/3D/Proof/Copy/Reduced Motion/320px、0 WCAG violation | passed |
| 最终宿主 TypeScript / Node test / Vite build | 0 错误、9/9 测试、24 modules 构建成功 | passed |
| Production dogfood | 主链路/故障恢复/390px/双语/主题通过；2 个问题已修复复验 | passed |
| 最终 Console / Network / axe | 0 error；0 外部请求；0 violation | passed |
| xLog/Tailwind 最终自动验收 | TypeScript 0 错误、10/10 tests、Next.js 16 production build 成功 | passed |
| xLog/Tailwind production 浏览器 | 主流程、320px、中英/主题、0 Console/Page error、0 外部请求、0 WCAG violation | passed |
| 依赖最新性 | 11 个直接依赖精确锁定；`pnpm outdated` 无输出 | passed |

## 错误日志

| 日期 | 错误 | 尝试次数 | 解决方案 |
|------|------|---------:|---------|
| 2026-08-20 | 暂无 | 0 | — |
| 2026-08-20 | `pnpm -v` 无法写只读 Corepack cache | 1 | 改用工作区或 `/tmp` 下的 `COREPACK_HOME` |
| 2026-08-20 | 本地 curl 误走代理到 7771 | 1 | 使用 `curl --noproxy '*'` |
| 2026-08-20 | 沙箱禁止本地监听与浏览器 socket | 2 | 按规则使用宿主环境运行本地预览和浏览器 |
| 2026-08-20 | 等待 2.6 秒 Copy Toast 两次超时 | 2 | 改为点击后立即读取 DOM/Clipboard |
| 2026-08-20 | 首次读取 Writing Skill 使用了不存在的工作区路径 | 1 | 改读 `/home/haodev/.agents/skills/writing-clearly-and-concisely/SKILL.md` |
| 2026-08-20 | 沙箱内 `npm install` 60 秒无输出 | 1 | 中止后改用宿主网络，不重复沙箱安装 |
| 2026-08-20 | `git diff --cached --check` 检出 10 个文件末尾空白行 | 1 | 机械移除多余尾部空行并重新暂存 |
| 2026-08-20 | 当前 agent-browser 不接受顶层 `viewport` 命令 | 1 | 查 CLI 帮助，改用 `set viewport 320 800` |
| 2026-08-20 | 阶段 2 三个新文件末尾多空行 | 1 | 机械规范为单个 EOF 换行，cached check 通过 |
| 2026-08-20 | 移动端 Demo 首次改用 `sticky` 后仍遮挡内容 | 1 | 截图与元素坐标证伪；改为文档流静态入口，复核首屏外 |
| 2026-08-20 | 等待 2.6 秒 Save Reject Toast 超时 | 1 | 页面状态证明业务完成；改为单一浏览器脚本在 1.3 秒时读取 Toast |
| 2026-08-20 | Production Welcome 标题层级跳级 | 1 | 两组共享卡片标题由 H3 改为 H2；新会话 axe 0 violation |
| 2026-08-20 | Production 默认 favicon 请求 404 | 1 | `index.html` 声明内联 favicon；新会话筛选请求为空 |
| 2026-08-20 | 首次迁移规划补丁匹配了不存在的日志行 | 1 | 读取实际文件尾部后按稳定锚点更新；未改动代码 |
| 2026-08-20 | Next SWC 包下载中断 `error (23)` | 1 | pnpm 自动重试后完整下载，安装成功 |
| 2026-08-20 | 沙箱运行 pnpm 无权打开宿主 store SQLite | 1 | 后续 pnpm 检查按规则在宿主环境运行 |
| 2026-08-20 | `pnpm start -- --port` 将 `--port` 识别为目录 | 1 | 使用 pnpm 参数格式 `pnpm start --port 4313` |
| 2026-08-20 | `next start` 警告与 `output: standalone` 不兼容 | 1 | 当前无独立服务器需求，移除 standalone 配置 |
| 2026-08-20 | Tailwind 初版只接入构建管线，未迁移 UI 样式 | 1 | 按用户门禁重开阶段，将常规样式改为 Tailwind |
| 2026-08-20 | Tailwind 无法应用 `font-inherit` | 1 | 根因是 utility 不存在；按钮字体继承保留标准 CSS 声明 |
| 2026-08-20 | 浏览器等待错误文案 `Identity ready` 超时 | 1 | 快照证明业务已成功；正确标题为 `Your identity is ready` |
| 2026-08-20 | `rg` 把以 `--` 开头的 CSS 变量正则识别为参数 | 1 | 根因为缺少 option terminator；改用 `rg -- "--pattern"` |
| 2026-08-20 | `apply_patch` 拒绝同一补丁删除并新增 `styles.css` | 1 | 编辑器禁止同路径多操作；拆为受 Git 保护的 Delete/Add 两次补丁 |
| 2026-08-20 | 浏览器等待 `Public Identity` 超时 | 1 | 快照证明已进入 Public；实际标题为 `Identity — Public View`，改以角色与页面快照验收 |
| 2026-08-20 | Tailwind Secondary Button 边框计算为透明 | 1 | 已定位共享 Base/Tone `border-color` 冲突；先加结构回归测试，再从 Base 移除颜色 |
| 2026-08-20 | Button 回归测试首次 Green 断言仍假定 Primary 以 `bg-accent` 开头 | 1 | 放宽为同一 Tone 字符串包含 `bg-accent`，保留真正约束：Base 不得声明透明边框 |
| 2026-08-20 | 当前 agent-browser 不提供 `audit --level aa` 命令 | 1 | 查询当前 CLI/skill 能力，改用其支持的可访问性检查方式 |
| 2026-08-20 | `querySelector('.py-[7px]')` 未正确转义 arbitrary class | 1 | 改用 `classList.contains('py-[7px]')` 精确定位元素 |
| 2026-08-20 | `rg` 默认正则引擎不支持组件选择器审计中的 negative lookahead | 1 | 改为列出全部点号选择器后人工确认仅保留主题基础设施选择器 |
| 2026-08-20 | 记录补丁再次对 `progress.md` 声明两个 Update | 1 | 合并为单个 Update File 下的多个 hunk |

## 五问重启检查

| 问题 | 答案 |
|------|------|
| 我在哪里？ | 阶段 10：已完成，frontend 已提交 |
| 我要去哪里？ | 提交规划证据 |
| 目标是什么？ | 原型 002 的完整前端 UI、交互和 Mock 业务状态 |
| 我学到了什么？ | 范围、状态模型、Mock 边界和 8 个原型缺陷；见 `findings.md` |
| 我做了什么？ | 已完成 JSX utilities 迁移，并修复共享按钮边框冲突 |
