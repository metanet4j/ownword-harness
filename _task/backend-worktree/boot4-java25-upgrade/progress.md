# progress.md — Boot 4 / Java 25 测试任务

范围与验收标准见[单元测试全覆盖计划](doc/单元测试全覆盖计划-20260920-090603.md)；逐模块状态见 `feature_list.json`，源码与测试分类见 `unit-test-inventory.json`。

## Current State

- **Last Updated**：2026-09-29。
- **Current Objective**：为四个子仓库建立完整单元测试、集成测试与逐模块验收证据。
- **Active Item**：`unit-u7-adapters` 收尾中：四个模块单元全部严格验收通过，Redis 与 Kafka 实连集成完成，FTP/SFTP 本地可控服务集成未完成（见下）。
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

- U7 单元：api-common 59/0/0/0（提交 6a1b0af，证据 `evidence/20260929T081536Z/`），覆盖 GlobalExceptionTranslator 的 12 类异常翻译、GlobalApiLogAspect/LogAspect 的切点与通知、BaseApiResult/R/ApiResult、ValidateUtils、JwtTokenProvider 与注解；缺口为登记的 BaseApiResult 无调用点枚举构造器与 ValidateUtils 隐式构造器。
- U7 集成（提交 225da53）：Redis 实连 14/0/0/0（`evidence/20260929T104221Z/` 同轮回归单元）、Kafka 实连 6/0/0/0，均连共享中间件，用例自建唯一 key 前缀/topic 并在结束时清理，实测无残留。
- 集成测试暴露并修复：`RedissonAutoConfiguration.redisson()` 未提供 `redisson.config` 时 `Redisson.create(null)` 抛 NPE，只配 `spring.data.redis.*` 的标准用法无法启动；改为按 `DataRedisProperties` 装配 `SingleServerConfig`，YAML 与集群路径不变，单元复跑 34/0/0/0（`evidence/20260929T092410Z/`）。
- U7 未完成项：FTP/SFTP 的本地可控服务集成。共享基础设施没有 FTP/SFTP 服务，本机也无对应服务软件；曾用 JDK 自带 socket 自研最小 FTP 服务端，已能覆盖 `doInit` 的连接建立与路径规范化，但数据通道与 commons-net 的 `storeFile` 无法可靠互通（FTP 数据流没有结束标记，客户端发完不关闭写侧连接），且手写协议实现即使跑通也不能代表真实 FTP 行为，故不采用。`FtpFileClient`/`SftpFileClient` 的 `doInit` 成功构造行维持按精确清单登记，等有可用的真实服务再补。
- 记录的行为：RedisUtils 的 key 走 JDK 序列化，`keys`/`delByKeys` 的通配符被当作普通字符编码因而匹配不到自身写入的键，`scan` 只匹配 UTF-8 键，`hincr`/`hdecr` 无兜底直接抛异常，`generate` 的 TTL 首次创建时不生效、第二次起正常，`mget` 对缺失键放 null，`RedisAtomicLong` 与 `RedisUtils` 不在同一键空间；Kafka 在 topic 名非法时同步抛 `KafkaException("Send failed")`，`failConsumer` 不执行。

