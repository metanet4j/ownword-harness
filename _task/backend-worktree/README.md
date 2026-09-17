# backend-worktree/ 子仓库清单

`_task/backend-worktree/boot4-java25-upgrade/` 下的 4 个目录是**git worktree**，不是普通子目录：
`.git` 是**文件**（gitdir 指针），主仓库是 `backend/` 下的同名仓库。它们不纳入 ownword 主仓。
数据由 `git -C <仓库> remote -v` 与 `git -C <仓库> rev-parse` 采集于 2026-09-17。

| 子目录（worktree） | 所属主仓库 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|---|
| `boot4-java25-upgrade/metanet4j-parent/` | `backend/metanet4j-parent/` | `feature/java25` | `50598c0` | https://github.com/metanet4j/metanet4j-parent.git |
| `boot4-java25-upgrade/metanet4j-base/` | `backend/metanet4j-base/` | `feature/java25` | `6e16cfa` | https://github.com/metanet4j/metanet4j-base.git |
| `boot4-java25-upgrade/metanet4j-sdk/` | `backend/metanet4j-sdk/` | `feature/java25` | `bae4c36` | https://github.com/metanet4j/metanet4j-sdk.git |
| `boot4-java25-upgrade/metanet4j-component/` | `backend/metanet4j-component/` | `feature/java25` | `e634982` | https://github.com/metanet4j/metanet4j-component.git |

## 约定

- `boot4-java25-upgrade/` 内的开发规则以该目录的 `AGENTS.md` 与计划文档为准；本文件只登记仓库信息。
- 四个仓库有依赖顺序：`parent` → `base` → `sdk` → `component`。
- 子仓库独立提交；本任务不推送远端。
- 改动经 worktree 写入主仓库，主仓库提交历史独立于 ownword 主仓。
