# 当前进度

## 当前任务

编码任务在同一任务内完成 API 前检、原测试映射、TDD、逐断言实际结果对照和提交。当前 activeItem=migration-impl-bignumber，nextItem=migration-impl-bignumber；`migration-impl-bignumber` 与 `migration-impl-hash-random` 均已回到 `in-progress`，先补齐逐断言 evidence 与 compare。

执行队列共 43 项：9 done、2 in-progress、32 not-started。其中编码任务 28 项，已完成 Hex、BigNumber 构造基础 2 项；完整大整数/模运算与哈希/随机源两项代码及 case-level clean test 已实现，但 taskAcceptance 未通过，不能标记 done。21 组 API 设计：values、hash-random 2 组完成，19 组待完成。133 个 API 文件、133 个原测试文件/5329 用例及 26 个辅助文件均已分配到唯一收口任务。

## 本次检查调整

- `feature_list.json` 新增 `taskAcceptanceRule`，并要求 implementation-slice 的 `done` 必须具有通过的 `taskAcceptance`：`casesCompared` 等于冻结用例数，`missingCases/missingAssertions/uncompared` 全为 0，`compareReport` 文件真实存在。
- `node audit-api.cjs batches` 已实现该 done 门禁；`test-audit.test.cjs` 增加反例：缺 taskAcceptance、status 非 passed、casesCompared 不符、存在 missing/uncompared、compareReport 缺失均拒绝。
- `./init.sh` 已允许同一工作区存在多个 `in-progress`，但 `activeItem` 必须指向其中一个进行中事项，`nextItem` 必须存在且为有效执行事项。
- 因此本次把 `migration-impl-bignumber` 与 `migration-impl-hash-random` 从 done 回退为 in-progress。

## 已有 Java 实现与证据

- Hex：taskAcceptance passed，8 用例、19 断言，证据 `.cache/evidence/hex-parity-20260920-150144-mgrmta7b/`。
- BigNumber 构造：taskAcceptance passed，28 用例、52 次实际断言，证据 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/`。
- 完整 BigNumber/模运算：java 提交 a697a49，174 个新增原用例，TS 174/174、目标工程 clean test 211/211；case-level 证据 `.cache/evidence/bignumber-final-20260920-173943-23798q/`，但尚无 174 用例的逐断言 TS/Java 原始值 compare。
- 哈希/HMAC/PBKDF2/随机源：java 提交 9fbcc9d，86 个新增原用例，TS 86/86、目标工程 clean test 297/297；case-level 证据 `.cache/evidence/hash-random-final-20260920-175813-4236q/`，但尚无 86 用例的逐断言 TS/Java 原始值 compare 与随机输入重放。

## 下一步与固定边界

先收口 migration-impl-bignumber 的逐断言 TS/Java 实际值比较（174 用例）和 migration-impl-hash-random 的逐断言比较及随机输入重放（86 用例）。两项 taskAcceptance passed 后，才恢复 done 并推进 migration-impl-curve。

六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 原用例、7554 AST 位置。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
