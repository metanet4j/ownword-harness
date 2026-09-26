# 会话交接

## 唯一下一步

`activeItem=nextItem=migration-impl-byte-codecs`，状态 in-progress。先读取 [feature_list.json](feature_list.json) 的本项 sourceFiles/testFiles/acceptanceFocus 与 [API 契约](doc/完整模块与API映射-20260920-122800.md)，完成 ReaderUint8Array、WriterUint8Array、utils 的 API 前检；然后通读六份固定原测试并按一一映射的 RED→GREEN 推进。冻结清单是 166 个注册用例，`utils.property.test.ts` 前两例各至少 300 次生成样本，不能将样本数混入用例分母。

## 已完成曲线验收

- Java 工程功能提交 `611b7af`、工程说明提交 `324e9af`，工作树干净。BasePoint/Curve/Point/JacobianPoint 及 Point.ts 的文件级 BigInt 导出已收口；其余四个 Java 工程和固定 TS 未修改。
- `.cache/evidence/curve-final-20260926-122724/` 保存 TS 三份 Jest 报告（覆盖五个原文件）、原断言轨迹、Java 全量 Surefire XML、`bsv-test` 原始日志及摘要、API 批次检查、逐断言报告和 SHA-256 manifest。固定 TS 原测试 144/144、Java post-commit `clean test` 460/460；逐断言 236/236 匹配，missing/uncompared=0，`taskAcceptancePassed=true`、`formalAcceptance=false`。
- `api-map.json` 的 curve 批次 153/153 reviewed，`test-map.json` 的曲线五文件 144 个用例/375 个 AST 位置全部映射；全局分别为 816/3576 声明与 440/5329 原用例。
- 复跑入口：`./init.sh`、`node audit-api.cjs batches --batch migration-api-curve`、`./verify.sh bsv-test`、`python3 task-parity.py --task migration-impl-curve --ts .cache/evidence/curve-final-20260926-122724/ts-parity.jsonl --java .cache/evidence/curve-final-20260926-122724/java-parity.jsonl --output <新报告路径>`。集成/API 检查按工作区规则使用宿主提权。

## 累计边界

先前 Hex、BigNumber 与哈希随机任务的逐断言证据在 `.cache/evidence/parity-final-20260920-191152-19403q/`。整模块全量 API、随机/属性重放通用收口、六模块最终测试门禁仍待后续事项；无过滤 `audit-api.cjs check` 和 `audit-tests.py check` 不因曲线单项通过而放宽。

Maven/pnpm 仅经任务脚本；不推送、不广播交易、不调用真实钱包或外部业务接口。根仓已有无关规则/技能/.opencode 修改，提交时仅选择本任务路径。
