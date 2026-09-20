# 会话交接

## 唯一下一步

当前 activeItem=migration-impl-bignumber，nextItem=migration-impl-bignumber。`migration-impl-bignumber` 与 `migration-impl-hash-random` 均已回到 in-progress，先补齐逐断言 TS/Java 实际值 compare；不要先推进 migration-impl-curve。

## 为什么回退

feature_list 的 implementationPolicy 要求：testFiles 的全部注册用例、参数行、断言和动态样本均有原始执行及 Java 证据；记录实际输入/输出/异常/调用顺序；复用 audit-tests.py compare 核对实际结果；零漏采/未比较。此前两项只有 case-level 映射、固定期望值和两端 clean test 通过，`formalAcceptance=false`，不满足 done 条件。

## 新增硬门禁

- `taskAcceptanceRule`：implementation-slice 的 done 必须有 `taskAcceptance.status=passed`、`casesCompared` 等于冻结用例数、`missingCases/missingAssertions/uncompared=0`、`compareReport` 文件存在。
- `node audit-api.cjs batches` 已实现该门禁，`node test-audit.test.cjs` 增加相应反例。
- `./init.sh` 允许存在多个 in-progress，但 activeItem 必须指向其中一个；nextItem 必须有效。
- 以后 `formalAcceptance=false` 不能再作为 implementation-slice done 的豁免。

## 恢复入口

- 目标仓当前提交：`9fbcc9d`（哈希/随机）、`a697a49`（完整大整数/模运算）。
- case-level 证据：
  - `.cache/evidence/bignumber-final-20260920-173943-23798q/`
  - `.cache/evidence/hash-random-final-20260920-175813-4236q/`
- 已完成且有 taskAcceptance passed 的：
  - Hex：`.cache/evidence/hex-parity-20260920-150144-mgrmta7b/`
  - BigNumber 构造：`.cache/evidence/hex-parity-20260920-153441-zd037qhq/`

## 固定边界

先为 174 个 BigNumber/模运算用例建立逐断言 TS/Java 原始值对照，再为 86 个哈希/随机用例建立同样对照；Random 的宿主分支必须提供可重放输入轨迹，不能用可注入 Runtime 直接代替真实轨迹。两项都通过 taskAcceptance 后才能恢复 done，再推进 migration-impl-curve。

scopeReview=pending；完整模块最终仍运行无过滤 API check 与六模块 audit-tests.py check。Maven/pnpm 仅经任务脚本；不推送、不广播交易、不调用真实钱包或外部业务接口。
