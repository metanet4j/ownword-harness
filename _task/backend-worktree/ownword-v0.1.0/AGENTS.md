# OwnWord v0.1.0 后端任务

遵循根 AGENTS.md 和[后端共享规则](../AGENTS.md)，Maven 使用[固定模板](../mvn-command.md)。

## Startup Workflow

读取本文件、共享规则，以及[统一任务清单](../../fronted-worktree/ownword-v0.1.0/feature_list.json)所指向的核心认知和设计。一次只做 activeItem，修改前检查各仓库状态。实际仓库来源由 environment.json 维护。

## Scope

用户已授权先把现有后端已提交成果合入各仓库 dev，再建立 feature/ownword-v0.1.0 worktree 连续实施。原迁移工作区保留，不推送远端，不使用子代理。仅新增设计明确的 v0.1 接口、解析和存储修复，不重做 SDK 迁移。

钱包交互与充值前广播模拟的边界以当前集成核心认知为准；所有其他后端能力、存储与实际主网读取真实。主网新交易发布等待充值，不以模拟结果关闭验收。

## Verification / Definition of Done

根前端任务 ./init.sh 检查环境登记和实际分支。Java 25 与 Maven 绝对路径、隔离 settings 遵循共享规则；测试执行 clean test 并核对每模块实际执行数。真实 HTTP、MongoDB、头像、原始交易与验签保留命令及来源证据；未执行不写通过。

每项实现、必要检查及日志审閱通过后在对应子仓库独立中文 Conventional Commit；任务文档仅在 ownword 根仓提交。共享设施只使用本任务隔离命名空间，不清空共享数据。

## End of Session

统一进展、验收状态和唯一下一步维护在前端任务 harness，不建立第二份业务状态清单。环境、启动命令和 evidence 引用可重复使用，待资金项显式保留。
