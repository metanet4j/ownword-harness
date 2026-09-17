# fronted-worktree/ 子仓库清单

`_task/fronted-worktree/` 下的下列子目录是前端工作副本，不纳入 ownword 主仓（根目录 `.gitignore` 已忽略）。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `own-word-web/` | — | — | — |

## 说明

- `own-word-web/` 目前**没有 `.git`**（只是工作副本，不是独立 Git 仓库）；按子仓库口径整体忽略。
- 若后续把它变成独立仓库（`git init` 或从远程 clone），在上表补分支、HEAD、远程地址。

## 约定

- 改这些目录时先进对应仓库操作，不要在主仓对它执行 `git add`。
- 新增或移除子仓库后更新本表，并在根目录总入口登记位置。
