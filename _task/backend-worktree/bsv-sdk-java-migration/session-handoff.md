# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源，[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。目标 Java 工程当前提交 `c0d9fdd`；主工程状态清洁，宿主完整 clean test 4916／4916、无失败／错误／跳过。交易完整功能 745／1390、交易验证 53／162、认证会话 85／160、认证传输 183／968 已有固定原用例／逐断言任务级对照；AuthFetch 属性 300 组固定 TS 实际输入与 Java 消费一致。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3576／3576 且已复核，21 个 API 批次均完成；原用例映射 5329／5329，测试站点映射 7554／7554。对称模块 fixed TS 原 536,870,928 字节 manual 第二轮在原 90 分钟上限内 66 分 16 秒通过，Jest 1／1、定制观测 3 条，输出 `.cache/evidence/symmetric-manual-ts-retry-20260926.*`；待与当前 Java manual 原断言和逐字节摘要做专用桥接。

## 并行工作

- AuthFetch 固定原测试 134／890 与 Transport 合批 183／968 已在当前 Java 提交对照；属性测试 300 组 fast-check 实际输入已封存并由 Java 同批重放，600 条断言精确一致。
- Hex＋BigNumber 构造当前提交的 36 例局部输入重放已通过；独立代理在 byte-codecs 扩展同输入采集，在对称 manual 建立真实语义桥，另有代理补随机／耗时与未执行分支的可核验证据。
- P0 新采集来源门禁已提交，工具反例通过；完整 `audit-tests.py check` 仍须全量真实输入和断言采集，不能用局部样例或任务级报告冒充。

## 验证与收工

`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。

每个已完成 Java 功能均在目标仓库独立提交。根仓本任务的 feature、API、用例映射、契约与工具改动尚待按范围提交；其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
