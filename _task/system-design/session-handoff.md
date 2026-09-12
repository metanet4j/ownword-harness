# session-handoff.md

## 当前状态

- **当前事项：design-flash-mini-001「flash-mini 原型：穹顶与地平线（全新设计，不参考任何现有实现，mini 紧凑版面）」**，
  `status=in-progress`，`activeItem=design-flash-mini-001`，产出 `designs/design-flash-mini-001`。
- 2026-09-12 用户要求：以全新设计另出一版，不参考任何现有实现代码；要求集合与 `design-astra-001` 一致；
  id=design-flash-mini-001，输出 designs/design-flash-mini-001。为避免双 in-progress，`design-astra-001` 暂置 `blocked`。
- 交付已完成并提交子仓库：`95490f2`（原型本体）、`6c3f5c3`（首轮干净检出复验）；视觉迭代提交 `8c3379c`（3D 卡片/模拟器 dock/抽象光晕穹顶）、`0388301`（迭代后干净检出复验，PRD v0.1_20260912-102440）。
- 2026-09-12 第二轮视觉迭代已完成：3D 卡片增加景深叠层/指针倾斜/translateZ；模拟器改为右下角可开合 dock；穹顶改为固定下层、出屏、光晕、抽象七线。
- 自动化证据（迭代后）：fresh-design 0 命中；模型 28/28；S2 token 28/28、0 自造颜色；浏览器 14/14；axe 15 次 0 violations、
  5 条 incomplete（6 节点）逐条人工复核；对比度 11/11；离线 3/3；19 张截图（含模拟器 dock 展开）；干净检出 4409 端口全绿。
- 13 条 doneCriteria 中 12 条已交付并取证，唯一未关闭：⑫ 用户视觉复核（`_d_meta.json` assets.status 仍为 `needs-review`）。
- 未决取舍：卡片整体为鼠标点击便利项，键盘用户通过独立 `Flip card` 按钮可达；若要严格等价，需要把卡片改为真正的可聚焦控件。

## 预览服务

- 一键启动（no-store，项目根为服务根目录）：
  `cd designs/design-flash-mini-001 && python3 verification/serve.py 4400`
- 访问：`http://127.0.0.1:4400/index.html`
- 模拟器：右下角 `Prototype` 开关，默认收起；`?sim=open` 直接展开，`?sim=1` 启用失败路径。
- 一键验证：`cd designs/design-flash-mini-001 && OWNWORD_PORT=4401 bash verification/run-all.sh`

## 唯一下一步

1. **用户视觉复核** flash-mini 原型：打开 4400 预览（建议同时看 `?sim=1`），确认：
   - 抽象七线的节奏与出屏延伸感、光晕强度；
   - 无刻度地平的高度与通栏感；
   - 3D Public Identity 卡片正/背面、景深叠层、指针倾斜与翻转手感；
   - 右下角 `Prototype` 模拟器 dock 的开合、位置与遮挡情况；
   - mini 单列版面、≤760px 固定底部操作条、320px 完整 BAP ID 首屏；
   - 中英 × 浅深四组合观感，以及 1440/960/768/390/320 响应式。
2. 复核通过后，把 `designs/design-flash-mini-001/_d_meta.json` 的 asset status 由 `needs-review` 改为 `approved`，
   在子仓库提交（commit 信息带 `(PRD v0.1_${datetime})`），再把 `design-flash-mini-001` 置 `done`。
3. 若用户要求调整视觉或交互，在本事项内迭代并复跑 `verification/run-all.sh`；改动提交到
   `designs/design-flash-mini-001` 子仓库，任务文档改动提交到根仓库。
4. `design-astra-001` 保持 `blocked`，等待用户决定是否继续视觉复核或归档；不要未经用户确认同时恢复两个 in-progress。
5. 核心认知 §12 三项待确认不在 v0.1 范围；进入 Artifact/Content/Explorer 前必须按
   `verification/implementation-handoff.md` 的验证方式关闭。

## 常用命令

```bash
# 预览（no-store，项目根为服务根目录）
cd designs/design-flash-mini-001
python3 verification/serve.py 4400
# http://127.0.0.1:4400/index.html?sim=1

# 一键全量验证
OWNWORD_PORT=4401 bash verification/run-all.sh

# 单独运行
node verification/check-fresh.mjs
node verification/check-model.mjs
node verification/check-tokens.mjs
OWNWORD_PORT=4400 node verification/check-browser.mjs
OWNWORD_PORT=4400 node verification/check-offline.mjs
node verification/review-accessibility.mjs
```
