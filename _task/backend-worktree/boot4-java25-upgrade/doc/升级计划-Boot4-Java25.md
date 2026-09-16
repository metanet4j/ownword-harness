# metanet4j 升级计划：Spring Boot 4.1.1 + Java 25 + 0.2.0

> 本文是本次升级的**唯一事实来源**（版本矩阵、决策、改动清单、验证门禁）。实施过程中如与本文冲突，先改本文再改代码。
> 本文已吸收 `doc/review-升级计划-Boot4-Java25-20260915-1545.md` 与 `doc/review-升级计划-Boot4-Java25-复评-20260915-1604.md` 的 P0/P1 结论；P0 项已全部落入下方改动清单与 Gate。
> **2026-09-15 中途变更**：用户指定中间件全部升级到新版本（ES 9.4.5 / Kafka 4.2.1 / MySQL 8.4 / MongoDB 8.0 / Redis 7.4 / Redisson 4.7.0）。§2、§3（D8–D10、D19、D23–D26）、§6.5、§7.3 已按新矩阵改写。

| 项 | 值 |
|---|---|
| 状态 | **计划已修订（含中间件升级矩阵）、环境部分就绪；代码未改动**（执行待批准） |
| 评审依据 | `doc/review-升级计划-Boot4-Java25-20260915-1545.md`、`doc/review-升级计划-Boot4-Java25-复评-20260915-1604.md` |
| 制定日期 | 2026-09-15 |
| 任务根目录 | `_task/backend-worktree/boot4-java25-upgrade/` |
| 影响仓库 | `metanet4j-parent`、`-base`、`-sdk`、`-component`（4 个独立 Git 仓库） |
| 规模 | 25 个 `pom.xml`；31 个含 `javax.` 导入的 Java 文件（迁 30，1 个 `javax.crypto` 不动）；14 个 Jackson 使用文件；3 个 Boot 4 包迁移文件；1 个 ES 客户端迁移文件（`EsConfig`） |
| 版本号 | parent / base / component → **0.2.0**；sdk **保持 0.2.0**（同名重发） |

> **当前边界**：本任务只做两件事——产出升级计划、准备好环境。4 个仓库的代码与 pom **均未改动**，全部停留在 `dev` 基线（worktree 在 `feature/java21`，与 `dev` 零差异）。曾试跑的版本号改动已全部撤销（见 §11）。

---

## 1. 目标与范围

把后端从 Spring Boot 2.3.2 / Java 11 / Spring Cloud Hoxton.SR8 **一步到位**升级到 Spring Boot 4.1.1 / Java 25 / Spring Cloud 2025.1.3，并把产品线版本号统一到 0.2.0。

### 范围内

- 4 个 metanet4j 仓库，共 **25 个 `pom.xml`**：`metanet4j-component` 根 1 + 子模块 21 = 22，`parent` / `base` / `sdk` 各 1。
- 随升级必须改动的 Java 源码、配置、文档：
  - `javax → jakarta/org.jspecify`：31 个文件含 `javax.` 导入，迁 30 个；`sdk/crypto/AesCBCUtil.java` 的 `javax.crypto.*` 不动。
  - Jackson 2 → 3：14 个文件；其中 6 个只用 `com.fasterxml.jackson.annotation.*`（注解包不变，不改），8 个 `core/databind/datatype` 导入迁 `tools.jackson.*`。
  - Boot 4 autoconfigure 包迁移：6 处导入、3 个文件（见 D13 / §6.5）。
  - ES 客户端 7.17.5 → 9.4.5：`EsConfig` 的 mapper/transport 与依赖坐标（见 D8 / D25 / §6.5）。
  - 坐标替换：springfox、JJWT、MyBatis-Plus、Druid、MySQL、swagger 注解。
- 4 仓库共有 13 处 `<java.version>11</java.version>` 覆盖（parent + 12 子模块），全部删除。
- 中间件服务端升级（ES 9.4.5、Kafka 4.2.1、MySQL 8.4、MongoDB 8.0、Redis 7.4）由本次验证环境提供，服务端本身的部署变更不在本仓库范围内。

### 范围外

- `backend/bitcoinj-sv`：独立上游 fork，经中央仓库的 `io.bitcoinsv:*:1.0.4/1.0.5` 被引用，**不参与本次改动**。仅当它在 Java 25 下出现编译或运行失败时单独立项。
- 生产环境部署、灰度、发布（本次只到编译门禁 + 本地 B 档运行验证）。
- `component-test` 的 cache 依赖仍为注释态（主链路不启 Redis），但 **B 档仍起 Redis 7.4 容器**，用于验证 `component-cache` 的 Redisson 4.7.0 装配与读写路径（见 D19 / §7.3）。
- springdoc Swagger UI：代码只用到 swagger 注解，本次只引 `swagger-annotations-jakarta`，不引 springdoc starter；需要 UI 时单独立项。

---

## 2. 版本矩阵（锁定）

| 组件 | 升级前 | 升级后 | 依据 |
|---|---|---|---|
| Spring Boot | 2.3.2.RELEASE | **4.1.1** | 2026-08-20 发布，Java 17–26 |
| Java | 11 | **25** | Boot 4.1 支持 17–26 |
| Spring Cloud | Hoxton.SR8 | **2025.1.3** | Cloud 5.0.3；其兼容校验接受 Boot `4.0.x`、`4.1.x` |
| Spring Cloud Alibaba | 2.2.3.RELEASE | **移除 BOM** | 全仓仅 1 处 import + 2 处已注释 starter |
| Spring Framework | 5.2.x | 7.0.9（随 Boot） | Boot 4.1.1 BOM |
| Jackson | 2.13.2 | **tools.jackson 3.1.5 + annotations 2.21.5** | Boot BOM `jackson-bom=3.1.5`、`jackson-2-bom=2.21.5`；注解仍是 `com.fasterxml.jackson.annotation.*` |
| Elasticsearch 客户端 | 7.17.5 | **9.4.5（与服务端同版）** | 服务端升 9.4.5；Elastic 官方兼容策略：9.x 客户端 ↔ 9.x 服务端 |
| Elasticsearch 服务端 | 7.17.5 | **9.4.5** | 本次服务端一并升级 |
| MyBatis-Plus | 3.4.2 | **3.5.17**（`mybatis-plus-spring-boot4-starter`） | 坐标改名；Boot 4 专用 starter |
| Druid | 1.2.1 | **1.2.28**（`druid-spring-boot-4-starter`） | 坐标改名；新包 `com.alibaba.druid.spring.boot4.autoconfigure` |
| MySQL 驱动 | `com.mysql:mysql-connector-java:8.0.25` | **`com.mysql:mysql-connector-j` 9.7.0** | 坐标改名；Boot BOM 管理；官方要求 MySQL 8.0+，服务端为 8.4 LTS |
| MySQL 服务端 | 8.0 | **8.4 LTS** | 本次一并升级；Connector/J 9.7.0 支持 8.0 及以上 |
| MongoDB 服务端 | 4.x/6.x（历史） | **8.0.32** | 本次一并升级 |
| MongoDB 驱动 | 4.x（随 Boot 2） | **5.8.1（Boot BOM）** | Boot 4.1.1 `mongodb.version=5.8.1` |
| Redis | 5.x/6.x（历史） | **7.4 LTS** | 本次一并升级 |
| Redisson | 3.17.0 | **4.7.0** | Redisson 官方：4.0.0 起支持 Boot 4.0、4.6.0 起支持 Boot 4.1；starter 自带 `redisson-spring-data-41` |
| Kafka Broker | 2.8.1 | **4.2.1** | 本次一并升级；Kafka 4.x 起 ZooKeeper 模式移除，必须 KRaft |
| JJWT | 0.9.1 | **0.13.0**（api / impl / jackson） | 0.9.1 依赖 `javax.xml.bind`，Java 25 下运行即失败 |
| springfox | 2.9.2 | **`io.swagger.core.v3:swagger-annotations-jakarta:2.2.55`** | 代码只用注解；不用 springdoc starter |
| Jackson 2（传递依赖） | — | 保留（ES 9.4.5、jjwt-jackson 的 runtime 依赖） | 代码层禁用 `com.fasterxml.jackson.core/databind` 导入；**pom/运行期允许存在**（ES 客户端 pom 同时带 Jackson 2.22.0 与 Jackson 3.1.0，均为 runtime） |
| Lombok | 1.18.20 | **1.18.46（Boot BOM）** | 1.18.20 在 JDK 25 编译期直接崩 |
| SLF4J | 1.7.32 | **2.0.18（Boot BOM）** | `log4j-slf4j2-impl` 要求 SLF4J 2.x |
| Log4j2 | 2.20.0 | **2.25.5（Boot BOM）** | 随 Boot BOM |
| Hibernate Validator | 6.1.5.Final | **9.1.3.Final（Boot BOM）** | 提供 `jakarta.validation.*` |
| JUnit | 4.13 | **4.13.2 + Jupiter 6.0.3 + vintage 6.0.3** | Boot BOM `junit-bom=6.0.3`；JUnit 4 用例走 vintage |
| Mockito | `mockito-inline 4.11.0` | **`mockito-core 5.23.0`（Boot BOM）** | 4.11/ByteBuddy 1.12 不支持 JDK 25 |
| Lettuce | 5.3.2.RELEASE | **7.5.2.RELEASE（Boot BOM）** | 随 Spring Data Redis 4.1；Redis 运行期不在 B 档 |
| commons-lang3 | 3.10 | **3.20.0（Boot BOM）** | 删除显式降级钉死 |
| maven-compiler-plugin | 3.8.1（父显式） | **3.15.0（Boot BOM）** | 删除父显式 `<version>`，保留 annotationProcessorPaths |
| metanet4j | parent/base/component 0.1.0；sdk 0.2.0 | **统一 0.2.0** | sdk 保持 0.2.0 = 同名重发 |

---

## 3. 决策记录

