# 会话交接

## 当前状态

以 [feature_list.json](feature_list.json) 为执行状态和依赖的唯一入口，行为依据见[核心契约](doc/完整模块与API映射-20260920-122800.md)。当前 16／43 执行事项 done，8 in-progress；主要在途为对称、钱包契约、交易基础、BEEF、钱包 JSON、钱包密钥、兼容层和证书模块。脚本模板已提交且任务级验收通过，因 auth／compat 依赖未完成仍按清单保持 not-started。脚本执行正在并行实施。

BEEF 目标 `7861580` 的干净工作树 `/tmp/bsv-beef-accept-7861580` 已完成 Maven 定向 83／83；完整逐断言报告 `.cache/evidence/transaction-beef-final-parity.json` 为 83／83、1553／1553、missing／uncompared／extra=0。干净提交 `4da4459` 的 16 类累计 Maven 402／402，通过数、失败数、错误数、跳过数分别为 402、0、0、0。钱包 JSON、脚本模板、交易基础、钱包契约四项任务在该提交的固定 TS／Java 逐断言报告分别为 58／78、17／96、74／115、253／1003，均缺失／未比较为 0；见各任务 `taskAcceptance.compareReport`。

对称普通 51／51、384／384 已逐字段对照；Java 536,870,928 字节 manual 1／1 与 Node 流式 oracle 一致。固定 TS 原 manual 90 分钟 timeout，120 分钟重跑需用户明确授权；目前不能将对称任务验收为完成。自动审批曾拒绝暂停计时器以绕过 90 分钟限制，理由是绕过资源上限；未执行该方式。

## 复跑入口

- BEEF：`python3 task-parity.py --task migration-impl-transaction-beef --ts .cache/evidence/transaction-beef-all-ts-parity.jsonl --java .cache/evidence/transaction-beef-all-java-parity.jsonl --java-worktree /tmp/bsv-beef-accept-7861580 --output <报告路径>`。
- 交易基础、钱包 JSON、脚本模板各自的本地逐断言报告见 `feature_list.json` 的 evidence；其固定原测试轨迹均在 `.cache/evidence/`。
- 钱包密钥 71 例与兼容层 122 例、脚本执行 546 例由三个子代理并行推进；脚本执行已有 524 例 Java 通过。兼容层 BSM／ECIES 的 15 例、21 断言已精确对照；共享逐断言记录器正支持钱包密钥异步拒绝与原时间阈值比较。
- Maven／pnpm 仅经 `./mvn.sh`、`./pnpm.sh`。集成、接口测试在宿主提权环境运行。完整门禁是无过滤 `node audit-api.cjs check` 与 `python3 audit-tests.py check`，目前剩余任务尚未覆盖，不应宣称完成。

只修改 `metanet4j-bsv-sdk` 工程代码／测试及本任务目录映射、状态与文档；固定 TS 和另外四个 Java 工程只读，不读 Archive，不推送或调用真实外部钱包／广播。根仓已有无关规则、技能和 `.opencode` 改动，提交时只选择本任务路径。
