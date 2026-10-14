# 当前实施：D03 Review、钱包发布、恢复与 Proof

D02 已提交前端 c0b2c67、后端 876ab3b。标准 Post / 修订 MAP 原字节验证、独立 Java AIP 验签、历史身份链映射、真实 HTTP/Mongo 查询与关系投影通过。最终前端 41 项测试全通过，lint/typecheck/build 通过；后端关联模块 188 项通过（OwnWord 新增 5 项），最终模块 clean test 和独立 package 通过。证据在 evidence/d02/checks.json；三个测试投影删除后冷启动从原交易重建一致。主网历史/checkpoint 未满足时作者仍 unverified，不能将隔离验证视为主网覆盖。

服务：前端生产 5071、API 5073、官方核心钱包 5078，数据库 ownword_v020；python3 run-services.py 管理。agent-browser 会话 v020-implementation 当前在 /content 的 Published 筛选，账户 0 已连接，320×720 英文浅色，真实空列表与停止 API 后错误/恢复重试均已验证，3 份草稿保留。所有故障已解除。

唯一下一步：接通 Review 冻结快照、共用日志互斥、签名准备/广播/同步、回读后草稿同版本清理、公开阅读和 Proof；再完成 D04 修订与历史、D05 完整验收。Review 签名按钮仍未接发布。

D03 实施注意：lib/domain/publish.ts 可复用 signedScript/snapshotFor/checkPrepared/runTransaction，但当前 recoverOperation 在 simulated 模式会调用广播，内容未知结果恢复不得沿用自动重发。现有 submissionAttempt 在准备前写入，内容流程须区分准备请求和真正广播尝试。lib/domain/journal.ts 使用 v1 operations/accounts，可添加判别内容载荷而不升级库；pending 集合要覆盖 validating/prepared。IdentityProvider 读取日志会直接拷贝 profile，需识别内容 kind 并给出相应恢复入口，不能让身份页承接内容操作。钱包 provider 的 recoverPreparation 目前仅返回 rawTx，没有已广播回执证据，需核对绑定实现的只读查询能力。不得用本地 404 证明未提交。

实际扩展、公共历史覆盖、主网资金广播和用户视觉复核门禁仍开放；D03–D05 未完成。
