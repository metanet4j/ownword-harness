# 会话交接

## 当前目标（Current Objective）

v0.4.0 个人主页原型及 R01–R05 公开个人网站调整已交付，当前入口为 `http://127.0.0.1:4314/profile.html`。状态与唯一下一步见 [progress.md](progress.md)，逐项提交及证据见 [feature_list.json](feature_list.json)，验收范围见[交付说明](交付验收v0.4.0-20261002-183602.md)。

用户明确要求从本轮起不使用任何子代理，后续设计、实施与验证均由主代理直接执行。

## 恢复入口（Next Session Startup）

1. 按 [AGENTS.md](AGENTS.md) 读取依据和当前状态，核对 `ownword-prototype` 分支及工作区差异。
2. 在本目录运行 `./init.ps1`；需要重启预览时先核实 `.runtime/server.json`，再使用 `./init.ps1 -Serve`。端口为 4314。
3. 当前没有待实施功能。依据胡先生后续复核意见登记调整项，再进入实施。

## 文件与边界（Files / Blockers）

任务状态与交付说明由根仓库管理；源码、构建产物及浏览器证据在独立原型 worktree。仅有人工视觉复核尚未进行，无已知实现阻塞。旧版 4313 预览未改动。
