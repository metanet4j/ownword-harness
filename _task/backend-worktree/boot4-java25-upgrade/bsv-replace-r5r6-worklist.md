# R5（旧依赖清理）与 R6（全量验收）清单

> **状态**：**施工前的清单**。R5 待 R4 完成后执行；R6 为最终验收。
> **依据**：§110—§113 的勘察 ＋ 各仓库实测。

## 一、R5：旧依赖清理

### 1.1 待清理的声明（实测：**恰好 3 个 POM**）

| # | POM | 声明的旧依赖 | 源码是否引用 |
| --- | --- | --- | --- |
| 1 | `metanet4j-component/metanet4j-tx-convertor/pom.xml` | `io.bitcoinsv.bitcoinjsv:bitcoinj-base`（**版本由父 POM／BOM 提供**） | **是**（R4 批次 2 会改掉） |
| 2 | `metanet4j-component/metanet4j-tx-validator/pom.xml` | 同上 | **否（0 处）** ⇒ **纯 POM 清理、无需改源码** |
| 3 | `metanet4j-component/metanet4j-tx-filter/pom.xml` | 同上 | **是**（R4 批次 2 会改掉） |

**⇒ R5 的动作**：**三处 `<dependency>` 一律删除**（源码已不引用旧类型时，依赖即应移除）；
**替换物无需新增**——这三个模块已依赖 `metanet4j-sdk`，**新 SDK 由其传递**。

### 1.2 R5 的验证

| # | 验证 | 判据 |
| --- | --- | --- |
| 1 | `grep -rc 'io\.bitcoinsv\|org\.bitcoinj'` 于三个模块的 `pom.xml` | **全为 0** |
| 2 | 全仓库 `mvn -o clean test`（component） | **全绿** |
| 3 | **JCL 计数**（§前期记录：**0**） | 保持 0 |
| 4 | 25 个 POM 树的依赖一致性 | 无旧坐标残留 |

## 二、R6：全量验收

### 2.1 六个维度的验收清单

| # | 维度 | 内容 | 判据 |
| --- | --- | --- | --- |
| **1** | **单元测试（SDK）** | `mvn -Punit-coverage clean test jacoco:report` | `failures／errors／skipped = 0`；覆盖门禁按 §D1 裁决后的口径 |
| **2** | **SDK 的 5 个 HTTP 用例** | 按 R0 的 `bsv-replace-vectors.json`（14 组冻结向量） | **全通过** |
| **3** | **component 的 18 个测试类／124 个用例** | 各子模块 `mvn clean test` | **全绿**；**集成测试不 `down -v`** |
| **4** | **25 个 POM 树的依赖一致性** | 无 `io.bitcoinsv`／`org.bitcoinj` 坐标 | **0 命中** |
| **5** | **旧类型残留** | 四个仓库 `src/{main,test}` 全量检索 | **0 命中** |
| **6** | **交付报告** | 汇总 R0—R6 的产物、验证、证据、提交 | **成文** |

### 2.2 交付报告应包含的内容（建议结构）

1. **R0—R6 各阶段的产物清单**（文件路径 ＋ 一句话作用）；
2. **每个阶段的验证证据**（命令 ＋ 退出码 ＋ 关键输出）；
3. **`feature_list.json` 的 `bsv-replace-*` 各 feature 的最终状态**；
4. **已知例外与登记**（D1 裁决后的 `unit-coverage-exceptions.json` 内容 ＋ 政策依据）；
5. **发现的代码质量问题与处置**（**S1**／**S2**／**V1**，及 §100—§102 的判定链）；
6. **未解决项与建议**（如 `MasterPrivateKey.generateLongWordList` 的 BIP39 校验和问题，§205 已建议单独立项）；
7. **本地提交记录**（四个仓库各自的提交区间；**注明"未推送远端"**）。

### 2.3 边界

- **R5 与 R6 均在 R4 完成、R3 收口之后**；
- **R6 的通过与否取决于 D1／D2 的裁决结果**——若 D1 未批准，第 1 项的"覆盖门禁"将仍不为 0；
- **本文件是清单**，不含任何已执行的改动。
