# 会话交接

## 唯一下一步

按最新拆分执行 migration-impl-curve。activeItem=null，nextItem=migration-impl-curve；features 共 43 项，11 done、32 not-started，其中编码任务 28 项、已完成 Hex、BigNumber 构造基础、完整 BigNumber/模运算、哈希/HMAC/PBKDF2/随机源 4 项。21 组 apiBatches 是嵌入设计清单，不作为独立执行队列。

读取沿途规则、计划及状态，运行 ./init.sh、node audit-api.cjs batches，并检查各仓状态。代码/测试/POM 仅允许改 metanet4j-bsv-sdk，任务根目录维护计划/映射/验证工具；其他四工程及固定 TS 只读。不要把检查器通过算成 SDK 通过。

## 编码任务的验收

具体范围与唯一状态在 feature_list.json；公共步骤/条件引用 implementationPolicy。sourceFiles 明确实现/前检范围，apiCompletionFiles 对 133 个 API 文件各承担一次完整实现收口；testFiles 对 133 原文件/5329 用例各分配一次；regressionTestFiles 只追加回归，不重复计数；26 个辅助文件全部纳入 fixtureFiles。

每项先复核所用 API，再补齐本项输入/采集和映射，逐行为执行 TS 参考、Java RED→GREEN，最后完整运行所分配原测试、目标工程 clean test、此前已完成项累计实际结果对照。保存当前版本绑定的原始报告和可复跑命令后才能 done；局部比较 formalAcceptance=false。发现范围外的必需依赖，先补入范围或合并任务并重跑分配检查，不能用桩/占位算法掩盖依赖。

## 已完成与恢复入口

migration-impl-hash-random 目标工程提交 9fbcc9d：Hash、SHA1/SHA256/SHA512、RIPEMD160、SHA1/SHA256/SHA512 HMAC、PBKDF2-HMAC-SHA512、DRBG、Random。6 个原测试文件共 86 个 Java 用例；累计 Java 映射 296/5329，siteReviews 962；目标工程 clean test 297/297。

可复跑命令：
- `./verify.sh bsv-test`：目标工程 clean test，297/297，零失败/错误/跳过。
- TS 批次 `.cache/evidence/hash-random-final-20260920-175813-4236q/` 保存 6 文件 Jest JSON、Surefire XML、revision、命令和 summary.json；TS 86/86。
- 前批证据 `.cache/evidence/bignumber-final-20260920-173943-23798q/`（174 用例）与 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/`（Hex+构造 36 用例）。
- `node audit-api.cjs batches --batch migration-api-hash-random` 与 `node test-audit.test.cjs` 通过。

该批次未生成 86 个新用例的逐断言 TS/Java 原始值文件，summary.json 标记 formalAcceptance=false；Random 的 Node/浏览器分支以可注入 Runtime 适配，未模拟真实 JS 宿主。无过滤 API check 和六模块 audit-tests.py check 仍按完整范围拒绝未迁移项（当前缺失 5033 Java 映射）。

## 固定边界

Random 使用宿主安全随机源，不在 Java 中伪造 globalThis/self/window/process 分支；SHA512HMAC.outSize 保留上游登记的 32，FastSHA.destroy 不设置 destroyed。PBKDF2 仅支持 sha512，其他 digest 报原消息。DRBG 仅用于 RFC 6979 内部非随机用途，不作为通用随机源。

scopeReview=pending；通用输入重放、随机/属性采集、全量 API 与最终收口门禁未完成。全部任务独立验收后再完成六模块联合验收，不能以内部任务完成代替完整模块验收。此前完整 TS 基线 .cache/evidence/ts-baseline-20260920-123124/ 为 5329/5329，manual 536870928 字节、37:16.72；无相关变化不重复长基线，但最终完整验收不得遗漏。

Maven/pnpm 仅经任务脚本；Node 嵌套 spawn 的审计可能在沙箱 EPERM，应宿主提权运行取得真实检查结果。只提交任务明确路径，不混入根仓既有规则/技能/.opencode 改动；不推送。独立 Java 仓本批提交 9fbcc9d，工作树保持干净。
