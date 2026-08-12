# 工作区指南

## 沟通

- 每次回复先称呼用户为“胡先生”。
- 默认使用简体中文，技术术语可保留英文。
- 回答简洁，但不省略关键证据和验证方式。

 ### 开工门禁

\- 进入 `_tasks/<任务名>/` 目录下开始任何工作前，第一步必须 Read `_tasks/<任务名>/AGENTS.md` 或者CLAUDE.md 。CLAUDE.md 、AGENTS.md优先级高于本文件。

\- 未读齐上述文件前，禁止一切操作。

## 工作区目录

设计文档 `ownword\spec`

外部仓库文档和代码 `ownword\reference`

- bap 协议 `reference\bap-master `
- schema、内容、关系 `reference\schema-master`
- 钱包 `reference\yours-wallet-main`
- 1sat、nft  `reference\1sat-ordinals-master`

设计原型 ``ownword\designs``

后端代码库 `ownword\backend`

## Working Rules

- 在你排查问题的过程中，不要只看到代码就下结论，做决策。看日志，查数据。有必须要的时候写一个简易的临时代码证明你的判断
- 确认你在集成测试，端到端测试过程中 查看的日志文件位置，查询数据库的链接，以及其他提供给你观测的工具或者组件的查看方式
- 如果在程序运行过程中，你看不到足够的日志，你应该在代码中添加日志，包括程序入口，出口，分支场景。尽可能获取更多的信息再做决策
- 坚持DRY 原则，DRY（Don't Repeat Yourself）绝不仅仅是“不要复制粘贴代码”。它的官方定义是：“在一个系统中，每一份知识（Knowledge）都必须有单一、明确、权威的表述。”
- 集成测试，接口测试必须使用 提权使用宿主环境来跑
- 出现问题不清楚的可以通过查询设计文档与核心认知文档进行确认，如果有核心认知文档和设计文档存在冲突，以核心认知文档作为唯一的准确事实来源
- 强调 核心认知文档作为唯一的准确事实来源，必须遵守 DRY原则

## Skill 路由

- 所有回复使用 `caveman`。

- 编写或修改文档时，同时使用 `caveman` 和 `writing-clearly-and-concisely`。

## Escalation

*架构决策\*：读 ownword\reference 外部文档、设计文档ownword\spec 确认，否则问用户