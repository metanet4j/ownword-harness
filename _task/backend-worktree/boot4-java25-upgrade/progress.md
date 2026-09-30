# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-30。
- **Current Objective**：无剩余工作；本任务已结项（Boot 4 / Java 25 升级 + 四仓库单元测试全覆盖）。
- **Active Item**：无。`unit-u9-acceptance` 已收尾：全量单元与集成验收通过、验收报告已交付；SFTP 实连按胡先生 2026-09-30 决定继续作为精确例外登记，不再列为待办。
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

- U8：mybatispuls-generator 6/0/0/0、component-test 14/0/0/0，均 gaps=0（提交 774e49c、3078453、559f530）；夹具下沉与集成清单核对完成。
- FTP 集成已完成（提交 3ce773b）：MiniFtpServer 按 RFC 959 用 JDK 自带 socket 实现 FtpFileClient 用到的命令子集，集成 7 例 + 单元补 1 例成功连接路径，component-file 60/0/0/0 gaps=0，`FtpFileClient` 例外已删除。
- U9 全量：`verify-unit.py --mode accept --scope all` 通过（`evidence/20260929T155751Z/`），25 POM、23 模块、**841 例**、0/0/0、全部 gaps=0；Surefire XML 独立核算 177 类/841 例，JaCoCo XML 独立核算 LINE 5469/115、BRANCH 1255/28、METHOD 1477/38。全量集成 18 类 124 例通过。报告见[验收报告](doc/验收报告-单元测试全覆盖-20260929-232313.md)。
- 收尾活体重跑（2026-09-30，`evidence/20260930T125355Z/`）：四仓库串行执行 `-Punit-coverage clean test jacoco:report jacoco:check` 全部退出 0，严格入口 `--evidence` 复核 23 模块 gaps=0；独立核算与 9-29 归档逐项一致（177 类/841 例、0/0/0、LINE 5469/115、BRANCH 1255/28、METHOD 1477/38）。本轮未执行 `-N install`——会话沙箱把隔离仓库 `~/.m2/metanet4j` 挂为只读；四仓库 HEAD 与归档一致，隔离仓库中的父 POM 与工作区逐字节相同。
- **无剩余工作。** SFTP 实连是唯一保留项，2026-09-30 胡先生决定按现状收尾：`SftpFileClient.doInit` 的成功构造行（2 行）继续按 `unit-coverage-exceptions.json` 精确登记，聚合 POM 的 `jacoco.unit.check.excludes` 保留该类。已评估但未采用的补齐方案：给 `metanet4j-component-file` 加 test 作用域 `org.apache.sshd:sshd-core` + `sshd-sftp`（纯 Java 进程内 SSH/SFTP 服务端，与 FTP 的 `MiniFtpServer` 同构，不改共享 infra、不动宿主环境），若将来要让覆盖率缺口归零，走该路径即可。
- 纠正上一轮的错误结论：曾判定「手写 FTP 服务端不可行」，实际是我漏发 `150` 中间响应（客户端因此不发数据）且 accept 循环单线程阻塞后续连接。FTP 已闭环。
- 记录的行为：RedisUtils 的 key 走 JDK 序列化，`keys`/`delByKeys` 的通配符被当作普通字符编码因而匹配不到自身写入的键，`scan` 只匹配 UTF-8 键，`hincr`/`hdecr` 无兜底直接抛异常，`generate` 的 TTL 首次创建时不生效、第二次起正常，`mget` 对缺失键放 null，`RedisAtomicLong` 与 `RedisUtils` 不在同一键空间；Kafka 在 topic 名非法时同步抛 `KafkaException("Send failed")`，`failConsumer` 不执行；`scanner` 按空白分词只取第一个词；jacoco 0.8.14 对 CLASS 元素的单类全名排除不可靠，需用包通配写法。

## Recommended Next Step

无剩余工作，本任务已结项。重启验证入口：`cd /home/haodev/ownword/_task/backend-worktree/boot4-java25-upgrade && ./init.sh`；全量验收 `python3 verify-unit.py --mode accept --scope all`（需要隔离仓库 `~/.m2/metanet4j` 可写，用于父 POM 与上游产物 install），集成验收 `cd metanet4j-component && mvn -s ~/.m2/metanet4j-settings.xml -B clean test -Dgroups=integration -DexcludedGroups=external`。若将来决定让覆盖率缺口归零，按 `unit-u7-adapters` 记录的内嵌 Apache MINA SSHD 方案补齐 SFTP，并同步删除 `unit-coverage-exceptions.json` 与聚合 POM `jacoco.unit.check.excludes` 里的 `SftpFileClient`。
