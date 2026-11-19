# 共享领域设计（Domain）

本目录是前后端共用的用例与领域协作入口。**术语、实体/属性、关系、业务状态、事件和不变量以[核心认知](../核心认知.md)为唯一权威；领域文件引用定义，负责用例编排、上下文责任、端口与验收映射。**

## 设计入口

| 上下文 | 当前领域入口 | 状态 |
| --- | --- | --- |
| 全局 Context Map | [上下文映射](上下文映射-v0.4.0-20261117-175100.md) | 设计提案，待评审 |
| Identity | [Identity 领域设计](identity/README.md) | 已整理跨端草案，待评审 |
| 支撑域 | [钱包、交易、链与 Ordinal 查询](supporting/README.md) | 基于本地源码划分职责与实施缺口，待评审 |
| Artifact | [领域入口](artifact/README.md) | 产品与原型已定义；完整链上 Binding 契约待验证 |
| Content | [领域入口](content/README.md) | 已有 v0.2.0 真实集成与 Revision 契约，待抽取独立领域设计 |
| Relationship | [领域入口](relationship/README.md) | v0.4.0 原型范围，生产协议待验证 |

## 编写规范

- 领域设计按七维组织：目的、结构、功能、关系、属性、状态、边界。结构、各维判据与交付检查按 [domain-design 技能](../../../../.agents/skills/domain-design/SKILL.md)；可复制骨架见[七维模版](../../../../.agents/skills/domain-design/references/domain-design-template.md)。
- 统一使用核心认知中的 `BapIdentity / BapProfile / BapId / BapNFT / IdentityNFTBinding` 等术语。
- 稳定的实体/值对象、聚合归属、字段约束、关系基数、业务状态机、事件可信度和异常边界先定义于核心认知。Domain 按编号/章节引用，写用例如何调用端口、分配责任及映射验收，不维护第二份定义表。
- DTO 字段/状态转换和代码调用归 Frontend/Backend，实现接口归 Contracts；Domain 不写 React Hook、Spring Controller 或 Mongo 集合细节。
- 领域设计不自动成为生产验证；协议未查实标注「待验证」，附负责人和关闭证据。
- 新需求影响全局事实时先评审[核心认知](../核心认知.md)，影响契约时同步[Contracts](../contracts/README.md)和实现设计。
- 对每个领域保持 `README.md` 稳定入口；新增独立设计文件按仓库规则带时间戳，批准前保留 `needs-review`。
