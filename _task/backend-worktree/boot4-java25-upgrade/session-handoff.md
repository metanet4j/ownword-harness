# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 范围与公开 API 测试，并以 `/goal` 要求持续推进到全部完成、遇无法解决的阻塞才停下报告。U0—U5 已完成（U5 三模块单元验收提交 c8c45c3、4904dac、fb29000；实连集成测试提交 5174917）；U0—U6 已完成、U7 进行中（component-file 提交 2195d08，59/0/0/0，含 8 个 disabled 用例改写；component-cache 提交 a7359a8，34/0/0/0；component-message 提交 d77695d，31/0/0/0 零缺口，并修复 base 的 BitcoinSchemaDto 缺陷）。U6 五模块单元全部达标（component-tx 29、component-bap 63（含 BapSearchListener 漏注入的最小修复）、component-bsocial 76、component-bitcoinschema 4、component-handler 5），并补齐 Mongo（6 例）与 MySQL（4 例）两条跨存储链路集成（提交 8a778c9，证据 evidence/20260928T211704Z/）；下一项 U7 外围能力。开工前先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK/component `target` 只允许串行运行 Maven；集成测试须在宿主环境提权执行。不要读取 Archive、推送远端、广播主网或清理共享中间件数据。

U5 证据：单元 store-sql `evidence/20260928T162746Z/`（11 例）、store-mongo `evidence/20260928T162233Z/`（56 例）、store-search `evidence/20260928T161725Z/`（32 例）；集成 store-search `evidence/20260928T160246Z/`（4 例）、store-mongo `evidence/20260928T161101Z/`（6 例）、store-sql `evidence/20260928T161623Z/`（5 例）。集成证据含 maven.log、Surefire XML、metadata.json 与服务侧日志/残留检查。U3 证据：component-model 20/0/0/0（`evidence/20260928T100401Z/`）、component-common 41/0/0/0（`evidence/20260928T103233Z/`）、component-core 纯接口 N/A（`evidence/20260928T103553Z/`）；U2 证据 `evidence/20260928T093257Z/`，U1 base 回归 `evidence/20260928T092443Z/`。

## Blockers

1. 无阻塞：共享中间件五个容器运行中且 healthy，连接信息见 `infra/README-ownword-infra-20260915-1720.md`（Mongo 需 `authSource=admin`，MySQL 需 `allowPublicKeyRetrieval=true`）。集成测试须用每轮唯一的库/索引/表并自行清理，运行方式为 `clean test -Dgroups=integration -DexcludedGroups=external`（不带 unit-coverage profile）。
2. 覆盖缺口一律按 `unit-coverage-exceptions.json` 精确清单登记（jacoco:check 按仓库属性排除 + `verify-unit.py` 双向核对）；`verify-unit.py` 的例外分支计数比较已修复为 `counters.get("BRANCH", 0)`（此前无 BRANCH 计数器的例外类会被误判）；暴露的缺陷按“失败回归 → 最小修复”处理并记入提交。

## Files

本任务主仓状态与验收文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`、`unit-coverage-exceptions.json`、`verify-unit.py`、`doc/单元测试全覆盖计划-20260920-090603.md`。component 仓库根新增 `lombok.config`；聚合 POM 含测试依赖与例外属性。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。证据目录为本地运行产物（evidence/ 已被 .gitignore 忽略），不代替 Git 提交。

## Next Session

继续 `unit-u7-adapters` 的最后一个模块：api-common（GlobalExceptionTranslator、GlobalApiLogAspect/LogAspect、BaseApiResult/R/ApiResult、ValidateUtils、JwtTokenProvider、注解共 10 类），用受控替身补单元测试并 `verify-unit.py --mode accept --scope metanet4j-api-common` 严格验收（缺口按 `unit-coverage-exceptions.json` 精确清单登记并同步 `jacoco.unit.check.excludes`）；随后补 Redis（6379）/Kafka（9092）实连集成与文件协议的本地可控服务集成，再进入 U8/U9。

可复用经验：Mockito `mockConstruction` 处理 `new` 出来的客户端（如 RedisAtomicLong）、`mockStatic` 处理 SpringUtil 等静态入口；复制自框架的配置类可用「build* 语义断言 + 反射逐项存取器往返」覆盖；**模块改动若涉及 base，必须先 install base 再跑 component 测试**（component 聚合不包含 base 模块）。沿用经验：MapStruct 生成实现带 SOURCE 保留的 `@Generated`（JaCoCo 不过滤，需按映射契约覆盖）；MyBatis-Plus Lambda wrapper 需先 `TableInfoHelper.initTableInfo(...)`；手工装配 MySQL 需挂 `MetaObjectHandler` 且事务代理用 `proxyTargetClass=true`；集成测试证据按 `evidence/<run-id>/<仓库>/<模块>/integration/` 归档。
