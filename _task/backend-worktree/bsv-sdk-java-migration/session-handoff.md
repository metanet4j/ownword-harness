# 会话交接

## 接手入口（先读这一节）

**当前状态（20260901 01:40）**：证据层已完备、来源已冻结，只剩「单次双侧全量运行 + 两套审计」即可结项。

- 权威状态：[feature_list.json](feature_list.json) —— 43 个事项中 **31 done／0 in-progress／12 未结**（4 个含专用局部的实现事项 + 8 个总门禁）。
- 输入计划：**5329／5329 = 100%**；`full-evidence-preflight.py` → `readyForFullCapture=true`、`planErrors=[]`、`completePlanError` 空。
- 统一窗口 v2（`recapture-all.sh final2-20260930`）：**108 项处理／107 篡改门禁通过／0 失败**，汇总「全部局部重采与篡改门禁通过」；106 个局部同为来源 `13f34162199d`（= 当前工作树）。
- 任务级对照：**14 个事项**已有 `task-parity.json`（合计约 1312 例，`missingCases`／`missingAssertions`／`uncompared` 全 0），已写入 `feature_list.json` 的 `taskAcceptance`。
- 冻结来源：SDK 仓 **`8b8e13d`**（`src/main` 零改动，仅 4 个测试文件）。

**v8 进度（21:30）**：11 分钟内即 **127 文件 PASS／0 FAIL**（远快于上一轮同点的 132 文件/55 分钟），随后停在重型文件上（jest 自 21:03 持续 111% CPU，疑为 66 分钟的 `AESGCM.man`）。若总时长仍 <90 分钟，则**无需** 180 分钟档，v8 会直接跑完。

- **v9 存活确认（21:41）**：cron 拉起后已跑 7 分 22 秒、jest **127 文件 PASS／0 FAIL**，进程父级为 cron，会话空闲清理不再影响它 ✓。
- **v10 进度（22:44）**：存活 16 分钟、jest 尚无 PASS —— 首个文件即重型文件（jest 按历史耗时把最慢的排最前，v9 也是同一现象的另一端），预计总时长 ~76–80 分钟，**仍在 90 分钟上限内**。
**全量串行跑完（20260901 05:55）**：`01:53:04` 结束（exit=0），`localsSelected 154`、**`filesCovered 130`**（比上一版多出 `aesgcm-man` 的文件），`localsFailed` 仍只有已知的 `utils-property`／`auth-fetch-property`（driver bug 已修，待 `--resume` 补跑）。代理已恢复活动（`run-full-ts-serial.py` 01:56 有更新）。

**driver 自检能力已确认（20260901 05:10）**：`run-full-ts-serial.py` 具备 `--resume`（跳过已完成局部）与 `--allow-partial`（仅子集自测；**不加该开关时覆盖不足即非零退出**），且报告说明各局部 jest JSON 按文件去重合并成一份以满足 `audit-tests.compare_ts` ✓。`aesgcm-man` 长跑仍在进行（约 01:35 起，预计 ~02:15 结束）；`fullRun.tsCommand` 待代理应用批准。

**全量串行阶段报告（20260901 05:00）**：`filesCovered 129`、**`casesCovered 5328`**、`inputsWritten 37114`、`assertionsWritten 55165`；`localsFailed` 仅 `utils-property`／`auth-fetch-property`（driver 预建 `--raw-dir` 的 bug，已修待 `--resume` 补跑），其 `problems` 正是这两个局部对应的 976 个缺失样本 + 4 个用例断言 ✓。`aesgcm-man` 仍在长跑（进程存活）。`fullRun.tsCommand` 尚未切换（等代理应用批准）。

**已批准接入（20260901 04:45）**：`fullRun.tsCommand` 由 `run-full-ts-capture.py` 换成 **`run-full-ts-serial.py`**（只改这一处；`tsReports` 与 `javaCommand` 不变）。四形态均已实跑通过（standard 55+／adapter 27／direct 18／vector 2，含 1940 例的 `script-spend-shared-vectors`）；仅 `utils-property`／`auth-fetch-property` 因 driver 预建 `--raw-dir` 失败，已修并单独复跑 **2/2 通过**。
**开跑前要求的两条证据**：①`--verify-only`／`--resume` 后 154 局部全通过；②driver 内置 `compare_ts` 自检（合并报告覆盖 **133 文件**且逐用例名与 `module-tests.json` 一致）。随后 `full-evidence-run.py run --run-dir .cache/evidence/full-run-11-20260901 --timeout-minutes 90`（cron 拉起；若被上限终止即为 180 分钟档所需的真实超时证据）。
**诚实性口径**：交付文档须写明 TS 侧是**逐局部串行采集后合并**（非单进程单次运行），与结项说明一致。

**全量串行进度（20260901 04:35）**：**153/154 局部 passed**（累计 15.6 分钟），仅剩 `aesgcm-man`（约 40 分钟长跑）在跑。

**全量串行进度（20260901 04:25）**：已完成 **145 个局部、全部 passed**（累计约 14.5 分钟）；剩余 9 个：`private-key-split`、`random`、`transaction-performance`、`random-additional`、`hash-additional`、`symmetric-key-compatibility`、`bignumber-dh-group`、`async-crypto-backend`、**`aesgcm-man`（约 40 分钟）**。

**全量串行进度（20260901 04:05）**：`89/154` 局部已完成、**全部 passed**、累计 8.2 分钟（日志逐行给出 `step/local/status/seconds/elapsed`）✓。

**路径 B 全量串行已启动（20260901 03:45）**：子集自测报告为 **7 文件／763 用例／8768 输入／1613 断言／122 秒／`problems=[]`** ✓；随后**全量串行**已启动——目录 `.cache/evidence/ts-serial-full-20260901/`、日志同名前缀 `.log`、进程 `run-full-ts-serial.py --run-dir .cache/evidence/ts-serial-full-20260901`。预计 TS 侧 ~48 分钟（其中 `aesgcm-man` 40 分钟），之后接一次无过滤 `clean test` 与两套审计。

**路径 B 更大子集自测（20260901 03:35）**：`ts-serial-selftest-20260901` 覆盖多个局部（`broadcaster`、`byte-base58`、`chronicle`、`compat-bsm`、`normative-vectors` 等，逐局部 `local/` 子目录），产出 **8768 行输入 / 1613 行断言**（约占全集 38092 样本的 23%）；`ts-serial-report.json` 尚未写出（收尾中）。

**路径 B 冒烟全绿（20260901 03:25）**：`ts-serial-shapes-20260901`（四形态，4 文件／23 用例／8.8 秒，`problems=[]` ✓）与 `ts-serial-vector-20260901`（vector 形态，**659 用例／1159 输入／1159 断言／29.9 秒，`problems=[]` ✓**）均通过。剩余：`script-spend-shared-vectors`（1940 例）与 154 局部全量串行。

**两路状态回报（20260901 03:20）**

- **路径 A（分派机制）**：已定位并改完五类根因（均非猜测）——①9 个 spend 探针读 `EVIDENCE_INPUT_PLAN` 同目录 `catalog.json` 失败 → 运行期把局部冻结计划复制到 `<runDir>/plans/<local>/` 并重指；②31 个 raw 局部无 emit 转换器（驱动用 `replay.emit_ts()` 内联而非字面量 `emit-ts` argv）→ 新增 `full-run-overrides.json` 的 `locals` 段逐局部登记 emit（`full-emit.py`／`full-emit-inline.py`／`full-emit-special.py`）；③断言缺口源于**共享断言轨迹的 matcher 序号被破坏**（`capture-bn-constructor.cjs` 等替换 `global.expect`，行格式不同）→ 这些局部改走 legacy 断言通道；④`capture-wallet-wire-parity.cjs` 与共享层双重记录同一 matcher → 从分派表移除；⑤24028 缺失样本是前四者的合成结果。下一步四个小子集自测 → 133 文件严格自测，ETA 40–60 分钟。
- **路径 B（串行合并 driver）**：映射表**已完成**——47 个非标准局部全部核实到真实入口、0 个 unresolved（27 个 adapter 按登记 manifest 里当时跑通的原命令还原；18 个 direct；2 个 vector 覆盖 2599 例），5 个 `/tmp` 语料副本消失的局部回退到冻结 SDK 资源并记 `substitutions`；driver 四形态已接入，标准/`adapter` 形态冒烟通过，`direct` 形态 2 个局部在定位，另修一处自研 `order_rows` 包装 NameError；ETA 30–45 分钟冒烟全绿，随后 154 局部全量串行（交 cron）。

**环境体检（20260901 03:15）**：`crontab` 已无条目 ✓（长跑用完即删的纪律已落实）、无残留 `mvn`／`jest`／`full-evidence` 进程 ✓、共享锁空闲 ✓。两路代理仍在运行（近数分钟静默，属正常分析间歇）。

**进展（20260901 03:00）**：路径 B 新增 `build-ts-serial-entries.py`（00:33，映射表生成器，可复现）与 `ts-serial-entries.json`（47 条「局部→TS 入口」，含 shape/script/args）✓；路径 A 继续改 `run-full-ts-capture.py` 与 `full-run-overrides.json`。全量串行运行尚未启动。

**等待期（20260901 02:45）**：两路代理均无新落盘（无 `run-full-ts-serial`／`run-full-ts-capture` 进程、无新证据目录）。当前可交付状态：路径 B 的 driver 已冒烟通过、四形态扩展方案已批准并写入本文档；路径 A 已改三个机制文件但未验证。**下一位接手者的最短路径**：①先问/查两路代理的当前状态；②优先把路径 B 扩到四形态并跑满 133 文件（TS 侧实测仅 ~48 分钟，其中 aesgcm-man 40 分钟）；③一次无过滤 `clean test`；④`audit-tests.py check` 显式传路径 + `audit-api.cjs check`；⑤结清剩余 12 项。

**路径 B 进展（20260901 02:35）**：`run-full-ts-serial.py`（506 行）与 `full-emit.py` 已落盘，冒烟测试目录 `.cache/evidence/ts-serial-smoke-20260901/` 产出完整的合并产物（`ts-inputs.jsonl`、`ts-assertions.jsonl`、`ts-assertions.raw.jsonl`、`ts-jest.json`、逐局部 `local/` 子目录、`ts-serial-report.json`），报告含 `casesCovered/casesPlanned`、`filesCovered/filesPlanned`、`inputsWritten`、`assertionsWritten`、`jestFiles/jestTests`、`localsFailed`、`problems=[]` ✓。下一步：扩到四形态并跑满 133 文件。
**路径 A 进展**：`capture-full-dispatch.cjs`／`run-full-ts-capture.py`／`build-full-run-probes.py` 已在 23:38–23:41 被修改（代理仍在迭代）。

**决定性与更正（20260901 02:30，代理核算 + 主代理批准）**：
- **标准局部只覆盖 2088／5329 用例** ✗。剩余 **3241 用例／14630 样本**落在 **26 个文件**上：18 个 `specialized-local`（`script-spend-shared-vectors` 1940 + `transaction-shared-vectors` 659 = 2599）＋ **29 个登记项缺 `capture` 字段的旧管线局部**（`mnemonic-original`、`bignumber-arithmetic`、`reader/writer`、`point-additional`、`jacobian`、`utils.*` 等，共 509 用例）；另有 4 个文件被标准与非标准局部**共同切分**。
- 硬门禁 `audit-tests.py::compare_ts` 要求 TS 报告含**全部 133 文件**且逐用例名一致、`audit.compare` 要求 Java 执行全部映射用例 → **必须 133 文件全覆盖**，只做标准局部永远到不了终点。
- **路径 C 放弃**：拼装 v2 的 107 份产物覆盖仍只有 107 文件，且 `full-evidence-run.py verify` 会校验两侧 `-run.json` 的 `fullRunId`／`producerSha256` 与阶段时间窗，**拼装证据只能靠伪造 manifest 过关 → 不可验证，永不采纳**。
- 成本数据（代理实测）：v2 的 TS 侧合计仅 **0.80 h**，其中 `aesgcm-man` 占 40 分钟、其余 106 个仅 **8 分钟** → 串行重跑可接受。
- **已批准路径 B 扩展**：同一个 driver 覆盖四形态——①标准 `--plan`；②旧式 `--replay`；③16 个 auth-fetch 直写探针；④`script-vector-evidence.py ts`／`transaction-vector-evidence.py ts`（覆盖 2599 用例）；并为 29 个无 `capture` 的旧管线局部**逐个核实真实 TS 入口**后补「局部→入口」映射。jest 报告合并沿用 `merge_reports` 做法，但必须保证逐用例名与 `module-tests.json` 完全一致。

**路径 C（更省，已交路径 B 代理评估，20260901 02:00）**：主代理实测发现——统一窗口 v2 的 **107 个运行目录每个都已具备全套产物**（`ts-inputs.jsonl`、`ts-assertions.jsonl`、`ts-assertions.raw.jsonl`、`java-inputs.jsonl`、`java-assertions.jsonl`、`java-assertions.raw.jsonl`），且 preflight 显示**同为来源 `13f34162199d`**（= 当前工作树）。因此可以：合并 106 个标准局部的 TS 产物（**零重跑**）→ 跑**一次**无过滤 `clean test` 拿 Java 侧 → `audit-tests.py check` 显式传路径跑模块门禁 → `audit-api.cjs check`。
**诚实性要求**：路径 C 的 TS 侧来自 106 次同源单文件采集，**不是**单进程单次运行；若门禁通过，必须在文档与结项说明里写明这一事实与依据（同源摘要、逐用例双侧同输入），不得表述为“单次全量运行”。

**路径 B 的实测坑（主代理亲测，已同步给代理）**：局部适配器有**两种接口形态** —— ①标准：`capture-*-local.py --local <名> --plan <计划目录> --report <路径> ts`；②旧式：`capture-broadcaster-side.py ts --replay <replay-inputs.jsonl> --report <路径>`（`broadcaster`／`capture-legacy-side.py`／`capture-drbg-side.py`，**没有 `--local`/`--plan`**）。实测 `capture-broadcaster-side.py --local broadcaster --plan … ts` 会报 `argument side: invalid choice: 'broadcaster'`。
**必须复用 `recapture-local.py` 的分派规则**：登记项有 `catalog` → `--plan <catalog 父目录>`；否则有 `replay` → `--replay <该路径>`；并且**必须设 `EVIDENCE_SIDE=ts`**（否则适配器报“采集侧别与运行环境不同”），输入写到 `EVIDENCE_INPUTS_PATH=<子目录>/inputs.jsonl`。

**当前两路并行（20260901 01:40）**：路径 A＝修 `capture-full-dispatch.cjs`／`run-full-ts-capture.py` 的单进程分派（已派代理，尚无落盘产物）；路径 B＝**后备实现**（已派第二路代理，任务书含我实测确认的机制细节：单局部适配器逐文件跑 jest、parity 写 `evidence/ts-assertions.raw.jsonl`、`prepare-*-local.py emit-ts --output` 是**覆盖写**（故每个局部用独立子目录收集 inputs 后再合并）、断言转换复用 `emit-assertion-observations.py`、排序与对账直接 import `run-full-ts-capture.py` 的函数）。路径 B 先用 5 个局部自测（含 v10 里“轨迹缺失”的典型四个），再跑全量 106 个标准局部。

**后备方案（路径 B，若路径 A 修不动就改走它）**：把“单次全量 TS 采集”实现为**逐局部 TS 采集的串行合并**——

1. 新建一个 driver：遍历 153 个可采局部，对每个局部调用它**已跑通的** TS 适配器（`capture-*-local.py ts`），
   把各自的输入行与 parity 断言行**追加**到统一运行目录（`ts-inputs.jsonl`、`ts-assertions.raw.jsonl`）；
2. 用现有 `run-full-java-capture.py`（它把汇总输入按局部切给全部 Java 重放，跑一次无过滤 `clean test`）；
3. 断言与对账沿用 `run-full-ts-capture.py` 后段的 `emit_assertion_observations` + 计划对账。

可行性依据：逐局部 TS/Java 双侧在窗口 v2 已 107/108 通过、0 失败；缺的只是“把它们串起来产出一份同源全量证据”。
代价：新增一个 driver（约百余行），但**全部复用已验证组件**，比修 `capture-full-dispatch.cjs` 的装载机制更可控。

**full-run-14 结果：TS ✓、Java ✓、bundle ✗（仅 4 个用例）（20260901 11:05）**：`06:54:18` 结束 exit=1。`java-capture` **全绿**（`Tests run: 5444, Failures: 0, Errors: 0`）——PBKDF2 修复生效 ✓✓；失败阶段是 `bundle`，唯一报错为 `Java 输入用例：缺失 [...]`，**只有 4 个 caseId**（5329 中的 4 个）。已把这 4 个 caseId 交给代理：反查所属局部/原文件 → 定位为何没进 Java 输入（该给却没给／sampleId 口径／本应由别的路径产出）→ 单点预验证 → `full-run-15`。

