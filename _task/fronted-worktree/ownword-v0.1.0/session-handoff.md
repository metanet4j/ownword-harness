# 当前交接

本轮链上先行、头像和多余接口删除已完成。前端 abb6b7c；后端 component 18403d4、233bbcb。允许范围内的真实服务与浏览器验收通过，详情见[当前报告](验收报告v0.1.0-20261014-010853.md)及 evidence/chain-first-20261014-112119。无需再次请求开工批准；设计和视觉保留人工复核状态。

唯一下一步：按 D02 实现 F04 的稳定钱包模块、独立 Mock 广播及后端真实业务查询/隔离投影；不能保留 simulationPreview 资料来源或让业务依赖 CWI。之后补真实公共历史与覆盖，资金到位后执行 I08/I09。

5041 前端、5042 CWI 模拟钱包、5043 Java API ready；运行配置在私有 _runtime/services.json（0600、Git 忽略）。run-services.py 可管理已核实的本任务进程；不要重启钱包或清空共享数据库。API 运行独立 jar 副本；重建前端前停止 frontend。冻结原型 tag 不变，5047 保留原型对照。

新流程只在钱包原交易回执后调用 transactions/sync，取消和无回执操作不写后端。IndexedDB 保存完整本地恢复依据与账户入口，账户变更后的旧回执仍存入原账户。同步失败不得重新签名；只读查找钱包原 operationId 标签，或使用保存的 rawTx 重放同 TxID。

账户 0 的测试资料已恢复 Maya Chen、Person、原 76 字符简介，头像为 b://92e174733bf2af03604c3fb02d6879389a81df8ffe6cc03ea3439fe1dfe4c95c。最新模拟操作 b08ae88b-77b2-4a18-9fc8-bc4f7b4cd3e1，TxID b8536c36077e60f565f7e23eab1de1d1bfebf416afec5dda24b33b90525591a0；刷新后从真实 IndexedDB 恢复。账户 1 旧未知操作 162406fd-8a4b-490a-8910-5c92e79af15d 保留，仍需只读恢复，禁止盲目重签。只读旧操作 GET 因此暂留。

修改前端后 npm run format，再执行 lint/typecheck/test/build。完整测试同时指定 OWNWORD_API_TEST_URL 与 OWNWORD_API_ASSET_TEST_DIR，命令见前端 README；缺配置的 skip 不计通过。本轮 18 项通过、skip 0；Java reactor 20/42/59/62 共 183 项，core/API JUnit 为 0。既有 Java Mock 回归不替代真实服务验收。
