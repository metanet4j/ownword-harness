# R3 覆盖率收口

用户已批准按计划修复至完成；待裁决状态已结束。当前精确例外见 `unit-coverage-exceptions.json`，方法承接与取消旧抽象的理由见 `bsv-replace-test-map.json`。

SDK 已修复历史种子兼容、全部跳过却成功、远程私钥依赖、摘要重复哈希、签名范围、金额精度与非零输出索引。`useForkId=false` 通过原生 SDK 的 legacy／OTDA 前像编码器恢复，不能作为缺失能力删除。

测试保留真实脚本验证；独立前像计算器与冻结输入／预期值仍作为验收依据。R3 已验证记录见 `feature_list.json`；最终以 R6 当前提交的全量严格验收为准。
