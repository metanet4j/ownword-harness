# session-handoff.md

## 当前状态

- design-001 已完成：`designs/own-word-prototype-001/`（PRD v0.1 全部 BDD 场景 + Public 3D 身份卡）。
- design-002 已完成：`designs/own-word-prototype-002/`（对照版「穹顶与地平线」全新设计，功能与 design-001 一致，视觉重设计）。jsdom 冒烟 32 项断言全过。

## 唯一下一步

1. 用户视觉复核并对照两版：
   - `http://127.0.0.1:4311/own-word-prototype-002/index.html`（穹顶与地平线）
   - `http://127.0.0.1:4311/own-word-prototype-001/index.html`（碑铭/印章基线）
   - 桌面 1440px 与移动 320px；重点：天穹/地平线观感、3D 身份卡旋转、主题/语言切换、Demo 注入场景。
2. 复核后 flip 两版 `_d_meta.json` 资产状态（approved / changes-requested），并按反馈迭代。

## 注意事项

- 原型无真实 Wallet：连接/发布/故障经右下角 "Demo" 面板模拟。
- Key Rotation 已下放 v0.1.1，两版原型均不含。
- 演示 BAP ID / TxID 为占位值，非产品事实。
- 视觉观感（布局重叠、动画手感）未实机确认（本环境无浏览器），需用户确认。
