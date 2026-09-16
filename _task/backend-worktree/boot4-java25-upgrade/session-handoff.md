# session-handoff.md — 会话交接

> 唯一起步点：先读 `../AGENTS.md`（共享规则）、`../mvn-command.md`（命令模板）、
> `doc/升级计划-Boot4-Java25.md`（任务事实来源），再读本文件。
> 本文件只写"现在到哪了、下一步做什么、卡在哪"，不复述任务内容。

## 30 秒现状

- 进度：**P0 环境与基线清理已完成**；代码**零改动**（四子仓库 0 脏、分支 `feature/java21`）。
- 状态：`activeItem = boot4-p05-prefetch`（in-progress），**已激活，等待执行**。
- 环境：共享中间件五个容器 healthy；全局工具链未被污染（JDK 8 / Maven 3.9.9 原样）。

---

# 本次交接：执行 `boot4-p05-prefetch`（依赖预取）

下一个 agent 直接照本章执行。**本事项不需要改任何仓库文件，因此不需要额外批准。**

## 1. 目标与理由

**目标**：把升级后要用的全部依赖**预先拉进隔离仓库** `~/.m2/metanet4j`，并输出失败清单。

**理由**：该仓库目前只有约 **264MB / 513 个 jar**（早期探针留下的），**本项目依赖树从未完整下载过**。
如果不预取，坐标写错、版本不存在、网络拉不动这些问题会在 P2/P3/P4 逐层冒出来，每个都要停下来排查。
预取把它变成一次性、可复现的动作。

## 2. 执行内容（照做）

**步骤 1：准备一个探针工程**（放 `/tmp` 即可，不要放进任何仓库）

`/tmp/boot4-prefetch/pom.xml`，父 POM 用 `spring-boot-starter-parent:4.1.1`，`java.version=25`，
`dependencyManagement` 额外 import `org.springframework.cloud:spring-cloud-dependencies:2025.1.3`，
依赖列表覆盖以下坐标（版本见括注，未标版本的由 BOM 管理）：

| 类别 | 坐标 |
|---|---|
| Web/基础 | `spring-boot-starter-web`、`spring-boot-starter-webflux`、`spring-boot-starter-validation`、`spring-boot-starter-aspectj`、`spring-boot-starter-data-mongodb`、`spring-boot-starter-data-redis`、`spring-boot-starter-data-jpa`、`spring-boot-starter-test` |
| 数据/存储 | `com.baomidou:mybatis-plus-spring-boot4-starter:3.5.17`、`com.alibaba:druid-spring-boot-4-starter:1.2.28`、`com.mysql:mysql-connector-j`、`org.mongodb:mongodb-driver-sync`、`com.baomidou:mybatis-plus-generator:3.5.17`、`org.apache.velocity:velocity-engine-core:2.4.1` |
| 搜索 | `co.elastic.clients:elasticsearch-java:9.4.5` |
| 消息 | `org.springframework.kafka:spring-kafka`（客户端 4.2.1 由 BOM 管） |
| 缓存 | `org.redisson:redisson-spring-boot-starter:4.7.0` |
| 安全/文档 | `io.jsonwebtoken:jjwt-api:0.13.0` + `jjwt-impl` + `jjwt-jackson`、`io.swagger.core.v3:swagger-annotations-jakarta:2.2.55` |
| 注解 | `org.jspecify:jspecify` |
| 保留的老依赖 | `io.bitcoinsv.bitcoinjsv:bitcoinj-legacy:1.0.4`、`io.bitcoinsv.bitcoinjsv:bitcoinj-base`（版本由父 depMgmt 给，探针里可写 1.0.4）、`io.bitcoinsv.jcl:jcl-store-levelDB:1.0.5`、`com.github.briandilley.jsonrpc4j:jsonrpc4j:1.0`、`com.alibaba:fastjson:1.2.76`、`com.google.guava:guava:30.1.1-jre`、`org.apache.logging.log4j:log4j-slf4j2-impl:2.25.5`、`cn.hutool:hutool-all:5.7.12` |

**步骤 2：执行预取**（命令模板见 `../mvn-command.md`）

```bash
export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem
MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"
cd /tmp/boot4-prefetch
$MVN -B dependency:go-offline 2>&1 | tee /tmp/boot4-prefetch/prefetch.log
# 若 go-offline 有已知局限，补一次：
$MVN -B dependency:resolve-plugins dependency:resolve 2>&1 | tee -a /tmp/boot4-prefetch/prefetch.log
```

**步骤 3：产出结论**（贴命令与输出，不要只写"成功"）

```bash
du -sh ~/.m2/metanet4j                       # 预取前后体积对比
find ~/.m2/metanet4j -name '*.jar' | wc -l   # jar 数对比
grep -c 'Downloaded from central' /tmp/boot4-prefetch/prefetch.log
grep -iE 'ERROR|Could not resolve|Failure to find' /tmp/boot4-prefetch/prefetch.log | head -30
```

