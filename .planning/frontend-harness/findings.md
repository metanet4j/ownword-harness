# 发现与决策

## 需求

- 对 `frontend` 执行 `harness-creator`。
- 保留当前运行中的预览服务。

## 研究发现

- Frontend 为独立 Git 仓库，当前工作树干净。
- `package.json` 已提供 `dev`、`typecheck`、`test`、`build`、`start`。
- Frontend 当前没有 `AGENTS.md`、`feature_list.json`、`progress.md`、`init.sh` 或 `session-handoff.md`。
- Next.js 16 dev 会自动生成 `AGENTS.md` 与 `CLAUDE.md`；若不控制，会产生重复指令与未提交变更。
- 官方生成器已创建五个最小文件，但内容是通用英文占位符，必须替换后才可使用。
- 生成的 `init.sh` 使用 `set -e`，能中止失败；仍应补 `set -u` 与 `pipefail`，并在缺少 pnpm/node_modules 时给出明确错误。
- 最近提交确认 Frontend 基线已完成：`a0b893a` 为 xLog 最新栈迁移，`4bce3de` 为 Tailwind utilities 完整迁移。
- Next.js 16.3.1 本地 schema 明确定义顶层 `agentRules?: boolean`；设置 `false` 是受支持配置。
- 运行中的旧 dev 进程已在配置生效前改写 `next-env.d.ts`；停止 dev 并运行 production build 后应恢复仓库版本，不能提交该生成差异。
- `./init.sh` 完整通过：TypeScript 0 错误、Node tests 10/10、Next.js 16.3.1 production build 成功。
- 首次 Frontend Harness 校验为 64/100：Verification 5/5、State 4/5；多数失败项来自中文标题/措辞未命中英文结构规则，Scope 与 Lifecycle 仍需对照规则复核。
- 校验器只扫描 Markdown 标题、列表、表格与代码块中的固定英文术语。用中英双语标题表达同一结构即可兼顾中文可读性与自动发现，无需重复规则正文。
- 中英双语结构标记后，五个子系统全部 5/5，总分 100/100，无 bottleneck。
- 静态审计通过：JSON 有效、Shell 语法有效、无生成器占位内容、`git diff --check` 无错误；`next-env.d.ts` 已由 production build 恢复干净。
- Frontend Harness 提交为 `b4a30a1`。production 预览已恢复到 3000，HTTP 200，Frontend 工作树干净。

## 技术决策

| 决策 | 理由 |
|------|------|
| 先运行官方生成脚本，再做最小适配 | 遵循 harness-creator 工作流 |
| 增加单一验证入口 | 防止只跑部分检查便声称完成 |
| 项目事实放进状态文件，AGENTS 只保留路由与门禁 | 保持短小、遵守 DRY |
| 在 Next 配置关闭自动 Agent 文件生成 | 避免每次 `pnpm dev` 污染工作树与覆盖指令边界 |
| 状态只记录已完成产品基线与当前 Harness 功能 | 删除生成器的虚构功能占位，避免 Agent 执行不存在的需求 |

## 遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 暂无 | — |
| 首次搜索 `agentRules` 同时命中大型 source map，输出过量 | 已从 `config-schema.js` 的精确命中确认类型，不再扫描 source map |
| `next-env.d.ts` 在 dev 运行期间再次变更 | 停止 dev，运行完整验证后确认它恢复；若仍有差异，只恢复该生成文件 |
| 中文 Harness 结构未命中固定英文检测词 | 标题补充精确英文别名，如 `Startup Workflow`、`Definition of Done`、`End of Session` |

## 资源

- `.agents/skills/harness-creator/SKILL.md`
- `frontend/package.json`
- `frontend/next.config.ts`
