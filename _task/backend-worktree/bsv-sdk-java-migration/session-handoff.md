# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源，[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。目标 Java 工程当前提交 `b9f5eb8`；本提交宿主无过滤 `clean test` 的 159 份 Surefire 报告为 5378／5378、无失败／错误／跳过，同一次运行覆盖全部 5329 个映射身份且无重复，另有 49 个 Java 回归。报告与摘要在 `.cache/evidence/java-full-b9f5eb8-20260927/`。对称加密 52／387、Compat 122／281、交易完整功能 745／1390、交易验证 53／162、认证会话 85／160、认证传输 183／968 已有固定原用例／逐断言任务级对照；AuthFetch 属性 300 组固定 TS 实际输入与 Java 消费一致。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3576／3576 且已复核，21 个 API 批次均完成；原用例映射 5329／5329，测试站点映射 7554／7554。固定 TS 标准／manual Jest 原始报告合计 5329／5329，并通过 `audit-tests.py compare-ts`。Spend 的第二组 455 个独立注册已由新 Java 类和新映射收口。对称模块 fixed TS 原 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过，连同当次 Java 原始轨迹和逐字节摘要的专用桥接见 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`。API 总审计见 `doc/API跨任务接口复核-20260927-000100.md`；Transaction 非阻塞、三个异步异常入口和 PATCH 状态说明修复已合入当前累计回归。

## 并行工作

- AuthFetch 固定原测试 134／890 与 Transport 合批 183／968 已在 `c0d9fdd` 对照；属性测试 300 组 fast-check 实际输入已封存并由 Java 同批重放，600 条断言精确一致。
- Hex＋BigNumber 构造 36 例局部输入重放已通过；byte-codecs 的 Base58 六例已有 `75a3dc1` 的双侧正式 capture。Wallet Contracts 中 BRC100ByteEncoding 两个属性用例在 `e2f4814` 完成 600 组实际同输入和断言；WERR 32 个原用例在 `ef41db2` 完成 32 组真输入、40 条断言；证书构造首 2 例完成 7 组真输入、6 条断言。Wallet Contracts 的 253／1003 当前值对照已通过，其余用例输入账本仍待补齐。代理正并行扩展脚本向量、钱包 JSON 字节和证书辅助函数的同输入采集。
- P0 新采集来源门禁已提交，语义规则 7／7、bundle 18／18、关联 3／3、宿主审计 41／41 自测通过。`full-evidence-preflight.py` 报告当前仅 47／5329 例具局部结构计划，新 WERR／证书计划待纳入；当前 Java 完整回归和 TS 原始报告不能代替单次完整双侧来源。完整 `audit-tests.py check` 仍须全量真实输入和断言采集。

## 验证与收工

`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。

每个已完成 Java 功能均在目标仓库独立提交。对称与 Compat 功能项状态已更新；继续逐项核对依赖链、当前接口行为和 P0 全量输入证据。新增 Java 变更后重跑完整 clean test 并封存 XML；当前回归快照只绑定 `b9f5eb8`。其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
