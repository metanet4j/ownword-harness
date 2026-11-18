# 当前交接

当前事项 `supporting-domains-v040` 已交付文档，状态 needs-review，无 in-progress 项；未改业务源码或原型。依据与证据见[feature_list.json](feature_list.json)和[progress.md](progress.md)。

入口：[支撑域](spec/domain/supporting/README.md)、[Identity](spec/domain/identity/README.md)、[Contracts](spec/contracts/README.md)、[Manifest](spec/versions/v0.4.0.yaml)。核心认知仍为唯一事实来源，产品目标统一 v0.4.0。

已核实 Yours 锁定的 Actions 0.0.212 和 Toolbox Client 2.12.0 发布包，完整性哈希与 bun.lock 一致。身份 Action 默认路径内部 signAction→processAction→postBeef，返回的 tx 是 Atomic BEEF；rawTx 提取与按 TxID 补查见支撑域 §4.4。该结论不外推外部 fundingProvider、其他 Action 或不同版本。

生产接入重点是高层接口未暴露跟踪引用、会话外 pending reference 恢复未实现，需验证持久记录关联与原交易补查。公共身份投影、历史验签、主链/reorg、Ordinal 历史、普通 Transfer 身份签名及编号/Binding 仍有实施门禁。当前设计不再要求 OwnWord 自建 Root 控制型初始化许可协议。

支撑域 §8.1 已给出 Yours 锁定版广播、UTXO、Ord 的确切 API 与复用示例，新增四个依赖包哈希/导出/路由已核实；只读策略接口返回 200，未广播。静态检查见 progress.md；未执行 BDD、真实扩展或主网验收。前端仓库路径当前不存在，旧 SHA 只作记录，恢复后核对。其他原型与技能待审事项保持原状态；不读取 Archive 或 spec/draft。

唯一下一步：用户复核当前设计后，按支撑域 A→B→C→D 顺序，先固定生产依赖与接口 fixtures，再验证钱包正常/拒绝/中断/丢回执/重启恢复。批准发布前维持 approvedForRelease=false、specSnapshot=null。
