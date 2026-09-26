# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源，[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。目标 Java 工程当前提交 `e4e97c4`；早前提交 `c0d9fdd` 的宿主完整 clean test 4916／4916、无失败／错误／跳过，合并后的全量回归待运行。对称加密 52／387、Compat 122／281、交易完整功能 745／1390、交易验证 53／162、认证会话 85／160、认证传输 183／968 已有固定原用例／逐断言任务级对照；AuthFetch 属性 300 组固定 TS 实际输入与 Java 消费一致。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3576／3576 且已复核，21 个 API 批次均完成；原用例映射 5329／5329，测试站点映射 7554／7554。对称模块 fixed TS 原 536,870,928 字节 manual 在原 90 分钟上限内 66 分 16 秒通过，连同当次 Java 原始轨迹和逐字节摘要的专用桥接见 `.cache/evidence/symmetric-task-parity-c0d9fdd.json`。API 总审计见 `doc/API跨任务接口复核-20260927-000100.md`；Transaction 非阻塞、三个异步异常入口和 PATCH 状态说明修复已合入，隔离回归分别 802／802、22／22、54／54，当前提交仍待累计回归。

## 并行工作

- AuthFetch 固定原测试 134／890 与 Transport 合批 183／968 已在 `c0d9fdd` 对照；属性测试 300 组 fast-check 实际输入已封存并由 Java 同批重放，600 条断言精确一致。
- Hex＋BigNumber 构造 36 例局部输入重放已通过；byte-codecs 的 Base58 六例已有 `75a3dc1` 的双侧正式 capture。Wallet Contracts 中 BRC100ByteEncoding 两个属性用例在 `e2f4814` 完成 600 组实际同输入和断言；另一代理独立采集 primitives 的三个属性用例。Wallet Contracts 的 253／1003 当前值对照已通过，其余用例输入账本仍待补齐。
- P0 新采集来源门禁已提交，语义规则 7／7、bundle 18／18、关联 3／3、宿主审计 41／41 自测通过；完整 `audit-tests.py check` 仍须全量真实输入和断言采集。

## 验证与收工

`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。

每个已完成 Java 功能均在目标仓库独立提交。对称与 Compat 功能项状态已更新；继续逐项核对依赖链、当前接口行为和 P0 全量输入证据，待正在进行的属性采集整合后运行主目标完整 clean test。其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
