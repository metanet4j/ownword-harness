# BSV 依赖替换任务交接

## 当前状态

胡先生已于 2026-10-10 授权“开始按照计划执行，先拆feature，记录执行进度和状态”，并在本次会话明确“目标是计划完全执行完成”。[feature_list.json](feature_list.json) 是执行状态的唯一来源；七个阶段汇总和 28 个执行项已拆分，当前无 activeItem，下一项 bsv-r3-keys；**R0（6/6）、R1（3/3）、R2（2/2）阶段全部完成、门禁 PASS**，进入 R3 业务 SDK 适配；`bsv-r3-keys` **进行中**：base 共享值类型基座完成（提交 caaeb8b，base 严格验收 43 例 0 失败、gaps=0），SDK 密钥／地址层（56058b4）与 BIP39／BIP32 层（5424b34）已迁移，SDK 的 BAP 结构改写已完成（BapPath + compat.HD + SigningKeyProvider，sdk 提交 c9df398）；UnSpendableDataLockBuilder 亦已迁移（哈希换 BsvHashBytes）；**生产仍有 28 个文件、测试 41 个文件引用 io.bitcoinsv**。当前 18 处编译错误全部在交易／签名组：RemoteTransactionBuilder 8、TransactionBuilder 4、RemoteTransactionSigner／RemoteOrdTransactionBuilder／BobHelper 各 2。既有升级与测试事项保持原样，不计为本次验收。

重启先读 ../AGENTS.md、../mvn-command.md、本目录 AGENTS.md、feature_list.json.planDoc、feature_list.json 与 progress.md，运行不带参数的 ./init.sh。授权在既定计划范围持续有效，无需重复请求。一次只做一个执行项，验证及提交齐全后更新状态。

## Blockers

- 无硬阻塞。轮次上限已由用户提升至 10000 并重新激活（此前 40 轮用尽的状态已解除）。
- 未完成项：R3 测试迁移（**有错文件 6 个**）、R3 严格验收、R4（component 52 生产／115 测试旧引用）、
  R5（旧依赖清理）、R6（全量验收与交付）。未完成项**未标记 done**（符合 DoD）。

## 当前度量（每轮重测）

| 维度 | 数值 |
| --- | --- |
| `metanet4j-sdk` 生产编译错误 | 0 |
| `metanet4j-sdk` 生产旧引用文件 | 3（起点 49） |
| `metanet4j-sdk` 测试 `test-compile` 退出码 | 1 |
| 有编译错误的测试文件 | 6 个：RemoteTransactionContractTest 66、BapBaseCoreContractTest 62、BsocialDataLockBuilderContractTest 26、CryptoHelperContractTest 24、SpecifyBapBaseContractTest 18、TransactionBuilderContractTest 4 |
| 测试旧引用文件 | 17 / 54（起点 41，降 59%） |

## 交接入口

- 阶段报告：`BSV依赖替换阶段报告-20261011-221500.md`（度量、约束执行情况、证据索引、剩余工作量与建议）
- 执行配方：`evidence/bsv-replace/r3-keys-20261010/migration-rules.md` §14—§24（字典、三步法、共同父类、覆盖迁移登记）
- 测量纪律：**唯一可靠判据是 `clean test-compile` 退出码**；grep 统计的错误数与文件数会被 javac 提前中止／上限封顶双重失真
