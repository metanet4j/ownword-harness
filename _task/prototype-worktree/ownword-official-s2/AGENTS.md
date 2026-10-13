# 官方组件改造版

遵循根 AGENTS.md。产品事实与页面依据继续使用核心认知及 v0.4.0 PRD。

- 本任务只修改本目录的新 worktree，分支 codex/prototype-official-s2；基线 5b3cdf8。原 v0.4.0 worktree 与 4314 预览保留。
- 用户已授权完整迁移官方组件并交付独立预览；独立执行，不使用子代理。
- 优先使用 @react-spectrum/s2@1.6.0 官方运行时和公开 API；保留 OwnWord 业务组合、媒体与版式。身份、钱包、发布为确定性模拟。
- 开工读取 feature_list.json、progress.md；恢复时读取 session-handoff.md。
- 修改源码后运行 npm run build；验收包括构建来源核对、继承模型、受影响页面浏览器正常与边界流程、主题双语与键盘、截图审阅。
- ./init.sh 检查，./init.sh --serve 在 4315 提供独立预览；端口占用时不终止其他进程。
- 原型提交在独立仓库，消息含 (PRD v0.4.0_YYYYMMDD-HHMMSS)；任务状态在根仓库提交，仅纳入本任务文件。
- 实现、验证、提交完成后记 implemented-and-verified，用户视觉复核前保持 needs-review。
