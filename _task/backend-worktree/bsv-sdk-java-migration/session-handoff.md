# 会话交接

## 唯一下一步

按最新拆分执行 migration-impl-bignumber。activeItem=null，nextItem=migration-impl-bignumber；features 共 43 项，9 done、34 not-started，其中编码任务 28 项、已完成 2 项。21 组 apiBatches 是嵌入设计清单，不作为独立执行队列；用户要求在编码任务开始前检查对应 API，不再等待全量设计完成后才研发。

读取沿途规则、计划及状态，运行 ./init.sh、node audit-api.cjs batches，并检查各仓状态。代码/测试/POM 仅允许改 metanet4j-bsv-sdk，任务根目录维护计划/映射/验证工具；其他四工程及固定 TS 只读。本次重整没有新增 Java 功能，不要把检查器通过算成 SDK 通过。

## 编码任务的验收

具体范围与唯一状态在 feature_list.json；公共步骤/条件引用 implementationPolicy。sourceFiles 明确实现/前检范围，apiCompletionFiles 对 133 个 API 文件各承担一次完整实现收口；testFiles 对 133 原文件/5329 用例各分配一次；regressionTestFiles 只追加回归，不重复计数；26 个辅助文件全部纳入 fixtureFiles。

每项先复核所用 API，再补齐本项输入/采集和映射，逐行为执行 TS 参考、Java RED→GREEN，最后完整运行所分配原测试、目标工程 clean test、此前已完成项累计实际结果对照。保存当前版本绑定的原始报告和可复跑命令后才能 done；局部比较 formalAcceptance=false。发现范围外的必需依赖，先补入范围或合并任务并重跑分配检查，不能用桩/占位算法掩盖依赖。

本次 node test-audit.test.cjs 已 41/41，新增两项各有实际 RED/GREEN，验证嵌入复核与分配遗漏/重复等反例；原始日志见 .cache/evidence/feature-plan-*.log。node audit-api.cjs batches 已通过 28 编码任务/21 API 组结构及完整分配检查。工具通过不代表 SDK 完成，通用采集/输入重放仍需随任务落实。

最终 ./init.sh 通过；无过滤 API check 按预期返回 1，拒绝 2913 项未映射。冻结清单/映射与旧已完成项证据保持不变，五个 Java 仓及固定 TS 仓均干净、提交未变。

完整 BigNumber、ReductionContext、MontgomoryMethod、Mersenne、K256 为下一项 apiCompletionFiles；所需 Utils 行为也在 sourceFiles，Utils 整文件由后续字节编解码任务收口。7 个未迁移原文件共 174 用例，累计既有构造 28 用例和 Hex 8 用例。原 serializers 待办已并入，不另起零散功能项。先复用 values 设计、核对源码和原测试并补齐采集，再逐行为 TDD。

## API 设计已完成

values：9 个完整文件、371 项。hash-random：3 个完整文件、292 项（Hash 277、DRBG 7、Random 8）。累计 663/3576，剩余 19 批、2913 项。Java 签名在 api-map.json，行为唯一依据为 doc/完整模块与API映射-20260920-122800.md。不要自动生成 reviewed 或用空壳清零。

hash-random 六个 TS 原测试实际 86/86 通过，133 组探针观察及内置断言通过；原始输入/返回/异常、源码/工具/报告哈希及命令见 .cache/evidence/api-hash-random-manifest.json 和同前缀文件。Hash 两种环境不是处处等价：重复摘要、PBKDF2 默认 keylen/0 长度/参数错误、RIPEMD160 越界 number[] 存在差异；SHA512HMAC.outSize 实际 32；FastSHA.destroy 不设 destroyed；DRBG seed 缺失/空列表不同；Random 构造选择、缓存及动态对象读取均已明确。此批设计未创建 Java 实现，不计新增 Java 测试。manifest 保留当时版本，不改写为本次计划版本。

后续对称加密任务须特别注意同步 Hash NODE_CRYPTO 与 AsyncCryptoBackend 注册表是不同机制；后者的已选后端结果权威，不能错误回退。此前 AES 探针仅证明 8 组小输入与 Node GCM 一致，不能宣称所有输入可直接 JCA；完整 AES 原大输入也不得缩小。相关线索在 API 契约“已核实、尚待逐项映射的行为”。

编码任务前检复用已完成设计，完整 API 组就绪后运行 batches --batch；无过滤 check 在全部声明设计完毕前仍应失败。结构检查不证明语义等价，也不能替代 5329 用例/7554 AST 的正式验收。

## 已有 Java 成果及恢复入口

目标仓 9c22ba1：BigNumber 构造基础原文件 28 用例；0ecb8d1：完整 Hex 8 用例。最新已有累计证据 .cache/evidence/hex-parity-20260920-153441-zd037qhq/：36 原用例、71 次断言、101 AST 位置，Java 37/37（基础测试 1 单列）；BigNumber 子项 52 次实际断言、92 次 API 调用轨迹一致。BigNumber 尚未完成完整参数分支/成员/其他测试，不能写成整类完成。

复验命令 python3 run-hex-parity.py --bn-constructor；已有证据可用 --verify <批次目录> 校验版本/哈希。test-hex-parity.py <批次> -v 的 14 项是工具反例，不计 SDK 用例。局部对照 formalAcceptance=false；正式 audit-tests.py check 始终重扫六模块，仍应拒绝 5293 个缺失 Java 映射。

采集器在原测试导入时安装，提前 require BigNumber 会改变 ts-jest 编译上下文。第 139 行 8 个非法字符串循环样本用 #1..#8，197 行空 Buffer 条件按原式保留；Number 用 IEEE-754 位模式。Jackson 3.1.5 仅 test 范围，生产无新增依赖。TDD 原始 RED/GREEN 日志 bn-01/05/06/07/08/09/12/16/18/19/22/23；其余 16 原用例直接 GREEN，未伪造红灯。

## 固定边界

BigNumber 保留 magnitude/sign/nominal length、red 身份和失败前副作用；小端 hex 的 1g 等分支还需实现。MontgomoryMethod.imul 零分支原 TypeError 未授权修复；Reader 的 not.toThrow('消息') 不能弱化。唯一已授权差异 WUA-ZERO-CAPACITY 尚未实现，精确范围见 api-map.approvedDifferences，不再询问。

scopeReview=pending；通用输入重放、随机/属性采集、全量 API 与最终收口门禁未完成。全部任务独立验收后再完成六模块联合验收，不能以内部任务完成代替完整模块验收。此前完整 TS 基线 .cache/evidence/ts-baseline-20260920-123124/ 为 5329/5329，manual 536870928 字节、37:16.72；无相关变化不重复长基线，但最终完整验收不得遗漏。

Maven/pnpm 仅经任务脚本；Node 嵌套 spawn 的审计可能在沙箱 EPERM，应宿主提权运行取得真实检查结果。只提交任务明确路径，不混入根仓既有规则/技能/.opencode 改动；不推送。独立 Java 仓本批保持 9c22ba1 且干净，无新提交。
