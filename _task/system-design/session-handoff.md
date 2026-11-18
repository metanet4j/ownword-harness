# 当前交接

当前事项 `supporting-domains-v040` 已交付，状态 needs-review，无 in-progress 项。本次仅整理文档；范围和证据见[feature_list.json](feature_list.json)及[progress.md](progress.md)。

从[支撑域 README](spec/domain/supporting/README.md)进入：领域设计承载能力/模型/状态/验收，上游接入依据承载 Yours/1sat 固定版本与 API 证据，Frontend/Backend 分别承载钱包和 Java 接入。四份文档均登记于[Manifest](spec/versions/v0.4.0.yaml)。版本关系引用[统一规则](spec/versions/README.md)，未新增支撑域独立版号。

已核查的 Action 签名/提交顺序、最终 rawTx、依赖哈希、匿名查询、鉴权说明差异及未验证范围均保留；Java 和 TypeScript 示例未运行，本次未新增网络请求。具体调用与限制以各自文档为准。

生产组合、原执行恢复、公共投影、历史验签、主链/reorg、Ordinal 历史、编号/Binding 和普通 Transfer 身份签名门禁仍开放。前端仓库当前缺失，旧 SHA 待恢复后核实。其他原型与技能待审事项保持原状态；不读取 Archive 或 spec/draft。

唯一下一步：用户复核分层入口后，按统一 v0.4.0 的 A→B→C→D 顺序固定生产依赖、补接口 fixtures，再实施钱包和 Java 集成。批准发布前维持 approvedForRelease=false、specSnapshot=null。
