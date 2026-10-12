# R5 与 R6 验收入口

执行状态仅在 `feature_list.json` 维护；阶段要求见 `doc/BSV依赖替换计划-20261010-103802.md`。

R5 核对全部 25 个 POM 的实际依赖树、源码／配置旧引用、公开 API、原测试方法、当前分类与精确覆盖率例外。依赖依据为 `bsv-replace-dependencies.json`，方法依据为 `bsv-replace-test-map.json`。

R6 按顺序运行全量单元严格验收、本地 HTTP 五例、共享基础设施集成 18 类 124 例，保存独立证据并检查本轮资源残留；随后安装已验证制品，重新解析 25 个 POM 的依赖树，绑定 V01—V14 和当前提交。

最终入口为 `python3 bsv-task-gate.py --stage r6 --json`；`init.sh` 只检查环境，不能替代验收。
