# 后端任务工作区

OwnWord 根仓库只跟踪本目录第一级文件，包括 [AGENTS.md](AGENTS.md)、[mvn-command.md](mvn-command.md) 和本文件。所有子目录及其中的任务文档、源码、证据和缓存均由根 `.gitignore` 忽略，在本地保留；新的任务目录自动适用。

## 当前仓库状态

以下任务的子仓库提交均已包含在各自的本地 `dev` 分支中，任务目录内已无代码仓库；任务资料仍保存在本地。

| 任务目录 | 已清理子仓库数 |
| --- | --- |
| `boot4-java25-upgrade/` | 4 |
| `bsv-sdk-java-migration/` | 5 |
| `ownword-v0.1.0/` | 6 |
| `ownword-v0.2.0/` | 1 |

后端开发入口见 [backend 仓库清单](../../backend/README.md)。`metanet4j-bsv-sdk` 的主仓库与 Git 数据库存放在 `backend/metanet4j-bsv-sdk/`，原任务分支和提交历史保留。

## 约定

- 工程与环境规则见 [AGENTS.md](AGENTS.md)，Maven 命令见 [mvn-command.md](mvn-command.md)。
- 任务资料在本地任务目录维护；源码在对应独立仓库提交。
- 删除任务 worktree 前，确认工作区干净且 HEAD 已包含在目标分支中，使用 `git worktree remove` 清理关联工作区。
