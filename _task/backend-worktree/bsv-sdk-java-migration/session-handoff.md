# 会话交接

## 状态

P0 的 migration-scope-review 已完成。具体范围及依据见[完整模块与 API 映射](doc/完整模块与API映射-20260920-122800.md)：完整迁移 primitives/compat/script/transaction/wallet/auth，15 个候选模块逐项有结论。PushDrop 的真实钱包测试辅助代码、钱包类型接口和 WalletWire 的 Certificate 依赖要求纳入 wallet/auth；transaction 测试还依赖 compat。六模块依赖形成闭环，P1 逐模块逐行为实施后联合验收，P2 独立 SDK 最终验收。

当前清单为 292 文件、133 测试文件、5329 用例、7554 AST 位置；原 4275 用例和所有旧文件校验值原样保留。scopeReview 仍为 pending，须等七项 P0 工作联合验收完成。API/用例映射、完整 TS 基线、输入重放和真实采集均未完成；Java 功能映射仍为空。

## Files

- feature_list.json：唯一状态与验收清单，15 项中 6 项 done；activeItem 为空，nextItem 为 migration-ts-baseline。
- module-scope.json：六模块及 15 个 moduleReviews 的范围结论；跨目录测试归属。
- module-tests.json：全部文件校验值、运行注册用例、AST 位置及含类型/测试的依赖图。
- doc/模块迁移计划-20260920-103547.md：P0–P2 阶段、脚本职责与执行顺序。
- doc/测试迁移契约-20260920-101559.md：完整模块、TDD 和逐用例实际结果一致性门禁。
- doc/测试完整性脚本-20260920-104440.md：清点、映射、比较命令及数据格式。
- workspace.json、README.md、init.sh、mvn.sh、pnpm.sh、verify.sh：固定环境和执行入口。
- .cache/evidence/scope-*：本次候选清单/差异、RED/GREEN、24 项检查器自测、目标基础测试、init 与预期失败证据。

## Blockers

开始完整 TS 基线无已知环境阻塞；须先评估 AESGCM.man.test.ts 超过 512 MiB 输入的实际资源需求、审查网络隔离和 mocks。完整基线未执行，不能声明所有 TS 用例通过。TS 的浏览器/Node/React Native 等平台专属行为须在 API 契约中明确 Java 对应方式，不可直接排除测试。

## Next Session

读取规则、计划和状态，运行 ./init.sh。将 migration-ts-baseline 设为唯一进行中项：读取冻结清单实现真实运行入口，保持 TS 原断言与 manual 规模不变，保存独立报告和资源证据。完成后继续 migration-api-contract，再按依赖推进其余 P0；不能提前进入 P1。

依赖清点修复已经 TDD 验证：类型接口与测试辅助依赖反例先失败，修复后 24/24 通过。目标工程新增 wallet/auth 顶层包、测试与向量目录，提交为 72d2007，clean test 的 infrastructure 用例 1/1 通过。未新增 SDK 功能测试，不能计入复刻数量。正式 check 当前应退出 1，缺失 5329 Java 映射；不能通过删清单、自动填写 reviewed 或复制 TS 输出绕过门禁。

本次只修改 metanet4j-bsv-sdk 工程；其他四工程源码/测试/POM/配置只读。固定 TS 上游不改。任务根目录维护计划和验证工具，根仓既有无关修改不提交；未推送。每个完成事项按所属仓库提交，收尾同步状态。
