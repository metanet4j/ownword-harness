# session-handoff.md — 会话交接

> 唯一起步点：先读 `../AGENTS.md`（共享规则）、`../mvn-command.md`（命令模板）、
> `doc/升级计划-Boot4-Java25.md`（任务事实来源），再读本文件。
> 本文件只写"现在到哪了、下一步做什么、卡在哪"，不复述任务内容。

## 30 秒现状

- 进度：**P0 环境 + P0 基线清理 + P0.5 预取 + P1 版本号统一 已完成**（四仓库均有提交，见 `progress.md`）。
- 状态：`activeItem = boot4-p2-parent`（in-progress）——用户 2026-09-16 指示「继续执行，改代码不必逐项确认」。
- 环境：共享中间件五个容器 healthy；全局工具链未污染；隔离仓库 `~/.m2/metanet4j` 已预取 352MB/705 jar。

---

# 本次交接：执行 `boot4-p2-parent`（父 POM 改造）

> 这是**测试能否真实执行的前置**：lombok 1.18.20 + JDK 25 编译必崩，本项不落地，后面所有测试都跑不起来。
> 改动清单以计划 **§6.2** 为准，本文件只写「怎么执行、怎么验」。

## 1. 改什么（计划 §6.2 摘要）

**属性与 BOM**
- `spring-boot-starter-parent` 2.3.2.RELEASE → **4.1.1**；`java.version` → **25**；`maven.compiler.release` → `${java.version}`。
- `spring-cloud.version` Hoxton.SR8 → **2025.1.3**；删除 spring-cloud-alibaba BOM import。
- 删除 `maven.compiler.source/target`（改用 release）。

**删除/上调的钉死（D14，逐条都做了才算完）**

| 属性/坐标 | 动作 |
|---|---|
| lombok 1.18.20 | 删除（跟随 Boot BOM 1.18.46）——**本项核心** |
| slf4j 1.7.32 与 3 个 depMgmt | 删除；移除 `slf4j-jdk14` |
| log4j 2.20.0 | 删除钉死；`log4j-slf4j-impl` → **`log4j-slf4j2-impl`**（base pom 同步换 artifactId） |
| hibernate-validator 6.1.5.Final | 删除（跟随 BOM 9.1.3.Final；6.1.5 是 javax.validation） |
| jackson 2.13.2（6 个 depMgmt） | 删除 core/databind/datatype/module 钉死（注解 2.21.5 由 jackson-2-bom 管，tools.jackson 由 jackson-bom 3.1.5 管） |
| junit 4.13 | → **4.13.2** |
| lettuce 5.3.2.RELEASE | 删除（跟随 BOM 7.5.2.RELEASE） |
| mysql-connector-java 8.0.25 | 删除属性；depMgmt 坐标改 `com.mysql:mysql-connector-j` |
| druid 1.2.1 | → **1.2.28**；artifactId → `druid-spring-boot-4-starter` |
| mybatis-plus 3.4.2（出现两次） | → **3.5.17**；artifactId → `mybatis-plus-spring-boot4-starter` |
| mybatis-plus-generator 3.4.1 | → **3.5.17** |
| velocity-engine-core 2.0 | → **2.4.1** |
| commons-lang3 3.10 | 删除（跟随 BOM 3.20.0） |
| jakarta.json 2.0.1 | 删除（跟随 BOM 2.1.3；ES 9.4.5 要求 2.1.3） |
| ES client 7.17.5 | → **9.4.5**（仍走 Rest5Client，不补 legacy rest-client） |
| springfox-swagger2 depMgmt | 删除；新增 `io.swagger.core.v3:swagger-annotations-jakarta:2.2.55` |
| jjwt 0.9.1 depMgmt | 改 `jjwt-api`/`jjwt-impl`/`jjwt-jackson` **0.13.0** |
| guava 30.1.1-jre / bcprov 1.71 / fastjson 1.2.76 / mapstruct 1.5.5.Final | **保留**（注明原因） |

**build / 插件**
- 删 compiler 插件的 `<version>3.8.1</version>`（用 Boot BOM 3.15.0）；`<source>/<target>` → `<release>${java.version}</release>`；
  保留 `annotationProcessorPaths`（mapstruct / lombok / lombok-mapstruct-binding）——**注意复评 P1-1：删 lombok 属性时同步改这里的字面量**。
- `maven-source-plugin` 保留。
- 新增 `maven-enforcer-plugin`：`requireJavaVersion [25,)` + `bannedDependencies` 拦 `javax.*`（白名单 `javax.cache:cache-api`）。

## 2. 怎么验（P2 Gate，三条都要贴输出）

```bash
export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem
MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"
cd $TASK/metanet4j-parent
$MVN -N install                                   # ① 成功，且装出 0.2.0
$MVN help:effective-pom | grep -A3 maven-compiler-plugin | grep -m1 '<version>'   # ② 3.15.0
$MVN enforcer:enforce                             # ③ 通过（含 javax.* 拦截规则生效）
```

## 3. 完成后

1. `mvn -N install` 产物确认后，parent 仓库单独提交（中文 Conventional Commits）。
2. 更新 `feature_list.json`（P2→done 附 evidence、`activeItem`→`boot4-p3-base-sdk` 或 null）、`progress.md`、本文件。
3. 若发现计划与实际不符：**先改计划文档，再改代码**，并在 `progress.md` 记录偏差。

---

## Next Session（后续顺序，做完一项再申请下一项）

1. ✅ `boot4-p05-prefetch` 依赖预取（0 失败，隔离仓库 352MB/705 jar）
2. ✅ `boot4-p1-version` 版本号统一 0.2.0（四条 Gate 全绿，四仓库已提交）
3. **`boot4-p2-parent` 父 POM 改造（in-progress，本次交接）**——**lombok 1.18.20 必须换掉，否则 JDK 25 下编译直接崩**
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
| 逐项批准 | 用户 2026-09-16 指示「继续执行，改代码不必逐项确认」；仅计划未覆盖的架构决策/取舍需停下来问 |
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
