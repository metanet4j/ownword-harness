# 会话交接

## 当前目标（Current Objective）

完成 v0.4.0 个人主页原型。状态与唯一下一步见 [progress.md](progress.md)，功能依赖和验收引用见 [feature_list.json](feature_list.json)。

## 恢复入口（Next Session Startup）

1. 按 [AGENTS.md](AGENTS.md) 读取依据及当前状态，核对 `ownword-prototype` 的分支、HEAD 与工作区差异。
2. 本目录运行 `./init.ps1` 或 `./init.sh`；需要预览时使用 `-Serve` 或 `--serve`，端口为 4314。
3. 先核实 `.runtime/server.json` 中的预览进程，再决定复用或重启；只推进清单允许的下一项。

## 文件与阻塞（Files / Blockers）

- 任务规则、初始化和证据位于本目录；界面源码在 `ownword-prototype`，两者由主代理分别提交。
- 当前没有需要用户决定的阻塞；待人工视觉复核的功能保持 `needs-review`。
