# 子仓库清单总入口

ownword 主仓内有多处子目录本身是**独立 Git 仓库**，不纳入主仓管理（根目录 `.gitignore` 已显式忽略）。
本文件只做总入口，登记"哪个目录装着子仓库"；各仓库的分支、HEAD、远程地址写在对应目录的清单里，避免重复维护。

| 位置 | 内容 | 明细 |
|---|---|---|
| `frontend/` | 1 个独立仓库（仅本地），主仓根直属 | 见下表 |
| `designs/` | 4 个独立仓库 + 1 个被忽略的第三方 vendor | [`designs/README.md`](designs/README.md) |
| `backend/` | 5 个独立仓库 | [`backend/README.md`](backend/README.md) |
| `_task/fronted-worktree/` | 1 个独立仓库 + 1 个任务 worktree | [`_task/fronted-worktree/README.md`](_task/fronted-worktree/README.md) |
| `Archive/prototype/` | 3 个仅本地的独立仓库 | [`Archive/prototype/README.md`](Archive/prototype/README.md) |
| `_task/backend-worktree/boot4-java25-upgrade/` | 4 个 git worktree（主仓库在 `backend/`） | [`_task/backend-worktree/README.md`](_task/backend-worktree/README.md) |
| `reference/` | 6 份外部源码快照，非 Git 仓库，整体忽略 | [`reference/README.md`](reference/README.md) |

## 主仓根直属仓库

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `frontend/` | `master` | `b4a30a1` | 无（仅本地） |

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- 改子仓库时进对应仓库操作，不要在主仓对它执行 `git add`。
- 新增或移除子仓库后，更新对应目录清单，并在本表登记位置。
