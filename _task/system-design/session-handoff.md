# session-handoff.md

## 当前状态

- design-001 已完成：`designs/own-word-prototype-001/`（PRD v0.1 全部 BDD 场景 + Public 3D 身份卡，碑铭/印章）。
- design-002 已完成：`designs/own-word-prototype-002/`（对照版「穹顶与地平线」，功能一致、视觉重设计）。
- design-003 已完成：`designs/own-word-prototype-003/`（对照版「新大陆/Territory」，功能一致、视觉重设计，commit f0784f5 (PRD v0.1)）。

## 唯一下一步

1. 用户视觉复核三版原型（重点：-001 碑铭/印章、-002 穹顶/地平线、-003 新大陆/制图的观感差异、3D 卡旋转、主题/语言切换），复核后 flip 各 `_d_meta.json` 资产状态（当前均 needs-review）。
2. 三版对照评审并选定最终视觉方向。

## 注意事项

- 原型无真实 Wallet：连接/发布/故障经右下角 "Demo" 面板模拟。
- Key Rotation 已下放 v0.1.1，原型不含。
- 演示 BAP ID / TxID 为占位值，非产品事实。
- 视觉观感（布局重叠、动画手感）未实机确认（本环境无浏览器），需用户确认。
