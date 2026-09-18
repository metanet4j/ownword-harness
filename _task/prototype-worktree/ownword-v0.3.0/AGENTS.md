# v0.3.0 Identity Artifact 原型任务指南

遵循[根 AGENTS.md](../../../AGENTS.md)。产品事实只查[核心认知](../../system-design/spec/核心认知.md)，功能与验收只查[版本设计文档](../../system-design/spec/prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)。本文件约束执行过程，不重写设计规则。

## 开工（Startup Workflow）

1. 完整阅读本文件、`feature_list.json`、`progress.md`、`session-handoff.md`。
2. 检查根仓库与 `ownword-prototype/` 的 Git 状态，保留他人改动；读取当前功能对应 PRD。
3. 运行 `./init.sh`，Windows 使用 `./init.ps1`，先处理实际失败再继续。
4. 按唯一下一步推进，先登记目标、依赖、验收和状态，不从聊天记录猜测已完成项。

## 范围与授权

- One feature at a time：同时只允许一个 `in-progress` 功能，`activeFeature` 与其一致。
- Stay in scope：用户已授权连续完成 A01–A09。按依赖逐项实施、验证和提交，完成一项即继续下一项；人工视觉复核前保留 `needs-review`，不因此中断后续功能。
- 身份、签名、交易、编号、ownership 与 Binding 均为可控样例；不接真实钱包，不读取密钥，不发送真实交易，不实现 metanet4j。
- 页面制作使用 `baoyu-design`，先读原型 `_d_meta.json` 和绑定的 `_ds/react-spectrum-s2/_ds_prompt.md`。只复用该 S2 的 bundle、组件和 token。
- `designs/react-spectrum-s2/` 是从基线恢复的消费副本，不包含完整生成工程；本任务不升级 S2 或重新生成该系统。
- 不读取 Archive、归档内容或 `spec/draft`。生产能力缺口查核心认知第 12 节，不将其误判为模拟原型阻塞。

## 仓库与环境

- `ownword-prototype/` 是独立原型仓库的 Git worktree。基线、分支、PRD、端口及日志以 `feature_list.json` 的 `environment` 为准。
- harness、审查报告和任务状态提交到根仓库；原型源码与功能证据只在原型仓库提交。不要把 worktree 源码加入根仓库。
- 原型提交信息带 `(PRD v0.3.0_YYYYMMDD-HHMMSS)`；每完成一个功能即验证并提交。合并、推送遵循用户授权。
- Node.js、Git、Python 是检查和预览工具。基线已包含浏览器 bundle，初始化不安装业务依赖；只有修改编辑器打包入口时才按原型锁文件安装并构建。

## 验证（Verification Commands）

- `./init.ps1` 或 `./init.sh`：验证登记、worktree、PRD、全部验收引用、依赖关系、S2 资源、JS/JSX 语法、身份、内容及 Artifact 模型，以及 harness 结构。检查不改变原型文件。
- 模型测试（model tests）可单独运行 `node ownword-prototype/check-model.cjs` 与 `node ownword-prototype/check-content.cjs`；Artifact 模型检查为 `node ownword-prototype/check-artifact.cjs`。三项均包含在启动检查中；浏览器证据另见功能清单。
- `./init.ps1 -Serve` 或 `./init.sh --serve`：检查后前台启动本地预览。日志位置见任务清单；Ctrl+C 停止。端口占用时失败并说明，不终止其他进程。
- 浏览器操作使用宿主环境的 `agent-browser`，使用独立 session；基线正常页面和一个相关边界即可，不把基线验证当作 Artifact 验收。
- 后续每项验证适用 BDD，默认正常场景、相关边界与受影响截图；扩大范围须有实际原因。签名、重组和存储边界按 PRD 的明确验收执行。
- H00 证据放本任务 `evidence/`；后续功能证据放原型 `evidence/`，以功能编号映射。运行日志放 `.runtime/`，不提交。

## 完成标准（Definition of Done）

实现、适用验证、截图和日志审阅、提交全部完成后才记录 `implemented-and-verified` 并标记 `needs-review`；人工复核前不标记 `done`。设计审查结果、初始化检查、用户视觉复核与生产验证分别记录。结构评分不能代替启动和浏览器证据。

环境必须 restartable。检查失败不静默忽略；状态文件只保存当前状态，不追加历史流水账。

## 收尾（End of Session）

1. 更新本任务 `feature_list.json` 的状态和 Verification Evidence，未运行的检查不得记为通过。
2. 更新 `progress.md` 与 `session-handoff.md`，保留唯一下一步及真实限制。
3. 同步 `../../system-design/` 的总体状态，功能细项只引用本任务清单。
4. 只暂存本任务文件并提交，检查 clean 状态或报告保留的既有改动。
