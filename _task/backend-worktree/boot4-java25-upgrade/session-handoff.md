# session-handoff.md — Boot 4 / Java 25 测试任务交接

## 当前状态

胡先生要求四个子仓库建立完整单元测试与集成测试，已批准 U0—U9 范围与公开 API 测试，并以 `/goal` 要求持续推进到全部完成、遇无法解决的阻塞才停下报告。U0—U6 已完成。U7 四模块单元全部严格验收通过：component-file 59/0/0/0（2195d08）、component-cache 34/0/0/0（a7359a8，修复 Redisson 配置装配缺陷 225da53）、component-message 31/0/0/0（d77695d，零缺口）、api-common 59/0/0/0（6a1b0af），均 gaps=0。外围集成已完成 Redis 实连 14/0/0/0 与 Kafka 实连 6/0/0/0；仅 FTP/SFTP 的本地可控服务集成未完成（无 FTP/SFTP 服务可连）。开工前先读本目录 `AGENTS.md`、`../AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，运行 `./init.sh`。共享 SDK/component `target` 只允许串行运行 Maven；集成测试须在宿主环境执行。不要读取 Archive、推送远端或广播主网。

U5 证据：单元 store-sql `evidence/20260928T162746Z/`（11 例）、store-mongo `evidence/20260928T162233Z/`（56 例）、store-search `evidence/20260928T161725Z/`（32 例）；集成 store-search `evidence/20260928T160246Z/`（4 例）、store-mongo `evidence/20260928T161101Z/`（6 例）、store-sql `evidence/20260928T161623Z/`（5 例）。集成证据含 maven.log、Surefire XML、metadata.json 与服务侧日志/残留检查。U3 证据：component-model 20/0/0/0（`evidence/20260928T100401Z/`）、component-common 41/0/0/0（`evidence/20260928T103233Z/`）、component-core 纯接口 N/A（`evidence/20260928T103553Z/`）；U2 证据 `evidence/20260928T093257Z/`，U1 base 回归 `evidence/20260928T092443Z/`。

## Blockers

1. 无阻塞：共享中间件五个容器运行中且 healthy，连接信息见 `infra/README-ownword-infra-20260915-1720.md`（Mongo 需 `authSource=admin`，MySQL 需 `allowPublicKeyRetrieval=true`）。集成测试须用每轮唯一的库/索引/表并自行清理，运行方式为 `clean test -Dgroups=integration -DexcludedGroups=external`（不带 unit-coverage profile）。
2. 覆盖缺口一律按 `unit-coverage-exceptions.json` 精确清单登记（jacoco:check 按仓库属性排除 + `verify-unit.py` 双向核对）；暴露的缺陷按“失败回归 → 最小修复”处理并记入提交。
3. U7 剩余的 FTP/SFTP 集成需要真实 FTP/SFTP 服务才能推进：共享 `ownword/infra` 只有 Mongo/ES/Kafka/Redis/MySQL，本机无 vsftpd/pure-ftpd/sshd，`com.sun.net.ftp.FtpServer` 已从 JDK 移除。该项不阻塞 U8/U9。

## Files

本任务主仓状态与验收文件：`feature_list.json`、`progress.md`、`session-handoff.md`、`unit-test-inventory.json`、`unit-coverage-exceptions.json`、`verify-unit.py`、`doc/单元测试全覆盖计划-20260920-090603.md`。component 仓库根新增 `lombok.config`；聚合 POM 含测试依赖与例外属性。ownword 主仓既有 `AGENTS.md`、`standard/`、`.agents/` 等无关改动须保留且不得混入本任务提交。证据目录为本地运行产物（evidence/ 已被 .gitignore 忽略），不代替 Git 提交。

## Next Session

U7 只剩 FTP/SFTP 的本地可控服务集成：需要一个可用的真实 FTP/SFTP 服务（共享基础设施不提供，本机也无服务软件），补上后即可把 U7 标记完成。其余部分不必等待，可直接推进 U8：mybatispuls-generator → component-test，验收命令 `verify-unit.py --mode accept --scope mybatispuls-generator` 与 `--scope metanet4j-component-test`。

可复用经验：Mockito `mockConstruction` 处理 `new` 出来的客户端（如 RedisAtomicLong）、`mockStatic` 处理 SpringUtil 等静态入口；复制自框架的配置类可用「build* 语义断言 + 反射逐项存取器往返」覆盖；**模块改动若涉及 base，必须先 install base 再跑 component 测试**（component 聚合不包含 base 模块）；`SpringApplicationBuilder(...).run()` 建上下文时，测试类的实例字段不会注入，必须用静态字段 + `context.getBean` 取 bean。实连集成要逐个 key/topic 记录并清理：Redis 的 key 经 JDK 序列化后带二进制前缀，客户端 `keys(prefix)` 匹配不到，只能用例侧记录 key 后按同一序列化路径删除。
