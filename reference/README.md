# reference/ 说明

本目录存放外部项目的参考源码与文档，用于查阅和设计取证。它们不是 Ownword 的运行依赖。主仓只保存本说明与[来源锁定清单](sources.lock.json)，源码目录继续忽略。

| 本地目录 | 当前用途 | 官方上游 |
| --- | --- | --- |
| `1sat-ordinals-master/1sat-ordinals-master/` | 1Sat 协议与术语，既有快照，本轮未重核 | [BitcoinSchema/1sat-ordinals](https://github.com/BitcoinSchema/1sat-ordinals) |
| `bap-master/bap-master/` | BAP 身份协议与实现，实际包版本与清单登记不一致 | [BitcoinSchema/bap](https://github.com/BitcoinSchema/bap) |
| `yours-wallet-main/yours-wallet-main/` | Yours Wallet 源码、依赖与 Provider 文档，既有快照，本轮未重核 | [yours-org/yours-wallet](https://github.com/yours-org/yours-wallet) |
| `1sat-sdk/` | 钱包 Actions、客户端、身份与签名实现，固定版本已恢复并核对 | [b-open-io/1sat-sdk](https://github.com/b-open-io/1sat-sdk) |
| `1sat-stack/` | 服务端路由、索引与身份解析实现，固定版本已恢复并核对 | [b-open-io/1sat-stack](https://github.com/b-open-io/1sat-stack) |
| `react-spectrum-main/` | 既有 Adobe 源码快照，本次未核对 | 未登记 |
| `schema-master/` | 既有 BitcoinSchema 快照，本次未核对 | 未登记 |
| `go-sdk/` | 已下载、未检出的参考仓库，本轮迁移不使用 | [bsv-blockchain/go-sdk](https://github.com/bsv-blockchain/go-sdk) |
| `ts-stack/` | TypeScript SDK 固定源码，版本由[迁移工作区](../_task/backend-worktree/bsv-sdk-java-migration/workspace.json)维护 | [bsv-blockchain/ts-stack](https://github.com/bsv-blockchain/ts-stack) |
| `js-junglebus/` | JungleBus Java 25 迁移的原始 SDK 对照源码，固定版本已 clone 并核对 | [gorillapool/js-junglebus](https://github.com/gorillapool/js-junglebus) |

来源锁定清单保存目标仓库、分支、commit、Git tree、文件数和包版本；`verificationScope` 与各条 `localStatus` 表示当前实际核对范围。2026-10-12 已从官方仓库恢复 `1sat-sdk` 和 `1sat-stack` 到登记的 commit，并核对 tree、文件数、包版本、干净工作区和 Git 完整性。两者保留独立 Git 元数据，以 detached HEAD 固定参考版本。

BAP 当前是无 Git 元数据的既有快照，实际包版本与目标版本的差异记录在清单中；其他快照本轮未重新核对，不能称为与清单全部一致。后续更新须先检查本地改动，再同步所需版本并重验清单。现有目录名沿用旧名称，以保持设计引用有效。`xLog-dev/` 当前不存在，不作为可用本地资料。

2026-10-13 按用户要求完整 clone `js-junglebus`，以 detached HEAD 锁定清单登记的提交。已核对官方 remote、commit、tree、37 个受跟踪文件、包版本、干净工作区及 `git fsck --full`；本次 `verificationScope` 只覆盖该仓库，既有仓库的验证时间沿用各条记录。已读取全部四个源码文件、README、依赖锁文件及 LICENSE，迁移方案见[Java 25 实现计划](../_task/backend-worktree/junglebus-java25-migration/doc/实现计划-20261013-110456.md)。该仓库的 `package.json` 标注 MIT，而实际 LICENSE 为 Open BSV；迁移交付须保留实际许可证及原版权声明。

## 查阅入口与已知差异

当前上游代码和文档仍有差异。保留上游原文，以以下源码入口核对调用方式；不能因完成同步就认定所有文档示例可运行。

| 内容 | 当前查阅入口与结论 |
| --- | --- |
| 资产列表与转移 | Yours [实际调用](yours-wallet-main/yours-wallet-main/src/pages/OrdWallet.tsx)与 SDK [Ordinal Actions](1sat-sdk/packages/actions/src/ordinals/index.ts)使用 `listOrdinals`、`sendOrdinals`；[Provider 文档](yours-wallet-main/yours-wallet-main/docs/provider-api.md)仍有 `getOrdinals`、`transferOrdinals` 旧名称。 |
| 转移参数与交易材料 | `sendOrdinals` 的 `transfers` 项使用钱包 basket 的 tracking `id` 和接收地址或公钥。动作内部装载当前输出与 BEEF；不要将 Origin、Inscription ID 或旧文档中的 `WalletOutput` 直接当作此参数。列表默认不保证附带 BEEF。 |
| 身份与签名 | [身份 Actions](1sat-sdk/packages/actions/src/identity/index.ts)、[AIP](1sat-sdk/packages/actions/src/signing/aip.ts)、[Sigma](1sat-sdk/packages/actions/src/signing/sigma.ts)。`resolveBapId` 查询钱包 basket；公共身份解析见 [BapClient](1sat-sdk/packages/client/src/services/BapClient.ts)及[服务端路由](1sat-stack/pkg/bap/routes.go)。Ownword 的全交易签名要求及未闭合能力以[核心认知第 6.4、12 节](../_task/system-design/spec/核心认知.md)为准。 |
| Friend 通信公钥与社交动作 | [getFriendPublicKey](1sat-sdk/packages/actions/src/signing/friendPubKey.ts) 使用 Type-42，输入的 `friendIdentityKey` 是对方压缩公钥，不是 BAP ID；与 BitcoinSchema Friend 示例的派生方式是否兼容仍需验证。[社交 Actions](1sat-sdk/packages/actions/src/social/index.ts) 当前只登记 `createSocialPost`；[BSocial 模板](1sat-sdk/packages/templates/src/bsocial/bsocial.ts) 有 Follow 构造入口，不能据此认定已有完整好友申请与接受流程。 |
| 社交索引 | [Stack BSocial](1sat-stack/pkg/bsocial/topic.go) 允许接收 `friend`、`unfriend` 等 MAP 类型；这是接收范围，不证明双向关系、身份签名或完整撤销语义。[业务路由](1sat-stack/pkg/bsocial/routes.go) 当前注册 Post 搜索，公开关系列表与人数契约仍需实际验证。 |
| 编号与内容解析 | [术语](1sat-ordinals-master/1sat-ordinals-master/readme/terms.md)定义 Inscription Number；[OrdFS 客户端](1sat-sdk/packages/client/src/services/OrdfsClient.ts)与[服务端](1sat-stack/pkg/ordfs/routes.go)中的 `sequence` 是资产转移链内序号，不能当作全局 Inscription Number。metanet4j 的编号补齐责任见核心认知。 |
| 旧公共 API | [public-apis.md](1sat-ordinals-master/1sat-ordinals-master/public-apis.md)已经标注 Historical。旧 GorillaPool 端点只作历史资料，新接入以锁定版本的 SDK、服务端及实际部署为准。 |

清单登记的 Yours 依赖版本与恢复的 SDK 固定版本不同，具体数值见来源锁定清单；Yours 当前快照本轮未重核。后续集成必须选定同一依赖组合验证。资料补齐验证的是源码来源与可用性，本轮没有安装运行依赖、编译钱包、启动服务或调用真实交易。

## 注意

- 目录内含上游配置和部署示例，源码整体忽略，避免将示例或运行态误纳入主仓。
- 清单登记的旧备份目录当前不存在，状态已注明；本轮只补齐两个缺失目录，未替换其他既有快照。
- 更新参考资料不等于升级 Ownword 产品依赖，也不证明线上服务可用。文档结论需要对应源码证据；接口行为仍须按实际版本验证。
