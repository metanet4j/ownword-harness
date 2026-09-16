# AGENTS.md — metanet4j 升级任务（Spring Boot 4.1.1 + Java 25 + 中间件升级）

> 本文件是本任务的**开工门禁**，优先级高于工作区级 `AGENTS.md`。
> 进入本目录做任何事之前，先读本文件，再读 `feature_list.json` 与 `session-handoff.md`。

## 1. 任务是什么

把 4 个独立 Git 仓库的 metanet4j 后端，从 **Spring Boot 2.3.2 / Java 11** 一步升级到
**Spring Boot 4.1.1 / Java 25**，并把中间件一并升级：

| 组件 | 目标版本 |
|---|---|
| Java / Spring Boot / Spring Cloud | 25 / 4.1.1 / 2025.1.3 |
| MongoDB（服务端 / 驱动） | 8.0.32 / 5.8.1 |
| Elasticsearch（服务端 / 客户端） | 9.4.5 / 9.4.5（走官方推荐 Rest5Client + Jackson3JsonpMapper） |
| Kafka（broker / 客户端） | 4.2.1（KRaft）/ 4.2.1 |
| Redis / Redisson | 7.4.11 / 4.7.0 |
| MySQL（服务端 / 驱动） | 8.4.11 / Connector-J 9.7.0 |

**唯一事实来源**：`doc/升级计划-Boot4-Java25.md`（含版本矩阵、决策 D1–D26、逐仓库改动清单、验证门禁）。
与本文冲突时以升级计划为准；升级计划与评审报告冲突时，先改文档再改代码。

评审记录：`doc/review-升级计划-Boot4-Java25-20260915-1545.md`（首轮 P0/P1）、
`doc/review-升级计划-Boot4-Java25-复评-20260915-1604.md`（复评，测试门禁 P0-A/P0-B）。

## 2. Startup Workflow（每次会话开工流程）

Before writing code，按顺序做完这 6 步：

1. `pwd` 确认在 `/home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade`。
2. 读本文件、`feature_list.json`、`session-handoff.md`。
3. 运行 `./init.sh` 确认环境与仓库状态；有异常先修，不要带病开工。
4. 从 `feature_list.json` 取 `activeItem`（为 `null` = 等用户批准，不要自行开工）。
5. **One feature at a time**：从 `feature_list.json` 只取一项做完；**Stay in scope**：不越界改无关文件。
6. 需要改代码时**先取得用户明确批准**，再动手。

若 `./init.sh` 失败，先修环境，再谈新工作。

## 3. Definition of Done

一项任务只有**同时**满足以下四条才算完成：

- [ ] 目标行为已实现（或该阶段要求的产物已产出）
- [ ] 要求的验证**真的跑过**（`./init.sh --full` 或该阶段门禁命令），并保留命令与输出
- [ ] 证据记录到 `feature_list.json` 的 `evidence` 与 `progress.md`
- [ ] 仓库可从标准启动路径重新开工（`./init.sh` 可跑，工作区干净）

任一条件不满足，不得标记 `done`。

## 4. End of Session（会话收尾流程）

Before ending a session，按顺序做完：

1. 更新 `progress.md`：`Current State`、`Last Updated`、`Current Objective`、`Recommended Next Step`。
2. 更新 `feature_list.json`：该项 `status` 与 `evidence`（claim done 必须附命令与输出）。
3. 更新 `session-handoff.md`：`Blockers`、`Files`、`Next Session`。
4. 四个子仓库各自 commit（中文 Conventional Commits）；本任务**不推送远端**。
5. 留下干净可 restartable 的工作区：`./init.sh` 能直接跑，无残留临时文件。

## 5. 目录结构

```
boot4-java25-upgrade/
├── AGENTS.md / feature_list.json / progress.md / session-handoff.md / init.sh   ← harness 五件套
├── doc/                     ← 升级计划 + 两份评审（已入 ownword 版本控制）
├── metanet4j-parent/        ← 独立 Git 仓库，分支 feature/java21
├── metanet4j-base/          ← 独立 Git 仓库
├── metanet4j-sdk/           ← 独立 Git 仓库
└── metanet4j-component/     ← 独立 Git 仓库（多模块聚合）
```

四个子仓库**不在 ownword 主仓的版本控制内**（`.git/info/exclude` 按仓库逐个排除，仅任务文档被跟踪）。
每个子仓库独立提交，commit 遵守 Conventional Commits 且用中文描述。

## 6. 构建命令（固定模板，不可简化）

```bash
JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem \
$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn \
  -s $HOME/.m2/metanet4j-settings.xml \
  -B clean package          # 测试验证时用 clean test（必须带 clean，见 §7）
```

