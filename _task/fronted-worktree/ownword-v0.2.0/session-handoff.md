# 当前实施：D04 修订与版本历史

D03 前端已提交 1fb21a0。共用 IndexedDB 日志接通冻结 Review、真实 AIP/原交易准备、广播、同步及独立后端回读；未知结果恢复只查询原操作，prepared 状态需明确继续。47 项不同测试通过（全套 46 项，图片缓存重建另行补跑 1 项）；lint/typecheck/build 通过。浏览器双击单交易、取消保留草稿、广播回执丢失后刷新恢复且零重播、继续编辑不被清理、独立访客阅读、CRLF 导出与 Proof 均通过，证据 evidence/d03/checks.json。任务清单无障碍名称已修复，阅读页 320px axe 0 违规。

服务：前端 5071、API 5073、官方核心钱包 5078，数据库 ownword_v020；python3 run-services.py 管理。前端运行 D03 最终构建。agent-browser v020-implementation 在新正文草稿 c2bf1c2e-404e-4d62-a2b2-58e1edf566d2，账户 0 已连接，1440×1000 英文浅色；v020-public 独立无钱包会话在公开阅读 53369cff56a462ce6074acf58b26ce11582299d0fe6a8f737af03fc221cecee4，1440×1000。全部故障已解除；浏览器 fetch 只剩无故障的计数/已释放延迟包装，刷新即可清除。其他原稿两份仍保留。

唯一下一步：D04 接通作者创建/继续修订、Review/广播前基线与覆盖复核、/read/:txid/history 历史页，验证新旧版本不变及缺失/分支状态。现有 /versions 阅读按钮需改为设计规定的 /history；后端接口仍 /contents/:txid/versions。lib/content/publish.ts 已有 revisionReference 和签名 MAP；Draft 存储已含 baseTxid/baseMarkdown 及唯一 revisionKey。

D02 后端 876ab3b 保持 clean。主网作者归属因公共历史/checkpoint 不足保留 unverified；隔离验证不代表主网覆盖。D04–D05、实际扩展、公共历史、主网资金广播和用户视觉复核仍未完成。
