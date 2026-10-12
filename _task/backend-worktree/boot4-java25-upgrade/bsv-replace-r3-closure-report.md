# R3 业务 SDK 适配

R3 执行项已按本轮实际证据收口，状态及提交见 `feature_list.json`。历史种子、签名失败语义、远程公开签名上下文、摘要、金额与非零索引均已修复；后续清单核对另恢复了 legacy 签名开关。

协议输入及独立预期值仍保存在 `bsv-replace-vectors.json`；当前测试承接见 `bsv-replace-current-vector-bindings.json` 和 `bsv-replace-test-map.json`。覆盖率例外以 `unit-coverage-exceptions.json` 为唯一清单。

最终全量验收由 R6 在当前提交执行；本文件不替代单元或集成报告。
