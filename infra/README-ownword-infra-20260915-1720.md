# ownword 研发共享中间件

长期基础设施，供 ownword 后续所有研发、联调、验证任务复用。**不是某个任务的临时环境**。

一句话原则：**版本固定、端口固定、凭据固定、开机自启、数据落卷。**

---

## 1. 包含什么

| 服务 | 镜像（钉到补丁号） | 容器名 | 宿主机端口 | 数据卷 |
|---|---|---|---|---|
| MongoDB | `docker.m.daocloud.io/library/mongo:8.0.32` | `infra-mongo` | 27017 | `mongo-data` |
| Elasticsearch | `docker.elastic.co/elasticsearch/elasticsearch:9.4.5` | `infra-es` | 9200 | `es-data` |
| Kafka（KRaft） | `docker.m.daocloud.io/apache/kafka:4.2.1` | `infra-kafka` | 9092 | `kafka-data` |
| Redis | `docker.m.daocloud.io/library/redis:7.4.11` | `infra-redis` | 6379 | `redis-data` |
| MySQL | `docker.m.daocloud.io/library/mysql:8.4.11` | `infra-mysql` | 3306 | `mysql-data` |

- compose 项目名：`ownword-infra`；`restart: unless-stopped`，docker 随系统启动（`systemctl is-enabled docker` = enabled）。
- 五个服务均带 healthcheck，`up.sh` 会等到全部 healthy 才返回。
- 磁盘占用约 6.6GB 镜像 + 数据卷；运行内存约 2.2GB（ES 1.1GB 最大，ES 堆固定 512MB）。

---

## 2. 常用命令

```bash
cd /home/haodev/ownword/infra

./up.sh            # 启动并等待全部就绪（最多 180s）
./status.sh        # 查看状态、端口、各服务版本
./down.sh          # 停止，保留数据
./down.sh -v       # 停止并删除数据卷（彻底重置）
```

---

## 3. 连接信息（唯一事实来源）

**MongoDB**

```
mongodb://bschema:bschema123@localhost:27017/<db>?authSource=admin
```

> `authSource=admin` **不可省略**：`MONGO_INITDB_ROOT_USERNAME` 创建的 root 用户在 `admin` 库。
> 实测省略后报 `MongoServerError: Authentication failed`。

**MySQL**

```
jdbc:mysql://localhost:3306/bap_user?useUnicode=true&useSSL=false&characterEncoding=utf8&allowPublicKeyRetrieval=true
user=root  password=root123
```

> MySQL 8.4 默认认证插件为 `caching_sha2_password`，JDBC 需带 `allowPublicKeyRetrieval=true`。

**Redis**

```
redis://localhost:6379     # 无密码
```

**Elasticsearch**

```
http://localhost:9200      # xpack.security.enabled=false，无认证
```

**Kafka（KRaft）**

```
bootstrap.servers=localhost:9092
```

> 4.x 起已移除 ZooKeeper 模式，不再需要 ZK。
> `KAFKA_ADVERTISED_LISTENERS=PLAINTEXT://localhost:9092` 面向**跑在宿主机上的应用**；
> 若应用也进入容器网络，需改为容器服务名。
> `CLUSTER_ID` 固定为 `ownword-infra-kraft-01`，数据卷复用时不匹配会导致 KRaft 拒绝启动。

---

## 4. 三条必须知道的约束

**1）Docker Hub 直连不可达，必须走 daocloud 全限定名。**
本机 docker daemon 无代理，`registry-1.docker.io` 反复 dial timeout；因此 Docker Hub 来源的镜像一律写 `docker.m.daocloud.io/...`，`docker.elastic.co` 可直连。若将来接入公司内部 registry，应整体替换本文件中的镜像地址。

**2）版本升级要显式改，不要让标签浮动。**
镜像全部钉到补丁号。升级步骤：改 `docker-compose.yml` 的 tag → 同步更新本 README 与使用方文档 → `./down.sh -v` → `./up.sh`（有数据卷的服务必须 `-v` 重建，否则可能升级失败）。

**3）端口是硬约定，注意既有占用。**
`ownword/reference/xLog-dev/docker-compose.db.yml` 里有 `redis-stack` 也占用 **6379**，与本共享 Redis 冲突，两者不能同时启动。

---

## 5. 被哪些任务使用

| 使用方 | 需要的服务 | 对应关系 |
|---|---|---|
| metanet4j 升级（Boot 4.1.1 / Java 25）B 档验证 | 五个全部 | 版本矩阵与之一致：Mongo 8.0 / ES 9.4.5 / Kafka 4.2.1 / Redis 7.4 / MySQL 8.4。任务文档见 `_task/backend-worktree/boot4-java25-upgrade/doc/升级计划-Boot4-Java25.md` |
| 后续 ownword 研发任务 | 按需 | 直接连上表端口，不要各自再起一套同端口的中间件 |

> 新增使用方时，在本表补一行，写明任务名与所需服务，避免重复编排同类中间件（DRY）。
