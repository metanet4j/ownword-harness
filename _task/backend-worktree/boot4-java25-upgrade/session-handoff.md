# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 范围与公开 API 测试，并以 `/goal` 要求持续推进到全部完成、遇无法解决的阻塞才停下报告。U0—U4 已完成；U5 进行中：store-sql、store-mongo、store-search 三模块单元验收已通过（提交 c8c45c3、4904dac、fb29000），三模块的实连集成测试待实施。开工前先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK/component `target` 只允许串行运行 Maven；集成测试须在宿主环境提权执行。不要读取 Archive、推送远端、广播主网或清理共享中间件数据。

U3 证据：component-model 20/0/0/0（`evidence/20260928T100401Z/`）、component-common 41/0/0/0（`evidence/20260928T103233Z/`）、component-core 纯接口 N/A（`evidence/20260928T103553Z/`）；提交 component `63560a3`、`4d3cf66`。U2 证据 `evidence/20260928T093257Z/`（head 670ee3d），U1 base 回归 `evidence/20260928T092443Z/`。

## Blockers

1. 无阻塞：共享中间件五个容器运行中且 healthy，连接信息见 `infra/README-ownword-infra-20260915-1720.md`（Mongo/MySQL 需带认证参数）。集成测试须用每轮唯一的库/索引/表并自行清理。
2. 覆盖缺口一律按 `unit-coverage-exceptions.json` 精确清单登记（jacoco:check 按仓库属性排除 + `verify-unit.py` 双向核对）；`verify-unit.py` 的例外分支计数比较已修复为 `counters.get("BRANCH", 0)`（此前无 BRANCH 计数器的例外类会被误判）；暴露的缺陷按“失败回归 → 最小修复”处理并记入提交。

## Files

本任务主仓状态与验收文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`、`unit-coverage-exceptions.json`、`verify-unit.py`、`doc/单元测试全覆盖计划-20260920-090603.md`。component 仓库根新增 `lombok.config`；聚合 POM 含测试依赖与例外属性。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。证据目录为本地运行产物（evidence/ 已被 .gitignore 忽略），不代替 Git 提交。

## Next Session

继续 `unit-u5-storage` 的集成部分：为 store-search（ES 唯一索引）、store-mongo（唯一库 + Spring Data 仓库/事件监听真实装配）、store-sql（唯一库 + MyBatis-Plus 真实装配）各写 `@Tag("integration")` 测试，用 `clean test -Dgroups=integration -DexcludedGroups=external` 提权运行并保存证据；随后 U6（component-tx → bap → bsocial → bitcoinschema → handler）。
