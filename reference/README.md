# reference/ 说明

本目录存放外部项目的参考源码与文档，用于查阅和设计取证。它们不是 Ownword 的运行依赖。主仓只保存本说明与[来源锁定清单](sources.lock.json)，源码目录继续忽略。

| 本地目录 | 当前用途 | 官方上游 |
| --- | --- | --- |
| `1sat-ordinals-master/1sat-ordinals-master/` | 1Sat 协议与术语，已核对并保留 Git 元数据 | [BitcoinSchema/1sat-ordinals](https://github.com/BitcoinSchema/1sat-ordinals) |
| `bap-master/bap-master/` | BAP 身份协议与实现，已同步 | [BitcoinSchema/bap](https://github.com/BitcoinSchema/bap) |
| `yours-wallet-main/yours-wallet-main/` | Yours Wallet 源码、依赖与 Provider 文档，已同步 | [yours-org/yours-wallet](https://github.com/yours-org/yours-wallet) |
| `1sat-sdk/` | 钱包 Actions、客户端、身份与签名实现，已补充 | [b-open-io/1sat-sdk](https://github.com/b-open-io/1sat-sdk) |
| `1sat-stack/` | 服务端路由、索引与身份解析实现，已补充 | [b-open-io/1sat-stack](https://github.com/b-open-io/1sat-stack) |
| `react-spectrum-main/` | 既有 Adobe 源码快照，本次未核对 | 未登记 |
| `schema-master/` | 既有 BitcoinSchema 快照，本次未核对 | 未登记 |

五份已核对资料的分支、commit、Git tree、文件数、核对时间和关键包版本集中记录在来源锁定清单。它们是浅克隆，仅用于参考；后续更新须先检查本地改动，再同步上游并重验清单。现有目录名沿用旧名称，以保持设计文档链接有效。先前列出的 `xLog-dev/` 当前不存在，不作为可用本地资料。

## 查阅入口与已知差异

当前上游代码和文档仍有差异。保留上游原文，以以下源码入口核对调用方式；不能因完成同步就认定所有文档示例可运行。

| 内容 | 当前查阅入口与结论 |
| --- | --- |
| 资产列表与转移 | Yours [实际调用](yours-wallet-main/yours-wallet-main/src/pages/OrdWallet.tsx)与 SDK [Ordinal Actions](1sat-sdk/packages/actions/src/ordinals/index.ts)使用 `listOrdinals`、`sendOrdinals`；[Provider 文档](yours-wallet-main/yours-wallet-main/docs/provider-api.md)仍有 `getOrdinals`、`transferOrdinals` 旧名称。 |
| 转移参数与交易材料 | `sendOrdinals` 的 `transfers` 项使用钱包 basket 的 tracking `id` 和接收地址或公钥。动作内部装载当前输出与 BEEF；不要将 Origin、Inscription ID 或旧文档中的 `WalletOutput` 直接当作此参数。列表默认不保证附带 BEEF。 |
| 身份与签名 | [身份 Actions](1sat-sdk/packages/actions/src/identity/index.ts)、[AIP](1sat-sdk/packages/actions/src/signing/aip.ts)、[Sigma](1sat-sdk/packages/actions/src/signing/sigma.ts)。`resolveBapId` 查询钱包 basket；公共身份解析见 [BapClient](1sat-sdk/packages/client/src/services/BapClient.ts)及[服务端路由](1sat-stack/pkg/bap/routes.go)。Ownword 的全交易签名要求及未闭合能力以[核心认知第 6.4、12 节](../_task/system-design/spec/核心认知.md)为准。 |
| 编号与内容解析 | [术语](1sat-ordinals-master/1sat-ordinals-master/readme/terms.md)定义 Inscription Number；[OrdFS 客户端](1sat-sdk/packages/client/src/services/OrdfsClient.ts)与[服务端](1sat-stack/pkg/ordfs/routes.go)中的 `sequence` 是资产转移链内序号，不能当作全局 Inscription Number。metanet4j 的编号补齐责任见核心认知。 |
| 旧公共 API | [public-apis.md](1sat-ordinals-master/1sat-ordinals-master/public-apis.md)已经标注 Historical。旧 GorillaPool 端点只作历史资料，新接入以锁定版本的 SDK、服务端及实际部署为准。 |

Yours 锁定的 `@1sat/actions`、`@1sat/client` 版本与本地 SDK 上游 HEAD 中的包版本不同，具体数值见来源锁定清单。后续集成必须选定同一依赖组合验证；本次没有安装依赖、编译钱包或调用真实交易。

## 注意

- 目录内含上游配置和部署示例，源码整体忽略，避免将示例或运行态误纳入主仓。
- 本次替换前的三份快照已保留，目录见来源清单的 `previousSnapshotsBackup`，未删除来源不明的旧文件；备份仅用于必要恢复，不作为当前设计依据。
- 更新参考资料不等于升级 Ownword 产品依赖，也不证明线上服务可用。文档结论需要对应源码证据；接口行为仍须按实际版本验证。
