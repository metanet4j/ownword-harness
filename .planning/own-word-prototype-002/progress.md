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

## 五问重启检查

| 问题 | 答案 |
|------|------|
| 我在哪里？ | 全部阶段已完成 |
| 我要去哪里？ | 已交付 Mock 前端闭环与验收证据 |
| 目标是什么？ | 原型 002 的完整前端 UI、交互和 Mock 业务状态 |
| 我学到了什么？ | 范围、状态模型、Mock 边界和 8 个原型缺陷；见 `findings.md` |
| 我做了什么？ | 五个功能提交与一个 dogfood 修复提交完成；最终宿主和 production 验收通过 |
