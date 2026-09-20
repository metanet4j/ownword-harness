# 当前进度

## 当前任务

编码任务按可独立验收的功能组划分，在同一任务内完成 API 前检、原测试映射、TDD、实际结果整理和提交。activeItem=null，nextItem=migration-impl-hash-random。

执行队列共 43 项：10 done、0 in-progress、33 not-started。其中编码任务 28 项，已完成 Hex、BigNumber 构造基础、完整大整数与模运算 3 项，剩余 25 项。21 组 API 设计移到 apiBatches，作为嵌入复核清单：values、hash-random 2 组完成，19 组待完成。133 个 API 文件、133 个原测试文件/5329 用例及 26 个辅助文件均已分配到唯一收口任务。

migration-impl-bignumber 已完成完整 BigNumber、ReductionContext、Mersenne、K256、MontgomoryMethod 以及本任务所需 Utils 编码辅助；7 个原测试文件 174 用例全部复刻并进入累计回归，既有 Hex 8 用例与原构造 28 用例在目标工程 clean test 中重跑通过。

## 本次验证

- `.cache/evidence/bignumber-final-20260920-173943-23798q/`：固定 TS 的 7 个原测试文件真实执行 174/174 通过，零失败/跳过/todo；TS 用例名和数量与 module-tests.json 一致。
- 目标工程 `./verify.sh bsv-test`：211/211 通过，primitives 210（Hex 8、构造 28、本项 174），infrastructure 1；零失败/错误/跳过。
- `test-map.json`：累计映射 210 个原用例，siteReviews 781 个；本项 174 个 Java 身份全部在 Surefire 实际执行。
- `node audit-api.cjs batches --batch migration-api-values`：371 声明结构复核通过；`node test-audit.test.cjs`：41/41 通过。
- `python3 audit-tests.py revision`：本批次绑定目标工程提交 a697a49 的工作树摘要；summary.json 记录命令、计数并明确 formalAcceptance=false。

本批按测试契约完成 Java 原测试复刻与固定期望值核验，但尚未生成 174 个新用例的逐断言 TS/Java 原始值文件；既有 Hex/构造项继续使用 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/` 的逐调用证据。无过滤 `node audit-api.cjs check` 与六模块 `python3 audit-tests.py check` 仍保留完整范围，不能以本项局部通过代替整模块验收。

## 已有 API 与 Java 成果

API 设计 values 371 项、hash-random 292 项，累计 12 个完整文件、663/3576 声明，仍有 2913 项未映射。源码、Java 签名和行为依据见 [API 契约](doc/完整模块与API映射-20260920-122800.md) 与 api-map.json。hash-random 原 TS 测试已有 86/86，133 组探针观察和内置断言通过；这些不是 Java 实现证明。

Java 映射测试用例 210/5329，缺失 5119；目标仓最新提交 a697a49（完整大整数与模约减）、9c22ba1（BigNumber 构造基础）、0ecb8d1（Hex）。完整 BigNumber 的参数分支、成员、序列化和模运算已实现，目标工程累计 210 个 primitives 用例通过；局部比对 evidence 的 formalAcceptance=false。完整 API、通用输入重放/随机轨迹、结果采集和最终收口未完成，scopeReview=pending。

## 下一步与固定边界

下一项 migration-impl-hash-random：按 API 前检、逐行为 TDD、原测试复刻和实际结果整理推进 Hash/DRBG/Random；hash-random 已完成的 292 项设计可直接复用，密码学差异和宿主行为按已登记线索处理。六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 原用例、7554 AST 位置。

WUA-ZERO-CAPACITY 最小修复授权保留，尚未实现；未来只把旧容量 0 的扩容起点设为 1，额外回归单列。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
