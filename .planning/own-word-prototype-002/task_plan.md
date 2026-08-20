# 任务计划：OwnWord 原型 002 功能实现

## 结论

- **状态：** completed。原型功能、xLog 最新技术基线与 Tailwind CSS 迁移均已完成。
- **门禁：** 胡先生已于 2026-08-20 回复“计划通过”。
- **目标：** 完整实现 `designs/own-word-prototype-002` 的 UI、交互、前端业务状态；钱包与外部 API 全部 Mock。

## 决策冻结

| 项目 | 方案 | 原因 |
|---|---|---|
| 事实源 | `_task/system-design/spec/核心认知.md` > PRD > 原型 | 遵守 SSOT 与 DRY |
| 视觉源 | `designs/own-word-prototype-002` | 用户指定；迁移，不重设计 |
| 目标目录 | `/home/haodev/ownword/frontend` | 工作区尚无前端工程 |
| Git | `frontend` 独立仓库；根 `.gitignore` 增加 `frontend/*` | 根仓库只跟踪文档/任务；功能提交隔离 |
| 技术栈 | xLog 基线：Next.js App Router、React、TypeScript、Tailwind CSS、pnpm；使用最新稳定版 | 胡先生于 2026-08-20 明确要求迁移并升级全部技术栈 |
| 中文字体 | `@fontsource-variable/noto-sans-sc` 自托管 | 宿主无中文字体；避免中文显示方框 |
| 状态 | 单一 `useReducer` 状态机 | 原型已验证；集中、可测、无额外 Store |
| Mock | 两个普通 TS 服务契约：Wallet、Identity | 现在 Mock；以后在同一边界替换真实实现 |
| 页面切换 | 内存 Screen 状态，不引入 Router | v0.1 无分享 URL；原型也无 URL 路由 |
| UI 基础 | 语义 HTML、原生 `<dialog>`、Pointer/Clipboard/File API | 少依赖；保留无障碍与完整交互 |
| 测试 | Node 内建 test + TypeScript 检查 + Next.js build + 真浏览器验收 | 覆盖业务状态与真实 UI，不加测试框架 |

以 `reference/xLog-dev` 的 Next.js App Router 工程结构为架构基线，不复制其 AGPL 业务代码。只引入当前功能实际需要的基线依赖；依赖版本以迁移时官方 npm `latest` 为准，并由 lockfile 固定。

## 范围

### 实现

- Wallet：Connect、Approve/Reject、Retry、Disconnect、Account Switch。
- Identity Resolve：`none / active / incomplete / failed`。
- Identity Create：Setup、Review、钱包确认、Processing、Ready、Cancelled、Failed。
- Identity：My Identity、Edit Profile、Public Identity、Proof。
- Profile：Avatar、Name、Type、Bio、校验、脏表单离开保护、保存全状态。
- 通用：完整 BAP ID/TxID Copy、English/中文、Light/Dark、响应式、Reduced Motion、Toast、Demo 故障注入。
- 3D Card：自动旋转、拖拽、暂停/恢复、重置、正反面与厚度。

### 不实现

- 真实钱包、真实 API、数据库、后端路由、链上广播。
- Content、Artifact、Explorer/Search、Relationship、Attestation、Messaging。
- Key Rotation、Public 分享 URL、登录态持久化。
- 原型之外的设计改版或完整 React Spectrum 组件库。

## 最小结构

```text
frontend/
├── package.json
├── pnpm-lock.yaml
├── next.config.ts
├── postcss.config.mjs
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   └── page.tsx
│   ├── App.tsx
│   ├── domain.ts          # 类型、状态机、校验、常量
│   ├── mocks.ts           # Wallet/Identity Mock 与故障注入
│   ├── messages.ts        # 唯一中英文字典
│   ├── ui.tsx             # 少量共享原生 UI
│   ├── screens-wallet.tsx
│   ├── screens-identity.tsx
│   ├── screens-public.tsx
│   └── styles.css         # Tailwind v4 主题、组件与必要原生 CSS
└── tests/
    ├── domain.test.ts
    └── stack.test.ts
```