**真注入链已找到并修复（20260901 09:50）**：根因是 `run-full-java-capture.py::main()` 的 `targets = set(configured) | set(discovered)` —— `configured` 来自 `full-run-probes.json['envs']`（115 个 `*_TS_INPUTS`，含 `MIGRATION_HASH_PBKDF2_TS_INPUTS`），**并集把上一版在 `discovered` 上排掉的变量又并了回来**。修复：`targets = sorted((set(configured) | set(discovered)) - set(EXCLUDED_TS_INPUT_ENVS))`（排除仍精确到一个变量，报告记 `excludedTsInputEnvs`）；**无需改 `full-run-probes.json`／`build-full-run-probes.py`**（登记本身没错）。
**两轮单点预验证**（均用 run-13 的 `ts-inputs.jsonl`、完整复刻注入表达式）：修复前并集 → 115 个变量、含 pbkdf2、`HashTest` **13 errors**（精确复现 run-13）；修复后 → **114 个变量、不含 pbkdf2、`Tests run: 30, Errors: 0, BUILD SUCCESS`** ✓。
**一处更正**：`tsInputEnvs`／`excludedTsInputEnvs` 写在 `java-capture-report.json`（非 `java-run.json`）；run-13 该报告实为 `tsInputEnvs: 115` + `excludedTsInputEnvs: [...]`，即「字段生效但并集旁路」。
**full-run-14 已就位**：`.cache/run-full-e2e.sh` 指向 `full-run-14-20260901`（90 分钟档 + 静默守卫；最后工具写入 05:35 → **05:46 自动开跑**），预计 ~07:00 出结果。

**full-run-13 结果：Java 阶段仍失败（20260901 09:40）**：`05:28:31` 结束 exit=1，`java-capture` 失败；`Tests run: 5444, Failures: 0, Errors: 13`，13 个错误仍是 `HashTest.passesPbkdf2Vector0..12` ✗ —— **上一处排除没有生效到实际注入链路**。
**主代理定位**：`grep -rln MIGRATION_HASH_PBKDF2_TS_INPUTS`（排除 `.cache/`）只剩 `capture-hash-pbkdf2-side.py`、**`full-run-probes.json`**、`run-full-java-capture.py` —— 分派表里仍登记着该变量（115 个 env 之一），全量 Java 阶段的注入很可能来自这里；且该轮 `java-run.json` 的 `tsInputEnvs` 长度为 0、`excludedTsInputEnvs` 为 None，与新增报告字段对不上。已要求代理先定位**真实注入链路**（`full-evidence-run.py` 的 stage env 构造／`full-run-probes.json` 的 `envs`／`build-full-run-probes.py`），在该点精确排除并做单点预验证，再开 `full-run-14`。

**full-run-13 进入 Java 阶段（20260901 09:15）**：TS 阶段（含 `AESGCM.man`）已完成并生成 `ts-run.json`；`java-*` 产物已出现（7 个），即一次无过滤 `clean test` 正在跑，预计 ~24 分钟（约 05:35 出总结果）。

**一行修复的预验证 + full-run-13 开跑（20260901 08:25）**：代理在改工具前先做**廉价预验证**——用汇总 `ts-inputs.jsonl`（排除该变量）单跑 `HashTest` → `Tests run: 30, Errors: 0, BUILD SUCCESS`（改前同路径 13 errors）✓；自检确认 `java_ts_input_envs()` 79→78、报告新增 `excludedTsInputEnvs`。**`full-run-13` 已由 cron 于 04:19:01 启动**（`.cache/run-full-e2e.sh` 带 `.started` 守卫 + **10 分钟静默窗口守卫**：任务侧 `.py/.cjs/.mjs/.sh` 近 10 分钟无改动且工作树干净才开跑——04:10 那次 tick 正确推迟）。预计 ~70 分钟（约 05:30）出结果。

**full-run-12 stage 结果（20260901 08:10）**：`ts-capture` **exit=0／2763 秒**（133/133 文件、5329/5329 用例、38092 输入、56744 断言、`problems=[]`）✓；`java-capture` **exit=1／1425 秒**——无过滤 `clean test` 得 `Tests run 5444, Failures 0, Errors 13, Skipped 0`，13 个错误全部来自 `HashTest` 的 PBKDF2 向量 ✗。总耗时 4189 秒（70 分钟），**90 分钟档有约 20 分钟余量，不需要 180 档**。

**根因（已定位到行）**：`HashPbkdf2InputReplay.load()`（冻结 SDK 测试代码）要求这 13 个用例 `sampleId == "call-0"`，而汇总计划用的是标准局部 `hash` 的口径 **`pbkdf2-01`** → `IllegalStateException: PBKDF2 固定 TS 输入缺失或重复：0`。逐局部全绿是因为该 replay 仅在 `MIGRATION_HASH_PBKDF2_TS_INPUTS` **被设置**时才消费语料（逐局部从不设置它，属**已退役局部** `hash-pbkdf2-vectors` 的遗留变量）；全量必炸是因为 `run-full-java-capture.py::java_ts_input_envs()` 会把 Java 源码里出现的**全部** `MIGRATION_*_TS_INPUTS` 指向本轮汇总输入，从而激活这个休眠变量。该变量全仓仅被 `HashPbkdf2InputReplay.java` 读取；同一批样本由 `HashTest` 主路径按 `pbkdf2-01` 正常产出（`java-inputs.jsonl` 有该行）→ **不设它不丢证据**，而喂 `call-0` 会产生计划外样本被 `evidence-bundle` 拒。

**已批准一行修复（任务侧）**：在 `run-full-java-capture.py` 的全局覆盖里**精确排除**该变量，并在返回值与报告里记录被排除项（`tsInputEnvs` 79 → 78 + `excludedTsInputEnvs`）。改完重新冻结 → 跑 `full-run-13`（90 分钟档）→ `verify` + 两套审计。

**e2e 复跑越过关键节点（20260901 07:50）**：`full-run-12` 的 **TS 阶段已完成**（含 `aesgcm-man`，154/154），已生成 `java-capture.log`／`java-inputs.jsonl`／`java-maven.log`／`java-run.json` → **Java 阶段（一次无过滤 `clean test`）正在跑**，预计 10–20 分钟。这已越过上次失败的 `producerSha256` 检查点 ✓。

**e2e 复跑已启动（20260901 07:15）**：工具集自 02:22:30 起**无任何任务侧 `.py/.cjs/.sh` 变动**（已用 `find -newermt` 核验为空 ✓），路径 B 的 `full-evidence-run.py run` 已拉起（`.cache/evidence/full-run-12.log`、`full-run-12.started`、pid 2046286）。路径 A 代理已结束并静默待命，其 8 项收尾与 `script-spend-shared-vectors` 探针共存缺陷（`jest.doMock` 争用 + `restoreAllMocks` 误伤）已定位为备用方案。

**路径 A 自测结果（备用路径有效证据，20260901 07:05）**：`selftest-all-20261001`（132 文件，除 `AESGCM.man`）**跑完**——jest **132 suites／5328 tests／0 失败**、**unmapped-files = 0**、**缺失原始轨迹 = 0**（探针装载与轨迹产出两类根因已消除）、标准断言轨迹裁剪 56648 行且手动重跑 `emit-assertion-observations.py` 退出码 0 ✓。仍待收尾 **8 个输入转换器**：`auth-fetch-property`、`utils-property`（缺 FAST_CHECK 固定与内联折算）、`reader`／`reader-uint8array`／`writer`／`writer-uint8array`（四者共用 374 行轨迹，需按 `source.file` 过滤）、`wallet-wire`（并发 OOM 特征）、**`script-spend-shared-vectors`（真实缺陷：`dc69e1c2…` 属 `Spend.test.ts` 且该文件已跑，报 0 vs 1 → Script／Spend 两探针共存时漏记，需专项定位）**。
**协调结果**：路径 A 已从 **02:22:30** 起停止一切任务侧写入并静默待命（不跑 jest／Maven）；**路径 B 在冻结工具集上独占复跑 e2e**（先自查 02:22:30 后无任务侧工具变动再开跑）。

### 操作红线（新增，代价 51 分钟）：e2e 前必须冻结「SDK 源码 + 任务侧工具」

**20260901 02:51 的失败**：路径 B 的 e2e（02:00 cron 拉起，已跑到 TS 阶段末）被判 `{"status": "FAIL", "reason": "当前源码、工具或清单与本轮来源不同：producerSha256"}` ✗。
**根因**：`full-evidence-run.py::producers()` 会哈希**全部任务侧 `.py`／`.cjs`／`.mjs`／`.sh` 文件**（不只是 SDK 源码），而路径 A 的代理在同一时段仍在编辑 `run-full-ts-capture.py`／`full-emit*.py`／`full-run-overrides.json`／`build-full-run-probes.py` → 在飞运行作废。
**红线（后续必须遵守）**：
1. 启动 `full-evidence-run.py run` 前，**SDK 源码与任务侧工具都必须冻结**（两路代理都停笔）；
2. 运行期间只允许写 `.cache/` 下的运行产物（不在 `producers()` 范围）；
3. 任何一处工具改动都会让整轮 e2e 白跑（本轮代价 51 分钟）。
**已采取动作**：已要求路径 A 立即停止写入、先跑完它自己的严格自测并报结果；已要求路径 B 暂不重跑，等工具集冻结后再开。

**路径 A 也打通了（20260901 06:40）**：机制五类根因全部修好（探针装载 `envOverrides` + `<runDir>/plans/<local>/`；`full-run-overrides.json` + `full-emit.py`／`full-emit-inline.py`／`full-emit-special.py`／`full-emit-hex-bn.py`；只有真替换 `global.expect` 的 hex-bn 走自产断言 sidecar，其余回共享轨迹 + 标准转换器并按“计划内原文件”裁剪；`capture-wallet-wire-parity.cjs` 从分派表移除以消除双重记录；`transaction` 加 `probePlan`；fast-check 固定种子；per-local 轨迹按 `source.file` 过滤）。已验证子集：Chronicle+KeyDeriver `problems=0`；39 个旧管线局部 jest **3613/3613**、输入 13642 行；`hex-bn` **71 样本 + 71 断言与冻结计划完全一致**。**全量 133 文件严格自测已启动**（`.cache/evidence/selftest-full-20261001`，无 `--allow-unresolved`）。
**两路并行现状**：路径 B 的 e2e（`full-run-11-20260901`）TS 阶段 153/154、在跑 `aesgcm-man`；路径 A 的全量严格自测在跑。**以先到者为准**，另一路保留作交叉验证。

**e2e 进度（20260901 06:35）**：TS 阶段 **136/154 局部 passed**（446 秒），剩余含 `aesgcm-man`（42 分钟）→ TS 约 03:00 结束，随后 Java 一次无过滤 `clean test`。

**e2e 进度（20260901 06:25）**：已生成 **121/154** 个局部子目录，进程存活 ✓，仍在 TS 串行阶段。

**e2e 进度（20260901 06:15）**：cron 于 02:00:01 拉起，`full-evidence-run.py run --run-dir .cache/evidence/full-run-11-20260901`（90 分钟档）；`full-run.json`／`input-plan.json`／`preflight.json`／`local/` 已生成，串行 driver 正在逐局部采集。预计 TS ~02:50 结束、之后 Java 一次无过滤 `clean test`（~10–20 分钟）→ ~03:10 出 stage 结果。

**全量 TS 证据已完备，e2e 正在跑（20260901 06:05）——卡点解除**

路径 B（逐局部串行采集后合并）已交付并验证，两条证据全过：

1. **154/154 局部通过**（`.cache/evidence/ts-serial-full-20260901`，`--resume` 补齐 `utils-property`／`auth-fetch-property` 后 `--verify-only` 全量复核）：
   `localsFailed=[]`、**`filesCovered 133/133`**、**`casesCovered 5329/5329`**、`inputsWritten 38092`、`assertionsWritten 56744`、`missingCases=0`、`missingSamples=0`、`problems=[]`；形态分布 standard 107／adapter 27／direct 18／vector 2。
2. **driver 内置 `compare_ts` 自检通过**（与最终门禁同一函数）：`{"files": 133, "cases": 5329}`、`jestFiles 133`、`jestTests 5329`；`crossCheck = {localsChecked: 117, skippedCustomConversion: 7, failures: []}`。
   顺带修掉真缺口：旧管线 `hex-bn` 用 `--kind both` 产两份 Jest 报告，而 `capture-legacy-side.py` 只在 Java 分支合并 → TS 分支漏合，`BigNumber.constructor.test.ts` 进不了报告；driver 现收全部 `ts-jest*.json` 按文件去重合并（未改该适配器）。

**配置切换已应用**（`full-evidence-locals.json` 仅 1 行）：`fullRun.tsCommand[1]`：`run-full-ts-capture.py` → **`run-full-ts-serial.py`**；`locals`／`retired`／`tsReports`／`javaCommand`／`javaReports` 逐字段未变；`full-evidence-preflight.py` 报 `readyForFullCapture=true`，`full-evidence-run.py::frozen()` 通过（133 文件／5329 用例，`javaRevision 13f3416…` = 窗口 v2 同源）。

**e2e 现状**：cron 于 02:00:01 拉起 `full-evidence-run.py run --run-dir .cache/evidence/full-run-11-20260901`（日志 `.cache/evidence/full-run-11.log`，90 分钟档）；TS 阶段已过 68/154，`input-plan.json` 与登记计划 5329 用例逐项同序相同。预计 TS ~50 分钟（含 `aesgcm-man` 实测 2524.5 秒）+ Java 一次无过滤 `clean test`；若被上限终止，其 manifest 即 180 分钟档所需的真实超时证据。

**诚实性口径（写进结项说明）**：全量运行的 TS 侧是**逐局部串行真实采集后合并**（同一运行目录、同一来源 `13f34162199d`、逐用例双侧同输入），**不是**单进程单次运行；`fullRun.tsCommand` 如实记录为 `run-full-ts-serial.py`。

**接手动作（按序）**

1. 等 v6 结束；若因 90 分钟上限被终止（`elapsedSeconds ≥ 90*60`），立刻用 180 分钟档重跑（协议要求引用真实超时的 manifest）：
   `python3 full-evidence-run.py run --run-dir .cache/evidence/full-run-7-20260901 --timeout-minutes 180 --retry-after .cache/evidence/full-run-9-20260901/full-run.json`
2. 校验：`python3 full-evidence-run.py verify .cache/evidence/full-run-<n>-20260930/full-run.json`
3. 接口面：`node audit-api.cjs check`
4. 逐事项复核：`./close-items.sh <标签>`（14 项已过；其余随全量运行）
5. 结项：把剩余 4 个实现事项（`script-spend`、`script-vectors`、`transaction-complete`、`auth-transport`）与 8 个总门禁写入 `feature_list.json`，并同步 `progress.md`。

**已知风险与注意**

- 全量 parity 轨迹 **805 MB**（4 行 126–252MB：个别用例把大数组逐元素写进断言轨迹）。`capture-broadcaster-inputs.cjs` 已改**分块扫描**（原 `readFileSync(...,'utf8')` 撞 V8 字符串上限，会让 ts-capture 整阶段失败）。
- `AESGCM.man.test.ts` 单次 TS 运行 **66 分钟**（窗口内已通过；全量运行同样会跑到）。
- 90→180 分钟协议：`--timeout-minutes 180` 必须引用一次**真实被 90 分钟上限终止**的运行。
- **严禁**在窗口／全量运行期间改 SDK 源码：`audit-tests.java_revision()` 哈希全部 tracked+untracked 文件，任何改动都会让 107 个局部与全量证据作废。
- 改 `module-scope.json` 必须同步 `module-tests.json` 的 `scopeSha256`（该字段即 `digest(module-scope.json)`）；`scopeReview` 已于提交 `093a2b2` 置 `reviewed`。

**工具速查**：`lock.sh`（所有 Maven／采集前置）、`recapture-all.sh`（逐局部重采 + 篡改门禁）、`final-window-guard.sh`（开窗六项守卫）、`close-items.sh`（逐事项任务级对照）、`full-evidence-run.py run|verify`（单次全量）、`audit-tests.py check`、`audit-api.cjs check`、`full-evidence-preflight.py`。

**零冲突约定（20260901 11:50 已批准）**：A1 只新建自包含的 `java-vector-inputs.py`，预验证走等价外层包装，**暂不动** `run-full-java-capture.py`；等 A2 停笔后由 A1 一方统一加两行接线（设 `MIGRATION_VECTOR_JAVA_INPUTS` + Maven 后调该脚本）。A2 若发现必须在同一文件改，须先停下问主代理。

**B 的新洞察**：839 MB 里 **4 行占 795 MB**（单行 264.8／264.8／132.4／132.4 MB，行号 962–965），即**单行 JSON 反序列化本身就是主要内存峰值** → 只把 `read_text().splitlines()` 换逐行读不够。已要求代理：①先实测单行解析峰值再设计；②若绕过巨行反序列化，**必须保持与比较层口径一致**（用 `test-audit.test.cjs`／`test-evidence-semantics.py` + 一次真跑证明，禁止“OOM 消失但审计不过”的假通过）；③优先对齐既有「大数组记 `{length, sha256}` + 逐字节见证」约定（`aesgcm-man`／`wallet-wire` 有先例），不得擅改计划/比较层口径。

**full-run-15 结果：Java 阶段新缺陷（20260901 13:10）** —— `08:59:15` 结束 exit=1，失败在 **`java-capture`**（不是 bundle）。
`java-maven.log` 报 `BUILD FAILURE`／surefire 阶段，唯一失败类 **`com.metanet4j.bsv.primitives.AESGCMManualTest`**（`Tests run: 885` 即止）；因 Maven 早退，`vectorInputs` 跳过、`assertions.error` 非空、`full-java-serial-convert.py` 也失败。
该用例在**逐局部**（窗口 v2）与 **TS 侧全量**（42 分钟）都通过 → 属「全量 Java 阶段」下的**资源/环境**问题（512 MB 大数组，疑 heap 或超时），**不是接线错误**。
已交 A2：①先诊断该类真实异常（读 `metanet4j-bsv-sdk/target/surefire-reports/` 下该类报告；对照该局部逐局部 recipe 是否本来带堆参数），给最小任务侧修法（例如全量 Java 阶段补 `MAVEN_OPTS`／`-DargLine`），**不改 SDK 源码**，我确认后再动；②第 7 例 TS 接线；③`known-gaps.json` 登记 + 三条自测；④预验证后跑 `full-run-16` 并交付两套审计与 `knownUnroutableCases` 计数。

