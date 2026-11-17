# Frontend / Identity 实现设计（OwnWord v0.4.0 目标）

> **状态：needs-review。** 跨端业务语义参考[Identity 领域设计](../../domain/identity/README.md)，事实仍以[核心认知](../../核心认知.md)为权威。本文件是对**现有** Next.js + TypeScript v0.2.0 工程的演进指南，并不声明 v0.4.0 Identity 已完成生产验收。

## 1. 源码基线

仓库：[metanet4j/ownword-web](https://github.com/metanet4j/ownword-web/tree/feature/ownword-v0.2.0)，核实分支 `feature/ownword-v0.2.0`，HEAD `6f9bccadc356e4a2e07afe3d8af6c3534f70402b`（v0.4.0 编写时的只读观察）。

| 代码位置 | 当前职责 | 目标与约束 |
| --- | --- | --- |
| `app/identity-app.tsx`, `app/identity-state.tsx` | Identity UI 与状态 | Presentation 只控制渲染、事件和界面反馈，不判断公共身份事实 |
| `lib/domain/types.ts` | `Profile / Resolution / Operation` 与基础校验 | 分离传输 DTO、业务结果、客户端操作日志，保留现有行为和字段兼容 |
| `lib/domain/publish.ts` | 身份交易准备/广播/同步编排 | 将可测 Use Case 从 React 抽离；原交易不得在恢复时重构 |
| `lib/domain/journal.ts` | 钱包操作日志与恢复 | IndexedDB 持久化、旧身份归属、幂等与账户切换门禁 |
| `lib/wallet/contracts.ts`, `lib/wallet/adapters/` | 钱包能力接口与具体实现 | 保持现有隔离层，业务不直接导入特定钱包 SDK |
| `lib/content/publish.ts` | Content 发布与修订 | 与 Identity 复用可验证交易基础步骤，不重复定义作者身份归属 |

已存在的目录不必为匹配文档结构一次性搬迁。优先通过文件/模块边界演进，保持通过的 v0.1/v0.2 功能与恢复测试。

## 2. 目标分层（职责逻辑层，不强制物理文件树）

- **Domain**：`BapId`、身份查询结果、可纯函数表达的前置条件、业务行为及状态转移；不调用 HTTP、Wallet 和 React Hook。
- **Application**：`ResolveMyIdentity`、`PublishIdentity`、`UpdateBapProfile`、`RotateIdentityKey`；按冻结内容、权限、持久化日志和交易结果协调外部端口。
- **Infrastructure**：`WalletProvider`、`IdentityApiClient`、`OperationJournal` 的具体适配；不能在 Adapter 内发明新的业务语义。
- **Presentation**：页面、S2 组件、ViewModel、Hook；负责 loading、disabled、dialog 和错误反馈，业务是否允许操作来自用例结果。

示意依赖：`React UI → Application Use Case → Domain + Ports ← Wallet/HTTP/Storage Adapters`。

## 3. 应用用例的实施契约

| 用例 | 前端职责 | 禁止事项 |
| --- | --- | --- |
| `ResolveMyIdentity` | 读取当前钱包 BapId，调用公共 Identity API；把 `published / verified-not-published / unknown` 映射到页面 | SDK `resolveBapId` / basket 没记录即解释为主网未发布 |
| `PublishIdentity` | Review 冻结 BAP ID、资料和账户；取得授权、准备交易并持久化；广播同一原交易；保存回执后同步并再查询 | 未保存回执先广播、结果未知自动重签或改用另一 TxID |
| `UpdateBapProfile` | 保持 Draft 与已发布 Profile 分离；逐笔处理 ID/头像/ALIAS 实际交易及部分成功 | 本地修改即声称公共资料生效 |
| `RotateIdentityKey` | 冻结当前 BAP ID、钱包上下文和 Review；执行钱包签名并观察结果 | 仅凭地址切换就宣布所有旧交易失效 |
| `ResolveIdentityByNumber` | 通过 Artifact 查询链上的编号和 Current Binding，再进入关联 BAP ID | 直接将 owner/creator 或数字 ID 当 BAP 身份 |

## 4. 状态机边界

- **领域查询**：是否已公开、覆盖足够与否，由后端/公共索引证据决定；模拟 `stored/empty` 只在隔离 scope 有意义。
- **客户端操作**：`reviewing → awaiting-signature → prepared → broadcasting → submitted / broadcast-unknown / cancelled / failed`；这是实现参考，不重定义核心认知产品状态。
- **链上观察**：`networkAccepted`、`signatureStatus`、确认数、主网可查询性彼此独立。HTTP 200/201/202 不证明所有维度已完成。
- **会话失效**：Account Switch / Disconnect 提升 session epoch；丢弃迟到回调，旧会话未提交授权失效，已提交交易仍用原 BAP ID/TxID 查询。
- **数据持久化**：广播前保存本地已签名原交易与恢复日志；读写失败显式反馈，不把未知结果降级为失败再自动重试。

## 5. API、契约与测试

现有真实调用保持 `POST /api/v1/transactions/sync` 四字段契约、`GET /api/v1/identities/{bapId}` 公共身份、`GET /api/v1/transactions/{txid}` 交易核查。机器可读的草案见[OpenAPI](../../contracts/openapi/ownword.yaml)；新增 DTO 前需与 Java 真实返回再次对照。

按[共享 Identity 验收](../../contracts/acceptance/identity.feature)和[原 v0.1/v0.2 BDD](../../prd/v0.1/设计文档v0.1.md)补充适用测试：

- 不同 `Resolution` 状态分流，`unknown` 保留重试而非 Setup；
- Profile Draft 取消后保留原稿，成功后从后端公共投影回读；
- 账户切换、刷新、断网、丢广播回执、同一 TxID 重试；
- 原交易签名/关键业务内容被篡改，阻止提交；
- 模拟 Wallet 真实 SDK 核心的覆盖不等于真实浏览器扩展授权或主网验收。

## 6. 与原型的关系

[原型 v0.4.0](https://github.com/metanet4j/ownword-design-prototype/tree/dev)在确定性模拟下表达 Identity、Content、Artifact 和主页交互。视觉与交互遵循 Spectrum S2，但其 `model.js`、fixture 与模拟成功不是生产领域事实来源。已实现界面只提取可观察行为、状态与 BDD，用实际 Wallet、HTTP 和证据替换模拟。

## 7. 实施顺序与待验证

1. 以现有 `lib/domain/types.ts` 和 Java 响应核对 `Resolution` 语义；保留兼容已有测试。
2. 把 `ResolveMyIdentity`、`PublishIdentity` 的端口和用例边界从组件中明确分离；保持原始交易与恢复日志行为。
3. 将 DTO 映射与 API 客户端隔离；先运行现有 unit/typecheck/lint/build，再做适用钱包/后端集成测试。
4. 对 Rotation、主网公开历史、Artifact Binding 接口逐一补真实协议验证；未验证保留门禁。

**待关闭**：真实 Yours 扩展的浏览器授权、主网资金与广播、公共 BAP 历史覆盖，以及相关 Indexer API；不能把原型和隔离模拟验收记为生产完成。

## 8. 证据

- [现有 Identity 真实集成设计](../设计文档v0.1.0-真实集成-20261013-183000.md)
- [Content 真实集成设计](../设计文档v0.2.0-内容真实集成-20261014-215514.md)
- [v0.2.0 验收与未关闭门禁](../../../../../知识库/前端/ownword-v0.2.0/README.md)
- [统一 v0.4.0 版本清单](../../versions/v0.4.0.yaml)
