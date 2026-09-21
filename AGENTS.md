# 工作区指南

## 沟通

- 每次回复先称呼用户为“胡先生”。
- 默认使用简体中文，技术术语可保留英文。
- 回答简洁，但不省略关键证据和验证方式。

## 文档编写
- 编写或修改文档时使用 `caveman`、`writing-clearly-and-concisely`；持久化文档使用完整、清晰的中文。
- 新建独立报告、设计文档的 Markdown 文件名带时间戳；固定入口和状态文件（如 AGENTS.md、SKILL.md、README.md、progress.md）除外，修改已有文件不因此重命名。
- 文档只保留当前内容，不追加变更历史；变更及原因写入 git commit。

## 开工门禁
- 修改任务文件或执行有副作用的命令前，从工作区根目录向下读取目标目录沿途存在的 AGENTS.md；子目录规则仅在其适用范围内优先。
- 允许先定位、查找和读取规则；缺少中间层文件不阻塞读取下级规则。

## 工作区目录

- 设计文档：`_task/system-design/spec`
- 外部仓库文档与代码：`reference`
- 设计原型与设计系统：`designs`
- 后端代码基线：`backend`

## 设计能力体系

OwnWord 设计能力架构见：

`standard/design-skill-architecture.md`

按 `_task/system-design/spec/核心认知.md` 第 10.5 节，OwnWord **固定使用 Spectrum S2 作为唯一主设计系统**。设计任务不再选择主设计系统，也不得由外部 skill 改用其他设计系统。

设计任务采用“事实与版本约束 → Spectrum S2 → 主设计执行 → 按需 specialist → 实现检查”的模型：

```text
核心认知（SSOT）
        ↓
当前版本设计文档
        ↓
Spectrum S2（固定）
        ↓
baoyu-design
   ├─ design-taste-frontend（按页面类型选择）
   └─ high-end-visual-design（按视觉目标选择）
        ↓
Prototype / Preview / Verify

react-spectrum skill：Spectrum S2 的组件、Token、交互与 Accessibility 实现检查
```

- 核心认知是 OwnWord 产品、设计、原型、代码和测试的唯一事实来源。
- 当前版本设计文档负责把核心认知落到页面、组件、流程、视觉方向和验收。
- Spectrum S2 的固定地位和四项设计原则均以核心认知第 10.5 节为事实来源；所有设计任务先明确用户任务、信息层级、内容关系和操作顺序，再进入组件与视觉实现。
- `baoyu-design` 是主设计执行框架；使用其 design-system 能力时直接采用 Spectrum S2，并遵循核心认知中的「秩序清晰、关系可感知、密度适当、表达准确」四项设计原则。
- `design-taste-frontend` 按页面类型选择使用强度；其中“选择设计系统”的规则对 OwnWord 不适用，不得替换 Spectrum S2。
- `high-end-visual-design` 仅用于明确需要强 premium / agency / cinematic 表达的页面或局部区域，其视觉规则只能在 Spectrum S2 与版本设计约束允许范围内使用。
- `react-spectrum` skill 用于 Spectrum S2 实现检查，不定义产品事实、页面结构或产品视觉方向。
- 新增设计规则或 skill 前先检查核心认知、当前版本设计文档和 Spectrum S2，避免重复定义或形成第二套设计系统。

## 按场景加载规范

命中下列场景时读取对应规范。

| 使用场景 | 规范 |
| --- | --- |
| 实施功能、修复问题或持续推进长任务 | [自主执行与任务完成](standard/自主执行与任务完成-20260917-194638.md) |
| 加载技能、处理指令冲突或解释技能导致的停顿 | [指令与技能边界](standard/指令与技能边界-20260917-194638.md) |
| 回复用户、编写文档、说明技术工作 | [沟通与写作](standard/沟通与写作-20260917-194638.md) |
| 已明确要求使用子代理协作 | [子代理协作](standard/子代理协作-20260917-194638.md) |
| 选择验证范围、运行检查或判断是否完成 | [测试与验证](standard/测试与验证-20260917-194638.md) |

## Working Rules

- 排查问题结合代码、日志、数据，必要时用最小实验验证，不凭代码片段下结论。
- 遵守 DRY：每份知识只有一个明确、权威的表述。核心认知是唯一事实来源，其他文档引用；冲突时以核心认知为准。
- 本地代码有结论的以本地代码为准，代码无法确认的考虑查官方文档。
- 每完成一个功能项即 git commit，只提交本任务改动，无改动不空提交。
- 不读取 Archive 归档内容。

## 浏览器

- 使用 agent-browser 技能操作浏览器

## 架构决策

- 先查 `_task/system-design/spec` 中的核心认知和相关设计依据；遵循现有架构的常规实现自行处理。
- 涉及架构变更且依据不足，或资料冲突无法消解时，请用户决定。