**用户裁决：6 例记为已知缺口（20260901 13:00）** —— 胡先生选择「记为已知缺口并如实披露」，**不重新冻结 SDK**（补齐那 6 例需新增 300+ 行 `AuthFetchPeerInputReplay.java` 并接线 6 个 `@Test` → 会改 `java_revision` → 窗口 v2 的 106 个同源局部与 14 项 task-parity 全部重跑）。

**A2 只读排查的三条硬结论（已核实，不得当作口径问题绕过）**：
1. `specialized-local` 只豁免**逐局部来源校验**（`recapture-local.py:27`／`local-evidence-gate.py:45`／`recapture-all.sh:17`／`full-evidence-preflight.py:161`），**不免**「全量计划逐用例双侧同输入」——`evidence-bundle.py:83` 用冻结清单全量比对（`:59` fail），`:96-106` 还要求 sampleId 序列与逐字节同值 → **这 7 例是真缺口**。
2. 6 个 peer 例在**全部 evidence 里 0 个 Java 产物**（只在 TS 产物里出现），无可并入之物；第 7 例有 2 份旧产物但 `javaRevision` 为旧值且 manifest 旧格式，`evidence-bundle.py:186` 要求行内 `runId` 等于本轮 manifest → **搬旧行必被拒**（绕过即伪造）。
3. 第 7 例只需 **TS 侧**接线（把 peer 探针并入该局部本轮 TS 汇总），不动 SDK、只需重跑该局部 TS + 一轮全量。

**已交办（A2 代理）**：①等 `full-run-15` 结束后做第 7 例 TS 接线（最小追加，落在 `run-full-ts-serial.py`／`ts-serial-entries.json`）；②新增 `known-gaps.json` 显式登记 6 例（caseId／局部／`ruleId`（拟 `frozen-test-without-replay-entry-v1`）／原因／证据指针／「补齐需要什么」），让 `evidence-bundle.py` 与 `audit-tests.py` **只读该登记**把其记为 `knownUnroutableCases` 并在每份报告/manifest 里**显式可见**，**不得放宽其它任何校验**（登记外缺口仍硬失败，禁止自由文本理由），并加三条自测（命中通过／登记外仍失败／篡改登记失败）；③随后 `full-run-16`（90 分钟档）并给出 stage + `verify` + `audit-tests.py check` + `audit-api.cjs check` + `knownUnroutableCases` 实际计数（期望 6）。

**A2 收尾完成、三组接线全部落地（20260901 12:40）**：

- **改了 4 个文件**：`run-full-java-capture.py`（唯一注入点，最后写入 07:35）—— A1 两行、wallet-wire 4 项**一起**注入（注释写明“只给一半”的两种退化）、A2 的 33 个 `-Dmigration.*` + 4 个自有 env、Maven 后 `full-java-serial-convert.py` 产标准行，并加运行期前置校验（引用文件存在／语料 javaMethod 不重叠／语料 sampleId 与 `input-plan.json` 逐项一致，不符则在 Maven 前中止）；`EXCLUDED_TS_INPUT_ENVS` 未动。新增 `build-java-serial-entries.py` + `java-serial-entries.json`（**36 局部／736 例**，`--check upToDate=true`）、`full-java-serial-convert.py`、`verify-java-serial.py`、报告文档。
- **聚焦验证三轮全绿**：focus1（5 类）`Tests run: 400, Failures: 0, Errors: 0`，147+82+62+39+70 例全部有输入、`sampleIdMismatchAgainstFrozenPlan=0`、`problems=[]`；focus2（2 类）✓；focus3（向量四类）**2599/2599 例／9445 行**、`problems=[]`。wallet-wire 硬指标：raw 轨迹 **377 KB**、见证 **33.56 MB／4 条**。
- **两项发现**：①emit 的 OOM 由 wallet-wire recipe 顺带解决（原始轨迹 800.2 MB → 约 43 MB，其中 757.5 MB 是那 4 条巨行）；②`migration.parity.largeArrays=true` 是 **JVM 级全局开关**，会误伤 2 条断言（`PushDropTest#passesVariousTestVectors#37` 70000 B、`TransactionPerformanceTest#deepSourceGraph` 186101 B）→ 处置：`repair_digest_actuals()` 做**验证性还原**（仅当 TS 同 `(caseId, assertionId)` 按字节重算的 length+sha256 完全一致才替换，否则保留并记 `problems`），已做正/反向验证。**主代理已批准保留**，并要求在最终报告写明判据与双向验证、`problems` 非空必须在 manifest 可见。
- **缺口收敛**：3342 例中 **3335 例已接通**（A1 2599 + A2 736）。**剩 7 例**：`auth-fetch-peer` 6 例（`AuthFetchPeerTest` 无任何输入重放入口，全 evidence 无这些 caseId 的 java-inputs 记录）+ `auth-fetch-known-txids` 1 例（TS 侧聚合缺口：该用例只有 `AuthFetch.knownTxidsInput` 行，replay 要 `knownTxidsPeerInput`）。已要求 A2 **只读**排查三问（是否属 `specialized-local` 而本不该要求／是否已有逐局部 Java 产物可合法并入／若必须改冻结 SDK 测试源码则给最小改动），由主代理决定。
- **`full-run-15` 已就绪**：`.cache/run-full-e2e.sh` 已改指 `full-run-15-20260901`（90 分钟档 + 静默守卫），crontab 已装；最后工具写入 07:35 → 守卫将在 ~07:46 后自动开跑。

**三项收尾的最新结论（20260901 12:20）**：

- **B 不是发射器问题**：4 条巨行全部来自 `WalletWireIntegrationTest#preservesLargeTypedBeef`（各 132 MB／3300 万元素的 typed array，解析峰值实测 2.88 GB/行）。逐局部早有约定：大数组记 `{length, sha256}` + 逐字节见证落 `java-large-actuals.jsonl`（`wallet-wire` 局部 raw 仅 0.1 MB、见证 33.6 MB）；全量没走这条约定，是因为 **Java 侧重放的开关键没打开**。已预验证 4 项 recipe（`MIGRATION_WALLET_WIRE_ASSERTION_INDEX` + `MIGRATION_WALLET_WIRE_JAVA_LARGE_ACTUALS` + `-Dmigration.walletWire.plan=…` + `-Dmigration.parity.largeArrays=true`）→ `WalletWireIntegrationTest` **82/0/0**、raw **0.12 MB**、见证 **33.56 MB**、该局部 82 例输入一并补齐。**四项必须同给**：只给 flag 不给 plan，raw 会变小但见证不产出。
- **A1 已完成并预验证**：新增自包含 `java-vector-inputs.py`（口径与 `normalize()` 逐字段一致）；4 个向量类一次跑齐 **2599/0/0** → `rowsAppended 9445`、`script-spend-shared-vectors 1940/1940`、`transaction-shared-vectors 659/659`、`unknownTests 0`、`problems []`。
- **接线方式（已定，采纳代理建议 (b)）**：三组线（A1 两行 + wallet-wire 4 项 + A2 自身 34 类）**全部由 A2 代理一次写入** `run-full-java-capture.py`（单一写者，最干净）；路径 B 代理已停手、不再改该文件。
- **收尾顺序**：A2 三组接线 + 聚焦验证 → 两路静默 10 分钟 → 带静默守卫的 cron 放行 **`full-run-15`**（90 分钟档，TS ~46 min + Java ~24 min）→ `verify` + `audit-tests.py check` + `node audit-api.cjs check`。

### full-run-14 精确读数与三项收尾分工（20260901 11:40，以此为准）

代理用流式统计更正了我此前的读数（`evidence-bundle.py::same()` 只打印缺失集合的前 4 个做示例，所以“4 个用例”是假象）：

| 项 | 计划 | 覆盖 | 缺失 |
| --- | --- | --- | --- |
| Java **输入**用例 | 5329 | 1987 | **3342**（78% 是向量四类：`ScriptVectorsTest` 1030／`TransactionCompleteVectorsTest` 659／`SpendValidVectorsTest` 455／`SpendStandaloneValidVectorsTest` 455）|
| Java **断言**用例 | 5329 | 124 | **5205**（`emit-assertion-observations.py` 解析 839 MB 原始轨迹时被 OOM 杀，kernel log `06:54:12` 确认）|

完整 3342 个缺失 caseId 已落盘 `.cache/evidence/full-run-14-20260901/missing-java-input-cases.json`。

**三项分工**：**B**＝断言发射改流式（独立、有界，代理先做，用现成自测 + run-14 的 839 MB 轨迹单点验证）；**A1**＝向量四类 2599 例（设 `MIGRATION_VECTOR_JAVA_INPUTS` + 调两个证据脚本的 `normalize`）；**A2**＝其余 34 类 743 例（各读自己的 `-Dmigration.*` 属性或自有 env，见 `java-capture-report.json` 的 `propertyDrivenReplays`）→ 已另派专代理建「局部→Java 入口」映射表。
三项齐活、两路都停笔、工具集重新冻结后，才统一放行 `full-run-15`（一次约 70 分钟）。

## 并行路线（20260929）

`python3 item-readiness.py` 给出各事项的冻结用例／已计划／当前来源复核与缺计划文件；据此排的后续分工：

| 子代理 | 当前 | 下一步（依赖满足后） |
| --- | --- | --- |
| SA2 | HTTPWalletWire 46 + window.CWI 31 | wallet-client 100（3 文件全无计划） |
| SA3 | transaction-beef 83 | script-templates 17 → script-spend 缺 91 |
| SA4 | Signature 36 + AESGCM 30 + ReductionContext 29 | transaction-verification 53 或 auth-sessions 85 |
| SA5 | HD 49 + Script 39 + Hash 17 | script-vectors 缺 26 → transaction-complete 缺 86 |
| 主代理 | 协调、验收、提交、统一重采 | auth-transport 缺 49；最终全量门禁 |

依赖链：beef → script-templates → script-spend → script-vectors → transaction-complete → transaction-verification；wallet-wire + wallet-hosts → wallet-client → auth-sessions → auth-transport。

已知残留风险：`prepare-transaction-local.py` 的 `loopSamples` 采用“该用例入口样本”做结构覆盖（与 bn-arithmetic 登记方式一致），最终全量门禁若对循环样本有更严要求，需要按站点补真实循环样本。

## 本轮交付（20260929 晚）

- `http-wallet-wire` 已完成：46 例／126 输入／51 断言，recapture／tamper（两个 true）／gate verify 全绿，带冻结语料的聚焦 Java 测试 46/46 逐字段一致。钱包宿主与 WalletWire 事项的冻结用例已全部有标准局部（wallet-wire 82 + http-wallet-wire 46 = 128），待静默窗口统一重采后出任务级对照并结项。
- `window-cwi` 的 TS 探针、冻结（31 例／60 输入／61 断言）与带语料聚焦测试 31/31 已通过，仅剩正式双侧采集。
- `hd` 49 例／227 样本／92 断言、`script` 39/99/96、`hash` 30/150/92 计划已冻结并登记，正在采集。
- 编译阻塞已清除：`ScriptInputReplay`（6 处 `List.of` 包成 `Arguments` lambda + 2 处 `action.run()`）、`HDInputReplay`、`HashInputReplay`（泛型放宽为 `List<?>` 并保留 Number 校验）修复后 `test-compile` 5437 源文件编译成功。

## 证据完整性复查（20260929）

对 13 个已登记标准局部逐个复跑 `local-evidence-gate.py verify`，全部与登记时一致、无损坏：交易基础五局部 74 例/150 输入/115 断言、广播器四局部 68/231/169、钱包宿主与 WalletWire 三局部 177/542/526，合计 319 个用例的既有证据可用。

## 全量运行接口

最终 `audit-tests.py check` 需要 `full-evidence-locals.json` 的 `fullRun.tsCommand/javaCommand/tsReports/javaReports`：TS 侧由一个按 `testPath` 分派探针的 `capture-full-dispatch.cjs` 在一次 Jest 运行里覆盖全部原文件，Java 侧用无过滤 `clean test` 并把全部 `MIGRATION_*_TS_INPUTS` 指向本轮汇总输入。该接口由基础设施子代理实现，完成后 `full-evidence-preflight.py` 的 `missingFullRunInterfaces` 应为空；覆盖率补齐后再跑单次双侧全量采集。

## 第三波（已派发）

SA9：`locking-unlocking-script` 12 例、`script-additional` 14 例、`binary-fetch-client` 12 例、`bignumber-additional` 19 例（合计 57 例），用独立登记表 `misc-locals.py` + `prepare-misc-local.py` + `capture-misc-local.py`，避免与在跑的四个登记表冲突。

## 第二波分工（待第一波交付后派发）

各子代理完成后**不要闲置**：按下列批次用 `send_message` 续派（保持同一子代理的管线上下文最省事）。

| 批次 | 事项 | 文件（未计划例数） | 备注 |
| --- | --- | --- | --- |
| B1 | wallet-client（100） | WalletClient.substrate(38)、WalletClient.additional(61)、WalletClient(1) | 依赖 wallet-wire／wallet-hosts 结项 |
| B2 | auth-sessions（85） | Peer(30)、Peer.certificatePolicy(15)、Peer.boundary(2)、SessionManager(11)、build(20)、cryptononce(7) | 依赖 wallet-client |
| B3 | auth-transport（49） | SimplifiedFetchTransport.additional(46)、SimplifiedFetchTransport(3) | 依赖 auth-sessions |
| B4 | script-spend（91） | Spend.additional(69)、Spend(20)、SpendComplex(1)、Spend.codeseparator(1) | 455 例已有旧局部 |
| B5 | script-vectors（26） | NormativeVectors(9)、Spend.verifier(9)、lrshiftnum(4)、Chronicle(3)、SpendValildVectors(1) | 529 例已计划 |
| B6 | transaction-complete（86） | Transaction.test(61)、Transaction.performance(25) | 659 例已计划 |
| B7 | script-model（65） | Script.test(39，进行中)、Script.additional(14)、LockingUnlockingScript(12) | — |
| B8 | curve（38）／bignumber（50）／keys-signatures（73）／symmetric（22）／hash-random（39）／compat（9） | Curve.unit(18)、Curve.additional(20)、BigNumber.additional(19)、ReductionContext(29，进行中)、PublicKey(14)、PublicKey.additional(32)、ECDSA(15)、Schnorr(12)、SymmetricKey(15)、Hash(17，进行中)、ECIES(9) | 已完成事项的补强 |

## 全量探针映射的三类权威来源（20260929 核实）

`build-full-run-probes.py` 生成 `full-run-probes.json` 后仍有 46 个局部未解析，来源如下：

1. **直写型 16 个**（`auth-fetch-additional-*`／`auth-fetch-primary-*`，`specialized-local` + `deriveCatalogFromPlan`）：探针与局部同名 `capture-<局部名>.cjs`，自己写 `EVIDENCE_*` 最终行，无需额外变量；原文件由该局部 `input_plan` 的 caseId 反查。
2. **适配器 replay 型 17 个**（arc-*、broadcaster、cached-keyderiver、fee-model、http-wallet-json、keyderiver、protowallet*、mnemonic*、wallet-property、werr-constructors、三类字节编码、validation-helpers、origin-header5、drbg29 等）：探针与语料变量都在适配器 TS 分支的 `env[...] = ...` 里；raw 型还需复用适配器里的 `prepare-*-inputs.py emit-ts` 转换。
3. **命名不规则的 13 个**：权威来源是该局部的 `*-local-gate.py`（含探针、catalog／plan 与期望报告），逐个取用；确实没有可复用探针的必须在严格模式下报错，不得猜测。

`run-full-ts-capture.py` 需要采集后校验：所有原始轨迹存在且非空、raw 型转换成功，任一缺失即整轮非零退出（防止“跑完但没有输入”的假绿）。

### 统一窗口待执行清单（代理已交付）

- **window-cwi**（代码侧就绪，已证明 TS 探针 31/31、带语料 Java 31/31 且输入逐字段一致）：`./lock.sh python3 recapture-local.py --name window-cwi --run .cache/evidence/window-cwi-standard-<新目录> --update` → `./lock.sh python3 local-evidence-gate.py tamper --name window-cwi` → 聚焦 `clean test -Dtest=WindowCWISubstrateTest,HTTPWalletWireTest` → `full-evidence-preflight.py`。可选反向验证：改冻结语料里 `getVersion` 的返回值应立刻报“Java 实际 window.CWI 入口或结果与固定 TS 不同”。
- **http-wallet-wire**：四项已绿（46/126/51、tamper 两个 true、verify 退出 0）；统一窗口会一并刷新。
- **transaction-signature-additional**：`ParityRecorder` 修复后重采被他人编译错误挡住，留待统一窗口（修复本身已在聚焦运行中验证 65/65）。

### 本轮修复验证

`324d3c3`（SDK）：恢复普通对象浅表示 + 新增 `recordJsMapDefined`/`assertDefinedJsMap`；聚焦运行 `RecordingAssertionsSemanticsTest` 21/21、`TransactionSignatureAdditionalTest` 24/24、`TransactionAdditionalTest` 20/20，合计 65/65 BUILD SUCCESS。

