# 当前进度

## 执行位置

权威清单与状态见 [feature_list.json](feature_list.json)：43 个执行事项中 16 done、9 in-progress、18 not-started。`activeItem=nextItem=migration-impl-symmetric`。API 映射 2777／3576，原用例映射 3302／5329；六模块完整门禁尚未通过。

## 已验证的增量

- BEEF／MerklePath 目标提交 `28e0028`、`7861580`：固定 TS／Java 83／83，1553／1553 条原断言；干净提交 Maven 五个测试类 83／83、失败／错误／跳过为 0。MerklePath 原 bench 101／501／999 规模和随机重放保留；BEEF 五文件 237 项 API 已复核。证据 `.cache/evidence/transaction-beef-final-parity.json`、`.cache/evidence/transaction-beef-clean-maven-retry.log`。
- 钱包 JSON 目标提交 `2d23200`：固定 TS／Java 58／58、78／78 条原断言，离线网络请求 0；66 项 API 与 58 用例、103 个源码站点映射。任务验收 `.cache/evidence/wallet-json-clean-parity.json`。
- 脚本模板目标提交 `9e420e3`：固定 TS／Java 17／17、96／96 条原断言；30 项 API 与 17 用例、45 个源码站点映射。任务验收 `.cache/evidence/script-templates-clean-parity.json`。完整 `Spend` 解释器与 auth／compat 依赖继续实施。
- 交易基础目标提交 `0a6a81e`：固定 TS／Java 74／74、115／115 条原断言；75 项 API 与 74 用例、171 个源码站点映射。任务验收 `.cache/evidence/transaction-base-clean-parity.json`。
- 钱包契约目标提交 `57c17c7`：固定 TS 253／253、1003 条原断言；隔离 Java 255／255，含两条真实 BEEF 输入探针。API-08 442 项与钱包验证 248 项已复核。任务验收 `.cache/evidence/wallet-contracts-clean-parity.json`。
- 干净目标提交 `4da4459` 的 16 类累计 Maven 402／402，通过数、失败数、错误数、跳过数分别为 402、0、0、0；四项任务级验收均已基于该提交重算。
- 钱包密钥目标提交 `b81b37f`：固定 TS／Java 71／71、162／162 条原断言；兼容层目标提交 `2004ecf`：122／122、281／281；脚本执行目标提交 `7174fa5`：546／546、568／568。各项均在干净目标工作树复验，API／用例／源码站点映射分别为 75／71／246、90／122／267、0／546／223；Spend 的 108 项 API 随完整向量任务收口。
- 广播器目标提交 `acd99a2`：固定 TS／Java 68／68、169／169 条原断言；44 次随机输入逐项重放，45 项 API、68 用例及 290 个源码站点映射。任务报告 `.cache/evidence/broadcasters-task-parity-acd99a2.json`。
- 认证证书目标提交 `fa67ce4`、`58a8f73`：五个固定原测试 50／50、128／128 条实际值断言；提交后干净目标工作树 Maven 50／50、失败／错误／跳过为 0。71 项 API、50 用例及 180 个源码站点映射，API 批次结构复核通过；任务报告 `.cache/evidence/auth-certificates-task-parity.json`。
- 已完成的脚本模型、HTTP／chain、密钥签名与更早基础模块的提交和验收报告见 [feature_list.json](feature_list.json)，未重复记录版本历史。

## 当前阻塞与并行工作

对称模块普通四文件 51／51、384／384 条断言在固定 TS native、fallback 与 Java 侧逐字段一致。原 536,870,928 字节 Java manual 1／1、三条断言通过，50.62 秒、峰值约 2.14 GiB；Node 内建 crypto 的同输入流式摘要与 Java 一致。固定 TS 原 manual 曾在 90 分钟上限退出 124，未产生完整 Jest 结果和断言轨迹；120 分钟有界重跑已向用户请求明确授权，尚未收到答复，不能标记对称任务完成。证据 `.cache/evidence/symmetric-nonmanual-validation.json`、`.cache/evidence/symmetric-manual-java.json`、`.cache/evidence/symmetric-manual-ts-timeout.json`。

脚本向量六份原测试 555 个用例正在补齐解释器语义；Wallet Wire 的 HTTP 层 46 个用例已通过，完整集成测试正在逐项增加，目前 45／82 个已在宿主 Maven 通过。`node audit-api.cjs batches` 已检查 133 文件、3576 声明和 28 个编码任务分配；仍有 799 项未映射。固定 TS 与其他四个 Java 工程只读；目标工程以 `metanet4j-bsv-sdk` 为唯一可改代码仓库，根仓既有无关改动保留。
