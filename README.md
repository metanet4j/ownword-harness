# 子仓库清单总入口

ownword 主仓内有多处子目录本身是**独立 Git 仓库**，不纳入主仓管理（根目录 `.gitignore` 已显式忽略）。
本文件只做总入口，登记"哪个目录装着子仓库"；各仓库的分支、HEAD、远程地址写在对应目录的清单里，避免重复维护。

技术方案、迁移计划、协议契约与验收文档统一从[知识库](知识库/README.md)查阅。

| 位置 | 内容 | 明细 |
|---|---|---|
| `frontend/` | `ownword-web/` 独立前端仓库，保留 v0.1/v0.2 版本分支 | [`frontend/README.md`](frontend/README.md) |
| `designs/` | 4 个独立仓库 + 1 个被忽略的第三方 vendor | [`designs/README.md`](designs/README.md) |
| `backend/` | 7 个独立仓库 | [`backend/README.md`](backend/README.md) |
| `_task/fronted-worktree/` | 前端任务入口说明；旧任务目录已清理 | [`_task/fronted-worktree/README.md`](_task/fronted-worktree/README.md) |
| `Archive/prototype/` | 3 个仅本地的独立仓库 | [`Archive/prototype/README.md`](Archive/prototype/README.md) |
| `_task/backend-worktree/` | 后端任务规则与 Maven 规范；旧任务目录已清理 | [`_task/backend-worktree/README.md`](_task/backend-worktree/README.md) |
| `reference/` | 6 份外部源码快照，非 Git 仓库，整体忽略 | [`reference/README.md`](reference/README.md) |

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- 改子仓库时进对应仓库操作，不要在主仓对它执行 `git add`。
- 新增或移除子仓库后，更新对应目录清单，并在本表登记位置。