| # | 决策 | 结论 | 理由 / 依据 |
|---|---|---|---|
| D1 | 迁移路径 | **一步到位**，不经过 3.5.x | 用户决策；3.5.x OSS 已 EOL |
| D2 | 本地仓库 | `~/.m2/metanet4j-settings.xml`，`localRepository=~/.m2/metanet4j` | 与既有仓库隔离 |
| D3 | 私服 | **不配置**，直连 Central | 用户指定；已验 Central 可达且新坐标齐全 |
| D4 | JDK | sdkman 注册 **`25.0.4.1-tem`**（Temurin 25.0.4.1+1），实体在 `/home/haodev/jdk/jdk-25.0.4.1+1`；**不切换 sdkman `current`** | sha256 双源校验一致；用户要求版本锁定仅限本任务 |
| D5 | Maven | `sdk install maven 3.9.16`（全局 default 仍 3.9.9，用绝对路径调用） | RC 版本不用于迁移 |
| D5a | **工具链版本隔离（用户约束）** | Java 25 / Maven 3.9.16 **只用于 `ownword` 本任务**；**禁止修改全局版本**：不执行 `sdk default java/maven`、不改 sdkman `current`、不改 `/etc/profile`、`~/.bashrc`、`~/.zshrc` 里的 JAVA_HOME/PATH；其他环境继续用它们原本的版本 | 用户 2026-09-15 明确要求；所有命令以绝对路径 + 显式 `JAVA_HOME` 调用（§4 模板） |
| D6 | sdk 版本号 | 保持 0.2.0 | 用户决策（接受同名重发） |
| D7 | Jackson | 全量迁 Jackson 3（`tools.jackson.*`）；`com.fasterxml.jackson.annotation.*` 注解不动 | Boot 4 默认；注解 2.21.5 由 `jackson-2-bom` 管理 |
| D8 | ES 客户端 | 升 **9.4.5**，与服务端同版；**走官方推荐的 Rest5Client transport**（ES 9 默认 transport，基于 Apache HttpClient 5）；`EsConfig` 改用 `ElasticsearchClient.of(...)` + `Jackson3JsonpMapper`；**不引入** legacy `org.elasticsearch.client:elasticsearch-rest-client` | 用户决策：以官方为准（服务端一并升 9.4.5、transport 走官方推荐）；官方 9.0.0 release notes：legacy `RestClient` 自 9.x 起变为可选外部依赖，替代品 Rest5Client 随客户端内置 |
| D9 | 验证档位 | **B 档**：MongoDB 8.0 + ES 9.4.5 + Kafka 4.2.1(KRaft) + Redis 7.4 + MySQL 8.4 | 本次服务端全部升级，验证范围随之覆盖五个中间件 |
| D10 | Kafka | **起 4.2.1 broker，KRaft 模式**（不再用 ZooKeeper） | Kafka 4.x 起 ZooKeeper 模式移除；客户端 4.2.1 与服务端 4.2.1 同版（官方矩阵：3.x/4.x broker 对 4.x 客户端 ✅ Fully Compatible） |
| D11 | 基线分支 | 4 仓库均以 `dev` 为基线；当前 worktree 在 `feature/java21`（与 `dev` 同点） | 当前均干净；技能默认 master，此处按实际取 dev |
| D12 | 回滚 | 开工前 4 仓库 dev 打 tag `pre-boot4-java25` | 保留可回退点 |
| D13 | Boot 4 autoconfigure 包迁移 | 按下表逐个改；Druid 新包为 `com.alibaba.druid.spring.boot4.autoconfigure` | Boot 4.1.1 jar 实测类已迁移 |
| D14 | 显式钉死清理 | 删除/上调：lombok、slf4j、log4j、hibernate-validator、jackson、junit、lettuce、mysql、commons-lang3、jakarta.json、elasticsearch.client 7.17.5；保留 fastjson 1.2.76、bcprov 1.71、guava 30.1.1 | 直接 depMgmt 条目优先于 import 的 BOM |
| D15 | Jackson 3 迁移范围 | 改 Java 导入 + pom 坐标 + 异常签名；注解类不改 | `JacksonUtil` 的 `catch(IOException)` 在 Jackson 3 下将不再成立 |
| D16 | JSpecify | 显式添加 `org.jspecify:jspecify`（Boot BOM 1.0.1）到 parent depMgmt + sdk 依赖 | sdk 无 Spring 依赖，`org.jspecify` 不会自动出现 |
| D17 | 测试引擎 | 保留 JUnit 4 用例：加 `junit-vintage-engine` + junit 4.13.2；基类去 `@RunWith` 保持 Jupiter；12 个继承类各自补 `@RunWith(SpringRunner.class)`；mockito-inline 换 `mockito-core 5.23.0` | Boot 4 starter-test 不带 vintage；不改则 21 个 JUnit4 用例不执行 |
| D18 | 悬空依赖 | 删除 `component-test` 的 `com.metanet4j.bootstrap:metanet4j-bootstrap:0.1.0` | 4 仓库与本地 m2 均无此 artifact，代码未引用；否则聚合构建直接失败 |
| D19 | component-cache / Redisson | **Redisson 3.17.0 → 4.7.0**（starter 自带 `redisson-spring-data-41`，Boot 4.1 下无需 exclusion）；改 `RedissonAutoConfiguration` 的 Boot 4 Redis 包名；从 redisson 排除 `javax.cache:cache-api`；全仓 grep `RedissonAutoConfigurationV2` 并改 `V4`；Redis 7.4 纳入 B 档做装配烟测 | Redisson 官方：4.0.0 起支持 Boot 4.0、4.6.0 起支持 Boot 4.1；`-XX` 后缀跟 Spring Data Redis 版本线，Boot 4.1 需 `-41`，3.17.0 带的是 `-26` 线，与 Spring Data Redis 4.1 硬冲突；`RedissonAutoConfigurationV2` 在 Boot 4 下静默失效 |
| D20 | compiler plugin | 删除父显式 `maven-compiler-plugin:3.8.1`，使用 Boot BOM 3.15.0；`<release>${java.version}</release>`；保留 mapstruct/lombok annotationProcessorPaths | Gate0 探针实际继承的是 3.15.0；父显式 3.8.1 会覆盖 BOM |
| D21 | enforcer | `requireJavaVersion [25,)`；`bannedDependencies` 拦 `javax.*`，白名单 `javax.cache:cache-api`（redisson 传递） | 不留 javax 残留；jsr305 属 `com.google.code.findbugs`，不需要 javax 白名单 |
| D22 | swagger | 只引 `swagger-annotations-jakarta`，不引 springdoc starter | 代码只用到注解，避免给所有模块引入 springdoc autoconfig |
| D23 | 中间件版本矩阵（用户指定） | ES 9.4.5、Kafka broker 4.2.1、MySQL 8.4 LTS、MongoDB 8.0.32、Redis 7.4 LTS、Redisson 4.7.0 | 用户决策；兼容性已逐条对官方文档核对，结论见 D24 与 §6.6 门禁 |
| D24 | 兼容性核对结论 | Java 25/Boot 4.1.1/Maven 3.9.x ✅；Cloud 2025.1.3 ✅（其 BOM 按 Boot 4.0.8 构建，4.1.x 在兼容声明内）；ES 9.4.5 客户端↔服务端 ✅；Kafka 4.2.1 客户端↔broker ✅；Connector/J 9.7.0 ↔ MySQL 8.4 ✅（官方要求 8.0+）；Redisson 4.7.0 ↔ Boot 4.1 ✅；MongoDB 驱动 5.8.1 ↔ 8.0.32：按用户指定执行 | 官方依据：Spring Boot System Requirements、Kafka 兼容矩阵、Elastic Java client 兼容策略、MySQL Connector/J 兼容章、Redisson Boot 4 专文 |
| D25 | ES 9 迁移面 | 只改 `EsConfig`（mapper/transport）与客户端依赖；业务查询 API 不动 | 代码实测未触及 ES 9 任何破坏性 API（aggregations/valueBody/matchedQueries/indicesBoost/dynamicTemplates/msearch/esql 均为 0 处） |
| D26 | 现存 ZooKeeper 容器 | 保留但**不再服务 Kafka**（Kafka 4.2.1 走 KRaft）；`e2e-zookeeper` 现仅供 rocketmq 使用 | Kafka 4.x 移除 ZooKeeper 模式 |

### Boot 4 包迁移对照（D13）

| 旧（Boot 2/3） | 新（Boot 4.1.1） | 使用位置 |
|---|---|---|
| `org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration` | `org.springframework.boot.jdbc.autoconfigure.DataSourceAutoConfiguration` | `component-test` 主类 |
| `...autoconfigure.jdbc.DataSourceTransactionManagerAutoConfiguration` | `org.springframework.boot.jdbc.autoconfigure.DataSourceTransactionManagerAutoConfiguration` | 同上 |
| `...autoconfigure.orm.jpa.HibernateJpaAutoConfiguration` | `org.springframework.boot.hibernate.autoconfigure.HibernateJpaAutoConfiguration` | 同上 |
| `...autoconfigure.http.HttpMessageConverters` | `org.springframework.boot.http.converter.autoconfigure.HttpMessageConverters` | `DefaultFeginClient`（未使用的 import，直接删除） |
| `...autoconfigure.data.redis.RedisAutoConfiguration` | `org.springframework.boot.data.redis.autoconfigure.DataRedisAutoConfiguration` | `RedissonAutoConfiguration` |
| `...autoconfigure.data.redis.RedisProperties` | `org.springframework.boot.data.redis.autoconfigure.DataRedisProperties` | `RedissonAutoConfiguration` |
| `com.alibaba.druid.spring.boot.autoconfigure.DruidDataSourceAutoConfigure` | `com.alibaba.druid.spring.boot4.autoconfigure.DruidDataSourceAutoConfigure` | `component-test` 主类 |

### 已核实「不需要」的服务

| 服务 | 结论 | 证据 |
|---|---|---|
| 服务 | 结论 | 证据 |
|---|---|---|
| Nacos | 不需要 | `component-test/pom.xml` 两个 nacos starter 被注释；`bootstrap.yml` 全注释 |
| Redis（主链路） | 主链路不需要，但 **B 档起容器验证 component-cache** | `component-test/pom.xml` 的 `metanet4j-component-cache` 依赖被注释；`tx-filter` / `component-cache` 无任何模块运行时依赖 |
| MySQL（主链路） | 主链路不需要，B 档仅验证连接器与建表往返 | 无用例引用 `MysqlBapService`/`JdbcTemplate`/`DataSource`；主类已 exclude DataSource + Druid + JPA |

---

## 4. 环境固化（Phase 0）

**工具链（已就绪，版本隔离在本任务内）**：

| 组件 | 项目内使用 | 全局状态（不动） |
|---|---|---|
| JDK | `~/.sdkman/candidates/java/25.0.4.1-tem` → `/home/haodev/jdk/jdk-25.0.4.1+1`（Temurin `25.0.4.1+1-LTS`） | sdkman `current` → **8.0.181-local（JDK 8）**，保持原样 |
| Maven | `~/.sdkman/candidates/maven/3.9.16/bin/mvn` | sdkman `current` → **3.9.9**，保持原样 |
| 本地仓库 | `~/.m2/metanet4j`（经 `~/.m2/metanet4j-settings.xml` 固定）；**当前仅 190MB，只有探针依赖，项目依赖树从未下载过** | 默认 `~/.m2/repository` 与 `whyt-server-repository` 等不受影响 |
| settings | `~/.m2/metanet4j-settings.xml` | 只含 `localRepository`；无私服、无镜像，直连 Central；不改 `~/.m2/settings.xml` |

**版本隔离要求（D5a）**：本次升级**只改本任务的调用方式，不改全局环境**。禁止：`sdk default java 25.0.4.1-tem`、`sdk default maven 3.9.16`、切换 `current` 软链、往 shell 启动脚本写 JAVA_HOME/PATH、`update-alternatives` 改系统 java。所有构建命令一律按下方模板以**绝对路径 + 显式 JAVA_HOME** 调用；其他项目/环境继续使用它们原本的 JDK 8 / Maven 3.9.9。

**项目内 Maven Wrapper：已移除（2026-09-15）**。`component-cache`、`component-message`、`component-test`、`tx-filter`、`tx-validator` 五个模块内曾存在**被 git 跟踪的过期 `.mvn/wrapper`**（`distributionUrl` 锁 Maven 3.8.2/3.8.3，会绕过本次 JDK 25 + Maven 3.9.16 的工具链锁定），已在 `metanet4j-component` 仓库提交 **`d677634`**（`build: 移除 5 个模块中过期的 Maven Wrapper（锁定 3.8.2/3.8.3）`）中全部删除，共 15 个文件。仓库内本无 `mvnw` 脚本、无任何脚本/CI/pom 引用；各模块 `.gitignore` 原有的 `.mvn/**`、`mvnw` 忽略规则保留。后续**不新增 `mvnw`、不使用 wrapper**，构建一律走 §4 的绝对路径 + 显式 `JAVA_HOME` 模板。

**验证环境（中间件，按新版本矩阵）**：

| 组件 | 目标版本 | 落点 / 现状（2026-09-15 实测） |
|---|---|---|
| Elasticsearch | **9.4.5** | 需拉 `docker.elastic.co/elasticsearch/elasticsearch:9.4.5`；本地现有 7.17.5 镜像 |
| Kafka | **4.2.1（KRaft）** | 需拉 `apache/kafka:4.2.1` 或官方二进制；**ZooKeeper 模式已不可用** |
| MongoDB | **8.0.32** | 需拉 `docker.m.daocloud.io/library/mongo:8.0`；本地现有 6.0 |
| MySQL | **8.4 LTS** | 需拉 `docker.m.daocloud.io/library/mysql:8.4`；本地现有 8.0 |
| Redis | **7.4 LTS** | 需拉 `docker.m.daocloud.io/library/redis:7.4` |
| 镜像来源风险 | — | Docker Hub 直连超时；daocloud 对部分 tag 返回 403（实测 `bitnami/kafka:2.8.1`）。**执行前必须先验 tag 可拉取性** |