只在文件确实过大时再拆分。数据流固定为：

```text
Screen 事件 → App/useReducer → Wallet/Identity 契约 → Mock
                    ↓
             单一状态渲染所有 Screen
```

## 业务状态规则

- Wallet、Identity、Profile 三个概念分离；Wallet Connected 不等于 Identity Active。
- Wallet Reject 映射 `cancelled`；处理异常映射 `failed`，两者不得混用。
- Account Switch/Disconnect 递增操作序号，忽略旧异步结果，清空旧 Identity，重新 Resolve。
- `incomplete` 表示 Identity 已发布，只补全 Profile；不得再次 Create Identity。
- 创建/保存均执行：意图 → Review → Wallet Confirm → Processing → Result → Details。
- 只持久化 `locale`、`theme`；刷新后 Wallet 回到未连接。
- 所有完整标识只保留一份原值；缩略仅用于展示，Copy 永远复制原值。
- Profile 校验只有一个函数，同时驱动字段错误与按钮门禁。
- Avatar 白名单只有一个常量：PNG/JPEG/WebP，最大 2 MiB；`accept` 由它生成。

## 原型勘误：实现时直接修正

1. Cancelled/Failed 顶栏错误显示 Connected：改为 Wallet 状态穷尽映射，并表驱动测试。
2. Name/Bio 超长仍可进入 Review：统一校验函数阻断。
3. `incomplete` 错误复用 Create：改为 Complete Profile/Save。
4. SVG 可绕过 Avatar 声明：MIME 单一白名单。
5. Public `<dl>` 结构非法、控制组缺 role：改为合法语义结构。
6. 中文字体缺失：自托管 Noto Sans SC，不依赖操作系统字体或 CDN。
7. Wallet/Demo 部分焦点仅浏览器默认 1px：统一 2px `:focus-visible`。
8. 移动端 Demo 浮钮进入内容区：改为不遮挡内容的底部抽屉入口。

## 执行阶段与提交

### 0. 评审门禁

- [x] 胡先生确认目标目录、技术栈、范围、勘误策略。
- **状态：** completed。

### 1. 工程与视觉基座

- **状态：** completed。Commit `f3498a2`。
- 初始化独立 Vite/React/TypeScript 工程和 lockfile。
- 建立 token、字体、主题、Locale、App Shell、Welcome/Dome/Footer。
- 迁移 SVG/CSS；无远程运行时资源。
- 最小测试：偏好默认值与持久化规则。
- **提交：** `feat(frontend): 建立原型视觉基座与偏好设置`

### 2. Wallet 与 Resolve

- **状态：** completed。Commit `9a0bdea`。
- 实现 Wallet Mock、授权 Dialog、连接/取消/失败/重试/断开。
- 实现 Resolve 三态、失败恢复、Account Switch、旧请求失效。
- 状态映射与切换规则表驱动测试。
- **提交：** `feat(frontend): 实现钱包与身份解析 Mock 流程`

### 3. Setup、Review、Create

- **状态：** completed。Commit `5a2280a`。

- 实现 Profile Form、Avatar、校验、Review。
- 实现创建确认、Processing、Ready、Cancelled、Failed。
- 测试字段边界、MIME/2 MiB、三类结果。
- **提交：** `feat(frontend): 实现身份设置与创建流程`

### 4. My Identity 与 Edit

- **状态：** completed。Commit `b9ebab7`。

- 实现 My Identity、完整 ID Copy、Edit、脏表单保护。
- 实现保存确认、成功/拒绝/失败保值；`incomplete` 走 Profile 补全。
- 测试 Copy 原值和保存状态。
- **提交：** `feat(frontend): 实现身份详情与资料编辑流程`

### 5. Public Identity、3D 与 Demo

- **状态：** completed。Commit `56663e7`。

