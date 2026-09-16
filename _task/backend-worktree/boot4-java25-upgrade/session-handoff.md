# session-handoff.md — 会话交接

> 给下一个会话（或下一个人）看的**唯一起步点**。先读本文件，再读 `AGENTS.md` 与 `feature_list.json`。

## 30 秒了解现状

- 任务：4 仓库 metanet4j 从 **Boot 2.3.2 / Java 11** 升到 **Boot 4.1.1 / Java 25** + 中间件全升。
- 进度：**P0 环境与基线清理已完成**；代码**一行未改**（4 仓库 0 脏）；升级计划与评审已定稿并入库。
- 阻塞：**等待用户批准**开始 P0.5/P1/P2。`feature_list.json` 的 `activeItem` 为 `null` 就是"没在干活"的信号。
- 环境：共享中间件五个容器正在运行；工具链锁定在任务内，全局未动。

## Next Session（唯一下一步，按顺序做完一步再申请下一步）

1. **P0.5 依赖预取**：用升级后的坐标集造探针 pom，预下载依赖，把坐标/网络风险提前暴露
   （本地仓库 `~/.m2/metanet4j` 目前只有约 190MB 探针依赖）。
2. **P1 版本号**：25 个 pom 统一 0.2.0 + `metanet4j.version` 属性 + 13 处 `java.version=11` 清零（纯机械，只改版本号）。
3. **P2 parent**：版本矩阵 + 钉死清理（**lombok 1.18.20 必须换掉，否则 JDK 25 下编译直接崩**）+ compiler/enforcer。
4. 之后 P3（base+sdk）→ P4（component，含 ES 9 与 Redisson 4.7.0 迁移）→ 测试门禁（复评 P0-A/P0-B）→ P5 验证 → P6 收尾。

## 开工自检（每次会话第一件事）

```bash
cd /home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade
./init.sh          # 环境 + 仓库状态（秒级）
./init.sh --full   # 追加真实构建；P2 之前预期失败，属正常
```

## 必须知道的六条硬约束

1. 构建必须用固定模板：`JAVA_HOME=~/.sdkman/candidates/java/25.0.4.1-tem` + `~/.sdkman/candidates/maven/3.9.16/bin/mvn -s ~/.m2/metanet4j-settings.xml -B`。**禁止裸 `mvn`**。
2. **不许改全局** java/maven 默认版本（`sdk default`、`current` 软链、shell 启动脚本都不许动）。
3. 测试一律 `mvn clean test`——**不 clean 的结果不可信**（曾被陈旧字节码骗过，出现 7 个假 error）。
4. **未获批准不改代码**。用户选方案 ≠ 批准开工（这条是踩过坑写下来的）。
5. 中间件用 `ownword/infra/` 的共享设施，**不要自起容器**，**不要 `down -v`**（会清掉跨任务数据）。
6. 本任务**不推送远端**；提交用中文 Conventional Commits，四个子仓库各自提交。

## Blockers（阻塞与未决取舍）

| 项 | 待决内容 |
|---|---|
| 测试迁移方式 | 已选「全新代」（38 个文件迁 Jupiter，含 sdk 14 个）。因越界改动已回退，**重做前需再次明确批准** |
| sdk 那 7 个曾报 NPE 的用例 | 需定性：是迁移引入的问题，还是既有问题（迁移前这些用例从未执行过，无法直接对比） |
| `Archive/prototype/`（207MB 归档） | 未纳入 ownword 版本控制，按约定保留未跟踪 |
| P2 是否连带清理 Jackson 钉死 | 会影响 base 的 `JacksonUtil` 迁移顺序（P3），需确认是否一次做完 |

## Files（关键路径速查）

| 东西 | 位置 |
|---|---|
| 升级计划（唯一事实来源） | `doc/升级计划-Boot4-Java25.md` |
| 两份评审 | `doc/review-升级计划-Boot4-Java25-20260915-1545.md`、`doc/review-...-复评-20260915-1604.md` |
| 共享中间件 | `ownword/infra/`（README 为连接信息唯一事实来源） |
| 本任务约束 | `AGENTS.md`（§4 硬性约束、§5 验证门禁） |
| 功能状态 | `feature_list.json` |
