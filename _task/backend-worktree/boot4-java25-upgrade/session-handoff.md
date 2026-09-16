# session-handoff.md — 会话交接

> 唯一起步点：先读 `../AGENTS.md`（共享规则）、`../mvn-command.md`（命令模板）、
> `doc/升级计划-Boot4-Java25.md`（任务事实来源），再读本文件。
> 本文件只写"现在到哪了、下一步做什么、卡在哪"，不复述任务内容。

## 30 秒现状

- 进度：**P0 环境 + P0 基线清理 + P0.5 依赖预取均已完成**；四子仓库仍**零代码改动**（分支 `feature/java21`，0 脏）。
- 状态：`activeItem = null`——**等待用户批准 P1/P2，不要自行开工**（`AGENTS.md` §4 红线）。
- 环境：共享中间件五个容器 healthy；全局工具链未被污染（JDK 8 / Maven 3.9.9 原样）；
  隔离仓库 `~/.m2/metanet4j` 已预取到 **352MB/705 jar**（升级后坐标集 0 失败）。

---

# 本次交接：P0.5 已完成 → 下一项 `boot4-p1-version`（改代码，**需用户批准**）

## 0. 上一步（P0.5 依赖预取）结果

- 状态：**done**（`boot4-p05-prefetch`，`activeItem` 已置 `null`）。
- 产物目录：`/tmp/boot4-prefetch/`（`pom.xml`、`prefetch.log` 1840 行、`resolved-deps.txt`、`trees/full-tree.txt`、`prefetch-summary.md`）。
- 结论：`dependency:go-offline`（2:09）+ `dependency:resolve-plugins dependency:resolve`（6s，新增下载 0 条）
  两次 BUILD SUCCESS；`ERROR|Could not resolve|Failure to find` = 0 行；
  隔离仓库 265MB/516 jar → **352MB/705 jar**；关键坐标逐条版本见 `feature_list.json` 的 evidence。
- 副作用核查：四子仓库 0 脏、`~/.m2/repository` 本次 0 处改动、全局 java/maven current 未变。
- 顺带得到的三条事实（已写入 `progress.md` 关键事实 9–11）：
  1. `spring-kafka` 库版本由 BOM 定为 **4.1.1**，「4.2.1」指 `kafka-clients`（Central 无 spring-kafka:4.2.1）；
  2. `spring-boot-starter-aop:4.1.1` 实测 absent，替代坐标 `spring-boot-starter-aspectj:4.1.1` OK（计划 §6.5 成立）；
  3. ES 9.4.5 客户端 Jackson 2(2.21.5)/3(3.1.5) 并存、无 legacy `elasticsearch-rest-client`；
     Redisson 4.7.0 传递带 `javax.cache:cache-api:1.1.1`（P4 按 D21 排除）。

## 1. 现在为什么不能直接开工

下一项 = **`boot4-p1-version`（版本号统一 0.2.0，纯机械）**。它要改 pom 文件，属于"改代码"；
按 `AGENTS.md` §4 与 `feature_list.json` 的 `note`，**必须由用户明确批准后才能动手**
（历史教训：曾把"选方案"误当"批准开工"，改了 44 个文件后全部回退）。

**向用户请求批准的原话**："请确认是否批准开工 `boot4-p1-version`（版本号统一 0.2.0，纯机械：25 个 pom 的 82 处版本字面量 + `metanet4j.version` 属性 + 13 处 `java.version=11` 覆盖清零）。"

## 2. 批准后照做（改动清单以计划 §6.1 为准）

- 82 处 `<version>0.1.0</version>` → `0.2.0`（全仓版本字面量共 84 处，其中 2 处 `0.2.0` 不动）；
- `metanet4j-parent/pom.xml` 第 14 行 `<metanet4j.version>0.1.0</metanet4j.version>` → `0.2.0`
  （**不在 `<version>` grep 统计内，最容易漏**；漏了会让子模块解析不到 0.2.0 的父 POM）；
- parent depMgmt：`metanet4j-base` 0.1.0→0.2.0；`metanet4j-sdk` 保持 0.2.0；
- 删除 13 处 `<java.version>11</java.version>`（逐文件位置见计划 §6.1）；
- 本次**不引入** `${revision}`（计划已列为后续优化）。

**P1 Gate（任务根目录执行，四条全绿才算完）**

```bash
grep -rn '<version>0\.1\.0</version>' --include=pom.xml . | grep -v /target/ | wc -l        # = 0
grep -rn '<metanet4j.version>0\.1\.0</metanet4j.version>' --include=pom.xml . | wc -l      # = 0
grep -rln '<java.version>11</java.version>' --include=pom.xml . | grep -v /target/ | wc -l   # = 0
find . -name pom.xml -not -path '*/target/*' | wc -l                                          # = 25
```

## 3. 完成后

1. `progress.md`：`Current State` / `What's Done`（增 P1 行）/ `Next`。
2. `feature_list.json`：`boot4-p1-version` → `done`（evidence 附四条门禁命令与输出），`activeItem` → `null`（或按用户续批 P2）。
3. 本文件：换成 `boot4-p2-parent`（同样需批准；注意复评 P1-1 的 `annotationProcessorPaths` 字面量陷阱）。
4. 四个子仓库各自 commit（中文 Conventional Commits）；**不推送远端**。
5. 收工前跑 `./init.sh`，保持 restartable 工作区。

---

## Next Session（后续顺序，做完一项再申请下一项）

1. ✅ `boot4-p05-prefetch`（已完成，0 失败；结论见 `progress.md` 与 `feature_list.json`）
2. `boot4-p1-version` 版本号统一 0.2.0（**下一项**，纯机械，门禁见计划 §6.1）——**改代码，需用户批准**
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
| P1/P2 需用户批准 | 当前 `activeItem=null`，P0.5 已完成；P1（版本号统一）与 P2（父 POM）都改代码，需用户明确批准后才能开工 |
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