### 本轮进展（20260929 深夜）

- **已采集并通过 verify+tamper 的局部**：`hd` 49/227/92、`push-drop` 6/151/85、`transaction-evidence` 4/12/12、`transaction-verifier` 15/35/30、`script` 39/99/96、`beef-party-additional` 3/73/7、`merkle-path` 25/125/63、`merkle-path-safe-offsets` 21/87/70、`merkle-path-bench` 13/2643/1290。
- **已交付但待采**：`window-cwi` 31/60/61、`hash` 30/150/92、`p2pkh-async-backend` 2/10/2、`r-puzzle` 9/17/9、`aesgcm` 30/457/334、`signature` 36/51/46、`reduction-context` 29/38/70、keys 六局部 97/223/134、misc 四局部 57/134/106、`chronicle-opcodes` 74/154/77、`simplified-fetch-transport-additional` 46/89/68；上一批失败均为**他人编译错误**或“采集期间源码变化”，不是内容不符。
- **两个生产缺陷已修**（SDK 仓 `d5c3f42` + 前一提交 `Signature.toCompact`）：① `Utils.toArray` 缺 BigNumber 类数组分支、② `Hash.bytes` 把 BigNumber 当空输入（此前 `sha256(BigNumber)` == `sha256("")`，使 RFC6979 签名与固定 TS 不同）。新增 `UtilsBigNumberArrayRegressionTest`（2 例，额外 Java 回归）。聚焦验证 97/97。
- **唯一在跑的代码缺口**：`beef`（Beef.test.ts，21 例）已派新代理接手；`BeefTest` 同时承载 `Transaction.test.ts` 用例，要求先出探针与计划、再一次性重写并保持既有断言与映射身份。

### 本轮批量采集结果（13 个局部 / 270 例 / 785 断言，来源 `00f91838`）

aesgcm 30/457/334、signature 36/51/46、reduction-context 29/38/70、hash 30/150/92、window-cwi 31/60/61、public-key 14/34/18、public-key-additional 32/48/47、locking-unlocking-script 12/29/14、script-additional 14/37/30、binary-fetch-client 12/13/25、bignumber-additional 19/55/37、r-puzzle 9/17/9、p2pkh-async-backend 2/10/2 —— 全部 verify + tamper 通过。

修掉两处适配器缺陷：`capture-keys-local.py`／`capture-gap-local.py` 误调 `prepare-transaction-local.py`（改用各自登记表的 prepare），以及 `sfta` 计划目录名不含局部名导致反查失败（已重命名为 `<局部>-plan-<日期>` 并重新登记）。

**仍待采集 6 个**：ecdsa、schnorr、symmetric-key、ecies、chronicle-opcodes、simplified-fetch-transport-additional —— 本轮失败均因 `beef` 代理正在书写 `BeefInputReplay.java` 导致模块编译中断（非内容问题），随最终窗口一并重采。

### 结项映射与剩余缺口（`item-locals.json`）

由登记表与冻结用例自动算出“事项 → 覆盖它的局部”。**计划覆盖已完整、可在最终窗口后直接结项的**：`wallet-wire` 128 例／2 局部、`wallet-hosts` 126／3、`transaction-verification` 53／3、`script-templates` 17／3。

**仍有未计划用例的事项（共约 565 例，交给下一波代理）**：wallet-client 100、script-spend 91、transaction-complete 86、auth-sessions 85、http-chain 47、curve 38、keys-signatures 37、script-vectors 26、hash-random 22、transaction-beef 21（beef 在做）、symmetric 7、auth-transport 3、bignumber 2。

### 证据完整性复检（20260930 凌晨）

对 24 个最近采集的标准局部逐个复跑 `local-evidence-gate.py verify`（不跑 Maven、不占共享锁）：**24/24 通过**，覆盖 hash、window-cwi、r-puzzle、p2pkh-async-backend、aesgcm、signature、reduction-context、public-key、public-key-additional、locking-unlocking-script、script-additional、binary-fetch-client、bignumber-additional、ecdsa、schnorr、hd、script、push-drop、transaction-evidence、transaction-verifier、beef-party-additional、merkle-path、merkle-path-safe-offsets、merkle-path-bench。它们绑定不同 Java 来源（并行改动所致），最终窗口统一重采后即可全部 `currentCaptureVerified=true`。

### hex-bn 收尾（方案①，20260930 02:20）

- 给 `build-full-run-probes.py` 增加 **`full-run-overrides.json` 覆盖机制**（合并 files 探针、把 resolvedLocals 从 unresolved 移除）；
- 新增 `full-run-overrides.json`：为 `hex.test.ts`（探针 `capture-hex.cjs`）与 `BigNumber.constructor.test.ts`（`capture-bn-constructor.cjs`）登记输出环境变量，并在 hex 探针上挂 emit：`prepare-hex-bn-inputs.py emit-ts --kind both --raw-hex {runDir}/hex.raw.jsonl --raw-bn {runDir}/bn.raw.jsonl --inputs {output} --assertions {runDir}/ts-assertions.jsonl`（断言由 legacy 转换器直接写入本轮断言文件；这些探针不加载 `capture-parity`，标准断言发射器会因“没有原始断言轨迹”跳过，不会互相覆盖）；
- `prepare-hex-bn-inputs.py` 的 `--run-id` 改为可缺省（回退 `EVIDENCE_RUN_ID`），因为全量分派表只替换 `{runDir}`／`{local}`／`{output}`；
- **分派表现状：110 原文件／125 探针／90 环境变量，`unresolved=0`，无探针原文件 23 个（均为尚未计划的代理在飞范围）**。
- 待办：在锁空闲时用 `run-full-ts-capture.py` 做一次只含这两个文件的子集自测（`--files` + `--allow-unresolved`），确认 emit 与断言落地格式正确。

### 全量分派表收敛（20260930 02:10）

- `public-key`／`public-key-additional` 两个局部此前不在全量分派表里（探针用变量索引读 `process.env[...]`，静态扫描识别不到）。按既有约定在各自探针头部加了一行字面量声明（`process.env.MIGRATION_PUBLIC_KEY[_ADDITIONAL]_TS_OBSERVATIONS`）后已正确解析。
- 分派表现状：**108 个原文件／123 个探针／90 个环境变量，未解析仅剩 `hex-bn`**；无探针原文件 25 个（286 例）。
- **关键风险清单**：无探针原文件里只有 **36 例是“已计划但全量运行拿不到输入”**——即 `hex-bn` 旧管线覆盖的 `BigNumber.constructor.test.ts` 28 例 + `hex.test.ts` 8 例；其余 250 例尚未计划（正在收口的代理会补）。
- `hex-bn` 收尾两选一：①给 `build-full-run-probes.py` 加 `full-run-overrides.json` 覆盖机制，并让该局部的探针改为同时喂 `capture-parity`（断言交给标准发射器），legacy 转换器只产输入；②在分派表里为该局部登记“direct 模式 + 自定义 emit”，并让 run-full-ts-capture 支持 emit 写 sidecar 断言后合并。二者都要在锁空闲时实测。

### 全量运行 ts-capture 失败定位与修复（20260901 01:30）

90 分钟档运行在 ~55 分钟时提前失败：`完整运行阶段失败：ts-capture`，jest 计数 132 PASS / **2 FAIL**，唯一失败文件是 `src/transaction/__tests/Broadcaster.test.ts`。

**根因**：`capture-broadcaster-inputs.cjs` 的 `afterEach` 用 `fs.readFileSync(parity, 'utf8')` 读**全局** parity 轨迹（逐局部采集时该文件很小，全量时是所有文件共享的同一份）；实测全量 parity 轨迹达 **805.8 MB**，其中 4 行分别 126–252 MB（个别用例把大数组逐元素写进断言轨迹）→ 撞上 V8 字符串上限（`Cannot create a string longer than 0x1fffffe8`）。

**修复**：把该探针改为**分块扫描**（8 MB 块 + 逐行按需 `JSON.parse`，只保留属于本用例的行），内存占用与文件大小无关；已确认全仓仅此一个探针用该模式（`grep -ln "readFileSync(parity" capture-*.cjs` 仅命中它）。

**重新启动**：90 分钟档全量运行 v6（`.cache/evidence/full-run-6-20260930`，日志 `.cache/evidence/full-run-6.log`）；它会通过 Broadcaster，若整套仍需 >90 分钟则被上限终止，从而**解锁** 180 分钟档重跑。

**遗留观察**：全量 parity 轨迹 805 MB / 运行目录 930 MB 属预期规模（大数组用例的逐元素断言），`emit-assertion-observations.py` 逐行处理可承受；如后续 OOM 再评估。

### 90 分钟档全量运行进行中（20260901 00:30）

`full-evidence-run.py run --run-dir .cache/evidence/full-run-5-20260930`（90 分钟档）已跑约 28 分钟：产出 11 个文件轨迹、jest **26 个文件 PASS、0 FAIL**，当前停在一个重型向量文件上（与之前全量尝试同一位置），预计 16:35 前后触及 90 分钟上限被终止并写出 manifest，随后用 `--retry-after` 跑 180 分钟档。

### 窗口 v2 完美收官 + 全量运行门禁协议（20260930 23:50）

**窗口 v2 完成**：汇总为「**全部局部重采与篡改门禁通过**」，**零失败**；`aesgcm-man` 1/2/3 也验证通过。`full-evidence-preflight.py`：`casesTotal 5329`、`structurallyPlannedCases 5329`、`readyForFullCapture=true`、`currentCaptureVerifiedCases 2052`。

**全量运行遇到三道前置门禁，已逐一处理**：
1. `完整模块及跨目录范围尚未复核` → `module-scope.json` 的 `scopeReview` 原为 `pending`。复核条件已由 `audit-tests.py collect()` 满足：`pendingModules=[]`、`crossModuleTestsPending=[]`，且 `moduleReviews` 给出六模块 `decision/reason/evidence`、`crossModuleTestOwners` 逐文件指定归属与理由、依赖复核见 `doc/完整模块与API映射-20260920-122800.md`。已置 `reviewed`（提交 `093a2b2`）。
2. `冻结清单与当前完整源码清点不同` → 唯一差异是 `scopeSha256`（该字段就是 `digest(module-scope.json)`），因上一步改动而变；已把 `module-tests.json` 的该字段重算同步。
3. `180 分钟须引用实际触及 90 分钟上限的运行` → `--timeout-minutes 180` 必须先有一次**真实被 90 分钟上限终止**的运行（`elapsedSeconds ≥ 90*60` 且 `≤ 90*60+10`）。故先启动 **90 分钟档**全量运行（`.cache/evidence/full-run-5-20260930`，日志 `.cache/evidence/full-run-5.log`），预期它会被上限终止并写出 manifest；随后用 `--timeout-minutes 180 --retry-after <.cache/evidence/full-run-5-20260930/full-run.json>` 重跑。

注意：全量 TS 含 66 分钟长跑 + 其余 132 个文件，整体约 2 小时 → **必然触发**该协议。

### 长跑收尾（20260930 23:20）

`aesgcm-man` 的 66 分钟 TS 长跑已约 38 分钟（14:21 启动，预计 15:27 前后结束）；窗口其余 106 个局部**全部完成、零失败、同为来源 `13f34162199d`**。

**长跑结束后立即执行**（命令已固化）：
```bash
./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-final2.json
python3 full-evidence-run.py run --run-dir .cache/evidence/full-run-2-20260930 --timeout-minutes 180
python3 full-evidence-run.py verify .cache/evidence/full-run-2-20260930/full-run.json
node audit-api.cjs check
```
注意：`full-evidence-run.py run` 会依次跑 tsCommand（含 66 分钟长跑）与 javaCommand（一次无过滤 `clean test`）并自动校验，全程约 2–2.5 小时；**必须用 `--timeout-minutes 180`**。

### 14 个事项取得完整任务级对照并入册（20260930 22:50）

用 `./close-items.sh final2` 对**计划完整的实现事项**跑任务级对照：**14 个成功**（每个都是 cases 全等、missing/uncompared 全 0、`taskAcceptancePassed=true`）：

| 事项 | 用例 | 断言 |
| --- | --- | --- |
| wallet-contracts | 253/253 | 1003 |
| keys-signatures | 146/146 | **40242** |
| wallet-wire | 128/128 | 351 |
| wallet-hosts | 126/126 | 287 |
| wallet-client | 100/100 | 184 |
| auth-sessions | 85/85 | 160 |
| transaction-beef | 83/83 | 1553 |
| transaction-base | 74/74 | 115 |
| wallet-keys | 71/71 | 162 |
| broadcasters | 68/68 | 169 |
| wallet-json | 58/58 | 78 |
| transaction-verification | 53/53 | 162 |
| auth-certificates | 50/50 | 128 |
| script-templates | 17/17 | 96 |

已把 14 个事项写入 `feature_list.json`（`status=done` + `taskAcceptance{status,casesCompared,assertionsCompared,missing*,uncompared,compareReport}`）；**事项状态分布：done 31 / not-started 12 / in-progress 0**。

**剩余 12 个**：4 个实现事项（`script-spend`、`script-vectors`、`transaction-complete`、`auth-transport`——它们含**专用局部**，`local-task-parity.py` 只处理标准局部，其验收随单次全量运行）与 8 个**总门禁**（`migration-api-contract`／`test-mapping`／`input-replay`／`result-capture`／`evidence-gate`／`map`／`core-modules`／`sdk-acceptance`）——后者由最终全量运行 + `audit-tests.py check` + `audit-api.cjs check` 决定。

### 同源性验证（20260930 22:20）

主代理独立核对：窗口 v2 的 **106 个局部全部记录同一来源 `13f34162199d`**，且与当前 `audit-tests.java_revision()` 一致 → **同源达标**，`close-items.sh`／`local-task-parity.py` 的前提（干净工作树 + 同一来源摘要）已满足。

`aesgcm-man` 长跑进行中（14:21 启动，预计 15:27 前后结束），窗口其余部分已全部完成、零失败。

### 窗口 v2 全部局部完成、零失败（20260930 22:00）

**107 项已处理、篡改门禁通过 106、失败 0** —— 仅剩最后一个局部 `aesgcm-man` 的 66 分钟 TS 长跑（14:21 启动，预计 15:27 前后结束），结束后窗口即退出并打印汇总。对比窗口 v1（6 处失败、353 例），本轮修复全部生效。

### 窗口 v2 进度（20260930 21:30）

已处理 **96/106**、篡改门禁通过 **95**、**失败 0**。剩余 10 个：`peer`、`private-key-split`、`random`、`transaction-performance`、`random-additional`、`hash-additional`、`symmetric-key-compatibility`、`bignumber-dh-group`、`async-crypto-backend`、**`aesgcm-man`（约 70 分钟）**——含长跑，预计再约 80 分钟（约 15:25）窗口退出。

### 窗口 v2 进度（20260930 21:00）

已处理 **73/106**、篡改门禁通过 **72**、**失败 0**；剩余约 35–50 分钟（`curve-unit` 等此前被 churn 拒绝的局部也在顺利采完）。

### 窗口 v2 进度（20260930 20:30）

已处理 **47/106**、篡改门禁通过 **46**、**失败 0**；剩余约 60–90 分钟。

### 窗口 v2 进度（20260930 20:00）

已处理 **23/106**、篡改门禁通过 **22**、**失败 0**；速率约 1 分钟/局部（比 v1 更快），剩余约 100 分钟。

### 契约文档同步 + 窗口 v2 进度（20260930 19:30）

按代理建议更新 `doc/测试迁移契约-20260920-101559.md`：条件未执行证明改写为**两条规则**，新增 `unreachable-guard-after-throw-v1` 的完整放行条件（冻结源码逐字匹配、同块紧邻调用、catch 首语句即实际执行断言、proof 绑定、两侧逐样本 throw 观测且排除断言失败名），并保留 `drbg-nist-invalid-input-v1` 原文语义。提交 `2fde0a8`。

### 两处缺口闭合、冻结 v2、窗口重跑已启动（20260930 19:15）

**两处缺口闭合**（哨兵规则代理终报）：`completePlanError = null`、**`readyForFullCapture = true`**、`planErrors=[]`、`missingFullRunInterfaces=[]`、`structurallyPlannedCases 5329/5329`、`plannedSamples 38092`（loopSamples 不新增样本）。
- 哨兵规则 `unreachable-guard-after-throw-v1`：严格形态（冻结源码 path+sha256 逐字匹配、恒假哨兵）、同块紧邻调用、catch 首语句即冻结断言站点、proof 绑定 `{ruleId,guardSiteId,sampleId}`、两侧观测逐样本 `kind=throw` 且排除断言失败名；DRBG 分支逐字未改；`lrshiftnum` 4/28/29 + tamper 两个 true + `currentCaptureVerified=true`。
- 925:7 循环：唯一调用点 `Transaction.test.ts:1003`，冻结轨迹里 500 个 sighash 用例 **100% 命中**（jest 720/720），只为这 500 例登记 `loopSamples`（49 例 scriptbuf 为空时不迭代，属结构性站点覆盖，已在报告说明）。
- 自测：semantics **14 OK**（含新增哨兵正反例）、bundle 24 OK、preflight 13 OK、`node --test test-audit.test.cjs` **43 pass/0 fail**。

**风险处置**：代理报告 12:34–12:36 有进程对工作区做过一次**整仓恢复**（其改动被短暂清空），故立即双仓提交保护：任务仓 `339f5a6`、SDK 仓 **`8b8e13d`（冻结来源 v2）**。

