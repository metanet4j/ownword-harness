# session-handoff.md — 会话交接

> 唯一起步点：先读 `../AGENTS.md`（共享规则）、`../mvn-command.md`（命令模板）、
> `doc/升级计划-Boot4-Java25.md`（任务事实来源），再读本文件。
> 本文件只写"现在到哪了、下一步做什么、卡在哪"，不复述任务内容。

## 30 秒现状

- 进度：**P0 / P0.5 / P1 / P2 / P3 全部完成并提交**；四仓库工作区干净（各 commit 见 `progress.md`）。
- 状态：`activeItem = boot4-p4-component`（in-progress）——本项是本次升级的主战场（22 pom + 源码迁移）。
- 基座：`~/.m2/metanet4j` 中 parent / base / sdk 的 0.2.0 均已安装，component 可直接构建。
- 环境：共享中间件五个容器 healthy；全局工具链未污染。

---

# 本次交接：执行 `boot4-p4-component`（22 个 pom + 源码迁移）

> 改动清单以计划 **§6.5** 为准（本节是执行摘要），门禁以 **§6.6** 的 grep/tree 命令为准。
> 依赖基座已就绪：`metanet4j-parent` / `-base` / `-sdk` 0.2.0 已 install 进隔离仓库。

## 1. pom 坐标（旧 → 新）

| 旧 | 新 | 位置 |
|---|---|---|
| `spring-boot-starter-aop` | `spring-boot-starter-aspectj` | component-common |
| `mysql:mysql-connector-java` | `com.mysql:mysql-connector-j`（BOM 9.7.0，不写版本） | store-sql、mybatispuls-generator |
| `com.alibaba:druid-spring-boot-starter` | `druid-spring-boot-4-starter` 1.2.28（parent 管） | store-sql |
| `com.baomidou:mybatis-plus-boot-starter` | `mybatis-plus-spring-boot4-starter` 3.5.17（parent 管） | store-sql |
| `io.springfox:springfox-swagger2` | `io.swagger.core.v3:swagger-annotations-jakarta` 2.2.55（parent 管） | component-model |
| `io.jsonwebtoken:jjwt` | `jjwt-api`(compile) + `jjwt-impl`/`jjwt-jackson`(runtime) 0.13.0 | api-common 等 |
| Jackson 2 core/datatype/module | **仅** `tools.jackson.core:jackson-databind`（datatype/module 已并入 databind） | base 已改，component-file 同 |
| redisson-spring-boot-starter 3.17.0 | **4.7.0**（自带 redisson-spring-data-41，勿加 exclusion）；**排除传递的 `javax.cache:cache-api`**（D21） | component-cache |
| `elasticsearch-java` 7.17.5（内联版本） | **9.4.5**；不引 legacy `elasticsearch-rest-client` | store-search |
| `jakarta.json-api` 钉死 | 删除（parent 已删，BOM 2.1.3） | store-search |
| `hibernate-validator` 6.x 钉死 | 走 BOM 9.1.3.Final（javax → jakarta） | base/component-common 等 |
| `log4j-slf4j-impl` | `log4j-slf4j2-impl`（base 已改，component 若有同步） | 全仓 grep |

## 2. 源码迁移（16 + 14 + 3 + 3 + 1 类）

- **javax → jakarta/jspecify（16 文件）**：validation 9 处 → `jakarta.validation.*`；
  `javax.annotation.Resource/PostConstruct` 5 处 → `jakarta.annotation.*`；
  `javax.servlet.http.HttpServletRequest` 2 处 → `jakarta.servlet.http.*`；测试文件 1 个（`S3FileClientTest`，`-DskipTests` 也要 test-compile）。
  **`javax.crypto` 不动**（在 sdk）。
- **Boot 4 包迁移（3 文件）**：`Metanet4jComponentTestApplication`（3 import + exclude 数组 + Druid 包名 boot4）、
  `DefaultFeginClient`（删未用的 `HttpMessageConverters`）、`RedissonAutoConfiguration`（`RedisAutoConfiguration`→`DataRedisAutoConfiguration`、`RedisProperties`→`DataRedisProperties`）。
- **Jackson 3（14 文件）**：8 个 `core/databind/datatype` 导入迁 `tools.jackson.*`；6 个只用注解的不动；
  **store-search 不删 Jackson 2**（ES 9.4.5 客户端的 `JacksonJsonpMapper` 仍用 Jackson 2）。