**JDK 安装偏差**：sdkman 的 `25.0.4-tem` 下载源是 GitHub，实测 145 KB/s；改用 TUNA 镜像的 `OpenJDK25U-jdk_x64_linux_hotspot_25.0.4.1_1.tar.gz`（6.4 MB/s）后 `sdk install java 25.0.4.1-tem <本地目录>` 注册。产物 sha256 `dbb698396d478e7fa2b1e50f4103324b2a99b90569ee27c33f2261f9215cf41e`，与 GitHub release、Adoptium API 两处一致。

**构建命令模板**（每次构建都用这一套）：

```bash
JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem \
$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn \
  -s $HOME/.m2/metanet4j-settings.xml \
  -DskipTests clean package
```

> `mvn -v` 在不导出 `JAVA_HOME` 时显示 JDK 1.8（sdkman current 指向 `8.0.181-local`）。所有命令必须按模板带 `JAVA_HOME`，否则 `--release 25` 直接失败。
> **该模板就是版本隔离的全部手段**（D5a）：不依赖、也不修改任何全局默认值。执行期间禁止用裸 `mvn` / 裸 `java` 完成构建与验证。

**隔离自检（Phase 0 收尾、P6 收尾各跑一次）**：

```bash
ls -l ~/.sdkman/candidates/java/current   # 仍应指向 8.0.181-local（JDK 8）
ls -l ~/.sdkman/candidates/maven/current  # 仍应指向 3.9.9
git -C <每个仓库> status --porcelain      # 不应出现 .mvn/ 或 wrapper 相关新增文件
```

**Gate 0 —— 通过**（证据见 §10）：`/tmp/gate0` 探针 `--release 25` BUILD SUCCESS；Boot 4.1.1 / Cloud 2025.1.3 / jackson 3.1.5 等坐标解析成功。

---

## 5. 阶段计划

| 阶段 | 产物 | Gate |
|---|---|---|
| P0 环境 | JDK 25、Maven 3.9.16、metanet4j-settings.xml（已过）；中间件镜像拉齐 + 五个服务握手验证（已过） | 空项目解析新坐标成功；五个中间件 healthy 且逐服务握手 PASS（§11 第五轮）；**全局 java/maven `current` 未变**（§4 隔离自检） |
| P0.5 依赖预取 | 用升级后的坐标集造探针 pom 预取依赖 | `dependency:go-offline` 成功（本地仓库当前为空壳，300+ jar 从未下载） |
| P1 版本号 | 25 个 pom 的 84 处版本字面量（82 改、2 不改）+ `metanet4j.version` 属性 + 13 处 `java.version` 覆盖清零 | §6.1 脚本断言全绿 |
| P2 parent | 版本矩阵、坐标、钉死清理、插件、enforcer | `mvn -N install` 成功；effective compiler 3.15.0；enforcer 通过 |
| P3 base + sdk | javax→jakarta/jspecify、Jackson 3、日志、jspecify 依赖 | 两仓库 `package` 成功（含 test-compile）；**2026-09-16 修正**：sdk 现存 26 个既有用例错误（见 §6.4），故编译门禁用 `mvn clean package -DskipTests`，测试执行数单独记录 |
| P4 component | 22 个 pom 坐标/源码/配置迁移、Boot 4 包迁移、ES 9 迁移、Redisson 4.7.0、测试引擎 | 聚合 `package` 成功；javax/旧包名 grep 归零；§6.6 依赖漂移断言通过 |
| P5 验证 | 编译门禁 + B 档（Mongo 8.0/ES 9.4.5/Kafka 4.2.1/Redis 7.4/MySQL 8.4）+ 测试实际执行数 | 用例通过 + 冒烟通过（§7）；逐模块执行数断言 |
| P6 收尾 | 4 仓库独立提交、文档同步 | 输出提交 ID 与编译命令 |

---

## 6. 逐仓库改动清单

### 6.1 P1 版本号 0.2.0（先做，纯机械）

- 版本字面量实测：`<version>0.1.0|0.2.0</version>` 共 **84 处**，分布 **25 个 pom**。
  - 82 处是 `0.1.0`（要改）；
  - 2 处是 `0.2.0`（sdk 自身版本、parent depMgmt 的 sdk 条目，不动）。
  - 分布最多：`component-test` 11 处、`component-bap` 8 处。
- 必须改的三类：
  1. 子模块 `<parent><version>0.1.0</version>`；
  2. 模块间依赖 `<dependency><version>0.1.0</version>`；
  3. 模块自身 `<version>0.1.0</version>`。
- **关键遗漏点**：`metanet4j-parent/pom.xml` 的 `<metanet4j.version>0.1.0</metanet4j.version>`（**2026-09-16 实测在第 18 行**；第 14 行是 `<version>${metanet4j.version}</version>`，勿混淆）也要改为 `0.2.0`。它不在 `<version>0.1.0</version>` 的 grep 统计内；不改会导致 `mvn -N install` 仍安装 0.1.0，子模块声明父 0.2.0 后解析失败。
- parent depMgmt：`metanet4j-base` 0.1.0→0.2.0；`metanet4j-sdk` 保持 0.2.0。
- 删除全部 13 处 `<java.version>11</java.version>`，位置：
  - `metanet4j-parent/pom.xml:20`
  - `metanet4j-component/pom.xml:20`
  - `metanet4j-component/metanet4j-store-sql/pom.xml:19`
  - `.../metanet4j-tx-convertor/pom.xml:17`
  - `.../metanet4j-component-bap/pom.xml:18`
  - `.../metanet4j-component-message/pom.xml:17`
  - `.../metanet4j-component-test/pom.xml:15`
  - `.../metanet4j-tx-validator/pom.xml:18`
  - `.../metanet4j-tx-filter/pom.xml:17`
  - `.../mybatispuls-generator/pom.xml:17`
  - `.../metanet4j-component-cache/pom.xml:17`
  - `.../metanet4j-store-search/pom.xml:17`
  - `.../metanet4j-store-mongo/pom.xml:18`
- 本次**不引入** `${revision}` CI-friendly 版本（需配 flatten 插件，风险大于收益），列为后续优化。

**P1 Gate（在任务根目录执行）**

```bash
grep -rn '<version>0\.1\.0</version>' --include=pom.xml . | grep -v /target/ | wc -l          # = 0
grep -rn '<metanet4j.version>0\.1\.0</metanet4j.version>' --include=pom.xml . | wc -l        # = 0
grep -rln '<java.version>11</java.version>' --include=pom.xml . | grep -v /target/ | wc -l   # = 0
find . -name pom.xml -not -path '*/target/*' | wc -l                                          # = 25
```

### 6.2 P2 metanet4j-parent

**属性与 BOM**

- `spring-boot-starter-parent` → `4.1.1`；`java.version` → `25`；`maven.compiler.release` → `${java.version}`。
- `spring-cloud.version` → `2025.1.3`；**删除** `spring-cloud-alibaba-dependencies` import。
- 删除 `maven.compiler.source/target`（用 release）。

**必须删除/上调的显式钉死（D14）**：直接 depMgmt 条目优先于 import 的 BOM，以下一项不改就会降级 Boot 4。

| 现状 | 目标 | 依据 / 风险 |
|---|---|---|
| `<lombok.version>1.18.20</lombok.version>` | **删除**（跟随 Boot BOM 1.18.46） | 1.18.20 在 JDK 25 编译必崩（实测） |
| `<slf4j.version>1.7.32</slf4j.version>` + `slf4j-api`/`jul-to-slf4j`/`slf4j-jdk14` depMgmt | **删除**（跟随 Boot BOM 2.0.18）；移除 `slf4j-jdk14` | `log4j-slf4j2-impl` 要求 SLF4J 2.x；1.7.32 会覆盖 BOM |
| `<log4j.version>2.20.0</log4j.version>` + log4j-api/core/slf4j-impl depMgmt | **三条 depMgmt 条目整条删除**（版本随 Boot BOM 2.25.5）；base pom 的 `log4j-slf4j-impl` → **`log4j-slf4j2-impl`** | 随 Boot BOM；base pom 同步换 artifactId。**注意**：保留不带 `<version>` 的 depMgmt 条目会屏蔽 BOM（见下方陷阱） |
| `<hibernate-validator.version>6.1.5.Final</hibernate-validator.version>` + depMgmt | **删除**（跟随 Boot BOM 9.1.3.Final） | 6.1.5 提供的是 `javax.validation.*`，迁 jakarta 后编译失败 |
| `<jackson.version>2.13.2 </jackson.version>` + `jackson-databind/core/annotations/jdk8/jsr310/parameter-names` depMgmt | **删除 2.x core/databind/datatype/module 钉死**；注解 2.21.5 由 `jackson-2-bom` 管理；`tools.jackson.*` 由 `jackson-bom 3.1.5` 管理 | 代码迁 tools.jackson 后，旧钉死会覆盖注解版本并留下双版本 |
| `<junit.version>4.13</junit.version>` | 改 **4.13.2**（junit-vintage-engine 需要） | Boot BOM `junit 4.13.2` |
| `<lettuce.version>5.3.2.RELEASE</lettuce.version>` | **删除**（跟随 Boot BOM 7.5.2.RELEASE） | 仅编译 Redis 模块；不删会与 Spring Data Redis 4 冲突 |
| `<mysql-connector-java.version>8.0.25</mysql-connector-java.version>` + `mysql:mysql-connector-java` depMgmt | **删除属性，depMgmt 条目整条删除**（`com.mysql:mysql-connector-j` 由 Boot BOM 管 9.7.0，子模块不写版本） | 旧坐标在新版已无版本管理；留空版本条目会屏蔽 BOM（见下方陷阱） |
| `<druid.version>1.2.1</druid.version>` + `druid-spring-boot-starter` depMgmt | 改 **1.2.28**；artifactId → `druid-spring-boot-4-starter` | 新 starter 是 Boot 4 专用坐标 |
| `<mybatis-plus>3.4.2</mybatis-plus>`（重复出现两次） | 改 **3.5.17**；depMgmt artifactId → `mybatis-plus-spring-boot4-starter` | 新坐标不被 Boot BOM 管理，必须显式给版本 |
| `<mybatis-plus-generator>3.4.1</mybatis-plus-generator>` | 改 **3.5.17** | 与 generator 模块一致 |
| `<velocity-engine-core>2.0</velocity-engine-core>` | 改 **2.4.1** | generator 模块升级 |
| `<commons-lang3.version>3.10</commons-lang3.version>` | **删除**（跟随 Boot BOM 3.20.0） | 原计划已列 |
| `<jakarta.json.version>2.0.1</jakarta.json.version>` | **删除**（跟随 Boot BOM 2.1.3） | ES 9.4.5 客户端要求 `jakarta.json-api` 2.1.3；P5 用 `dependency:tree` 验证无冲突 |
| `<guava.version>30.1.1-jre</guava.version>` | 保留并注明原因 | Boot BOM 不管理；无 JDK 25 风险 |
| `<bcprov-jdk18on.version>1.71</bcprov-jdk18on.version>` | 保留并注明原因 | 本次不动，安全升级单独立项 |
| `<fastjson.version>1.2.76</fastjson.version>` | **保持 1.2.76**（原计划写 1.2.83 是笔误，已修正） | 停更；本次不动 |
| `<elasticsearch.client.version>7.17.5</elasticsearch.client.version>` | 改 **9.4.5**；**不需要**补 `org.elasticsearch.client:elasticsearch-rest-client`（走 Rest5Client，随客户端 jar 内置） | 见 D8 / D25；Boot BOM 的 `elasticsearch-client.version=9.4.5` 已管理 `co.elastic.clients:elasticsearch-java` |
| `<mapstruct.version>1.5.5.Final</mapstruct.version>` | 保留 | JDK 25 探针 BUILD SUCCESS |
| `io.springfox:springfox-swagger2` depMgmt | 删除；新增 `io.swagger.core.v3:swagger-annotations-jakarta:2.2.55` | 代码只用注解 |
| `io.jsonwebtoken:jjwt` depMgmt | 改为 `jjwt-api` / `jjwt-impl` / `jjwt-jackson` 0.13.0 | 0.9.1 依赖 javax.xml.bind |

**依赖管理陷阱（2026-09-16 实测，P3 构建暴露）**

