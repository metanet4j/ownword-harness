# 当前进度

## 当前任务

已按用户要求重整 feature_list.json：编码任务按可独立验收的功能组划分，在同一任务内完成 API 前检、原测试映射、逐行为 TDD、实际结果对照和提交。无需先完成全部 API/P0；六个完整模块的最终验收范围不变。本次只调整任务计划、状态及必要检查工具，没有修改 Java 工程或 TS 上游。

执行队列共 43 项：9 done、0 in-progress、34 not-started。其中编码任务 28 项，已完成 Hex、BigNumber 构造基础 2 项，剩余 26 项。21 组 API 设计移到 apiBatches，作为嵌入复核清单，2 组完成、19 组待完成，不再单独排期。activeItem=null，nextItem=migration-impl-bignumber。

每项明确 sourceFiles、apiCompletionFiles、testFiles、regressionTestFiles、fixtureFiles、apiBatchRefs、依赖、交付物和验收重点；共用步骤与验收条件只在 implementationPolicy 维护。133 个 API 文件各有唯一完整实现收口任务，133 个原测试文件/5329 用例各有唯一归属，26 个辅助文件全部分配。原 serializers 待办并入完整大整数，较大脚本/交易能力按原测试完整文件分组；源码依赖闭环按真实可运行行为处理，禁止占位实现或缩减测试。

## 本次验证

- `node audit-api.cjs batches`：28 个编码任务、21 个嵌入 API 组的依赖/状态及全量文件分配通过；结果见 `.cache/evidence/feature-plan-allocation.log`。该检查只证明结构完整，不证明 Java 已实现或测试通过。
- `node test-audit.test.cjs`：41/41 通过，零失败/跳过。新增两项先 RED 后 GREEN，覆盖嵌入 API 复核及任务分配；遗漏/重复原测试、遗漏/重复 API 收口、未知源码、错误 API 引用、遗漏辅助资料、冒进完成均被拒绝。
- 自测原始日志为 `.cache/evidence/feature-plan-audit-tests.log`；新增 RED/GREEN 为 `feature-plan-embedded-{red,green}.log` 与 `feature-plan-allocation-{red,green}.log`，位于同一证据目录。工具自测不计 SDK 用例。
- `./init.sh`：最终环境自检通过；无过滤 `node audit-api.cjs check` 按预期返回 1，仍拒绝 2913 项未映射。日志为 `.cache/evidence/feature-plan-init-final.log` 与 `feature-plan-api-full-check.log`；没有放宽完整 API 门禁。

冻结范围、API 映射、测试映射与全部已完成项原证据逐项对比保持不变；下一任务的依赖已完成。五个 Java 仓及固定 TS 仓均干净、提交未变，git diff --check 通过。既有 API-02 manifest 是当时版本证据，不改写为本次任务计划的版本。

## 已有 API 与 Java 成果

API 设计 values 371 项、hash-random 292 项，累计 12 个完整文件、663/3576 声明，仍有 2913 项未映射。源码、Java 签名和行为依据见 [API 契约](doc/完整模块与API映射-20260920-122800.md) 与 api-map.json。hash-random 原 TS 测试已有 86/86，133 组探针观察和内置断言通过，索引见 `.cache/evidence/api-hash-random-manifest.json`；这些不是 Java 实现证明。

目标仓提交 9c22ba1（BigNumber 构造基础）、0ecb8d1（Hex）。最近累计对照证据 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/`：原用例 36/36、71 次断言、101 个 AST 位置；Java 共 37/37（基础测试 1 单列），零失败/错误/跳过。BigNumber 子项为原 constructor 文件 28 用例、45 静态断言→52 次执行、92 个 API 调用，实际输入/返回/异常及断言实参一致；完整 BigNumber 尚未实现。本次未重复执行 Java 测试。

采集比较工具已有自测 14/14，包含循环漏采、重复、API 调用缺失、输入位/断言值/错误消息变化及报告篡改反例。实施与复验入口见模块迁移计划。

## 下一步与固定边界

下一项 migration-impl-bignumber 收口完整 BigNumber、ReductionContext、MontgomoryMethod、Mersenne、K256，原待办 serializers 已合入；7 个尚未迁移原文件共 174 用例，另累计构造 28 用例和 Hex 8 用例。任务开始先复用已完成 values 设计、复核所需 Utils 行为并补齐本项采集，之后逐行为 TDD；未满足独立验收不能 done。

六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 原用例、7554 AST 位置。Java 映射 36/5329，缺失 5293；完整 API、通用输入重放/随机轨迹、结果采集和最终收口未完成，scopeReview=pending。此前完整 TS 基线为 5329/5329（含原规模 manual），不是 Java 完成证明。

WUA-ZERO-CAPACITY 最小修复授权保留，尚未实现；未来只把旧容量 0 的扩容起点设为 1，额外回归单列。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
