# 当前进展

当前事项为 `identity-core-convergence-v040`，状态 needs-review。Identity 的稳定领域事实已收敛到核心认知，下游文档改为引用和实现映射；任务范围和证据见[feature_list.json](feature_list.json)。

## 当前产出

- [核心认知](spec/核心认知.md)：集中 Identity 术语、功能编号、实体/属性、关系、状态图、事件和规则索引；类型一致性及历史核验缺口统一列入待确认。
- [Identity 领域设计](spec/domain/identity/领域设计-Identity-v0.4.0-20261117-175100.md)：引用核心定义，保留用例协作、责任、端口、执行恢复序列和验收映射。
- [前端实现设计](spec/frontend/identity/实现设计-Identity-v0.4.0-20261117-175100.md)承接原公共查询 DTO 映射；[后端实现设计](spec/backend/identity/实现设计-Identity-v0.4.0-20261117-175100.md)按核心属性编号引用 Java 字段边界。
- [文档总入口](spec/README.md)、[Domain 入口](spec/domain/README.md)、[Contracts](spec/contracts/README.md)与 [ADR-001](spec/decisions/ADR-001-统一产品版本与文档职责-20261117-175100.md)统一文档职责。支撑域仍从[既有入口](spec/domain/supporting/README.md)进入，状态保持 needs-review。

## 验证范围

本次相对路径、Markdown 标题锚点、围栏、JSON、Manifest/OpenAPI 严格 YAML 和 git diff --check 均通过。核心编号唯一性检查覆盖 9 个模型、5 项功能、8 个 Identity 属性、6 个 Profile 属性、8 类事件、12 条规则索引及 12 项关系；三个 Identity 状态图已做文本结构检查，未渲染。

迁移比较确认原八类事件和六行公共查询映射保留；BDD 场景内容未变，仅更新 Identity 来源注释，仍为 Identity 18、支撑域 16、Artifact 2 个场景且未执行。未改业务代码、OpenAPI、Manifest、依赖或原型，未新增网络请求、真实扩展、主网广播或重组实验。

## 实施限制与下一步

本次是领域事实归位，未关闭类型一致性、公共覆盖和历史验签待确认项。真实钱包、原执行恢复、主链/reorg、Ordinal 历史、全交易签名及 Binding 门禁仍按[核心认知待确认](spec/核心认知.md#12-待确认)和 [Manifest](spec/versions/v0.4.0.yaml)推进；前端源码缺失与旧 SHA 待恢复核实的限制保留。

其他原型、技能及 v0.2.0 验收状态保持 feature_list.json 与[既有知识库](../../知识库/前端/ownword-v0.2.0/README.md)中的记录。

唯一下一步：人工复核核心认知与下游映射；通过后按支撑域 A→B→C→D 补 fixtures、关闭对应协议门禁并实施真实集成。人工复核前不记 done，不创建发布 Tag。
