# 会话交接

## 唯一下一步

activeItem=null，nextItem=migration-impl-curve。`migration-impl-bignumber` 与 `migration-impl-hash-random` 已完成逐断言 taskAcceptance 并恢复 done；本次到此停止，尚未开始 curve。

## 逐断言验收入口

证据批次：`.cache/evidence/parity-final-20260920-191152-19403q/`

- `ts-parity.jsonl`：Jest setup `capture-parity.cjs` 记录的全部 matcher received/异常。
- `parity-java.jsonl`：Java `ParityRecordingExtension` + `RecordingAssertions` 记录的全部断言实际值。
- `bignumber-parity.json`：174 用例、1145 断言匹配，missing/uncompared=0，`taskAcceptancePassed=true`。
- `hash-random-parity.json`：86 用例、432 断言匹配，missing/uncompared=0，`taskAcceptancePassed=true`；13 个 Random 随机字节用例按 matcher/边界/pass 策略单列。
- 复跑：`python3 task-parity.py --task <id> --ts <ts-path> --java <java-path> --output <report>`。

## 已完成 Java 提交

- `a2f0aa7`：BigNumber/哈希随机测试接入逐断言轨迹采集。
- `9fbcc9d`：哈希、HMAC、PBKDF2、DRBG、Random。
- `a697a49`：BigNumber、ReductionContext、Mersenne、K256、MontgomoryMethod。
- `9c22ba1`：BigNumber 构造基础。
- `0ecb8d1`：Hex。

目标工程 clean test 当前 297/297；Hex/构造既有逐调用证据仍保留在 `.cache/evidence/hex-parity-*`。

## 固定边界

Random 的 Node/浏览器分支在 Java 中为可注入 Runtime 适配；随机字节测试不比较跨语言具体字节，只比较原有行为断言。完整六模块 API、通用随机/属性重放和最终 audit-tests.py check 未完成，不能把内部任务 done 当成整模块完成。

Maven/pnpm 仅经任务脚本；不推送、不广播交易、不调用真实钱包或外部业务接口。只提交任务明确路径，不混入根仓既有规则/技能/.opencode 改动。
