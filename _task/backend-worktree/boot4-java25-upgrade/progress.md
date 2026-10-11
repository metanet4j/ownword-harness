# 进度

## Current State

**R0—R6 全部完成。** 四仓库均在 `feature/bsv-sdk-replace` 分支，**未推送远端**。

| 阶段 | 结果 |
| --- | --- |
| **R0 基线映射** | 完成（api／tests／vectors／gate） |
| **R1 制品接入** | 完成（artifact／dependencies／fingerprint） |
| **R2 base 适配** | 完成 |
| **R3 业务 SDK 适配** | **完成：五条门禁全部达成** |
| **R4 component 适配** | **完成：43／43 文件** |
| **R5 旧依赖清理** | **完成：四仓库 9 处旧坐标清除、JVM 旧类型归零** |
| **R6 全量验收与交付** | **完成：六维度验收 ＋ 交付报告（10 章）** |

## 最终验收数据

| 模块 | 结果 |
| --- | --- |
| **`metanet4j-base`** | **47 例、0 失败 0 错误、`gaps=0`** |
| **`metanet4j-sdk`** | **271 例、0 失败 0 错误、`gaps=0`** |
| `component-tx` | 25 例全绿 |
| `tx-convertor` / `tx-filter` / `tx-validator` | 54 / 7 / 4 例全绿 |
| **`component-test`** | **错误由 96 降到 10（−90%）**；余 10 例已定性、**无一由本次替换造成** |
| **四仓库 POM 旧坐标** | **0** |
| **四仓库源码旧类型** | **0**（`base` 的 5 处经核实仅 Javadoc） |

## R6 的修复产出（7 项）

① R4 的两个密钥包不一致；② `SignErrorException` 吞掉根因；③ `sourceOutputOf` 硬编码 0 号；
④ `attachSourceOutput` 把输出固定放 0 号（**③④互相掩盖**）；⑤ 两个 `LocalTestUtxoProvider` 补锁定脚本；
⑥ 6 个 `@Tag("external")` 类从未被 surefire 排除；⑦ `TransactionBuilderContractTest.inputSum` 固化了旧行为。

## 遗留事项（建议单独立项，不阻塞交付）

1. `MasterPrivateKey.generateLongWordList()` 的 BIP39 校验问题（§205）；
2. `component-test` 的 Spring 配置（缺 `IBlockTaskService`／`ITxUtxoService` bean）；
3. `sdk.PrivateKey` vs `bsv.PrivateKey` 的类型边界（R4 出现 5 次）；
4. `S2`（`signInputs` 返回值语义）的行为处置。

## Last Updated

2026-10-11

## Current Objective

无（R0—R6 已全部完成）。

## Recommended Next Step

1. 需要时把四仓库的 `feature/bsv-sdk-replace` 分支推送远端（**当前遵约束未推送**）；
2. 处理"遗留事项"中的第 1、2 项（**均与本任务无关、建议独立立项**）。