**窗口 v2 已启动**：守卫六项全过（静默/编译/计划 138-0/分派 `unresolved=0` 且无探针原文件 0/覆盖率 5329-5329/工作树干净）；`./recapture-all.sh final2-20260930`（后台，日志 `.cache/evidence/final-window2-20260930.log`），首个局部 `hex-bn` 已通过篡改门禁（其相对路径修复生效）。

### 哨兵规则落地 + 发现被掩盖的第二处缺口（20260930 18:45）

**已完成（哨兵豁免）**：`audit-tests.py` 新增 `unreachable-guard-after-throw-v1`（严格形态 + 逐样本异常结局 + proof 绑定，DRBG 路径未改）；`prepare-spend-local.py` 支持写入 `unexecutedSites`（重跑 freeze 可复现）；新计划 `.cache/evidence/lrshiftnum-plan-guard-20260930`；重采 `lrshiftnum-standard-guard-20260930` → **4 例／28 样本／29 断言**、tamper 两个 true、`planValid=true` 且 `currentCaptureVerified=true`；`20:9`／`39:9` 不再缺失。

**新发现（被 `same_keys` 首次报错掩盖）**：断言缺口修好后，`completePlanError` 暴露第二处——`冻结循环站点覆盖：缺失 1 … src/transaction/__tests/Transaction.test.ts:925:7:loop`。根因：925 行的 while 循环在 `Transaction.fromBinary` 内，唯一执行它的用例 `da0cd369…`（"1 mb transaction"）归**专用局部** `transaction-shared-vectors`，而该局部由 `transaction-vector-evidence.py:prepare` 生成、站点窗口写死 909-914/995-1066（排除 925）、`loopSamples` 全空；`transaction` 局部只登记了同文件另外 7 个循环。两处计划分别冻结于 09-27 与 09-30 01:28，**均早于本轮改动 → 缺口本就存在**。计划校验顺序是“先断言、后循环”，所以此前只报断言缺口。

**已批准修法**（任务侧工具+计划数据，不碰 SDK）：扩展 `transaction-vector-evidence.py` 的 prepare 把 925:7 纳入专用局部清单并登记 `loopSamples`，prepare 到新 `transaction-vector-plan-20260930`，`register-local.py` 增 `--capture-kind` 以保留 `specialized-local`；并要求**先验证该循环在冻结轨迹里确有执行记录**——若轨迹里没有，只改计划会与轨迹不符，必须先让该局部 TS 探针纳入观测并重跑 TS。旧计划与旧成品保留不动。

### 比较层改动独立验证（20260930 18:00）

主代理独立复跑 beef 代理留下的比较层改动与自测：`python3 test-evidence-semantics.py` → **OK**；`node --test test-audit.test.cjs` → **43 pass / 0 fail**。改动（`audit-tests.py` +19、`test-evidence-semantics.py` +31）确认无回归。

哨兵规则代理仍在探索阶段（尚未落盘）。

### 哨兵规则重派（20260930 17:30）

第一路哨兵规则代理**中途失败、未产出可用产物**（`audit-tests.py` 现有的 +19 行是 beef 代理的零实参 matcher 规则与自测，已核实完好）。已重派一路，并在任务书里给出更明确的切入顺序（先读 `validate_unexecuted`／`validate_branch_observations` 弄清 `samples`／`rows` 形状 → 复现 `completePlanError` → 读 catalog 站点原文 → 再设计规则）。

规则要求不变：`unreachable-guard-after-throw-v1` 必须同时满足“站点形态与冻结源码逐字匹配（恒假哨兵，紧跟必然抛错的调用）”“该用例**每个**样本的紧邻调用都有异常结局”“实际执行的是同一 catch 块的断言”，任一不满足即拒绝。

### 六处失败全部修好；三项判断的裁决（20260930 17:00）

修复代理终报：**6/6 全部修好**，每项 recapture 退出 0、tamper 两个 true。补充根因：`drbg29` 还叠加了“两侧共用 `assertions.raw.jsonl`、Java 追加到 TS 轨迹后”的问题（改为按侧别命名）；`chronicle-opcodes` 修完身份后又见 `inputSequence/lockTime` 的 Long vs Integer 类型差（改走 `numeric(...)` 并扩 long 分支）；`simplified-fetch-transport-additional` 实际是**六层问题叠加**（undefined body 投影、URL 字面量、deserialize 实参形状与字面量、null 捕获/varargs、JSON 键序、两处断言表示）。

**我对三项判断的裁决（全部接受）**：
1. **1 条“Java 不可复现样本”登记**（`sft-additional` 的 `malformedHeaderErrorKeepsCauseText` / `send-02`）：原用例对 `JSON.parse` 抛**字符串**，Java 异常必带 Throwable 原因，无法产出同一 message；该用例的构造入口仍重放、两条消息断言原样保留。计划重冻结为 46 例／**88** 样本／68 断言，全局 `plannedSamples` 38093 → **38092**。接受，并要求在最终报告里如实列出这条排除。
2. **JSON 键序规范化**作为**探针侧投影**（不改生产序列化）：原用例本就只断言解析后的对象，字段/值仍严格比较。接受（比改生产字节序更符合“只做迁移、不改行为”）。
3. **比较层零实参 matcher 语义规则**：最终全量门禁共用，必须在场；代理已扫 788 份既有证据的 1631 条零实参断言、形态仅 `[]`/`null`/`{type:array,value:[]}`/`{type:undefined}`，记法一致的站点仍走严格比较，并加自测。接受。

**新发现的既有阻塞项**：`completePlanError = 冻结断言站点覆盖：缺失 2 … lrshiftnum.test.ts:20:9 与 :39:9` → `readyForFullCapture=false`。这两处是 `try { <调用必然抛错>; expect(true).toBe(false) } catch { expect(e).toBeTruthy() }` 里**设计上不可达的哨兵断言**，而现有 `unexecutedSites` 豁免**硬绑定 DRBG**（`if case_id not in DRBG_BRANCH_CASES: require(not exclusions, …)`）。已派代理新增同等严格的通用规则 `unreachable-guard-after-throw-v1`（要求：该用例每个冻结样本的紧邻调用都记录到异常、实际执行的是同一 catch 块的断言、站点形态与冻结源码逐字匹配），并加正反自测、把 `lrshiftnum` 计划补齐到 `completePlanError` 为空。

### 六处失败：5 处已修复并核验（20260930 16:40）

| 局部 | 用例/输入/断言 | 状态 |
| --- | --- | --- |
| validation-helpers | 147/149/203 | ✓ verify |
| hex-bn | 36/71/71 | ✓ verify（相对路径修复）|
| beef | 21/390/123 | ✓（比较层零实参 matcher 规则）|
| drbg29 | 29/72/30 | ✓ verify（适配器缺省参数）|
| chronicle-opcodes | 74/154/77 | ✓ verify（caseId 映射，SDK 改动 2 文件）|
| simplified-fetch-transport-additional | — | 进行中（SDK 改动 2 文件已落地）|

SDK 侧当前 4 个文件改动，均在批准范围内。等最后一个局部通过后即执行“重跑计划”一节。

### 重跑计划（20260930 16:15）

等修复代理把 2 处 SDK 测试源码改动落地并逐项验证（聚焦 `clean test` 全绿 + 各自 recapture/tamper 通过）后，按序执行：

```bash
# 1. 新冻结提交（记录改动文件与理由）
cd metanet4j-bsv-sdk && git add -A && git commit -m 'test(migration): 冻结来源 v2（sft-additional 补 Undefined 分支、chronicle-opcodes caseId 映射）' && cd ..
# 2. 重跑完整统一窗口（后台，约 3.3 小时；日志 .cache/evidence/final-window2-20260930.log）
nohup ./recapture-all.sh final2-20260930 > .cache/evidence/final-window2-20260930.log 2>&1 &
# 3. 复核 + 单次双侧全量运行（注意 --timeout-minutes 180，全量 TS 含 66 分钟长跑）
./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-final2.json
python3 full-evidence-run.py run --run-dir .cache/evidence/full-run-2-20260930 --timeout-minutes 180
# 4. 逐事项对照与接口复核
./close-items.sh final2 && node audit-api.cjs check
```

注意：窗口重跑会覆盖 101 个局部的证据（新旧一视同仁），但 `validation-helpers`／`hex-bn`／`beef`／`drbg29` 四处修复已包含在任务侧工具里，会随窗口生效。

### 六处失败：修好 4 个、批准 2 处 SDK 改动（20260930 16:00）

修复代理成果（**均未改 SDK 源码**，revision 仍 `f5c7e707`）：
1. `validation-helpers` 147/149/203 —— 计划文件复制生效，tamper 两个 true；
2. `hex-bn` 36/71/71 —— 根因是**适配器把相对路径直接拼进 `-Dmigration.input.plan=`**，而 surefire 的 CWD 是模块目录 → `NoSuchFileException` → `LegacyInputReplay.<clinit>` 失败；改为 `args.replay.resolve()`；
3. `beef` 21/390/123 —— 根因是**零实参 matcher 的 expected 记法**（TS `toBeUndefined(undefined)` 记 `{type:undefined}`、Java 记 `[]`；`toBeNull()` 反之），在**比较层** `audit-tests.py::matcher_semantics` 增加零实参 matcher 语义规则（要求 matcher/negated 相同、两侧 expected 均为空形态、actual 仍逐值相等）并加自测；
4. `drbg29` —— 照 legacy 适配器思路，`capture-drbg-side.py` 的 `--catalog/--mapping` 改为可缺省并按语料同目录派生。

**批准 2 处 SDK 测试源码改动**（皆真实缺陷，共 120 例）：
- `simplified-fetch-transport-additional`（46）：additional 类漏镜像基类 `body == Undefined.INSTANCE → undefined()` 分支 → 只加该分支，不动显式 null 口径；
- `chronicle-opcodes`（74）：`ChronicleOpcodesTest` 把 `...ChronicleOpcodesTest#chronicleCaseNNN` 当 caseId，而计划/协议用 64 位 hash（历史上三次采集从未成功）→ 按序号映射到计划 hash（照 `BeefTest` 的 `CASES` 写法）。

**代价与后续（已确认）**：`audit-tests.java_revision()` 哈希所有仓库全部 tracked+untracked 文件，改 `src/test` 会让 revision 前移 → 窗口内 101 个局部与刚跑的**全量 TS 长跑证据全部作废**。因此：①已**停掉在跑的全量 TS 长跑**（省算力）；②等代理改完并逐项验证后，**重新冻结来源 → 重跑完整统一窗口（约 3.3 小时）→ 再跑单次双侧全量运行 + `audit-tests.py check`**。

### 窗口后复核与结构性发现（20260930 15:10）

`full-evidence-preflight.py` 复核：**`casesTotal 5329`、`structurallyPlannedCases 5329`（100%）、`plannedSamples 38093`、`plannedAssertionInstances 56744`、`planErrors=[]`**；`currentCaptureVerifiedCases 1882`（102 个局部）。

**关键结构性发现**：未同源复核的 52 个局部（3447 例，占 65%）绝大多数是**专用局部**（`auth-fetch-additional-*` 等约 47 个），preflight 对它们标注“专用局部采集的结构计划；尚未接入标准双侧 capture，不计当前全量来源”。也就是说：**这 65% 的验收路径不是逐局部采集，而是单次双侧全量运行**（`run-full-ts-capture.py` + `run-full-java-capture.py` + `audit-tests.py check`）——全量分派表已为它们的原文件配好探针（`unmappedCatalogFiles=0`），全量 Java 侧则以一次 `clean test` 覆盖全部测试类。

**已启动全量 TS 捕获**（后台，日志 `.cache/evidence/full-ts-capture.log`，运行目录 `.cache/evidence/full-run-final-20260930/`）：它只跑 jest、不占 `run.lock`，因此与修复代理并行；预计 1.5–2.5 小时（含 `AESGCM.man` 的 66 分钟）。

**顺序约束**：全量 Java 侧（一次 `clean test`）必须等 6 处失败的 Java 侧问题修好后再跑，否则会整体失败。

### 最终窗口完成（20260930 14:45）

`recapture-all.sh final-20260930` 跑完：**处理 108 项、篡改门禁通过 101 项、失败 6 项**（合计 353 例），耗时约 3 小时 20 分钟（含 `aesgcm-man` 的 66 分钟长跑）。

**六个失败项与定性**：
| 局部 | 例数 | 现象 |
| --- | --- | --- |
| validation-helpers | 147 | TS 读 `<formal>/input-plan.json` 不存在（已复制修复，待重跑）|
| chronicle-opcodes | 74 | Java：`固定 TS Chronicle 输入缺失：ChronicleOpcodesTest#chronicleCase001` |
| simplified-fetch-transport-additional | 46 | Java：`send-0…` 入口结果不一致 |
| hex-bn | 36 | 旧管线 Java 侧失败（其 36 例已由全量分派表覆盖）|
| drbg29 | 29 | TS 适配器仍需 `--catalog/--mapping`（旧式参数）|
| beef | 21 | 断言不一致 `Beef.test.ts:93:7` |

已派一路专用代理按 2→4→5→6→3→1 顺序定点修复（严禁改 SDK 源码，因其已冻结在 `ba10dd4`）。

### 窗口收尾：仅剩 aesgcm-man 长跑（20260930 14:30）

窗口已处理 107 项、篡改门禁通过 **100** 个、**无失败项**；最后一个局部 `aesgcm-man` 的 TS 长跑 09:43 启动（66 分钟），预计 10:50 前后完成，随后窗口退出并打印汇总。

### 窗口进度（20260930 13:40）

已处理 **101/106**、篡改门禁通过 **94**、**无失败项**。剩余 6 个：`random-additional`、`hash-additional`、`symmetric-key-compatibility`、`bighumber-dh-group`、`async-crypto-backend`（各约 1.5 分钟）与 **`aesgcm-man`（约 70 分钟，含 66 分钟 TS 长跑）**，整体预计再约 80 分钟。

### 窗口进度（20260930 13:15）

已处理 **83/106**、篡改门禁通过 **77**、**无失败项**；剩余约 35 分钟。

### 窗口进度（20260930 12:55）

已处理 **69/106**、篡改门禁通过 **63**、**无失败项**；`wallet-client` 等此前被 churn 反复拒绝的局部也在窗口内顺利采完。剩余约 55 分钟。

### 窗口进度（20260930 12:35）

已处理 **61/106**、篡改门禁通过 **56**、**仍无失败项**；剩余约 68 分钟。

### 窗口进度（20260930 12:10）

已处理 **42/106**，篡改门禁通过 **37** 个，**无失败项**；速率约 1.5 分钟/局部，剩余约 96 分钟。
`validation-helpers` 的重采在队列中（等待共享锁）。

### 窗口内两处局部问题的处置（20260930 11:40）

1. **`validation-helpers`（147 例，占 2.8%）**：TS 阶段报 `FileNotFoundError: .../validation-helpers-formal-20260929/input-plan.json`。根因是适配器按约定读 `<catalog父目录>/input-plan.json`，而该局部的计划文件此前只存在于任务根（`validation-helpers-input-plan.json`）。已按约定把计划复制到 `<formal>/input-plan.json`（147 用例），并单独排队重采（后台，日志 `.cache/evidence/validation-helpers-recapture.log`）。
2. **全量扫描**：153 个登记局部的 `input_plan` 全部存在且为合法 JSON（0 异常），说明这是孤例。
3. `broadcaster`（11 例）在窗口中**采集通过**，说明代理担心的 parity 环境变量冲突只影响全量运行（已在 `capture-full-dispatch.cjs` 修复），不影响逐局部采集。

### 窗口吞吐实测（20260930 11:20）

已完成 5 个局部：hex-bn（失败，见上）、wallet-property、werr-constructors、auth-master-certificate-constructors、auth-master-certificate-remaining；相邻完成间隔 1.3／4.3／1.4／0.3 分钟（4.3 那次包含我并行跑 hex-bn 抢锁），即**约 1.8 分钟/局部**，106 个局部预计 **约 3.2 小时**，与预估一致。窗口目前**无失败项**。

### 最终窗口已启动 + 两处工具修复（20260930 11:00）

**守卫六项全过**：静默 ✓、`test-compile` ✓、`validate-plans` **138 检查/0 失败** ✓、分派表 **153 局部／133 原文件／151 探针／115 环境变量，`unresolved=0`、`unmappedCatalogFiles=0`** ✓、覆盖率 **5329/5329（100%）** ✓、工作树已冻结（SDK `ba10dd4`）✓。

**最终窗口已启动**：`./recapture-all.sh final-20260930`（后台，日志 `.cache/evidence/final-window-20260930.log`），处理 **106 个可采局部**，预计 3.5–4 小时；已完成 5 个、其中 3 个篡改门禁通过。

**本轮两处工具修复**：
1. `capture-legacy-side.py`：`--kind` 缺省 `both`、单报告自动派生与合并（`<testsuite>` / jest JSON），使旧管线局部适配标准 recapture 流程；
2. `capture-full-dispatch.cjs`：**整轮共享环境变量不再被逐文件覆盖**（`MIGRATION_PARITY_TS_OBSERVATIONS` 等）——否则 `broadcaster`／`wallet-wire` 的断言行会落到各自的文件里，全量断言转换读不到而 strict 失败（由最后 2 文件代理发现）。

**hex-bn（36 例）暂挂**：其旧管线在标准流程下 Java 侧报错（28+36+8 例 Errors，可见次级 `BigNumberObservation.complete()` NPE），且 tamper 因无成功运行目录而报“来源不匹配”。它的 36 例**已在全量分派表中**（探针 + legacy emit 覆盖，见第 30 轮），因此最终单次双侧全量运行仍会为其产出证据；逐局部采集留待窗口后单独处理。

