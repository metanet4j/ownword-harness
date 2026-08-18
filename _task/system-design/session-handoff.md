# session-handoff.md

## 当前状态

- design-001 已完成：`designs/own-word-prototype-001/`（PRD v0.1 全部 BDD 场景 + Public 3D 身份卡），jsdom 冒烟 56 项断言全过。
- design-002 已完成复制基线：`designs/own-word-prototype-002/`（与 design-001 内容一致，供对照迭代）。

## 唯一下一步

1. 用户指定对照差异方向（视觉 / 交互 / 文案等）→ 在 `own-word-prototype-002` 上迭代，与 `own-word-prototype-001` 对照评审。
2. 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-001/index.html` 与 `/own-word-prototype-002/index.html`（桌面 1440px 与移动 320px，重点：3D 身份卡旋转观感、主题/语言切换、Demo 面板注入场景）。复核后 flip `_d_meta.json` 资产状态。

## 注意事项

- 原型无真实 Wallet：所有连接/发布/故障场景经右下角 "Demo" 面板模拟。
- Key Rotation 已下放 v0.1.1，原型不含。
- 演示 BAP ID / TxID 为占位值。
- 视觉观感（布局重叠、动画手感）未实机确认（本环境无浏览器），需用户确认。
