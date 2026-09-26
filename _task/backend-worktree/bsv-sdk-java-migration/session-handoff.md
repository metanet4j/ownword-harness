# 会话交接

## 当前执行

`activeItem=nextItem=migration-impl-symmetric`；`migration-impl-wallet-contracts`、`migration-impl-transaction-base`、`migration-impl-transaction-beef`、`migration-impl-wallet-json` 并行实施。按 [feature_list.json](feature_list.json) 的源文件、测试文件、依赖与验收重点执行；行为依据见[契约](doc/完整模块与API映射-20260920-122800.md)。

对称任务 52 个原用例中 51 个普通用例与 384 条实际断言已匹配；`AESGCM.man.test.ts` 本轮 90 分钟超时、退出码 124，未产生 Jest 结果或三条轨迹，未验收，证据 `.cache/evidence/symmetric-manual-ts-timeout.json`。脚本模型已通过累计提交后验收。交易基础 74／74 个原 Java 用例隔离通过，等待 TS 逐断言收口。BEEF 21 个与 BeefParty 3 个原 Java 测试已写，MerklePath 59 例待实现。钱包协议目标提交 `57c17c7`，固定 TS 253／253、1003／1003，真实 BEEF 隔离集成 255／255；累计 Maven 待证明层接入。钱包 JSON 58 例在并行实施。

## 已验收基线

- 脚本模型目标工程提交 `1001f22`；独立干净工作副本累计 `clean test` 1985／1985，失败、错误、跳过为 0。固定 TS 四文件 1104／1104，提交后逐实际值 4276／4276，missing／uncompared／extra=0；三次随机输入和 1030 条原向量保留。证据在 `.cache/evidence/script-model-final-20260926-141500/`，本项 `taskAcceptancePassed=true`、局部 `formalAcceptance=false`。
- Java 目标工程最新完整 HTTP／chain 提交 `857928e`；独立干净工作副本累计 `clean test` 880／880，失败、错误、跳过为 0。固定 TS 九文件 78／78，提交后的逐实际值比较 133／133，missing／uncompared／extra=0；离线网络 fixture、Jest、Surefire XML、两端轨迹和哈希清单在 `.cache/evidence/http-chain-final-20260926-140200/`。本项 `taskAcceptancePassed=true`、局部 `formalAcceptance=false`。
- 密钥与签名提交 `67ccb86`：固定 TS 146／146、提交后断言 40242／40242，10078 次随机输入重放一致。证据在 `.cache/evidence/keys-final-20260926-133303/`。
- 累计原用例映射 1960／5329，API 声明映射 1398／3576。API-11 剩余 45 项归广播任务，仍 in-progress；对称 API-06 已复核 60／60，脚本模型 API-07 已复核 280／280。

## 复跑入口与边界

`./verify.sh bsv-test` 验证当前累计 Java；HTTP 已验收提交可通过 `python3 task-parity.py --task migration-impl-http-chain --ts .cache/evidence/http-chain-final-20260926-140200/ts-parity.jsonl --java .cache/evidence/http-chain-final-20260926-140200/java-parity.jsonl --java-worktree /tmp/bsv-http-accept-857928e --output <新报告路径>` 复核。六模块完整门禁仍是无过滤 `audit-api.cjs check` 与 `audit-tests.py check`。集成、接口测试按工作区规则在宿主提权环境执行。

Maven／pnpm 仅经任务脚本；固定 TS 与其他四个 Java 工程只读。根仓已有无关规则、技能和 `.opencode` 修改，提交时仅选择本任务路径。
