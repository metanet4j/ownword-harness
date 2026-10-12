# v0.4.0 Identity 个人主页原型任务指南

遵循[根 AGENTS.md](../../../AGENTS.md)。产品事实查[核心认知](../../system-design/spec/核心认知.md)，页面与验收查[v0.4.0 设计文档](../../system-design/spec/prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md)，不读取 Archive 或 spec/draft。

## 开工（Startup Workflow）

1. 完整阅读本文件、feature_list.json、progress.md 和 session-handoff.md。
2. 检查根仓库、来源原型仓库与 ownword-prototype 的状态，保留他人改动。
3. 运行 `./init.sh --plan` 检查任务与验收登记；运行 `./init.sh` 检查真实 worktree 和继承基线。Windows 使用 init.ps1。
4. 基线未恢复时只推进可独立完成的审查与任务准备；基线、worktree 和页面均未通过时不得称为已初始化或已制作。

## 范围与授权

- 用户已授权审查后连续完成 P01–P10，不在每项结束时重复请求批准。
- 本任务独立执行，不使用子代理。
- One feature at a time：activeFeature 与唯一 in-progress 事项一致，依赖以 feature_list.json 为准。
- 原型必须基于经核实的 v0.3.0；基线、来源、实际分支和端口以 environment 为准。任务记录与截图不替代源码。
- 保留 v0.3.0 的 S2 绑定、共用组件、字体、主题、模块导航、身份上下文、内容和 Artifact 体验；新公开路由通过适配接入，不覆盖旧管理模块。
- 制作用 baoyu-design，读取基线 _d_meta.json 与绑定提示；react-spectrum 检查组件、Token、交互和无障碍，不升级或重新导入另一套运行时。
- 身份、Wallet、关系交易、索引与 Proof 使用确定性样例。导航、复制、筛选、媒体播放和键盘操作实际工作，不接真实钱包或生产 API。

## 提交与验证（Verification Commands）

- 原型为独立 Git worktree，源码和功能证据提交到原型仓库；harness、审查与任务状态提交到根仓库。
- 每完成一项即提交，原型提交含 `(PRD v0.4.0_YYYYMMDD-HHMMSS)`；合并与推送按用户授权。
- `./init.sh --plan`：检查 PRD、32 条 BDD、功能依赖、状态和文档引用；不表示 worktree 可用。
- 源码、CSS、模型或页面模板修改后运行 `npm run build`；纯文档修改无需重建。预览使用预编译资源，不在浏览器内使用 Babel。
- `./init.sh`：检查预编译产物的新鲜度、来源对象、Git 祖先、实际 S2 绑定和资源、语法、继承模型与 harness 结构。
- `./init.sh --serve`：通过检查后前台启动独立预览，端口占用时明确失败，不终止其他进程。
- 每项默认验证正常场景、相关边界和受影响截图，按 PRD 累积全部 BDD 证据。好友必须完成双方操作，媒体必须实际播放；不默认重跑全量旧版矩阵。
- 浏览器使用 agent-browser 独立 session。检查、实际浏览器证据、视觉评审和生产验证分别记录。
- H00 证据位于任务 evidence；功能证据位于原型 evidence/homepage-v040；运行日志放 .runtime，不提交。

## 完成标准（Definition of Done）

实现、验证、截图与日志审阅、提交完成后记录 implemented-and-verified，并保持 needs-review；用户视觉复核前不标记 done。未检查项目不能记为通过，缺失基线不得以旧版替代。

## 收尾（End of Session）

更新 feature_list.json、progress.md 与 session-handoff.md，保留唯一下一步。根 system-design 只引用本任务的功能状态与证据，不重复定义设计事实。环境需可重复启动，未完成工作如实交接。
