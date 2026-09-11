# session-handoff.md

## 当前状态

- **当前事项：design-astra-001「astra 原型打磨至生产实现就绪」**，`status=in-progress`，`activeItem=design-astra-001`，
  产出 `designs/own-word-prototype-s2-astra-001`。
- 2026-09-11 用户裁决：`feature_list.json` 只保留本事项，其余 11 条事项条目已移除（移除前内容见根仓库提交 `9f0584a`）；
  「同时只允许一个 in-progress」的并行破例结束，本事项为唯一 in-progress。同日按用户要求清空本事项的 `evidence` 字段内容
  （权威证据在原型 `verification.md` 与原型内 `evidence/`，删除前文本见根仓库提交 `3b3146a`）。
- astra 子仓库工作区干净，最近提交 `6f39097`（PRD v0.1_20260911-133906）：版面收窄 `main` 1280 → 1120px、双栏 gap 96 → 64px，
  并加 `max-height: 640px` 的矮窗口压缩（1220×555 主操作进首屏：整页 1042 → 771px；320×568 用 fixed 底部操作条）。
  上一提交 `3192c8e`：按用户要求移除公开身份卡旁的视角控件，保留自动旋转与指针拖拽翻面。
- 词典 148 键；token 65/65；断言：模型 74、浏览器 **454**（新增 4 条短窗口断言）、离线 4，axe 38 份 0 violations。
- 12 条 doneCriteria 中 11 条已交付并取证，唯一未关闭：⑪ 用户视觉复核（`_d_meta.json` 资产仍为 `needs-review`）。
- 未决取舍：卡片背面「链上记录」失去键盘入口（只剩拖拽与自动旋转），需要键盘可达时要补一个可聚焦的翻面入口。
- 打磨 round 1–22 的完成项、缺陷与决策见 `progress.md` 2026-09-09 / 09-10 各节；
  BDD 映射与证据索引见原型内 `verification.md`，模拟点生产替换契约见原型内 `implementation-handoff.md`。

## 预览服务

- 本次启动：`http://127.0.0.1:4312/own-word-prototype-s2-astra-001/index.html`
  （no-store 静态服务，根目录 `designs/`，改文件后刷新即生效；服务脚本 `/tmp/astra-preview-server.py`）。
- 备用入口：`http://127.0.0.1:4311/own-word-prototype-s2-astra-001/index.html`
  （另一处实时服务，实测与工作区 `index.html` md5 相同，同为 no-store）。
- 实测：关键资源全部 200；浏览器打开标题正确、React 已挂载（`h1`×1、穹顶×1、地平线×1），
  console 0 error（仅 React DevTools 与浏览器内 Babel 两条已知提示）。

## 唯一下一步

1. **用户视觉复核** astra 原型（本次已改动公开身份页）：确认删除控件后的版面、七线穹顶的节奏与疏密、
   无刻度地平线高度、3D 卡自动旋转与拖拽翻面手感、中英 × 浅深四组合观感，以及 1440/960/768/390/320 版面。
2. 若要求卡片背面键盘可达，补一个可聚焦的翻面入口并补断言；否则保持现状。
3. 复核通过后，把 `_d_meta.json` 的资产状态由 `needs-review` 改为 `approved`，再将 `design-astra-001` 置 `done`；
   若需调整，在本事项内迭代并复跑验证脚本，改动在 astra 子仓库提交且信息带 `(PRD v0.1_${datetime})`。
4. 核心认知 §12 三项待确认不在 v0.1 范围；进入 Artifact/Content/Explorer 前必须按
   `implementation-handoff.md` 的验证方式关闭。

## 常用命令

```bash
# 预览服务（no-store，根目录 designs/）
python3 /tmp/astra-preview-server.py 4312 /home/haodev/ownword/designs

# 原型自检（在原型目录内，先确保 4312 在服务）
cd designs/own-word-prototype-s2-astra-001
node check-model.cjs
node check-copy.cjs
python3 check-tokens.py
OWNWORD_PORT=4312 python3 check-browser.py
OWNWORD_PORT=4312 python3 check-offline.py
```
