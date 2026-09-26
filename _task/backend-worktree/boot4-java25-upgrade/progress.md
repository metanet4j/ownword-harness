# progress.md — boot4-java25-upgrade 进度

本文件只记录当前状态；范围和验收标准见[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)，逐模块状态见 `feature_list.json`。

## 当前状态

- **更新时间**：2026-09-26。
- **当前目标**：为四个子仓库建立完整单元测试、集成测试与逐模块覆盖率证据。
- **当前阶段**：`unit-u2-sdk` 已恢复实施，子代理分别处理 Bob/Txo 与数据脚本签名；U0 测试基线及 U1 base 已完成，U3—U9 待实施。
- **下一步**：当前提交的 SDK 全量基线已在宿主复跑；串行验证子代理提交的测试，继续 SDK 剩余公开 API 与逐类覆盖。

## 已验证结果

U0 [四仓测试基线](doc/测试基线与障碍-20260926-145423.md)列出 25 POM、369 个生产 Java 文件、最初 52 个测试文件，以及 19 项集成边界的隔离和观测方式。当前 `unit-test-inventory.json` 已增至 84 个测试文件。U0 全仓基线有 56 个旧用例通过、8 个跳过；17 个含可执行代码的 component 模块零本地单元测试。`component-core` 仅定义接口，按 N/A 处理。宿主五项共享服务健康。

U1 base 提交 `bae7eb6` 与 `77ad9fd`：UTXO 相等性缺陷先红后绿；AIP 坏签名返回 false；BAP 固定身份向量、协议枚举、DTO 与 Jackson 行为均有断言。最终提交后，`python3 verify-unit.py --mode accept --scope metanet4j-base` 退出 0；19 个测试全部通过，零失败/错误/跳过，JaCoCo LINE 208/208、BRANCH 76/76、METHOD 51/51，`jacoco:check` 通过。证据在本地 `evidence/20260926T072220Z/`；同一提交的 base 0.2.0 构件已安装至隔离 Maven 仓库。

U2 sdk 的 HTTP 子项提交 `4f4a590`：客户端与 Provider 可使用本地端点；异常 JSON、503、请求路径、广播载荷及 UTXO 映射有断言。宿主本地 HTTP 集成测试 5/0/0/0，证据 `evidence/20260926-u2-http/integration/`；隔离单元基线 32/0/0/0，LINE 392/2005、BRANCH 35/505、METHOD 114/462，证据 `evidence/20260926T075317Z/`。这仍是基线，未通过 100% 严格验收。公网 Bitails 历史用例继续标记 `external`，由本地用例替代。component 的 17 个零测试模块、文件模块 8 个禁用测试、固定 ES 索引与交易主网广播风险仍未消解，不能宣布整体验收完成。

U2 工具子项提交 `7e96ebd`：负长度读取统一为 `ProtocolException`；字节游标、越界、固定 SHA-256 与 Bitcoin 签名消息的 VarInt 边界有断言。最新 SDK 隔离单元基线 36/0/0/0，LINE 400/2000、BRANCH 39/507、METHOD 115/461；`ReadUtils` 与 `UtilsExtend` 逐类行、分支、方法无缺口，证据 `evidence/20260926T080341Z/`。

U2 密钥子项提交 `986fddd`：非压缩 WIF 往返修复先红后绿；key=2 的 WIF、公钥、公钥哈希与主网／测试网地址使用独立固定向量；非法长度、校验和、压缩标志与前缀均有断言。最新 SDK 隔离单元基线 39/0/0/0，LINE 434/1996、BRANCH 51/503、METHOD 131/461；`PrivateKey`、`PublicKey`、`AddressEnhance` 逐类无覆盖缺口，证据 `evidence/20260926T082536Z/`。

U2 加密子项提交 `5ef3f2c`：ECIES 的固定／随机临时密钥、往返解密、错误魔数和 MAC 篡改均有断言；AES-CBC 与平台 PKCS5 Cipher 对照，SHA-512 与 JDK 摘要对照。最新 SDK 隔离单元基线 42/0/0/0，LINE 438/1993、BRANCH 55/503、METHOD 131/458；`Ecies`、`AesCBCUtil`、`DigestUtilExtend` 逐类无覆盖缺口，证据 `evidence/20260926T083103Z/`。

U2 主密钥子项提交 `bf40681`：BIP39/BIP32 的固定助记词、口令与 xprv 独立向量通过；随机词表数量／唯一性、反序列化与越界输入有断言，过大或负长度立即失败。最新 SDK 隔离单元基线 44/0/0/0，LINE 442/1993、BRANCH 60/507、METHOD 133/457；`MasterPrivateKey` 逐类无覆盖缺口，证据 `evidence/20260926T083620Z/`。

