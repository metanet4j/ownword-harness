# 会话交接

## 当前执行

`activeItem=nextItem=migration-impl-symmetric`；`migration-impl-http-chain` 并行进行，两项状态均为 in-progress。按 [feature_list.json](feature_list.json) 的 sourceFiles、testFiles、fixtureFiles 与 acceptanceFocus 执行；API 行为依据见[契约](doc/完整模块与API映射-20260920-122800.md)。

对称任务有五个原测试文件、52 个注册用例、60 项 API 声明；`AESGCM.man.test.ts` 的一例必须执行原 536,870,928 字节规模，避免用通用逐元素 JSONL 采集造成内存膨胀，另保存流式 SHA-256、断言及资源报告。HTTP/chain 任务有九个原测试文件、78 个注册用例、113 项当前源文件 API 声明；Promise rejection 的 `.rejects` 链和 `toBeDefined` 采集须在共享 `capture-parity.cjs` 补齐后重采，不能把缺失断言视作通过。

## 已验收基线

- Java 目标工程提交 `67ccb86`，密钥与签名七个源文件及 11 个原测试文件已迁移。固定 TS 146/146，共享 Java `clean test` 802/802；逐断言 40242/40242 匹配，missing/uncompared/extra=0。原 10,000 次随机私钥循环与 10,078 次随机调用保持原规模并重放。
- `.cache/evidence/keys-final-20260926-133303/` 保存 Jest、Surefire XML、两端断言轨迹、随机输入、任务映射和 SHA-256 manifest。`taskAcceptancePassed=true`、`formalAcceptance=false`；API-05 仅七个当前源文件 129 项完成，归 `TransactionSignature.ts` 与 `primitives/index.ts` 的 48 项继续待后续任务。
- 累计已映射 778/5329 原用例和 945/3576 API 声明。`./init.sh`、`node audit-api.cjs batches`、`node test-audit.test.cjs`（宿主环境 41/41）通过。

## 复跑入口与边界

`./verify.sh bsv-test` 验证累计 Java；`python3 task-parity.py --task migration-impl-keys-signatures --ts .cache/evidence/keys-final-20260926-133303/ts-parity.jsonl --java .cache/evidence/keys-final-20260926-133303/java-parity.jsonl --output <新报告路径>` 验证密钥原断言。集成/API 检查按工作区规则使用宿主提权。完整六模块门禁继续使用无过滤 `audit-api.cjs check` 与 `audit-tests.py check`；局部通过不能代替最终验收。

Maven/pnpm 仅经任务脚本；固定 TS 与其他四个 Java 工程只读。根仓已有无关规则、技能和 `.opencode` 修改，提交时仅选择本任务路径。
