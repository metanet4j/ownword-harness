# system-design 进度

## 2026-08-14（二）— 三风格拆分：006 / 006-2 / 006-3

### 决策

- 用户要求撤销 -006 内的三风格切换改动（已 `git checkout` 还原，-006 保持纯碑刻与航图）。
- 三种风格各建独立仓库：`own-word-prototype-006`（碑刻与航图）、`own-word-prototype-006-2`（灯塔与信号）、`own-word-prototype-006-3`（地平线与大陆）。DOM 与逻辑完全一致，仅皮肤不同（各仓库独立 `motif.css`），不带切换器。

### 完成项

- 006-2 灯塔与信号：Hero 同心环+脉冲外环+闪烁信号点；BAP ID 铭牌信号面板（深色底+刻度线+亮色等宽字）；徽章光晕；状态/航点闪烁；3D 卡图表环脉冲。
- 006-3 地平线与大陆：黎明暖色渐变+加粗地平线+铜色太阳航行+大陆色带；契约双框铭牌；地图轨迹航点；3D 卡路线+太阳。
- 两仓库各自 `_verify.mjs` 32/32、`_audit.mjs` 17/17、console/runtime/network error 0、320px 无溢出、双主题对比度 AA；独立 Git 提交 `(PRD v0.1)`。
- 预览：`http://127.0.0.1:4311/own-word-prototype-006-2/index.html`、`http://127.0.0.1:4311/own-word-prototype-006-3/index.html`。

### 风险

- 三套对比中，基础功能验证在 -006 已完整通过；-006-2/-006-3 与基础版 DOM/逻辑同源，若后续功能迭代，需同步三个仓库（当前可接受，等待用户选定风格后收敛为一个仓库）。

---

## 2026-08-14 — design-001：v0.1 最终完成版原型（designs/own-word-prototype-006）

### 完成项

- 从零建立 `designs/own-word-prototype-006`（独立 Git 子仓库），未读取前几套原型代码或截图。
- Baoyu Design `import-design-system.mjs` 绑定 React Spectrum S2（primary）；页面用 `Button`/`StatusLight`/`Badge` 组件与 `--rs-*` 令牌，自建受控表单沿用 `s2-*` 视觉类。
- 视觉基调（用户选定）：碑刻与航图融合。衬线碑铭 Hero/身份名、地平线航点动线、签署条钱包请求、BAP ID 铭牌；公共身份页 CSS 3D 立体旋转卡片。
- 覆盖 PRD v0.1 全部用户流程与关键状态（见 feature_list evidence）。

### 验证结果

- 无头 Chrome CDP（提权宿主环境）：`_verify.mjs` 32/32 PASS，`_audit.mjs` 17/17 PASS，console/runtime/network error 0。
- HTTP 预览：`http://127.0.0.1:4311/own-word-prototype-006/index.html`（`python -m http.server 4311 --directory designs`）。
- 关键断言：Copy 传完整 BAP ID、失败值仍可见；语言/主题刷新持久且 BAP ID 不变；1440px 铭牌首屏可见；320px 各关键页无横向溢出；键盘焦点环可见；3D 卡随指针倾斜、离开回正、移动端静态、reduced-motion 停动画；Light/Dark 对比度 AA（dark 下 accent 按钮深色文字）。
- 截图：`preview-desktop.png`、`preview-mobile.png`、`shot-my-identity.png`、`shot-public-3d.png`、`shot-setup.png`、`shot-dark-zh.png`、`shot-mobile-my.png`、`shot-mobile-public.png`。

### 决策

1. 公共身份 3D 用 CSS 3D 卡片升级版（用户选择），非 Three.js；自包含、离线可用。
2. BAP ID mock 格式依据 `reference/bap-master/bap-master/PROTOCOL.md`：`base58(ripemd160(sha256(rootAddress)))`，与协议示例同性质的 fake value。
3. Key Rotation 按 PRD §9 待确认 #5 下放 v0.1.1，不进入原型。
4. dark 主题保留亮蓝 accent（链接对比度达标），accent 按钮改深色文字满足 4.5:1。
5. 演示身份入口与 Prototype 故障注入面板是原型脚手架，不作为产品功能进入 PRD/后端。

### 风险

- 原型内所有 BAP ID、钱包地址均为 mock；不得在后续设计中当作真实数据引用。
- `_verify.mjs`/`_audit.mjs` 依赖本机 Chrome 与 4311 端口服务；换环境需重跑并记录。

### 对 PRD / 后端设计的同步事项

1. PRD §9 待确认的 inline 答案已按确认执行（本地头像、默认 Light、仅会话断开、无分享 URL、Rotation 下放）。建议下次修订把答案移入正文决策记录；非阻塞。
2. PRD 5.6「Leave with unsaved changes」原型实现为应用内返回路径守卫；浏览器级离开（刷新/关标签）未守卫。建议 PRD 明确边界或标注为后续。
3. 核心认知 6.1 Account Switch 语义（取消敏感操作→清除旧上下文→解析新身份）已实现并验证。
4. `spec/backend` 尚无文档；原型交互均映射已有核心认知抽象（WalletProvider、BlockchainTransaction），未引入新核心事实，无同步需求。
5. 核心认知 §12 三项待确认与 v0.1 无关（Artifact/签名封装/链状态映射），不变。
6. 核心认知 10.5「Identity 页首屏突出 BAP ID」已由 My Identity 铭牌落实。

### 文件

- `designs/own-word-prototype-006/`：index.html、styles.css、strings.jsx、app.jsx、_verify.mjs、_audit.mjs、_d_meta.json、vendor/、_ds/react-spectrum/、截图 8 张。
- `_task/system-design/feature_list.json`：design-001 evidence 已写入。
