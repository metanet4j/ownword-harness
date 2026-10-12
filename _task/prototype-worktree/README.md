# 原型 worktree 任务目录

采用“任务容器 + 独立原型 worktree”的结构。任务说明与 harness 由根仓库管理，原型源码目录由根 `.gitignore` 显式排除，在对应原型仓库提交。

| 任务 | 入口 | 原型目录与当前可用性 |
| --- | --- | --- |
| v0.2.0 文字内容高保真原型 | [任务指南](ownword-v0.2.0/AGENTS.md) | `ownword-v0.2.0/ownword-prototype/`；具体状态见任务容器 |
| v0.3.0 Identity Artifact 原型 | [任务指南](ownword-v0.3.0/AGENTS.md) | 登记路径为 `ownword-v0.3.0/ownword-prototype/`，源码已从最新远端分支取得，待恢复该入口的 worktree；状态见任务容器 |
| v0.4.0 Identity 个人主页原型 | [任务指南](ownword-v0.4.0/AGENTS.md) | 计划路径为 `ownword-v0.4.0/ownword-prototype/`；任务准备中，尚未创建 worktree |

基线、分支、启动方法与任务进展在任务容器内维护。

v0.4.0 必须在已核实的 v0.3.0 原型基础上推进。原型仓库为 `https://github.com/metanet4j/ownword-design-prototype.git`；仓库地址和任务目录存在不代表已取得所需版本，实际基线核对结果查 v0.4.0 任务容器。
