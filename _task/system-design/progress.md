# 当前进展

当前事项为 `domain-subdomain-context-v040`，状态 needs-review。已把子域类型与限界上下文归入核心认知 §5，并按执行端把上下文划分为前端与后端两套边界；任务范围和证据见[feature_list.json](feature_list.json)。

## 当前产出

- [核心认知](spec/核心认知.md)：§5.1.1 子域类型（SD-01~12）、§5.1.2 按执行端划分的限界上下文（前端 6 / 后端 6 / 共享 1）、§5.2 按端标注的 12 个领域接口、§5.4 交易职责修订。
- [上下文映射](spec/domain/上下文映射-v0.4.0-20261117-175100.md)：按执行端重写，Mermaid 图区分 FE/BE 子图。
- [Domain 入口](spec/domain/README.md)：入口表改为「子域 → 前端上下文 / 后端上下文」三列。
- [ADR-002 交易执行归属钱包](spec/decisions/ADR-002-交易执行归属钱包-20261119-140000.md)：交易构造、签名、广播统一由 Yours Wallet 完成。
- [domain-design 技能](../../.agents/skills/domain-design/SKILL.md)：七维写作规范。
- [核心认知模版](../../.agents/skills/core-principle/references/core-cognition-template.md)：15 节骨架。

## 解决的问题

**两套上下文划分并存。** 原本 §5.1 模块列 6 个业务模块，上下文映射列 8 个上下文（Wallet 拆为 Wallet Integration、Transaction Support、Chain & Ordinal Query），写领域设计时无法裁决。现按执行端统一：前端 6 个上下文以 Wallet 为权威、面向意图与交互；后端 6 个以 Bitcoin 为权威、面向不可变记录与投影。

**交易执行主体不明。** 代码实测显示前端 16 处直接 import `@bsv/sdk` 构造交易，后端 `api-ownword` 六个类 import `metanet4j-bsv-sdk` 解析交易。ADR-002 明确交易只在钱包侧执行，后端只解析与验签；核心认知 §5.4 原文「metanet4j 可构造和验证交易」已改为「只解析和验证交易，不构造待签交易」。

## 验证范围

核心认知 §5 结构完整（5.1 → 5.1.1 → 5.1.2 → 5.2 → 5.3 → 5.4）；§5.1.2 的 13 个上下文行与 §5.2 的 12 个接口行均标注执行端；旧上下文名（Wallet Integration、Transaction Support、Chain & Ordinal Query）在全 spec 目录已清零；六个文件相对链接断链均为 0；`feature_list.json` 可解析。

未执行真实钱包调用、主网广播、Java/TS 运行时或前端构建。本次仅文档改动。

## 实施限制与下一步

前端 `@bsv/sdk` 的使用范围尚未按 ADR-002 审计改造，六处交易构造待处理。钱包 API 是否支持自定义 MAP（`ownword.revision`、`ownword.rootTxid`、`ownword.previousTxid`）未验证，这是 Revision 语义能否只在钱包侧完成的前提。

唯一下一步：验证 Yours Wallet API 的自定义 MAP 能力，再按 ADR-002 改造前端六处交易构造。人工复核前不记 done。
