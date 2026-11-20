# 前端仓库

本目录作为前端仓库容器。源码位于 `ownword-web/`，由独立 Git 仓库管理；OwnWord 根仓库只管理本说明，并通过 `.gitignore` 排除该子仓库。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
| --- | --- | --- | --- |
| `ownword-web/` | `feature/ownword-v0.2.0` | `6f9bcca` | https://github.com/metanet4j/ownword-web.git |

`feature/ownword-v0.1.0`（`04bb127`）和 `master`（`34353ef`）均已推送到同名远端分支，尚未合并到 `master`。当前检出 `feature/ownword-v0.2.0`，它包含另两个分支的全部历史，业务实现（`app/`、`lib/`）位于此分支。

验收报告和状态记录见[前端知识库](../知识库/前端/README.md)。私有钱包、服务配置与头像数据仍保存在根目录 `.local-state/frontend/`，继续在本地保留并由 Git 忽略。
