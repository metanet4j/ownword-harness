# 当前交接

当前事项 `identity-core-convergence-v040` 已交付，状态 needs-review，无 in-progress 项。本次仅收敛 Identity 文档事实；范围和证据见[feature_list.json](feature_list.json)及[progress.md](progress.md)。

从[核心认知](spec/核心认知.md)进入，Identity 的实体/属性、关系、状态、事件及约束以此为唯一权威。[Identity 领域设计](spec/domain/identity/README.md)保留用例、责任与端口；DTO 转换归 Frontend/Backend，接口形状归 Contracts。文档职责已同步总入口及 ADR-001。

已通过文档路径/锚点、围栏、编号唯一性、JSON、严格 YAML 和差异检查；原八类事件、六行公共查询转换及 36 个 BDD 场景的内容保留。状态图仅检查文本结构，BDD 未执行；未改业务代码、API、依赖或原型，也未重新验证钱包/主网。

[支撑域分层入口](spec/domain/supporting/README.md)、[上游依据](spec/contracts/upstream/接入依据-Yours与1sat-20261118-164032.md)和[统一版本基线](spec/versions/v0.4.0.yaml)继续有效，相关事项仍 needs-review。类型策略和历史核验待确认统一由核心认知 §12.7/§12.8 维护，其他真实集成与协议门禁未关闭；前端源码与旧 SHA 仍待恢复核实。其他原型与技能待审事项保持原状态；不读取 Archive 或 spec/draft。

唯一下一步：人工复核核心认知与下游映射；通过后按统一 v0.4.0 的 A→B→C→D 补 fixtures、关闭对应门禁并实施集成。批准发布前维持 approvedForRelease=false、specSnapshot=null。
