# 共享领域设计（Domain）

本目录是前后端共用的用例与领域协作入口。**术语、实体/属性、关系、业务状态、事件和不变量以[核心认知](../核心认知.md)为唯一权威；领域文件引用定义，负责用例编排、上下文责任、端口与验收映射。**

限界上下文按执行端划分，前端与后端各自有独立边界和权威来源，见[核心认知 §5.1.2](../核心认知.md#512-限界上下文)。

## 设计入口

| 子域 | 前端上下文 | 后端上下文 | 当前领域入口 | 状态 |
| --- | --- | --- | --- | --- |
| 全局 | — | — | [上下文映射](上下文映射-v0.4.0-20261117-175100.md) | 按执行端重划，待评审 |
| Identity（SD-01） | Frontend Identity | Backend Identity | [Identity 领域设计](identity/README.md) | 已整理跨端草案，待评审 |
| Content（SD-02） | Frontend Content | Backend Content | [领域入口](content/README.md) | 已有 v0.2.0 真实集成与 Revision 契约，待抽取独立领域设计 |
| Artifact（SD-03） | Frontend Artifact | Backend Artifact | [领域入口](artifact/README.md) | SDK 有协议构造；两端业务实现待建 |
| Relationship（SD-04） | Frontend Relationship | Backend Relationship | [领域入口](relationship/README.md) | 能力未开放，生产协议待验证 |
| Explorer（SD-05） | Frontend Reading | — | 无独立入口 | 读模型契约待建 |
| 支撑能力（SD-06~10、SD-12） | Frontend Wallet | Backend Transaction、Backend Chain Query | [支撑域](supporting/README.md) | 基于本地源码划分职责与实施缺口，待评审 |

## 编写规范

- 领域设计按七维组织：目的、结构、功能、关系、属性、状态、边界。结构、各维判据与交付检查按 [domain-design 技能](../../../../.agents/skills/domain-design/SKILL.md)；可复制骨架见[七维模版](../../../../.agents/skills/domain-design/references/domain-design-template.md)。
- 一个子域在前端与后端是两个上下文，分别写各自的领域设计，不合并成一份。前端以 Wallet 为权威、面向意图与交互；后端以链上事实为权威、面向不可变记录与投影。
- 统一使用核心认知中的 `BapIdentity / BapProfile / BapId / BapNFT / IdentityNFTBinding` 等术语。
- 稳定的实体/值对象、聚合归属、字段约束、关系基数、业务状态机、事件可信度和异常边界先定义于核心认知。Domain 按编号/章节引用，写用例如何调用端口、分配责任及映射验收，不维护第二份定义表。
- DTO 字段/状态转换和代码调用归 Frontend/Backend，实现接口归 Contracts；Domain 不写 React Hook、Spring Controller 或 Mongo 集合细节。
- 领域设计不自动成为生产验证；协议未查实标注「待验证」，附负责人和关闭证据。
- 新需求影响全局事实时先评审[核心认知](../核心认知.md)，影响契约时同步[Contracts](../contracts/README.md)和实现设计。
- 对每个领域保持 `README.md` 稳定入口；新增独立设计文件按仓库规则带时间戳，批准前保留 `needs-review`。
