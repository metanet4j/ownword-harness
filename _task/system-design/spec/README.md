# OwnWord 设计与开发指南

> **当前设计目标：v0.4.0（待评审，不代表已经发布）。** [版本基线清单](versions/v0.4.0.yaml)记录原型、前端、后端当前证据及实际 Git 提交；`versions` 是产品版本，不是 Maven/npm 依赖版本。

## 从哪里开始

1. [核心认知](核心认知.md)：产品事实和跨版本不变量的**唯一权威来源（SSOT）**。
2. [PRD v0.4.0](prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md)：当前目标版本新增的产品范围与原型验收；历史版本见 [PRD 目录](prd/)。
3. [领域设计入口](domain/README.md)：统一领域语言、上下文映射、聚合和业务用例；由前后端共同遵循。
4. [契约入口](contracts/README.md)：当前 API、协议验证的契约状态和 BDD 验收映射。
5. [前端开发入口](frontend/identity/README.md)和[后端开发入口](backend/identity/README.md)：领域用例如何在各自代码中实施、验证和恢复。
6. [架构决策](decisions/README.md)与[统一版本清单](versions/v0.4.0.yaml)：明确决策、待决问题及交付进度。

## 版本原则

- **一个 OwnWord 产品目标版本**，目前为 `v0.4.0`；Domain、Contracts、Frontend、Backend 文档共同服务该目标，不另行发明领域语义版本号。
- 各模块的**设计审批、实现、模拟验证、真实集成与主网验收状态分别记录**。同属 `v0.4.0` 不等于同一天完成，更不等于全部生产验收通过。
- 已批准的旧能力继续沿用，不因目标版本提高而复制或重写没有变化的领域事实。
- 发布前将所用**文档主仓、原型、前端及后端组件的完整 Git SHA** 写入清单；审批前 `specSnapshot` 为空，不误标为已锁定的发布基线。
- 独立 Git 仓库保留自身的构建与依赖版本（例如 `package.json`、Maven `pom.xml`），与 OwnWord 产品目标版本分离。
- 新独立设计 Markdown 继续保留时间戳；各目录使用不随版本变动的 `README.md` 做稳定入口。历史文件先留原位，明确标注其作用，避免断链。

## 工程现状与开发边界

- [Identity v0.1.0 PRD](prd/v0.1/设计文档v0.1.md)和[真实集成设计](frontend/设计文档v0.1.0-真实集成-20261013-183000.md)对应已经推进的身份闭环。
- [Content v0.2.0 已批准集成设计](frontend/设计文档v0.2.0-内容真实集成-20261014-215514.md)及[本地验收报告](../../../知识库/前端/ownword-v0.2.0/README.md)有实现证据；真实钱包扩展、公共历史及主网发布仍有门禁。
- [Artifact v0.3.0 PRD](prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)和 [v0.4.0 公共主页 PRD](prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md)以原型为主，生产链上契约不能从样例推断。
- 原型仓库、前端仓库和后端组件仓库为独立 Git 仓库；提交关系及当前核查值见[版本清单](versions/v0.4.0.yaml)，不使用根仓库 HEAD 冒充全部工程状态。

## 文档职责与实现顺序

`核心认知 → PRD → Domain → Contracts → Frontend/Backend Implementation → BDD/集成证据`。

PRD 描述用户任务；Domain 描述业务模型与语义；Contracts 描述系统交互的可验证输入输出；Frontend/Backend 描述实现细节。所有文档引用核心认知的事实，不抄写另一份规则。涉及变更时先查领域规则与 API 兼容性，再改应用代码；验证证据的状态来自[_task/system-design/feature_list.json](../feature_list.json)及各版本验收报告。

**Identity 技术 Review**：[评审报告（Changes Requested）](domain/identity/评审报告-Identity-v0.4.0-20261118-103500.md) 已形成领域状态/初始化资格、字段映射、历史密钥验签、接口与 BDD 的整改设计；首次主网发布仍须真实公共历史证据或经批准的安全初始化协议才可关闭 P0。

**当前待评审**：统一目录与 v0.4.0 清单、Identity 跨端领域边界、Binding 公共协议和 Mainnet 验收缺口。设计编写完成不自动将任何任务标为 `done`。
