# 当前进度

## 执行位置

`activeItem=nextItem=migration-impl-byte-codecs`，已进入字节编解码与 Reader/Writer 任务。43 个执行事项中 12 done、1 in-progress、30 not-started；28 个编码任务中 5 done、1 in-progress、22 not-started。权威状态与依赖见 [feature_list.json](feature_list.json)。

## 已验收结果

- 曲线任务 `migration-impl-curve` 已通过：固定 TS 五个原文件 144/144；Java 提交 `611b7af`（功能）和 `324e9af`（工程说明）后执行 `./verify.sh bsv-test`，累计 460/460，失败、错误、跳过均为 0。`task-parity.py` 对照 144/144 个原用例、236/236 条原断言，缺失、未比较、额外 Java 原断言均为 0。独立证据目录为 `.cache/evidence/curve-final-20260926-122724/`，局部报告 `formalAcceptance=false`。
- 曲线四个源文件的 153/153 声明已映射并复核；`node audit-api.cjs batches --batch migration-api-curve` 通过。累计完成 values、hash-random、curve 三组 API，816/3576 项；剩余 2760 项。
- 累计原测试映射 440/5329，尚余 4889。此前完成的 Hex 8、BigNumber 构造 28、完整 BigNumber/模运算 174、哈希/HMAC/PBKDF2/随机源 86 个原用例仍在本次 Java 全量回归中通过；前批逐断言报告见 `.cache/evidence/parity-final-20260920-191152-19403q/`。
- `./init.sh` 已通过固定 TS、工具链、缓存隔离与任务清单检查。完整六模块 `audit-tests.py check` 和无过滤 `audit-api.cjs check` 仍按剩余范围拒绝通过，不能把单项验收当作整模块完成。

## 下一步

`migration-impl-byte-codecs` 的冻结清单为 Reader.test.ts、ReaderUint8Array.test.ts、Writer.test.ts、WriterUint8Array.test.ts、utils.property.test.ts、utils.test.ts，共 166 个注册用例；其中两个 property 用例各至少 300 次生成样本。先做本组 API 前检和原文件/辅助资料通读，再按测试契约逐行为 RED→GREEN、采集两端真实输入/断言，累计运行 Java `clean test`。WUA-ZERO-CAPACITY 只按已授权的最小修复实施，额外 Java 回归单列。

仅修改 `metanet4j-bsv-sdk` 的工程代码、测试和 POM；固定 TS 与其他四个 Java 工程只读。根仓既有无关改动保留，不推送、不广播交易或调用真实钱包/外部业务接口。
