# fronted-worktree/ 子仓库清单

OwnWord 根仓库只跟踪本目录第一级文件；所有子目录及其中的任务文档、源码、证据和缓存均由根 `.gitignore` 忽略，在本地保留。新的任务目录自动适用，源码继续由各独立 Git 仓库管理。
主 clone 恢复基线核实于 2026-10-13。主 clone 已恢复，任务 worktree 的 19 份既有源码摘要保持一致；当前登记见[环境文件](ownword-v0.1.0/environment.json)。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `own-word-web/` | `master` | `34353ef` | https://github.com/metanet4j/ownword-web.git |

## 任务 worktree

| 任务目录 | worktree 子目录 | 所属主 clone | 分支 | HEAD |
|---|---|---|---|---|
| `ownword-v0.1.0/` | `own-word-web/` | `own-word-web/` | `feature/ownword-v0.1.0` | `04bb127` |
| `ownword-v0.2.0/` | `own-word-web/` | `own-word-web/` | `feature/ownword-v0.2.0` | 起点 `04bb127`；当前见[任务清单](ownword-v0.2.0/feature_list.json) |

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- 改这些目录时先进对应仓库操作，不要在主仓对它执行 `git add`。
- 新增或移除子仓库后更新本表，并在根目录总入口登记位置。