### 长跑进入收尾阶段（20260930 10:30）

`AESGCM.man` 的 jest 运行已约 42 分钟：探针已开始产出入口轨迹（`ts-calls.raw.jsonl` 784 字节，06:52），`ts-jest.json` 尚未落盘（即 jest 仍在跑）。预计 07:16 前后结束，随后冻结计划并登记，覆盖率即达 5329/5329。

### 窗口待发（20260930 10:15）

`AESGCM.man` 长跑已约 38 分钟（预计 07:16 前后结束）。窗口命令已定：`./recapture-all.sh final-20260930`，将处理 **106 个可采局部**（含即将登记的 `aesgcm-man`），预计 3.5–4 小时（该局部本身占约 70 分钟）。

启动后建议按 30–60 分钟粒度读取作业输出；窗口内**严禁**任何 Maven／采集／源文件改动。

### 来源冻结完成（20260930 10:00）

静默达标后执行冻结提交：SDK 仓 `ba10dd4`（94 个文件：primitives 31／script 18／transaction 12／wallet 8／auth 8／chaintrackers 6／http 4／support 2），提交前 `test-compile` **BUILD SUCCESS**，提交后 `git status` **0 未提交**。

至此守卫六项中 ①②③④⑥ 全部通过，**只剩 ⑤ 覆盖率 5328/5329**，等 `AESGCM.man` 的 66 分钟冻结运行（06:10 起）结束后登记即达 100%。

**重要约束**：`ba10dd4` 之后不得再编辑 SDK 仓任何源码；若必须修改，冻结失效，需重新提交并从窗口第一步重来。

### 窗口前登记体检（20260930 09:45）

对全部已采集局部逐条核对 `ts_run_manifest`／`java_run_manifest`／`ts_inputs`／`java_inputs` 四类路径：**0 个悬空引用**。最新两局部（spend-additional、whats-on-chain-chain-tracker）均指向以 `d` 结尾的成功运行目录。

`AESGCM.man` 长跑进行中（已约 36 分钟，预计 07:16 前后结束）。

### spend 批收尾完成、全仓接近静默（20260930 09:30）

spend/链跟踪修缺代理**已停笔**，两局部全绿且 `currentCaptureVerified=true`：`spend-additional` 69/70/76、`whats-on-chain-chain-tracker` 8/26/10；`planErrors=[]`、聚焦 `clean test` 77/0/0/0、`test-compile` BUILD SUCCESS。三处根因均为接线/投影：①spend 构造实参漏镜像 TS 的 `memoryLimit`/`isRelaxed`/`unlockingScript`；②**该文件 4 例 `PrivateKey.fromRandom()` 使探针自身不确定**（冻结自采与标准采集拿到不同密钥）→ 新增 `spend-seeded-entropy.cjs` 种子加载（对齐 `verifier-seeded-entropy.cjs` 口径，已实测对无随机熵文件逐行无影响）；③WOC tracker 构造体内又造了一个未包装客户端，导致一次 HTTP 调用被记两次入口。

**静默进度**：全仓最后一次 Java 写入是 06:37（已停笔）；`AESGCMManualInputReplay.java`／`AESGCMManualTest.java` 早在 06:08–06:09 就绪且未再改。唯一在跑的是 `AESGCM.man` 的 66 分钟 TS 冻结运行（06:10 起，只写 `.cache`，不碰 `src`）。

**下一轮起可执行的收尾序列**（长跑结束后立刻做）：①代理冻结计划 + `register-local.py`（覆盖率应达 5329/5329）；②`cd metanet4j-bsv-sdk && git add -A && git commit`（冻结来源）；③`./final-window-guard.sh 10` 应六项全过；④后台启动 `./recapture-all.sh final-$(date +%Y%m%d)`（105+ 局部，约 3.5–4 小时）。

### 守卫复跑（20260930 09:20）

①静默 ✗（spend 代理 10 分钟内有改动）；②编译 ✓；③计划 ✓（137 检查／0 失败）；④分派表 ✓（152 局部／132 原文件／150 探针／114 环境变量，`unresolved=0`，无探针原文件 1 个）；⑤覆盖率 ✗ 5328/5329（仅 `AESGCM.man` 1 例）；⑥工作树 ✗ 94 个未提交（冻结时提交）。

结论：六项里只有三项待办，且都属“等长跑 + 等停笔 + 冻结提交”这类时序事项，无技术风险项。

### 等待期状态（20260930 09:10）

`AESGCM.man` 冻结运行约 24 分钟；spend/链跟踪修缺代理在做收尾复验（06:33 仍改 `WhatsOnChainChainTrackerInputReplay`）。两路之外全部代理已停笔。

### 等待期状态（20260930 09:00）

- `AESGCM.man` 冻结运行已跑约 23 分钟（预计 07:16 前后结束）。
- SDK 工作树 94 个未提交改动，**生产源码 `src/main` 为 0**（四处生产修复均已提交），意味着冻结提交只涉及测试侧文件。
- 最后活跃代理：spend/链跟踪修缺（06:32 仍在改 `WhatsOnChainChainTrackerInputReplay`，应在做修复后复验）。

### `AESGCM.man` 探针已落盘、分派表已解析（20260930 08:45）

探针 `capture-aesgcm-man-inputs.cjs` 已写好，66 分钟冻结运行进行中（`ts-jest.log` 为空即 jest 仍在跑，输出缓冲）。
分派表刷新：**152 局部／132 原文件／150 探针／114 环境变量，`unresolved=0`**，无探针原文件仅剩 1 个（即 `AESGCM.man` 自身，待冻结后登记计划）。
覆盖率仍 5328/5329，等该冻结运行结束、登记计划后即达 **100%**。

### 关键 infra 缺口修复：全量 TS 捕获会静默跳过 `.man.test.ts`（20260930 08:35）

**问题**（由最后 2 文件代理实测发现）：`sdk/jest.config.js` 的 `testPathIgnorePatterns` 含 `\.man\.test\.ts$`，而 `run-full-ts-capture.py` 只用 `--runTestsByPath` 指定文件、**没有覆盖该忽略规则** → jest 会把 `AESGCM.man.test.ts` 静默过滤掉，strict 模式下最终全量运行会以“raw 型轨迹缺失／探针没装成”整轮非零退出。

**实测确认**（主代理复核）：`jest --listTests --runTestsByPath .../AESGCM.man.test.ts` **无输出**；追加 `--testPathIgnorePatterns /node_modules/` 后正常列出该文件。全 SDK 仅此一个 `.man.test.ts`。

**修复**：在 `run-full-ts-capture.py` 的 jest 命令里补 `'--testPathIgnorePatterns', '/node_modules/'`（与 `run-ts-baseline.py`、`collect-cases.cjs` 的既有做法一致）。已提交。

**另**：`async-crypto-backend` 3 例／10 输入／9 断言已通过（语义规则 `async-ready-null-adapter-v1` 用自写行满足：Java 侧真 null + 原 matcher + 空期望 + `pass:true`）；`AESGCM.man` 的 66 分钟冻结运行仍在继续（06:10 起）。

### 锁内正常推进（20260930 08:25）

锁持有者即 `capture-primitives-last-local.py`（最后 2 文件代理的适配器），正在跑 `async-crypto-backend` 的 Java 侧；队列里还有一个 `local-evidence-gate` 等待者。`AESGCM.man` 的 66 分钟冻结运行仍在继续（不占锁）。

在跑代理已收敛到 2 个（spend/链跟踪修缺收尾、最后 2 文件）。

### 两路修缺全部收口（20260930 08:15）

`spend-additional` 采集通过（verify ✓）——至此首采暴露的 4 处内容问题**全部解决**：`peer-certificate-policy` 15/35/47、`simplified-fetch-transport` 3/6/10、`whats-on-chain-chain-tracker` 8/26/10、`spend-additional`（69 例）。

仍在进行：`async-crypto-backend` 的 Java 侧（排队等锁）、`AESGCM.man` 的 66 分钟冻结运行（06:10 起）。覆盖率 5328/5329。

### 队列与长跑状态（20260930 08:05）

- `async-crypto-backend`：TS 侧 06:08 完成，Java 侧仍在**排队等锁**（现场 3 个等待者，均为修复代理的采集）。
- `AESGCM.man`：66 分钟 jest 冻结运行进行中（06:10 起，预计 07:16 前后结束），按要求不占锁。
- `spend-additional`：修复代理仍在迭代。

### 两处长跑进行中（20260930 07:50）

- `async-crypto-backend`：TS 侧已完成（`ts-jest.json` 06:08），Java 侧排队等锁。
- `AESGCM.man`：探针目录 `aesgcm-man-probe-20260930` 已于 06:10 起跑（66 分钟 TS 冻结运行，不占锁）。
- `spend-additional`：修复代理仍在迭代。

**提醒**：`AESGCM.man` 这次 TS 运行结束前不要动 `.cache/evidence/aesgcm-man-probe-20260930/`（代理据此冻结计划）。

### 覆盖率 5328/5329（20260930 07:40）

`async-crypto-backend`（3 例）已冻结计划并进入采集（`async-crypto-backend-plan-20260930`／`-probe-20260930`／`-standard-20260930-a`），**全仓仅剩 `AESGCM.man` 1 例未计划**；该例需一次 66 分钟 TS 冻结运行（不占锁）。

### 等待收尾（20260930 07:30）

覆盖率仍 5325/5329（`async-crypto-backend` 3 + `AESGCM.man` 1）；`spend-additional` 仍在修（最近改动 `SpendObservation.java` 05:58）。**提醒后续轮次**：此刻再提交任何 Java 改动都会让在飞的 `spend-additional` 采集作废，因此冻结提交要等到三路全部停笔。

### 分派表刷新（20260930 07:20）

重跑 `build-full-run-probes.py`：**151 局部／131 原文件／149 探针／113 环境变量，`unresolved=0`**，**无探针原文件只剩 2 个**（`AESGCM.man.test.ts`、`AsyncCryptoBackend.test.ts`，正在做）。这一步也顺带把认证修缺代理提到的“表里仍指向被取代的计划目录”问题刷新掉了。

`spend-additional` 仍在重试采集；`whats-on-chain-chain-tracker` 已通过（8/26/10）。

### 三批交付汇总（20260930 07:10）

**① 原语剩余批 7 个局部收口**（该批合计 42 例／229 输入／**40362 断言**）：private-key 7/55/40021、private-key-split 8/99/17、random 5/11/219、random-additional 8/10/62、hash-additional 9/22/19、symmetric-key-compatibility 3/22/22、bignumber-dh-group 2/10/2；七者 recapture 与 tamper 均通过、`verify` 复核通过。新增共享支撑 `support/TsInputReplay.java` 与 `capture-parity-array-length.cjs`。

**② 认证修缺两处收口**：`peer-certificate-policy` 15/35/47、`simplified-fetch-transport` 3/6/10，两次重采**同一来源 `161bc96e`**，tamper 两个 true、preflight 两局部 **`currentCaptureVerified=true`**（全仓当前仅这两个 + peer 为 true）。
　差异根因：前者 Java 只登记了 `requestCertificates` 第一个实参（TS 是 `[policy, "remote"]`）；后者请求 `body` 被记成 `{type=string,value=INSTANCE}`，实为生产用 `Undefined.INSTANCE` 表达 TS 的 undefined，重放投影只判了 `null`。两处均只改投影/接线。

**③ `AESGCM.man` 的特殊排期**（重要）：该 TS 用例单次运行需 **66 分钟**（512MB 明文；Java 仅 49 秒），标准流程要跑两次（冻结 + 正式采集）。裁决：**冻结 + 登记现在做**（TS-only 运行不占 `run.lock`），**正式双侧采集留给最终窗口**（窗口因此延长约 70 分钟，可接受）；并要求沿既有传统采用“大数组记 `length + sha256`、witness 仍逐字节循环”的记录口径。

### `simplified-fetch-transport` 采集通过（20260930 07:00）

认证修缺代理两处全部收口：`peer-certificate-policy` 15/35/47、`simplified-fetch-transport` 3 例（第二次换目录重试成功，verify ✓）。
仍在跑：spend 与链跟踪修缺（`spend-additional`、`whats-on-chain-chain-tracker`）、最后 2 个原语文件（4 例）。

### 收尾脚本 `close-items.sh`（20260930 06:50）

新增 `close-items.sh <日期标签>`：窗口后对**计划已完整的实现事项**（当前 26 个）逐个跑 `local-task-parity.py`，把该事项的全部局部汇总成任务级逐断言报告，输出到 `.cache/evidence/<事项>-final-<标签>/`，并打印成功/失败汇总。

前置条件（脚本自身不做检查）：Java 工作树干净（`local-task-parity.py` 会校验并要求同一来源摘要）、相关局部已在同一来源下重采完毕。

### 全量证据一致性抽检（20260930 06:40，主代理只读）

对 `.cache/evidence/*/parity.json` 逐份核对：用例数 > 0、双侧（ts/java）用例均非空、所有 `*sha256` 字段彼此一致。结果 **111 份全部自洽、0 异常**，可作为最终窗口前的证据基线。

注：parity.json 的 `cases` 字段在部分文件里是**计数（int）**、部分文件是**列表**，编写消费脚本时要兼容两种形态（本轮第一次抽检就因按列表解包而报错，已修正）。

### 最终窗口规模核算（20260930 06:30）

`recapture-all.sh` 的局部清单是**从 `full-evidence-locals.json` 动态枚举**（凡登记了 `capture` 且非 `specialized-local`），因此不存在硬编码遗漏；当前将处理 **101+ 个可采局部**，每个局部内部跑「TS jest → Java `clean test` → bundle 汇总 → 篡改门禁」。

实测吞吐参照：上一批 20 个局部（含篡改门禁）耗时约 25–30 分钟 → **约 1.5 分钟/局部**，因此最终窗口预计 **2.5–3 小时**（不是此前按“每局部两次 Maven”估的 8 小时以上）。

### `bignumber-dh-group` 采集通过（20260930 06:20）

原语批第 9 个（也是该批最后一个）局部落地：2 例（verify ✓）。运行产物 116 个局部。
剩余未计划仍为 4 例：`AESGCM.man` 1、`AsyncCryptoBackend` 3（专用代理正在做）。

### 最后 4 例改由专用代理接管（20260930 06:15）

全仓仅剩 `AESGCM.man.test.ts`（1 例）与 `AsyncCryptoBackend.test.ts`（3 例）未计划，原语批代理尚未开工这两者。已把这两个文件**从原语批接管出来**交给专用代理（局部 `aesgcm-man`／`async-crypto-backend`），并通知原语批代理不要再做，避免重复劳动与登记冲突。

注意点已写进新代理任务书：`AsyncCryptoBackend.test.ts` 在 `audit-tests.py` 里已有固定语义规则，探针必须按原观察形状记录。

### `symmetric-key-compatibility` 采集通过（20260930 06:05）

原语批第 8 个局部落地（3 例，verify ✓）；剩 `AESGCM.man` 1、`AsyncCryptoBackend` 3 共 **4 例**。运行产物 115 个局部。

### 覆盖率 5325/5329（20260930 06:00）

原语批已完成 `BigNumber.dhGroup`（正在写 `BigNumberDhGroupInputReplay`/`Test`），剩 **4 例**：`AESGCM.man` 1、`AsyncCryptoBackend` 3。

### 等待最后 6 例（20260930 05:50）

原语批已登记/采集 `symmetric-key-compatibility`，剩 `AESGCM.man` 1、`AsyncCryptoBackend` 3、`BigNumber.dhGroup` 2。共享锁常年 2 个等待者（三路代理队列），主代理继续不占锁。两路修缺（`simplified-fetch-transport`、`spend-additional`/`whats-on-chain-chain-tracker`）在进行中，`peer-certificate-policy` 已通过。

**给后续轮次的提醒**：此刻不要重试 churn 类局部（`wallet-client`、`curve-unit`、`spend-chronicle-vector` 等），三路停笔前成功率极低；直接等守卫六项全过后统一窗口一次采完。

### 距 100% 仅剩 3 个文件 / 6 例（20260930 05:45）

守卫复跑：编译通过、`validate-plans` 135 检查 0 失败、分派表 150 局部／130 原文件／148 探针／112 环境变量且 **`unresolved=0`**、**无探针原文件只剩 3 个**；未过项为静默（三路代理在改）、覆盖率 **5323/5329**（缺 6 例）、工作树 88 个未提交。

剩余 6 例全在原语批最后一个代理手上：`AESGCM.man` 1、`AsyncCryptoBackend` 3、`BigNumber.dhGroup` 2。该批已完成 6/9（private-key、private-key-split、random、random-additional、hash-additional、symmetric-key-compatibility）。

### 重试结果（20260930 05:35）

趁 8 分钟静默重试 4 个 churn 类局部：**`wallet-client-substrate` 38/38/70 通过**（含篡改门禁）；`wallet-client`、`spend-chronicle-vector` 仍被“采集期间源码发生变化”拒绝；`curve-unit` 被 **`PeerCertificatePolicyTest.java` 的编译错误**挡住（认证修缺代理在飞文件，非曲线内容问题）。

结论再次确认：只要还有代理在改共享测试模块，任何采集都可能被拒；这类局部只能等全部停笔后的统一窗口。运行产物 114 个局部。

### 修复代理逐个收口（20260930 05:25）

