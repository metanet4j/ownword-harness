# 会话交接

## 状态

P0 的 migration-scope-review、migration-ts-baseline 已完成。具体范围见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)：六个完整模块 primitives/compat/script/transaction/wallet/auth，15 个候选模块逐项有结论。类型、测试辅助及运行依赖形成六模块闭环；P1 逐模块逐行为实施后联合验收，P2 为独立 SDK 最终交付。

冻结清单为 292 文件、133 测试文件、5329 用例、7554 AST 位置，原四模块的 4275 用例未减少。TS 全部 5329/5329 实际通过，含原规模 manual，1 个快照通过，零跳过。API/用例映射、输入重放和真实采集未完成；Java 功能映射仍为空，scopeReview 总标志仍为 pending。

## Files

- feature_list.json：15 项中 7 项 done、8 项 not-started；activeItem 为空，nextItem 为 migration-api-contract。
- doc/TS完整基线-20260920-124400.md：完整运行命令、网络 fixture、资源预算/实测及证据边界。
- run-ts-baseline.py、ts-offline-guard.cjs：真实运行和离线保护；./verify.sh ts-modules 为完整入口，须按集成测试规则宿主提权执行。
- .cache/evidence/ts-baseline-20260920-123124：最终 standard/manual 两份原始 Jest JSON、日志、资源记录、manifest；两次旧普通报告已分别归档，不能混用。
- .cache/evidence/ts-baseline-final.log：联合核对 PASS，133 文件、5329 用例及模块分布。
- module-scope.json、module-tests.json：范围结论、跨目录归属、文件校验、注册用例、AST 位置和含类型/测试的依赖图。
- doc/模块迁移计划-20260920-103547.md、doc/测试迁移契约-20260920-101559.md、doc/测试完整性脚本-20260920-104440.md：阶段/步骤、完整模块/TDD/结果契约及验收数据格式。
- workspace.json、README.md、init.sh、mvn.sh、pnpm.sh、verify.sh：固定环境和统一入口。

## 验证与限制

工具自测 31/31 通过；新增 TS 独立报告比较、网络拦截/fixture、循环连接参数日志修复均有 RED/GREEN。完整普通部分最终在宿主运行，132 文件/5328 用例通过，含内存内 WalletWire 集成，不接数据库；4 条精确失败 fixture，零未登记网络请求。耗时 2:00.76，峰值 RSS 1530540 KiB。

manual 实际执行 536870928 字节输入，1/1 通过，耗时 37:16.72，峰值 RSS 2000384 KiB。首次 manual 在 guard 建立前于禁网沙箱独立启动，已审查为纯 AES 字节计算；manifest 如实标记 audited-pure-computation，无伪造网络日志。后续完整入口对两个进程均使用 guard。1 MiB 资源探针不计入 SDK 基线。

API 行为及两端实际结果仍待准备。manual 后续须记录密文/tag 和解密输入输出，不能仅以两个实现各自往返成功代替一致性；大输出需要逐字节可核对的二进制记录。正式 check 当前应退出 1，缺失 5329 Java 映射；compare-ts 不能当作 Java 迁移通过。

## Next Session

读取规则、计划与状态并运行 ./init.sh。将 migration-api-contract 设为唯一进行中项，完成六模块全部 API/行为到 com.metanet4j.bsv 的逐项映射，包含无测试的 API、默认值/状态/异常/异步、内部断言及浏览器/Node/React Native 环境差异。API/测试边界解决后继续用例映射、输入重放、真实采集和 P0 联合验收；不得提前进入 P1。

无需因开启新会话重跑已验证且源码未变的 37 分钟 manual；需要重新采集实际输入/输出或阶段累计验收时按契约执行完整范围。所有测试进程已完成。

本次唯一工程为 metanet4j-bsv-sdk；新增 wallet/auth 包目录提交 72d2007，基础测试 1/1。范围复核和依赖清点修复在根仓提交 3615e0a。其他四工程源码/测试/POM/配置只读，固定 TS 上游无改动，未推送。根仓既有无关改动保留，收尾只提交本任务资料和工具。
