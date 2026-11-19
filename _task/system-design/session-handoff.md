# 当前交接

当前事项 `domain-subdomain-context-v040` 已交付，状态 needs-review，无其他 in-progress 项。本次把子域类型与限界上下文归入核心认知，并按执行端重划上下文；范围和证据见[feature_list.json](feature_list.json)及[progress.md](progress.md)。

从[核心认知 §5.1.1、§5.1.2](spec/核心认知.md)进入。子域类型用 `SD-01~12` 引用；限界上下文按执行端划分——前端 Frontend Wallet / Identity / Content / Artifact / Relationship / Reading，后端 Backend Identity / Content / Artifact / Relationship / Transaction / Chain Query，加 Cross-end Reader 共 13 个。同一子域在两端是两个上下文、两套模型、两个权威来源，不合并成一份领域设计。

[ADR-002](spec/decisions/ADR-002-交易执行归属钱包-20261119-140000.md) 已记录交易执行统一由 Yours Wallet 完成。核心认知 §5.4 随之修订为「metanet4j 只解析和验证交易，不构造待签交易」；§5.2 的 `WalletProvider` 明确为唯一交易执行入口。

已通过：§5 结构完整，13 个上下文行与 12 个接口行均标注执行端，旧上下文名全 spec 目录清零，六个文件相对链接断链为 0，`feature_list.json` 可解析。未执行真实钱包、主网或前端构建。

两点需注意：其一，前端仍有 16 处直接 import `@bsv/sdk`，其中六处是交易构造（`lib/domain/protocol.ts`、`lib/domain/publish.ts`、`lib/content/protocol.ts`、`lib/wallet/adapters/cwi.ts`），尚未按 ADR-002 改造；其二，钱包 API 是否支持自定义 MAP 未验证，若不支持则 Revision 语义无法只在钱包侧完成，ADR-002 需重新评估。

唯一下一步：验证 Yours Wallet API 的自定义 MAP 能力，再按 ADR-002 改造前端交易构造。人工复核前维持 needs-review，`approvedForRelease=false`、`specSnapshot=null` 保持原值。
