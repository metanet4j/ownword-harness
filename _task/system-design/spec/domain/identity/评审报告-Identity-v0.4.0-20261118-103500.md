# OwnWord v0.4.0 Identity 跨端领域设计 Review

> **评审结论：Changes Requested（暂不批准完整开发基线）**。
>
> 评审性质：**代码与文档静态审查**，不是主网或运行时安全审计；未启动服务、未调用真实 Wallet、未执行测试、未关闭公共索引/Binding 协议门禁。
>
> 审阅目标：[Identity 跨端领域设计](领域设计-Identity-v0.4.0-20261117-175100.md)、[Context Map](../上下文映射-v0.4.0-20261117-175100.md)、[Frontend 指南](../../frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md)、[Backend 指南](../../backend/identity/实现设计-Identity-v0.4.0-20261117-175100.md)、[OpenAPI 草案](../../contracts/openapi/ownword.yaml)、[BDD 草案](../../contracts/acceptance/identity.feature)、[v0.4.0 版本清单](../../versions/v0.4.0.yaml)。
>
> **事实权威**：[核心认知](../../核心认知.md)。优先级：P0 阻断真实主网闭环；P1 阻断领域/契约评审通过；P2 影响后续可维护性或发布完备性。

## 1. 评审范围及代码基线