- `dependencyManagement` 中**不带 `<version>` 的条目会屏蔽 Boot BOM 的版本管理**（就近条目优先），
  导致子模块声明该依赖时报 `'dependencies.dependency.version' ... is missing`。
- 对照实验：`parent=spring-boot-starter-parent:4.1.1` 时 `log4j-slf4j2-impl` 不写版本可解析；
  换成 `metanet4j-parent:0.2.0`（其 depMgmt 有一条不带 version 的同名条目）即报 version missing。
- 规则：**"跟随 BOM"的坐标必须整条删除 depMgmt 条目**，不能保留空版本条目；
  确需保留条目（如带 exclusion 的 `spring-boot-starter-logging`）时，必须显式写版本。

**build / 插件**

- 删除 `<plugin>maven-compiler-plugin</plugin>` 的 `<version>3.8.1</version>`，让 Boot BOM 的 3.15.0 生效；保留 `<annotationProcessorPaths>`（mapstruct / lombok / lombok-mapstruct-binding）。
- 删除 `<source>${java.version}</source>`、`<target>${java.version}</target>`，改为 `<release>${java.version}</release>`（或依赖 `maven.compiler.release` 属性）。
- `maven-source-plugin`（parent 3.3.0、base 3.0.1）保留；统一到 3.3.0 可选。
- 新增 `maven-enforcer-plugin`（版本由 Boot BOM 管理 3.6.3）：
  - `requireJavaVersion [25,)`；
  - `bannedDependencies` 拦 `javax.*`，白名单 `<exclude>javax.cache:cache-api</exclude>`（redisson 传递）；如选择在 component-cache 排除该依赖，则白名单可去掉。

**P2 Gate**：`mvn -N install` 成功；`mvn help:effective-pom` 中 compiler 3.15.0；`mvn enforcer:enforce` 通过。

### 6.3 P3 metanet4j-base

- `pom.xml` 的 `log4j-slf4j-impl` → `log4j-slf4j2-impl`（scope runtime）。
- pom 的 Jackson 依赖切到 tools.jackson（**只保留一条**，版本由 Boot BOM 管理）：
  - `tools.jackson.core:jackson-databind`
- **修正（2026-09-16 实测）**：Jackson 3 已把 jdk8 / jsr310 / parameter-names 三个模块**并入 databind**——
  `tools.jackson.datatype:jackson-datatype-jsr310`、`...-jdk8`、`tools.jackson.module:jackson-module-parameter-names`
  在 Central 上 404，且在三方 BOM `tools.jackson:jackson-bom:3.1.5` 中被 XML 注释掉（未管理）；
  `jackson-databind-3.1.5.jar` 内置 `tools/jackson/databind/ext/javatime/**`。
  故 base（以及 P4 的 component-file）**不要**再引入这三个坐标，否则 `version is missing`。
- `model/AIP.java`、`model/BPP.java`：`javax.validation.constraints.*` → `jakarta.validation.constraints.*`。
- `util/JacksonUtil.java` 重写：
  - 导入改 `tools.jackson.databind.json.JsonMapper`、`tools.jackson.core.type.TypeReference`、`tools.jackson.databind.JavaType`、`tools.jackson.core.JacksonException`；注解 `JsonInclude` 保持 `com.fasterxml.jackson.annotation`。
  - `new ObjectMapper()` + `configure(...)` 改为 `JsonMapper.builder().enable(JsonReadFeature.ALLOW_UNESCAPED_CONTROL_CHARS, JsonWriteFeature.ESCAPE_NON_ASCII).build()`；`setSerializationInclusion` 用 builder 的 inclusion 配置。
  - `JsonProcessingException`（checked）→ `JacksonException`/`tools.jackson.core.JacksonException`（unchecked）。
  - **删除** `catch (IOException e)`（第 67、77 行）与 `throws IOException`；`readValue` 失败改捕获 `JacksonException`。
- hibernate-validator 版本由 parent 9.1.3 提供，base 不需要新增 depMgmt。

### 6.4 P3 metanet4j-sdk

- `javax.annotation.*` 12 处 → `org.jspecify.annotations.*`：
  - 11 处 `Nullable` → `org.jspecify.annotations.Nullable`；
  - 1 处 `Nonnull`（`BsocialDataLockBuilder.java`）→ `org.jspecify.annotations.NonNull`（注意大写 N）。
  - 文件清单：`TransactionExtend`、`Ecies`、`BsocialDataLockBuilder`（Nonnull+Nullable）、`EcKeyLiteExtend`、`bap/BapBase`、`bap/SpecifyBapBase`、`script/ScriptExtend`、`utils/TxHelperExtend`、`input/TransactionInputEnhance`、`output/TransactionOutputEnhance`、`PrivateKey`。
- `bap/MasterKeyBapBase.java`：`javax.validation.constraints.NotNull` → `jakarta.validation.constraints.NotNull`。
- `javax.crypto.*`（`crypto/AesCBCUtil.java`）**不动**。
- 新增 `org.jspecify:jspecify` 依赖（parent depMgmt 不写版本，由 Boot BOM 1.0.1 管理；sdk pom 加 compile 依赖）。
- `src/test/java/.../TestData.java` 的 `com.fasterxml.jackson.core.type.TypeReference` → `tools.jackson.core.type.TypeReference`（通过 base 传递 tools.jackson）。
- 版本号保持 0.2.0；`<parent><version>` 改 0.2.0。

**既有缺陷（2026-09-16 P3 实测发现，不属本次迁移）**

- 现象：`cd metanet4j-sdk && mvn clean install` → `BitcoinschemaTransactionTest` 13 error + `OrdTransactionTest` 13 error，
  全部同一个 NPE：
  ```
  java.lang.NullPointerException: Cannot invoke "io.bitcoinsv.bitcoinjsv.crypto.DeterministicKey.getPrivKey()"
    because "this.rootPrivateKey" is null
      at BapBase.getRootPrivateKey(BapBase.java:319)
      at BapBase.getRootAddress(BapBase.java:351)
      at MasterKeyBapBase.<init>(MasterKeyBapBase.java:35)
      at BapBase.<init>(BapBase.java:49)
      ...
      at TransactionContextTest.before(TransactionContextTest.java:45)
  ```
  报告：`metanet4j-sdk/target/surefire-reports/com.metanet4j.sdk.transcation.{BitcoinschemaTransactionTest,OrdTransactionTest}.txt`
- 根因（代码级）：`BapBase extends MasterKeyBapBase`；父类构造器第 35 行调用 `getRootAddress()`，
  该方法被 `BapBase` 覆写（351 行）并读取 `BapBase.rootPrivateKey`，而该字段要到 `super()` 返回后才在 51 行赋值
  ——典型的"构造器调用可覆写方法"缺陷。
- 影响面：所有走 `BapBase.fromOnlyMasterPrivateKey(...)` / `fromRootChildNumberList(...)` 的构造路径都会 NPE（不只测试）。
- 处置：**P3 不修**（P3 范围是依赖/包名迁移，改构造顺序属行为变更），归入 `boot4-tests-jupiter` 或单独立项，需用户决策。
- 与迁移无关的证据：P3 对 `BapBase.java`、`MasterKeyBapBase.java`、`TransactionContextTest.java` 的改动只有 import 行（javax→jspecify/jakarta），
  `git -C metanet4j-sdk diff` 可核。

---

### 6.5 P4 metanet4j-component（21 子模块 + 根 pom = 22 个 pom）

**坐标（不改会直接报 `version is missing` 或编译失败）**

| 旧 | 新 | 位置 |
|---|---|---|
| `spring-boot-starter-aop` | `spring-boot-starter-aspectj`（4.1.1 上 404） | `metanet4j-component-common/pom.xml:41` |
| `com.mysql:mysql-connector-java` | `com.mysql:mysql-connector-j` | `metanet4j-store-sql`、`mybatispuls-generator` |
| `com.baomidou:mybatis-plus-boot-starter` | `mybatis-plus-spring-boot4-starter`（版本 3.5.17 由 parent 管理） | `metanet4j-store-sql/pom.xml:32` |
| `com.alibaba:druid-spring-boot-starter` | `druid-spring-boot-4-starter`（版本 1.2.28 由 parent 管理） | `metanet4j-store-sql/pom.xml:43` |
| `io.springfox:springfox-swagger2` | `io.swagger.core.v3:swagger-annotations-jakarta` | `metanet4j-component-model/pom.xml` |
| `io.jsonwebtoken:jjwt` | `jjwt-api`（compile）+ `jjwt-impl`/`jjwt-jackson`（runtime）0.13.0 | `metanet4j-api-common` 等使用处 |

**MyBatis-Plus 3.5.17 的类搬迁（2026-09-16 实测，P4 构建暴露）**

- `IService` / `ServiceImpl` 在 3.5.17 已从 `com.baomidou.mybatisplus.extension.service(.impl)`
  移到 **`com.baomidou.mybatisplus.spring.service(.impl)`**（证据：`mybatis-plus-spring-3.5.17.jar` 内含
  `com/baomidou/mybatisplus/spring/service/IService.class`；`extension` 包下已无该类）。
- 影响：`metanet4j-store-sql` 的 **11 个文件**需同步改 import（原计划未覆盖）。
- 兼容性已核实：新 `ServiceImpl` 继承 `spring.repository.CrudRepository`（含 `protected M baseMapper`），
  `IService` 继承 `extension.repository.IRepository`（save/getById/updateById/removeById/listByIds/getOne/exists/count 等仍在），
  故只改 import 即可，方法调用无需调整（store-sql 的 service 均为薄壳，用 `baseMapper` 直连 mapper）。
- **自动填充 API 变更（同批实测）**：`MetaObjectHandler.setInsertFieldValByName(...)` / `setUpdateFieldValByName(...)`
  在 3.5.17 已删除，需改用 `strictInsertFill(metaObject, field, Class, value)` / `strictUpdateFill(...)`
  （语义差异：strict 填充只在字段为 null 且实体标注 `@TableField(fill=...)` 时生效，不再无条件覆盖）。
  影响 `store-sql/handler/MetanetObjectHandler.java`。

**javax → jakarta / jspecify（component 16 个文件）**

| 类别 | 文件 |
|---|---|
| validation（9） | `component-file`：`LocalFileClientConfig`、`FtpFileClientConfig`、`S3FileClientConfig`、`SftpFileClientConfig`、`DBFileClientConfig`、`validation/ValidationUtils`；`api-common`：`GlobalExceptionTranslator`、`utils/ValidateUtils`；`store-mongo`：`bsocail/po/BsocialBase` |
| `javax.annotation.Resource/PostConstruct`（5） | `component-bap/handler/MysqlStoreBapDtoHandler`、`component-bap/service/MysqlBapService`、`component-message/consumer/BitcoinSchemaConsumer`、`component-cache/RedisUtils`、`api-common/security/JwtTokenProvider` |
| `javax.servlet.http.HttpServletRequest`（2） | `api-common/aspect/GlobalApiLogAspect`、`api-common/security/JwtTokenProvider` |
| **测试文件（1，必须改；`-DskipTests` 仍 testCompile）** | `component-file/src/test/.../core/client/s3/S3FileClientTest.java` |

> `JwtTokenProvider` 同时含 `Resource/PostConstruct` 与 `HttpServletRequest` 导入，只计 1 个文件；上表各行之和会重复 1 次。

> 计数说明：全仓 `^import javax.` 共 31 个文件；base 2 + sdk 13 + component 16。sdk 中 `javax.crypto/AesCBCUtil` 不动，故迁移总数 = 30（含上述测试文件）。

**Boot 4 包迁移（3 个文件，见 D13）**

