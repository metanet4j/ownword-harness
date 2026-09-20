# 会话交接

## 执行入口

用户授权已完成设计且依赖闭合的部分先编码，不能以全量 P0/API 设计未完成阻止内部项。完整六模块、全部 5329 原用例及最终联合门禁保持不变。范围和顺序以 feature_list.json 的 scope/implementationPolicy 为准。

读取沿途规则、计划及状态，运行 ./init.sh，核对各仓状态。当前无进行中项，唯一下一步 migration-impl-bignumber-serializers：完整 BigNumber.serializers.test.ts 16 个原用例，先审查所需 Utils 编解码和 BigNumber 构造/参数分支，按单行为 TDD。源码、Java 测试与 POM 仅修改 metanet4j-bsv-sdk；其他四工程只读。

## 已完成且可复验

目标仓最新提交 9c22ba1：BigNumber 构造基础及原文件全部 28 个用例；前一功能提交 0ecb8d1 为完整 Hex。当前 BigNumber 仍未完成全部参数分支、成员或其他原测试，不要把 28 构造用例通过写成整个构造 API/BigNumber/模块等价证明。下一项补齐必要重载、无参零值和协议编码；后续还需完整 arithmetic/binary/utils/additional/dhGroup 和模运算测试。

`python3 run-hex-parity.py --bn-constructor` 累计执行两个原 TS 文件及 Java 全部 clean test。最新提交后批次 `.cache/evidence/hex-parity-20260920-153441-zd037qhq/`：原用例 36/36，断言结果 71/71，101 AST 位置；Java 共 37/37（基础 1 单列）。BigNumber 子项 28/28、45 静态断言→52 次执行、92 个 API 调用；全部实际输入/结果/异常及断言实参一致。

BigNumber 的 139 行保留 8 个非法字符样本，断言 ID 使用 #1..#8；197 行空 Buffer 条件按原式保留。采集器在原测试导入时安装，避免提前 require 改变 ts-jest 首次编译上下文；TS 源码/断言不修改，调用真实实现一次，内部调用不重复采集。Number 按 IEEE-754 位模式记录，保持 NaN/负零的表示能力；本项不宣称这些未在原文件出现的输入已完成实现。

Java BigNumberObservation 使用 test 范围 Jackson 3.1.5（父工程版本管理且缓存已有）；生产 SDK 无新增依赖。保留 BSV 与 bn.js MIT 许可和来源资源。TDD 原始日志 bn-01/05/06/07/08/09/12/16/18/19/22/23-red/green.log，12 个真实红绿行为；其余 16 用例为已有行为的直接 GREEN，未人为制造失败。

`python3 test-hex-parity.py <累计批次目录> -v` 为 14 个工具自测，不计 SDK 用例。`run-hex-parity.py --verify <批次>` 要求 Java 提交/工作树、源码/映射/工具及原始报告仍匹配；变化后重新采集，不改旧版本号。局部 catalog/mapping 仅用于 compare，formalAcceptance=false；正式 check 始终重扫六模块，当前应拒绝剩余 5293 个 Java 映射。

收尾 ./init.sh、audit-api.cjs batches 通过；audit-tests.py check 实际重扫 133 原文件/5329 用例，按预期拒绝剩余 5293 映射（多余 0）。日志见 .cache/evidence/bn-init-final.log、bn-api-batches-final.log、bn-formal-gate-final.log；提交后 14 项工具反例通过见 bn-parity-selftests-final.log。

## 剩余设计与边界

API 21 批只有 values 完成设计（9 完整文件、371 声明），剩余 3205/3576。设计不等于实现。契约入口为 doc/完整模块与API映射-20260920-122800.md；node audit-api.cjs batches 检查完整归属/状态，正式 check 不按文件过滤。

BigNumber 须保留 magnitude/sign/nominal length、red 身份和失败前副作用。小端 hex 的双字符 parseInt 与 Hex 的严格校验不同（1g 输入等边界尚待 Java 补齐），类型/默认参数/错误顺序不能按 JDK 默认替代。MontgomoryMethod.imul 零分支的原 TypeError 未授权修复；Reader 的 not.toThrow('消息') 不能弱化为 assertDoesNotThrow。详见契约，不自动修正上游怪异行为。

WUA-ZERO-CAPACITY 已授权未来只把旧容量 0 的扩容起点设为 1，单列差异与额外回归；尚未实施，不再重复询问。其他差异未经授权仍按原行为。

P0 通用输入重放、随机/属性采集、全量映射与联合门禁未完成。此前完整 TS 基线 `.cache/evidence/ts-baseline-20260920-123124/` 为 5329/5329；manual 输入 536870928 字节、37:16.72。无相关变化不为会话切换重跑，但完整阶段最终采集/验收仍须覆盖。

Maven/pnpm 只经任务脚本。Node 嵌套 spawnSync 清点在沙箱曾 EPERM，清点/工具自测使用宿主；原语单元测试不需要中间件或跨工程构建。固定 TS 提交 f999e0c1aad9a7afd0cbadaaf23841d049af9d5a。feature_list 39 项，10 done、0 in-progress、29 not-started。根仓无关改动保留，不推送。
