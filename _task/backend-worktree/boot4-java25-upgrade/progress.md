# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-28。
- **Current Objective**：为四个子仓库建立完整单元测试、集成测试与逐模块验收证据。
- **Active Item**：`unit-u5-storage` 已完成（三模块单元 + 实连集成）；下一项 `unit-u6-business`（component-tx → bap → bsocial → bitcoinschema → handler）待开工。
- U3 三模块严格验收均通过：component-model 20/0/0/0（LINE 73/78、BRANCH 2/2、METHOD 18/19，evidence/20260928T100401Z/）、component-common 41/0/0/0（LINE 239/248、BRANCH 42/42、METHOD 86/95，evidence/20260928T103233Z/）、component-core 纯接口 N/A（evidence/20260928T103553Z/）。提交：component 63560a3、4d3cf66。
- component 仓库根启用 `lombok.config`（`addLombokGeneratedAnnotation`），Lombok 生成成员由 JaCoCo 内置 `AnnotationGeneratedFilter` 逐成员识别；聚合 POM 补 JUnit/Mockito 测试依赖与 `jacoco.unit.check.excludes` 属性。缺口一律按 `unit-coverage-exceptions.json` 精确清单登记并由 `verify-unit.py` 双向核对。
- U3 测试暴露并最小修复：`ConvertTypeEnum` 构造器未写入 `id`、`JacksonBeanUtils.copyProperty` 忽略目标类型；`StateHelper` 删除不可达空 `default`；`LocalTestUtxoProvider` 目录可配置、`BitcoinSchemaTransaction` 可注入 UTXO provider（默认行为不变）。
- U5 单元（最终重跑，源码含集成测试文件）：store-sql 11/0/0/0（LINE 24/24、BRANCH 4/4、METHOD 14/14，`evidence/20260928T162746Z/`）、store-mongo 56/0/0/0（LINE 311/315、BRANCH 54/56，`evidence/20260928T162233Z/`）、store-search 32/0/0/0（LINE 97/98、BRANCH 31/31、METHOD 35/36，`evidence/20260928T161725Z/`）；提交 c8c45c3、4904dac、fb29000。
- U5 集成（提交 5174917）：store-search 4/0/0/0 连 ES 9.4.5（唯一索引，`evidence/20260928T160246Z/`）、store-mongo 6/0/0/0 连 Mongo 8.0.32（唯一库 + Spring Data 仓库与事件监听真实装配，`evidence/20260928T161101Z/`）、store-sql 5/0/0/0 连 MySQL 8.4.11（唯一库 + Druid/MyBatis-Plus/XML mapper/事务真实装配，`evidence/20260928T161623Z/`）。各证据含 maven.log、Surefire XML、元数据与服务侧日志/残留检查；ES、Mongo、MySQL 均确认无 `it-u5-*` 残留，共享数据未改动。
- store-search 单元测试用受控 ES client 替身（`EsClientStub` 执行被测代码传入的请求 lambda 并还原请求对象）；`IndexConstant` 隐式构造器按既有口径登记为精确例外。记录的行为：未映射的 Field Kind 在构造 Query 时即抛 `MissingRequiredPropertyException`，被 `search` 的 catch 转成空结果。
- 修复 `verify-unit.py` 的例外分支计数比较（`counters.get("BRANCH", 0)`）：无 BRANCH 计数器的例外类此前被误判为“例外分支计数不符”，U3 证据回放已验证修复。
- U4 四模块严格验收均通过：connect-planaria 12/0/0/0（`evidence/20260928T110034Z/`）、tx-convertor 54/0/0/0（`evidence/20260928T122818Z/`）、tx-filter 7/0/0/0（`evidence/20260928T130137Z/`）、tx-validator 4/0/0/0（`evidence/20260928T130312Z/`）。提交：component 53d5d62、347635f 及后续。
- U4 测试暴露并最小修复：UtxoConvertor 输出分支互换（P2PKH/P2PK 均抛异常）、BAP append-data 未设签名地址与 appendData、协议反射工厂前缀错位与非文本字段跳过。
- U2 sdk 严格验收 203/0/0/0，证据 `evidence/20260928T093257Z/`（head 670ee3d）；U1 base 回归 19/0/0/0，证据 `evidence/20260928T092443Z/`。

## 阻塞与剩余工作

- U6—U9 尚未开始；U6 需要 component-tx、component-bap、component-bsocial、component-bitcoinschema、component-handler 五个模块的单元测试与跨存储业务链路集成（Mongo/MySQL/ES/Kafka 已就绪）。
- 共享中间件五个容器当前全部运行且 healthy（`./init.sh` 校验）；集成测试按 `infra/README-ownword-infra-20260915-1720.md` 的连接信息连本机端口，用每轮唯一的库/索引/表，结束后清理自身资源，不动共享数据。
- 四仓库分支仍为 `feature/java25`，未推送远端。

## Recommended Next Step

开工 U6：先读 component-tx 与 component-bap 的公开接口与调用链，按模块顺序补单元测试（受控替身）并逐个严格验收，再补跨存储业务链路集成；每个模块完成后独立提交并更新 inventory/例外清单。
