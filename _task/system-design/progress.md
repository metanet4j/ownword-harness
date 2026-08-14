# system-design 进度

## 2026-08-14 — design-004 穹顶与地平原型（007）

### 决策

- 用户澄清风格：就是穹顶之下加地平（穹顶天幕+地平基准线+刻度秩序感），非天文观测台，无其他风格方向。
- 006-4 已丢失，备份目录 `C:\haodev\system-design-backup` 无 006-4；从零全新构建 `designs/own-word-prototype-007`，未读取任何旧实现。
- design-001 的 006 仓库已移入备份目录，状态改 blocked（与 002/003 一致，保留为对比候选）。

### 完成项

- 隐喻系统：穹顶=话语之天（衬线碑铭体），地平基准线=事实之地（等宽读数），中央刻标=基准中心；身份立于基准线上，BAP ID 是铭牌坐标。
- 功能：覆盖 PRD v0.1 BDD 全部流程（Wallet 全状态、解析分流、Setup 校验、Review、创建生命周期、My Identity、Public 3D 卡、Edit Profile、EN/zh-CN、Light/Dark）。
- 技术：React/ReactDOM/Babel 本地 vendor（unpkg 卡死，改 npm 下载 vendor，无 CDN 依赖）；React Spectrum S2 设计系统 primary。
- 契约：`data-ow-screen`/`data-ow-test`；故障注入 URL 参数 walletFail/resolveFail/noIdentity/incomplete/createFail/copyFail。
- 验证全绿：`_verify.mjs` 82/82（CDP 9252）、`_audit.mjs` 27/27（CDP 9254）、console/runtime/network error 0、320px 无溢出、双主题对比度 AA、3D 8 层视差、reduced-motion 静态。截图 10 张。
- 独立 Git 仓库提交 `a91a91c` `(PRD v0.1)`；`_d_meta.json` 资产 needs-review，等待用户复核。
- 预览：`http://127.0.0.1:4311/own-word-prototype-007/index.html`（服务 `python -m http.server 4311 --directory C:\haodev\ownword\designs`）。

### 风险

- 本会话模型无图像输入，截图未回读模型，视觉检查由 `_audit.mjs` 计算样式断言代替；用户需在浏览器复核视觉效果。
- 007 CDP 端口 9252/9254，与其他原型仓库端口（9222/9224、9232/9234、9242/9244）互斥。
- HTTP 服务曾中途死亡导致验证误报连接拒绝；服务需保持后台运行（job pwsh-1）。

### 对 PRD / 后端设计的同步事项

- 无新同步项：007 严格按核心认知与 PRD v0.1 BDD 实现，未引入新术语、状态或流程。
