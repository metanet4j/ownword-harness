# 后端任务工作区

OwnWord 根仓库只跟踪本目录第一级文件，包括 [AGENTS.md](AGENTS.md)、[mvn-command.md](mvn-command.md) 和本文件。所有任务子目录均由根 `.gitignore` 忽略，新的任务目录自动适用。

## 当前入口

本目录当前无任务子目录。Boot 4 / Java 25 升级、BSV SDK 迁移和 JungleBus 迁移的 `doc` 文档已集中到[知识库](../../知识库/README.md)，原任务脚本、缓存、构建产物和过程附件已清理。

后端开发入口见 [backend 仓库清单](../../backend/README.md)。BSV SDK 和 JungleBus 的主仓库及 Git 数据库均位于 `backend/` 下，任务分支和提交历史保留。

## 约定

- 工程与环境规则见 [AGENTS.md](AGENTS.md)，Maven 命令见 [mvn-command.md](mvn-command.md)。
- 临时任务资料在本地任务目录维护；需长期保存的文档迁入知识库，源码在对应独立仓库提交。
- 删除任务 worktree 前，确认工作区干净且 HEAD 已包含在目标分支中，使用 `git worktree remove` 清理关联工作区。
