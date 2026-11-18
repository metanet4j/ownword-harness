# 当前交接

v0.2.0 内容集成设计已获批准，本地功能与技术验收已完成；用户视觉复核及真实扩展、公共身份历史/checkpoint、主网资金与广播门禁仍保留。实际范围和状态见[前端验收与状态记录](../../知识库/前端/ownword-v0.2.0/README.md)，不因工作区清理将整体版本标记完成。

前端完整仓库位于根目录 `frontend/ownword-web/`，保留 v0.1/v0.2 及 master 分支，当前检出 v0.2；后端仓库位于 `backend/`。旧前后端任务目录已清理，长期文档集中到[知识库](../../知识库/README.md)，私有钱包与服务配置在 Git 忽略的 `.local-state/frontend/` 本地保留。

已有 v0.4.0 原型视觉复核和实际钱包扩展、公共历史、主网门禁继续保留，状态不得因为此次文档调整而改变。知识库中的旧启动命令仅作为实施记录，重新启动须按当前目录准备环境。

## v0.4.0 统一文档交接（needs-review）

已在 `spec/README.md` 建立当前开发指南，在 `spec/versions/v0.4.0.yaml` 记录统一产品目标与独立 Git SHA / 验收状态。Domain/Identity、Context Map、Contracts、Frontend/Identity、Backend/Identity 和 ADR-001 已新增；原 PRD、后端历史草案与代码仓库均保留。

静态路径与链接检查通过；OpenAPI 仅为 Identity/TransactionSync 子集草案，BDD 尚未实现 Step Definition；未执行运行时或主网验证，未锁定发布 Tag。完成证据见 `feature_list.json` 的 `system-design-unified-version-v040` 与 `progress.md`。

已完成 Identity 跨端 DDD 静态技术 Review，参见 [Identity v0.4.0 评审报告](spec/domain/identity/评审报告-Identity-v0.4.0-20261118-103500.md)。结论为 Changes Requested，P0×1、P1×5、P2×3；首要阻塞是没有公开投影的初始主网 BAP 身份无法进入发布流程。任务 `review-identity-cross-end-v040` 已记录，原领域设计与统一版本清单仍保持 needs-review，未改动业务代码，未执行真实钱包/主网验收。

唯一下一步：评审并确定 R-01 首次 BAP Identity 发布的领域决策（区分公共存在性验证与初始化操作资格），完成设计与集成证据后再处理 R-02～R-06 的跨端契约和历史签名问题。