- 实现 3D 卡、拖拽/旋转/暂停/重置、Proof、完整 TxID/BAP ID。
- 实现 Reduced Motion、Demo 故障注入与移动端抽屉。
- 修正语义结构和焦点样式。
- **提交：** `feat(frontend): 实现公开身份卡与故障演示`

### 6. 集成验收与收口

- **状态：** completed。Fix commit `533bccd`。

- 宿主环境 TypeScript、9 个 Node tests、production build 全部通过。
- 真浏览器完成主路径、故障恢复、双语/主题、移动端和无障碍验收。
- 修复 Welcome 标题跳级与 favicon 404；全新 production 会话复验通过。
- 证据写入 `progress.md` 与 `frontend/artifacts/dogfood/report.md`。
- **提交：** 仅在发现问题时使用对应 `fix(frontend): ...`；不制造空提交。

### 7. xLog 最新技术栈迁移

- **状态：** completed。Commit `a0b893a`。
- 审计 xLog App Router、Provider、Tailwind 与 pnpm 结构。
- 从 Vite 迁移到 Next.js App Router，保留既有 UI、状态机、Mock 边界与测试。
- 将布局、间距、排版、响应式和常规组件样式迁移到 Tailwind CSS；全局 CSS 只保留 Token、伪元素、3D 和关键帧。
- 使用官方 npm `latest` 版本，生成 pnpm lockfile。
- 执行 TypeScript、业务测试、production build 与真浏览器回归。
- **提交：** `refactor(frontend): 迁移至 xLog 最新技术栈 (PRD v0.1)`

## 验收门禁

### 自动化

- TypeScript strict：0 error。
- `node:test`：状态映射、三态分流、异步失效、表单边界、Copy 原值全部通过。
- Next.js 16 production build：成功；App Router 静态生成，Tailwind v4 编译成功。

### 浏览器

- 视口：1440×900、320×800；无横向溢出。
- 主题/语言：Light/Dark、English/中文；刷新后偏好保留，中文无方框。
- 主路径：Connect → Resolve → Setup → Review → Create → My → Edit → Public。
- 故障路径：Connect/Resolve/Create/Save 的 Reject、Failed、Retry；Account Switch、Disconnect。
- Public：正面、背面、斜角；自动旋转、拖拽、暂停、重置；Reduced Motion 静态降级。
- Copy：Clipboard 严格等于完整 BAP ID/TxID；Toast 由 `aria-live` 宣告。
- Console：0 业务 error/warning；Network：0 外部 API/钱包/CDN 请求。
- WCAG A/AA 自动审计：0 violation；键盘顺序、Dialog 焦点、Light/Dark 对比人工复核。

### 交付证据

- 每阶段命令、结果、截图和日志位置写入 `progress.md`。
- 每个功能阶段有独立 Git commit；只精确暂存任务文件，不混入现有工作树修改。
- 最终提供功能矩阵、测试结果、提交清单、已知限制。

## 已知环境事项

| 事项 | 执行策略 |
|---|---|
| Corepack 默认 cache 只读 | `COREPACK_HOME` 指向工作区或 `/tmp` |
| 安装依赖需要网络 | 评审通过后按需申请宿主权限 |
| 集成/接口测试必须宿主运行 | Next production 预览和浏览器验收均用宿主环境 |
| xLog 无 `node_modules` | 不复用其安装目录；目标工程独立安装 |
| 根工作树有大量无关修改 | 不清理、不覆盖；精确路径暂存 |

## Review 结果

胡先生已通过以下四点：

1. 新建独立仓库 `/home/haodev/ownword/frontend`。
2. 原评审采用 Vite；胡先生于 2026-08-20 明确将其替换为 xLog 最新技术基线。
3. 保留原型视觉，但直接修正上述 8 个已证实缺陷。
4. v0.1 只做列出的 Mock 闭环，不扩展真实钱包/API 和其他模块。

全部执行阶段已完成。
