# 当前交接

F04 已实施并完成允许范围验收。前端 bf25772；后端 component 11f925f；认知/设计 9f85424。24 项检查、模块边界 lint、类型、最终 build、Java clean package 和真实浏览器正常/取消/停机恢复通过；详情见[当前报告](验收报告v0.1.0-20261014-010853.md)。设计和视觉保留人工复核，无需再次申请已授权范围的开工许可。

唯一下一步：核实实际 Yours 扩展的准备签名但不广播能力；随后补充分公共历史与 checkpoint，充值后运行 I08/I09。live 默认不放行未验准备能力，不能用本地 Mock 通过冒充主网验收。

5041 production、5042 原测试钱包、5043 Java API ready。配置 _runtime/services.json（0600、忽略）；run-services.py 管理本任务进程。不要重启钱包、清空共享数据或在运行中覆盖前端构建。原型固定 tag，未移动。浏览器上传/截图/HAR 均使用绝对路径，最终会话 ownword-wallet-final 的稳定身份页已检查。

公共钱包入口 lib/wallet/index.ts，稳定接口 contracts.ts；具体 CWI/SDK 在 adapters。业务编码和同步在 lib/domain。已签名原交易保存后才广播；接受回执后才 POST 原交易，普通资料/头像/已广播业务恢复查后端。未广播准备恢复仅封装在钱包内部。

账户 0 恢复 Maya Chen、Person、原 76 字符简介和原 JPEG 字节；最新 Profile TxID 02b0060f4f506e34047ab2ad2484742614802e70f855dec0264278ddbb15798f，头像 b://8871d052209d324260854f22f9aa10f48bee30179358c8529560d8e42526c9ef。操作标识和回执见 evidence/wallet-module-20261014/browser-final-journal.json。账户 1 的旧未知操作 162406fd-8a4b-490a-8910-5c92e79af15d 保留，禁止盲目重签。

复跑 ./init.sh；源码修改按 README 运行 format/lint/typecheck/test/build。完整测试设置真实 API URL 和隔离缓存路径；node 使用 --test-isolation=none 执行实际 24 项，skip 不算通过。Java 依赖 183 项、API JUnit 0；真实接口依据 HTTP。当前 wallet RPC 请求限 2 MiB，未验证主网费用或 5 MiB 图片大交易。
