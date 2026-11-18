# OwnWord 设计与开发指南

> **当前设计目标：v0.4.0（待评审，不代表已经发布）。** [版本基线清单](versions/v0.4.0.yaml)记录原型、前端、后端当前证据及实际 Git 提交；`versions` 是产品版本，不是 Maven/npm 依赖版本。

## 从哪里开始

1. [核心认知](核心认知.md)：产品事实和跨版本不变量的**唯一权威来源（SSOT）**。
2. [PRD v0.4.0](prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md)：当前目标版本新增的产品范围与原型验收；历史版本见 [PRD 目录](prd/)。
3. [领域设计入口](domain/README.md)：引用核心认知的模型和状态，描述上下文责任、用例编排、端口与验收映射；由前后端共同遵循。
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

核心认知定义稳定的实体、属性、关系、业务状态、事件和约束；PRD 描述用户任务；Domain 引用这些定义并编排用例、分配职责；Contracts 描述系统交互的可验证输入输出；Frontend/Backend 描述实现映射。其他文档不维护第二份模型或状态定义。涉及变更时先更新核心事实并核对用例和 API 兼容性，再改应用代码；验证证据的状态来自[_task/system-design/feature_list.json](../feature_list.json)及各版本验收报告。

**Identity 与支撑边界**：[支撑域设计](domain/supporting/README.md)按 Yours Wallet 与 SDK 源码明确身份管理、交易签名/提交、链状态和 Ordinal 查询职责。[Identity 技术 Review](domain/identity/评审报告-Identity-v0.4.0-20261118-103500.md)中的独立初始化资格方案已按钱包管理边界修订；当前设计不再要求 OwnWord 自建 Root 控制型初始化协议。钱包实际集成、历史验签、提交恢复及主网门禁仍待实证。

支撑域入口按领域语义、上游接入依据、钱包实现和 Java 实现分层导航；HTTP 路径、凭据与源码取证归 Contracts，上下端调用与代码示例归各自实现设计。版本含义与发布快照遵循[统一版本规则](versions/README.md)。

**当前待评审**：统一目录与 v0.4.0 清单、Identity 跨端领域边界、Binding 公共协议和 Mainnet 验收缺口。设计编写完成不自动将任何任务标为 `done`。