U2 脚本／Sigma 模型子项提交 `82c5283`：push data 的空引用、空内容、OP_RETURN、OP_0 与有效内容均有断言，Sigma BSM 协议字段使用真实空交易和脚本验证。最新 SDK 隔离单元基线 46/0/0/0，LINE 457/1991、BRANCH 68/507、METHOD 138/456；`ScriptHelper`、`Sig`、`SignResponse`、`Algorithm` 逐类无覆盖缺口，证据 `evidence/20260926T084746Z/`。

U2 Sigma 核心子项提交 `3c0f214`：构造小交易验证 outpoint、输出和消息哈希；四种本地密钥签名、远程签名、重复签名、第二实例、已有 OP_RETURN 及缺失输入均有断言。重复签名错误追加实例、空输入越界、远程上下文缺少可选字段会抛异常三项缺陷先红后绿。最新 SDK 隔离单元基线 56/0/0/0，LINE 701/1987、BRANCH 165/513、METHOD 176/455；`Sigma`、`PreSignHashContext`、`PreSignHashUtils` 逐类无覆盖缺口，证据 `evidence/20260926T090939Z/`。

U2 BAP 默认 API 子项提交 `a86bfa5`：用不同固定私钥验证五类默认地址映射，用真实主密钥验证字节／文本加解密；原先无效密文或缺失密钥会打印堆栈并返回 `null`，已改为抛出有原因的 `IllegalStateException`，先红后绿。SDK 隔离单元基线 59/0/0/0，LINE 713/1983、BRANCH 165/512、METHOD 182/455；`BapBaseCore` 逐类无覆盖缺口，证据 `evidence/20260926T091719Z/`。

U2 BAP 生命周期子项提交 `7c030d3`：签名密钥轮换、按身份／签名地址反查、轮换后对象重建均有断言；上一私钥路径错误、根地址作为 current 时序号 `-1`、未匹配地址返回 `null` 三项缺陷先红后绿。SDK 隔离单元基线 62/0/0/0，LINE 756/1984、BRANCH 183/514、METHOD 187/455；`BapBase` 本体 LINE 111/139、BRANCH 20/28，证据 `evidence/20260926T092325Z/`。

U2 BAP KeyBag 子项提交 `12f2c70`：根／当前签名密钥、支付及 Ord 密钥按公钥哈希检索；有效公钥以前返回 `null`，现转公钥哈希查找，先红后绿。SDK 隔离单元基线 65/0/0/0，LINE 789/1985、BRANCH 193/512、METHOD 196/455；`BapProviderKeyBag` 逐类无覆盖缺口，证据 `evidence/20260926T092920Z/`。

U2 BAP 路径子项提交 `451db1d`：固定十六进制片段验证高位无符号数和 hardened 开关；原 `Integer.parseInt` 对 `80000000` 抛 `NumberFormatException`，改 `Long.parseLong` 后通过。SDK 隔离单元基线 66/0/0/0，LINE 798/1985、BRANCH 199/512、METHOD 197/455，证据 `evidence/20260926T093336Z/`。

U2 BAP 变体子项提交 `20cb3f0`：远程身份只持有五类公开地址、不持有私钥；默认与 Panda 配置路径以及 Tagged Derivation 固定向量有断言。PandaBapBase 未把配置应用名带出的问题先红后绿。SDK 隔离单元基线 69/0/0/0，LINE 846/1986、BRANCH 199/512、METHOD 225/455；`BapBaseAbstract`、`RemoteBapBase`、`PandaBapBase`、两套配置逐类无缺口，`TaggedDerivation` 仍有一个隐式构造器未覆盖，证据 `evidence/20260926T094111Z/`。

U2 显式 BAP 子项提交 `b70f3b0`：六种构造入口、身份／密钥 getter、KeyBag 按哈希选择支付或 Ord 私钥、未知哈希错误均有断言；有效公钥返回 `null` 的缺陷先红后绿。SDK 隔离单元基线 71/0/0/0，LINE 886/1986、BRANCH 203/512、METHOD 242/455；`SpecifyBapBase` 与其 KeyBag 逐类无覆盖缺口，证据 `evidence/20260926T094519Z/`。

U2 BAP 工厂与身份解密子项提交 `1e14af8`：各工厂构造相同根身份、高位签名路径、配置应用名、绝对路径密文解密均有断言；坏密文原先打印堆栈并返回 `null`，现抛有原因的异常，先红后绿。该提交的 SDK 隔离单元基线 73/0/0/0，LINE 899/1984、BRANCH 203/510、METHOD 247/454；`BapBase` 当时 BRANCH 26/26、LINE 136/137，未覆盖的 `encryptSelf()` 已在后续提交实现，证据 `evidence/20260926T095306Z/`。

