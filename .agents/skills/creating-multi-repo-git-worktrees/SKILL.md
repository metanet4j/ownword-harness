---
name: creating-multi-repo-git-worktrees
description: Use when one task spans 2+ Git repositories and requires a combined worktree layout, per-repository base branch control, compile-or-package verification without tests, independent commits, and a consolidated delivery report.
---

# 创建多仓库 Git Worktree

## 概览

该技能用于“一个业务任务影响多个 Git 仓库”的场景。

**核心原则：** 目录组织统一在任务根目录下，但开发、验证、提交必须按仓库隔离。

## 何时使用

- 一个任务涉及 `2+` 仓库，需要组合 worktree。
- 仓库不一定都在同一个固定根目录下，需要通用路径算法。
- 分支策略是“默认基线分支 + 仓库级覆盖”。
- 验证只允许 `compile` 或 `package -DskipTests`，禁止 `mvn test`。
- 最终要按仓库输出编译命令和提交 ID。

单仓库任务不使用本技能。

## 输入参数

必填：

- `task_name`：任务名。
- `business_goal`：业务目标。
- `repos[]`：仓库绝对路径列表。

可选：

- `parent_repo`：父仓库（仅在需要提交子仓库指针时使用）。
- `task_root`：任务根目录。传入则直接使用。
- `layout_anchor`：显式相对路径锚点。
- `default_base_branch`：默认 `master`。
- `repo_base_overrides`：仓库级基线分支覆盖映射。
- `task_name_en`：任务名英文 slug。未传时自动从 `task_name` 转换。
- `change_type`：Conventional Commits 类型（如 `fix`、`feat`）。未传时按任务语义推断。

## 任务名默认转英文规则

1. 若传入 `task_name_en`，直接使用。
2. 若未传，默认从 `task_name` 转为英文 slug：
   - 优先语义英文翻译（例如 `医保上传重试` -> `medical-upload-retry`）。
   - 若短时间无法精确翻译，使用拼音转写再 kebab-case。
3. slug 规范：小写、仅保留 `a-z` `0-9` `-`，连续 `-` 折叠为一个。
4. 若转换后为空，回退为 `task-<timestamp>`。

## 分支命名与提交规范（Conventional Commits 1.0.0 中文）

来源：<https://www.conventionalcommits.org/zh-hans/v1.0.0/>

分支命名：

- 格式：`<type>/<task_name_en>-<repo_slug>`。
- `type` 必须使用 Conventional Commits 类型集合：
  - `feat` `fix` `docs` `refactor` `perf` `test` `build` `ci` `chore` `style` `revert`
- 新功能必须使用 `feat`。
- 缺陷修复必须使用 `fix`。

提交信息：

- 标题格式：`<type>[optional scope][!]: <description>`。
- `type` 必填，`scope` 可选，冒号后必须有空格。
- 若有正文或脚注，必须保持规范空行。
- 破坏性变更使用 `!` 或 `BREAKING CHANGE:`。

## 通用路径规划（不绑定固定路径）

### 1）确定布局锚点

按以下优先级：

1. `layout_anchor`（且所有仓库都在其下）。
2. `parent_repo`（且所有仓库都在其下）。
3. `repos[]` 的最长公共祖先目录。
4. 若公共祖先过宽（例如仅 `/`），切换为 `absolute-layout` 模式。

### 2）确定任务根目录

- 传入 `task_root`：直接用。
- 未传且存在锚点：`<anchor>/_tasks/<task_name_en>`。
- 无有效锚点（absolute-layout）：`<current_working_directory>/_tasks/<task_name_en>`。

### 3）映射仓库目标路径

- 有锚点：`repo_rel = relative(repo_abs, anchor)`。
- absolute-layout：`repo_rel = strip-leading-slash(repo_abs)`。
- worktree 目标：`wt_path = <task_root>/<repo_rel>`。

这样可以在任意目录结构下保持稳定映射，不写死 `/home/...`。

## 执行流程

