# OwnWord 统一版本基线

- **当前产品目标**：[v0.4.0.yaml](v0.4.0.yaml)。状态为 `needs-review`，尚未锁定为正式发布。
- 本目录的版本号是 **OwnWord 产品目标版本**，并非 `package.json`、Maven POM 或独立子仓库的构建版本。
- 一次产品版本涵盖 PRD、共享领域模型、HTTP/BDD 契约、前端/后端实现设计、原型和验收。各文档引用同一产品版本，**交付状态各自维护**。
- 一个版本里可以沿用此前已核实且未变更的能力：不重复复制已批准的 Identity、Content 等业务规则。
- 支撑域沿用同一规则：领域、上游依据和前后端实现各有当前文档，由 Manifest 关联；文件名中的产品目标版本不构成独立支撑域版号。SDK/Maven 版本仅用于锁定实际依赖组合，不决定产品版本。
- 发布前填充 `specSnapshot` 的不可变 Git SHA/Tag，核实原型、前端与所有相关后端组件的 Git SHA 与实际测试证据。当前只记录可核实的观察基线，不表示整版已经通过主网验收。
- 升级 `v0.5.0` 时创建新 Manifest；设计文件继续通过稳定的 `README.md` 入口提供当前视图，历史通过 Git Tag/Commit 保留。

相关决策：[ADR-001](../decisions/README.md)；文档导航：[spec README](../README.md)。
