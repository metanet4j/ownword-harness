# AGENTS.md — ownword-v0.1.0（前端任务 harness）

> 工作区级规则见 `/home/haodev/ownword/AGENTS.md`（沟通、文档、Working Rules、开工门禁）。本文件只写本任务目录特有的内容。

## 1. 这里有什么

- 路径相对本文件所在目录：`own-word-web/` 是目标任务 worktree。实际基线、Git 恢复情况及后端 worktree 以 `feature_list.json` 的 environment 为准。
- 远程：`https://github.com/metanet4j/ownword-web.git`
- 任务分支：`feature/ownword-v0.1.0`。用户已授权后端现有成果先合入 dev，再从 dev 建立版本 worktree；前端保留指定路径与既有源码。

## 2. Startup Workflow 开工

1. `pwd` 确认在本目录。
2. 读工作区根 `AGENTS.md`。
3. 读 `../README.md`（仓库与 worktree 清单）。
4. 完整读取 `feature_list.json`、`progress.md` 和 `session-handoff.md`，按 documents 加载认知及设计；运行 `./init.sh --plan`，环境阶段后运行 `./init.sh`。
5. One feature at a time：activeItem 对应唯一 in-progress 项，先检查仓库状态，保留他人改动。独立执行，不使用子代理。

## 3. 范围与验证

- Scope boundary：实施 v0.1 身份闭环，不修改指定原型。完整认知、接口与 mock 边界只定义在 documents 指向的文档中。
- 后端本地合并及版本 worktree 已按用户授权完成。当前停在文档审阅阶段；用户明确开工前只处理核心认知和设计反馈，不继续业务开发。实际授权及状态见 feature_list.json；不推送远端。
- Verification commands：`./init.sh --plan` 检查任务和文档；`./init.sh` 检查实际 Git worktree。源码改动运行当前 package 中 lint、typecheck、test、build；尚未存在的命令先实现再登记，不声称已通过。
- 后端按共享 Maven 规范显式设置 JDK，真实测试不使用响应 Mock。集成测试、命令、退出码和逐项来源记录到 evidence；主网发布待资金时只完成不依赖资金部分。
- Definition of done：实现、实际检查、日志/截图核查、相关仓库提交及可重复运行说明齐备。模拟流程不关闭主网 I08/I09；整项未满足全部验收时不标记 done。设计文档人工复核前保持 needs-review，但不阻塞已授权实现。

## 4. 收尾

- 前端代码在 `own-word-web/` 内提交，任务文档在根仓库提交，均用中文 Conventional Commits。
- 不擅自改 `master`、不擅自新建分支、不推送远端（除非用户明确要求）。
- End of session：更新 feature_list、progress、session-handoff，保留唯一下一步和可 restartable 的环境。每完成一个功能项独立提交，仅纳入本任务改动。
