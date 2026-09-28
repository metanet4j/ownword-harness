# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 范围与公开 API 测试，并以 `/goal` 要求持续推进到全部完成、遇无法解决的阻塞才停下报告。U0—U5 已完成（U5 三模块单元验收提交 c8c45c3、4904dac、fb29000；实连集成测试提交 5174917）；U6 进行中：五个模块单元测试全部完成——component-tx（630303b，29/0/0/0）、component-bap（2fbd3f7，63/0/0/0，含 BapSearchListener 注入缺陷的最小修复）、component-bsocial（b9bfb97，76/0/0/0）、component-bitcoinschema（4/0/0/0）、component-handler（5/0/0/0，提交 2648727），剩余跨存储业务链路集成。开工前先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK/component `target` 只允许串行运行 Maven；集成测试须在宿主环境提权执行。不要读取 Archive、推送远端、广播主网或清理共享中间件数据。

U5 证据：单元 store-sql `evidence/20260928T162746Z/`（11 例）、store-mongo `evidence/20260928T162233Z/`（56 例）、store-search `evidence/20260928T161725Z/`（32 例）；集成 store-search `evidence/20260928T160246Z/`（4 例）、store-mongo `evidence/20260928T161101Z/`（6 例）、store-sql `evidence/20260928T161623Z/`（5 例）。集成证据含 maven.log、Surefire XML、metadata.json 与服务侧日志/残留检查。U3 证据：component-model 20/0/0/0（`evidence/20260928T100401Z/`）、component-common 41/0/0/0（`evidence/20260928T103233Z/`）、component-core 纯接口 N/A（`evidence/20260928T103553Z/`）；U2 证据 `evidence/20260928T093257Z/`，U1 base 回归 `evidence/20260928T092443Z/`。

## Blockers

1. 无阻塞：共享中间件五个容器运行中且 healthy，连接信息见 `infra/README-ownword-infra-20260915-1720.md`（Mongo 需 `authSource=admin`，MySQL 需 `allowPublicKeyRetrieval=true`）。集成测试须用每轮唯一的库/索引/表并自行清理，运行方式为 `clean test -Dgroups=integration -DexcludedGroups=external`（不带 unit-coverage profile）。
2. 覆盖缺口一律按 `unit-coverage-exceptions.json` 精确清单登记（jacoco:check 按仓库属性排除 + `verify-unit.py` 双向核对）；`verify-unit.py` 的例外分支计数比较已修复为 `counters.get("BRANCH", 0)`（此前无 BRANCH 计数器的例外类会被误判）；暴露的缺陷按“失败回归 → 最小修复”处理并记入提交。

## Files

本任务主仓状态与验收文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`、`unit-coverage-exceptions.json`、`verify-unit.py`、`doc/单元测试全覆盖计划-20260920-090603.md`。component 仓库根新增 `lombok.config`；聚合 POM 含测试依赖与例外属性。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。证据目录为本地运行产物（evidence/ 已被 .gitignore 忽略），不代替 Git 提交。

## Next Session

补 `unit-u6-business` 的跨存储业务链路集成：用真实 Mongo/MySQL/ES（每轮唯一库/索引，`@Tag("integration")`，命令 `clean test -Dgroups=integration -DexcludedGroups=external`）验证 raw 交易 → resolver → handler → 存储的端到端链路，BAP 与 bsocial 各留成功路径与失败传播路径的证据；随后进入 U7（component-file → cache → message → api-common）。沿用经验：MapStruct 生成实现带 SOURCE 保留的 `@Generated`（JaCoCo 不过滤，需按映射契约覆盖）；MyBatis-Plus Lambda wrapper 需先 `TableInfoHelper.initTableInfo(...)`；Spring 上下文回归用例可暴露漏注入类缺陷；集成测试证据按 `evidence/<run-id>/<仓库>/<模块>/integration/` 归档（脚本口径见 U5）。
