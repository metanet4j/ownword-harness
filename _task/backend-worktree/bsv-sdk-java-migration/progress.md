# 当前进度

## 执行位置

权威任务状态见 [feature_list.json](feature_list.json)：43 个执行事项中 16 个 `done`、12 个 `in-progress`、15 个 `not-started`；`activeItem=nextItem=migration-impl-symmetric`。目前 API 映射 3495／3576 项且已映射项全部复核；原用例映射 5299／5329 个、源码测试站点映射 7428／7554 个，剩余均属 AuthFetch。六模块完整门禁尚未通过。

目标 Java 工程主分支当前提交 `c19285f`。固定 TypeScript 仓库及其他四个 Java 工程只读；目标工程 `metanet4j-bsv-sdk` 是唯一可改代码仓库。工作区根仓的既有无关改动保留。

## 已取得的任务级验收

- 交易完整功能：目标提交 `f1b5752`；固定 TS／Java 745／745 个原用例、1390／1390 条实际断言一致，报告 `.cache/evidence/transaction-complete-clean-parity-9bcb650.json`。
- 交易验证与证据：目标提交 `dfacef7`；固定 TS／Java 53／53、162／162 条实际断言一致，报告 `.cache/evidence/transaction-verification-parity-main-20260926.json`。交易模型 API-09 的 126 项与证据 API-10 的 176 项均通过单批审计。
- 认证会话：目标提交 `94d5bc0`，异步存储修复 `7c382f6`，公开异步存储入口 `3e58d02`；固定 TS／Java 85／85、160／160 条实际断言一致，另有两例延迟 Future 回归，报告 `.cache/evidence/auth-sessions-parity-main-7c382f6.json`。API-19 的 101 项通过单批审计。
- 认证传输：固定 TS／Java 49／49、78／78 条实际断言一致；主工程已合入响应头排序和 HTTP／JSON 边界修复 `adabdde`。传输自身 26 项 API 已复核。AuthFetch 仍在实施；阶段提交 `c19285f` 已合入主工程，当前阶段宿主 240／240 个相关测试通过，主工程组合定向 133／133 通过。

主工程在会话异步修复合入前完成整合回归 4781／4781、失败／错误／跳过均为 0；之后会话定向 87／87、传输与 Peer 定向测试通过。待 AuthFetch 合入后重新运行完整回归。部分已通过任务的排期状态仍非 `done`，因为依赖链须等待对称模块完整验收。

## 当前阻塞与后续门禁

对称模块普通四文件固定 TS／Java 51／51、384／384 条断言一致；Java 原 536,870,928 字节 manual 1／1 与 Node 原生流式 oracle 一致。固定 TS 原 manual 曾在 90 分钟上限退出 124，未产生 Jest 结果和断言轨迹。已按胡先生指定的相同 90 分钟上限重跑原测试，证据写入 `.cache/evidence/symmetric-manual-ts-retry-20260926.*`；完成前不能标记该任务通过。

AuthFetch 六个原测试文件尚有 30 个用例、126 个站点待映射；API-20 尚有 81 项 AuthFetch.ts 声明待复核。完整 `audit-tests.py check` 还需汇总固定上游与当前 Java 版本的全量执行报告、输入重放与逐断言结果，并完成 P0 证据门禁；现有任务级报告不能代替完整六模块报告。
