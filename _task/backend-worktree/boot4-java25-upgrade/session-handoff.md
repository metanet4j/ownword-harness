# session-handoff.md — 会话交接

> 唯一起步点：先读 `../AGENTS.md`（共享规则）与 `doc/升级计划-Boot4-Java25.md`（任务事实来源），再读本文件。
> 本文件只写"现在到哪了、下一步做什么、卡在哪"，不复述任务内容。

## 30 秒现状

- 进度：**P0 环境与基线清理已完成**；代码**零改动**（四子仓库 0 脏、分支 `feature/java21`）。
- 状态：`feature_list.json` 的 `activeItem = null`，即**等待用户批准**开始 P0.5/P1/P2。
- 环境：共享中间件五个容器 healthy；全局工具链未被污染。

## Next Session（唯一下一步，按顺序做完一步再申请下一步）

1. `boot4-p05-prefetch` 依赖预取——本地仓库目前只有约 260MB 探针依赖，项目依赖树从未下载。
2. `boot4-p1-version` 版本号统一 0.2.0（纯机械，门禁见计划 §6.1）。
3. `boot4-p2-parent` 父 POM 改造——**lombok 1.18.20 必须换掉，否则 JDK 25 下编译直接崩**。
4. 之后：P3（base+sdk）→ P4（component，含 ES 9 与 Redisson 4.7.0）→ 测试门禁（复评 P0-A/P0-B）→ P5 验证 → P6 收尾。

## 开工自检

```bash
cd /home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade
./init.sh          # 环境 + 仓库状态（秒级）
./init.sh --full   # 追加真实构建；P2 之前预期失败，属正常进度
```

## Blockers（阻塞与未决取舍）

| 阻塞/取舍 | 说明 |
|---|---|
| 等批准开工 | P0.5/P1/P2 均未开始；用户明确"选方案 ≠ 批准开工" |
| P2 与测试门禁互相牵扯 | 测试门禁（`boot4-tests-jupiter`）**依赖 P2**：不改 parent 的 lombok 与测试依赖，测试根本跑不起来 |
| sdk 那 7 个曾报 NPE 的用例 | 需定性：是迁移引入还是既有问题（迁移前这些用例从未执行，无法直接对比） |
| Jackson 钉死何时清理 | 影响 base `JacksonUtil` 的迁移顺序（P3），需确认是否一次性做完 |
| `Archive/prototype/`（207MB 归档） | 按约定未纳入 ownword 版本控制 |

## Files（关键路径）

| 内容 | 位置 |
|---|---|
| 共享工程/环境规则 | `../AGENTS.md` |
| 任务事实来源（目标/版本矩阵/决策/改动清单/门禁） | `doc/升级计划-Boot4-Java25.md` |
| 问题定性与评审 | `doc/review-升级计划-Boot4-Java25-20260915-1545.md`、`doc/review-...-复评-20260915-1604.md` |
| 共享中间件（连接信息唯一事实来源） | `ownword/infra/` |
| 阶段状态 | `feature_list.json` |
