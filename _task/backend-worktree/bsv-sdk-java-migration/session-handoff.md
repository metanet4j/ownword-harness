# 会话交接

## 状态

TypeScript 环境准备已验收；用户要求的测试一比一复刻已写入测试迁移契约。Java 生产移植与测试复刻尚未开始。

## Files

- `workspace.json`：四仓 feature/java25 起点、迁移分支、TS 固定提交与工具版本。
- `README.md`、`init.sh`、`mvn.sh`、`pnpm.sh`、`verify.sh`：环境使用与验证入口。
- `upstream-tests.json`、`inventory-tests.py`：测试文件及辅助向量清单，含校验值；不是已完成的逐用例映射。
- `doc/环境检查报告-20260920-101559.md`：实测命令、结果与未验证范围。
- `doc/测试迁移契约-20260920-101559.md`：用户要求的 TDD、一比一复刻和零遗漏门禁。

## Blockers

环境无阻塞。架构实施前仍需收敛公共 core 落点与公开 Java 类型兼容；现有授权覆盖环境和迁移准备，不能将本轮验证自动视作公共模块拆分批准。

## Next Session

读取本目录 AGENTS.md、README.md、feature_list.json、测试迁移契约，运行 ./init.sh。将 migration-map 设为进行中，按实际调用建立模块/接口和逐用例映射，明确所有上游测试文件的范围归属；默认被排除的 AESGCM.man.test.ts 必须有去向，不静默遗漏。

开始新增 Java 测试前，具体接口边界须满足 tdd 技能要求；按用户指定上游测试逐项映射，任何尚未确认的接口差异须先解决。一次只写一个失败测试并实现使其通过，保留 RED/GREEN 证据。全部 Java 对应测试实际通过且逐项核对无遗漏之前，不得标记迁移完成。

四个 worktree 保持 feature/java25 起点，未改 Java/POM，未推送。根仓既有无关规则/技能修改继续保留，不混入本任务提交。