- `component-test/src/main/.../Metanet4jComponentTestApplication.java`：Druid 包名（boot4.autoconfigure）+ `DataSourceAutoConfiguration`/`DataSourceTransactionManagerAutoConfiguration` 迁 `org.springframework.boot.jdbc.autoconfigure`。**2026-09-16 修正**：`HibernateJpaAutoConfiguration` 不迁包也不排除——`spring-boot-hibernate` 不在该模块类路径上（无 JPA 依赖），保留 exclude 会导致编译期找不到类；故直接删除该 import 与 exclude 项。
- `connect-planaria/.../fegin/DefaultFeginClient.java`：删除未使用的 `HttpMessageConverters` import。
- `component-cache/.../RedissonAutoConfiguration.java`：`RedisAutoConfiguration`→`DataRedisAutoConfiguration`、`RedisProperties`→`DataRedisProperties`（`getCluster`/`getTimeout` 方法名已在 Boot 4 中确认存在）；**同时把 redisson 依赖升到 4.7.0**（见下"Redisson 4.7.0"）。

**Redisson 4.7.0（component-cache）**

- `component-cache/pom.xml`：`redisson-spring-boot-starter` 3.17.0 → **4.7.0**；Boot 4.1 下 starter 自带 `redisson-spring-data-41`，**不要**加 exclusion（加了反而错配）。
- 删掉 `<=3.52` 时代的 `redisson-spring-data-2x` 残留依赖（若有）。
- 全仓 grep `RedissonAutoConfigurationV2`（YAML / properties / 注解三种写法都要查），存在则改 `RedissonAutoConfigurationV4`——该名字在 Boot 4 下**不报错也不生效**，是官方点名的静默陷阱。
- 排除 redisson 传递的 `javax.cache:cache-api`，否则 enforcer 的 `bannedDependencies` 会拦（见 D21）。
- **Spring Cache 集成拆包（2026-09-16 实测）**：4.7.0 起 `org.redisson.spring.cache.*`
  （`CacheConfig` / `RedissonSpringCacheManager`）已从主 jar 拆到独立坐标
  **`org.redisson:redisson-spring-cache:4.7.0`**；`component-cache/pom.xml` 需补该依赖（原计划未覆盖）。
- **Micrometer 2.x 移除 `io.micrometer.core.instrument.util.StringUtils`**：`RedisUtils` 改用已有的
  `cn.hutool.core.util.StrUtil.isBlank(...)`（原计划未覆盖）。
- 保留模块内自研 `RedissonAutoConfiguration` 的显式包路径调整；`RedissonProperties` 的 `spring.redis.redisson.*` 前缀未变，不需要改配置。

**Elasticsearch 9.4.5（store-search）**

- `store-search/pom.xml`、parent depMgmt：`elasticsearch-java` 7.17.5 → **9.4.5**。**不引入** legacy `org.elasticsearch.client:elasticsearch-rest-client`（走 Rest5Client，随客户端内置）。
- `store-search/.../EsConfig.java`：改用官方推荐写法（9.x 起新增的高层入口 + Jackson 3 mapper），去掉 `org.apache.http.HttpHost` / `org.elasticsearch.client.RestClient` 两个 import：

```java
ElasticsearchClient client = ElasticsearchClient.of(b -> b
        .host("http://localhost:9200")
        .jsonMapper(new Jackson3JsonpMapper()));
```

  - `ElasticsearchClient.of(...)` 由 `ElasticsearchTransportConfig` 构建，**默认 transport 即 Rest5Client**；如需 legacy，用 `useLegacyTransport(true)` 显式退回（本项目不退回）。
  - 已核实的签名：`ElasticsearchClient.of(Function<ElasticsearchTransportConfig.Builder, Builder>)`；`ElasticsearchTransportConfig.Builder` 提供 `host(String|URI)`、`hosts(List<URI>)`、`usernameAndPassword`、`apiKey`、`sslContext`、`jsonMapper(JsonpMapper)`、`useCompression`、`transportFactory(...)`、`useLegacyTransport(boolean)`；备选显式构造 `new Rest5ClientTransport(Rest5Client, JsonpMapper)` 亦可。
- `Jackson3JsonpMapper` 是 9.4.5 jar 内置类（`co.elastic.clients.json.jackson.Jackson3JsonpMapper`），字节码实测引用 `tools.jackson.databind.json.JsonMapper`，与全仓 Jackson 3 一致。
- 业务查询 API **不需要改**：代码实测未触及 ES 9 任何破坏性 API（`aggregations`/`Aggregation`/`valueBody`/`matchedQueries`/`indicesBoost`/`dynamicTemplates`/`msearch`/`esql`/`DenseVector` 均 0 处），只用到 `indices/search/index/get/delete/cluster/bool/match/term/sort/size/from`。
- `EsTest`（component-test）同步改 mapper 与构造方式；ES 服务端地址仍是 `localhost:9200`。

**Jackson 3（14 个文件）**

| 处理 | 文件 |
|---|---|
| 注解不变，仅确认 | `component-file/.../FileClientConfig`、`S3FileClientConfig`（`@JsonTypeInfo`/`@JsonIgnore`）；`api-common/base/R`、`component-model/.../BaseResult`（`@JsonFormat`）；`component-model/.../domain/bap/Identity`；`sdk/.../Txo`（`@JsonProperty`） |
| 迁 `tools.jackson.*` 导入 | `base/util/JacksonUtil`；`component-common/utils/JacksonBeanUtils`；`component-bap/service/BapSearchService`；`store-search/repository/BapIdentityRepository`（未使用 import 可直接删）；测试 `BapBaseTest`、`BitcoinschemaTransactionTest`、`EsTest`、`sdk/src/test/TestData` |
| pom 坐标 | `base`、`component-file` 的 Jackson 依赖只保留 `tools.jackson.core:jackson-databind`（版本由 Boot BOM 管理；datatype/module 三坐标在 Jackson 3 不存在，见 §6.3 修正）；**`store-search` 不删 Jackson 2**——ES 9.4.5 客户端 pom 同时以 runtime 引入 Jackson 2.22.0 与 Jackson 3.1.0，其 `JacksonJsonpMapper` 仍引用 Jackson 2，删了会在运行期挂 |

**Swagger 注解（3 个文件 + 1 个 pom）**

- `api-common/base/R.java`、`component-model/.../api/BaseResult.java`：`@ApiModel(description=...)` → `@Schema(description=...)`。
- `component-model/.../api/ListResult.java`：`@ApiModel(value="列表结果")` → `@Schema(name="列表结果")`；`@ApiModelProperty(value=...)` → `@Schema(description=...)`。
- `component-model/pom.xml`：`io.springfox:springfox-swagger2` → `io.swagger.core.v3:swagger-annotations-jakarta`（版本由 parent 管理）。

**JJWT（0.13 API）**

- `api-common/security/JwtTokenProvider` 重写：`Jwts.parser().verifyWith(key)`、`Jwts.SIG.HS256`、`Keys.hmacShaKeyFor(bytes)`；不再使用 `SignatureAlgorithm` 与 `javax.xml.bind`。
- 依赖改 `jjwt-api`（compile）、`jjwt-impl` + `jjwt-jackson`（runtime）。

**配置**

- `component-test/src/main/resources/application.yml`：`spring.redis.*` → `spring.data.redis.*`（Boot 4 下 Boot 2 的 `spring.redis.*` 已移除；B 档起 Redis 7.4 容器做 `component-cache` 装配烟测）。
- Mongo URI 补 `?authSource=admin`（MongoDB 8.0 官方镜像用 `MONGO_INITDB_ROOT_USERNAME` 建的是 admin 库 root，见 §7.3）。
- `spring.kafka.default.*` 由 `DefaultKafkaProperties`（prefix `spring.kafka.default`，继承自定义 `KafkaProperties`）绑定；P5 启动时确认绑定仍成立（`KafkaJaasLoginModuleInitializer` 等类在 Spring Kafka 4.1.1 中仍存在）；broker 升 4.2.1 后 `bootstrap-servers` 仍是 `localhost:9092`，但 broker 必须是 KRaft 模式。
- 主类 exclude 项按 D13 更新；Druid 配置在 DataSourceAutoConfiguration/Druid 被 exclude 后不再生效，主链路 MySQL 仍不需要（MySQL 8.4 仅在 B 档做连接器往返验证）。

**每个子 pom**

- 删除 `<java.version>11</java.version>` 覆盖（12 个子模块，见 §6.1 清单）。
- 版本字面量改 0.2.0。

**generator 模块（`mybatispuls-generator`）**

- `mybatis-plus-generator` 3.3.1 → 3.5.17；`velocity-engine-core` 2.0 → 2.4.1；parent 版本 0.1.0→0.2.0。
- `MybatisPulsCodeGenerator.java` 整体改用 `FastAutoGenerator` API：
  - `FileOutConfig` 在 3.5.17 已删除；
  - `InjectionConfig` 已移到 `com.baomidou.mybatisplus.generator.config` 包；自定义文件输出改用 `injectionConfig(...).customFile(...)` 形式；
  - 不再使用旧 `AutoGenerator` + `GlobalConfig/DataSourceConfig/PackageConfig/StrategyConfig` 的 setter 组合，改为 `FastAutoGenerator.create(url,user,pwd).globalConfig(...).packageConfig(...).strategyConfig(...).injectionConfig(...).templateEngine(new VelocityTemplateEngine()).execute()`。

**Boot 4 / Spring Kafka 4 的 API 变更（2026-09-16 实测，P4 构建暴露）**

- `PropertyMapper.get().alwaysApplyingWhenNonNull()` 已删除（`alwaysApplyingWhenNonNull()` 在 Boot 4 不存在）。
  Boot 4 的 `Source.adapt(...)` 已内建非空过滤（源码：`value != null && predicate.test(value)`），
  故 `PropertyMapper.get()` 即为原语义；影响 `component-message/config/KafkaProperties.java` 6 处。
- Spring Kafka 4 的 `KafkaTemplate.send(...)` 返回 `CompletableFuture`（不再返回已移除的 `ListenableFuture`），
  `addCallback(success, failure)` 需改为 `whenComplete((result, ex) -> ...)`；
  影响 `component-message/producer/AbstractMessageProducer.java`。

**测试基建（D17/D18，P4 内完成）**

- `component-test/pom.xml` 增加 `junit-vintage-engine`（Boot BOM/junit-bom 管理 6.0.3）+ junit 4.13.2。
- 基类 `Metanet4jComponentTestApplicationTests`：去掉 `@RunWith(SpringRunner.class)` 与 JUnit 4 import，保持 Jupiter `@Test` + `@SpringBootTest`。
- 12 个继承基类的 JUnit 4 测试类各自补 `@RunWith(SpringRunner.class)` + import（保持 `@Autowired` 生效）。
- 删除悬空依赖 `com.metanet4j.bootstrap:metanet4j-bootstrap:0.1.0`（代码无引用）。
- `component-file/pom.xml`：删除 `mockito-inline:4.11.0` 与 `mockito-inline.version` 属性，改 `org.mockito:mockito-core`（版本由 Boot BOM 5.23.0 管理）。
- `MessageProducerTest` 无断言，P5 用发送回调日志/状态判断；建议补回调断言（可选，但要能证明确实执行）。

### 6.6 权威清单与全局 grep 门禁

实施时以下列命令输出为准，不接受口头计数：

```bash
# 规模
find . -name pom.xml -not -path '*/target/*' | wc -l                                      # 25
# P1
grep -rn '<version>0\.1\.0</version>' --include=pom.xml . | grep -v /target/ | wc -l       # 0
grep -rn '<metanet4j.version>0\.1\.0</metanet4j.version>' --include=pom.xml . | wc -l      # 0
grep -rln '<java.version>11</java.version>' --include=pom.xml . | grep -v /target/ | wc -l # 0
# javax：只允许 AesCBCUtil
grep -rn '^import javax\.' --include='*.java' . | grep -v /target/
# Boot 4 旧包名：应为 0
grep -rn -E 'org\.springframework\.boot\.autoconfigure\.(jdbc|orm\.jpa|http\.HttpMessageConverters|data\.redis)' --include='*.java' . | grep -v /target/
# Jackson 旧 core/databind：应为 0（annotation 可保留；ES 9.4.5 客户端自带 Jackson 2 属 pom/runtime 依赖，不在本 grep 范围）
grep -rn -E 'com\.fasterxml\.jackson\.(core|databind|datatype|module)' --include='*.java' . | grep -v /target/
# ES 9 迁移与 Redisson 版本（新增门禁，见 D8/D19）
mvn -s ~/.m2/metanet4j-settings.xml -pl metanet4j-component/metanet4j-store-search dependency:tree \
  -Dincludes=co.elastic.clients,org.elasticsearch.client    # 断言 elasticsearch-java=9.4.5；不应出现 legacy rest-client
mvn -s ~/.m2/metanet4j-settings.xml -pl metanet4j-component/metanet4j-component-cache dependency:tree \
  -Dincludes=org.redisson                                    # 断言 redisson-spring-data-41 存在且无 redisson-spring-data-2x
grep -rn 'RedissonAutoConfigurationV2' . --include='*.yml' --include='*.yaml' --include='*.properties' --include='*.java' | grep -v /target/   # 应为 0
grep -rn -E 'org\.apache\.http\.HttpHost|org\.elasticsearch\.client\.RestClient|RestClientTransport' --include='*.java' . | grep -v /target/  # 应为 0（已走 Rest5Client）
```

