# system-design 任务指南

本目录只用于 PRD 与实现设计。业务事实、任务状态、验证证据分开记录。

## 目录说明
根目录 ownword
其余路径采用相对路径

## 原型预览

```powershell
python -m http.server 4311 --bind 127.0.0.1 --directory ownword\designs
```

访问 `http://127.0.0.1:4311/<项目目录>/`。

## Git 仓库结构

- 根仓库 `ownword` 只跟踪文档与任务文件；`.gitignore` 忽略 `designs/*`。
- `designs/` 下每个目录是独立 Git 子仓库，各自提交：`bsv-identity-studio-v1`、`react-spectrum`（设计系统）、`own-word-prototype`、`-002`、`-003`、`-004`（各套原型）。
- 改原型：进对应子目录提交，不动根仓库。
- 改任务文档（AGENTS.md、feature_list.json、progress.md、session-handoff.md）：在根仓库提交。

## Git 提交规则

- `designs/` 下各子仓库每次 Git commit 信息必须带当前 PRD 版本号，格式 `(PRD v0.1_${datetime})`；根仓库提交不受此限。
- 版本号不明时先向用户确认，确认前禁止提交。

## 开工顺序

1. 确认工作目录为 `_task\system-design`。
2. 完整阅读本文件。
3. 阅读 `feature_list.json`、`progress.md`；续接任务时再读 `session-handoff.md`。

未完成以上步骤，不得修改设计文档。

## 产出目录

- 核心认知 定义系统的核心认知，是原型，prd，后端设计的核心知识来源  `system-design\spec\核心认知.md`
- 可交互高保真原型 替代大部分PRD描述 目录 `designs\own-word-prototype`
- prd 描述无法可靠表达的产品事实 目录 `_task\system-design\spec\prd`
- 后端设计文档 后端架构设计与详细实现设计 `_task\system-design\spec\backend` 
- 设计系统，进行高保真原型设计时必须使用 设计系统 默认选择 `designs/react-spectrum-s2`

## 事实来源

- 当前设计文档记录该事项的需求与实现设计。
- `feature_list.json` 只记录事项范围、状态、依赖和完成证据。
- `progress.md`、`session-handoff.md` 只记录过程与交接，不承载设计事实。

- 设计结论必须引用 `reference`目录 或其他明确证据。资料冲突时停止相关结论，记录冲突并请用户裁决。
- 不允许读取 draft的内容  `task\system-design\spec\draft`

## 工作规则

- 同时只允许一个 `in-progress` 事项。开始前先在 `feature_list.json` 写清目标、依赖、完成条件。
- 不凭代码片段下结论。涉及现有系统时，结合设计文档、代码、日志、数据或最小实验取证；本目录不修改代码。
- 未确认信息标为“待确认”，写明负责人或验证方式。禁止把假设写成事实。
- 架构决策先查 `_task\system-design\spec` 和 `reference`；仍无依据再问用户。
- 遵守 DRY：同一知识只在一个权威位置定义，其他文档用路径和章节链接引用。
- 修改范围限于当前事项。未经用户要求，不修改 `spec`、`reference`、`designs`、`backend` 或任何代码。
- 原型设计 必须使用设计系统和 Baoyu Design 技能，未发现设计系统和技能则停止原型设计，并向用户反馈


## 原型验证范围

- 原型作为产品文档，默认只验证本次改动：一个正常场景、一个相关边界场景，并查看受影响页面截图。
- 不默认运行全量回归、整套专项测试或穷举屏宽／语言／主题组合；不为小改动新增大批自动化用例。
- 用户明确要求扩大验证，或最小验证发现关联问题时，再扩大范围；扩大前说明原因，只检查相关部分。
- 交付时如实说明已验证内容与未验证范围，不把既有测试结果表述为本次通过。
- 此规则仅适用于原型迭代，不降低生产代码或真实服务的验证要求。

## 完成标准

事项标记 `done` 前必须满足：

- 核心认知必须是唯一事实来源，不允许在prd，设计文档中重复
- PRD 含可验证验收标准；实现设计逐项映射验收标准。
- 阻塞性“待确认”已清零。
- 已人工复核事实、范围、验收标准、实现映射和待确认项；证据写入 `feature_list.json` 与 `progress.md`。

## 收工顺序

1. 更新 `feature_list.json` 状态与证据。
2. 更新 `progress.md` 的完成项、风险、决策、文件与验证结果。
3. 跨会话任务更新 `session-handoff.md`，写明唯一下一步。
4. 人工复核设计文档；发现缺项时不得声称完成。
