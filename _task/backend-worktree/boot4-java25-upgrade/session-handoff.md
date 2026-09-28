# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 的实施范围及公开 API 测试。U0、U1 与 U2 已完成；U2 落实两项决定：远程转移保留 `Transaction` 返回并新增 `prepareSendOrdinal` 准备入口，12 行无行为或不可达字节码按精确例外记录。当前仅 `unit-u3-foundation` 待开工。先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK `target` 只允许串行运行 Maven；集成测试须在宿主环境提权执行。不要读取 Archive、推送远端、广播主网或清理共享中间件数据。

SDK 提交 `670ee3d`：`python3 verify-unit.py --mode accept --scope metanet4j-sdk` 退出 0，203/0/0/0，LINE 1965/1977、BRANCH 514/514、METHOD 445/455；证据 `evidence/20260928T093257Z/`（head 670ee3d），产物已安装。父 POM 例外机制提交 `7302e1b`；base 回归 19/0/0/0，证据 `evidence/20260928T092443Z/`。例外清单与理由见 `unit-coverage-exceptions.json`，反例证据 `evidence/20260928-u2-exception-controls/`。

## Blockers

1. 共享中间件当前没有运行容器。启动下一阶段的数据库、搜索、消息及缓存集成测试前，按 `infra/README-*.md` 核对连接、服务日志和资源隔离。
2. 无其他阻塞。SDK 的 12 行缺口已按用户批准口径记录为精确例外；任何新增未覆盖字节码或例外失效都会让严格验收失败（`verify-unit.py` 双向核对 + `jacoco:check` 排除清单）。

## Files

本任务主仓的状态与验收文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`、`unit-coverage-exceptions.json`、`verify-unit.py`、`doc/单元测试全覆盖计划-20260920-090603.md`。SDK 工作树 0 脏，HEAD `670ee3d`；父仓库 HEAD `7302e1b`。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。各证据目录为本地运行产物，不代替 Git 提交。

## Next Session

从 `unit-u3-foundation` 开始：按计划 §5 顺序推进 component 基础模块（model → common → core），沿用同一验收口径（`verify-unit.py --mode accept`；如遇无行为或不可达字节码，先按精确清单机制登记再验收）；每模块完成后提交并更新状态文件。
