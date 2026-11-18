# Frontend / Identity 实现设计（OwnWord v0.4.0 目标）

> 状态：needs-review。业务语义遵循[核心认知](../../核心认知.md)、[Identity 领域](../../domain/identity/README.md)和[支撑域](../../domain/supporting/README.md)。本文为实施指南，未修改前端代码或验收真实扩展。

## 1. 实现基线

既有前端登记为 `metanet4j/ownword-web` 的 `feature/ownword-v0.2.0`，观察 SHA `6f9bccadc356e4a2e07afe3d8af6c3534f70402b`，来源见[v0.2.0 验收记录](../../../../../知识库/前端/ownword-v0.2.0/README.md)。当前工作区没有该前端源码目录，本轮不把旧观察当作重新核实的 HEAD；实施前恢复并核对实际仓库。

| 既有代码位置 | 演进职责 |
| --- | --- |
| `app/identity-app.tsx / identity-state.tsx` | UI、加载态、业务 Review 和恢复入口 |
| `lib/domain/types.ts` | 兼容 DTO、Profile 映射与独立的查询结果 |
| `lib/domain/publish.ts` | 身份业务用例，消费交易支撑端口 |
| `lib/domain/journal.ts` | 调用前业务意图、执行引用、原交易与恢复记录 |
| `lib/wallet/contracts.ts / adapters/` | Yours 会话、本人身份 Actions、交易能力及错误适配 |
| `lib/content/publish.ts` | Content 业务编排，复用交易支撑；保留自己的载荷与验收 |

沿现有模块逐步接入，不为匹配领域名称搬迁目录。依赖方向为 `UI → Application → Domain/Ports ← Wallet、HTTP、Storage Adapters`。

## 2. 钱包身份适配

`WalletIdentityPort` 封装本人 BapId、钱包发布记录、Profile、发布/更新/轮换能力。会话、解锁、站点权限和逐笔授权由钱包管理，OwnWord 保存所需会话引用，不复制钱包权限系统或密钥历史写模型。

| 情况 | 前端分流 |
| --- | --- |
| 钱包身份明确可新建、公共查询 unknown，无已知冲突和未决操作 | 可 Review 并请求钱包已有 Action；公共身份仍显示待核实 |
| 钱包已有身份、Profile 不完整 | 更新资料，避免再次初始化 |
| 钱包状态/权限未知或账户不匹配 | 保留草稿，重读钱包/重新授权 |
| 公共已核实身份与钱包记录冲突 | 先匹配和恢复钱包跟踪，避免重复 ID |
| 原 Action/TxID 待恢复 | 进入原操作，不新建相同业务交易 |

删除以公共 `unknown` 单独拦截钱包首次发布的耦合；不新增 OwnWord 的 Root 证明型初始化资格接口。钱包 basket 无记录也不能映射为公共 NOT_PUBLISHED。

### 2.1 资料映射

| 来源字段 | 领域字段 | 处理 |
| --- | --- | --- |
| Java DTO `name / bio / imageUrl / type` | `name / description / image / type` | 显式映射；按核心认知校验 |
| Wallet Schema.org `name / description / image / @type` | 同上 | 与 Java DTO 使用不同 Adapter；不能把 bio 原样传给钱包 |
| 公共 Profile 缺少可信时点 | `updatedAt` 未知 | 不用浏览器时间补成链上更新时点 |

Yours 当前 `saveProfile` 固定 `@type: Person`；组织资料和 Identity.type / Profile.type 一致性待产品与钱包适配实证，不据此扩写钱包已支持范围。

### 2.2 公共查询映射

`mainnet/published` 仅在 Proof/来源有效时成为 PUBLISHED；`not-published` 需要充分历史覆盖，否则 UNKNOWN；`unknown`、失败和坏响应保持 UNKNOWN。`incomplete` 需结合初始声明证据判发布状态，Profile 完整度另判。模拟 `stored/incomplete/empty` 只在隔离 scope 使用。完整映射见[Identity §6](../../domain/identity/领域设计-Identity-v0.4.0-20261117-175100.md#6-状态钱包管理与公共查询)。

## 3. 交易执行与恢复

前端通过 `WalletExecutionPort` 选择已核实的 Action 路径或两阶段路径；具体调用顺序和可取得的材料以[支撑域 §4](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md#4-签名与交易执行)的版本取证为准。

1. Review 冻结操作 BapId、scope、账户、业务字段、目标及所选执行路径。
2. 调用前保存 operationId、业务意图、flowId/步骤及适配器可用的恢复关联；再次检查会话。
3. 委托钱包执行，立即保存实际返回的 reference、TxID、交易材料及错误。两阶段路径在继续提交前保存其真实 Prepared 材料。
4. 高层调用中断或回执丢失时，按可取得的原钱包记录/TxID 恢复；禁止自动再调用创建 Action。当前身份 Action 不返回 actionId/reference，也未接收业务 operationId；Toolbox 会话外 pending reference 恢复未实现。需验证持久查询关联或补适配，缺口保持 UNKNOWN。
5. 原交易可取得且满足同步条件时，按现有四字段契约同步；独立回读交易状态与公共 Identity/Profile。

优先从 Action 返回的 `tx` 用 `Transaction.fromAtomicBEEF` 提取目标交易，再 `toHex()` 得 rawTx，并重算 TxID；仅有 TxID 时按[支撑域 §4.4](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md#44-提交后取得最终-rawtx)通过原交易查询补齐，不把整个 BEEF 直接当 rawTx hex。无可恢复材料时不能制造成功回执，也不能推断“从未广播”。

多笔流程每笔使用独立 operationId，共享本地 flowId。当前 Sync 请求恰有四字段，不能直接添加 flowId。ID + ALIAS 若由钱包同笔组合则记一笔；头像和后续资料等按实际交易分别恢复。后续取消保留先前提交结果。

账户/网络切换提升 session epoch，作废未提交 Review；迟到的原执行结果仍写入原账户/scope 的日志，不能丢弃恢复证据或改归属新身份。UI 不因 HTTP 成功、已有 TxID 或已同步就显示全部业务成功。

## 4. 链与 Ordinal 读取

交易详情消费 `TransactionQueryPort` 的来源、原状态、块锚、Proof 与主链结论；接收、传播、观察、接受、入块和业务可读分别显示。断流、超时和 reorg 保留原证据并重新查询原 TxID。

资产界面区分钱包持有列表与公共查询。Wallet tracking ID 用于钱包资产动作；outpoint 用于输出/花费；Origin 用于资产追踪。Ordinal 历史 partial 时展示缺口/继续读取，不宣称最新持有人已确认。sequence、score 和 blockIdx 都不填充全局编号。

## 5. 实施与验证

先固定 Yours 实际依赖和身份/执行接口，核实授权、交易材料及恢复引用；再接入 Mapper、交易日志和公共回读。复用现有 API，不为逻辑端口假设新的 HTTP 路由。签名历史、普通 Transfer 身份签名、编号和 Binding 缺口按支撑域门禁处理。

对应设计验收见[Identity BDD](../../contracts/acceptance/identity.feature)和[支撑域 BDD](../../contracts/acceptance/supporting.feature)。实施时覆盖：钱包新建与已存在、公共 unknown、明确冲突、授权拒绝、会话切换、丢回执恢复、同 TxID 同步、BEEF 解码及多笔部分完成。再运行所改前端的适用类型/构建检查和真实扩展集成；模拟结果与主网结果分别记录。

版本与发布状态见[Manifest](../../versions/v0.4.0.yaml)。原型的确定性模拟不提供钱包或主网能力证据。
