# session-handoff.md — 会话交接

## 当前任务

胡先生要求四个子仓库建立完整单元测试与集成测试，并已确认通过公开 API 测试；MongoDB、ES、MySQL、Kafka、Redis、文件和 HTTP 边界实测，公网服务本地模拟，自动测试不广播主网。当前 `unit-u2-sdk` 正在实施；U0 测试基线及 U1 base 已完成。

开始工作时读取 `../AGENTS.md`、`../mvn-command.md`、本目录 `AGENTS.md`、[测试计划](doc/单元测试全覆盖计划-20260920-090603.md)、`feature_list.json`，再运行 `./init.sh`。遵守单功能项实施、提交和测试门禁；不读取 Archive，不推送，不修改四仓基线。

## 已完成与证据

parent `4112a48` 提供 JaCoCo 0.8.14 `unit-coverage` profile。`unit-test-inventory.json` 列明 25 POM、369 生产 Java、当前 61 测试 Java、安全分类及 19 项集成边界。sdk Bitails 公网用例标记 `external`；component 的 Spring 基类、ES 与 SSE 类标记 `integration`。U0 基线证据 `evidence/20260926T064228Z/`，报告见[测试基线](doc/测试基线与障碍-20260926-145423.md)。宿主五服务健康。

U1 base 提交 `bae7eb6` 和 `77ad9fd`，严格入口在最终提交后退出 0：19/0/0/0，LINE 208/208、BRANCH 76/76、METHOD 51/51；证据 `evidence/20260926T072220Z/`。`jacoco:check` 已通过，同一提交的 base 构件 `install -DskipTests` 成功。AIP 坏签名缺陷与 UTXO outpoint 相等性缺陷已修复；BAP 身份派生有固定向量断言。

U2 HTTP 子项已提交 sdk `4f4a590`。两个客户端与 Provider 的本机 HTTP 集成测试 5/0/0/0，覆盖成功、畸形 JSON、503，证据 `evidence/20260926-u2-http/integration/`；隔离单元测试 32/0/0/0，LINE 392/2005、BRANCH 35/505、METHOD 114/462，证据 `evidence/20260926T075317Z/`。该单元结果是基线，U2 尚未达到严格验收。

## 下一步

U2 继续从 SDK 密钥、BAP、交易、脚本、工具类公开 API 补单元测试。最新缺口按 `evidence/20260926T075317Z/metanet4j-sdk/metanet4j-sdk/unit/jacoco-unit/jacoco.xml` 排序：Sigma 194 行、BsocialDataLockBuilder 128 行、BobHelper 128 行等。每完成一个行为项提交；严格验收须逐类 LINE/BRANCH/METHOD 100%，完成后继续 U3。

集成测试运行前核对 `infra/README-*.md` 连接参数、`docker logs`、应用日志和 Surefire XML，宿主提权运行。当前 `EsTest` 会删除固定索引、`DefaultCompleteTxFactory` 硬编码广播；未隔离前不运行这些历史实连用例。
