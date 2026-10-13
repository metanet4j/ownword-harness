# JungleBus Java 25 迁移

阶段与开工条件见[实现计划](doc/实现计划-20261013-110456.md)，审查见[计划审查](doc/计划审查-20261013-111315.md)。状态与证据见 feature_list.json 和 progress.md。

原始源码：../../../reference/js-junglebus；独立 Java 工程：metanet4j-junglebus，分支 feature/java25。

运行 ./init.sh 检查环境，./verify.sh baseline 验证 JS，./verify.sh test 运行 Java 测试，./verify.sh package 打包。缓存位于本任务 .cache。

J00–J06 已完成，Java 37 项测试、JS 77 项基线通过，真实 JSON 普通订阅收到 100 条交易后取消并关闭。完整结果见[交付验收报告](doc/交付与真实集成验收-20261013-124200.md)，SDK 使用见[工程 README](metanet4j-junglebus/README.md)。

真实测试显式运行 `./live-test.sh <subscriptionId> <新输出目录> JSON`；不会进入默认离线测试。运行 `python3 collect-evidence.py` 核对当前产物、测试执行数和已保存的 100 条交易。
