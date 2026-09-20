# 当前进度

## 当前任务

按用户最新要求回到 API 整理。已完成 migration-api-hash-random 的完整设计：Hash.ts 277、DRBG.ts 7、Random.ts 8，共 292 项；累计 values + hash-random 为 12 个完整文件、663/3576 声明，剩余 19 批、2913 项。源码、Java 签名和行为依据见 [API 契约](doc/完整模块与API映射-20260920-122800.md#api-hash-random) 与 api-map.json。

已核对 24 个直接声明导出绑定和 2 个 Hash namespace 导出。契约包含原生/纯 TS 的输入转换、摘要重复调用、内部状态/克隆/销毁、PBKDF2 参数顺序与缺省值、DRBG 状态推进，以及 Random 宿主优先级/缓存/异常。SHA512HMAC.outSize=32 等源码实际行为保留；没有新授权差异。

## 本批验证

- `node audit-api.cjs batches --batch migration-api-hash-random`：292/292 映射结构通过；values 的 371 项也保持通过。
- 六个原 TS 测试文件实际 86/86 通过，零失败/跳过：Hash 30、Hash.additional 9、HMAC 5、DRBG 29、Random 5、Random.additional 8。TS 源码和原断言未改；86 不计作 Java 已迁移。
- `node api-hash-random-probe.cjs`：133 组真实观察和内置断言通过，覆盖原生/纯 TS/无 Buffer 及隔离随机宿主；不计 SDK 用例。
- 环境自检、全批文件归属/状态检查通过；无过滤 `audit-api.cjs check` 仍按预期拒绝 2913 项未映射。检查器只能证明结构无漏项，语义复核依据是全文源码、原测试及观察记录。

原始 Jest JSON、日志、探针输入/返回/异常及哈希在 `.cache/evidence/api-hash-random-*`；命令、源码/脚本/报告哈希和结果索引为 `.cache/evidence/api-hash-random-manifest.json`。本批只修改任务根目录的 API 映射、契约、状态及探针，无 Java 工程改动，无须重复其 clean test 或 37 分钟 AES manual。

## 已有 Java 成果

目标仓提交 9c22ba1（BigNumber 构造基础）、0ecb8d1（Hex）。最近累计对照证据 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/`：原用例 36/36、71 次断言、101 个 AST 位置；Java 共 37/37（基础测试 1 单列），零失败/错误/跳过。BigNumber 子项为原 constructor 文件 28 用例、45 静态断言→52 次执行、92 个 API 调用，实际输入/返回/异常及断言实参一致；完整 BigNumber 尚未实现。上述是已有有效证据，本批未声称重新执行 Java。

采集比较工具自测已有 14/14，包含循环漏采、重复、API 调用缺失、输入位/断言值/错误消息变化及报告篡改反例。实施与复验入口见模块迁移计划。用户此前允许已完成设计且依赖闭合的部分先编码的授权保留，规则见 feature_list.json 的 implementationPolicy；当前优先继续 API。

## 剩余门禁与下一步

六模块仍为 primitives/compat/script/transaction/wallet/auth，冻结范围 292 文件、133 测试文件、5329 原用例、7554 AST 位置。Java 映射 36/5329，缺失 5293；完整 API、通用输入重放/随机轨迹、结果采集和 P0 联合门禁未完成，scopeReview=pending。此前完整 TS 基线为 5329/5329（含原规模 manual），不是 Java 完成证明。

feature_list.json 共 39 项：11 done、0 in-progress、28 not-started；activeItem=null，唯一下一步 migration-api-symmetric（AESGCM、SymmetricKey、AsyncCryptoBackend 三个完整文件、60 项）。BigNumber serializers 暂留待办。

WUA-ZERO-CAPACITY 最小修复授权保留，尚未实现；未来只把旧容量 0 的扩容起点设为 1，额外回归单列。工程代码/测试/POM 仅允许修改 metanet4j-bsv-sdk，其他工程与固定 TS 只读；根仓既有无关修改保留，未推送。
