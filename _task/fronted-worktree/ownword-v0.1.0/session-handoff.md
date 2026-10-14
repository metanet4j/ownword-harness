# 当前交接

F05 钱包轮询修正已提交 bde801a；闲置 24→0 次 RPC，前台账户切换、取消和隔离账户 1 发布通过，29 项及格式/类型/最终构建产物通过。用户最新要求“改完就行”，已结束追加验收；自动审批拒绝重启前端和新浏览器复验，未执行。旧运行进程引用已替换资源问题保留，F05 needs-review。当前并行 F06 状态与改动保留，详见统一清单。


W01 官方核心与助记词钱包实现、检查和提交完成，前端 4fe782b，后端 11f925f（本轮未改）；参考来源 20540d9，认知/设计 c92813f。29 项当前检查、格式/lint/类型/build 及真实浏览器验收通过。W01、D02 保留人工复核，activeItem=null。范围和证据见[当前报告](验收报告v0.1.0-20261014-010853.md)，无需再次申请已授权范围的开工许可。

唯一下一步：核实 Chrome 扩展的准备签名但不广播能力；随后补充分公共历史与 checkpoint，充值后运行 I08/I09。本地官方核心复用不能算插件桥接/权限或主网验收，live 仍保留准备能力门禁。

5041 production、5048 官方核心钱包、5043 Java API ready；旧 5042 钱包原进程保留。配置 _runtime/services.json（0600、忽略），新钱包私有记录位于 OWNWORD_YOURS_WALLET_DIR；助记词、存储 ID 和根公钥目录复用，可 restart wallet，不能 restart legacy-wallet。不得清空共享数据或在运行中覆盖前端构建。浏览器上传/截图/HAR 使用绝对路径；最终会话 ownword-yours-core。

公共入口 lib/wallet/index.ts、稳定 contracts.ts；官方核心在私有 yours-core.ts，由 scripts/yours-wallet-server.ts 独立进程运行。@1sat/wallet-node 0.0.88 / wallet 0.0.121、utils 0.0.43、工具箱 2.14.8 固定。真实 SQLite 保存准备/签名交易；MockServices 仅隔离钱包资金/广播。业务编码和查询/同步在 lib/domain；原交易保存、广播接受后才同步后端。

官方钱包账户 0：BAP ID 3ggZAZzzWfZi92mreHvoK7hRszCg；Maya Chen 1、Person、原简介及 JPEG 12,108 字节。最终 Profile TxID 391fe964b9cc8263fd6998b033ba049337968fa467d01d0b0e2e25cf461f7a81，头像 b://31da0b77bdc616e65af3ed8eb6d2f8f0af16c2fc1454e850eaa8c52bea66eb0b。原生 signAction、实际同步 body、解析报告在 evidence/yours-core-20261014-154941，三者格式用途不同。账户 1 已用于本轮 RPC session verification 测试身份；旧钱包账户 1 的未知操作 162406fd-8a4b-490a-8910-5c92e79af15d 留在 legacy 服务，不得迁入新种子或盲目重签。

复跑 ./init.sh；源码检查按 README。测试需要真实 API URL 和本任务资产缓存目录，--test-isolation=none 必须核对最终实际 29 项、0 skip；不能只看退出码，integration-first.txt 注册不全。后端 Java 183 项为旧基线，API JUnit 0，本轮 API 来自真实 HTTP。钱包 RPC 上限 12 MiB，尚未验 5 MiB 图片/主网费率。新模块公共契约与 bf25772 无差异。