- **Swagger（3 文件 + 1 pom）**：`@ApiModel`→`@Schema(description=...)`、`@ApiModel(value=)`→`@Schema(name=)`、`@ApiModelProperty(value=)`→`@Schema(description=)`。
- **JJWT 0.13**：`JwtTokenProvider` 重写（`Jwts.parser().verifyWith(key)`、`Jwts.SIG.HS256`、`Keys.hmacShaKeyFor`），不再用 `SignatureAlgorithm`/`javax.xml.bind`。
- **ES 9**：`EsConfig` 改 `ElasticsearchClient.of(b -> b.host(...).jsonMapper(new Jackson3JsonpMapper()))`（Rest5Client），测试 `EsTest` 同步。
- **Redisson**：`RedissonAutoConfigurationV2` → `RedissonAutoConfigurationV4`（yml/properties/注解三种写法都查）。
- **配置**：`application.yml` 的 `spring.redis.*` → `spring.data.redis.*`；Mongo URI 补 `?authSource=admin`。

## 3. Gate（§6.6，逐条贴输出）

```bash
export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem
MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"
cd $TASK/metanet4j-component
$MVN clean package -DskipTests          # ① 聚合编译（含 test-compile；测试执行归 P5）
grep -rn '^import javax\.' --include='*.java' .. | grep -v /target/     # ② 只允许 sdk 的 AesCBCUtil
grep -rn -E 'org\.springframework\.boot\.autoconfigure\.(jdbc|orm\.jpa|http\.HttpMessageConverters|data\.redis)' --include='*.java' .. | grep -v /target/   # ③ = 0
grep -rn -E 'com\.fasterxml\.jackson\.(core|databind|datatype|module)' --include='*.java' .. | grep -v /target/  # ④ = 0
grep -rn -E 'org\.apache\.http\.HttpHost|org\.elasticsearch\.client\.RestClient|RestClientTransport' --include='*.java' .. | grep -v /target/  # ⑤ = 0
$MVN -pl metanet4j-store-search dependency:tree -Dincludes=co.elastic.clients,org.elasticsearch.client   # ⑥ ES=9.4.5 且无 legacy
$MVN -pl metanet4j-component-cache dependency:tree -Dincludes=org.redisson                               # ⑦ redisson-spring-data-41 在、无 2x
grep -rn 'RedissonAutoConfigurationV2' . --include='*.yml' --include='*.yaml' --include='*.properties' --include='*.java' | grep -v /target/   # ⑧ = 0
```

## 4. 完成后

1. component 仓库单独提交（中文 Conventional Commits）；若 base/sdk 需同步（如 log4j artifactId），各自提交。
2. 更新 `feature_list.json`（P4→done 附 evidence、`activeItem`→`boot4-tests-jupiter` 或 null）、`progress.md`、本文件。
3. 计划与实际不符时：**先改计划文档，再改代码**。

---

## Next Session（后续顺序，做完一项再申请下一项）

1. ✅ `boot4-p05-prefetch`、✅ `boot4-p1-version`、✅ `boot4-p2-parent`、✅ `boot4-p3-base-sdk`
2. **`boot4-p4-component`（in-progress，本次交接）**——22 pom + 源码迁移 + ES 9 + Redisson 4.7.0
3. 之后：`boot4-tests-jupiter`（测试门禁）→ `boot4-p5-verify` → `boot4-p6-finish`

## 开工自检

```bash
cd /home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade
./init.sh          # 环境 + 仓库状态（秒级）
./init.sh --full   # 追加真实构建；P2 之前预期失败，属正常进度
```

## Blockers（阻塞与未决取舍）

| 阻塞/取舍 | 说明 |
|---|---|
| sdk 26 个既有错误 | `BapBase` 构造顺序缺陷（父类构造器调被覆写方法）→ NPE；**需用户决策**：修构造顺序 or 修测试夹具（计划 §6.4） |
| 测试门禁基线 | `boot4-tests-jupiter` 依赖已解除（P2 完成），但需先决定 sdk 构造顺序缺陷的处置 |
| 逐项批准 | 用户 2026-09-16 指示「继续执行，改代码不必逐项确认」；仅计划未覆盖的架构决策/取舍需停下来问 |
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
