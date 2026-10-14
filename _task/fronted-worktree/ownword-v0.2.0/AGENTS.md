# OwnWord v0.2.0 实施任务

开工先读根 AGENTS.md、本文件、feature_list.json、progress.md、session-handoff.md 及 documents 指向的认知与设计；执行 ./init.sh。业务实现基于用户已批准的 R01 方案 B，范围为 C01–C10、X01/X02；事实只在认知和设计中维护。

前端 own-word-web 与后端 ../../backend-worktree/ownword-v0.2.0/metanet4j-component 是独立 worktree，分支 feature/ownword-v0.2.0。其余后端依赖复用已核对基线。一次只推进一个 activeItem，独立执行，不使用子代理，不推送、不合并。原型和 v0.1 环境保留。

源码按现有 package 执行 lint、typecheck、test、build；后端按共享 Maven 规范显式 JAVA_HOME、隔离 settings 和 clean test，核对每模块执行数。浏览器使用 agent-browser，真实服务存储与业务查询不能响应 Mock。钱包交互、测试资金与广播的允许模拟边界见设计；未完成的实际扩展、公共索引和主网门禁明确记录。

每项完成后独立提交对应仓库，仅提交本任务改动；根仓库只提交 harness 与文档。结束前更新任务状态、证据及唯一下一步。功能、真实检查和可重复启动均完成才可标记通过；用户视觉复核和主网门禁未满足时不声称整体验收完成。
