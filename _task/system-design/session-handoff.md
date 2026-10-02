# 会话交接

本轮已完成 [v0.1.0 身份前端实现计划](spec/frontend/前端实现计划v0.1.0-20261002-230500.md) 和 v0.4.0 首页冗余介绍区删除。当前状态见 [progress.md](progress.md)，事项范围与证据见 [feature_list.json](feature_list.json)。

唯一下一步是按用户后续指令进入计划 F00–F05。前端位置为 `C:\haodev\ownword\_task\fronted-worktree\own-word-web`，起点为 `master@34353ef08050f29d79bf15965b13093882e4e817`；本轮未修改该仓库。恢复时读取沿途 AGENTS.md 和计划，先核对是否有新改动，再开始对应阶段。

用户确认只做 v0.1 身份功能；钱包、后端及一切阻塞依赖可先 Mock，必须定义与实际 API 对应的契约，真实接入后续替换。当前原型用于视觉、v0.1 PRD 用于范围，排除内容、Artifact、全局搜索、密钥轮换及可分享公开主页。禁止使用任何子代理。

原型在独立 worktree，最近源码提交 `c76ad3d`，预览 `http://127.0.0.1:4314/`。原型后续调整先读取 [版本任务规则](../prototype-worktree/ownword-v0.4.0/AGENTS.md) 和 [任务清单](../prototype-worktree/ownword-v0.4.0/feature_list.json)，再在其任务目录运行 `./init.ps1`；重启先核实 `.runtime/server.json`。自动验证不代表用户视觉批准。