- component-bsocial 76/0/0/0（LINE 529/530、BRANCH 118/118、METHOD 153/154，`evidence/20260928T190248Z/`，提交 b9bfb97）：12 个测试类覆盖 manager/resolver/两个 handler/三个 service/两个 listener/五组转换器/两个 MapStruct 包（含嵌套 rels、childs 与上下文缓存分支）；缺口为登记的 `ConverterHelper` 隐式构造器。
- component-bsocial 记录的当前行为：不受支持的 `linkIdentity`/`linkBsocial` 类型不建交易、随后解引用 NPE；`mapList` 为空时 handler 与 MySQL 转换器抛 `NoSuchElementException`（经 ConversionService 包装为 `ConversionFailedException`）；`BsocialDoMapper` 对 null 列表保持 null（不调用 MAPConvert）。
- component-bitcoinschema 4/0/0/0（LINE 7/7、BRANCH 4/4、METHOD 2/2，`evidence/20260928T194451Z/`）与 component-handler 5/0/0/0（LINE 12/12、BRANCH 4/4、METHOD 5/5，`evidence/20260928T195825Z/`）均无覆盖率缺口，提交 2648727；记录的行为：`BitcoinSchemaTxHandler.handleBsocialTx` 的转换结果未被使用。
- U6 集成（提交 8a778c9）：MongoBusinessChainIntegrationTest 6/0/0/0 与 MysqlBusinessChainIntegrationTest 4/0/0/0，均为本地离线构造签名的真实原始交易（不联网、不广播）走 解析器 → DTO → Store handler → 存储；证据 `evidence/20260928T211704Z/`（含无 `it_u6_*` 残留检查），同轮回归了 U5 三个存储模块集成用例（6/4/5 例）。单元验收复跑 76/0/0/0（`evidence/20260928T211756Z/`）。
- U7 进展：component-file 59/0/0/0（LINE 188/199、BRANCH 52/52、METHOD 63/66，`evidence/20260928T232443Z/`，提交 2195d08）；原 8 个 `@Disabled` 用例全部改写为有效测试（local 用 `@TempDir`；FTP/SFTP 注入替身 + 本地不可达端口；S3 用 MinioClient 替身并覆盖三家云 endpoint/domain/region 推导）。
- U7 进展：component-cache 34/0/0/0（LINE 335/340、BRANCH 74/76、METHOD 74/74，`evidence/20260928T235318Z/`，提交 a7359a8）——RedisUtils 58 个方法全部经受控替身验证（含「客户端全抛异常」兜底用例），RedissonAutoConfiguration 覆盖单机创建/关闭与集群装配，CacheManagerConfig 验证缓存 TTL 与 KeyGenerator。
- U7 进展：component-message 31/0/0/0，LINE 408/408、BRANCH 14/14、METHOD 199/199 **零缺口**（`evidence/20260929T002046Z/`，提交 d77695d）；覆盖 Kafka 配置（含反射逐项验证 60 个存取器与 92 个无参取值方法）、生产者四个重载与成功/失败回调、三个监听器的发布与提交行为。
- U7 缺陷修复：`BitcoinSchemaDto` 无无参构造器导致 Jackson 反序列化 `flink_bap_sink_topic` 必然失败（监听器发布分支生产不可达）；补 `@NoArgsConstructor` 后回归用例转绿（base 提交 53ed9ad，base 复验 20/0/0/0、`evidence/20260929T002545Z/`）。
- U7 记录的行为：`KafkaProperties.Listener` 的 ackMode/noPollThreshold 未设默认值（上游为 BATCH/0.0）；DataSize 类映射经 asInt 产出 Integer。
- U7 记录的行为：未提供 redisson.config 时 `Redisson.create(null)` 抛 NPE；集群模式下节点不可达即创建失败；`RedisUtils.findKeysForPage` 的 page 为 0 基。
- U7 进展：component-message 31/0/0/0，LINE 408/408、BRANCH 14/14、METHOD 199/199 **零缺口**（`evidence/20260929T002046Z/`，提交 d77695d）；覆盖 Kafka 配置（含反射逐项验证 60 个存取器与 92 个无参取值方法）、生产者四个重载与成功/失败回调、三个监听器的发布与提交行为。
- U7 缺陷修复：`BitcoinSchemaDto` 无无参构造器导致 Jackson 反序列化 `flink_bap_sink_topic` 必然失败（监听器发布分支生产不可达）；补 `@NoArgsConstructor` 后回归用例转绿（base 提交 53ed9ad，base 复验 20/0/0/0、`evidence/20260929T002545Z/`）。
- U7 记录的行为：`KafkaProperties.Listener` 的 ackMode/noPollThreshold 未设默认值（上游为 BATCH/0.0）；DataSize 类映射经 asInt 产出 Integer。
- U7 记录的行为：无 bucket 前缀的腾讯云 endpoint 推导出空 region 被 MinioClient 拒绝；带 scheme 的 endpoint 走 MinIO 的 domain 拼法。FTP/SFTP 的「构造即连服务」行因共享基础设施无该服务，按精确清单登记为例外（成功构造路径留待本地可控服务）。
- `verify-unit.py` 例外核对改为按「方法名:行号」建键，修复同名重载（如 `createTempFile` ×3）互相覆盖导致的类级计数误判。
- U6 集成记录的行为：ID 交易由 root 签名时 `isRootBap` 为真 → 走 root 分支整体替换 signers（而非追加）；两个 handler 的搜索事件发布仍被注释，事件驱动的 ES 索引不会触发；手工装配 MyBatis-Plus 时需显式挂 `MetaObjectHandler`，事务代理需 `proxyTargetClass=true`（否则 `@Resource` 按具体类型注入失败）。
- component-bap 63/0/0/0（LINE 293/305、BRANCH 69/70、METHOD 88/88，`evidence/20260928T180551Z/`，提交 2fbd3f7）：11 个测试类覆盖两个 BapService、两个事件监听器、两个 Store handler、resolver/validator/converter 与 MapStruct 生成的映射实现；缺口为登记的 `MongoStoreBapDtoHandler` 数据分支不可达。
- component-bap 暴露并最小修复：`BapSearchListener` 的 `BapSearchService` 漏写 `@Autowired` → 字段恒 null，`BapSearchEvent` 发布即 NPE、搜索身份永不落库（MAP/ES 搜索数据链路断点）。先用 Spring 上下文回归用例复现，再补注解通过。
- component-tx 记录的当前行为：`DefaultUtxoResolver.listUtxoAddress` 忽略入参 bapBase（取工厂付款密钥）；`BapDataLockBuilder.buildRoot/buildId` 数据锁不签名（AIP 签名在交易输入侧）；`DefaultCompleteTxFactory` 的广播 lambda 用静态替身验证；钱包无法解锁输入时 `calculateChangeAmount` 先抛 RuntimeException。
- 共享中间件五个容器当前全部运行且 healthy（`./init.sh` 校验）；集成测试按 `infra/README-ownword-infra-20260915-1720.md` 的连接信息连本机端口，用每轮唯一的库/索引/表，结束后清理自身资源，不动共享数据。
- 四仓库分支仍为 `feature/java25`，未推送远端。

## Recommended Next Step

U7 只剩 FTP/SFTP 的本地可控服务集成：需要一个可用的真实 FTP/SFTP 服务（共享基础设施不提供，本机也无服务软件）。补上后即可把 U7 标记完成并进入 U8（mybatispuls-generator → component-test）。在此之前可并行推进 U8 的模块验收，不必等待。
