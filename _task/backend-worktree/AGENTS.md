# AGENTS.md — backend-worktree（多仓库后端工作区）

> 本文件是 `_task/backend-worktree/` 下**所有任务共享**的工程与环境说明：仓库布局、Maven 命令、环境准备。
> 具体任务的目标、阶段、改动清单、验证门禁**写在各任务的计划文档里**，不写在本文件。
> 进入某个任务前，先读本文件，再读该任务目录的 `AGENTS.md` 与计划文档。

## 1. 这里有什么

`backend-worktree/` 用 **git worktree** 把同一个后端拆成多个独立仓库，放在一个目录下方便跨仓库改造：

```
backend-worktree/
├── AGENTS.md                      ← 本文件（共享规则）
└── <task>/                        ← 每个任务一个目录
    ├── AGENTS.md                  ← 任务级 harness（开工门禁/DoD/收尾）
    ├── doc/                       ← 该任务的计划与评审
    ├── metanet4j-parent/          ← 独立 Git 仓库（worktree）
    ├── metanet4j-base/            ← 独立 Git 仓库
    ├── metanet4j-sdk/             ← 独立 Git 仓库
    └── metanet4j-component/       ← 独立 Git 仓库（多模块聚合）
```

关键点：

- 每个子目录都是**独立 Git 仓库**（含各自的 `.git`），有各自的提交历史与分支；**不隶属于 ownword 主仓**。
- worktree 里的 `.git` 是**文件**（gitdir 指针），不是目录——脚本判定仓库要用 `git rev-parse --git-dir`，不能用 `-d .git`。
- 四个仓库有**依赖顺序**：`parent` → `base` → `sdk` → `component`，构建必须按此顺序。
- 子模块的 `<parent>` 未写 `relativePath`，**父 POM 必须先 install** 到本地仓库。

## 2. 环境准备

### 2.1 工具链（按任务需要注册，全局默认不动）

| 组件 | 落点 | 说明 |
|---|---|---|
| JDK | `~/.sdkman/candidates/java/<版本>` | 用 `sdk install java` 注册；**不要 `sdk default`** |
| Maven | `~/.sdkman/candidates/maven/<版本>/bin/mvn` | 同上，用绝对路径调用 |

**版本隔离原则**：为某个任务装新版本工具链时，只注册、不切换全局默认。禁止：

- `sdk default java|maven`
- 改 sdkman `current` 软链
- 改 `/etc/profile`、`~/.bashrc`、`~/.zshrc` 里的 `JAVA_HOME`/`PATH`
- `update-alternatives` 改系统 java

其他任务/环境继续使用它们原本的版本；需要哪个版本，就在命令里**显式指定**。

## 3. Maven 命令模板

**永远显式指定 JAVA_HOME；不要用裸 `mvn`**——shell 默认 JDK 可能不是任务需要的版本，裸跑会得到误导性的失败。

```bash
JAVA_HOME=<任务的 JDK 绝对路径> \
<任务的 Maven 绝对路径>/bin/mvn \
  -B clean package          # 跑测试用 clean test
```

若任务需要指定 settings（本地仓库位置、私服等），再加 `-s <settings 绝对路径>`。

判定当前 Maven 实际用的是哪个 JDK：

```bash
JAVA_HOME=<JDK 路径> <mvn 路径> -v | grep 'Java version'
```

**测试一律带 `clean`**：`target/` 里的陈旧字节码会让 surefire 报出与源码不符的结果（曾出现过指向源码中不存在的字段的假 error）。不 clean 的测试结果不可信。

## 4. 共享中间件（跨任务基础设施）

多个任务需要同一套中间件时，**不要各自起容器**，用共享设施。

- 位置：`ownword/infra/`（在 ownword 工作区，不在 `_task/` 下）
- 编排：compose 项目 `ownword-infra`，容器 `infra-mongo` / `infra-es` / `infra-kafka` / `infra-redis` / `infra-mysql`
- 特点：镜像钉到补丁号、五个服务均挂命名数据卷、`restart: unless-stopped`（开机自启）
- 连接信息与凭据的唯一事实来源：该目录下的 `README-*.md`

```bash
cd /home/haodev/ownword/infra
./up.sh        # 启动并等待全部 healthy
./status.sh    # 容器 / 端口 / 版本
./down.sh      # 停止，保留数据
./down.sh -v   # 停止并清空数据（会清掉跨任务数据，慎用）
```

**镜像来源注意**：本机 docker daemon 直连 Docker Hub 不可达，Docker Hub 来源的镜像一律写
`docker.m.daocloud.io/` 全限定名；`docker.elastic.co` 可直连。若接入公司内部 registry，应整体替换。

## 5. Git 约定

- **不擅自改 `dev`/`test`/`master`，不擅自新建分支**；分支策略由各任务计划指定（常见做法：在任务指定的 feature 分支上改）。
- 每个仓库**独立提交**；commit 用中文 Conventional Commits，说明"改了什么、为什么"。
- **不推送远端**，除非用户明确要求。
- 提交前先 `git status --short` 与 `git diff --name-only --cached` 确认范围，不混入无关改动。

## 6. 验证与证据

- 任何"完成"的声明都要附**命令与输出**，不接受"应该没问题"。
- 版本相关的结论**以官方文档为准**（Spring / Kafka / Elasticsearch / MySQL / MongoDB 等），把链接与结论写进任务文档。
- 测试验收不接受"总执行数 > 0"这种口径——按模块给出执行数，并确认关键用例真的被执行。
