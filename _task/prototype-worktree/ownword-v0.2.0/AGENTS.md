# v0.2.0 内容原型任务指南

遵循[根 AGENTS.md](../../../AGENTS.md)。本任务只制作高保真交互原型，范围与验收见[版本设计文档](../../system-design/spec/prd/v0.2.0/设计文档v0.2.0-20260917-210556.md)。

## 开工（Startup Workflow）

1. 完整阅读本文件，再读 `feature_list.json`、`progress.md` 和 `session-handoff.md`。
2. 检查根仓库与 `ownword-prototype/` 的 Git 状态，保留他人改动；原型目录必须是 Git worktree。
3. 阅读当前功能对应 PRD 章节；全局事实只查 `../../system-design/spec/核心认知.md`，不读 Archive 或 spec/draft。
4. 运行 `./init.sh` 验证环境。按交接的唯一下一步开始，先记录目标、依赖、验收引用和状态。

## 范围与事实来源

- One feature at a time：只允许一个 `in-progress` 功能。`feature_list.json` 记录依赖与状态，不重复定义 PRD 行为。
- Stay in scope：只处理当前功能。签名、钱包授权、广播、查询和 Proof 使用可控样例，不接真实服务、不读取密钥、不发送交易。
- 页面设计使用 `baoyu-design`，先读原型 `_d_meta.json` 与绑定的 S2 `_ds_prompt.md`；沿用本地 S2，不引入平行视觉系统。
- Markdown 参考本地 xLog 的交互；依赖按 PRD 第 6 节在用到时引入，初始化不安装产品框架或服务 SDK。
- 用户已授权先审查设计文档，审查通过后连续逐项完成 C01–C10；每项独立验证与提交，不把基线截图当成内容功能完成证据。

## 仓库与验证

- `ownword-prototype/` 是独立原型仓库的 worktree。源仓库、基线、分支、版本和 PRD 路径以 `feature_list.json` 的 `environment` 为准。
- 本目录 harness 和版本设计文档提交到根仓库；原型源码与内容功能证据在原型仓库提交，不把 worktree 源码纳入根仓库。
- 原型提交前检查 `prdVersion` 与权威 PRD，提交信息携带 `(PRD v0.2.0_YYYYMMDD-HHMMSS)`；每个功能实现并验证后提交。合并或推送按用户本次授权执行。
- `./init.sh`：路径、分支、S2、状态和依赖、脚本 syntax/lint、现有模型 test，以及 harness 结构检查。只验证这些命令实际覆盖的内容。
- `./init.sh --serve`：前台启动 4312 静态预览；Ctrl+C 结束。日志 `.runtime/preview.log`。端口被占用时不结束其他进程。旧版 4311 独立运行。
- 浏览器验证使用宿主环境的 `agent-browser`。默认一个正常场景与相关边界，查看受影响截图，记录 console/errors；不默认全量回归。
- H00 证据在本目录 `evidence/`；内容功能证据放原型 `evidence/` 并标注 C 编号。运行日志放 `.runtime/`，不提交。

## 完成标准（Definition of Done）

功能实现、适用 BDD 验证、截图及日志审阅完成后，记录 Verification Evidence，提交并标记 `needs-review`。只有用户复核通过才能标记 `done`；没有复核不等于阻塞后续已授权任务。依赖项已实现并验证、无阻塞问题时，可继续后续项。不得把结构评分或模拟发布解释为产品集成验收。

环境须可重复启动（restartable），检查失败不能静默忽略。遇到不明确需求先查 PRD 与核心认知；只有仍阻碍当前范围时再询问，不将生产接入问题带回原型任务。

## 收尾（End of Session）

1. 更新功能状态、实际证据、限制和待复核项；未运行的检查不得记为通过。
2. 更新 `progress.md` 当前结果与 `session-handoff.md` 唯一下一步，不写历史流水账。
3. 同步 `../../system-design/` 三个状态文件的总体进展，细项只引用本任务清单。
4. 显式暂存本任务文件并提交，检查 clean 状态或说明保留的既有改动；保持下一会话可从 `./init.sh` 续接。
