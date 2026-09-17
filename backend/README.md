# backend/ 子仓库清单

`backend/` 下的下列子目录均为**独立 Git 仓库**，不纳入 ownword 主仓（根目录 `.gitignore` 已忽略）。
数据由 `git -C <仓库> remote -v` 与 `git -C <仓库> rev-parse` 采集于 2026-09-17。

| 子目录 | 当前分支 | HEAD | 远程仓库 |
|---|---|---|---|
| `bitcoinj-sv/` | `master` | `1946a149` | https://github.com/bitcoin-sv/bitcoinj-sv.git |
| `metanet4j-parent/` | `dev` | `50598c0` | https://github.com/metanet4j/metanet4j-parent.git |
| `metanet4j-base/` | `dev` | `6e16cfa` | https://github.com/metanet4j/metanet4j-base.git |
| `metanet4j-sdk/` | `dev` | `bae4c36` | https://github.com/metanet4j/metanet4j-sdk.git |
| `metanet4j-component/` | `dev` | `e634982` | https://github.com/metanet4j/metanet4j-component.git |

## 约定

- 子仓库独立提交、独立推送，内容不进入 ownword 主仓。
- `metanet4j-*` 四个仓库有依赖顺序：`parent` → `base` → `sdk` → `component`。
- 改这些目录时先进对应仓库操作，不要在主仓对它们执行 `git add`。
- 新增或移除子仓库后更新本表，并在根目录总入口登记位置。
