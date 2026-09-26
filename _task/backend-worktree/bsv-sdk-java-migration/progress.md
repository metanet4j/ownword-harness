# 当前进度

## 执行位置

`activeItem=nextItem=migration-impl-keys-signatures`，已进入密钥与签名算法任务。43 个执行事项中 13 done、1 in-progress、29 not-started；28 个编码任务中 6 done、1 in-progress、21 not-started。权威状态与依赖见 [feature_list.json](feature_list.json)。

## 已验收结果

- 字节任务 `migration-impl-byte-codecs` 已通过：Java 工程提交 `e8b83f4` 后执行 `./verify.sh bsv-test`，累计 656/656，失败、错误、跳过均为 0。固定 TS 六个原文件 192/192；`task-parity.py` 对照 192/192 个原用例、1242/1242 条原断言，缺失、未比较、额外 Java 原断言均为 0。独立证据目录为 `.cache/evidence/byte-final-20260926-125839/`，局部报告 `formalAcceptance=false`。
- 两个 Base58 property 用例按固定 seed 各采集并重放 300 组真实输入；WUA-ZERO-CAPACITY 已按授权最小修复，4 个额外 Java 回归不计入原用例。`node test-audit.test.cjs` 在宿主环境 41/41 通过。
- 本项六个原文件 192 个用例及 467 个 AST 位置已映射，累计 632/5329，尚余 4697。ReaderUint8Array、WriterUint8Array、utils 的 139 项 API 设计映射已复核，所属 values 批次 371 项分批检查通过；累计 values、hash-random、curve 三组 API 为 816/3576 项。
- 以前完成的 Hex、BigNumber、哈希随机及曲线原用例仍在本次 Java 全量回归中通过。`./init.sh` 检查固定 TS、工具链、缓存隔离与任务清单；完整六模块 `audit-tests.py check` 和无过滤 `audit-api.cjs check` 仍按剩余范围拒绝通过。

## 下一步

`migration-impl-keys-signatures` 的冻结清单为 11 个原测试文件、146 个注册用例，包含 BRC42 私钥和公钥向量。先复核 ECDSA、Polynomial、PrivateKey、PublicKey、Schnorr、Secp256r1、Signature 的 API 与原测试，再按测试契约逐行为 RED→GREEN；随机 k/密钥须采集真实输入并在 Java 重放，累计运行 `clean test`。

仅修改 `metanet4j-bsv-sdk` 的工程代码、测试和 POM；固定 TS 与其他四个 Java 工程只读。根仓既有无关改动保留，不推送、不广播交易或调用真实钱包/外部业务接口。
