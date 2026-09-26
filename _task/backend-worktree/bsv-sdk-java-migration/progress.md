# 当前进度

## 执行位置

`activeItem=nextItem=migration-impl-symmetric`；`migration-impl-wallet-contracts`、`migration-impl-transaction-base` 并行进行。43 个执行事项中 16 done、3 in-progress、24 not-started；28 个编码任务中 9 done、3 in-progress、16 not-started。权威状态与依赖见 [feature_list.json](feature_list.json)。

## 已验收结果

- 脚本模型任务 `migration-impl-script-model` 已通过：Java 工程提交 `1001f22`，固定 TS 四个原文件 1104／1104；干净工作副本累计 Java `clean test` 1985／1985，失败、错误、跳过均为 0；提交后逐断言 4276／4276，missing／uncompared／extra 均为 0。1030 条原脚本向量和三次随机输入重放保留，另有 1 条 Java 边界回归。证据目录 `.cache/evidence/script-model-final-20260926-141500/`，局部报告 `formalAcceptance=false`。
- HTTP／chain 任务 `migration-impl-http-chain` 已通过：Java 工程提交 `857928e`，固定 TS 九个原文件 78／78；独立干净工作副本的累计 Java `clean test` 880／880，失败、错误、跳过均为 0；提交后的逐断言对照 78／78 个原用例、133／133 条实际值，missing／uncompared／extra 均为 0。固定 mock 全程离线。证据目录 `.cache/evidence/http-chain-final-20260926-140200/`，局部报告 `formalAcceptance=false`。
- 13 个完整 HTTP／chain 源文件的 113 项 API 已复核。API-11 另 45 项广播实现归后续任务，批次保持 in-progress；累计 API 映射 1398／3576，其中对称任务 60 项、脚本模型 280 项已审查。HTTP 原用例 78 个、AST 位置 236 个已映射，累计 1960／5329；脚本模型 1104 个用例、228 个 AST 位置已合并。
- 密钥与签名任务 `migration-impl-keys-signatures` 已通过：Java 工程提交 `67ccb86`，固定 TS 11 个原文件 146／146；累计 Java `clean test` 802／802；提交后逐断言 40242／40242，缺失、未比较、额外 Java 断言均为 0。10,078 次 TS Random 实际输入与 Java 重放逐项一致，其中私钥循环 10,000 次保持原规模。证据目录 `.cache/evidence/keys-final-20260926-133303/`。
- `./init.sh`、API 批次检查及审计自测已在密钥任务验收时通过；HTTP 状态更新后的批次复核见本次命令记录。六模块无过滤检查继续由剩余任务推进。

## 当前工作

对称任务五个原测试文件共 52 个用例；普通四文件 51／51、384／384 断言已通过，536,870,928 字节 manual 用例正按原规模验证。脚本模型已验收；交易基础任务正实施 10 个源文件和 74 个原用例，BEEF／MerklePath 的真实解析与序列化边界已开始提供。钱包契约原 TS 六文件 253／253 已采集，正在实施 Java 协议类型、错误与验证边界。

仅修改 `metanet4j-bsv-sdk` 的工程代码、测试和 POM；固定 TS 与其他四个 Java 工程只读。根仓既有无关改动保留，不推送、不广播交易或调用真实钱包／外部业务接口。
