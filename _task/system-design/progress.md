# 当前进展

v0.2.0 内容集成设计已获批准，本地功能与技术验收已完成；用户视觉复核及真实扩展、公共身份历史/checkpoint、主网资金与广播门禁仍保留。实际范围和状态见[前端验收与状态记录](../../知识库/前端/ownword-v0.2.0/README.md)，不因工作区清理将整体版本标记完成。

前端完整仓库位于根目录 `frontend/ownword-web/`，保留 v0.1/v0.2 及 master 分支，当前检出 v0.2；后端仓库位于 `backend/`。旧前后端任务目录已清理，长期文档集中到[知识库](../../知识库/README.md)，私有钱包与服务配置在 Git 忽略的 `.local-state/frontend/` 本地保留。

## 新版设计技能承接原型（needs-review）

`claude-design` 已设为原型设计与迭代的默认主技能。现有 HTML、JSX 工程直接沿用源码、Spectrum S2 绑定及构建预览入口；画布编辑器按需启用。技能入口、原型迭代技能和本目录规则已同步，分工与载体要求统一见[设计总指南](../../standard/OwnWord设计与设计系统.md)；本轮未改动原型页面、依赖或产品事实。

技能登记、YAML 元数据、49 处本地文件引用和定向差异检查通过，锁定文件已记录本地适配后的内容校验值。通用 harness 扫描基线与当前均为 36/100，其英文关键词和默认字段未覆盖本项目中文规则与任务结构，本轮按实际路由与引用检查交付，未扩大为 harness 改造。规则修改待用户复核。

## v0.3.0 顶部导航去箭头同步（needs-review）

按用户要求，把 v0.3.0 设计文档第 4.1 节的顶部导航规则改为“当前模块名称 + 工作区图标，不使用下拉箭头，当前模块在菜单中明确标出，辅助操作以分隔线分组”。同时在原型 V0.4.0-r4 中把顶栏控件高度改为 `--ownword-header-control`：桌面 36px，`pointer: coarse` 时 44px，使文档中“触控范围至少 44px”成立。原型构建与检查通过，`verify-header-menu.mjs` 19 项通过；文档与原型的对应关系待用户复核后标记 done。

唯一下一步：复核新版默认承接现有原型的规则，后续设计迭代直接在目标工程推进。既有原型视觉复核及真实扩展、公共历史和主网验收仍按各自事项跟踪；知识库中的旧启动命令仅作为实施记录，重新启动须按当前目录准备环境。

## Identity 后端领域设计（needs-review）

根据现有核心认知与 Identity v0.1 / Artifact v0.3 设计，在 `spec/backend/领域设计-Identity-v0.1.0-20261117-165000.md` 新增 DDD 后端方案，包含限界上下文、Identity 与 Artifact Binding 聚合边界、身份签名及密钥轮换、交易同步、状态、可重建投影、端口与 BDD 验收。原有产品事实不改写。

只读校验：文件已在 `dev` 可读取；14 个章节、3 个 Mermaid 图、来源引用、目录存在性已核对。未执行真实服务、密码学向量或主网测试；R01–R06 仍待验证，用户复核前保持 `needs-review`。提交：`3244b88a`、`a4aa2b88`；任务记录提交 `f05de392`。

此事项下一步：用户审阅领域模型与待确认契约后，再决定是否开始后端实现。此前导航视觉复核事项状态未改变。

## v0.4.0 统一开发设计基线（needs-review）

按用户认可的治理方案，在 `spec/README.md` 建立统一入口，`spec/versions/v0.4.0.yaml` 记录目标版本与独立原型/前端/后端 Git SHA 及验收状态；核心认知和历史 PRD 保持权威与原位。共享 Domain 增加 Context Map、Identity 领域设计及 Artifact/Content/Relationship 缺口入口；Contracts 增加仅覆盖已核实 Java 两项接口的 OpenAPI 草案和 6 个 BDD 设计级场景；Frontend/Backend 分别增加基于现有 TypeScript/Java 的 Identity 实现指南，并创建 ADR-001。原 v0.1 后端设计保留历史，生产源码、原型和 npm/Maven 版本均未改动。

**验证**：GitHub `dev` 上新增路径及相对链接核对通过（119 个相对链接、0 个未解析），YAML 中 18 个文档/证据路径存在，OpenAPI 内部 Schema 引用可解析，6 个 Gherkin 场景具备 Given/When/Then 结构。上述为文档静态检查，**没有**执行 Java/TypeScript 测试、Swagger/OpenAPI 严格 Schema 校验、Wallet 扩展或主网交易。实际 API DTO、Signature/Binding/Indexer 与公共历史仍有未关闭项。

