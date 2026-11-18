# 链与 Ordinal 查询实现设计（OwnWord v0.4.0 目标）

> 状态：needs-review。领域端口、状态与验收以[支撑域](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md)为准；外部请求和鉴权以[上游接入依据](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md)为准。OneSatStackClient 是待实施的 Java 适配器，本文不宣称已经修改或运行后端代码。

## 1. Java HTTP 接入

**后端使用 Java 直接请求同一套 HTTP API。** `@1sat/client` 是 TypeScript 包，作为请求路径、参数和响应语义的参考；当前 Java 接入沿用 JDK `java.net.http.HttpClient`。先在 `metanet4j-api-ownword` 的 Infrastructure Adapter 中实现一个具体 `OneSatStackClient`，由现有查询/同步流程调用；类名是实施建议，当前源码尚无该客户端。公共接口密钥结论引用 [上游访问与鉴权](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md#3-访问与鉴权)。

现有 [IdentityApi](../../../../../backend/metanet4j-component/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/IdentityApi.java) 已创建可复用的 JDK HttpClient，连接超时 10 秒、单次请求超时 15 秒，并显式处理 HTTPS_PROXY；[Java 构建基线](../../../../../backend/metanet4j-parent/pom.xml)为 Java 25。接入时抽取并注入同一 HTTP 配置，保留部署代理行为。建议新增服务端配置 `OWNWORD_1SAT_BASE_URL=https://api.1sat.app`，按[上游 API 路径](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md#2-公共-api-与客户端入口)统一拼接请求；这是待实施配置，不是现有已生效变量。现有 `OWNWORD_BAP_URL` 仍是完整的 BAP profile 路径前缀，迁移前保持兼容。

| 后端能力 | HTTP 与解析方式 | 接入位置/约束 |
| --- | --- | --- |
| 原交易、BEEF、Proof | `BodyHandlers.ofByteArray()`；三种格式分别解析 | `getRawTx/getBeef/getProof`；原交易字节转 hex 后交 metanet4j 校验，不将 BEEF 当 rawTx |
| 交易状态、链头、TXO、Ord 元数据、BAP | 读取 UTF-8 JSON，按对象或数组转换 DTO | `getStatus/searchTxos/getTxosByTxid/getSpend/getMetadata` 等按需加入同一客户端；保留缺失字段、来源和观测时点 |
| Owner 同步与 TXO 流 | SSE，以流式 handler 读取并处理事件/断流 | 使用时按 [上游 API 路径](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md#2-公共-api-与客户端入口) 的刷新路径处理，不能用普通 JSON 数组解析器，也不能把未刷新索引的空数组当作地址没有资产 |
| 已签材料提交 | `BodyPublishers.ofByteArray(bytes)`，Content-Type 为 application/octet-stream | 按 [上游 API 路径](../../contracts/upstream/接入依据-Yours与1sat-20261118-164032.md#2-公共-api-与客户端入口) 的固定版本入口提交；解析 200/202/400 的原始业务状态，超时走 [领域状态与恢复](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md#6-状态恢复与链上观测) 的原交易恢复 |

最小原交易读取示意，放在上述客户端内部；HttpClient 和主机基址由构造时注入，Transaction 使用现有 `com.metanet4j.bsv.transaction.Transaction`：

```java
String getRawTx(String txid) throws IOException, InterruptedException {
    if (txid == null || !txid.matches("[0-9a-f]{64}")) {
        throw new IllegalArgumentException("Invalid txid");
    }
    var request = HttpRequest.newBuilder(
            baseUrl.resolve("/1sat/beef/" + txid + "/tx"))
            .timeout(Duration.ofSeconds(15))
            .header("Accept", "application/octet-stream")
            .GET().build();
    var response = http.send(request, HttpResponse.BodyHandlers.ofByteArray());
    if (response.statusCode() != 200) {
        throw new IOException("1sat rawTx HTTP " + response.statusCode());
    }
    String rawTx = HexFormat.of().formatHex(response.body());
    if (!txid.equals(Transaction.fromHex(rawTx).id("hex"))) {
        throw new IOException("TXID_MISMATCH");
    }
    return rawTx;
}
```

这是请求和字节处理示意，尚未在 Java 模块编译或运行；生产 Adapter 再按 [领域状态与恢复](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md#6-状态恢复与链上观测) 映射超时、404、429、上游错误与坏响应。404/缺索引保持来源相关的未观测状态，不能证明交易未广播；InterruptedException 向上传递或恢复中断标记。JSON 对象可沿用现有 Document.parse 转换，TXO 搜索为数组，须使用项目现有 JSON Mapper 的数组/DTO 解析，不能直接套对象解析。响应体需按部署策略设置大小上限；错误状态不能作为交易字节送入解析器。

**现有代码的实际调整点**：IdentityApi.transaction(txid) 当前从 WhatsOnChain 分别取 hex 和交易详情，再把 confirmations>0 映射为 networkAccepted。应将原交易读取替换为 OneSatStackClient，并分别保存 Stack 提交观测与 Chaintracks/Proof 主链证据，不仅替换 URL。IdentityApi.identity(bapId) 当前丢弃 BAP 正文，需改为解析并验证公共事件/资料，再重建投影。[TransactionSyncApi](../../../../../backend/metanet4j-component/metanet4j-api-ownword/src/main/java/com/metanet4j/api/ownword/TransactionSyncApi.java) 的首次同步与重放都调用该 transaction 方法；两条路径共用新的查询适配，避免只改 HTTP 回读而遗留旧观测逻辑。

钱包签名、身份发布和高层 Action 继续由前端调用 Yours。高层 Action 已内部提交时，前端取得 rawTx/TxID 后仍使用现有四字段 `POST /api/v1/transactions/sync`，后端校验、存证并查询，不触发第二次创建或自动广播。确需后端转发独立已签材料时才使用提交方法，执行前验证原交易和 TxID；当前 Sync 接口语义不因此变成广播接口。完整 Ordinal 历史、主链重组与业务验证仍按 [领域查询与验收](../../domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md#7-ordinal-交易查询) 补齐，HTTP Client 本身不提供这些领域结论。

## 2. 现有 API 与公共投影

现有 OwnWord `POST /api/v1/transactions/sync` 和 `GET /api/v1/transactions/{txid}` 可复用，但后者目前会返回 storage receipt 或有限 chain observation，不能冒充本设计完整的 TransactionQuery/OrdinalQuery。尚无已核实的 OwnWord Ordinal 历史/编号 HTTP 端点，本轮不在 OpenAPI 发明路径。SDK 公共客户端的上游路由也不等于 OwnWord 后端已实现同名路由。

Java `IdentityApi` 目前缺投影时丢弃公共 BAP 响应正文并返回 unknown，`TransactionSyncApi` 写 chain_events 后未见身份投影生成路径；实现时应接通公共 BAP/事件→可重建身份投影，供业务回读，不能以同步回执代替。

## 3. 主链与验证边界

ChaintracksClient 的 subscribeReorgs 当前抛出未实现错误，生产适配须补主链重查，不能把订阅新块或固定 true 的 isSynchronized 当作重组验证。

Java 示例尚未编译运行；本次仅迁移已有设计。部署 fixtures 须覆盖 binary/JSON/SSE、异常状态、原交易校验、同步重放、主链重查和查询覆盖；真实钱包、广播与重组实验仍待单独验收。
