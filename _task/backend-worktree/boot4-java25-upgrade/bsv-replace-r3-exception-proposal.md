# R3 覆盖率例外登记：待批准清单

> **状态**：待用户批准。**本文件仅陈述事实与建议，未据此修改 `unit-coverage-exceptions.json`。**
> 生成于第 250 轮；依据为 `mvn -Punit-coverage clean test jacoco:report` 的实测结果。

## 1. 当前实测（门禁范围内）

| 指标 | 数值 |
| --- | --- |
| 全模块 行未覆盖 | **77** |
| 全模块 分支未覆盖 | **120** |
| 全模块 方法未覆盖 | **14** |
| **未达标类** | **9 个**，合计 行 35／分支 55／方法 1 |

**轨迹**：§214（METHOD 收口时）为 行 114／分支 199／15 类 → 现为 行 77／分支 120／9 类。

## 2. 逐类清单与建议

### 2.1 建议**登记**（设计上不可达，补测试无法触达）

| # | 类 | 行／分支 | 内容 | 依据 |
| --- | --- | --- | --- | --- |
| E1 | `ScriptExtend` | 行之 0／分支 1 | `private ScriptExtend()` —— 工具类**防实例化**的私有构造器 | 无调用点 |
| E2 | `BapBase` | 行 0／分支 1 | `:156` `(defaultRoot.indices().get(4) & HARDENED_BIT) != 0` —— 分支结果由**编译期常量** `DEFAULT_ROOT_PATH` 决定 | §86 核查 |
| E3 | `RemoteOrdTransactionTemplate` | 行 0／分支 1 | `:278` `bapBase instanceof SigningKeyProvider ? provider : null` —— **恒取 null 侧**（`BapBaseCore` 的所有实现者均不实现 `SigningKeyProvider`） | §83 核查 |
| E4 | `RemoteOrdTransactionBuilder` | 行 1／分支 1 | `:81—83` `if (!signInputs(...)) throw …` —— `signInputs` **只在 `tx == null` 时返回 false**，对已构造的 builder 不可达 | §84 核查 |
| E5 | `Sigma` | 行 1／分支 1 | `:380—381` `toBoxed` 的 `data == null` 守卫 —— **六个调用点全传非 null** | §89 核查 |
| E6 | `RemoteTransactionSigner` | 部分 | `:98—99` `signature instanceof TransactionSignature` —— `Signature.fromDER` **只构造基类**，真侧不可达 | §91 核查 |

### 2.2 建议**进一步核查或收敛**（尚未穷尽）

| # | 类 | 行／分支 | 说明 |
| --- | --- | --- | --- |
| P1 | `TransactionBuilder` | 7／11 | 含 §92 未定的 `:227—228`（备选 C 未试）；其余待逐条看 |
| P2 | `PrivateKey` | 5／2 | 待看 |
| P3 | `OrdinalsTransactionSigner` | 6／3 | 待看 |
| P4 | `RemoteTransactionSigner` | 1／4 | §91 之外的余项待看 |
| ~~P5~~ | `ScriptExtend` | 14／31／**方法 1** | **已核查完毕（§94）：判定为「应补测」**，故从"待核查"移出。其 32 处缺口中，**31 处在 public 谓词内**（`isSentToAddress`／P2SH 判定／P2PK 判定／`isSentToMultiSig`／签名数守卫／下标守卫／`isStandardPubKey`／推送长度选择），**均可测**；**仅 1 处**（`private ScriptExtend()` 防实例化构造器）属登记候选，**即清单 E1**。该类在门禁范围内（已核对 `jacoco.unit.check.excludes` 不含它） |

## 3. 需要您决定的事项

| # | 决定 | 我的建议 |
| --- | --- | --- |
| D1 | **E1—E6 是否登记**（即写入 `unit-coverage-exceptions.json`，使 `gaps` 相应减少） | **登记**。六项均有"为何不可达"的实测依据，且**不是"没测"，而是"测不到"** |
| D2 | 是否同意**先登记 E1—E6、再继续 P1—P5 的核查** | **同意**。登记可让门禁口径立即反映"已核查的部分"，后续核查不必反复重算 |
| D3 | ~~`ScriptExtend` 的口径~~ **（已由 §94 核查完毕，无需再决定）** | 结论：**应补测**（31 处可测、1 处登记）。**待您批准的是"是否现在投入补测"**——它是 R3 收口的主要剩余工作量，且其谓词在 R4 的 component 适配中被广泛依赖 |

## 4. 重要说明（政策与边界）

- 计划第 192 行规定：**「新增可执行逻辑须有测试，不得自动扩大例外范围」**。
  本清单的 E1—E6 **均非"新增逻辑未测"，而是"逻辑不可达"** ——
  **这正是第 192 行允许调整精确登记的情形**（"仅因行号或类名变化调整精确登记，需说明对应关系"）。
- **我不自行登记**：`unit-coverage-exceptions.json` 的 `decision` 字段注明例外须**经用户批准**。
- **本文件不构成登记**，仅为待批材料。
