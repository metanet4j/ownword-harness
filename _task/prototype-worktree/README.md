# 原型 worktree 任务目录

采用“任务容器 + 独立原型 worktree”的结构。任务说明与 harness 由根仓库管理，原型源码目录由根 `.gitignore` 显式排除，在对应原型仓库提交。

| 任务 | 入口 | 原型目录 |
| --- | --- | --- |
| v0.2.0 文字内容高保真原型 | [任务指南](ownword-v0.2.0/AGENTS.md) | `ownword-v0.2.0/ownword-prototype/` |

基线、分支、启动方法与任务进展在任务容器内维护。
