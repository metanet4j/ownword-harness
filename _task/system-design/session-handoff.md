# session-handoff.md

## 当前状态

- **最终视觉方向已选定：design-002「穹顶与地平线」**（`designs/own-word-prototype-002/`）。
- design-001（碑铭/印章）、design-003（新大陆/Territory）、styles-001（三版风格探索）已封存（feature_list.json status=archived，目录保留）。
- design-002 状态 in-progress，`activeItem`=design-002，继续按用户要求迭代直到定稿。

## 唯一下一步

1. 用户逐条提出 design-002 的修改要求；逐条实现 → 验证（HTTP / Babel / jsdom / 真实 Chrome）→ commit（`(PRD v0.1)`），直至定稿。
2. 定稿后 flip `designs/own-word-prototype-002/_d_meta.json` 资产状态（needs-review → approved），design-002 标 done。

## 注意事项

- design-002 预览：`http://127.0.0.1:4311/own-word-prototype-002/index.html`（改视觉后 Ctrl+Shift+R 强刷绕过缓存）。
- 只改 -002，不动 -001 / -003 / styles。
- 原型无真实 Wallet：连接/发布/故障经右下角 "Demo" 面板模拟。
- Key Rotation 已下放 v0.1.1，原型不含。
- 演示 BAP ID / TxID 为占位值，非产品事实。
- 视觉观感（布局重叠、动画手感）需用户人工确认。
