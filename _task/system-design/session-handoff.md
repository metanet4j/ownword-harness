# 当前交接

当前事项 `reference-identity-refresh` 为 `needs-review`。参考源码和文档已同步，设计依据已修正并检查；`design-artifact-v030-doc` 保留待复核状态。

续接时先读[任务指南](AGENTS.md)、[功能清单](feature_list.json)和[进展](progress.md)。参考入口及上游文档差异见[reference 说明](../../reference/README.md)，准确来源和版本以[sources.lock.json](../../reference/sources.lock.json)为准。更新参考库前检查其 Git 状态，不覆盖本地修改；旧快照备份仅用于必要恢复。

产品事实见[核心认知](spec/核心认知.md)，页面和验收见[v0.3.0 设计文档](spec/prd/v0.3.0/设计文档v0.3.0-20260918-215142.md)。identityKey 含义已由用户确认，不重复提问。普通 Transfer 的签名缺口已写入核心认知第 12 节，不能因更新 SDK 就认为所有交易已满足身份签名要求。

源码来源和完整性、文档链接、BDD、JSON 及差异检查通过，详见进展；未安装或运行外部项目。后续制作仍须按设计文档第 9 节恢复 v0.2.0 基线与 S2 资源，本轮没有制作原型或实现生产 API。

唯一下一步：用户复核参考资料入口及同步后的 v0.3.0 设计依据。
