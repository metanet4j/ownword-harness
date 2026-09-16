# progress.md — boot4-java25-upgrade 进度

> 会话连续性日志：只写**当前状态**与下一步。任务内容见 `doc/升级计划-Boot4-Java25.md`，
> 共享规则见 `../AGENTS.md`；某处为什么这么改，查 git log（文档不留变更记录）。

## Current State（当前状态）

- **Last Updated**：2026-09-16（交付后修复 I/II 均完成：任务全部收口，P0~P6 + 两轮交付后修复全 done）
- **Current Objective**：无（本任务已交付；交付物见 `doc/验收报告-Boot4-Java25-20260916-1320.md`）
- **Recommended Next Step**：无必做项；如有后续动作，先看文末「下一步」与「未决项」
- **远端状态**：四仓库已推送 `origin/feature/java21`（三轮：交付成果 → 交付后修复 I → 交付后修复 II），远端 `dev`/`master` 未被触碰；ownword 仍为本地提交
- **执行授权**：用户 2026-09-16 指示「继续执行，改代码不必逐项确认」；仅在计划未覆盖的架构决策/取舍上停下问（`AGENTS.md` §5）
- **依赖基座**：parent / base / sdk / component 的 0.2.0 均可构建安装
- **中间件**：共享设施 `ownword/infra/` 五个容器 healthy 运行中
- **全局工具链**：JDK 8 / Maven 3.9.9 未被改动（`./init.sh` 每次校验）

## 门禁与证据（最新一轮）

| 模块 | 执行数 | 结果 |
|---|---|---|
| metanet4j-base | 2 | 2 通过 |
| metanet4j-sdk | 26 | 26 通过（含交付后新增 3 个离线回归用例；另 29 个 external 被排除） |
| metanet4j-connect-planaria | 1 | 1 通过 |
| metanet4j-component-file | 8 | 8 通过（8 skipped 为需凭据的 S3/SFTP 用例） |
| metanet4j-component-test | 101 | 101 通过（交付后修复 II 后 +6：3 个撤销 external 的 resolver 用例、1 个补断言的 `testAddress`、2 个新回归类实例） |

- 复跑：`export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem`；`MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"`；
  `(cd metanet4j-component && $MVN clean test -DexcludedGroups=external)`
- `contextLoads` 在 9 个类的 `TEST-*.xml` 中真实执行。**注意口径**：surefire 的 `.txt` 只记失败项，
  通过用例不出现 → 判定 `contextLoads` 必须看 XML，`grep *.txt` 会误报"未执行"。
- §6.6 九条 grep 门禁全绿（pom 25 / 0.1.0 字面量 0 / `metanet4j.version=0.1.0` 0 / `java.version=11` 0 /
  `import javax.*` 仅白名单 `AesCBCUtil` / Boot 4 旧包名 0 / Jackson 旧 core·databind 0 /
  `RedissonAutoConfigurationV2` 0 / http·RestClient·RestClientTransport 0）
- 依赖树断言：`elasticsearch-java:9.4.5` + `elasticsearch-rest5-client:9.4.5`（无 legacy rest-client）、
  `redisson-spring-data-41:4.7.0`（无 2x）、`kafka-clients:4.2.1`、`mongodb-driver-sync:5.8.1`、`mysql-connector-j:9.7.0`
- 原始日志：`/tmp/boot4-p5-diag/`（`full-gate.log`、`component-test-green.log`、`diag-before/after.log`、
  `repro-mongo*.log`、`es*.log`、`resolver*.log`）

## What's Done（已完成）

| 事项 | 证据 |
|---|---|
| P0 环境（工具链 + 共享中间件 `ownword/infra`） | ownword 提交 `8770634`；五服务握手 PASS |
| P0 基线清理（移除 5 个模块的过期 Maven Wrapper） | metanet4j-component `d677634` |
| P0.5 依赖预取（隔离仓库 265MB/516 jar → 352MB/705 jar，0 失败） | `/tmp/boot4-prefetch/prefetch.log` |
| P1 版本号统一 0.2.0（82 处 + 属性 + 13 处 `java.version=11` 清零） | parent `5f462fa` / base `d0e2384` / sdk `52e59bb` / component `6ecd226` |
| P2 父 POM（Boot 4.1.1 / Java 25 / claim 清理 / compiler 3.15.0 / enforcer） | parent `935b5f5` + `a82ab4e` |
| P3 base + sdk（jakarta·JSpecify / Jackson 3 / 日志） | base `4f5a65a`；sdk `097870d` |
| P4 component（22 pom + 源码迁移 + ES 9 + Redisson 4.7.0 + 测试基建） | component `b468ba8`（含 6 处先改计划的偏差） |
| 测试门禁（全仓 39 文件迁 Jupiter + sdk 两处构造链缺陷修复 + 联网用例打 Tag） | parent `50598c0` / base `6e16cfa` / sdk `451020e`·`bc966e5` / component `0ce5c18` |
| **P5 验证与收敛**（Mongo 认证根因、ES 两处、resolver 两类、`ComplteTxFactoryTest` 定性；门禁复跑全绿） | 见计划 §11「P5 验证」记录与本文件「门禁与证据」；component 提交 `73e3ad4` |
| **P6 收尾**（四仓库提交确认 + 文档同步 + 验收报告输出） | `doc/验收报告-Boot4-Java25-20260916-1320.md`；ownword 提交见 git log |
| **交付后修复 I**（sdk `initSignType` 死代码 + 测试应用 Redis/MySQL 配置对齐） | sdk `bae4c36`（含离线回归用例 + 负向验证）、component `d585194`；已推送 |
| **交付后修复 II**（`MongoBapService.findIdentityKey` 空桩 + `TxoBobConverter` 用例从未执行） | component `e634982`（含自足回归用例 + 负向验证；3 个 resolver 用例撤销 external 并自足化）；已推送 |

