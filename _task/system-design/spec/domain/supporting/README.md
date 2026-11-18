# 支撑域入口

当前交付目标为 OwnWord v0.4.0，设计状态 needs-review。稳定职责以[核心认知 §5.4](../../核心认知.md#54-支撑能力与产品领域的责任)为权威。

## 版本如何管理

遵循[统一版本规则](../../versions/README.md)：领域设计维护当前视图，产品发布由 Manifest 锁定文档快照；SDK/Maven/Git 依赖单独记录。文件名中的 v0.4.0 表示本次产品交付目标，支撑域不另设一套产品版号，也不按产品版本复制未变化的设计。设计、实现和真实验收分别记录。

## 按职责阅读

| 需要了解 | 文档 | 内容边界 |
| --- | --- | --- |
| 能力、模型、端口与状态 | [领域设计](领域设计-支撑域-v0.4.0-20261118-141904.md) | Wallet Integration、Transaction Support、Chain / Ordinal Query；SUP-01~10、恢复与验收 |
| Yours / 1sat 接口与源码依据 | [上游接入依据](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md) | 固定依赖证据、HTTP 路径、鉴权/密钥、线上只读观测；不作为 OwnWord 已批准 API |
| 前端钱包与交易执行 | [钱包接入实现设计](../../frontend/supporting/实现设计-钱包与交易执行-v0.4.0-20261118-164032.md) | 固定版本 Action 调用链、签名/提交、Atomic BEEF 与 rawTx、丢回执恢复 |
| Java 查询与同步接入 | [后端实现设计](../../backend/supporting/实现设计-链与Ordinal查询-v0.4.0-20261118-164032.md) | JDK HttpClient、binary/JSON/SSE、现有查询与同步改造点 |
| 实际目标与发布门禁 | [v0.4.0 Manifest](../../versions/v0.4.0.yaml) | 文档与工程基线、依赖哈希、各能力实施状态和开放门禁 |
| 可验证行为 | [supporting.feature](../../contracts/acceptance/supporting.feature) | 16 个设计场景，尚未接入运行器 |

上下文协作见 [Context Map](../上下文映射-v0.4.0-20261117-175100.md)与 [Identity](../identity/README.md)。源码已有能力、OwnWord 待适配能力和协议缺口分别表达；文档整理不代表真实钱包、Java 接入或主网已验收。
