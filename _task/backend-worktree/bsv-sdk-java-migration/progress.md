# 当前进度

## 执行位置

`activeItem=nextItem=migration-impl-symmetric`；`migration-impl-http-chain` 同步进行。43 个执行事项中 14 done、2 in-progress、27 not-started；28 个编码任务中 7 done、2 in-progress、19 not-started。权威状态与依赖见 [feature_list.json](feature_list.json)。

## 已验收结果

- 密钥与签名任务 `migration-impl-keys-signatures` 已通过：Java 工程提交 `67ccb86`，固定 TS 11 个原文件 146/146；共享 Java `clean test` 累计 802/802，失败、错误、跳过均为 0；提交后的 `task-parity.py` 对照 146/146 个原用例、40242/40242 条原断言，缺失、未比较、额外 Java 原断言均为 0。证据目录 `.cache/evidence/keys-final-20260926-133303/`，局部报告 `formalAcceptance=false`。
- 10,078 次 TS Random 实际输入与 Java 重放资源逐项一致，其中 10,000 次私钥循环保持原规模；BRC42 私钥、公钥向量及 ECDSA、Schnorr、P-256 输入均已执行。篡改循环第 20,000 条 Java 实际值后比较器拒绝通过；检查器自测在宿主环境 41/41 通过。
- 本项 146 个用例、356 个 AST 位置已映射，累计 778/5329，尚余 4551。七个完整源文件的 129 项 API 已复核，累计 945/3576；API-05 还有归后续交易任务的 48 项，批次保持 in-progress。此前已完成项在共享 Java 全量回归中继续通过。
- `./init.sh` 与 `node audit-api.cjs batches` 已通过。无过滤 `audit-api.cjs check` 和六模块 `audit-tests.py check` 仍由剩余范围决定。

## 当前工作

对称任务的 AESGCM、AsyncCryptoBackend、SymmetricKey 与五个原测试文件由子代理实施；其中 manual 测试保留原 536,870,928 字节规模，另用流式摘要记录实际输入与结果。HTTP/chain 任务依赖已完成的字节模块，另一子代理并行处理 13 个源文件和九个原测试文件。两项完成后按各自冻结用例、API、随机输入及累计 `clean test` 收口并提交。

仅修改 `metanet4j-bsv-sdk` 的工程代码、测试和 POM；固定 TS 与其他四个 Java 工程只读。根仓既有无关改动保留，不推送、不广播交易或调用真实钱包/外部业务接口。
