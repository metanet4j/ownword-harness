# reference/ 说明

本目录存放**外部项目的源码快照**，用于查阅与对照，不属于 ownword 主仓的产物。
目录整体忽略（`.gitignore` 的 `/reference/*`），只保留本说明以标注目录结构。

| 子目录 | 性质 | 远程仓库 |
|---|---|---|
| `1sat-ordinals-master/` | 上游源码快照（解压副本，无 `.git`） | 无 |
| `bap-master/` | 上游源码快照 | 无 |
| `react-spectrum-main/` | Adobe React Spectrum 上游源码 | 无 |
| `schema-master/` | 上游源码快照 | 无 |
| `xLog-dev/` | 上游源码快照 | 无 |
| `yours-wallet-main/` | 上游源码快照 | 无 |

## 注意

- 目录内含上游自带的 `.npmrc`、`.env.example`、`deploy/*/secret.yaml` 等示例文件，整体忽略可避免误入库。
- 升级某份快照时直接替换对应子目录，本说明不记录版本号。
