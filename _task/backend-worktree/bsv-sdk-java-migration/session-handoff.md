# 会话交接

## 唯一下一步

用户最新要求“还是回来，继续整理api”。下一项 migration-api-symmetric：完整 AESGCM.ts、SymmetricKey.ts、AsyncCryptoBackend.ts 三文件、60 项声明，按 apiBatchPolicy 通读源码/全部相关原测试、逐项映射并核对行为。当前 activeItem=null、nextItem=migration-api-symmetric，39 项中 11 done、28 not-started。BigNumber serializers 暂留待办，不把此前先编码授权撤销或改成绝对 P0 禁止。

读取沿途规则、计划及状态，运行 ./init.sh、node audit-api.cjs batches，并检查各仓状态。设计只维护任务根目录；代码/测试/POM 仅允许改 metanet4j-bsv-sdk，其他四工程及固定 TS 只读。

## API 设计已完成

values：9 个完整文件、371 项。hash-random：3 个完整文件、292 项（Hash 277、DRBG 7、Random 8）。累计 663/3576，剩余 19 批、2913 项。Java 签名在 api-map.json，行为唯一依据为 doc/完整模块与API映射-20260920-122800.md。不要自动生成 reviewed 或用空壳清零。

hash-random 六个 TS 原测试实际 86/86 通过，133 组探针观察及内置断言通过；原始输入/返回/异常、源码/工具/报告哈希及命令见 .cache/evidence/api-hash-random-manifest.json 和同前缀文件。Hash 两种环境不是处处等价：重复摘要、PBKDF2 默认 keylen/0 长度/参数错误、RIPEMD160 越界 number[] 存在差异；SHA512HMAC.outSize 实际 32；FastSHA.destroy 不设 destroyed；DRBG seed 缺失/空列表不同；Random 构造选择、缓存及动态对象读取均已明确。此批设计未创建 Java 实现，不计新增 Java 测试。

下一批须特别注意同步 Hash NODE_CRYPTO 与 AsyncCryptoBackend 注册表是不同机制；后者的已选后端结果权威，不能错误回退。此前 AES 探针仅证明 8 组小输入与 Node GCM 一致，不能宣称所有输入可直接 JCA；完整 AES 原大输入也不得缩小。相关线索在 API 契约“已核实、尚待逐项映射的行为”。

完成时运行本批 batches --batch 和无过滤 check；全量应在全部声明设计完毕前失败。结构检查不证明语义等价，也不能替代 5329 用例/7554 AST 的正式验收。

## 已有 Java 成果及恢复入口

目标仓 9c22ba1：BigNumber 构造基础原文件 28 用例；0ecb8d1：完整 Hex 8 用例。最新已有累计证据 .cache/evidence/hex-parity-20260920-153441-zd037qhq/：36 原用例、71 次断言、101 AST 位置，Java 37/37（基础测试 1 单列）；BigNumber 子项 52 次实际断言、92 次 API 调用轨迹一致。BigNumber 尚未完成完整参数分支/成员/其他测试，不能写成整类完成。

复验命令 python3 run-hex-parity.py --bn-constructor；已有证据可用 --verify <批次目录> 校验版本/哈希。test-hex-parity.py <批次> -v 的 14 项是工具反例，不计 SDK 用例。局部对照 formalAcceptance=false；正式 audit-tests.py check 始终重扫六模块，仍应拒绝 5293 个缺失 Java 映射。

采集器在原测试导入时安装，提前 require BigNumber 会改变 ts-jest 编译上下文。第 139 行 8 个非法字符串循环样本用 #1..#8，197 行空 Buffer 条件按原式保留；Number 用 IEEE-754 位模式。Jackson 3.1.5 仅 test 范围，生产无新增依赖。TDD 原始 RED/GREEN 日志 bn-01/05/06/07/08/09/12/16/18/19/22/23；其余 16 原用例直接 GREEN，未伪造红灯。

## 固定边界

BigNumber 保留 magnitude/sign/nominal length、red 身份和失败前副作用；小端 hex 的 1g 等分支还需实现。MontgomoryMethod.imul 零分支原 TypeError 未授权修复；Reader 的 not.toThrow('消息') 不能弱化。唯一已授权差异 WUA-ZERO-CAPACITY 尚未实现，精确范围见 api-map.approvedDifferences，不再询问。

scopeReview=pending；通用输入重放、随机/属性采集、全量 API 与 P0 联合门禁未完成。此前完整 TS 基线 .cache/evidence/ts-baseline-20260920-123124/ 为 5329/5329，manual 536870928 字节、37:16.72；无相关变化不重复长基线，但最终完整验收不得遗漏。

Maven/pnpm 仅经任务脚本；Node 嵌套 spawn 的审计可能在沙箱 EPERM，应宿主提权运行取得真实检查结果。只提交任务明确路径，不混入根仓既有规则/技能/.opencode 改动；不推送。独立 Java 仓本批保持 9c22ba1 且干净，无新提交。
