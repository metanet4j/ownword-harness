# 当前交接

当前事项 `domain-subdomain-context-v040` 已交付，状态 needs-review，无其他 in-progress 项。本次把子域类型与限界上下文归入核心认知，并新增领域设计写作技能；范围和证据见[feature_list.json](feature_list.json)及[progress.md](progress.md)。

从[核心认知 §5.1.1、§5.1.2](spec/核心认知.md)进入。子域类型用 `SD-01~12` 引用，限界上下文承载映射以 §5.1.2 表为准；[domain-design 技能](../../.agents/skills/domain-design/SKILL.md)按目的、结构、功能、关系、属性、状态、边界七维组织领域设计文档，[七维模版](../../.agents/skills/domain-design/references/domain-design-template.md)提供可复制骨架。

已通过：核心认知 8 个上下文名与上下文映射一致、SD 编号唯一、§5 结构完整、既有 `§5.4` 与 `#5-结构` 锚点有效；技能三文件围栏成对、围栏外断链 0、骨架路径在落地目录可解析；`feature_list.json` 可解析。未执行真实钱包、主网或 Java/TS 运行时验证，未改业务代码、契约与原型。

两点需注意：其一，domain-design 技能当前只被 [Domain 入口](spec/domain/README.md)引用，未登记进根 AGENTS.md 的场景加载表，与 core-principle 的既有惯例一致；其二，试写 Artifact 草稿揭示核心认知本身缺少 Artifact/Content/Relationship 的实体编号与功能编号，重写这些上下文时需先登记编号缺口，不自行发明。

唯一下一步：用户复核子域分类判定与限界上下文承载映射；确认后按七维重写 Artifact 或 Content 领域设计。人工复核前维持 needs-review，`approvedForRelease=false`、`specSnapshot=null` 保持原值。
