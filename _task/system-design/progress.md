# 当前进展

当前事项为 `domain-subdomain-context-v040`，状态 needs-review。已把子域类型与限界上下文定义归入核心认知 §5，并新增 domain-design 技能供下游七维写作使用；任务范围和证据见[feature_list.json](feature_list.json)。

## 当前产出

- [核心认知](spec/核心认知.md)：§5.1.1 子域类型（SD-01~12 与四条边界规则）、§5.1.2 限界上下文（8 个上下文承载映射与五条边界规则）、§2.1 两条新术语。
- [domain-design 技能](../../.agents/skills/domain-design/SKILL.md)：七维写作规范、引用地图与交付检查。
- [七维模版](../../.agents/skills/domain-design/references/domain-design-template.md)：可复制骨架，含定义引用表、编号缺口、验收映射。
- [七维要点](../../.agents/skills/domain-design/references/domain-essentials.md)：跨维咬合、一致性与事务、反模式。
- [Domain 入口](spec/domain/README.md)：编写规范改为引用七维技能。

## 解决的问题

原本存在两套上下文划分：§5.1 模块列 6 个业务模块，[上下文映射](spec/domain/上下文映射-v0.4.0-20261117-175100.md)列 8 个上下文（Wallet 拆为 Wallet Integration、Transaction Support、Chain & Ordinal Query），写领域设计时无法裁决对齐哪套。§5.1.2 用承载映射表统一：业务模块是工作区划分，限界上下文是语言与模型边界，两者不要求同名同目录。

子域分类此前在核心认知无定义，仓内唯一分类在后端 v0.1.0 草案（已被标为历史草案）。§5.1.1 提供正式定义与编号，下游改为引用。

## 验证范围

核心认知 8 个上下文名称与上下文映射一致；SD 编号 12 个唯一且不与既有前缀冲突；§5 结构完整（5.1 → 5.1.1 → 5.1.2 → 5.2 → 5.3 → 5.4）；既有 `§5.4` 与 `#5-结构` 锚点仍有效。技能三份文件围栏成对、围栏外断链 0、模版骨架路径在 `domain/content/` 实测可解析。`feature_list.json` JSON 可解析。

未执行真实钱包、主网、Java/TS 运行时验证。本次仅文档与技能规则，未改业务代码、契约或原型。

## 实施限制与下一步

domain-design 技能经三轮子代理评审（可执行性、仓库规则一致性、真实试写）后修补；试写 Artifact 草稿暴露的 8 处填不出的列中，6 处来自核心认知缺事实（如 Artifact 无 `E-ART-*` 编号、§6.1 为无编号 bullet），非模版缺陷。

唯一下一步：用户复核子域分类判定与限界上下文承载映射；确认后按七维重写 Artifact 或 Content 领域设计验证模版可用性。人工复核前不记 done，不创建发布 Tag。