- 本地仓库固定在 `~/.m2/metanet4j`（经 `~/.m2/metanet4j-settings.xml`），与默认 `~/.m2/repository` 隔离。
- 安装顺序：`parent`（`-N install`）→ `base` → `sdk` → `component`（聚合）。
- 子模块 `<parent>` 未写 `relativePath`，父 POM 必须先 install。

## 7. 硬性约束（违反即返工）

1. **工具链版本隔离**：Java 25 / Maven 3.9.16 **只用于本任务**。禁止 `sdk default java|maven`、
   禁止改 sdkman `current`、禁止改 shell 启动脚本里的 `JAVA_HOME`/`PATH`。全局默认仍是 JDK 8 / Maven 3.9.9，其他环境不受影响。
2. **禁止裸 `mvn`**：不设 `JAVA_HOME` 时 Maven 跑在 JDK 8 上，`--release 25` 直接失败。
3. **测试一律 `mvn clean test`**：本项目历史上出现过"surefire 从陈旧 `target/` 字节码取结果"导致的假失败/假通过，
   不 clean 的测试结果不可信。
4. **未经批准不改代码**：实施前必须先得到用户明确批准。选方案 ≠ 批准开工。
5. **中间件用共享设施**：不要自起容器。用 `ownword/infra/`（见 §9）。
6. **不推送远端**：本任务只做本地提交，除非用户明确要求推送。
7. 主链路不启 Redis/MySQL；它们只在 B 档验证中出现。

## 8. 验证门禁（claim done 之前必须跑过并贴证据）

```bash
./init.sh            # 环境与仓库状态自检（秒级）
./init.sh --full     # 追加真实构建与测试；当前阶段预期失败，见下方说明
```

- **分模块测试执行数**：不接受"总数 > 0"，必须逐模块给出 surefire 执行数（base / sdk / component-test / connect-planaria）。
- **`contextLoads` 出现性**：`grep -r contextLoads */target/surefire-reports/*.txt` 必须命中，否则"上下文启动"冒烟等于没跑。
- **依赖漂移断言**：`elasticsearch-java=9.4.5` 且不出现 legacy `elasticsearch-rest-client`；
  `redisson-spring-data-41` 存在且无 `redisson-spring-data-2x`；`kafka-clients=4.2.1`；`mongodb-driver-sync=5.8.1`；`mysql-connector-j=9.7.0`。
- **grep 门禁**：`javax.*` 仅允许 `AesCBCUtil`；Boot 4 旧包名归零；`RedissonAutoConfigurationV2` 归零；
  `HttpHost|RestClientTransport|org.elasticsearch.client.RestClient` 归零。
- `./init.sh --full` **在 P2/P3/P4 完成前预期失败**（当前 `metanet4j-parent` 仍是 Boot 2.3.2 + lombok 1.18.20，JDK 25 下编译直接崩）。
  失败即当前进度，不代表环境坏。

## 9. 共享中间件（跨任务基础设施）

位置 `ownword/infra/`（**不在本任务目录内**），compose 项目 `ownword-infra`：

```bash
cd /home/haodev/ownword/infra && ./up.sh      # 启动并等待全部 healthy
./status.sh                                    # 容器/端口/版本
./down.sh                                      # 停止，保留数据；-v 才清数据（本任务不要用 -v）
```

| 服务 | 连接 |
|---|---|
| MongoDB 8.0.32 | `mongodb://bschema:bschema123@localhost:27017/bschema?authSource=admin`（**authSource 不可省，实测省略报 Authentication failed**） |
| Elasticsearch 9.4.5 | `http://localhost:9200`（无认证） |
| Kafka 4.2.1 | `localhost:9092`（**KRaft，无 ZooKeeper**） |
| Redis 7.4.11 | `redis://localhost:6379`（无密码） |
| MySQL 8.4.11 | `jdbc:mysql://localhost:3306/bap_user?...&allowPublicKeyRetrieval=true`，`root/root123` |

镜像来源：Docker Hub 经 daemon 直连不可达，一律走 `docker.m.daocloud.io` 全限定名；`docker.elastic.co` 可直连。

## 10. 升级流程（Escalation）

- 架构决策：查 `doc/升级计划-Boot4-Java25.md` 的决策表（D1–D26）；文档未覆盖则问用户。
- 版本兼容争议：以官方文档为准（工作区规则明确要求），把链接与结论写进计划。
- 发现计划与实际不符：先改计划文档，再改代码，并在 `progress.md` 记录偏差。
- 卡住超过两轮：停下来把阻塞条件写清楚再问用户，不要反复试错。
