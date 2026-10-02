# 会话交接

## 接手入口

> **任务已完成。** 若要复核，从第一节的命令开始；若要继续开发，注意第三节的三条约束。

## 一、验收已通过（2026-10-02）

`full-run-52-20260901`（19:50 起、20:54 结束，3728 秒）在一次运行内完成 TS 与 Java 双侧全量采集、证据合并与终审：

```
ts-capture   exit=0  2446.2 秒
java-capture exit=0  1193.3 秒
bundle       exit=0    44.3 秒
check        exit=0    42.9 秒
```

`status=passed`、`formalAcceptance=true`、`fullRunId=240c100e77754b89a2ed02230fd1a3a1`、17 项产物哈希写入 `artifactSha256`。

### 复核命令（全部 exit=0）

```bash
cd /home/haodev/ownword/_task/backend-worktree/bsv-sdk-java-migration
R=.cache/evidence/full-run-52-20260901

python3 full-evidence-run.py verify $R/full-run.json

python3 audit-tests.py check --catalog module-tests.json --mapping test-map.json \
  --input-plan $R/input-plan.json --ts-inputs $R/ts-inputs.jsonl \
  --java-inputs $R/java-inputs.jsonl --ts-assertions $R/ts-assertions.jsonl \
  --java-assertions $R/java-assertions.jsonl --ts-run-manifest $R/ts-run.json \
  --java-run-manifest $R/java-run.json --ts-report $R/ts-jest.json \
  --java-report $R/java-surefire.xml --observations $R/parity-results.json

node audit-api.cjs check
```

### 覆盖与七项交付

133/133 文件、5329/5329 用例（两侧各 5329）、38092 输入样本、**56744 断言逐条一致**，缺失／未执行／未比较均为 0。

| # | 交付 | 值 |
| --- | --- | --- |
| 1 | 四阶段 exit 与耗时 | 见上表，合计 3728 秒 |
| 2 | `full-evidence-run.py verify` | PASS |
| 3 | `audit-tests.py check` | PASS |
| 4 | `node audit-api.cjs check` | PASS（3576 声明） |
| 5 | `knownUnroutableCases` | **6**（`frozen-test-without-replay-entry-v1`，登记 6 条） |
| 6 | `crossLanguageInputSubstitutions.count` | **25**（substitutions 42、unorderedComparisons 1） |
| 7 | `assertionSources` | legacy 168 例/1713 行 + shared 5161 例/55031 行 = **56744** |

### 须如实披露的三处例外

1. **6 例已知缺口**：`auth-fetch-peer` 的 6 个用例在冻结 SDK 测试里没有输入重放入口（源码不读 `MIGRATION_*_TS_INPUTS`、不写 `EVIDENCE_INPUTS_PATH`）。补齐需新增重放类并改 `java_revision`。用户此前已裁决：记为已知缺口、如实披露、不重新冻结。
2. **25 例按设计的跨语言输入差异**：`cross-language-input-rules.json` 的 16 条精确规则，逐条注 gate 文件:行。
3. **32 条有据的未执行断言**（`justifiedUnexecutedAssertions`），逐条绑定固定规则、条件站点与实际分支样本。

另记：`TransactionEvidenceCoordinatorTest` 有 1 例既有 async 竞态 flake（堆压力下偶发，同参数单跑通过），属迁移测试自身竞态，未改冻结源码。

## 二、本轮修复清单

九个缺陷，全部定位到具体文件与行、修复后有验证，详见 [progress.md](progress.md) 的「2026-10-02 验收轮修复的工具链与 SDK 缺陷」一节：

- **任务侧**：`audit-tests.py`、`capture-parity.cjs`、五个 `replay-*.py`、`run-full-ts-serial.py`、`build-full-run-probes.py`、新增 `semantic-plan-rules.py`、`test-map.json`
- **SDK 侧**（`metanet4j-bsv-sdk` 分支 `feature/bsv-sdk-java-migration`，两个提交）：`RecordingAssertions` 四处 `toThrow` 的 expected 由「类源码／原生函数源码」统一改为类简单名，删除 6 个失效冻结语料。

修复背景：此前十几次运行的中断有三类原因——WSL2 虚拟机被外部重启（旧交接单误记为 SIGTERM，`setsid nohup` 无法抵御）；`fullRun.tsCommand` 被 `build-full-run-probes.py` 里的硬编码改回旧 driver，令 `a568cff` 的切换失效；以及上述九个缺陷本身。逐条诊断见 [验收阻塞诊断与工具链修复](doc/验收收尾交接-20261001-170000.md) 与 progress.md。

ownword 主仓提交（未推送）：`9c89b7b`、`22c2624`、`df58111`、`028c0d1`。

## 三、后续开发的约束

1. **哈希绑定**：`full-evidence-run.py::producers()` 会哈希任务根目录下全部 `.py/.cjs/.mjs/.sh`；`validate_retry` 还要求 180 分钟档引用一份**真实触及 90 分钟上限**且 `producerSha256` 逐项相同的运行。改动这些文件后，`full-run-52` 不能直接复用——需重新产出同源超时来源或接受重跑。
2. **来源绑定**：`test-map.json`、`module-tests.json`、输入计划的哈希都写进了 `ts-run.json`/`java-run.json`；改动任一清单后必须重跑才能让终审通过。
3. **环境判据**：本机 WSL 上 `uptime -s` 每次调用有 1–2 秒漂移，判断「是否重启」要用 `last -x reboot` 首行，不要做 `uptime -s` 字符串比较。

## 四、复现环境

- SDK：`metanet4j-bsv-sdk`（`feature/bsv-sdk-java-migration`，HEAD `3dd8beb`；验收记录的 `javaRevision` 为 `ce6b50d7cb35…`）
- 其余四个 Java 工程（parent／base／sdk／component）全程只读，未改动
- 上游 TS：`reference/ts-stack`（固定提交 `f999e0c1aad9a7afd0cbadaaf23841d049af9d5a`）
- Maven 与 pnpm 一律走 `./mvn.sh`／`./pnpm.sh`；开跑前建议先跑 `./final-window-guard.sh 10`（六项守卫）
- 注意：`verify.sh bsv-test` 执行的是裸 `mvn clean test`（不设 `MIGRATION_*_TS_INPUTS`），此时 `DefaultHttpClientAdditionalTest` 的 4 例会失败；全量运行由 `run-full-java-capture.py` 设置全部 78 个 env，不受影响。