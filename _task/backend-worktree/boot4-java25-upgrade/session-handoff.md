# session-handoff.md — 会话交接

## 30 秒现状

当前目标是四个子仓库完整的单元测试与集成测试。用户已明确要求实施，`unit-u0-baseline` 正在进行；`tdd` 技能要求的公共接口边界确认已发出，测试代码尚未编写。

起步时读取 `../AGENTS.md`、`../mvn-command.md`、本目录 `AGENTS.md`、[升级计划](doc/升级计划-Boot4-Java25.md)、[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md) 和 `feature_list.json`，然后运行 `./init.sh`。

测试计划已扩展到集成测试与共享资源隔离。四子仓库均在 `feature/java25` 且工作区干净；parent JaCoCo 配置已提交为 `4112a48`。`verify-unit.py --mode baseline --scope metanet4j-base` 已端到端通过并保存证据：2 个用例，行 35/225、分支 6/78、方法 6/55；严格检查预期失败。宿主 `infra/status.sh` 确认五服务健康。其余模块仍只留有 2026-09-16 旧报告。

## Blockers（阻塞与待确认）

- **测试接口确认**：用户已授权代码实施；`tdd` 技能要求写测试前确认公开接口边界，已发送包含四仓库公共 API 和集成服务的具体边界请求。
- **覆盖率待扩展**：base 基线已采集；其余模块尚无当前覆盖率。`unit-test-inventory.json` 列齐 25 POM、369 个生产文件和 52 个测试文件，但只有 parent/base 分类复核完成。
- **环境与隔离**：`./init.sh` 退出 0；其沙箱内中间件检查告警，提权运行 `infra/status.sh` 已确认五服务 healthy、端口可达。现有 `EsTest#recreateIndex` 会删除固定索引，旧集成测试不能直接作为新门禁；测试前确认日志、连接及隔离资源。
- **报告口径**：文件模块旧 XML 为 8 个全部跳过，实际通过数 0；历史“8 通过”表述不能继续沿用。其余遗留测试去向见测试计划 §2。

## Files（关键路径）

| 内容 | 位置 |
| --- | --- |
| 新增测试范围、逐模块清单、阶段与验收 | `doc/单元测试全覆盖计划-20260920-090603.md` |
| 计划评审结论与依据 | `doc/review-单元测试全覆盖计划-20260920-091540.md` |
| 原升级约束与验收依据 | `doc/升级计划-Boot4-Java25.md` |
| 任务规则与工具链 | `AGENTS.md`、`../AGENTS.md`、`../mvn-command.md` |
| 当前阶段状态 | `feature_list.json` |
| 当前进度与验证说明 | `progress.md` |
| U0 分类与证据入口 | `unit-test-inventory.json`、`verify-unit.py`；本地 `evidence/20260926T061230Z/` 与反例证据 `evidence/20260926-u0-pilot/` |
| 共享设施连接信息 | 工作区 `infra/README-*.md` |

## Next Session（唯一下一步）

收到公开接口边界确认后，按测试计划 §4.4 完成其余测试分类，修正未标注联网用例，并从安全的单元集逐模块采集基线。parent JaCoCo profile 已实测继承；`verify-unit.py` 已用 base 证据验证五类缺失／跳过反例均返回非零，后续还需核对全仓测试发现、生成代码与集成资源。复用现有 Jupiter/Mockito；不并行推进多个功能项，不擅自新建分支，不推送。

每项完成后按仓库独立提交、记录实测证据并同步三个状态文件。最终验收必须同时满足覆盖率和实际执行账目，不能以 BUILD SUCCESS 或被排除的外部用例代替单元测试通过。