U2 后续两个提交：`ea025e7` 为旧版 `CryptoHelper` 补固定 BIP39 根／子密钥、主网／测试网 WIF／地址和随机入口断言；`5cd4abf` 按胡先生确认，将 `encryptSelf()` 实现为加密当前 `identityKey`，由 `decryptSelf()` 还原，测试先红后绿。提交 `5cd4abf` 的定向 `clean test` 10/0/0/0，日志和 Surefire XML 在 `evidence/20260926-u2-crypto-self-targeted/`。宿主全量 `verify-unit.py` 申请被自动审批系统拒绝，原因是使用额度上限；命令未执行，当前 SDK 提交尚无全量覆盖率结论。上段 73/0/0/0 和覆盖率仅对应旧提交 `1e14af8`。

U2 脚本扩展子项提交 `f86f9ea`：普通地址、多签、P2SH、Ord 和未知脚本的花费字节估算、签名占位替换及脚本创建时间都有断言。定向 `clean test` 2/0/0/0，JaCoCo `ScriptExtend` LINE 30/30、BRANCH 24/24、METHOD 4/4，证据 `evidence/20260926-u2-script-targeted/`。这是定向覆盖率，SDK 全量仍待宿主验证。

U2 Ord 脚本构建子项提交 `d7552a5`：收款地址、内容封装、缺失媒体字段、MAP 元数据必填字段与 `cmd` 过滤都有断言。定向 `clean test` 3/0/0/0，JaCoCo `OrdScriptBuilder` BRANCH 16/16、LINE 25/26、METHOD 1/2；剩余隐式构造器，证据 `evidence/20260926-u2-ord-script-targeted/`。这是定向覆盖率，SDK 全量仍待宿主验证。

U2 Ord 交易解析与赎回数据子项提交 `8a540b9`：有效／畸形脚本、地址、关联输出和密钥选择有断言，移除不可达的空值判断。定向 `clean test` 7/0/0/0；`RedeemDataExtend` LINE 13/13、BRANCH 6/6、METHOD 5/5；`TxHelperExtend` BRANCH 32/32、LINE 40/41、METHOD 6/7，余隐式构造器。证据 `evidence/20260926-u2-txhelper-redeem-targeted/`。SDK 全量仍待宿主验证。

U2 交易扩展类子项提交 `6f32283`：内存交易验证显式索引、关联输出、outpoint 哈希和空解锁脚本。定向 `clean test` 2/0/0/0，三个类的 LINE/METHOD 均 100%，证据 `evidence/20260926-u2-transaction-enhance-targeted/`。SDK 全量仍待宿主验证。

U2 签名上下文线程隔离子项提交 `7b3d43d`：按哈希取回、缺失错误及跨线程不可见均有断言。定向 `clean test` 2/0/0/0，`AllHashSigThreadLocal` LINE 7/7、BRANCH 2/2、METHOD 4/4，证据 `evidence/20260926-u2-threadlocal-targeted/`。SDK 全量仍待宿主验证。

U2 ForkID 签名哈希子项提交 `da46655`：独立预映像核对 ALL/SINGLE/NONE × ANYONECANPAY 与缺失输出，定向 `clean test` 2/0/0/0。`SigHashExtend` BRANCH 25/26、LINE 50/53、METHOD 1/2；未知消息长度容量分支、不可达 I/O 异常处理和隐式构造器仍有缺口，证据 `evidence/20260926-u2-sighash-targeted/`。SDK 全量仍待宿主验证。

U2 二进制消息签名子项提交 `39f82a9`：固定非 UTF-8 消息签名、哈希签名一致性、紧凑签名公钥恢复和改动消息失效有断言。定向 `clean test` 1/0/0/0，`EcKeyLiteExtend` LINE 28/30、BRANCH 7/12、METHOD 7/7，证据 `evidence/20260926-u2-eckey-targeted/`。

当前 SDK HEAD `39f82a9` 的宿主全量隔离单元基线：96/0/0/0，LINE 1116/1989、BRANCH 312/508、METHOD 284/454，证据 `evidence/20260926T150042Z/`。基线采集成功，但严格 100% 验收仍未完成。

## 仓库与工作区

四子仓库沿用 `feature/java25`，不推送。parent JaCoCo 配置提交 `4112a48`，sdk 测试分类提交 `2577406`，component 测试分类提交 `de1f59f`。ownword 主仓既有 `AGENTS.md`、standard 规范及技能文件的无关改动保留，不纳入本任务提交。
