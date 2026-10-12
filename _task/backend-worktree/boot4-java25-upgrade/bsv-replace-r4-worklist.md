# R4 component 适配

R4 的基础、交易、下游、资源隔离和收口五项状态与证据见 `feature_list.json`。组件已使用新业务／原生 SDK 类型，并修复金额、txid、coinbase、源码与测试编译、自检脚本和共享测试资源隔离问题。

`BitcoinSchemaTransaction.correctlySpends` 执行原生 `Spend`，不静默跳过脚本验证。集成测试只创建和清理本轮唯一数据库、表、索引、topic、consumer group、Redis key 前缀与本地临时资源。

当前公开 API 与测试去向见 `bsv-replace-api-map.json`、`bsv-replace-test-map.json`；最终全集成结果由 R6 验收。