---

## 7. 验证方案

### 7.1 编译门禁（每仓库）

```bash
mvn -s ~/.m2/metanet4j-settings.xml -DskipTests clean package
```

安装顺序：`parent`（`-N install`）→ `base` → `sdk` → `component`（多模块聚合）。
> `-DskipTests` 仍会编译测试代码；P4 的 javax/Jackson 测试文件必须一并迁移，否则 testCompile 失败。
> base/sdk 的 `<parent>` 未写 `relativePath`，父 POM 必须先 install 到本地仓库。

### 7.2 冲突体检

- `mvn dependency:tree`：确认无 `javax.*` 残留（白名单 `javax.cache:cache-api` 除外）；Jackson 2/3 并存符合预期（ES 9.4.5 与 jjwt-jackson 带 Jackson 2，均为 runtime）。
- **依赖漂移断言（新增）**：`elasticsearch-java` = 9.4.5 且**不出现** legacy `org.elasticsearch.client:elasticsearch-rest-client`（走 Rest5Client）；`redisson-spring-data-41` 存在、无 `redisson-spring-data-2x`；`kafka-clients` = 4.2.1；`mongodb-driver-sync` = 5.8.1；`mysql-connector-j` = 9.7.0。
- `mvn enforcer:enforce`：Java 版本 + banned javax。
- `mvn dependency:analyze`：确认坐标替换后无遗漏。
- `mvn help:effective-pom`：compiler 3.15.0；不再有被覆盖的旧版本。

### 7.3 B 档运行验证（docker）

**服务现状（2026-09-15 核查）**：

| 服务 | 目标版本 | 现状（2026-09-15 实测） |
|---|---|---|
| MongoDB | **8.0.32** | ✅ 已拉取 `docker.m.daocloud.io/library/mongo:8.0`（1.27GB，24s）；27017 空闲 |
| Elasticsearch | **9.4.5** | ✅ 已拉取 `docker.elastic.co/elasticsearch/elasticsearch:9.4.5`（2.51GB，103s）；9200 空闲 |
| Kafka | **4.2.1（KRaft）** | ✅ 已拉取 `docker.m.daocloud.io/apache/kafka:4.2.1`；9092 空闲；**注意：`apache/kafka:4.2.1` 裸 tag（Docker Hub）不可达，必须写 daocloud 全限定名** |
| Redis | **7.4 LTS** | ✅ 已拉取 `docker.m.daocloud.io/library/redis:7.4`（170MB）；6379 空闲 |
| MySQL | **8.4 LTS** | ✅ 已拉取 `docker.m.daocloud.io/library/mysql:8.4`（1.12GB，9s）；3306 空闲 |
| zookeeper:3.9 | 保留（**不再服务 Kafka**） | 容器 `e2e-zookeeper` 在跑，位于 `infra_default`；Kafka 4.2.1 走 KRaft，该容器现仅供 rocketmq 使用 |
| compose | ✅ 已迁到共享设施 | **`ownword/infra/docker-compose.yml`**（compose 项目 `ownword-infra`，容器 `infra-mongo` / `infra-es` / `infra-kafka` / `infra-redis` / `infra-mysql`）；五个服务均含 healthcheck 且 `restart: unless-stopped`；任务目录下的临时副本已删除（DRY） |
| Mongo authSource | ✅ 已定方案 | 实测原 URI 认证失败、`?authSource=admin` 成功 → P4 采用方案 A（改 `application.yml`） |

**共享中间件（2026-09-15 起为长期基础设施）**：用户确认"后续所有研发任务都要用到"，故不再作为本任务的临时验证环境，而是抽到 **`ownword/infra/`** 作为跨任务共享设施。该目录含 `docker-compose.yml`、`README-ownword-infra-20260915-1720.md`（连接信息与约束的唯一事实来源）、`up.sh` / `down.sh` / `status.sh`。

- 镜像**钉到补丁号**：`mongo:8.0.32`、`mysql:8.4.11`、`redis:7.4.11`、`elasticsearch:9.4.5`、`apache/kafka:4.2.1`（避免浮动标签在有数据卷时升级失败）。
- 五个服务**全部挂命名数据卷**（`ownword-infra_{mongo,es,kafka,redis,mysql}-data`），`./down.sh` 保留数据、`./down.sh -v` 才彻底重置。
- `restart: unless-stopped` + docker 开机自启 → 机器重启后自动恢复；容器名不带任务名前缀。

**本任务如何使用它**：

```bash
cd /home/haodev/ownword/infra && ./up.sh      # 启动并等待全部 healthy
./status.sh                                    # 查看状态/端口/版本
./down.sh                                      # 停止（保留数据）
```

**连接信息（详见 `ownword/infra/README-ownword-infra-20260915-1720.md`）**：

| 服务 | 连接串 |
|---|---|
| MongoDB | `mongodb://bschema:bschema123@localhost:27017/bschema?authSource=admin`（**`authSource` 不可省**） |
| Elasticsearch | `http://localhost:9200`（无认证） |
| Kafka | `bootstrap.servers=localhost:9092`（KRaft，无 ZooKeeper） |
| Redis | `redis://localhost:6379`（无密码） |
| MySQL | `jdbc:mysql://localhost:3306/bap_user?...&allowPublicKeyRetrieval=true`，`root/root123` |

执行步骤：

1. 启动前确认端口空闲：27017 / 9200 / 9092 / 6379 / 3306；`./up.sh` 会等到五个服务全部 healthy（实测约 70s）。
2. Mongo 认证：**已实测定为方案 A** —— 应用 yml URI 必须追加 `?authSource=admin`（实测原 URI `Authentication failed`，加 `authSource` 后成功；root 用户在 admin 库）。方案 B（进容器在 `bschema` 库建同名用户）本次不采用。
3. Kafka（4.2.1 KRaft）`CLUSTER_ID` 固定为 `ownword-infra-kraft-01`；数据卷复用时不可改，否则 KRaft 拒绝启动。如关闭自动建 topic，需手动建 `parse_block_topic`。
4. Redis：无需认证，与应用 `spring.data.redis.host/port` 对齐。
5. MySQL：JDBC URL 必须带 `allowPublicKeyRetrieval=true`（8.4 默认 `caching_sha2_password`）。
6. 本任务验证结束后**不要 `down -v`**（那会清掉共享数据）；如确需重置，先确认没有其他任务在用。

**拉取来源与风险（2026-09-15 实测结论）**：Docker Hub 经 daemon 直连**不可达**（`registry-1.docker.io` dial timeout，多次复现），因此**所有 Docker Hub 来源的镜像都必须走 `docker.m.daocloud.io/` 全限定名**；`docker.elastic.co` 可直连。`docker.m.daocloud.io` 是 DaoCloud 提供的 **Docker Hub 公共镜像加速站（pull-through cache）**，非 Docker 官方、也不是私有仓库——它只加速公共镜像下载，与 Maven 私服无关（Maven 侧仍直连 Central）。用户 2026-09-15 确认使用该加速站。daocloud 对**极旧 tag** 会返回 403（实测 `bitnami/kafka:2.8.1`），但本项目五个目标 tag 均已实测拉取成功。备用方案（若将来 tag 失效或加速站不可用）：Apache 官方二进制 `https://archive.apache.org/dist/kafka/<ver>/kafka_2.13-<ver>.tgz` 可达（4.2.1 与 2.8.1 均实测 200）。**若后续接入公司内部 registry/镜像代理，应整体替换本节的 daocloud 地址**；生产环境使用第三方镜像源时建议核对 digest。磁盘余量 741G，足够。

覆盖用例（`metanet4j-component-test`，`*Test*.java` 实测 25 个，含重名 `CommonTest` ×2 与非测试类 `LocalTestUtxoProvider`）：

| 依赖 | 用例 | 说明 |
|---|---|---|
| **MongoDB 8.0**（上下文刷新阶段建索引，必需） | `BapMongodbTest`、`BsocialReplyMongodbTest`、`BsocialMongodbTest`、`DataTest` | 12 个类继承 `@SpringBootTest` 基类；`auto-index-creation: true` |
| **ES 9.4.5** | `EsTest`、`BapSearchServiceTest` | 静态 client 硬编码 `localhost:9200`；`EsConfig` 已迁 `Jackson3JsonpMapper` |
| **Kafka 4.2.1（KRaft）** | `MessageProducerTest` | 无断言；验证 `DefaultKafkaProperties.buildProducerProperties()` 与发送路径（建议补回调断言） |
| **Redis 7.4**（`component-cache` 装配烟测，独立小用例） | 新增或复用 cache 相关用例 | 验证 Redisson 4.7.0 的 `redissonConnectionFactory` 装配 + 一次读写；覆盖 D19 的 `-41` 模块路径 |
| **MySQL 8.4**（连接器往返，独立小用例） | 新增或复用 store-sql 用例 | 验证 Connector/J 9.7.0 连接 + 建表/读写/删表；主链路不依赖 MySQL |
| 无需外部服务 | `StateCalculatorTest`、`ComplteTxFactoryTest`、convertor/resolver 等 | 纯逻辑 |

**冒烟重点**：上下文启动、JWT 登录、Jackson 3 序列化输出、ES 查询、Kafka 发送。

### 7.4 测试引擎与执行门禁

- 引擎：JUnit Platform（Jupiter 6.0.3 + vintage 6.0.3）；JUnit 4.13.2。
- **2026-09-16 实测修正**（P3 构建）：纯 JUnit 4 模块（base、sdk）**不需要 vintage 也会真实执行**——
  surefire 3.5.6 只要在测试类路径上发现 `junit:junit` 4.x 就自动选 `surefire-junit4` provider
  （日志：`Using auto detected provider org.apache.maven.surefire.junit4.JUnit4Provider`）；
  实测 base 2/2 通过、sdk 4 通过（另有 26 个既有错误，见 §6.4）。
  因此复评 P0-A"这些模块的 JUnit 4 用例会被静默跳过"的前提**不成立**。
  但 **vintage 仍是必需的**：只要模块里同时存在 Jupiter 用例（如 `component-test`、`component-file`），
  该模块就走 JUnit Platform，其中的 JUnit 4 用例必须有 vintage 才能被平台执行（否则同样静默丢失）。
  D17 的"引擎装到每个含 JUnit 4 用例的模块"作为统一口径保留（成本低、避免混用陷阱）。
- 验收：`mvn -pl metanet4j-component-test -am test` 后，**逐模块**断言 surefire 实际执行数：base > 0、sdk > 0、component-test > 0、connect-planaria > 0；component-test 内至少覆盖一个 Mongo 8.0 用例、一个 ES 9.4.5 用例、一个 Kafka 4.2.1 用例、一个纯逻辑用例；Redis/MySQL 各一个独立小用例。
- 基类用例必须真的被执行：断言 surefire 报告里出现 `contextLoads`（`grep -r contextLoads */target/surefire-reports/*.txt`），否则"上下文启动"冒烟等于没跑（见复评 P0-B）。
- 若选择把测试全迁 Jupiter（替代 vintage 方案），需单独评估工作量后再改本计划；默认按 D17 执行。
- 记录测试基建遗留：`MessageProducerTest` 无断言（建议补）；`CommonTest` 重名文件、`LocalTestUtxoProvider` 非测试类，命名不规范不影响本次门禁。

