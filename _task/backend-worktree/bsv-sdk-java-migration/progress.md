# 当前进度

## 当前任务

编码任务按可独立验收的功能组划分，在同一任务内完成 API 前检、原测试映射、TDD、实际结果整理和提交。activeItem=null，nextItem=migration-impl-curve。

执行队列共 43 项：11 done、0 in-progress、32 not-started。其中编码任务 28 项，已完成 Hex、BigNumber 构造基础、完整大整数与模运算、哈希/HMAC/PBKDF2/随机源 4 项，剩余 24 项。21 组 API 设计：values、hash-random 2 组完成，19 组待完成。133 个 API 文件、133 个原测试文件/5329 用例及 26 个辅助文件均已分配到唯一收口任务。

migration-impl-hash-random 已完成 Hash、SHA1/SHA256/SHA512、RIPEMD160、SHA1/SHA256/SHA512 HMAC、PBKDF2-HMAC-SHA512、DRBG 与 Random 宿主适配；6 个原测试文件 86 用例全部复刻并进入累计回归。

## 本次验证

- `.cache/evidence/hash-random-final-20260920-175813-4236q/`：固定 TS 的 6 个原测试文件真实执行 86/86 通过，零失败/跳过/todo；TS 用例名和数量与 module-tests.json 一致。
- 目标工程 `./verify.sh bsv-test`：297/297 通过，primitives 296（Hex 8、构造 28、BigNumber 174、哈希随机 86），infrastructure 1；零失败/错误/跳过。
- `test-map.json`：累计映射 296 个原用例，siteReviews 962 个；本项 86 个 Java 身份全部在 Surefire 实际执行。
- `node audit-api.cjs batches --batch migration-api-hash-random`：292 声明结构复核通过；`node test-audit.test.cjs`：41/41 通过。
- `python3 audit-tests.py revision`：本批次绑定目标工程提交 9fbcc9d 的工作树摘要；summary.json 记录命令、计数并明确 formalAcceptance=false。

本批按测试契约完成 Java 原测试复刻与固定向量核验，但尚未生成 86 个新用例的逐断言 TS/Java 原始值文件；Random 的 Node/浏览器分支在 Java 中以可注入 Runtime 显式适配，不能宣称等同真实 JS 宿主环境。无过滤 API check 与六模块 `audit-tests.py check` 仍保留完整范围。

## 已有 API 与 Java 成果

API 设计 values 371、hash-random 292，累计 12 个完整文件、663/3576 声明，仍有 2913 项未映射。源码、Java 签名和行为依据见 [API 契约](doc/完整模块与API映射-20260920-122800.md) 与 api-map.json。

Java 映射测试用例 296/5329，缺失 5033；目标仓最新提交 9fbcc9d（哈希/随机）、a697a49（大整数/模约减）、9c22ba1（构造）、0ecb8d1（Hex）。SHA/HMAC/PBKDF2/DRBG 以固定上游向量和 RFC 6979 向量核验；Random 使用宿主 CSPRNG。完整 API、通用输入重放/随机轨迹、结果采集和最终收口未完成，scopeReview=pending。

## 下一步与固定边界

下一项 migration-impl-curve：按 API 前检、逐行为 TDD、原测试复刻和实际结果整理推进曲线、点与 ECDSA 依赖。六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 原用例、7554 AST 位置。

WUA-ZERO-CAPACITY 最小修复授权保留，尚未实现；未来只把旧容量 0 的扩容起点设为 1，额外回归单列。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
