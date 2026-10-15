# backend/ 子仓库清单

`backend/` 下的下列子目录均为**独立 Git 仓库**，不纳入 ownword 主仓（根目录 `.gitignore` 已忽略）。
分支与提交以各仓库的实际 Git 状态为准；迁移计划、协议契约和验收文档见[知识库](../知识库/README.md)。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `bitcoinj-sv/` | `master` | `1946a149` | https://github.com/bitcoin-sv/bitcoinj-sv.git |
| `metanet4j-parent/` | `dev` | `917b7bd` | https://github.com/metanet4j/metanet4j-parent.git |
| `metanet4j-base/` | `dev` | `279a7a6` | https://github.com/metanet4j/metanet4j-base.git |
| `metanet4j-sdk/` | `dev` | `bb298d0` | https://github.com/metanet4j/metanet4j-sdk.git |
| `metanet4j-component/` | `dev` | `fbb048e` | https://github.com/metanet4j/metanet4j-component.git |
| `metanet4j-bsv-sdk/` | `dev` | `10fd42d` | https://github.com/metanet4j/metanet4j-bsv-sdk.git |
| `metanet4j-junglebus/` | `dev` | `1272067` | 本地独立工程；来源与许可证见[协议契约](../知识库/后端/junglebus-java25-migration/API与协议契约-20261013-114000.md) |

BSV SDK 和 JungleBus 的主仓库与 Git 数据库分别存放在 `metanet4j-bsv-sdk/` 和 `metanet4j-junglebus/`；原任务分支与提交历史保留。旧任务目录已清理，后端任务规则见[后端任务工作区](../_task/backend-worktree/README.md)。

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- `metanet4j-*` 四个仓库有依赖顺序：`parent` → `base` → `sdk` → `component`。
- 改这些目录时先进对应仓库操作，不要在主仓对它们执行 `git add`。
- 新增或移除子仓库后更新本表，并在根目录总入口登记位置。