1. 从 `task_name` 解析 `task_name_en`（未传则默认转英文）。
2. 解析 `change_type`：
   - 新功能用 `feat`，缺陷修复用 `fix`。
   - 其他类型按实际变更选择 `docs`/`refactor`/`perf`/`test`/`build`/`ci`/`chore`/`style`/`revert`。
3. 校验每个 `repo` 路径存在且是 Git 仓库。
4. 对每个仓库执行 `git status --short` 检查脏工作区。
5. 若存在无关改动，先确认“忽略并仅暂存任务文件”或“停止”。
   - 若用户明确要求“不提问直接执行”，默认选择“忽略无关改动 + 仅暂存任务文件”，并在最终报告记录该决策。
6. 用通用算法确定锚点与任务根目录。
7. 创建任务根目录和每仓库目标路径，保持相对结构。
8. 按仓库解析基线分支：
   - 优先 `repo_base_overrides[repo]`，否则 `default_base_branch`（默认 `master`）。
   - 先查本地分支，再查 `origin/<base>`。
   - 若仍不存在，回退到 `origin/HEAD` 对应默认分支，并在报告标记 fallback。
9. 为每个仓库创建独立分支与 worktree：
   - 分支名：`<change_type>/<task_name_en>-<repo_slug>`。
   - 必须仓库独立，禁止共用同一分支上下文。
10. 对 worktree 根目录（`_tasks`）执行 `AGENTS.md` 补齐检查：
   - 若 `<tasks_root>/AGENTS.md` 不存在，则从“当前工作根目录”的 `AGENTS.md` 复制到 `<tasks_root>/AGENTS.md`。
   - `tasks_root` 取值为 `<anchor>/_tasks`（例如 `/home/haodev/worksapces/_tasks`）。
   - 若当前工作根目录缺少 `AGENTS.md`，在报告中记录 warning，不阻塞后续流程。
11. 在各自 worktree 中实现改动。
12. 按仓库独立验证（仅以下两类）：
   - `mvn ... compile -DskipTests`
   - `mvn ... package -DskipTests`
13. 按仓库独立提交，提交信息遵循 Conventional Commits。
14. 若 `parent_repo` 产生子仓库指针变更，再单独提交父仓库。
15. 输出最终报告：受影响仓库、编译命令、提交 ID。

## 命令模板

### 计算公共锚点（Python）

```bash
python3 - <<'PY'
import os

repos = [
    "/path/repo-a",
    "/path/repo-b",
]
print(os.path.commonpath(repos))
PY
```

### 创建并映射单仓库 worktree（保持相对结构）

```bash
task_name="医保上传重试"
task_name_en="medical-upload-retry"
change_type="fix"
task_root="/path/to/_tasks/$task_name_en"
anchor="/path/to/anchor"
repo_abs="/path/to/anchor/server/yt-plat"
base_branch="master"
branch_name="$change_type/$task_name_en-yt-plat"

repo_rel="$(python3 - <<'PY'
import os
print(os.path.relpath('/path/to/anchor/server/yt-plat', '/path/to/anchor'))
PY
)"
wt_path="$task_root/$repo_rel"

mkdir -p "$(dirname "$wt_path")"
git -C "$repo_abs" worktree add "$wt_path" -b "$branch_name" "$base_branch"
```

### 若 `_tasks` 缺失则补齐 AGENTS.md

```bash
current_root="$(pwd)"
source_agents="$current_root/AGENTS.md"
tasks_root="/home/haodev/worksapces/_tasks"
target_agents="$tasks_root/AGENTS.md"

if [ ! -f "$target_agents" ]; then
  if [ -f "$source_agents" ]; then
    cp "$source_agents" "$target_agents"
  else
    echo "WARN: missing $source_agents, skip AGENTS.md copy for $tasks_root"
  fi
fi
```

### Maven 编译验证（禁止测试）

```bash
mvn -s /home/haodev/.m2/whyt-server-settings-linux.xml \
  -DskipTests \
  -DskipAssembly=true \
  -Dmaven.assembly.skipAssembly=true \
  compile

# 或
mvn -s /home/haodev/.m2/whyt-server-settings-linux.xml \
  -DskipTests \
  -DskipAssembly=true \
  -Dmaven.assembly.skipAssembly=true \
  package
```