状态 `needs-review`；用户尚未批准 v0.4.0 的正式发布基线，因此 `specSnapshot: null`，未创建 Release Tag。证据和待决条件见 `feature_list.json` 的 `system-design-unified-version-v040`。下一步：用户评审统一版本清单、Identity 跨端职责及待确认的 Contract，随后确定是否批准基线。


## Identity 跨端 DDD 技术 Review（Changes Requested）

已静态核对 `核心认知.md`、v0.4.0 Identity 跨端模型、Context Map、Frontend/Backend 实现指南、OpenAPI/BDD、统一版本清单，并对照 `metanet4j/ownword-web@6f9bccad` 与 `metanet4j/metanet4j-component@fbb048ea` 的真实 TypeScript/Java 代码。结果：[评审报告](spec/domain/identity/评审报告-Identity-v0.4.0-20261118-103500.md)。

发现 **P0×1、P1×5、P2×3**：P0 是首次主网身份发布时 `GET identity → unknown`、前端拒绝创建的流程阻塞；P1 涉及查询结果映射、Identity/Profile 属性归属、Rotation 历史签名、类型化 OpenAPI、BDD 验收覆盖；P2 涉及编号查找的上下文归属、TypeScript 分层、发布 SHA 锁定门禁。报告每项附代码证据、影响、责任方和关闭条件。评审方向认可，共享设计及发布基线**不批准**，仍保留 `needs-review`。

证据：报告 39 个相对/外部引用均有明确来源，内部路径 0 个丢失；未执行运行时测试、Wallet 扩展、主网或重组实验。新增 `review-identity-cross-end-v040` 状态为 `needs-review`，未修改真实业务代码/原型、原有 PRD 和身份领域规则。先关闭 R-01，再处理 R-02 至 R-06，最后复核 R-07 至 R-09。


## Identity DDD Review 设计整改（needs-review）

按用户要求先修订设计文档（不修改业务代码），根据上轮评审 R-01~R-08 在现有统一 v0.4.0 目标下完成：

- 共享 [Identity 领域设计](spec/domain/identity/领域设计-Identity-v0.4.0-20261117-175100.md)：拆分公开查询、Profile 完整度、Wallet Control 和 Initialization Eligibility；定义 ALLOW/BLOCK/NEED_EVIDENCE 初次身份发布资格、恢复时序、Identity/Profile 关键属性与历史 Key Rotation 的 signing-time 验证端口；编号解析归 Explorer。
- [Frontend](spec/frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md) 和 [Backend](spec/backend/identity/实现设计-Identity-v0.4.0-20261117-175100.md)：补实际 TS/Java 类型映射、交易幂等/恢复、Root 历史覆盖及逐步应用层迁移。
- [OpenAPI](spec/contracts/openapi/ownword.yaml)：现有 5 条 Java 路由的候选类型化契约，包含 6 种 Identity DTO、Coverage、Error、Transaction 恢复；[Identity BDD](spec/contracts/acceptance/identity.feature)：18 个场景、8 行查询状态样例。
- [v0.4.0 Manifest](spec/versions/v0.4.0.yaml)：记录设计整改状态和仍待实证的技术门禁；`approvedForRelease=false`、`specSnapshot=null` 保持不变。

**已静态检查**：本轮相关 8 份 Markdown 的 77 个相对链接均有效，无未配对代码围栏；OpenAPI 5 个已核实路径、22 个 Schema 和 61 处引用没有悬空；18 个 Gherkin 场景具备 Given/When/Then。**未完成**严格 YAML/OpenAPI 验证器、BDD Step Definition、TypeScript/Java 运行时测试、真实扩展和主网查询/广播。

**关键残余 P0**：有 Root Control 仍不能在公共 BAP 历史覆盖未知时安全断言“可以初始化”；已明确 NEED_EVIDENCE 保护与 PENDING 原交易恢复，但需要 Indexer 的充分历史证据或经过产品/安全批准的链上初始化防冲突协议才能解除广播阻塞。R-03 Identity/Profile type 策略、R-04 历史验签向量和 R-05/06 契约测试仍待实施。当前事项 `remediate-identity-design-review-v040` 为 `needs-review`，未批准开发/正式发布基线。
