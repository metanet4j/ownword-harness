# 会话交接

任务结论与唯一下一步见 [progress.md](progress.md)，详细证据见[验收报告](验收报告v0.2.0-20261015-015045.md)。D05 已提交实现，当前为 needs-review；不要重复请求实施许可，也不要把用户视觉复核或外部门禁自动视为通过。

## 恢复环境

- 本目录 `python3 run-services.py start/status/stop/restart` 管理 frontend/api/wallet；最终构建运行在 5071/5073/5078。再次构建前先停止 frontend，构建完成后再启动。
- 私有服务配置和钱包位于忽略目录 `_runtime`，不得打印或提交。当前钱包账户 0，所有故障已解除；准备状态未知的验收操作均已显式放弃，最后的钱包失败为终态，不存在本次遗留的待广播操作。
- `v020-implementation` 浏览器当前 tab t4，1440×1000，英文浅色，已连接到工作台；保留三份验收草稿。旧 tab t2 已在接管验收中关闭。
- `v020-public` 为无钱包公开阅读会话；`v020-final` 为最终构建新建的无钱包阅读会话，无未处理异常。`v020-prototype` 在 4315，对照正文仅修改了该浏览器的原型本地数据，原型仓库未改。
- 浏览器历史错误缓冲区保留前期注入故障与旧构建记录；本 CLI 的 `errors --clear` 没有清除它们。最终异常检查使用全新会话，历史和最终记录分别保存在 evidence/d05。

## 再验注意

使用 agent-browser；CodeMirror 的 CLI `fill` 会插入旧文档前，替换全文应使用真实 Ctrl+A 后输入或编辑器事务。公开测试文章、修订和操作标识已记录在 evidence/d03–d05，无需重新生成资金交易。

前后端 worktree 均为 feature/ownword-v0.2.0，已提交且干净；禁止推送或合并。根目录用户已有的 AGENTS.md、infra、skills-lock 及其他任务改动不属于本任务，继续保留。