- `peer-certificate-policy` 修复后采集通过：**15 例／35 输入／47 断言**（verify ✓）；`simplified-fetch-transport` 在采。
- `hash-additional` 采集通过：**9 例／22 输入／19 断言**（verify ✓），原语批已完成 5/9（private-key、private-key-split、random、random-additional、hash-additional）。
- 运行产物 112 个局部；覆盖率仍 5320/5329，未计划 9 例（AESGCM.man 1、AsyncCryptoBackend 3、BigNumber.dhGroup 2、SymmetricKeyCompatibility 3）在原语批在建。

### 最终窗口守卫脚本（20260930 05:15，主代理）

新增 `final-window-guard.sh [静默分钟数]`：开窗前必须六项全过——①最近 N 分钟无人改 Java；②`test-compile` 通过；③`validate-plans.py` 0 失败；④`build-full-run-probes.py` `unresolved=0`；⑤计划覆盖率 = 5329/5329；⑥SDK 工作树无未提交改动。任一失败即非零退出并打印失败项，避免“带病开窗”（窗口一开来源就冻结，返工代价极高）。

首次运行结果（20260930 05:15）：②③④通过（`validate-plans` 134 检查 0 失败；分派表 149 局部／129 原文件／147 探针／111 环境变量，`unresolved=0`，**无探针原文件仅剩 4 个**）；①⑤⑥未过——①静默未达（三路代理在改）、⑤覆盖率 5320/5329（缺 9 例，原语剩余批在建）、⑥SDK 工作树 86 个未提交改动（待冻结时提交）。

### 重采环境性失败（20260930 05:00）

对 5 个“环境性失败”局部重采：**`wallet-client-additional` 61/107/108** 与 **`block-headers-service` 19/47/24** 通过（含篡改门禁）；`wallet-client`、`wallet-client-substrate`、`curve-unit`、`spend-chronicle-vector` 仍被“采集期间源码发生变化”拒绝（三路修复代理在改 Java）。结论：这类被 churn 反复拒绝的局部只能留到最终静默窗口，逐个重试没有收益。

当前：局部 149 个、运行产物 110 个；覆盖率 99.7%（未计划 18 例，全在原语剩余批的 5 个文件）。

### 本轮批量采集与两处修复（20260930 04:40）

**采集批（17 个从未采过的局部）**：6 个通过并过门禁——`curve-additional` 20/23/40、`cryptononce` 7/30/12、`auth-build` 20/60/20、`session-manager` 11/35/14、`peer-boundary` 2/6/7、`spend-complex` 1/1/2；11 个失败，其中 **4 个是真内容问题**（`peer-certificate-policy` 的 `requestCertificates-*`、`simplified-fetch-transport` 的 `send-02`、`spend-additional` 的 `Spend.constructor-01`、`whats-on-chain-chain-tracker` 的“Java 入口多于 TS”），已派两路定点修复；其余 5 个（wallet-client ×3、curve-unit、spend-chronicle-vector、block-headers-service）是“采集期间源码变化”或他人在飞编译错误，属环境性，重采即可。

**peer 成为第一个 `currentCaptureVerified=true` 的局部**：30 例／147 输入／60 断言，五项验收全绿。其生产修复扩到**三处同族循环**（general + certificateRequest + certificate 回调），并做红绿验证（缺陷态 3/3 快速失败 CME，修复态 3/3 通过）。

**篡改门禁工具缺陷已修**：`local-evidence-gate.py` 的受保护站点判定按裸站点 ID 比较（重复执行实例身份是 `<站点>#<轮次>`），否则带固定语义规则的重复站点会被误判“篡改未被拒绝”；新增 `test-local-evidence-gate.py` 4 例自测（含非语义站点 `#2` 仍须被拒）。

**transaction-performance 交付**：25 例／6380 输入／70 断言，四项门禁全绿；实测该文件**无任何耗时断言**，“性能”只体现为规模，故全部按确定性结果逐值比较。

### peer 生产修复落地并采集通过（20260930 04:20）

`Peer.processGeneralMessage` 改为遍历监听器快照（原因：原测试的监听器会在回调里自注销，Java `LinkedHashMap` 迭代中删除会抛 CME 丢消息，而固定 TS 的 Map 迭代允许删除）。新增 `PeerGeneralListenerUnsubscribeTest` 作为额外 Java 回归（与上游断言分开计数）。

采集结果：**peer 30 例 / 147 输入 / 60 断言**，`verify` 与 `tamper`（两个 true）均通过；生产修复随 SDK 仓 `a9050d6` 提交。`random`（5 例）亦已采集落地。

剩余缺口仍为原语剩余批的 6 个文件（26 例）：Hash.additional 9、Random.additional 8、AsyncCryptoBackend 3、SymmetricKeyCompatibility 3、BigNumber.dhGroup 2、AESGCM.man 1；另有 `transaction-performance`（25 例）在建。

### 覆盖率 99%（20260930 04:05）

已计划 **5303/5329 = 99%**，未计划仅剩 **26 例**，全部在原语剩余批代理手上：`Hash.additional` 9、`Random.additional` 8、`AsyncCryptoBackend` 3、`SymmetricKeyCompatibility` 3、`BigNumber.dhGroup` 2、`AESGCM.man` 1。`Peer.test.ts` 30 例已随 peer 代理登记进入计划。局部登记 148 个，100 个已有运行产物。

### 登记一致性体检（20260930 04:40，主代理）

对 147 个登记局部做只读体检：**`input_plan`／`capture`／已登记运行产物路径全部存在，无悬空引用**；唯一异常是 **16 个 `auth-fetch-additional-*` 局部缺 `catalog.json`／`mapping.json`**（计划仍在、且已被合并进全局计划）。它们属早期专用局部、没有 `capture` 适配器（47 个无 capture 的局部之一），全量运行用的是全局 catalog/mapping 与探针分派，因此不影响最终验收；如后续要单独复采这些局部，需要重新生成它们的 catalog/mapping。

另：`beef` 内容已对齐（196/196 样本一致），但连续多次采集都被“采集期间源码发生变化”拒绝——并行代理仍在改 Java，该局部与其余绑定旧来源的局部一并在最终静默窗口重采。

### spend 修复批全部完成（20260930 04:25）

`chronicle` 3/4/3 与 `normative-vectors` 9/**7506**/340 已修复并采集通过（tamper 两个 true、`planValid=true`）。根因仍是投影/接线：①32 位字段两侧表示不同（TS 无符号 number vs Java 有符号 int，如 `sourceOutputIndex` 4294967295/-1、`transactionVersion` 2383752062/-1911215234）→ 探针共享库 `spend-probe-lib.cjs` 新增 `jsInt32`（按同一 32 位模式的有符号十进制）与 `jsSatoshis`（undefined→0 且不做截断）；②`formatOTDA` 被 `ignoreChronicle` 开关污染（TS 只给 `format` 的副本）；③`toBeInstanceOf` 期望值口径（改用全仓既有的 `Exception.class`，catch 已限定 RuntimeException）；④`checksum` 登记成 null。

影响面已核：口径改动对 <2^31 的值是恒等映射，新旧冻结计划逐字节相同，不影响其它局部。

**至此 spend/http 修复批 5 个局部（spend-core、spend-verifier、default-http-client、chronicle、normative-vectors）全部通过。**

### 本轮四项结论（20260930 04:15）

**1) BEEF 差异不是生产缺陷（重要更正）**：`toHex-194` 的“字节不同”是误判——Java 测试把 `isValid` 写在 `toHex` 之前，而重放按 `cursor` 位置比对样本，于是 Java 第一个断言就消费了 `toHex` 样本。恢复原测试顺序后，cb017c 用例 **196/196 样本逐字段一致**（`toHex` 两侧同为 13922 字符十六进制），`Beef.mergeProvenTxs`/`MerklePath.combine`/`trim` 一行未动。
　　续查发现：TS 的 `toAtomicBEEF`／`toUint8ArrayAtomic` **内部**会调用 `findAtomicTransaction`／`isAtomic`，探针把这些内部调用也记为入口样本，因此 Java 必须“消费样本但不加断言”（上游 `8_toBinaryAtomic` 只有 7 条断言）。已按此补两行调用；另删除 Java 侧自加的两条断言（TS 无对应）。

**2) spend/http 三局部全部修复并通过**：`spend-core` 20/20/34、`spend-verifier` 9/9/20、`default-http-client` 3/5/10，三次 `tamper` 均两个 true，preflight `planErrors=[]`、三局部 `planValid=true`。根因分别是：Jest 把类构造函数源码当 expected（改用 `assertThrowsClassSource` + 提取资源文件）、Java 直接 `new Spend(params)` 绕过重放入口（改 `replay.spend`）、环境投影 `globalFetch` 布尔不一致（改用已有 `globalFetchStub()`）。

**3) `test-map.json` 映射缺陷（孤例）**：`Transaction.performance.test.ts` 的 `it.each` 两个变体共用回调，constructed 变体被错挂到下一个用例的 6 个站点上，导致冻结必然失败。已授权修复为与 parsed 变体同站点（271/278/280）；代理写了精确检测器复核**全 133 个原文件中仅此一组**不一致，修后 `validate-plans.py` 129 通过／0 失败、`planErrors=[]`；断言实例总数 11555→11552（siteReviews 7554 不变）。

**4) `peer` 生产修复已落地**：`Peer.processGeneralMessage` 改为遍历快照并附注释说明（TS 允许迭代中删除、Java 需快照避免 CME 丢消息）。

