# v0.1.0 原型视觉同步

遵循根 AGENTS.md。事实来源为核心认知，功能边界为 `_task/system-design/spec/prd/v0.1/设计文档v0.1.md`，设计系统固定使用当前绑定 Spectrum S2。

## 开工

读取 feature_list.json、progress.md、session-handoff.md，检查工作区与原型 Git 状态；运行 `./init.sh`。本次用户授权按 v0.1.0、v0.2.0、v0.3.0 顺序应用已确认的视觉优化，每版独立审查、修改和验收。独立执行，不使用子代理。

## 范围

只修改身份原型适用的字级、密度、辅助信息、返回入口与复制反馈；保持本版身份功能和绑定资源。页面使用 baoyu-design，frontend-design 参与审核，react-spectrum 核对组件、Token 与交互。

## 验证与提交

`./init.sh` 检查分支、基线、绑定、模型、文案、Token 与 JSX 语法；`./init.sh --serve` 在 4311 启动静态预览，端口被占用时失败，不终止其他服务。浏览器使用 agent-browser，核对正常与相关边界及实际截图。本版使用已有浏览器 Babel，不为视觉同步更换运行时。

原型独立提交并携带 `(PRD v0.1_YYYYMMDD-HHMMSS)`；任务文档提交到根仓库，只提交本任务变更。实现、验证及提交后标记 implemented-and-verified、needs-review，用户视觉复核前不标记 done；不因此阻塞后续已授权版本。

## 收尾

更新 feature_list.json、progress.md、session-handoff.md 与 system-design 总体进度，记录实际证据和唯一下一步。
