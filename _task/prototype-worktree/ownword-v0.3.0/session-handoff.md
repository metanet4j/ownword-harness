# 当前交接

## 当前目标（Current Objective）

设计审查与 harness 准备已完成，H00 待复核；A01–A09 尚未开始。

## 续接

先读 AGENTS.md、feature_list.json、progress.md；运行 `./init.ps1` 或 `./init.sh`。环境数据以清单为准，产品行为以 PRD 与核心认知为准。

## 唯一下一步（Recommended Next Step）

收到用户后续制作指示后，登记 A01 为唯一进行中事项，更新 `executionScope`，再开始身份入口与 Artifact 工作台。当前不自动续做。

## 文件（Files）与阻塞（Blockers）

环境入口为 `init.ps1`、`init.sh` 和 `bootstrap.mjs`，登记在[功能清单](feature_list.json)。验证证据见[环境检查](evidence/environment-check.json)及其引用的日志、截图。根仓库保存 harness 与设计资料，原型 worktree 保持基线干净状态。

当前没有模拟原型制作阻塞。S2 仅恢复消费副本，完整生成工程不在本轮恢复范围；生产能力待验证项仍以核心认知第 12 节为准。

预览运行于清单登记的本地地址，生命周期由启动终端管理；终端关闭后可执行 `./init.ps1 -Serve`，Git Bash 使用 `./init.sh --serve`。先检查现有预览，不终止占用端口的其他进程。
