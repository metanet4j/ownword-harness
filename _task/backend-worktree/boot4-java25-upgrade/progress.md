# 进度

## Current State

验收未通过，已获授权修复至计划完成。R0—R2 的既有产物保留；R3—R6 重新按实际门禁验证，状态以 feature_list.json 为准。四仓库均在 feature/bsv-sdk-replace；本轮不推送。

## Last Updated

2026-10-12

## Current Objective

恢复历史助记词输入的派生兼容性，并修正新钱包词表生成。

## 已确认的验收缺口

- component-bap 测试源码缺少新接口实现，仍调用已不存在的交易序列化方法。
- 旧词串导入被新增 checksum 检查拒绝；离线交易测试 2 例中 1 例错误。
- component POM 覆盖单元排除项；EsTest 操作固定业务索引，资源隔离未完成。
- 全量覆盖率证据及方法清单不一致，最终 25 POM 依赖树和提交后绑定未完成。

## 当前证据

- 验收摘要：/tmp/ownword-upgrade-review-20261012/audit-summary.json。
- base：47 例、gaps=0；SDK：271 例、gaps=0；本地 HTTP：5 例通过。这些不能替代最终全量验收。
- 修复前状态快照：evidence/bsv-replace/repair-20261012/pre-repair-feature-list.json。

## Recommended Next Step

以旧制品冻结历史词串的派生向量，先复现，再修复 MasterPrivateKey 与 CryptoHelper 的公共派生入口。
