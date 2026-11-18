# 当前进展

当前事项为 `supporting-domains-v040`，状态 needs-review。用户要求核实支撑域版本划分并整理结构，本次已按既有 ADR-001 完成文档分层；任务范围和证据见[feature_list.json](feature_list.json)。

## 当前产出

- [支撑域稳定入口](spec/domain/supporting/README.md)：统一导航领域、上游依据和两端实现。
- [领域设计](spec/domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md)：保留能力、模型、端口、状态、恢复和验收。
- [上游接入依据](spec/contracts/upstream/接入依据-Yours与1sat-20261118-164032.md)：集中固定版本源码证据、HTTP 路径、鉴权/密钥与已完成的只读验证。
- [钱包实现设计](spec/frontend/supporting/实现设计-钱包与交易执行-v0.4.0-20261118-164032.md)与[Java 实现设计](spec/backend/supporting/实现设计-链与Ordinal查询-v0.4.0-20261118-164032.md)：承接原调用链、材料转换、示例与改造点。
- [统一版本规则](spec/versions/README.md)和 [Manifest](spec/versions/v0.4.0.yaml)：补充版本含义及四份文档路径；发布门禁保持开放。

## 验证范围

本次相对路径、Markdown 标题锚点、围栏、JSON、Manifest/OpenAPI 严格 YAML 和 git diff --check 均通过。迁移核对保留了全部 Java/TypeScript/PowerShell 示例、状态图、HTTP 路径表、SUP-01~10 和已核查包哈希；既有契约和 BDD 未修改。

本次未新增网络请求、编译运行示例或修改 Java/TypeScript 业务代码。先前包取证与匿名 GET 证据已迁移至上游接入依据，不能算作本次重新验证。设计和示例不构成真实扩展、主网广播、SSE 或重组验收。

## 实施限制与下一步

生产依赖组合、高层 Action 丢回执关联、跨会话恢复、公共身份投影、历史验签、主链/reorg、Ordinal 历史和 Artifact 协议门禁仍待实际集成；详细依据由分层文档及 Manifest 维护。前端旧 SHA 仅作记录，本地当前无 frontend/ownword-web 源码目录，实施前恢复核对。

其他原型、技能及 v0.2.0 验收状态保持 feature_list.json 与[既有知识库](../../知识库/前端/ownword-v0.2.0/README.md)中的记录。

唯一下一步：用户复核分层入口后，按支撑域 A→B→C→D 顺序固定生产组合、补 fixtures 并实施真实集成。人工复核前不记 done，不创建发布 Tag。
