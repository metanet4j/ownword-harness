# session-handoff.md

## 当前状态

- **当前事项：design-flash-mini-001「flash-mini 原型：穹顶与地平线（全新设计，不参考任何现有实现，mini 紧凑版面）」**，
  `status=in-progress`，`activeItem=design-flash-mini-001`，产出 `designs/design-flash-mini-001`。
- 2026-09-12 用户要求：以全新设计另出一版，不参考任何现有实现代码；要求集合与 `design-astra-001` 一致；
  id=design-flash-mini-001，输出 designs/design-flash-mini-001。为避免双 in-progress，`design-astra-001` 暂置 `blocked`。
- 交付已完成并提交子仓库：`95490f2`（原型本体，PRD v0.1_20260912-094341）、`6c3f5c3`（干净检出复验，PRD v0.1_20260912-094621）。
- 自动化证据：fresh-design 0 命中；模型 28/28；S2 token 28/28、0 自造颜色；浏览器 14/14；axe 15 次 0 violations、
  5 条 incomplete（7 节点）逐条人工复核；对比度 11/11；离线 3/3；18 张截图；干净检出 4405 端口全绿。
- 13 条 doneCriteria 中 12 条已交付并取证，唯一未关闭：⑫ 用户视觉复核（`_d_meta.json` assets.status 仍为 `needs-review`）。
- 未决取舍：卡片整体为鼠标点击便利项，键盘用户通过独立 `Flip card` 按钮可达；若要严格等价，需要把卡片改为真正的可聚焦控件。

## 预览服务

- 一键启动（no-store，项目根为服务根目录）：
  `cd designs/design-flash-mini-001 && python3 verification/serve.py 4400`
- 访问：`http://127.0.0.1:4400/index.html`
- 模拟器：追加 `?sim=1`，可切换四态分流、账户 A/B/C、操作成功/失败；普通预览不显示模拟器。
- 一键验证：`cd designs/design-flash-mini-001 && OWNWORD_PORT=4401 bash verification/run-all.sh`

## 唯一下一步

1. **用户视觉复核** flash-mini 原型：打开 4400 预览（建议同时看 `?sim=1`），确认：
   - 七线穹顶的节奏、疏密与 keystone 汇聚；
   - 无刻度地平的高度与通栏感；
   - 3D Public Identity 卡片正/背面、翻转按钮与 reduced-motion 表现；
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