| 对象 | 仓库 / 读到的版本 | 证据边界 |
| --- | --- | --- |
| 文档 | `metanet4j/ownword-harness` `dev` | v0.4.0 统一设计目标，当前 needs-review |
| 前端 | [`ownword-web`](https://github.com/metanet4j/ownword-web/tree/feature/ownword-v0.2.0) `6f9bccadc356e4a2e07afe3d8af6c3534f70402b` | Next.js/TypeScript 身份页面、`lib/domain`、Wallet 接口 |
| 后端 | [`metanet4j-component`](https://github.com/metanet4j/metanet4j-component/tree/dev) `fbb048eab9ff565ea2f4aff1bd01720b9240d407` | `metanet4j-api-ownword` Java Controller、Sync、IdentityProtocol |
| PRD | [v0.1 Identity](../../prd/v0.1/设计文档v0.1.md)、[v0.3 Artifact](../../prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)、[v0.4 公开主页](../../prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md) | 产品行为和原型，不视为已部署 API |

**总体方向可保留**：跨端共享业务语言、Identity 与 Artifact Binding 独立聚合、Wallet 与链上 Proof 分离、产品版本和工程依赖版本分开、模拟和真实链上证据独立，均符合现有权威规则。以下问题决定何时能够批准为开发基线。

## 2. Findings（按优先级）

### R-01 [P0] 首次主网 Identity 发布的入口存在解析循环依赖

**代码事实**：

- Java 的 [`IdentityApi.identity()` L62–76](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java#L62-L76) 在不存在 `identity_projection` 时，查询公共 BAP 服务但**不会**根据单次服务响应证明“未发布”，统一返回 `kind=unknown` 与 `coverage=unknown`。
- TypeScript 的 [`publish.ts` L364–382](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/publish.ts#L364-L382) 对 `mainnet + unknown` 直接抛出 `PUBLIC_IDENTITY_UNVERIFIED`。
- [`identity-app.tsx` L1165–1198](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/app/identity-app.tsx#L1165-L1198) 在非模拟模式下，仅 `kind=not-published` 显示 Setup 入口。

**影响**：一个新 BAP ID 若尚无后端公开投影，无法获得 `not-published` 的充分证据，正式前端便无法进入首次创建。它是当前代码的**静态流程阻塞**；未运行主网实测，不能扩写为所有环境都必然无法发布。

**要求修正**：将“能否证明公开不存在”与“是否可由钱包授权提交新的初始 BAP 声明”分开建模。明确 `PublicationEligibility`（创建前置证据与风险门槛）、`IdentityResolution`（公共查询事实）和未完成操作恢复。不得简单将 `unknown` 改成 `not-published`；明确重复创建、防双签、Root/Current 路径证明、主网查证失败时的安全退路。

**关闭证据**：先给出首次创建的状态/时序与判定表，再通过新 BAP ID、公共索引无记录、暂时故障、已有已发布身份、广播未知五组集成测试验证；主网真实验收保持另一个门禁。责任方：Identity Domain + Frontend UseCase + Java Indexer。

### R-02 [P1] 共享 `IdentityResolution` 与真实传输结果缺少权威映射

**证据**：[共享领域设计 §6 L93–101](领域设计-Identity-v0.4.0-20261117-175100.md#6-状态与领域结果)仅给出 `published/not-published/unknown`；[前端 `Resolution` L86–105](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts#L86-L105)允许 `published/incomplete/not-published/unknown/stored/empty`；[Java `storedTestIdentity()` L79–105](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java#L79-L105)在 `broadcast-mock` 使用 `stored/incomplete/empty`；[核心认知 §6.1](../../核心认知.md#61-mvp)明确 Profile 不完整需补全。

**影响**：两个端可能把同一个 `kind` 解释成不同的 Identity 生命周期或授权能力；模拟的 `empty` 还可能被误用为公共未发布。

**要求修正**：按 `network/scope` 定义**传输 DTO → 领域 Resolution → 页面 ViewModel** 的完整映射表。至少区分 Public Identity 证明、Profile Completeness 和钱包会话能力三个维度；明确 `stored/incomplete/empty` 是隔离模拟结果还是领域可复用概念。异常与未知不可省略。

**关闭证据**：六种现有 `kind` 的实际 DTO 样例 + TypeScript exhaustiveness 测试 + Java 来源/覆盖测试。责任方：Frontend Identity + Backend Identity。

### R-03 [P1] Identity/Profile 的类型与字段映射尚未落到领域模型

**证据**：[核心认知 §7.2–7.3](../../核心认知.md#72-bapidentity)分别定义 `BAPIdentity.type` 与可变的 `BAPProfile.type`，资料字段称 `description/image`；[共享领域设计 §4 L39–58](领域设计-Identity-v0.4.0-20261117-175100.md#4-战术模型与聚合)的 Identity 聚合结构未列 `type`，也未说明两处 type 的一致性与变更规则；现有 [TypeScript `Profile` L1–7](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts#L1-L7)采用 `bio/imageUrl/type`，Java [`IdentityProtocol.profile()` L24–30](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityProtocol.java#L24-L30)也使用 `bio/imageUrl`。

**影响**：文档不足以告诉开发者 `type` 变更是否修改 Identity 声明，以及领域 `description/image` 与 DTO `bio/imageUrl` 的可逆映射，容易出现写入字段漂移。

**要求修正**：在 Domain 给出字段归属/可变性与 Identity.type、Profile.type 的业务决策；在 Contracts 给出 DTO 到领域字段的显式 Mapper；涉及事实变动时先修正核心认知，不能在实现文档中擅自做决定。

**关闭证据**：字段映射表 + 修改 Profile.type 的 Given/When/Then + Java/TS 对照测试。责任方：Domain + Frontend/Backend Identity。

### R-04 [P1] Key Rotation 的历史签名归属缺少可执行验证模型

**证据**：[共享领域设计 §4/§5/§7](领域设计-Identity-v0.4.0-20261117-175100.md)提出 `IdentityKeyHistory` 和 `IdentityKeyRotatedVerified`；[核心认知 §6.4、§11.17](../../核心认知.md#64-全部链上交易的身份归属)要求历史交易按签名时有效路径验证。当前 Java [`IdentityApi.currentAddress()` L43–48](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java#L43-L48)读取投影的当前地址（模拟流还按本地 `updatedAt` 选记录）；[`IdentityProtocol.verify()` L40–68](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityProtocol.java#L40-L68)接受当前 signer 状态，但未体现一个完整的“交易签名时点→可验证历史路径”解析端口。

**影响**：当前路径不能代替历史授权证据；只按现在的地址或本地更新时间判断，会有旧交易误判和重放顺序问题。此为**实施缺口**，尚未证实真实历史交易必然失败。

**要求修正**：定义 `SigningPathAt(txEvidence)` 和 `RotationHistoryResolver` 的输入、输出、证据顺序、重组处理及 UNKNOWN 策略。链序冲突不可通过本地 `updatedAt` 推断。

**关闭证据**：旧签名、轮换、新签名、乱序索引、历史重放和 reorg 的验签向量。责任方：BAP/Indexer + Java Identity。

### R-05 [P1] OpenAPI 目前无法作为前后端开发的类型权威

**证据**：[OpenAPI `ownword.yaml`](../../contracts/openapi/ownword.yaml)仅列 `GET /identities/{bapId}` 与 `POST /transactions/sync` 两条 API，返回 `Envelope.data` 为 `additionalProperties: true` 的无约束对象，未定义完整的 `IdentityResolution`、`SyncReceipt`、`Coverage`、`Proof` 及 Error Schema；但[Frontend 指南 §5](../../frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md#5-api契约与测试)已把 `GET /transactions/{txid}` 列为恢复必要接口，Java 代码也有该路径 [`IdentityApi` L109–116](https://github.com/metanet4j/metanet4j-component/blob/dev/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java#L109-L116)。

**影响**：无法仅凭 OpenAPI 生成类型安全的前端客户端，也无法通过契约校验捕获状态/字段漂移；误以为该文件是完整、已批准的 v0.4.0 API 会误导后续开发。

**要求修正**：按当前 Java 返回与 TS 类型逐项生成 `oneOf/discriminator` 的结果模型，保留 `scope/source/coverage/proof`；补齐恢复必需接口和 4xx/5xx 错误模型。未确认字段可标 `needs-review`，正式类型发布前用真实 response fixture 验证。

**关闭证据**：OpenAPI 严格校验、Java 契约测试、由固定 fixtures 检验 TS DTO/Mapper；先确保 v0.1/v0.2 API 向后兼容。责任方：Backend API + Frontend Integration。

### R-06 [P1] BDD 草案未覆盖主线和高风险恢复，无法形成开发验收闭环

**证据**：[Identity `.feature`](../../contracts/acceptance/identity.feature)目前仅 4 个设计级场景，[Artifact `.feature`](../../contracts/acceptance/artifact.feature)仅 2 个。尚无主网首次发布、Profile 多笔部分成功、Account Switch、Identity 轮换历史、签名覆盖篡改、广播结果未知及 Indexer 重组的跨端场景和 Step Definition。

**影响**：领域约束已写在文档中，但下一轮改造 Use Case 或 DTO 时，缺少可重复判定“实现与领域语言一致”的证据。

**要求修正**：先用 PRD/核心认知编号建立 `Requirement → Rule → UseCase → API → Frontend Test/Backend Test` 追溯矩阵，优先补 R-01/02/04 对应的 BDD；技术实现单测与合同测试分别承担，不强制两端共用运行器。

**关闭证据**：有明确 Given/When/Then、负向场景、执行环境、负责人及实测/跳过状态；真实主网标注独立验收。责任方：Domain + QA + 两端。

### R-07 [P2] `ResolveIdentityByNumber` 的用例归属与限界上下文图不一致

**证据**：[Identity 领域设计 §3](领域设计-Identity-v0.4.0-20261117-175100.md#3-主要-use-case)把 `ResolveIdentityByNumber` 放在 Identity Use Case；[Context Map](../上下文映射-v0.4.0-20261117-175100.md)将编号/Origin/Current Binding 归 Artifact，把公开 ID 查找归 Explorer；[核心认知 §6.1](../../核心认知.md#61-mvp)也将精确查找归 Explorer。

**影响**：后续开发可能在 Identity 模块内直接访问 Artifact 数据，造成聚合边界穿透。

**要求修正**：让 `Explorer.ResolveByInscriptionNumber` 通过 Artifact 解析编号→Origin→Current Binding，再引用 Identity 公共查询；Identity 只对 `BapId` 提供身份解析。责任方：Domain / Explorer。

### R-08 [P2] 前端 Domain 仍与 SDK、HTTP 和操作日志耦合，需要渐进迁移计划

**证据**：[现有 `lib/domain/publish.ts` L1–25](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/publish.ts#L1-L25)直接引入 BSV SDK、`@1sat/templates`、钱包接口及 `api`；[`lib/domain/types.ts` L1–125](https://github.com/metanet4j/ownword-web/blob/feature/ownword-v0.2.0/lib/domain/types.ts#L1-L125)同时包括 Profile、远程 API、操作日志与校验。文档将逻辑分层列为**目标**，并未宣称源码已经拆分。

**影响**：新模块沿旧结构继续增加时，React/UI、交易 SDK 与领域逻辑可能难以独立替换和单测。

**要求修正**：按风险从小到大抽 `IdentityPolicy` / `IdentityResolutionMapper`（纯 TS）、`PublishIdentityUseCase`（Application）、`WalletPort/IdentityApiPort/JournalPort`（Adapter），每次迁移保持现有回执恢复与测试行为。无需一次性“重构为全新的四层目录”。责任方：Frontend。

### R-09 [P2 / 发布门禁] v0.4.0 Manifest 有意不锁定全部依赖和文档快照

**证据**：[v0.4.0.yaml](../../versions/v0.4.0.yaml)保留 `approvedForRelease=false`、`specSnapshot=null`、`otherBackendDependencies.releaseLock=pending`，且原型为模拟、前端 v0.2.0 仍有实际扩展/主网门禁。

**评估**：这些状态**正确反映目前未发布的事实**，不是文档缺陷。它们意味着 v0.4.0 可作为研发目标，却尚不能创建“已验收发布”的 Tag。

**关闭证据**：用户审批设计版本、主文档不可变 SHA、逐一核实参与发布的后端依赖 SHA、开放门禁的真实证据。责任方：Release Owner + 相关模块负责人。

## 3. 整改顺序与阶段性通过条件

| 顺序 | 要完成的工作 | 通过依据 |
| --- | --- | --- |
| A（必先） | R-01：首次主网 Identity 发布的领域决策/前端入口/后端验证闭环 | 初始发布的正向、已有身份、索引 unknown、广播 unknown 的集成测试 |
| B | R-02 + R-03：结果映射及 Identity/Profile 字段归属 | 完整 DTO↔领域映射表，模拟与主网分别校验 |
| C | R-04：Key Rotation 的历史签名时点验证 | 历史验签与 reorg/乱序向量通过 |
| D | R-05 + R-06：OpenAPI 合同与 BDD 自动验收 | OpenAPI 校验、Java/TS fixtures 一致、负向场景 |
| E | R-07 + R-08：边界调整与分层渐进重构 | 模块依赖检查、现有测试无回归 |
| Release | R-09：锁定版本快照并关闭主网发布门禁 | 完整 Git SHA 和用户审批记录 |

**评审结论**：认可共享领域语言 + 独立前后端实现 + 单产品版本的方向；对实际可开发的 Identity v0.4.0 完整基线提出 Changes Requested。需要先关闭 R-01 的主网初始发布流程，以及 R-02/03/04/05/06 的模型和契约缺口。P2 可以按工程迭代实施，但正式发布仍必须满足 R-09。

## 4. 本轮验证与没有验证的内容

已核对 Identity 的 SSOT、v0.4.0 PRD、共享模型、Context Map、TypeScript `types.ts/publish.ts/identity-state.tsx/identity-app.tsx` 和 Java `IdentityApi.java/TransactionSyncApi.java/IdentityProtocol.java`，以及当前 OpenAPI、BDD 和 Manifest 中的静态事实。代码路径判断来自上述固定 Git SHA，非运行时覆盖报告。

尚未执行 Java/TypeScript 单测和集成测试、OpenAPI 严格 validator、真实钱包扩展、Indexers 真实响应、资金交易或重组实验，也没有检查所有后端依赖仓库的实际部署组合。新提出的 `PublicationEligibility` 与 `SigningPathAt` 是**设计建议的概念名**，不是已经存在的协议或代码。

**状态管理**：本报告可作为正式 Review 反馈，**不代表用户已批准领域设计**；原 Identity 设计和统一版本清单继续保留 `needs-review`，待问题逐项关闭再复核。