**另**：`private-key` 7/55/**40021** 与 `private-key-split` 8/99/17 采集通过（前者验证“输入取样 + 断言逐执行登记”口径；代理并指出循环类随机用例必须两侧同熵，否则 4 万条断言无法逐值比较，已按固定熵记录回放）。

### 采集推进（20260930 04:00）

- `default-http-client` 3/5/10 ✓、`private-key` **7/55/40021** ✓（10,000 次循环 × 4 断言 = 4 万断言实例，验证了“输入取样 + 断言逐执行登记”的 1:1 口径在现有工具链下可跑通；最终全量的断言文件会相应变大，属预期）。
- spend/http 修复批只剩 `chronicle`、`normative-vectors` 重采；BEEF 字节差异诊断在跑第 4 轮采集。
- 运行产物 96 个局部；局部登记 144 个。

### peer 生产缺陷授权修复（20260930 03:45）

`peer` 代理定位到 `Peer.processGeneralMessage`（`auth/Peer.java:662`）的真实移植缺陷：Java 用 `for (var callback : generalCallbacks.values())` 遍历，而原测试的监听器会在回调里 `stopListeningForGeneralMessages` 自己 → `ConcurrentModificationException`，后续监听器不再执行、消息丢失、用例挂死；TS 的 `for (const callback of …values())` 允许迭代中删除，故 TS 正常。

已授权其应用 1 行修复（遍历 `new java.util.ArrayList<>(generalCallbacks.values())` 快照），并要求：加一条独立 Java 回归（两个监听器、第一个自注销、断言不抛 CME 且第二个仍收到消息、与上游用例分开计数）、跑 `PeerTest`/`PeerTransportErrorTest`/回归全绿、再登记+采集+篡改门禁。同时认可其证书 `fieldNames` 口径修正（字段密文逐证随机，比较字段名不削弱断言侧）。

另：`spend-verifier` 修复后采集通过（9 例／9 输入／20 断言），`spend-core` 亦已通过；spend/http 修复批次只剩 `chronicle`、`normative-vectors`、`default-http-client` 在重采。

### 缺口收敛到 94 例（20260930 03:30）

- `spend-core` 修复成功并采集成 20 例／20 输入／34 断言（`verify` 通过）——首采暴露的断言差异由修复代理解决。
- `item-locals.json` 刷新：**22/28 个实现事项计划完整**；未计划 94 例，全部落在在跑代理范围内（auth-sessions 30 由 peer 接线、hash-random 22／keys-signatures 8／symmetric 7／bignumber 2 由原语剩余批、transaction-complete 25 见下）。
- **补派最后一处无人认领的缺口**：`Transaction.performance.test.ts`（25 例）→ 局部 `transaction-performance`，并明确性能类口径：耗时阈值按“布尔是否满足 + 规模计数”记录，确定性字节/哈希/txid 仍逐值比较，跨语言毫秒不逐值比较。

### 分派表解析缺陷修复（20260930 03:40，主代理）

**现象**：spend（9）与 http-chain（5）等 14 个局部登记后**没有进入全量分派表**（`unresolved`），最终单次全量运行会拿不到它们的输入。

**根因**（两步定位）：①驱动里 `env[entry['ts_observations_env']] = str(evidence / 'ts-calls.raw.jsonl')` 的右值先按字面量求值，`existing()` 会到**计划目录**里找同名文件；这些代理的探针把 `ts-calls.raw.jsonl` 残留在了计划目录，于是被判成“冻结语料”（`file`）而不是“本轮产物”（`output`）；②`Div` 分支里 `('run_dir',)` 与判成 `file` 的右值组合没有兜底，最终 `plan['outputs']` 为空 → 该局部 unresolved。

**修法**（`build-full-run-probes.py`，两处最小改动）：`Div` 分支的语料直取规则排除 `run_dir`；`run_dir / x` 分支在右值被判成 `file` 时按 `output` 处理（取 basename）。
（先试过“按文件名过滤计划目录”，但会误伤 ARC 的合法语料 `MIGRATION_ARC_RANDOM_REPLAY`，已回退。）

**结果**：分派表 **123 原文件／141 探针／105 环境变量，`unresolved=0`**；无探针原文件 23→10，且其中**已计划却拿不到输入的用例为 0**——剩余 10 个原文件（Peer 30、Transaction.performance 25、PrivateKey 系列、Random 系列、Hash.additional、AESGCM.man、AsyncCryptoBackend、SymmetricKeyCompatibility、BigNumber.dhGroup，共 94 例）正是三路在跑代理的范围。

### beef 投影二次收敛与更实质的差异（20260930 03:20）

- 第一次采集失败在 `constructor-01`：探针的 `MerklePath` 构造投影仍带 `txid`，Java 侧对应站点也带。已把**构造投影**两侧一并收敛为只比较 `{offset, hash}`，重跑探针（21/21、390 输入、123 断言，注意轨迹文件是**追加写**，重跑前必须先删）后重新冻结，计划不变。
- 第二次采集：`constructor-01` 差异消失，只剩 `batchProvenMergeEqualsSequentialBytes`（caseId `cb017c09…`）的 **`toHex-194` 结果字节不同**——即同一输入下 TS 与 Java 生成的 BEEF 字节不一致。这已超出“投影/别名副作用”范畴，指向 Java 侧 `combineCompatibleBumps`／`MerklePath.combine`／`trim` 的合并语义差异。
- 已派诊断代理：先定位首个差异字节与长度差，对照 TS `Beef.mergeProvenTxs` + `MerklePath.combine/trim` 与 Java 同名实现，确认是否生产缺陷；是则最小改动修复并重新采集+门禁，否则给出可复现证据与可选处置。

### transaction 局部交付

`transaction`（`Transaction.test.ts` 61 例／233 输入／161 断言）代码侧完成并登记，离线自检：JUnit Launcher 61/61、java-inputs 233/233 全等、`compare_actuals` 零不一致。其冻结副本按登记的 8 个 Java 类裁剪用例（同文件另有 659 例向量局部），并把 8 份 Surefire 合并成一个 `<testsuites>`。

### 首采暴露内容问题与定点修复（20260930 03:00）

对**风险最高**的已交付局部先做小窗口采集，结果：`lrshiftnum` 4/28/29、`default-http-client-additional` 6/10/14 通过（含篡改门禁）；5 个局部失败——`spend-core`（断言实际结果不一致 `Spend.test.ts:580:7`）、`spend-verifier`（Java 缺一个输入用例 `db11cbc5…`）、`chronicle` 与 `normative-vectors`（同一族：`TransactionSignature.formatOTDA-02` 的入口/参数投影不一致）、`default-http-client`（`defaultHttpClient-01` 参数一致但 Java 返回 null）。均为**重放接线/投影问题**，非生产算法差异。

已派两路修复代理定点处理（一路修 chronicle+normative-vectors 的 format/formatOTDA 投影，一路修 spend-core/spend-verifier/default-http-client），要求改投影而不放宽断言、不改生产源码，修好后重采 + 篡改门禁 + preflight。

### beef 投影收敛（主代理亲自完成）

TS 的 `mergeProvenTxs` 会就地改写**调用方传入的** MerklePath（`group.paths[0]`），从而给其叶子补 `txid` 标志；Java 为新路径建新列表、不改调用方对象。这属别名副作用、非 API 结果（上游用例只断言批量与顺序合并的字节相等与 `isValid`，两侧皆过）。已把探针与 Java 重放的**输入侧**叶子投影收敛为 `{offset, hash}`，Beef 自身 bumps 的叶子仍逐值比较 `txid`；重跑探针（21/21、390 输入、123 断言）后重新冻结，**新计划与旧计划逐用例完全相同**，已重新登记。

### 代码优先策略见效（20260930 02:30）

切换后已有两路交回**代码侧完成**的简报，且都附了无锁离线证据：

| 代理 | 局部 | 用例/输入/断言 | 离线证据 |
| --- | --- | --- | --- |
| wallet-client | wallet-client／-additional／-substrate | 1/3/6、61/107/108、38/38/70 | javac 子集编译 0 error；JUnit launcher 100 全绿；Java 写出输入与样本 ID 完全对齐；复用 `evidence-bundle.build` 比对三局部全部 ok；篡改模拟两条路径均被拒；清空输入环境变量后行为不变 |
| curve | curve-unit／curve-additional | 18/82/61、20/23/40 | 隔离 javac 0 error；JUnit 38/38；输入同 ID 同序；`audit-tests.compare_actuals` 逐断言 **0 处不符** |

主代理独立核验（不占锁）：`validate-plans.py` **114 个标准局部通过、0 失败**；分派表 **110 原文件／126 探针／91 环境变量，`unresolved=0`**；上述五个局部均已登记且各自的原文件都已接入探针。

当前唯一编译阻塞：`transaction/TransactionInputReplay.java:356`（transaction 代理在飞）。其余代理继续代码收口。

### 死锁诊断与第二次策略切换（20260930 02:20）

**诊断**：最近 45 分钟全队 **0 个采集落地**。锁并非卡死（持有者是 480% CPU 的 Maven 运行），真正原因是**8 路代理并行编辑同一测试模块**：任何一个 2–4 分钟的捕获窗口内都会有别人的文件在飞，于是捕获必然以 `BUILD FAILURE`（他人在飞文件）或“采集期间源码发生变化”收场——互相等待形成死锁。

**切换**：已通知全部 8 路代理**停止一切采集**（recapture／tamper／聚焦 clean test 都不再执行，编译自检最多一次 `test-compile`），改为把代码侧做到“一编译就过”并用不占锁手段自检（javac 单编、`offline-*-check.sh`、`audit-tests.compare_actuals` 离线比对），然后交简报（用例/输入/断言数、文件清单、是否已登记、还差哪一步）。

**后续**：等所有人交完代码侧，主代理确认 `test-compile` 干净、提交在飞文件，再**独占**运行统一采集窗口（`recapture-all.sh final-<日期>`，含篡改门禁与 preflight）。期间不再允许任何并行 Maven 操作。

### 采集队列瓶颈（20260930 02:00）

各代理已进入采集阶段，但**共享 `run.lock` 成为唯一瓶颈**：现场有 5 个 flock 等待者 + 1 个 java 进程，多个局部已完成 TS 侧（01:32–01:54）却还在排队等 Java 侧 `clean test`。按每个局部 2–4 分钟估算，仅当前排队的采集就需要 1–2 小时；主代理因此**完全不占锁**（连编译复检都停掉），只做只读校验与登记。

推论：最终统一窗口（65+ 个局部）必须在**所有代理停止采集之后**独占运行，否则队列会互相拖延；窗口期间也不要并行做任何 Maven 操作。

### 结构覆盖率跃升（20260930 02:00）

- **已计划 4998/5329（93%）**，未计划降到 **331 例**；113 个标准局部的计划全部通过结构校验，且**没有任何用例被两个局部同时登记**（无冲突）。
- **计划已完整的事项 18 个**（上轮仅 4 个）：script-model 1104、wallet-contracts 253、byte-codecs 192、auth-transport 183、curve 144、wallet-wire 128、wallet-hosts 126、compat 122、wallet-client 100、transaction-base 74、wallet-keys 71、broadcasters 68 等。
- 仍有缺口：script-spend 91、transaction-complete 86、auth-sessions 45（代理登记中）、script-vectors 25、hash-random 22、transaction-beef 21（beef 在做）、http-chain 17、keys-signatures 15。
- `item-locals.json` 已按最新登记刷新，可用于最终窗口后逐事项出任务级对照。

### 编译恢复与本轮协调（20260930 01:30）

- 我修掉最后一个阻塞：`auth/SessionManagerInputReplay.describeOptional` 的返回类型从 `Map<String,Object>` 改为 `Object`（原语义是 `value ?? undefined()`，非空时可能是字符串），整模块恢复可编译。
- spend 代理确认 `clean test-compile` **exit=0、零错误**；http-chain 代理按我的提示把 10 处 `MockFetch` 改成 `new FetchHttpClient(fetch)` 后其文件零错误。
- 四路代理（wallet-client、curve、auth、http-chain）与 spend、beef、transaction、keys-small 已陆续进入采集阶段；`run.lock` 队列饱和（我的编译复检排队 600 秒超时），因此主代理暂停一切会占锁的操作，把窗口让给采集。
- 局部登记数 125（89 个有运行产物，正在快速增加）。

### 并发阻塞与协调（20260930 01:06）

- `script` 包在飞文件出现实参表**尾随逗号**语法错误（`ChronicleTest:27`、`LrShiftNumTest:23`、`NormativeVectorsTest:35/59`、`SpendAdditionalTest:94`、`SpendCoreTest:51`、`SpendVerifierTest:34`），导致整个测试模块编译失败，wallet-client／curve／auth 等代理的采集全部被拒；已定向通知 spend 代理优先修复。
- wallet-client 代理代码侧已完成并冻结计划：主 1 例／3 输入／6 断言、additional 61／107／108、substrate 38／38／70（合计 100 例／148 输入／184 断言），只等编译恢复。
- 局部登记数 118（89 个有运行产物）。

### 第八波待派（并发已满，等一路空闲立即派发）

**并发上限 8 个活跃子代理**（超出时报 `subagent limit reached`）。当前 8 路在跑，因此最后一批 46 例待有空位再派，范围已核准：

| 文件 | 缺口 | 局部名 |
| --- | --- | --- |
| `src/primitives/__tests/PrivateKey.test.ts` | 7 | `private-key` |
| `src/primitives/__tests/PrivateKey.split.test.ts` | 8 | `private-key-split` |
| `src/primitives/__tests/Random.test.ts` | 5 | `random` |
| `src/primitives/__tests/Random.additional.test.ts` | 8 | `random-additional` |
| `src/primitives/__tests/Hash.additional.test.ts` | 9 | `hash-additional` |
| `src/primitives/__tests/AESGCM.man.test.ts` | 1 | `aesgcm-man` |
| `src/primitives/__tests/AsyncCryptoBackend.test.ts` | 3 | `async-crypto-backend` |
| `src/primitives/__tests/SymmetricKeyCompatibility.test.ts` | 3 | `symmetric-key-compatibility` |
| `src/primitives/__tests/BigNumber.dhGroup.test.ts` | 2 | `bignumber-dh-group` |

注意：`Random*`／`AsyncCryptoBackend` 在 `audit-tests.py` 里已有固定语义规则，探针必须按原观察形状记录；`PrivateKey.test.ts` 的 10,000 次循环按既定 1:1 口径（输入样本取代表迭代 + 断言逐执行登记）。

### 第七波（补派，小范围）

- `keys-small` 代理：ECDSA.additional 12 + ECDH 2 + Secp256r1 7 + bug-31 1（22 例，四个小文件）。
- `http-chain` 代理：先核对 http-chain 事项中仍无计划的文件（约 47 例，含 BlockHeadersService 19 等），要求范围偏大时优先收口前 2 个文件并交剩余清单，不留半成品 Java。
- 计划结构校验：96 个标准局部全部通过（并行期仍可用 `validate-plans.py` 体检）。未计划用例仍为 565 例，等各代理登记后下降。

### 第六波（20260930 凌晨）与代理失败情况

- `tx-complete` 与 `curve/keys` 两路代理**中途失败且未留收尾报告**：前者未落任何文件；后者留下 `curve-locals.py`、`prepare-curve-local.py`、`capture-curve-local.py`、`capture-curve-additional-inputs.cjs`、`CurveAdditionalInputReplay.java`（可续用）。
- 因此改为**小范围重派**：`transaction`（Transaction.test.ts 61 例）与 `curve-unit`+`curve-additional`（38 例，续用前任产物）各一路。
- 失败代理提示：范围过大（8 个文件/75 例）时容易中途终止；后续按 1–2 个文件为单位派发。
- **PrivateKey.test.ts 的 10,000 次循环决策**：按 1:1 口径处理——探针记录有代表性的若干次迭代作为输入样本（供 `loopSamples` 结构覆盖），断言实例仍按每次执行登记（`<站点>#<轮次>`），即该用例的计划会达到 4 万级实例；这是原测试真实执行量的忠实反映，不做抽样削减。
- 本轮补采成功：`ecdsa` 15/31/21、`schnorr` 12/63/15（verify + tamper 通过）。`symmetric-key`、`ecies` 因“采集期间源码变化”失败，`chronicle-opcodes`、`simplified-fetch-transport-additional` 因他人在飞编译错误失败——四者代码侧均已就绪，随最终窗口重采。

### 第五波分工（20260930 凌晨已派发，5 路并行）

| 代理 | 范围 | 用例 |
| --- | --- | --- |
| beef 代理 | `Beef.test.ts` 21 例（镜像 `BeefTest`） | 21 |
| wallet-client 代理 | WalletClient 三文件 | 100 |
| auth 代理 | auth-sessions 六文件 + SimplifiedFetchTransport 基础 3 例 | 88 |
| spend 代理 | script-spend 缺口 91 + script-vectors 缺口 26 | 117 |
| tx-complete 代理 | `Transaction.test.ts` 61 + `Transaction.performance.test.ts` 25 | 86 |
| curve/keys 代理 | Curve.unit 18 + Curve.additional 20 + keys-signatures 剩余 37 | 75 |

派完后仍未分配的缺口：hash-random 22、symmetric 7、bignumber 2、http-chain 47（共 78 例），等有代理空闲再派。

### 最终窗口规模与预计耗时（20260930 凌晨）

可重采局部 **65 个**（58 个已有运行产物）；每个局部的 Java 侧都要一次无过滤口径的 `clean test -Dtest=<类>`，模块重编译主导，预计 **2–3 小时**串行。窗口内禁止任何人改 Java 源码，否则来源摘要前移、该批作废。当前唯一在改 Java 的是 `beef` 代理（`BeefInputReplay.java` 还剩 1 处类型错误），其余 10 个代理均已收工。

### 统一窗口顺序（待 beef 落地后执行）

1. `./lock.sh ./mvn.sh -f metanet4j-bsv-sdk/pom.xml test-compile` 确认编译干净；
2. `./recapture-all.sh final-<日期>`（对所有登记了 capture 的局部逐个重采 + 篡改门禁，目录与来源统一）；
3. `./lock.sh python3 full-evidence-preflight.py --output .cache/evidence/preflight-final-<日期>.json`（期望 `planErrors=[]`、大量 `currentCaptureVerified=true`）；
4. 对可结项事项跑 `local-task-parity.py` 出任务级报告并更新 feature_list。

## 协作策略切换：先收口代码，统一窗口再采集（20260929 晚）

`run.lock` 一度积压 12 个等待者（队首约 30 分钟），且测试模块被多份在飞文件反复打断编译。已通知全部在跑代理：**停止重试式采集**，改为①优先修完各自文件的编译错误（当前阻塞项：`HashTest`、`PublicKeyTest`、`PublicKeyAdditionalTest`、`ReductionContextTest`、`SignatureTest`）；②把探针、计划、Java 重放、测试接线、登记等代码侧做完；③需要验证时低频取锁（先 `test-compile`，失败等 5 分钟）；④各自交“待采集清单”。随后由主代理在静默窗口按登记表串行重采（`recapture-all.sh`）并出任务级对照。

### hex-bn 转换器（本轮已完成部分）

- 新增 `prepare-hex-bn-inputs.py`：把旧管线 `replay-legacy-inputs.emit_ts` 包成 CLI（`emit-ts` 子命令），`capture-legacy-side.py` 改为调用它；用既有轨迹验证：输入 71 行、断言 71 行，身份与值与旧输出**逐项一致**。
- 两个旧探针补了“固定原文件：src/...test.ts”声明，分派表因此能把探针唯一对应到原文件（原文件解析数 66→77、探针 80→93）。
- 仍未解析：分派表无法为 `hex-bn` 解析 raw 轨迹的环境变量取值（旧驱动用 `evidence / (kind + '.raw.jsonl')` 计算，解析器不认），且该局部断言来自旧转换器而非 `capture-parity`。**待办**：在 `build-full-run-probes.py` 增加 `full-run-overrides.json` 覆盖机制，或把 hex-bn 升级为标准局部（探针 + `emit-assertion-observations`）。

## 全量运行接口已交付（20260929）

`fullRun` 段已写入 `full-evidence-locals.json`，preflight 的 `missingFullRunInterfaces=[]` 达成。新增：`build-full-run-probes.py`（生成 `full-run-probes.json`：84 局部／66 原文件／80 探针）、`capture-full-dispatch.cjs`（按 testPath 分派探针）、`run-full-ts-capture.py`（全量 TS + raw→emit-ts 转换 + 采集后校验）、`run-full-java-capture.py`（无过滤 `clean test` + 全部 `MIGRATION_*_TS_INPUTS` 指向本轮 ts-inputs + Surefire 汇总）。自测：三类代表子集 Jest 69/69、官方 `evidence-bundle capture` 端到端 EXIT=0（inputs 251 行、assertions 159 行、missing/extra/duplicates 均为 0）。

**严格模式仍会拒绝的三类缺口**（最终全量运行前必须清零或明确处置）：
1. `unresolved` 2 个：`chronicle-opcodes`（无可用探针）、`hex-bn`（跨 2 原文件 2 探针且无 CLI 转换器）；
2. **67 个 catalog 原文件没有任何探针**（auth 8／compat 2／primitives 25／script 13／transaction 14／wallet 5）；
3. **30 个 raw 局部缺 CLI emit-ts 转换器**（auth-fetch-property、bignumber-*、byte-base58、cached-keyderiver、drbg29、http-wallet-json、jacobian、json-byte-encoding、keyderiver、mnemonic-*、origin-header5、point-*、protowallet*、script-spend-shared-vectors、transaction-shared-vectors、utils-property、validation-helpers、wallet-error、wallet-property、wallet-wire、werr-constructors）。

另：Java 侧 35 个 `MIGRATION_*_TS_INPUTS` 可全部共用同一份 `<runDir>/ts-inputs.jsonl`；另有 38 个 `-Dmigration.*` 冻结语料属性仍驱动部分重放（不消费本轮输入），属“局部尚未升级到标准接口”。

## 全量分派策略（已拍板）

`run-full-ts-capture.py` 必须把三类探针都纳入分派：直写型、raw 型（再经 `prepare-*-local.py emit-ts` 转换）、外部语料型（由分派器按适配器 TS 分支的 `env[...]` 设置 `MIGRATION_*_RANDOM`／`_VECTOR_CATALOG`／`_META`／`_TS_CLOCK` 等语料变量）。**默认严格**：无法解析探针或语料的原文件必须让整轮非零退出并打印缺口，同时写 `unmapped-files.jsonl`／`unresolved-probes.json`；`--allow-unresolved` 只允许子集自测使用，不得出现在 `fullRun.tsCommand` 里。全量运行不允许出现“绿但不完整”。

## 计划结构校验（并行期可用）

`python3 validate-plans.py` 只读计划／catalog／mapping，不要求源码稳定，可随时运行；preflight 因并行改源码被拒时用它先做结构体检。当前结果：70 个标准局部计划全部通过（0 失败），16 个 `captureKind=specialized-local`（auth-fetch 系列，`deriveCatalogFromPlan`）走各自专用校验，不在本脚本范围。

## 收尾统一重采

并行子代理的 Java 改动会不断推进来源摘要，因此**收尾时**在所有人停止改源码后执行一次统一重采：`./recapture-all.sh <日期标签> [局部名...]`（不传局部名则重采全部登记了 capture 适配器的标准局部，并逐个跑篡改门禁）。随后 `python3 full-evidence-preflight.py` 应显示这些局部 `currentCaptureVerified=true`；再对每个待结项用 `python3 local-task-parity.py --task <事项> --local ... --output <目录>` 出任务级报告，最后提交。

## 验证与收工

- `migration-impl-transaction-base` 五个文件全部落地标准双侧局部（fee-model 18、live-policy 8、ef-cache 4、transaction-additional 20、signature-additional 24，合计 74 例／150 输入／115 断言），同一 Java 来源下 verify 与 tamper 通过，聚焦 `clean test` 74／74。任务级对照与 `done` 待并行子代理的 Java 改动提交后统一执行。
- 广播器四文件已结项（68/68、169/169，提交 `1f1c660` 记录适配器升级）；xdm-browser-boundary、react-native25、wallet-wire 三局部已验证，钱包宿主与 WalletWire 两项仍缺 HTTPWalletWire 46 例、window.CWI 31 例；transaction-beef 五文件 83 例已派给第三个子代理。
- 并行协作已启用：`lock.sh` 串行化共享目标工程的 Maven／采集，`register-local.py` 带 flock 登记局部，`doc/子代理采集作业说明-20260929-175251.md` 是子代理作业规范；两个后台子代理分别处理广播器五局部与钱包宿主／WalletWire 三局部。
任务级对照用 `python3 local-task-parity.py --task <id> --local <局部> … --output <目录>`（复用 `audit-tests.py` 的比较规则并核对冻结用例覆盖）。`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。本代理 shell 的 PATH 前置 DSH checkout 的 `node_modules/.bin`，`pnpm --version` 会解析到 11.7.0，使 `./init.sh` 报“全局 pnpm 版本未变”失败；去掉该 PATH 项后 `./init.sh` 全绿（全局 pnpm 仍为 11.23.0），任务命令走 `./pnpm.sh`，不受影响。

每个已完成 Java 功能均在目标仓库独立提交。对称与 Compat 功能项状态已更新；继续逐项核对依赖链、当前接口行为和 P0 全量输入证据。新增 Java 变更后重跑完整 clean test 并封存 XML；现有完整回归快照绑定 `c23c6f6`。其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
