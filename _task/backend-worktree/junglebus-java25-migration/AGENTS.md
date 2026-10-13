# JungleBus Java 25 迁移任务

## Startup Workflow 开工

阅读 `../AGENTS.md`、`../mvn-command.md`、本文件、实现计划、feature_list、progress 和 session-handoff，运行 `./init.sh`。一次只推进一个事项。

## Scope Boundary 范围与授权

用户已要求 review 通过后开始实施。按 `doc/实现计划-20261013-110456.md` 先完成 J01 五项门槛，再连续实施 J02–J06，不重复请求开工批准。

只修改本任务资料、验证工具和独立工程 `metanet4j-junglebus/`。原始 `reference/js-junglebus` 与其他后端工程只读；不执行上游安装脚本，JS 基线在 `.cache/js-baseline/` 运行。

新工程在自己的 Git 仓库、`feature/java25` 分支提交；根仓只提交任务资料和必要的精确忽略路径。工具链和缓存按任务隔离，不修改既有后端分支，不推送远端。

## Definition of Done 验证与完成

Verification commands: `./init.sh`、`./verify.sh baseline`、`./verify.sh test`、`./verify.sh package`。

`./init.sh` 只检查环境和固定源码；`./verify.sh baseline` 验证 JS 行为与协议样本；`./verify.sh test` 执行 Java clean test；`./verify.sh package` 完整打包。阶段完成须有实际命令、测试数和关键用例证据。模拟服务不能替代真实部署验证。每阶段通过后提交。

API、协议和状态事实只记在契约及固定样本中，状态文件只记录范围、进展和证据。收工同步清单、进展、交接，保留唯一下一步。

## End of Session 收工

One feature at a time：只推进当前事项；更新 `feature_list.json`、`progress.md`、`session-handoff.md`，记录证据并提交后交接。
