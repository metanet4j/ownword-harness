# 会话交接

## 权威状态

[feature_list.json](feature_list.json) 是任务状态来源，[完整模块与 API 契约](doc/完整模块与API映射-20260920-122800.md) 是行为依据。目标 Java 工程当前提交 `c19285f`；主工程状态清洁。已通过交易完整功能 745／1390、交易验证 53／162、认证会话 85／160 的固定原用例／逐断言任务级对照。认证传输固定原测试 49／78 一致，AuthFetch 阶段宿主 240／240 通过。证据路径见 [progress.md](progress.md) 与 [feature_list.json](feature_list.json)。

当前 API 映射 3495／3576，原用例映射 5299／5329，测试站点映射 7428／7554；剩余均在 AuthFetch。对称模块 fixed TS 原 536,870,928 字节 manual 仍未验收；保留胡先生明确指定的 90 分钟上限，第二轮原测试正在运行，输出 `.cache/evidence/symmetric-manual-ts-retry-20260926.*`。不能缩小输入、延长上限或把 Java／oracle 结果当作原 Jest 通过。

## 并行工作

- `/tmp/bsv-auth-fetch-f1b5752`：AuthFetch 原测试复刻、剩余 30 个用例和 126 个站点映射，固定 TS 动态时间戳／栈仅作字段级语义核验；完成后提交并合入主工程。
- `/tmp/bsv-auth-sessions-0472fc0`：API-20 AuthFetch.ts 的 81 条设计映射并行复核，只读 AuthFetch Java 工作树，不修改其源码。
- P0 输入重放、逐断言结果采集及反例门禁由独立代理推进；不得放松 `audit-tests.py check` 原验收条件，也不得伪造输入账本。

## 验证与收工

`node audit-api.cjs batches` 检查结构分配，单批可用 `--batch ID`；完整门禁是无过滤 `node audit-api.cjs check`、`python3 audit-tests.py check`，后者还需 `module-scope.json.scopeReview=reviewed` 与当前源码版本的完整原始报告和结果。Maven／pnpm 使用任务目录 `./mvn.sh`、`./pnpm.sh`；集成和接口测试须在宿主提权环境运行。

每个已完成 Java 功能均在目标仓库独立提交。根仓本任务的 feature、API、用例映射、契约与工具改动尚待按范围提交；其他无关工作区修改不得暂存或提交。不读 Archive，不调用真实外部钱包或广播。
