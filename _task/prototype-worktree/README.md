# 原型 worktree 任务目录

采用“任务容器 + 独立原型 worktree”的结构。OwnWord 根仓库只跟踪本目录第一级文件；所有子目录及其中的任务说明、harness、源码、证据和缓存均由根 `.gitignore` 忽略，在本地保留。新的任务目录自动适用，原型源码在对应独立仓库提交。

| 任务 | 入口 | 原型目录与当前可用性 |
| --- | --- | --- |
| v0.2.0 文字内容高保真原型 | [任务指南](ownword-v0.2.0/AGENTS.md) | `ownword-v0.2.0/ownword-prototype/`；具体状态见任务容器 |
| v0.3.0 Identity Artifact 原型 | [任务指南](ownword-v0.3.0/AGENTS.md) | 登记路径为 `ownword-v0.3.0/ownword-prototype/`，源码已从最新远端分支取得，待恢复该入口的 worktree；状态见任务容器 |
| v0.4.0 Identity 个人主页原型 | [任务指南](ownword-v0.4.0/AGENTS.md) · [交付说明](ownword-v0.4.0/交付验收v0.4.0-20261012-224835.md) | `ownword-v0.4.0/ownword-prototype/`；继承最新 v0.3.0，P01–P10 已实现并验证，等待用户视觉复核；[本地预览](http://127.0.0.1:4314/) |

基线、分支、启动方法与任务进展在任务容器内维护。

当前 v0.4.0 从已核实的 v0.3.0 提交 `1355bdc` 建立，分支为 `codex/prototype-v0.4.0-homepage`。原型仓库为 `https://github.com/metanet4j/ownword-design-prototype.git`，基线与逐项源码提交查 v0.4.0 任务容器。作废的旧 v0.4.0 文件和验收记录已删除。
