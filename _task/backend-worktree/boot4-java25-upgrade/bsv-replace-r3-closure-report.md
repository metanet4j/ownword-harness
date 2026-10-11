# R3（业务 SDK 适配）收口报告

> 生成于第 293 轮。**依据**：实测命令输出 + `evidence/bsv-replace/r3-keys-20261010/migration-rules.md`（§1—§106）。

## 一、五条门禁的达成情况

| # | 门禁 | 状态 | 证据 |
| --- | --- | --- | --- |
| **1** | 生产／测试源码中**不含旧库类型** | ✅ **达成** | `grep -rl 'io\.bitcoinsv'` → **生产 0 个文件、测试 0 个文件** |
| **2** | **测试全绿**（`failures／errors／skipped` 均为 0） | ✅ **达成** | 最近一次运行：`Tests run: 268, Failures: 0, Errors: 0, Skipped: 0` |
| **3** | **冻结协议向量通过** | ✅ **达成** | `bsv-replace-vectors.json` 的 **14 组向量全部 `status: frozen`**；历次全量运行中相关契约用例 **0 失败**（含 `OrdHistoricalFixtureContractTest` 的真实链上签名夹具） |
| **4** | **原有行为处置已登记** | ✅ **达成** | `migration-rules.md` §1—§106：逐条记录"删了什么、保留了什么、为何"；`bsv-replace-artifact.json` 中 `upstreamDefects` 与 `deferredItems`（`SIGMA-VERIFY-001` 已解决） |
| **5** | **覆盖率缺口 `gaps=0`** | ⏳ **待裁决** | 见第二节 |

## 二、第 5 条门禁的当前状态

| 指标 | §214（METHOD 收口时） | **现在** | 变化 |
| --- | --- | --- | --- |
| 全模块 行未覆盖 | 114 | **55** | **−59** |
| 全模块 分支未覆盖 | 199 | **79** | **−120** |
| 方法未覆盖 | 14 | 14 | — |
| 未达标类 | 15 | **9** | −6 |
| **未达标类合计** | — | **行 13／分支 14／方法 1** | — |

**剩余 14 个分支 ＋ 1 个方法的去向（逐项明确、无遗漏）**：

| 去向 | 明细 | 项数 |
| --- | --- | --- |
| **登记候选 E1—E8** | E1（1 方法）、E2／E3／E4／E5／E8（各 1 分支） | **6** |
| **已证不可达** | `PrivateKey:75—77`（§226）、`OrdinalsTransactionSigner:103—105`（§93／§272） | **2** |
| **待定性 P1—P4** | `RemoteTransactionSigner:124`、`OrdinalsTransactionSigner:116`、`PrivateKey:72—73`、`TransactionBuilder:227—228` | **2～3** |
| **技术性说明** | `RemoteTransactionSigner:108`／`:110`（§106：四个组合都写过仍各余 `b1`，推断为 jacoco 拆分行归属） | **2** |
| **合计** | | **14 ＋ 1 方法** ✓ |

## 三、需要您裁决的事项

| # | 决定 | 我的建议 |
| --- | --- | --- |
| **D1** | **E1—E8 是否登记**（写入 `unit-coverage-exceptions.json`） | **登记**——八项均附"为何不可达"的实测依据，**非"未测"而是"测不到"** |
| **D2** | **S1（`resolveKeyProvider` 恒 null）／S2（`signInputs` 返回值形同虚设）选 A 还是 C** | **S2 选 A**（修正语义，改动局限在 `signInputs` 内部）**／S1 选 C**（保留＋登记，其修正涉及类型层次、宜单独立项） |
| **D3** | **P1—P4 是否现在穷尽**（约 2 轮） | **建议现在穷尽**，使 R3 一次性收干净 |
| **D4** | 技术性说明（`:108`／`:110`）是否接受"待 R6 用整体数字复核" | **接受**——已无组合可补 |

## 四、R3 期间产出的三项代码质量发现（非覆盖率）

| # | 发现 | 性质 | 处置建议 |
| --- | --- | --- | --- |
| **S1** | `RemoteOrdTransactionTemplate` 的 `resolveKeyProvider` **恒返回 null**（§83） | **语义缺陷** | 保留＋登记（或单独立项） |
| **S2** | `RemoteTransactionSigner.signInputs` **只在 `tx == null` 时返回 false**（§84，§272 第二次实证） | **语义缺陷** | 修正语义 |
| **V1** | `Signature.fromDER` 只构造基类 ⇒ `instanceof TransactionSignature` 真侧不可达（§91） | 不可达 | 登记（**E6**） |

## 五、边界

- **本报告不构成登记**，不改变任何生产代码；`unit-coverage-exceptions.json` 的 `decision` 字段注明例外须**经用户批准**。
- **D2 若选 A 会改变运行时行为**，须您明确同意后我再动手。
- 本报告可随裁决结果更新。
