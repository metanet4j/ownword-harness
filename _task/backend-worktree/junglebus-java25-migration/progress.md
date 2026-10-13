# 当前进展

## Current State 当前状态

J01 已通过本地契约验收：实际固定 JS 基线 77 项断言，双格式 × 普通/Lite，HTTP/WebSocket 与固定帧通过。契约见 doc/API与协议契约-20261013-114000.md。发现上游 Protobuf pause/start 对象编码为空 bytes，Java 明确修正为 UTF-8 JSON bytes。

当前 J02：独立 Maven 工程、模型、生成协议类型和样本重放测试。真实部署的兼容验证仍待线上证据。

## Next Steps 下一步

唯一下一步：建立 feature/java25 独立工程，运行模型与协议样本测试。

## Blockers and Risks 风险

真实服务验证待实际订阅 ID；按契约使用原始高度保守重放。
