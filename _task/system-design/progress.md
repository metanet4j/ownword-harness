# 当前进展

当前交付为 `supporting-domains-v040`，状态 needs-review：已按用户要求将钱包、交易签名/提交、链上状态和 Ordinal 交易查询整合到统一 v0.4.0 领域设计。任务范围与证据见[feature_list.json](feature_list.json)，本文不另定义产品规则。

## 当前产出

- [核心认知 §5.4](spec/核心认知.md#54-支撑能力与产品领域的责任)：明确稳定责任与事实来源。
- [支撑域](spec/domain/supporting/README.md)：SUP-01~10、操作/链状态、原执行恢复、Ordinal 输出/花费/历史、能力缺口及源码映射。
- [Identity](spec/domain/identity/README.md)、[Context Map](spec/domain/上下文映射-v0.4.0-20261117-175100.md)、[前端](spec/frontend/identity/README.md)和[后端](spec/backend/identity/README.md)：同步钱包委托边界；公共 unknown 不再单独阻止钱包已有身份动作。
- [Contracts](spec/contracts/README.md)：保留五条既有路由；Identity 18 个、支撑域 16 个、Artifact 2 个设计场景，尚无 Step Definition。
- [Manifest](spec/versions/v0.4.0.yaml)：统一目标、独立组件版本和门禁；approvedForRelease=false、specSnapshot=null。

## 源码核查与限制

Yours 实际 package.json 为 5.1.0，锁定 Actions 0.0.212；与 reference/sources.lock.json 的部分记录不同。独立参考 SDK 的 Actions 为 0.0.221。已从 npm 只下载读取 0.0.212 和 wallet-toolbox-client 2.12.0 发布包，两者完整性哈希均与 Yours bun.lock 一致，未安装或执行。

固定版本身份 Action 的默认钱包路径内部完成签名并尝试 postBeef，返回最终交易材料没有调用方暂停点；tx 是 Atomic BEEF。最终 rawTx 优先从该返回值提取，或按 TxID 补查原字节，校验 TxID 后保存。完整调用链、适用范围及包哈希见[支撑域 §4、§11](spec/domain/supporting/领域设计-支撑域-v0.4.0-20261118-141904.md)。

身份高层接口未暴露 actionId/reference 或业务 operationId；Toolbox 会话外 pending reference 续签恢复未实现。生产适配需核实丢回执的持久关联与查询恢复。其余开放项包括公共身份投影、历史验签、主链/reorg、Ordinal 历史、普通 Transfer 身份签名、编号/Binding 和 Identity/Profile 类型策略。

## 验证范围

本轮已做源码与发布包取证、JSON 解析及严格 YAML 解析（无警告）；OpenAPI 保留 5 条路由、22 个 Schema、61 处内部引用，均无悬空。17 份 Markdown 的 189 个本地引用可定位，无未配对围栏；36 个 Gherkin 场景具备 Given/When/Then，git diff --check 通过。这些检查不构成运行验收。

未运行正式 OpenAPI 规范验证器、BDD 场景、Java/TypeScript 服务、真实钱包扩展、主网提交或重组实验；未改业务代码、原型和 reference。前端 SHA 为旧登记，本地当前无 frontend/ownword-web 源码目录，实施前须恢复核对。

## 其他事项

v0.2.0 本地功能与技术验收依据保留在[知识库](../../知识库/前端/ownword-v0.2.0/README.md)；真实扩展、公共历史/checkpoint、主网资金与广播门禁仍开放。原型视觉复核、导航与新版技能接入的待审状态继续由 feature_list.json 各自记录；本轮不改变其审批结果。

当前设计统一为 v0.4.0，人工复核前不记 done，不创建发布 Tag。唯一下一步：用户复核当前支撑边界与调用链，按支撑域实施顺序补实际接口 fixtures 与钱包集成证据。
