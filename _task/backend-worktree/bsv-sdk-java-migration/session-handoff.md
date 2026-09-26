# 会话交接

## 唯一下一步

`activeItem=nextItem=migration-impl-keys-signatures`，状态 in-progress。读取 [feature_list.json](feature_list.json) 的本项七个 sourceFiles、11 个 testFiles、两个 BRC42 fixtureFiles 与 acceptanceFocus，并对照 [API 契约](doc/完整模块与API映射-20260920-122800.md)先做 API 前检。冻结清单是 146 个注册用例；随机 k/密钥需采集实际输入、固定并在 Java 重放。

## 已完成字节验收

- Java 工程提交 `e8b83f4`，工作树干净；完整 ByteView、旧/新 Reader/Writer、Utils 均已实现。固定 TS 六个原测试文件 192/192；Java post-commit `clean test` 656/656；逐断言 1242/1242 匹配，missing/uncompared/extra=0。
- `.cache/evidence/byte-final-20260926-125839/` 保存四份 Jest 报告、两端原断言轨迹、32 份 Java Surefire XML、`bsv-test` 日志与摘要、API 分批检查、检查器自测、固定 property 输入及 SHA-256 manifest。两个 property 用例各重放 300 组；WUA-ZERO-CAPACITY 的 4 个 Java 额外回归单列。`taskAcceptancePassed=true`、`formalAcceptance=false`。
- 本项六文件 192 个用例/467 个 AST 位置均在 `test-map.json` 映射；累计 632/5329。values 批次 371 个设计声明已复核，累计三组 API 816/3576。
- 复跑入口：`./init.sh`、`node audit-api.cjs batches --batch migration-api-values`、`./verify.sh bsv-test`、`python3 task-parity.py --task migration-impl-byte-codecs --ts .cache/evidence/byte-final-20260926-125839/ts-parity.jsonl --java .cache/evidence/byte-final-20260926-125839/java-parity.jsonl --output <新报告路径>`。集成/API 检查按工作区规则使用宿主提权。

## 累计边界

先前 Hex、BigNumber 与哈希随机任务的逐断言证据在 `.cache/evidence/parity-final-20260920-191152-19403q/`，曲线证据在 `.cache/evidence/curve-final-20260926-122724/`。整模块全量 API、其余随机输入重放、六模块最终测试门禁仍待后续事项；无过滤 `audit-api.cjs check` 和 `audit-tests.py check` 不因单项通过而放宽。

Maven/pnpm 仅经任务脚本；不推送、不广播交易、不调用真实钱包或外部业务接口。根仓已有无关规则/技能/.opencode 修改，提交时仅选择本任务路径。
