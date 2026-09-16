# mvn-command.md — Maven 命令固定模板

> 本文件是 `_task/backend-worktree/` 下所有任务的 **Maven 命令唯一事实来源**。
> `AGENTS.md` 只引用本文件，不重复内容。
> 每条命令都在本机实测过（Maven 3.9.16 / JDK 25 / 隔离仓库 `~/.m2/metanet4j`）。

## 1. 执行前的固定前置（每次都要）

```bash
export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem
MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"
```

- **JAVA_HOME 必设**：不设时 shell 默认是 JDK 8，`--release 25` 直接失败。
- **`-s` 必带**：把依赖装进隔离仓库 `~/.m2/metanet4j`，不污染全局 `~/.m2/repository`。
- **`-B`**：批处理模式，无交互，脚本里必须带。

验证当前 Maven 实际跑在哪个 JDK：

```bash
$MVN -v | grep 'Java version'      # 期望：Java version: 25.x
```

## 2. 生命周期与阶段（理解命令的基础）

Maven 三种生命周期，本项目只用到前两种：

| 生命周期 | 阶段顺序 |
|---|---|
| `clean` | pre-clean → **clean** → post-clean |
| `default` | validate → **compile** → test-compile → **test** → **package** → verify → **install** → deploy |

**阶段是链式的**：执行后面的阶段会自动执行前面的全部阶段。

```bash
mvn test        # = validate → compile → test-compile → test
mvn package     # = 上面全部 + package（所以 package 会跑测试）
mvn install     # = 上面全部 + 安装到本地仓库
```

## 3. 各命令的准确含义

| 命令 | 做什么 | 本项目要点 |
|---|---|---|
| `mvn compile` | 只编主代码到 `target/classes` | 不编测试代码；快速验证主代码 |
| `mvn test-compile` | 编主代码 + 测试代码 | 测试源码有错在此暴露 |
| `mvn test` | 上面全部 + surefire 执行测试 | **验收主命令，必须带 `clean`** |
| `mvn package` | 上面全部 + 打 jar/war | 包含 test，会跑测试 |
| `mvn install` | 上面全部 + 装进 `~/.m2/metanet4j` | 下游模块靠它解析依赖 |
| `mvn verify` | 上面全部 + 集成测试（failsafe） | 本项目未用 failsafe，等同 package |
| `mvn deploy` | 上面全部 + 推远程仓库 | **本项目无远程仓库，不可执行** |

## 4. 常用 flag

| flag | 含义 | 何时用 |
|---|---|---|
| `-N` | 只构建当前 POM，**不进子模块** | 装 parent（packaging=pom）；在聚合工程目录只处理聚合 POM |
| `-pl <模块>` | 只构建指定模块 | 单模块调试 |
| `-am` | 连同它依赖的模块一起构建 | 单跑下游模块时保证上游最新 |
| `-o` | 离线模式 | 依赖已拉全时加速 |
| `-U` | 强制刷新 SNAPSHOT/元数据 | 依赖版本异常时 |
| `-DskipTests` | **跳过执行，但仍编译测试** | 只验证主代码编译 |
| `-Dmaven.test.skip=true` | 编译与执行都跳过 | 连测试代码有错也不想被卡 |
| `-Dtest=类名` / `-Dtest='类#方法'` | 指定测试类/方法 | 定位单个用例 |
| `-Dgroups` / `-DexcludedGroups` | 按 Jupiter `@Tag` 筛选 | 分离需要外部服务的用例 |
| `-q` / `-X` | 精简输出 / debug 日志 | 排查问题用 `-X` |

## 5. 本项目的执行顺序（依赖靠本地仓库传递，顺序不能乱）

仓库的 packaging 决定了 flag 的用法：

| 仓库 | packaging | 说明 |
|---|---|---|
| `metanet4j-parent` | pom | 只发 POM → 用 `-N install` |
| `metanet4j-base` | jar | 普通模块 |
| `metanet4j-sdk` | jar | 普通模块 |
| `metanet4j-component` | pom + 21 modules | **聚合工程**，命令会递归进子模块 |

**标准流程**：

```bash
TASK=$(pwd)      # 在任务目录下执行
export JAVA_HOME=$HOME/.sdkman/candidates/java/25.0.4.1-tem
MVN="$HOME/.sdkman/candidates/maven/3.9.16/bin/mvn -s $HOME/.m2/metanet4j-settings.xml -B"

# ① 父 POM 变更后必做（否则子模块用的还是旧父 POM）
(cd $TASK/metanet4j-parent && $MVN -N install)

# ② 逐层：上游先 install，下游才能解析依赖
(cd $TASK/metanet4j-base      && $MVN clean install)
(cd $TASK/metanet4j-sdk       && $MVN clean install)
(cd $TASK/metanet4j-component && $MVN clean package)
```

## 6. 单模块与单用例调试

```bash
# 只跑某个子模块（在 component 目录下）
$MVN -pl metanet4j-component-test clean test

# 连同它依赖的上游模块一起构建
$MVN -pl metanet4j-component-test -am clean test

# 单个类 / 单个方法
$MVN -pl metanet4j-component-test clean test -Dtest=BapMongodbTest
$MVN -pl metanet4j-component-test clean test -Dtest='BapMongodbTest#testSave'
```

## 7. 三条硬规则

1. **测试一律 `clean test`**：不 clean 时 surefire 会从陈旧 `target/test-classes` 执行旧字节码，
   曾导致报错指向源码中不存在的字段，产生假 error。**不 clean 的测试结果不可信。**
2. **三种"跳过"别混**：只验证主代码用 `-DskipTests`；连测试代码都不编用 `-Dmaven.test.skip=true`；
   **验证测试迁移完整性时两个都不能加**。
3. **`clean` 与 `install` 不要一起用在父 POM 上**：父 POM 是 `pom` packaging，`-N install` 足够；
   对聚合工程不加 `-N` 会递归跑 21 个子模块，容易误伤。

## 8. 测试结果的判定（不看 BUILD SUCCESS）

**BUILD SUCCESS 不能证明用例跑过**——没有对应测试引擎时，用例会被静默跳过而构建照样绿。判定要三件事一起看：

```bash
# ① 逐模块执行数（不接受"总数 > 0"）
grep -h 'Tests run' $TASK/*/target/surefire-reports/*.txt
grep -h 'Tests run' $TASK/metanet4j-component/*/target/surefire-reports/*.txt

# ② 关键用例真的执行了（上下文冒烟）
grep -rl 'contextLoads' $TASK/*/target/surefire-reports/*.txt

# ③ 报告文件清单：没出现的测试类 = 没执行
ls $TASK/metanet4j-component/metanet4j-component-test/target/surefire-reports/
```

关于 `maven-surefire-plugin`：它由 Maven 在 `test` 阶段自动调用，**不需要在本项目 pom 里显式配置**；
版本由 Spring Boot 的 `starter-parent` 的 pluginManagement 提供（当前 Boot 2.3.2 → 2.22.2；
升级到 Boot 4.1.1 后 → **3.5.6**，3.x 才可靠支持 JUnit 5）。核对实际版本：

```bash
$MVN help:effective-pom | grep -A2 maven-surefire-plugin
```