### 独立提交

```bash
git add <task-related-files>
git commit -m "fix(module): brief description"
git rev-parse --short HEAD
```

## 报告模板

```text
任务：<task_name>
任务英文名：<task_name_en>
目标：<business_goal>

受影响仓库：
1) <repo-1>
2) <repo-2>

编译命令：
- <repo-1>: <compile-or-package-command>
- <repo-2>: <compile-or-package-command>

提交 ID：
- <repo-1>: <sha>
- <repo-2>: <sha>
- <parent_repo>: <sha 或 N/A>

基线分支说明：
- <repo>: requested <base>, resolved <actual-base>, fallback <yes/no>

分支命名说明：
- <repo>: <type>/<task_name_en>-<repo_slug>
```

## 常见合理化借口

| 借口 | 事实 |
| --- | --- |
| "路径很固定，直接写死 `/home/...`" | 跨仓库任务常发生在不同根目录，必须动态解析锚点。 |
| "多个仓库用同一个分支名就够了" | 每仓库都要独立分支与提交，便于隔离回滚。 |
| "分支名用 hotfix 开头就行" | 分支前缀必须与 Conventional Commits 类型一致（如 `fix`、`feat`）。 |
| "为了保险跑一次 `mvn test`" | 本流程明确禁止测试，只允许 compile/package 且跳过测试。 |
| "父仓库无论如何都提交一次" | 仅在父仓库确实有子仓库指针变更时提交。 |
| "脏改动先不管" | 必须先处理脏工作区策略，且只暂存任务相关文件。 |

## 红旗

严禁：

- 写死单一路径根。
- 跳过 `task_name` 到英文 slug 的默认转换。
- 破坏相对目录结构。
- 多仓库混合提交。
- 在本流程中执行 `mvn test`。
- 跳过仓库级编译验证。
- 父仓库无变更仍强行提交。

必须：

- 使用通用锚点解析。
- 分支命名与提交信息统一遵循 Conventional Commits。
- 仓库级分支/基线独立决策。
- 仓库级独立验证与提交。
- 若 `_tasks` 目录缺少 `AGENTS.md`，从当前工作根目录复制同名文件补齐。
- 最终输出仓库级编译命令和提交 ID。

## 快速参考

| 场景 | 动作 |
| --- | --- |
| `task_name_en` 未提供 | 默认将 `task_name` 转英文 slug 后使用。 |
| 任务类型是修复 | 分支和提交 `type` 必须使用 `fix`。 |
| 任务类型是新功能 | 分支和提交 `type` 必须使用 `feat`。 |
| 传入 `task_root` | 直接使用，不再推导。 |
| 未传 `task_root` 且有锚点 | 用 `<anchor>/_tasks/<task_name_en>`。 |
| 无有效公共锚点 | 切换到 absolute-layout。 |
| 某仓库有基线覆盖 | 仅覆盖该仓库。 |
| 请求基线分支不存在 | 回退 `origin/HEAD` 默认分支并记录。 |
| `_tasks` 目录缺少 `AGENTS.md` | 从当前工作根目录复制 `AGENTS.md` 到 `_tasks` 目录；若源文件不存在则记录 warning。 |
| 父仓库无指针变化 | 报告父仓库提交为 `N/A`。 |
| 用户要求不提问且工作区脏 | 默认忽略无关改动，仅暂存任务文件，并在报告说明。 |

## 常见错误

- 相对路径用当前 shell 目录计算，而不是锚点目录。
- 分支名仍用 `hotfix/...`，而不是 `<type>/<task_name_en>-<repo_slug>`。
- 多个仓库误用同一 worktree 目标路径。
- 未在报告中记录基线分支 fallback。
- `_tasks` 缺少 `AGENTS.md` 时未执行补齐或未记录 warning。
- 着急提交时把无关脏改动一起暂存。
- Maven 命令漏掉 `-s /home/haodev/.m2/whyt-server-settings-linux.xml`。