---

## 8. Git 工作流

> 以下步骤在**执行阶段**（待批准）进行。本次曾试跑并已全部回退，仓库现处于 `feature/java21`（与 `dev` 同点，见 §11）。

- 任务根目录 `_task/backend-worktree/boot4-java25-upgrade/`，4 个仓库 worktree 保持相对结构（复用现有 worktree，从 `feature/java21` 切到新分支）。
- 分支：`feat/boot4-java25-metanet4j-parent`、`-base`、`-sdk`、`-component`。
- 基线：`dev`（4 仓库均干净；worktree 当前 `feature/java21` 与 `dev` 零差异）。
- 提交：每仓库独立提交，遵循 Conventional Commits；破坏性变更用 `!` 或 `BREAKING CHANGE:`。
- 回滚：开工前 4 仓库 dev 打 tag `pre-boot4-java25`。
- 产出报告：受影响仓库、每仓库编译命令、每仓库提交 ID。

---

## 9. 风险与遗留项

| 项 | 说明 | 处置 |
|---|---|---|
| Spring Cloud Alibaba 移除 | 将来若需 Nacos/Sentinel 需重新引入 BOM | 记录；现无用例依赖 |
| ES 客户端与服务端同步升 9.4.5 | 跨两个大版本（7.17.5 → 9.4.5），但代码未触及任何破坏性 API（实测 0 处）；风险集中在客户端装配（Jackson 3 mapper + rest-client 显式依赖） | 按 D8/D25 迁移；P5 用 `EsTest` 实连 9.4.5 验证 |
| Cloud 2025.1.3 按 Boot 4.0.8 构建 | 其 BOM 的 `<spring-boot.version>` 是 4.0.8，与目标 4.1.1 有一处小落差；兼容校验接受 `4.1.x` | 记录；P3/P4 编译与 P5 启动时观察 `Spring Cloud CompatibilityVerifier` 是否告警 |
| Kafka 4.2.1 必须 KRaft | Kafka 4.x 移除了 ZooKeeper 模式；生产集群需已迁移到 KRaft，否则应用升客户端也接不上 | 记录；生产侧确认集群模式，B 档按 KRaft 起 |
| Kafka 客户端与服务端同版 4.2.1 | 官方矩阵：3.x/4.x broker 对 4.x 客户端 ✅ 全兼容 | 无遗留风险（原 2.8.1 的"部分兼容"问题随服务端升级消失） |
| Redisson 4.7.0 为本次新增改动 | 3.17.0 与 Spring Data Redis 4.1 硬冲突，必须升；升级后 Redis 从"仅编译"进入"运行验证" | 按 D19 执行；B 档起 Redis 7.4 做装配烟测 |
| `RedissonAutoConfigurationV2` 静默失效 | Boot 4 下该名字不报错也不生效，配置里写了等于没写 | 全仓 grep 改 `V4`（§6.6 门禁） |
| fastjson 1.2.76 停更 | 全仓仍在使用 | 本次不动，单独立项迁移 |
| 私服缺失 | `com.metanet4j` 产物需本地 install 提供 | 构建顺序已保证 |
| `bitcoinj-sv` 未验证 | Java 25 下运行表现未知 | 出现失败时单独立项 |
| springdoc UI 未引入 | 本次只引 swagger 注解 | 需要 UI 时单独立项 |
| JSpecify 与 JSR305 语义差异 | `@NonNull` 比 JSR305 `@Nonnull` 更严格 | 仅注解，无运行时/tooling 影响；如接 nullness 工具再评估 |
| 显式钉死清理不彻底 | 残留 pin 会静默降级 Boot 4 | 以 §6.2 表 + `effective-pom`/`dependency:tree` 门禁为准 |

---

## 10. 证据附录（实测）

| 结论 | 命令 / 来源 |
|---|---|
| 25 个 pom；component 根+21 子模块 | `find . -name pom.xml -not -path '*/target/*' \| wc -l` = 25；component 目录 22 个 pom |
| 84 处版本字面量 / 25 个 pom（82×0.1.0、2×0.2.0） | `grep -rn '<version>0\.[12]\.0</version>' --include=pom.xml`；分布 component-test 11、component-bap 8 |
| 31 个文件含 `javax.` 导入；迁 30 | `grep -rl '^import javax\.' --include='*.java'`；`AesCBCUtil`（javax.crypto）不动 |
| sdk javax.annotation = 12 处 | 11×Nullable + 1×Nonnull |
| 13 处 `<java.version>11</java.version>` | parent + 12 子模块 |
| 14 个文件使用 `com.fasterxml.jackson` | 其中 6 个仅注解，8 个需迁 tools.jackson |
| Boot 4.1.1 存在 | Central `spring-boot-dependencies/4.1.1` |
| Boot BOM 关键值 | `commons-lang3=3.20.0`、`hibernate-validator=9.1.3.Final`、`jackson-2-bom=2.21.5`、`jackson-bom=3.1.5`、`junit-jupiter=6.0.3`、`lombok=1.18.46`、`mockito=5.23.0`、`slf4j=2.0.18`、`log4j2=2.25.5`、`mysql=9.7.0`、`maven-compiler-plugin=3.15.0`、`jspecify=1.0.1`、`spring-kafka=4.1.1` |
| Lombok 1.18.20 在 JDK 25 失败 | 探针 `/tmp/probe-lombok`：`Fatal error compiling: ExceptionInInitializerError: com.sun.tools.javac.code.TypeTag :: UNKNOWN`；1.18.46 BUILD SUCCESS |
| MapStruct 1.5.5 在 JDK 25 可用 | 探针 `/tmp/probe-mapstruct` BUILD SUCCESS |
| compiler 3.8.1 + release 25 可编译 | 探针 `/tmp/probe-compiler` BUILD SUCCESS；但父显式 3.8.1 会覆盖 BOM 3.15.0 |
| Boot 4 包迁移 | jar 实测：`spring-boot-jdbc/4.1.1` 的 `org/springframework/boot/jdbc/autoconfigure/DataSource*`；`spring-boot-hibernate` 的 `.../hibernate/autoconfigure/HibernateJpaAutoConfiguration`；`spring-boot-http-converter` 的 `.../http/converter/autoconfigure/HttpMessageConverters`；`spring-boot-data-redis` 的 `DataRedisAutoConfiguration`/`DataRedisProperties`（含 `getCluster`/`getTimeout`） |
| Druid 新包 | `druid-spring-boot-4-starter:1.2.28` 内 `com/alibaba/druid/spring/boot4/autoconfigure/DruidDataSourceAutoConfigure` |
| `spring-boot-starter-aop` 4.1.1 不存在 | Central 404；`spring-boot-starter-aspectj` 200 |
| Cloud 2025.1.3 接受 Boot 4.1 | `spring-cloud-commons 5.0.3` `CompatibilityVerifierProperties` 默认 `4.0.x`、`4.1.x` |
| FileOutConfig 删除 | generator 3.5.17 jar 计数 0；`InjectionConfig` 已移到 `...generator.config` |
| Boot 4 starter-test 不含 JUnit 4/vintage | `spring-boot-starter-test:4.1.1` 依赖仅 `junit-jupiter`；无 vintage |
| JUnit 4 用例占比 | component-test 21 个类 `import org.junit.Test`；12 个类继承 `@SpringBootTest` 基类 |
| Mockito 冲突 | `mockito-inline:4.11.0`（component-file compile scope）vs Boot BOM `mockito-core 5.23.0` |
| Redisson 传递 javax | `redisson:3.17.0` → `javax.cache:cache-api`（compile）；升 4.7.0 后仍需排除该传递依赖 |
| sdk 无 Spring/JSpecify 传递 | `jsonrpc4j:1.0` 的 spring-core/context/web 均 `optional=true`；base 不带 Spring |
| 悬空依赖 | `component-test` 依赖 `com.metanet4j.bootstrap:metanet4j-bootstrap:0.1.0`；4 仓库与本地 m2 均无，代码无 import |
| fastjson 实际版本 | 父 POM `<fastjson.version>1.2.76</fastjson.version>`（非 1.2.83） |
| ES 服务端原为 7.17.5 | `backend/metanet4j-component/doc/部署文档.md`（`cd es7.17.5/`）；本次按用户决策升 9.4.5 |
| Nacos 不需要；Redis/MySQL 主链路不需要 | starter 注释态；用例无 DataSource 引用；main 已 exclude；Redis/MySQL 仅作为 B 档验证服务 |
| 中间件兼容性（官方文档） | Java 25 在 Boot 4.1.1 支持区间（Java 17–26，Spring 官方 System Requirements）；Kafka 官方兼容矩阵：3.x/4.x broker ↔ 4.x 客户端 ✅ 全兼容；Elastic 官方：9.x 客户端 ↔ 9.x 服务端；MySQL 官方 Connector/J 9.0 兼容章："支持 MySQL 8.0 及以上"；Redisson 官方专文：4.0.0 起支持 Boot 4.0、4.6.0 起支持 Boot 4.1 |
| ES 9.4.5 客户端内置 Jackson 3 mapper | 字节码实测 `Jackson3JsonpMapper` 引用 `tools.jackson.databind.json.JsonMapper` / `tools.jackson.core.JacksonException`（仅 `com.fasterxml.jackson.annotation.JsonInclude` 仍属 Jackson 2）；`elasticsearch-java-9.4.5.pom` 同时以 runtime 引入 Jackson 2.22.0 与 Jackson 3.1.0 |
| ES 9 起 RestClient 为外部可选依赖，改用 Rest5Client | Elastic 官方 9.0.0 release notes："The RestClient is part of the external dependency `elasticsearch-rest-client`, which is now optional"；官方 transport 文档把 REST 5 Client 列为推荐低层客户端；9.4.5 jar 内 `transport/rest_client` 与 `transport/rest5_client` 两套 transport 并存 |
| ES 9 的高层入口与默认 transport | 字节码实测：`ElasticsearchClient.of(Function<ElasticsearchTransportConfig.Builder,?>)` 存在；`ElasticsearchTransportConfig.Builder` 提供 `host/hosts/usernameAndPassword/apiKey/sslContext/jsonMapper/useCompression/transportFactory/useLegacyTransport`；`Rest5ClientTransport` 有 `(ElasticsearchTransportConfig)` 与 `(Rest5Client, JsonpMapper)` 构造 |
| ES 9 破坏性 API 未触及 | 代码 grep：`aggregations`/`Aggregation`/`valueBody`/`matchedQueries`/`indicesBoost`/`dynamicTemplates`/`msearch`/`esql`/`DenseVector` 均 0 处 |
| Redisson 4.7.0 坐标与自带模块 | Central 实测 200；starter pom `spring-boot.version=4.1.0`，依赖含 `redisson-spring-data-41`（Boot 4.1 下无需 exclusion） |
| Cloud 2025.1.3 的构建基线 | `spring-cloud-dependencies-2025.1.3.pom` 属性 `<spring-boot.version>4.0.8`；parent 为 `spring-cloud-dependencies-parent 5.0.3` |
| JUnit 4 用例真实总量 37 个 | 逐模块 `grep -rl '^import org.junit.Test;'`：component-test 21、sdk 13、base 2、connect-planaria 1（复评 P0-A） |
| B 档服务就位情况 | **共享中间件 `ownword-infra` 五个容器运行中且 healthy，逐服务握手全部 PASS**（MongoDB 8.0.32 / ES 9.4.5 / Kafka 4.2.1 KRaft / Redis 7.4.11 / MySQL 8.4.11）；镜像已钉补丁号、五个服务均挂命名数据卷、`restart: unless-stopped`；镜像来源：ES 走 `docker.elastic.co`，其余走 `docker.m.daocloud.io`（**裸 `apache/kafka:4.2.1` 经 Docker Hub 不可达**；daocloud 对极旧 tag 返回 403）；Mongo 认证实测需 `?authSource=admin` |

---

## 11. 执行记录