## 关键事实（避免重复踩坑）

1. **不改 lombok 钉死则编译不通**：lombok 1.18.20 + JDK 25 = `Fatal error compiling: TypeTag :: UNKNOWN`。
2. **测试必须 `clean test`**：陈旧 `target/` 字节码会产生假 error。
3. **MongoDB 认证必须带 `authSource=admin`**；Boot 4 的连接配置前缀是 **`spring.mongodb.uri`**（`spring.data.mongodb.*` 全系 deprecated）。
4. **YAML 顶层键不能插在 `spring:` 块中间**：一旦顶格插入（如 `planaria:`），其后所有 `spring.*` 键会被归到插入键之下，
   Spring 侧表现为"配置静默不生效"（本次真实踩坑：Mongo 无凭据连接 → `Command find requires authentication`；
   修复见计划 §11 P5 记录）。写嵌套配置后建议用 `python -c "import yaml;..."` 打印真实结构核对。
5. **Kafka 是 KRaft**：4.x 已移除 ZooKeeper；`CLUSTER_ID` 固定，数据卷复用时不可改。
6. **ES 9 迁移面很小**：改动集中在 `EsConfig` 的 mapper/transport 与依赖坐标；索引/字段是否真的存在要用 `_mapping` 查（本次 `txInMemoryPoolTimeStamp` 就是"产品里不存在的字段"）。
7. **Docker Hub 不可达**：镜像走 `docker.m.daocloud.io/` 全限定名（`docker.elastic.co` 可直连）。
8. **worktree 的 `.git` 是文件**：判定仓库用 `git rev-parse --git-dir`。
9. **`spring-kafka` 不要带 4.2.1 版本号**：4.2.1 是 `kafka-clients`；`spring-kafka` 由 BOM 管（4.1.1）。
10. **`spring-boot-starter-aop` 在 4.1.1 上不存在**，替代坐标 `spring-boot-starter-aspectj`。
11. **ES 9.4.5 客户端同时带 Jackson 2 与 Jackson 3**（预期）。
12. **depMgmt 里不带 `<version>` 的条目会屏蔽 Boot BOM**：跟随 BOM 的坐标必须整条删除 depMgmt 条目。
13. **Jackson 3 只有 core/databind 三件套**：`datatype-jdk8`/`datatype-jsr310`/`module-parameter-names` 已并入 databind。
14. **纯 JUnit4 模块不会静默跳过**：surefire 3.5.6 见到 `junit:junit` 会自动选 junit4 provider。
15. **Jupiter 会静默忽略非 void 的 `@Test` 方法**（`@Test public String foo()` 不报错也不执行）；
    报告里没出现的类要能逐条解释（AGENTS §8 口径）。
16. **`BapDataLockBuilder.initSignType` 曾是死代码**（父类 `signType` 已初始化成 `CURRENT`，非 null，导致 `if (signType == null)` 恒假）→ `buildRoot()`/`buildId()` 用 CURRENT 地址签名、
    `BapHelper.isRootBap` 判 false、解析器认不出 root。**已于交付后修复**（sdk `bae4c36`：直接写入 `signType`；新增离线回归用例 `BapDataLockBuilderSignTypeTest` + 负向验证）。
17. **`MongoBapService.findIdentityKey` 是返回 null 的桩**且带 `@Primary` → Mongo-only 部署下「签名地址 → identityKey」反查恒失效；
    真实实现在 `MysqlBapService`（本测试应用按设计未纳入 store-sql）。相关用例已打 `@Tag("external")`。

## 未决项（需用户决策）

| # | 事项 | 影响 | 建议 |
|---|---|---|---|
| 1 | ~~sdk `initSignType` 死代码~~ **已修** | — | ✅ sdk `bae4c36`（含离线回归用例 + 负向验证），已推送 |
| 2 | ~~测试应用 Redis/MySQL 配置与共享设施不一致~~ **已对齐** | — | ✅ component `d585194`，已推送 |
| 3 | ~~`MongoBapService.findIdentityKey` 空桩~~ **已修** | — | ✅ component `e634982`（委托 `BapIdRepository.findIdentityKey`；自足回归用例 + 负向验证），已推送 |
| 4 | ~~`TxoBobConverter`（3 个用例）从未被 surefire 选中~~ **已修** | — | ✅ component `e634982`：改名 `TxoBobConverterTest`；1 补断言入门禁 / 1 空用例删除 / 1 打方法级 external |
| 5 | 未打基线 tag `pre-boot4-java25` | 计划 §8 草案要求开工前打；实测 `dev` 全程未移动，回滚等价 `git checkout dev` | 如需留痕可补打 |
| 6 | 57 个用例被 `@Tag("external")` 排除 | sdk 29 + component-test 28（需公网广播、本机绝对路径夹具、MySQL/S3 凭据、2023 主网 outpoint 等） | 已逐类定性归档；不进常规门禁 |

## 下一步（Next）

1. 本任务已交付并已推送：提交 ID = parent `50598c0` / base `6e16cfa` / sdk **`bae4c36`** / component **`e634982`**；
   远端 `origin/feature/java21`（四仓库一致）；验收报告见 `doc/验收报告-Boot4-Java25-20260916-1320.md`。
2. 如需继续：① 需要留痕则补打基线 tag `pre-boot4-java25`；② ownword 任务文档若要推送需明确指示。
