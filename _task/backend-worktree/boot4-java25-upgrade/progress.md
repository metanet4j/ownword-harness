# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-28。
- **Current Objective**：为四个子仓库建立完整单元测试、集成测试与逐模块验收证据。
- **Active Item**：`unit-u5-storage`（store-sql → store-mongo → store-search），刚开工；U4 已完成。
- U3 三模块严格验收均通过：component-model 20/0/0/0（LINE 73/78、BRANCH 2/2、METHOD 18/19，evidence/20260928T100401Z/）、component-common 41/0/0/0（LINE 239/248、BRANCH 42/42、METHOD 86/95，evidence/20260928T103233Z/）、component-core 纯接口 N/A（evidence/20260928T103553Z/）。提交：component 63560a3、4d3cf66。
- component 仓库根启用 `lombok.config`（`addLombokGeneratedAnnotation`），Lombok 生成成员由 JaCoCo 内置 `AnnotationGeneratedFilter` 逐成员识别；聚合 POM 补 JUnit/Mockito 测试依赖与 `jacoco.unit.check.excludes` 属性。缺口一律按 `unit-coverage-exceptions.json` 精确清单登记并由 `verify-unit.py` 双向核对。
- U3 测试暴露并最小修复：`ConvertTypeEnum` 构造器未写入 `id`、`JacksonBeanUtils.copyProperty` 忽略目标类型；`StateHelper` 删除不可达空 `default`；`LocalTestUtxoProvider` 目录可配置、`BitcoinSchemaTransaction` 可注入 UTXO provider（默认行为不变）。
- U4 四模块严格验收均通过：connect-planaria 12/0/0/0（`evidence/20260928T110034Z/`）、tx-convertor 54/0/0/0（`evidence/20260928T122818Z/`）、tx-filter 7/0/0/0（`evidence/20260928T130137Z/`）、tx-validator 4/0/0/0（`evidence/20260928T130312Z/`）。提交：component 53d5d62、347635f 及后续。
- U4 测试暴露并最小修复：UtxoConvertor 输出分支互换（P2PKH/P2PK 均抛异常）、BAP append-data 未设签名地址与 appendData、协议反射工厂前缀错位与非文本字段跳过。
- U2 sdk 严格验收 203/0/0/0，证据 `evidence/20260928T093257Z/`（head 670ee3d）；U1 base 回归 19/0/0/0，证据 `evidence/20260928T092443Z/`。

## 阻塞与剩余工作

- U5—U9 尚未完成；当前从 store-sql 开始。
- 共享中间件当前没有运行容器；启动存储、消息与缓存阶段的集成测试前，须按 `infra/README-*.md` 核对连接、服务日志与资源隔离。
- 四仓库分支仍为 `feature/java25`，未推送远端。

## Recommended Next Step

按计划 §5 推进 U5：store-sql → store-mongo → store-search，单元测试用受控替身（JdbcTemplate/MongoTemplate/ES client），实连集成留待中间件启动后单独验证；逐模块达到 §3 口径并提交证据。