## 3. 验收标准（Definition of Done）

- [ ] 探针工程仅位于 `/tmp`，**未创建/修改任何仓库文件**（执行后 `git -C <四个仓库> status --porcelain` 仍为 0 行）
- [ ] `dependency:go-offline` 的失败清单被**逐条列出**（成功也要列出"解析到的关键版本"）
- [ ] 关键坐标确认可解析：ES 9.4.5、Kafka 4.2.1、Redisson 4.7.0、MyBatis-Plus 3.5.17、Druid 1.2.28、MongoDB 5.8.1、Connector/J 9.7.0、swagger-annotations-jakarta 2.2.55
- [ ] 日志落盘可复现（`/tmp/boot4-prefetch/prefetch.log`）
- [ ] 结论写入 `feature_list.json` 的 `evidence` 与 `progress.md`；本事项置 `done`，`activeItem` 置 `null`

## 4. 已知坑（别踩）

1. **必须带 `-s ~/.m2/metanet4j-settings.xml`**，否则依赖进全局 `~/.m2/repository`，污染其他项目。
2. **必须设 `JAVA_HOME`**，否则跑在全局 JDK 8 上。
3. **Docker Hub 直连不可达与本事项无关**（那是容器镜像）；Maven 走 Central，实测可达。若个别坐标 404/超时，重试一次再判定。
4. **`dependency:go-offline` 不是万能**：它对某些插件的传递依赖解析不全，属已知局限，所以步骤 2 有第二次补齐命令；缺的条目要记下来而不是当失败。
5. **探针 pom 的父版本用 4.1.1**：若 `spring-boot-starter-parent:4.1.1` 拉不到，先确认 Central 可达再判定（早期探针 `/tmp/gate0` 已成功解析过 Boot 4.1.1）。

## 5. 完成后

1. 更新 `feature_list.json`：`boot4-p05-prefetch` → `done`（附 evidence）、`activeItem` → `null`。
2. 更新 `progress.md`：`Current State`、`Last Updated`、`What's Done` 增行。
3. 更新本文件：把"本次交接"换成下一个事项（`boot4-p1-version`），或写明等待用户批准 P1/P2。
4. **只在 ownword 仓库提交文档**（`git add` 任务目录下的 harness 文件）；四个子仓库本次无改动，不应有提交。

---

## Next Session（后续顺序，做完一项再申请下一项）

1. ✅ `boot4-p05-prefetch`（本次交接，执行中）
2. `boot4-p1-version` 版本号统一 0.2.0（纯机械，门禁见计划 §6.1）——**改代码，需用户批准**
3. `boot4-p2-parent` 父 POM 改造——**lombok 1.18.20 必须换掉，否则 JDK 25 下编译直接崩**——**改代码，需用户批准**
4. 之后：P3（base+sdk）→ P4（component，含 ES 9 与 Redisson 4.7.0）→ 测试门禁（复评 P0-A/P0-B）→ P5 验证 → P6 收尾

## 开工自检

```bash
cd /home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade
./init.sh          # 环境 + 仓库状态（秒级）
./init.sh --full   # 追加真实构建；P2 之前预期失败，属正常进度
```

## Blockers（阻塞与未决取舍）

| 阻塞/取舍 | 说明 |
|---|---|
| P1/P2 需用户批准 | 本事项（P0.5）不需要；后续改代码的事项都需要 |
| P2 与测试门禁互相牵扯 | 测试门禁（`boot4-tests-jupiter`）**依赖 P2**：不改 parent 的 lombok 与测试依赖，测试根本跑不起来 |
| sdk 那 7 个曾报 NPE 的用例 | 需定性：是迁移引入还是既有问题（迁移前这些用例从未执行，无法直接对比） |
| Jackson 钉死何时清理 | 影响 base `JacksonUtil` 的迁移顺序（P3），需确认是否一次性做完 |
| `Archive/prototype/`（207MB 归档） | 按约定未纳入 ownword 版本控制 |

## Files（关键路径）

| 内容 | 位置 |
|---|---|
| 共享工程/环境规则 | `../AGENTS.md` |
| Maven 命令固定模板 | `../mvn-command.md` |
| 任务事实来源（目标/版本矩阵/决策/改动清单/门禁） | `doc/升级计划-Boot4-Java25.md` |
| 问题定性与评审 | `doc/review-升级计划-Boot4-Java25-20260915-1545.md`、`doc/review-...-复评-20260915-1604.md` |
| 共享中间件（连接信息唯一事实来源） | `ownword/infra/` |
| 阶段状态 | `feature_list.json` |