### Phase 0（2026-09-15）—— ✅ 完成

**环境**：JDK `25.0.4.1-tem`（sdkman 注册）+ Maven `3.9.16`，本地仓库 `~/.m2/metanet4j`。

**Gate 0 探针**（`/tmp/gate0`，jar 工程 + 1 个 Java 25 源文件）：

- `mvn -s ~/.m2/metanet4j-settings.xml -B clean compile` → **BUILD SUCCESS**，168 秒（含首次全量下载 107 MB / 161 jar）。
- 编译日志：`Compiling 1 source file with javac [debug release 25]`。
- 实际生效的编译插件：`maven-compiler-plugin 3.15.0`（由 Boot 4.1.1 BOM 管理；父 POM 显式 3.8.1 会覆盖它，故 D20 要求删除显式版本）。

**解析到的关键版本**（实测 `dependency:list`）：

| 坐标 | 解析版本 | 来源 |
|---|---|---|
| `org.springframework.boot:spring-boot` | 4.1.1 | Boot BOM |
| `com.mysql:mysql-connector-j` | 9.7.0 | Boot BOM |
| `org.hibernate.validator:hibernate-validator` | 9.1.3.Final | Boot BOM |
| `jakarta.validation:jakarta.validation-api` | 3.1.1 | Boot BOM |
| `io.swagger.core.v3:swagger-annotations-jakarta` | 2.2.55 | 显式 |
| `io.jsonwebtoken:jjwt-*` | 0.13.0 | 显式 |
| `com.baomidou:mybatis-plus-spring-boot4-starter` | 3.5.17 | 显式 |
| `com.alibaba:druid-spring-boot-4-starter` | 1.2.28 | 显式 |
| `org.springdoc:springdoc-openapi-starter-webmvc-ui` | 3.1.1 | 显式（本次不采用，见 D22） |
| `co.elastic.clients:elasticsearch-java` | 7.17.5（探针时）→ 目标 **9.4.5** | 显式；走 Rest5Client，无需再引 legacy `elasticsearch-rest-client`（见 D8） |
| `tools.jackson.core:jackson-databind` | 3.1.5 | Boot `jackson-bom` |
| `com.fasterxml.jackson.core:jackson-annotations` | 2.21.5 | Boot `jackson-2-bom` |

**Jackson 3 关键发现**：

1. `tools.jackson:jackson-bom:3.1.5` 的 `jackson.version.annotations=2.21` —— Jackson 3 配套 2.21 注解，`com.fasterxml.jackson.annotation.*` 包名与版本不变，注解一行不用改；只有 core/databind/datatype/module 迁 `tools.jackson.*`。
2. `JsonProcessingException` 在 Jackson 3 中已不存在，替代是 `tools.jackson.core.JacksonException`（unchecked）；`JacksonUtil` 的 `catch(IOException)`/`throws IOException` 必须同步调整（D15）。
3. `ObjectMapper.configure()` 已移除，改 `JsonMapper.builder()...build()`。
4. 运行期冒烟通过：序列化 `{"n":"hello"}`、反序列化正常、坏 JSON 抛 `tools.jackson.core.exc.StreamReadException`。
5. 类路径上 Jackson 2（ES 客户端、jjwt-jackson 的 runtime 依赖）仍存在，与 Jackson 3 并存符合预期，无需干预；ES 9.4.5 起可直接用 `Jackson3JsonpMapper` 走 Jackson 3 路径。

### 回退记录（2026-09-15）

按要求撤销了全部代码改动，仓库恢复原状：

| 撤销项 | 处理 | 结果 |
|---|---|---|
| `chore(release): bump metanet4j to 0.2.0`（4 仓库各 1 次提交） | 删除承载提交的分支，提交不可达 | 4 仓库 `diff dev` = 0，工作区 0 脏文件 |
| 分支 `feat/boot4-java25-<repo>`（4 条） | `git branch -D` | 已删除，4 仓库回到 `feature/java21` |
| tag `pre-boot4-java25`（4 个） | `git tag -d` | 已删除（`metanet4j-sdk` 的 `v0.2.0` 是原有资产，未动） |

**保留项**：JDK 25、Maven 3.9.16、`~/.m2/metanet4j` 与 settings、Gate 0 探针 `/tmp/gate0`、本计划文档、Review 记录。

### 中间件矩阵与兼容性核对（2026-09-15，第二轮）—— ✅ 文档完成

用户指定中间件全部升级，本次据此重定 §2 版本矩阵、D8–D10/D19/D23–D26、§6.5、§7.3、§9、§10：

- **结论**：Java 25 / Boot 4.1.1 / Maven 3.9.x ✅；Cloud 2025.1.3 ✅（按 Boot 4.0.8 构建，兼容校验接受 4.1.x）；ES 9.4.5 客户端 ↔ 服务端 ✅；Kafka 4.2.1 客户端 ↔ broker ✅（4.x 起必须 KRaft）；Connector/J 9.7.0 ↔ MySQL 8.4 ✅；Redisson 4.7.0 ↔ Boot 4.1 ✅；MongoDB 驱动 5.8.1 ↔ 8.0.32 按用户指定执行。
- **ES 9 迁移面**：`EsConfig` 改用 `ElasticsearchClient.of(...)` + `Jackson3JsonpMapper`（**Rest5Client 为官方推荐 transport，ES 9 默认**）；不再需要 legacy `elasticsearch-rest-client`；业务查询 API 无需改动。
- **Redisson 4.7.0**：3.17.0 与 Spring Data Redis 4.1 硬冲突，必须升级；starter 自带 `redisson-spring-data-41`。
- **环境**：五个中间件镜像与 tag 的可拉取性未验证，列为执行阶段第一步。

### 镜像 tag 可拉取性验证（2026-09-15，第三轮）—— ✅ 完成

| 镜像 | 结果 | 耗时 / 大小 |
|---|---|---|
| `docker.elastic.co/elasticsearch/elasticsearch:9.4.5` | ✅ | 103s / 2.51GB |
| `docker.m.daocloud.io/apache/kafka:4.2.1` | ✅ | daocloud 转发 |
| `apache/kafka:4.2.1`（裸 tag，Docker Hub） | ❌ `registry-1.docker.io` dial timeout | 29s 失败 |
| `docker.m.daocloud.io/library/mysql:8.4` | ✅ | 9s / 1.12GB |
| `docker.m.daocloud.io/library/redis:7.4` | ✅ | 已是最新 / 170MB |
| `docker.m.daocloud.io/library/mongo:8.0` | ✅ | 24s / 1.27GB |

**结论**：五个目标版本全部可获取；**Docker Hub 必须经 daocloud 全限定名**，compose 已按此写入。备用源（Apache 官方二进制 4.2.1 / 2.8.1）实测 200。

### 首个代码改动（2026-09-15，第四轮）—— ✅ 已提交

| 项 | 值 |
|---|---|
| 仓库 | `metanet4j-component`（唯一受影响仓库，其余 3 仓库仍 0 脏） |
| 分支 | `feature/java21`（按 AGENTS.md 要求，未使用 dev/test/master、未新建分支） |
| 提交 | **`d677634`** — `build: 移除 5 个模块中过期的 Maven Wrapper（锁定 3.8.2/3.8.3）` |
| 范围 | 15 个文件删除（`.mvn/wrapper/` × 5 模块：`MavenWrapperDownloader.java`、`maven-wrapper.jar`、`maven-wrapper.properties`），598 行删除 |
| 依据 | 用户指令；wrapper 锁定 Maven 3.8.2/3.8.3 会绕过 JDK 25 + Maven 3.9.16 的版本隔离（D5a）；仓库内零引用，各模块 `.gitignore` 本就忽略 `.mvn/**` 与 `mvnw` |
| 验证 | 删除后 `find . -name .mvn` 无残留；`git status --short` 干净；未触碰任何 pom/源码 |

### 中间件握手验证（2026-09-15，第五轮）—— ✅ 全部 PASS

中间件编排已迁出任务目录，落盘为**共享设施 `ownword/infra/`**（compose 项目 `ownword-infra`，容器 `infra-mongo` / `infra-es` / `infra-kafka` / `infra-redis` / `infra-mysql`）；`cd /home/haodev/ownword/infra && ./up.sh` 后 5 个容器全部 healthy，逐服务实测：

| 服务 | 实测版本 | 握手动作 | 结果 |
|---|---|---|---|
| MongoDB | **8.0.32** | `buildInfo` + `ping` + insert/find roundtrip + drop | ✅ PASS |
| Elasticsearch | **9.4.5**（Lucene 10.4.0） | 建索引 + 写入 + `_search` 命中 + 删索引 | ✅ PASS |
| Kafka | **4.2.1（KRaft）** | broker api-versions + 建 `parse_block_topic` + 生产 + 消费 + describe | ✅ PASS |
| Redis | **7.4.11** | `PING` + `SET/GET`（带 TTL） | ✅ PASS |
| MySQL | **8.4.11**（`caching_sha2_password`） | `SELECT VERSION()` + 建库/建表/REPLACE/SELECT/DROP | ✅ PASS |

- **宿主机端口全部可达**：27017 / 9200 / 9092 / 6379 / 3306 从宿主机 `127.0.0.1` 均可连接；ES 版本号从宿主机 `curl` 复核为 `9.4.5`。
- **Mongo 认证结论（重要）**：应用原 URI `mongodb://bschema:bschema123@localhost:27017/bschema` **认证失败**（`MongoServerError: Authentication failed`）；加 `?authSource=admin` **成功**。→ P4 必须采用 §7.3 的**方案 A：URI 追加 `?authSource=admin`**。
- **Kafka 监听地址**：`KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092` 是按"应用跑在宿主机"设计的；若将来把应用也放进容器网络，需同步改成容器服务名。
- **资源占用**：ES 1.11GB、MySQL 484MB、Kafka 409MB（CPU 峰值 197% 在建 topic/auth 阶段）、Mongo 227MB、Redis 10MB，合计约 2.2GB，磁盘与内存余量充足。

**服务就位状态**：五个中间件**当前处于运行中且已转为长期共享设施**（`ownword/infra/`，`restart: unless-stopped`），可直接进入 P4/P5。**验证结束后不要执行 `down -v`**（会清掉跨任务共享的数据）；如确需重置，先确认没有其他任务在用。

### 环境就绪清单

| 检查项 | 状态 |
|---|---|
| JDK 25（`25.0.4.1-tem`）可用、sha256 双源校验一致 | ✅ |
| Maven 3.9.16 在 JDK 25 上运行（命令需带 `JAVA_HOME`） | ✅ |
| **全局 java/maven 默认版本未被修改**（D5a） | ✅ 实测：java `current` → `8.0.181-local`，maven `current` → `3.9.9`（均保持原样） |
| **未使用/未新增 Maven wrapper** | ✅ 五个模块内过期的 `.mvn/wrapper`（锁 Maven 3.8.2/3.8.3）已删除并提交 `d677634`（metanet4j-component 仓库）；本次不新增 `mvnw`，全部走绝对路径 |
| `~/.m2/metanet4j` 本地仓库可用、与默认仓库隔离 | ✅（仅 190MB，只含探针依赖；项目依赖树待 P0.5 预取） |
| Boot 4.1.1 / Cloud 2025.1.3 / springdoc 3.1.1 / jjwt 0.13.0 等新坐标可解析 | ✅ |
| `--release 25` 编译通过 | ✅ |
| Jackson 3 运行期冒烟 | ✅ |
| docker 可用于 B 档验证；27017/9200/9092/6379/3306 空闲；`e2e-zookeeper` 在跑（仅供 rocketmq，Kafka 4.2.1 走 KRaft） | ✅（目标版本镜像待执行阶段拉取并先验 tag） |
| 4 仓库代码状态 = `feature/java21`（与 dev 同点、0 脏） | ✅ |
| 中间件版本矩阵与兼容性核对（官方文档） | ✅ 见 §2 / D23–D24 / §10 证据表 |
| 中间件目标版本镜像与 tag 可拉取性 | ✅ 五个 tag 全部实测拉取成功（Kafka 需用 daocloud 全限定名） |
