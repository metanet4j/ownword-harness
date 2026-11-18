# 共享领域设计（Domain）

本目录是前后端共用的业务模型与领域语言入口。**所有跨模块事实以[核心认知](../核心认知.md)为权威；领域文件负责给出用例、聚合边界和一致性决策。**

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

- 统一使用核心认知中的 `BapIdentity / BapProfile / BapId / BapNFT / IdentityNFTBinding` 等术语。
- Domain 描述前置条件、领域不变量、实体/值对象、聚合、状态机、领域事件、异常与验收映射；**不写** React Hook、Spring Controller、Mongo 集合名等分端实现细节。
- 领域设计不自动成为生产验证；协议未查实标注「待验证」，附负责人和关闭证据。
- 新需求影响全局事实时先评审[核心认知](../核心认知.md)，影响契约时同步[Contracts](../contracts/README.md)和实现设计。
- 对每个领域保持 `README.md` 稳定入口；新增独立设计文件按仓库规则带时间戳，批准前保留 `needs-review`。
