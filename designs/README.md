# designs/ 子仓库清单

`designs/` 下的下列子目录是**独立 Git 仓库**，不纳入 ownword 主仓（根目录 `.gitignore` 已忽略）。
数据由 `git -C <仓库> remote -v`、`git -C <仓库> worktree list` 与 `git rev-parse` 采集于 2026-10-15。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `own-word-prototype-pick/` | `dev` | `fb6ed59` | https://github.com/metanet4j/ownword-design-prototype.git |
| `ownword-design-prototype/` | `master` | `50673d0` | 无（同一远端的旧克隆，已解除远端关联，仓库保留本地） |

`own-word-prototype-pick/` 是四个原型任务 worktree 的主仓，任务到 worktree 的对应关系见 [_task/prototype-worktree/README.md](../_task/prototype-worktree/README.md)，链接关系以 `git worktree list` 为准。

## 被忽略的非仓库目录

| 子目录 | 性质 | 处理 |
|---|---|---|
| `react-spectrum-s2/` | 第三方 design system 副本，非 Git 仓库 | 从索引移除并整体忽略，内容不入主仓 |

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- 改这些目录时先进对应仓库操作，不要在主仓对它们执行 `git add`。
- 新增或移除子仓库后更新本表，并在根目录总入口登记位置。
