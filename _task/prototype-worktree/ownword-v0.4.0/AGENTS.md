# v0.4.0 原型任务规则

## 开工（Startup Workflow）

1. 读取根规则、[核心认知](../../system-design/spec/核心认知.md)、[设计指南](../../../standard/OwnWord设计与设计系统.md)、[v0.4.0 PRD](../../system-design/spec/prd/v0.4.0/设计文档v0.4.0-个人主页-20260918.md)及[设计审查](设计审查v0.4.0-20261002-174225.md)。领域事实只引用这些来源。
2. 读取 [feature_list.json](feature_list.json)、[progress.md](progress.md)、[session-handoff.md](session-handoff.md)，核对原型分支与最近提交。
3. 在本目录运行 `./init.ps1` 或 `./init.sh`。失败时先修复或明确记录基线失败，再实施新功能。

## 范围与顺序（Scope）

- **One feature at a time**：仅一个功能可为 `in-progress`，按清单依赖推进 H00、P01–P06；状态唯一来源是 `feature_list.json`。
- 用户已授权连续完成 P01–P06。功能实现并验证后标记 `needs-review`、提交并继续下一项；此状态表示等待人工视觉复核，不构成暂停授权。只有用户确认后才标记 `done`。
- 原型仅修改 `ownword-prototype` worktree；任务规则、状态和证据留在本目录。原型与父仓库分别提交本任务改动，不纳入用户或其他任务的修改。
- 绑定 `ReactSpectrumS2_ad4872` 的现有 S2 轻量消费副本，禁止升级或修改 `_ds`。不新增生产服务、钱包或协议实现；新增范围先登记再实施。

## 验证与完成（Definition of Done）

- 完成清单行为与验收引用；PRD 只有两项标题 BDD，禁止沿用其他版本的编号或条数。
- 运行 `npm run build` 更新受影响的原型产物，再运行 `./init.ps1`（含 build 新鲜度、模型 test、UI 与 harness 检查）。纯文档调整不重复构建。
- 用 agent-browser 实测受影响路径的正常、失败或边界状态；按影响覆盖桌面、手机、中文、深色、键盘、浏览器错误与无障碍。截图前移开指针，记录实际结果及工具未判定项。
- **Verification Evidence**：保存命令与输出、截图和中文结论，清单引用真实证据后才可转为 `needs-review`。自动检查不等于人工视觉批准，也不代表获奖认定。

## 收尾与恢复（End of Session）

- 更新当前状态、阻塞和唯一下一步，不追加历史；在 `session-handoff.md` 留下恢复入口。
- 每个完成并验证的功能独立提交；子代理只交付获委派文件，由主代理复核、维护状态与提交。
- 保持可恢复（restartable）：`./init.ps1 -Serve` 或 `./init.sh --serve` 在 `http://127.0.0.1:4314/` 启动，日志与进程记录位于 `.runtime`。端口占用先核实所属任务，不终止未知进程。
