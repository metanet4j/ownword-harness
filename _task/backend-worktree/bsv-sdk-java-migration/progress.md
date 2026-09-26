# 当前进度

## 当前任务

activeItem=migration-impl-curve，nextItem=migration-impl-curve。曲线与点运算正在实施；`migration-impl-bignumber` 与 `migration-impl-hash-random` 已完成的逐断言验收保持 done。

执行队列共 43 项：11 done、1 in-progress、31 not-started。其中编码任务 28 项，已完成 Hex、BigNumber 构造基础、完整大整数/模运算、哈希/HMAC/PBKDF2/随机源 4 项，曲线任务进行中，其余 23 项尚未开始。21 组 API 设计：values、hash-random 2 组完成，19 组待完成。

## 曲线任务阶段性结果

- 固定 TS 的 `JacobianPoint.test.ts` 35/35 通过；Java `JacobianPointTest` 35/35 通过，37 条原断言的实际值全部匹配，缺失和额外断言均为 0。对照报告为 `.cache/evidence/curve-partial-parity.json`，`taskAcceptancePassed=false`，因为曲线事项共有 144 个原用例。
- `CurveAdditionalTest` 9 个基础用例和 `PointCoreTest` 11 个内部用例通过；后者是阶段性回归，不充抵尚未复刻的上游用例。
- `./verify.sh bsv-test` 累计执行 352/352，失败、错误、跳过均为 0；`node audit-api.cjs batches` 结构检查通过。
- 已实现基础 `Curve`、`BasePoint`、`Point`、`JacobianPoint`。Point 的完整编码、JSON、预计算和标量运算分支、Curve 的 endomorphism 与全部 API 尚未收口；相应测试、映射和逐断言对照继续进行，曲线事项保持 in-progress。

## 本次逐断言对照

证据批次：`.cache/evidence/parity-final-20260920-191152-19403q/`

- TS 原测试 13 文件一次运行：260/260 通过；Java 目标工程 `./verify.sh bsv-test`：297/297，零失败/错误/跳过。
- `task-parity.py` 以 TS `expect` 轨迹和 Java `RecordingAssertions` 轨迹按用例做有序断言配对：
  - `migration-impl-bignumber`：174 用例、1145 个上游断言全部匹配，缺失/未比较 0；额外 Java 断言 24 个单列。
  - `migration-impl-hash-random`：86 用例、432 个上游断言全部匹配，缺失/未比较 0；额外 Java 断言 11 个单列。
- Random 随机字节用例：13 个用例按测试契约只比较 matcher、期望长度/边界和 pass；跨语言随机字节本身不要求相等，已单列策略。
- Java 端提交 a2f0aa7 提供 `ParityRecorder` / `RecordingAssertions` / 扩展；Jest 端 `capture-parity.cjs` 只包 `expect` 记录 received/异常，不改原断言。
- `node audit-api.cjs batches` 已通过新的 done 门禁；`./init.sh` 通过。

## 已有 Java 成果

Java 映射测试用例 331/5329，缺失 4998；其中 JacobianPoint 的 35 个原用例已完成阶段性对照，其余完成项为：
- Hex：8 用例。
- BigNumber 构造：28 用例。
- 完整 BigNumber/模运算：174 用例，目标工程累计 211/211；逐断言对照通过。
- 哈希/HMAC/PBKDF2/随机源：86 用例，目标工程累计 297/297；逐断言对照通过。

完整 API、通用随机/属性重放、六模块最终收口和 scopeReview 仍未完成；无过滤 API check 与 `audit-tests.py check` 继续按完整范围拒绝未迁移项。

## 下一步与固定边界

下一步继续 migration-impl-curve：先补 `Point.test.ts` 和 `Point.additional.test.ts` 的完整原测试，再补 `Curve.additional.test.ts`、`Curve.unit.test.ts` 剩余行为，完成 144 用例及 153 声明的逐项收口。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
