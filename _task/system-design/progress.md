# progress.md


## 2026-09-11 design-astra-001 打磨：版面收窄 + 矮窗口压缩（A+B）

### 完成项

- 用户报告 1220×555 窗口（截图 2439×1110 物理像素 ÷ DPR 2）下「界面太宽、太高」，量测定位原因后按 A+B 修：
  1. **收窄内容（B）**：`main` 的 `max-width` 1280 → **1120px**，宽窗口两侧留白；`.workbench` 双栏 gap 96 → **64px**。
  2. **矮窗口压缩（A）**：`@media (max-height: 640px)` 增加页面级规则——topbar 100 → 64px、间距降档、`.page-heading h1` → 32px、表单 padding/gap 收紧、bio 文本域 112 → 72px、头像 76 → 56px、表单操作行 sticky 到视口底；`(max-height: 640px) and (max-width: 650px)` 下改 `position: fixed` 底部操作条并给 `main` 留 104px 余量。
- astra 子仓库提交 `6f39097`（PRD v0.1_20260911-133906）：`app.css`、`check-browser.py`、`verification.md`、`implementation-handoff.md` 与重生成的证据。

### 量测与验证

| 项 | 修前 | 修后 |
| --- | --- | --- |
| 编辑页整页高（1220×555，含通知条） | 1042px | **771px** |
| 主操作行位置（1220×555） | 804–873（低于首屏 249px） | **486–555（可见，sticky）** |
| 主操作行位置（320×568） | 低于首屏 | **499–568（可见，fixed 条）** |
| 表单卡宽（1440 窗口） | 573px | 505px |

- 五套脚本全绿：模型 74、词典 4（148 键）、token 65/65（原 66：`--s2-spacing-1000` 不再被引用）、浏览器 **454/454**（新增 4 条短窗口断言）、离线 4；axe 38 份 0 violations、32 项 incomplete。
- 报告原因：宽 = `main` 上限 1280 大于窗口 1220 导致整宽铺开 + 双栏 gap 96 + `h1` 用 `clamp(36px,4vw,51px)` 在 1220 取 48.8px；高 = topbar 100 + 通知条 87 + 表单卡 682 = 1042px，而页面级没有任何矮窗口断点（唯一 `max-height: 640px` 只管弹窗）。
- 覆盖盲区已补：响应式矩阵只变宽度、高度恒 800，`1220×555` 这类窗口从未被验过；现新增 4 条断言。

### 决策

1. 压缩只在高度 < 640px 生效；390×844 等常规手机高度保持正常滚动。
2. 320×568 用 fixed 底部操作条而非 sticky：卡片内容盒会限制 sticky 的行程（实测只能上移 32px），fixed 才能保证主操作可见。

### 风险 / 待确认

- E1 用户视觉复核仍未关闭；本次改动 `_d_meta.json` 仍为 `needs-review`。
- 卡片背面「链上记录」仍无键盘入口（上一轮遗留，待用户裁决）。

### 唯一下一步

用户刷新预览复核版面（宽窗口留白与矮窗口首屏操作行），确认后关闭 E1。


## 2026-09-11 design-astra-001 打磨：公开身份卡移除视角控件

### 完成项

- 按用户要求移除 Public Identity 3D 卡旁的整组视角控件（用户截图所示区域）：`View chain record`（翻面按钮）、`Pause rotation` / `Rotate identity`、`Reset view`、`Viewing angle` 滑块，以及只为解释该开关而存在的 reduced-motion 提示。
- 交互保留：进入公开身份页仍然自动旋转；指针拖动卡片改变视角（0.35°/px），跨过 90° 露出背面「链上记录」。
- 同步清理：`copy.js` 删除 7 个随之失效的词典键（155 → 148，中英同步）；`app.css` 删除 `.card-actions`、`.rotation-controls`、`.rotation-label` 规则；`components.jsx` 删除不再使用的 `stage` ref。
- astra 子仓库提交 `3192c8e`（PRD v0.1_20260911-123602，34 个文件）。

### 验证结果（`OWNWORD_PORT=4312`，指向本次启动的实时服务）

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 模型断言 | 74/74 | 脚本 stdout（`evidence/model-results.txt` 是 09-09 手工留档的 59，见「发现 3」） |
| 词典契约 | 4/4，148 键（原 155） | `evidence/copy-contract.json` |
| S2 token | 66/66 解析，0 未定义 | `evidence/token-resolution.json` |
| 浏览器 | 450/450（原 451：删 2 条翻面按钮断言、改 1 条 reduced-motion 断言、新增 2 条拖拽断言） | `evidence/browser-results.json` |
| axe | 38 份审计 0 violations；32 项 incomplete 全为 color-contrast | `evidence/axe-incomplete-summary.json` |
| 离线启动 | 4/4（阻断全部外部域） | `evidence/offline-startup.json` |

### 过程中发现

1. **键盘路径变化（取舍需用户确认）**：删掉翻面按钮后，卡片背面只能靠拖拽或自动旋转露出。为保住验收覆盖，`check-browser.py` 新增 `drag_card()`（CDP 鼠标拖动）驱动「跨过 90° 露出链上记录」「拖回正面」「链上记录面 axe 审计」「TxID 复制」四条断言；键盘用户不再有翻面入口。
2. **中文截图与 09-10 提交的版本逐字节不同**：原因是 Adobe Typekit 字体可达性——可达时 6 个字面加载、320px 中文首页整页高 831px，阻断外部域时为 875px。同环境独立复测 320×831 与新证据一致；英文页面及与本次改动无关的截图逐字节相同。中文 `color-contrast` incomplete 因此多出 `.welcome-intro` 节点，`evidence/axe-incomplete-review.json` 已覆盖（浅色 13.7:1、深色 12.44:1）。差异属字体环境，不是本次改动引起。
3. `evidence/model-results.txt` 仍是 59 的过期手工留档（`check-model.cjs` 只打印 stdout、不写该文件）；用户此前要求清空 `feature_list.json` 的 `evidence` 字段，故本轮不再回填，待用户决定该文件是刷新还是删除。

### 决策

1. 只删控件、保留自动旋转与拖拽：3D 公开身份的视觉命题不退化，改动范围最小。
2. 断言迁移到拖拽而不是删除覆盖：双面链上记录、单面在可访问树、TxID 复制仍逐条有证据。

### 风险 / 待确认

- 背面「链上记录」不再有键盘入口；若要求键盘可达，需补一个可聚焦的翻面入口（待用户裁决）。
- E1 用户视觉复核仍未关闭（`_d_meta.json` = `needs-review`）。

### 唯一下一步

用户复核删除后的版面：`http://127.0.0.1:4312/own-word-prototype-s2-astra-001/index.html`；确认是否需要键盘翻面入口或恢复某个控件。


## 2026-09-11 用户裁决：feature_list.json 只保留 design-astra-001，启动 astra 预览服务

### 完成项

- 按用户要求把 `feature_list.json` 从 12 条事项裁剪为只保留 `design-astra-001`（astra 原型打磨至生产实现就绪），`activeItem` 由 `design-flash4.1-002` 改为 `design-astra-001`。移除的 11 条：design-flash-001/002/003/004、design-flash4.1-001/002、design-001/002/003、styles-001、harness-001；移除前内容见根仓库提交 `9f0584a`。裁剪后 `in-progress` 恰好 1 个，并行破例结束。
- 启动 astra 原型预览服务：`http://127.0.0.1:4312/own-word-prototype-s2-astra-001/index.html`（no-store 静态服务，根目录 `designs/`，改文件后刷新即生效）。
- 4311 已有另一处实时服务，同样指向 `designs/` 且返回当前工作区文件，保留作备用入口。
- 按用户要求清空 `design-astra-001` 的 `evidence` 字段内容（9102 字符 → 空，字段保留）；权威证据仍在 `designs/own-word-prototype-s2-astra-001/verification.md` 与原型内 `evidence/`，删除前的文本可在根仓库提交 `3b3146a` 回溯。

### 验证结果

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| HTTP 资源 | `index.html`、`app.css`、`app.jsx`、`components.jsx`、`model.js`、`copy.js`、`_ds/react-spectrum-s2/_ds_bundle.js`、`vendor/react.development.js`、`brand/ownword-mark.svg` 全部 200 | curl 实测（4312） |
| 服务一致性 | 4311 返回的 `index.html` 与工作区文件 md5 相同（`7937df33517f18820d60b10820116bb5`），两者均为 no-store | curl + md5sum |
| 页面渲染 | 标题与 URL 正确；`h1`×1、穹顶×1、地平线×1、按钮×5；console 仅 2 条已知提示（React DevTools、浏览器内 Babel），0 error | agent-browser 会话 `astra-e9671acd2448` |
| JSON 合法性 | 裁剪后 `feature_list.json` 解析通过，12 条 doneCriteria 与 output 字段完整，唯一 in-progress | `python3 -c json.load` |

### 决策

1. 预览服务不改动 astra 仓库：服务脚本放在 `/tmp/astra-preview-server.py`，原型目录只做被测对象，不新增非交付文件、不产生未提交改动。
2. 本轮不改原型代码，也不重跑五套验证脚本（工作区处于 `babe8ef` 干净状态，上一轮 round 22 结果即当前基线）；用户复核后如要迭代，再按 `verification.md` 命令复跑。
3. 移除的事项条目不留在本文件，靠根仓库 git 历史回溯：事项状态只有一份权威记录。

### 风险 / 待确认

- astra 的 12 条 doneCriteria 中，E1 用户视觉复核仍未关闭；本模型无图像输入能力，截图的观感判断只能由用户完成。

### 唯一下一步

用户视觉复核 astra 原型（七线穹顶节奏、无刻度地平高度、3D 卡翻面手感、中英 × 浅深、五档视口），确认后再定打磨范围。


## 2026-09-11 design-flash4.1-002 从零完整交付：穹顶与地平线

### 完成项

- 新增事项 `design-flash4.1-002`（`feature_list.json`，`status=in-progress`，`activeItem` 改为 `design-flash4.1-002`，`output=designs/own-word-prototype-s2-flash4.1-002`）；验收标准沿用 `design-flash-001` 的 13 条。
- 约束遵守：设计过程**未读取任何现有原型实现代码**（design-001/002/003、styles-001、astra、flash-001/002/003/004、flash4.1-001）；事实依据只有核心认知、PRD v0.1、`designs/react-spectrum-s2` 与 `reference/`。
- 一次性完整交付，不再分两步：交付目录包含 `index.html`、`styles.css`、`src/core/core.js`（UMD 纯逻辑，Node/浏览器同源）、`src/ui/app.jsx`、本地 React/ReactDOM/Babel vendor、设计系统消费副本 `_ds/react-spectrum-s2`、完整证据与文档。
- 视觉命题（独立实现）：**七线穹顶＝七条嵌套立方拱线**（`DOME_ARCHES` halfWidth/height；控制点 y＝horizon−4h/3 使拱顶精确为 h；端点严格落在地平线）；**无刻度地平**＝整幅唯一一条 1px 线，与穹顶基线共用 `HORIZON_RATIO=0.62`；**3D Public Identity**＝站在地平线上的翻面卡（正面 Profile/背面 Proof，按钮、←→、Enter/Space、40px 拖拽，隐藏面 `aria-hidden`+`tabindex=-1`，reduced-motion 无过渡）。七条线对应 PRD §1 七项能力，第 05 条按 §9 第 5 项画虚线 deferred。
- 功能范围：PRD 28 条场景可交互（5.1–5.6、8.8、5.9、5.10）。WalletDialog 模拟 Approve/Reject/System failure；resolve 四态；创建成功/取消/失败；Copy 完整 BAP ID（CDP 读取浏览器剪贴板实测）；Edit 保存/取消/离开保护；Account Switch 取消敏感操作并清旧 Identity；Disconnect；中英×浅深即时切换且持久化，协议值不变。
- flash 子仓库已提交：`f3ce701`（PRD v0.1_20260911-0852，1084 个文件）。

### 验证结果（`bash verification/run.sh`，exit=0 全绿）

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 模型断言 | 57/57（几何 G01–G10、能力 C01–C05、标识 I01–I05、校验 P01–P05、状态 S01–S23、术语 T01–T05、视图 V01–V04） | `evidence/model-results.txt`、`geometry.json` |
| S2 token | 73/73 引用解析（设计系统 2511 变量），项目 CSS 0 原始颜色字面量 | `evidence/token-resolution.{json,txt}` |
| 术语 | 禁区用词 0 命中；en/zh-CN 各 206 key | `evidence/term-scan.txt` |
| 无 CDN | index 实际加载 13 个文件 0 远程 URL；Typekit `font-faces.css` 明确不加载 | `evidence/no-cdn.txt` |
| 浏览器 BDD | 85/85；28 条场景全过；0 page error / 0 console error / 0 外部请求 | `evidence/browser-checks.txt`、`console.txt`、`network.txt` |
| 响应式 | 80 组全绿（320/390/768/960/1440 × light/dark × en/zh-CN × Welcome/My Identity/Setup/Resolution failed），无溢出、主 CTA 首屏、唯一地平线 0 tick、7 拱线、BAP ID 首屏实测可见 | `evidence/responsive-matrix.jsonl`、`screens/*.png`（32 张） |
| axe | 25 状态 violations 0；191 incomplete 全为 color-contrast；12 token 对最低 4.51:1 | `evidence/axe/*.json`、`axe-incomplete-summary.json`、`contrast-review.{json,txt}` |
| 干净环境 | 从仅含 git 跟踪文件的临时目录复跑全绿：模型 57/57、token 73/73、浏览器 85/85、axe 0 violations | `evidence/clean-env-run.txt` |

### 过程中发现并修正的缺陷

1. **设计系统按钮色阶在深色下不达 AA**：`components.css` 的 `.s2d-button-accent` 白字在深色仅 3.51:1；项目样式按 S2 语义背景角色覆盖为 `--s2-accent-background-color-default`，两主题 ≥4.51:1，缺口记入 `verification.md` 与交接文档。
2. **320px 卡片内容裁切**：窄屏 `.ow-card-anchor` 的 `min-height:160px` 使卡片超过地平线可用高度，BAP ID 被裁剪；改为卡片高度≤地平线可用空间并压缩窄屏卡片排版，同时 My Identity 面板新增首屏完整 BAP ID 行，Tab/命中测试确认可见。
3. **桌面表单 CTA 首屏不可见**：`Review/Save` 在 768/960/1440 位于首屏之下；`.ow-form-actions` 改为全尺寸 sticky，80 组矩阵复验主 CTA 全部首屏可见。
4. **干净环境剪贴板/网络端口硬编码**：`browser-check.py` 曾把 4321 写死，clean-env 的 4331 复跑误报；改为从 `OWNWORD_URL` 派生 origin 与白名单后 clean-env 全绿。
5. **axe incomplete 处理**：3D 变换卡片内文字 axe 无法计算背景，产生 191 个 `color-contrast` incomplete（非 violation）；`axe-review.py` 逐节点列出并人工重算 token 对比对，最低 4.51:1。

### 决策

1. 七线穹顶采用**嵌套立方拱线**（非纬线环/经线弧），几何公式与断言在 `core.js` + `model-check.mjs` 中唯一表达，便于 Node/浏览器共同验证。
2. 纯逻辑用 UMD `core.js`，Node 与浏览器加载同一份；视图用 React + 本地 Babel，生产按交接文档预编译。
3. 设计系统只加载实际需要的本地 CSS 与 bundle；Typekit 远程字体声明不加载，使用系统字体回退，满足无 CDN。
4. URL 参数（`?screen/theme/locale/hold/nextWallet/...`）只用于评审/截图钉住状态，不写回链上事实；用户显式切换才持久化偏好。
5. 所有原型控制、fixtures、人为延时在 `implementation-handoff.md` 标注为生产移除项。

### 风险 / 待确认

- **用户视觉复核未完成**（第 ⑫ 条）：`_d_meta.json` 资产状态保持 `needs-review`；本模型无图像输入能力，穹顶节奏、地平线高度、卡片翻面手感与断点观感需用户目视确认。
- 核心认知 §12 三项（Inscription Number 端点、Artifact 签名封装、Blockchain 状态映射）属 Artifact/Content/Explorer 范围，本版未实现，已在交接文档逐项标注验证方式与“待确认”。
- 原型 BAP ID、Profile、txid 均为 fixture；真实密钥/签名/交易替换点见 `implementation-handoff.md`。

### 唯一下一步

用户打开预览：
`http://127.0.0.1:4311/own-word-prototype-s2-flash4.1-002/index.html`
（深色中文：`?theme=dark&locale=zh`；证明面：`?screen=my-identity&face=back`）。
确认后由用户把 `_d_meta.json` 资产状态改为 `approved`，再把 `design-flash4.1-002` 置 `done`；如需调整，本事项内迭代并重跑 `bash verification/run.sh`。
## 2026-09-11 design-flash4.1-001 第一步：首页风格（穹顶与地平线）

### 完成项

- 新增事项 `design-flash4.1-001`（`feature_list.json`，`status=in-progress`，`activeItem` 改为 `design-flash4.1-001`，`output=designs/own-word-prototype-s2-flash4.1-001`）；验收标准沿用 `design-flash-001` 的 13 条。
- 约束：设计过程**未读取任何现有原型实现代码**（design-001/002/003、styles-001、astra、flash-001/002/003/004）；事实依据只有核心认知、PRD v0.1、`designs/react-spectrum-s2` 与 `reference/`。
- 第一步交付首页：`index.html` + `styles.css` + `src/core/*`（几何/能力/文案/状态机/示例数据）+ `src/ui/*`（视图）+ `vendor/`（本地 React）+ `_ds/react-spectrum-s2`（设计系统导入副本）。
- 视觉命题落地：**七线穹顶＝七条纬线环**（半球方程 `rx²+z²=R²`，穹顶高度 0..0.94R 等分，12° 正交俯视投影；每条环远侧实、近侧虚）；**无刻度地平**＝整幅唯一一条 1px 直线，由 DOM 绘制并与穹顶底平面共用同一 `--u` 换算；**3D Public Identity**＝中心骑在地平线上的翻面卡（正面 Profile、背面 Proof）。
- 七条线自下而上对应 PRD 第 1 节七项能力；第 05 条按第 9 节第 5 项画虚线并标 `Planned for v0.1.1`；能力文本索引落在地平线之下。
- 架构：纯逻辑层 node 与浏览器加载同一份文件；视图用 `React.createElement`，**不引入浏览器内 Babel/JSX**；运行时本地化，无 CDN。
- flash 子仓库已初始化并提交：`7472672`（PRD v0.1_20260911-0342，1062 个文件）。

### 验证结果（`bash verification/run-step1.sh`，exit=0 全绿）

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| 模型断言 | 56/56（几何 G1–G19、能力 C1–C5、文案 I1–I4、状态机 P1–P15、示例 S1–S6、禁区词 T1–T3、装配 A1–A4） | `evidence/model-results.txt`、`geometry.json` |
| S2 token | 68/68 引用解析（设计系统 2511 变量），0 颜色字面量 | `evidence/token-resolution.{json,txt}` |
| 浏览器矩阵 | 20 组（320/390/768/960/1440 × 浅深 × 中英）无溢出/无重叠/CTA 首屏/卡片贴线/两面不溢出 | `evidence/browser-checks.txt`、`responsive-matrix.jsonl`、`screens/*.png` |
| axe | 7 个状态 violations 0；87 个 incomplete 节点实例去重 62 组逐条实测对比度 | `evidence/axe/*.json`、`axe-manual-review.json` |
| 对比度 | 69 组全部达标（信息性最低 4.81:1；装饰性 aria-hidden 文本单列） | `evidence/contrast.{json,txt}` |
| 交互 | 按钮/←→/Enter/拖拽翻面、阈值 40px、Copy 完整 BAP ID、Copied 不位移、失败保留标识、语言与主题持久化且 BAP ID 不变、reduced-motion 无过渡、Tab 焦点可见 | `browser-checks.txt` B18–B36 |
| 运行期 | 0 页面错误、0 console error、0 外部请求（同源 29 项） | `console.txt`、`network.txt` |
| 干净环境 | 默认 headless 浏览器（触摸档 1.25×）复跑同样 38/38 全绿 | `clean-env-run.txt` |

### 过程中发现并修正的缺陷

1. **指针捕获吞掉按钮点击**：卡片 `pointerdown` 时 `setPointerCapture` 使 click 落在卡片而非按钮上，鼠标点击翻面/复制失效 → 改为按钮不参与拖拽，位移超过 8px 才 capture（`browser-checks.txt` B21/B26 覆盖）。
2. **触摸档卡片溢出**：`--s2-scale: 1.25` 下 320/768/960 的证明面内容超出固定卡片高度 → 卡片高度改为随 `--s2-scale` 缩放，并加高窄屏档（B6 覆盖两种档位）。
3. **深色 CTA 对比度**：设计系统 `.s2d-button-accent` 深色白字仅 3.51:1（AA 需 4.5）→ 只在 CTA 容器内改用 `--s2-accent-color-700`（5.25:1），缺口入 `verification.md` 缺口表。
4. **浏览器缓存导致复现失真**：`python -m http.server` 的启发式缓存会让复现读到旧 `styles.css`（一度出现"改了 CSS 断言不变"）→ 新增 `verification/serve.py`，显式 `Cache-Control: no-store`，并写入复现文档。
5. **地平线在 compact 档缺少定位**：`.ow-horizon` 的 `top` 只写在 wide 媒体查询里，窄屏落到容器顶部 → 常量统一到基础规则并加断言（G15 + B3）。

### 决策

1. 视图不用浏览器内 Babel/JSX，改用 `React.createElement`：少约 3 MB 运行时与首屏转译，且 `src/core` 因此能被 node 直接加载，模型断言与浏览器测的是同一份几何与状态代码。
2. 七条线改为**纬线环**而不是经线弧：与"穹顶"语义一致、可用半球方程严格检验，并与既有原型的经线表达形式区分开。
3. 地平线由 **DOM** 绘制（不是 SVG 内一条线）：保证它在任何视口都通栏、且与穹顶底平面用同一个 `--u` 对齐，便于断言。
4. 能力文本索引放在**地平线之下**（地面＝链上事实），穹顶之上只留产品能力与文案；第 05 条 deferred 用虚线环 + 徽标双表达，不靠颜色单独表达状态。
5. URL 参数只用于评审/截图钉住状态，不写回存储；用户显式切换才持久化。
6. 验证服务器改用 `verification/serve.py`（no-store），并把"默认 headless 浏览器复跑"作为干净环境证据。

### 风险 / 待确认

- **用户视觉复核未完成**（第 ⑫ 条）：本步只交付首页风格，穹顶节奏、地平线高度、卡片翻面手感与断点观感需用户目视确认；`_d_meta.json` 资产状态保持 `needs-review`。
- 桌面档（`--s2-scale: 1`）与触摸档（1.25×）是设计系统的两套尺寸：验收截图取自桌面档，触摸档另有独立复跑证据；两档均已通过同一套断言。
- 深色下头像首字母（装饰性 `aria-hidden` 文本）实测 3.51:1，低于正文 AA；已单列记录（姓名文字重复表达同一信息）。
- 核心认知第 12 节三项待确认不在首页范围，第 2 步交付时按"未关闭不得写成事实"处理。

### 唯一下一步

用户打开 `http://127.0.0.1:4311/own-word-prototype-s2-flash4.1-001/index.html`（深色中文：
`?theme=dark&locale=zh`，翻面态：`?face=proof`）确认首页风格；确认后进入第 2 步：实现 PRD v0.1 §5（5.1–5.4、5.6、5.7）
与 §8.8、§9 裁决的全部场景，补齐状态机、生产替换契约与 13 条 doneCriteria，并把 `_d_meta.json` 资产状态置 `approved`。

## 2026-09-10 design-flash-004 立项并交付第一步：首页风格（穹顶与地平线）

### 完成项
- 新增事项 `design-flash-004`（`feature_list.json`），`status=in-progress`，`activeItem` 由 `design-flash-003` 改为 `design-flash-004`；沿用 `design-flash-001` 的 13 条 doneCriteria。用户于 2026-09-10 指定交付，并要求**第一步先给首页风格、单个 HTML、提供预览地址，确认后再继续**。
- 第一步交付 `designs/own-word-prototype-s2-flash-004/index.html`（单页）：七线穹顶（椭圆弧经线，半球正视投影，正弦间距）、1px 通栏无刻度地平、站在地平线上的 3D Public Identity 卡（正/背面翻转）、七线图例、S2 token 条；中英与浅深可切换且刷新持久。
- 设计系统按 baoyu-design 消费流程导入为 `_ds/react-spectrum-s2`，绑定写入 `_d_meta.json`（`assets.status=needs-review`）。
- 证据与文档：`verification/run-step1.sh`（一键复现）、`verification/probes.js`、`verification/geometry-check.js`、`verification.md`、`README.md`、`.gitattributes`。
- flash 子仓库已初始化并提交：`8a17e8b`（1000 个文件，PRD v0.1_20260910-0745）。

### 验证结果
- `bash verification/run-step1.sh` 本轮 63 项断言全绿（exit=0）：
  - 几何与状态模型 39/39（node 加载浏览器同一份 `app.js`）：七线均起于穹顶顶点、落在地平线，脚点严格左右有序且正弦间距；卡片矩形不压任何一条线；恰好一条 active、一条 deferred。
  - 响应式 320/390/768/960/1440：无横向溢出、CTA 首屏可见、无可聚焦元素重叠、触控目标 ≥24px。
  - axe 20 状态（5 视口 × 浅深 × 中英）＋ 翻面态：violations 0。
  - 对比度：48 采样最低 3.51:1 全部达 AA；对 axe 报的 46 个 incomplete 节点逐节点手工重算，最低 3.51:1、0 失败。
  - 术语：中英页面禁区用词（注册账号／登录账号／Verified Identity／Create BAP NFT 等）0 命中；Publish 未与 submit/broadcast 混用。
  - 交互与偏好：每个 Tab 停靠点有可见 outline；方向键可翻转并复位；reduced-motion 移除翻转过渡；Copy 携带完整 BAP ID；刷新后中英×浅深持久且 BAP ID 不变；console/errors 0 条。
- 无外部 CDN：交付文件 0 条 http(s) 资源引用（SVG 命名空间除外）；设计系统的 Typekit 远程字体声明未被引用，改用本地 face + 系统字体回退。

### 决策
1. 第一步只交付一个自包含 `index.html`（+ 本地 `styles.css`/`app.js`），不引入 React/Babel/设计系统 bundle：单文件便于你直接审阅风格，完整运行时在第 2 步接入（届时按设计系统提示本地化 vendor，仍然无 CDN）。
2. 用 URL 参数 `?theme=&locale=` 钉住 UI 状态：只为评审与截图可复现，不写入 localStorage，也不影响任何身份/链上值。
3. 状态色与选中态不靠颜色单独表达：选中态同时有 `aria-pressed`，焦点色改用已定义的 `--s2-focus-indicator-color`。
4. 穹顶与卡片共用一套画布几何：卡片列＝画布宽 30%（右列），卡片顶＝地平线下 74 画布单位，保证任何视口下经线都不压卡片。

### 风险 / 待确认
- **用户视觉复核未完成**（13 条 doneCriteria 第 ⑫ 条）：本模型无图像输入能力，穹顶节奏、地平线位置、3D 翻转手感与断点观感必须由你目视确认；`_d_meta.json` 资产状态保持 `needs-review`。
- axe 报 color-contrast incomplete（无法自动判定装饰层上的文本背景）：已逐节点人工重算并记录，属人工复核而非自动判定。
- 设计系统缺口：`--s2-focus-ring-color` 被自带 `components.css` 引用但未在 `tokens/` 定义（回退 `--s2d-accent`）；`.s2d-button-secondary` 深色下对比不足，本页改用 `--s2d-layer-raised`。需反馈设计系统维护者。
- 剩余 12 条 doneCriteria（BDD 全覆盖、生产替换契约、干净环境复现等）属第 2 步。

### 唯一下一步
用户打开 `http://127.0.0.1:4311/own-word-prototype-s2-flash-004/index.html`（深色中文：加 `?theme=dark&locale=zh`）确认首页风格；确认后实现 PRD v0.1 §5（5.1–5.10）、§8.8 与 §9 裁决的全部场景，逐条补齐 13 条 doneCriteria 证据。

## 2026-09-09 design-astra-001 立项并激活：astra 原型打磨至生产实现就绪

### 完成项
- 新增事项 `design-astra-001`（`feature_list.json`），`status=in-progress`，`activeItem` 由 `design-002` 改为 `design-astra-001`；写入 12 条 doneCriteria（BDD 全覆盖、术语一致、S2 一致性、无障碍、响应式、双语双主题、状态断言、生产替换契约、无 CDN 依赖、证据可复现、用户视觉复核、提交规范）。
- `design-002` 置为 `archived` 并加 `statusNote`：当前视觉方向由 `designs/own-word-prototype-s2-astra-001` 承接，目录与证据保留、不再迭代。至此 `in-progress` 唯一。
- 基线确定：`designs/own-word-prototype-s2-astra-001` @ `d7706da`（09-06 00:18）。回退前状态（412ca12）保存在分支 `backup/astra-412ca12` 与 `stash@{0}`；按用户裁决，本次打磨**不使用** backup 分支成果。
- 激活前按开工门禁完整阅读 `_task/system-design/AGENTS.md`、`CLAUDE.md`、`feature_list.json`、`progress.md`、`session-handoff.md`，并核对核心认知第 11/12 节与 PRD v0.1 第 5、8.8、9 节范围。

### 验证结果
- `feature_list.json` 经 JSON 解析校验通过：6 个事项，`in-progress` 恰好 1 个（`design-astra-001`），其余为 archived/done。
- 原型基线核对：工作区 `git status` 干净，HEAD = `d7706da`，1130 个跟踪文件；`index.html` 引用 unpkg CDN（回退后状态），`vendor/` 已随 stash 移出。
- 预览可用性实测：`http://127.0.0.1:4312/own-word-prototype-s2-astra-001/index.html` 为实时服务（返回回退版本，`lab.html` 404）；4311 是快照服务，仍返回回退前内容，不能用于本轮打磨的观测。

### 决策
- feature id 采用 `design-astra-001`：`verification.md` 第 7 行已将该 id 记为当前任务，避免新增重复命名。
- 打磨基线为 `d7706da`，不恢复已回退的 13 个提交（含离线启动、演练台分离、实现交接文档、行尾修复）；这些能力若仍需，按 doneCriteria 重新实现并单独取证。
- 核心认知第 12 节三项待确认（Inscription Number 端点、Artifact 签名封装、Blockchain 状态映射）不作为本轮原型阻塞，但必须按 doneCriteria 第 8 条在实现交接文档中显式标注验证方式。

### 待办
- 按 doneCriteria 逐项打磨与取证；每完成一项：astra 子仓库提交（`(PRD v0.1_${datetime})`）+ 更新本文件与 `feature_list.json` 证据。
- 打磨完成后 `_d_meta.json` 资产状态由用户确认后 flip 为 approved。

### 缺口清单（round 1，按 doneCriteria 分组）

依据：PRD v0.1 第 5 节 / 8.8 / 第 9 节裁决逐条枚举得 **28 条在范围内场景**（§5.1×3、§5.2×2、§5.3×4、§5.4×5、§5.5×3、§5.6×3、§8.8×3、§5.9×3、§5.10×2；§5.7×3 按第 9 节第 5 项裁决下放 v0.1.1 排除），对照 `designs/own-word-prototype-s2-astra-001` @ `d7706da` 的实现与 `verification.md` 映射。

| 组 | 缺口 | doneCriteria | 处置 |
| --- | --- | --- | --- |
| A 观测层 | A1 `check-browser.py` 硬编码 `127.0.0.1:4311`；4311 现为快照服务，跑它等于验证错的版本 | ⑩ | 已改为读 `OWNWORD_URL` / `OWNWORD_PORT` |
| A 观测层 | A2 `verification.md`「复现与观测」只有 Windows 路径与 4311，缺跨平台与实时服务前提 | ⑩ | 待改 |
| A 观测层 | A3 响应式只验 320px + 1440 截图，未覆盖 390/768/960 | ⑤ | 待改 |
| A 观测层 | A4 axe 只拦 critical/serious，未断言 0 violations，incomplete 未逐条记录 | ④ | 待改（现状：32 份审计 violations=0、incomplete=26 全为 color-contrast） |
| B 依赖与卫生 | B1 `index.html` 依赖 unpkg 三条 CDN（React/ReactDOM/Babel），`font-faces.css` 依赖 use.typekit.net 字体 | ⑨ | 待处理（本地化或明确降级） |
| B 依赖与卫生 | B2 无 `.gitattributes`；HEAD 为 LF，Windows 侧编辑会引入 CRLF 全量差异 | ⑨ | 待加 `* text=auto eol=lf` |
| C 生产契约 | C1 无实现交接文档：钱包连接与签名、BAP 解析与 Indexer、头像存储、交易广播与确认、状态归一化五类模拟点未文档化 | ⑧ | 待产出 |
| C 生产契约 | C2 核心认知第 12 节三项待确认未在原型侧标注验证方式 | ⑧ | 待产出 |
| C 生产契约 | C3 原型期入口（页脚 `Interactive prototype` 面板、模拟失败与复制失败开关）未标注为可移除 | ⑧ | 待产出 |
| D 验收覆盖 | D1 28 条场景需逐条映射到脚本断言 + 证据文件（当前 `verification.md` 为粗粒度映射） | ① | 待补细 |
| D 验收覆盖 | D2 §5.5「BAP ID 出现在首屏」仅桌面断言，320 未断言 | ① | 待补 |
| D 验收覆盖 | D3 §5.10「图标按钮有可访问名称」仅靠 axe 间接覆盖 | ① | 待补显式断言 |
| D 验收覆盖 | D4 §5.9「状态不依赖颜色」无显式断言 | ① | 待补显式断言 |
| D 验收覆盖 | D5 核心认知第 11 节可验证验收中属 v0.1 范围的第 6/7/10/11 项未映射 | ② | 待核对并映射 |
| E 用户复核 | E1 `_d_meta.json` 资产状态仍为 `needs-review` | ⑪ | 待用户确认 |

### round 1 结果（2026-09-09，提交 `acafbd9`）

关闭 A1–A4、B2、D2–D4：

- **A1/A2**：`check-browser.py` 改读 `OWNWORD_URL` / `OWNWORD_PORT`（默认 4311）；`verification.md` 复现段改为跨平台，并给出“先 `diff` 确认服务的是当前工作区文件”的判别命令。
- **A3**：响应式矩阵由 320px 扩为 320/390/768/960 + 1440 桌面，`inspect()` 内每屏每组合逐宽度断言。
- **A4**：axe 断言由“无严重/致命”收紧为 **0 violations**；incomplete 逐条记录（屏幕/规则/目标/原因）到 `evidence/axe-incomplete-summary.json`。
- **观测缺陷（新发现）**：切换语言或主题后立即审计会采到按钮 150ms `color/background/border` 过渡的中间色，导致 `ready zh/light` 误报对比度 4.17:1（`#f1f1f1` on `#3d65fb`）。加 `settle()` 等待有限过渡结束后，同一页面计算样式为 `rgb(255,255,255)` on `rgb(59,99,251)`，axe 0 violations。判定为观测方法缺陷，非产品缺陷；两条路径均留证。
- **B2**：新增 `.gitattributes`（`* text=auto eol=lf` + 二进制声明），消除 Windows 侧编辑产生的全量行尾差异。
- **D2/D3/D4**：新增显式断言——320px 下 BAP ID 首屏可见、图标按钮具备可访问名称、状态不以颜色单独表达（`span[role="img"]` 与 `.s2d-status` 检查）。

验证：`node check-model.cjs` 59 项通过；`OWNWORD_PORT=4312 python3 check-browser.py` **360 项通过**，32 份 axe 审计 0 violations，26 项 incomplete 全为 `color-contrast`（文本位于装饰层、渐变或伪元素之上，axe 无法判定背景；目标与原因见 `evidence/axe-incomplete-summary.json`），`evidence/browser-errors.txt` 为空。

仍未关闭：B1（CDN 依赖）、C1–C3（生产替换契约文档）、D1（28 条场景逐条映射）、D5（核心认知第 11 节映射）、E1（用户视觉复核）。

### round 2 结果（2026-09-09，提交 `a88071d`）

关闭 B1、C1–C3：

- **B1 本地化启动依赖**：从 unpkg 取回 React 18.3.1、ReactDOM 18.3.1、`@babel/standalone` 7.29.0 三个原文件放入 `vendor/`，`openssl dgst -sha384` 计算的哈希与 `index.html` 既有 `integrity` 值逐一相等；`index.html` 改引本地路径，CDN 引用归零。来源、版本、大小与哈希记入 `vendor/README.md`。字体仍外链 `use.typekit.net`，许可不允许随仓库分发，故保留外链并记录离线回退到系统字体的降级行为。
- **新增 `check-offline.py`**：以 `--allowed-domains 127.0.0.1,localhost` 阻断全部外部域，断言启动脚本同源、Welcome 渲染、启动占位被替换、Babel 离线编译 JSX 并走到 Setup。4 项通过，`evidence/offline-errors.txt` 为空。
- **C1–C3 生产替换契约**：新增 `implementation-handoff.md`——状态机契约（`epoch` 会话序号、敏感操作取消、draft/profile 分离、校验规则、四态分流）、11 项模拟点到生产替换的输入输出与验收、不得丢失的可观察行为、生产替换清单；核心认知第 12 节三项待确认单列，未关闭前不得写成事实；演示面板、fixtures 与人为延时明确标注为不得进入生产。

验证：`node check-model.cjs` 59 项；`OWNWORD_PORT=4312 python3 check-browser.py` 360 项（切换 vendor 后重跑通过）；`OWNWORD_PORT=4312 python3 check-offline.py` 4 项；axe 0 violations、26 项 incomplete 记录不变。改动后证据仅 `public-*` 截图因 3D 自动旋转存在像素差异。

仍未关闭：D1（28 条场景逐条映射到断言与证据文件）、D5（核心认知第 11 节范围内条目映射）、E1（用户视觉复核后 flip `_d_meta.json`）。

### round 3 结果（2026-09-09，提交 `88d7c80`）

关闭 D1、D5：

- **D1**：`verification.md` 的 BDD 对应改为 **28 条场景逐条映射**（PRD 第 5.7 节 3 条按第 9 节第 5 项裁决排除），每条给出断言名与证据文件；同时补 5 条缺失的显式断言——连接后显示 Connected、解析失败解释并给出 Try Again/Disconnect、已发布身份直接进入 My Identity、My Identity 呈现头像/姓名/类型/简介/BAP ID 五项、切换深色后语义表面令牌改变。补断言过程中发现原脚本对 §5.1 成功、§5.3 首条与失败、§5.5 字段完整性只有间接覆盖。
- **D5**：新增「核心认知可验证验收映射（v0.1 范围内）」，把第 11 节中属 v0.1 的第 6/7/10/11 条映射到断言；其余 8 条属 Content、Artifact、Relationship、Binding，本版无对应界面。
- 模型输出落盘为 `evidence/model-results.txt`（59 项），使模型断言与浏览器断言都有可提交的证据文件。

验证：`OWNWORD_PORT=4312 python3 check-browser.py` **365 项通过**（新增断言全部通过），axe 仍 0 violations、26 项 incomplete；`node check-model.cjs` 59 项。

仍未关闭：E1（用户视觉复核）。另需复核 doneCriteria ②（术语与核心认知一致、无禁区用词）与 ③（token 引用 100% 解析）是否有自动化证据，④ 的 26 项 incomplete 需给出逐条复核结论。

### round 4 结果（2026-09-09，提交 `c3915cd`）

关闭 doneCriteria ②③④ 的证据缺口：

- **② 术语与禁区用词**：按核心认知第 2.3 节扫描原型文案与结构，禁区词命中 0（`注册`、`登录`、`sign up`、`log in`、`register`、`Verified`、`BAP NFT`、`Create BAP NFT`、`Broadcast`、`Push`）；唯一 `Submit` 命中是 `onSubmit` 事件处理器名而非用户文案；Publish 用词统一为 `Published` / `Publishing`。记录 `evidence/term-scan.txt`。
- **③ 设计系统一致性**：新增 `check-tokens.py`——提取原型自身 CSS 的全部 `var(--s2*)` 引用，与设计系统 7 个 CSS 文件定义的 2509 个令牌比对；**66 个引用全部解析，0 未定义**。记录 `evidence/token-resolution.json`。
- **④ axe incomplete 逐项复核**：26 项 incomplete 全为 `color-contrast`（文本位于装饰层、渐变或伪元素之上，axe 无法判定背景）。复核方式：取实测计算样式（颜色、字号、字重）与元素实际背景（页面表面或身份卡渐变三个端点色），按 WCAG 2.1 计算最差对比度。**22 组组合全部达标，最差 6.37:1**（`.eyebrow` 深色，要求 4.5:1）。记录 `evidence/axe-incomplete-review.json`。

验证：`node check-model.cjs` 59 项、`python3 check-tokens.py` 66/66 解析、`python3 check-offline.py` 4 项、`OWNWORD_PORT=4312 python3 check-browser.py` 365 项（原型源码自 `a88071d` 后未再变动，证据与源码状态一致）。

仍未关闭：**E1 用户视觉复核**——需用户查看预览后确认，再把 `_d_meta.json` 资产状态由 `needs-review` 改为 `approved`。

### round 5 结果（2026-09-09，提交 `1a2132b`）

补 doneCriteria ④/⑤ 的无障碍证据，并修掉一个真实缺陷：

- **发现并修复缺陷**：跳至正文链接（`a.skip-link` → `#main`）聚焦后可见，但激活时焦点落回 `BODY`——`main` 缺 `tabindex="-1"`，链接等于不起作用。补 `tabIndex="-1"` 与 `main:focus { outline: none }` 后实测 `document.activeElement === main`。
- **新增断言**（全部通过）：跳至正文聚焦可见、激活后焦点进入 `main` 地标；键盘 Tab 经过的 5 个控件都有可见焦点环（`:focus-visible` 2px 轮廓）；钱包弹窗打开时焦点进入弹窗、关闭后回到触发按钮；`prefers-reduced-motion` 下 3D 自动旋转关闭且装饰动画时长降为 0.01ms。
- 复核 `_d_meta.json` 资产索引与目录一致（index/brand/brand-explorations 均存在）；`implementation-handoff.md` 补充品牌页定位（设计参考，生产不迁移）。

验证：`node check-model.cjs` 59 项、`check-tokens.py` 66/66、`check-offline.py` 4 项、`OWNWORD_PORT=4312 python3 check-browser.py` **373 项**通过，axe 0 violations、26 项 incomplete。

### round 7 结果（2026-09-09，提交 `b194fa9`）

- **错误路径覆盖**：把 `Storage.prototype.setItem` 改为抛错后切换偏好，断言页面以 `role="alert"` 明示「偏好无法保存」而不是静默失败（`Unwritable storage is announced instead of failing silently`）。

验证：`node check-model.cjs` 59 项、`OWNWORD_PORT=4312 python3 check-browser.py` **382 项**通过，axe 0 violations、26 项 incomplete。

### round 8 结果（2026-09-09，提交 `781c684`）

- **干净检出复现**：`git archive HEAD` 解压到临时目录（不含工作区残留与浏览器缓存），用独立端口 4313 服务，四个脚本结果与工作区完全一致——59 模型断言 / 66-of-66 token 解析 / 4 项离线检查 / 382 项浏览器检查。证明已提交的树自包含，不依赖未跟踪文件或工作区外资源。证据 `evidence/clean-checkout-verification.json`。
- 清掉遗留调试截图 `evidence/review-debug.png`（.gitignore 已忽略，未进版本库）。

验证：见上；工作区干净。

### round 9 结果（2026-09-09，提交 `aeb2cdf`，批 1：文案与断言解耦）

用户批准我的新方案后开工，先做批 1（低风险、且是批 3 文案精简的前提）：

- **词典抽离**：中英双语 142 键从 `app.jsx` 移到 `copy.js`（UMD 形式，node 可 `require`），新增 `check-copy.cjs` 校验两语言键集一致、无空串、无核心认知第 2.3 节禁区用词、无重复长句。
- **断言去文案化**：状态改由 `data-*` 暴露（`data-notice`/`data-error`/`data-busy`/`data-incomplete`/`data-copy-feedback`/`data-field-error`/`data-modal-title`/`data-action`），389 项浏览器断言不再按句子匹配文案；每个状态仍同时断言"文本非空"，保留 PRD「要显示提示」的意图。
- **面板关闭三态**：新增 `useDismissable`——点外点击、Escape（焦点回归触发按钮）、Tab 移出均可关闭；补 `aria-controls`。过程中修掉一个真实缺陷：`focusin` 判断写成 `relatedTarget`（旧焦点）而非 `target`，导致"Tab 移出"晚一次才生效。
- **确认提示 6s 自动消失**：`CLEAR_NOTICE` 动作 + `noticePaused` 暂停；悬停或聚焦暂停倒计时，`Failed` 类错误常驻不消失。模型断言 59 → 62。
- **小屏弹窗实测**：320×800 下创建确认弹窗内容高于视口、弹窗内可滚动；主操作 Cancel/Approve 首屏可见，原型专用的模拟行需滚动。新增断言 `Dialog primary actions stay inside a 320px viewport`，并写入 `implementation-handoff.md` 第 3.1 节作为生产注意项。
- **测试脚本加固**：点击前 `scrollIntoView({behavior:"instant"})`（`scroll-behavior: smooth` 会让坐标点击漂移）；布局签名改用绝对坐标（此前滚动位置不同会误报"深浅布局位移"）。

验证：62 项模型断言、4 项词典契约、66/66 令牌解析、4 项离线检查、**389 项浏览器检查**全部通过；axe 0 violations、26 项 incomplete。

### round 10 结果（2026-09-09，提交 `14f6408`，批 2-a：移动端/容器溢出量测）

用户批准方案后继续批 2 中客观的部分（穹顶交互重写涉及手感，仍等用户观感结论）：

- **新增量测探针**：`CONTAINER_OVERFLOW` 检查文本与控件是否超出父元素内容盒，覆盖 8 屏 × 4 双语/主题组合 × 4 宽度（320/390/768/960）。先用 `OWNWORD_MEASURE=1` 只记录不判定，triage 后再转为永久断言。
- **首轮命中 4 处，全部判为伪影**：都在公开身份卡的 `.plate-person h2/.bio`，且随 3D 旋转角度变化（实测角度 -10° 时 -3.6px，90° 时 +3.1px，180° 时 +51.6px，225° 时 +83.5px）。这是 `rotateY` 变换后的投影差，不是布局缺陷。探针排除 `.identity-object` 子树（该卡仍受视口溢出断言覆盖），复测 **0 处**。
- **转为永久断言**：每屏每组合各一条 `no element overflows its container`（32 条），浏览器检查 389 → **421 项**。量测记录 `evidence/layout-measurements.json`。

验证：62 模型断言 + 4 词典契约 + 66/66 令牌 + 4 离线 + 421 浏览器检查通过；axe 0 violations、26 项 incomplete。

### round 11 结果（2026-09-09，提交 `eb0380a`，批 3-a：链上记录）

用户此前批准我的方案倾向「链上记录做最小两态」，本轮落地：

- **双面公开身份卡**：正面身份；背面「链上记录」显示区块高度、确认状态、发布 TxID（有值才显示）。翻面由「查看链上记录 / 查看身份」按钮或视角滑块跨过 90° 触发；同一时刻只有一面在可访问树里（另一面 `inert` + `aria-hidden`）。
- **数据口径**：`model.js` 新增 `transaction`（fixture：TxID + 区块高度），新建身份为 pending、已发布身份为 confirmed，`DISCONNECT`/`SWITCH` 清空、保存资料保留。核心认知第 12 节第 3 项状态映射未关闭，因此**只显示 pending/confirmed 两态**，不显示 SEEN/ACCEPTED/MINED 等枚举名，也不把 fixture 当事实（写入 `verification.md` 扩展章节与实现交接第 3 节）。
- **修复真实缺陷**：双面卡 180° 时装饰层 `.plate-depth` 与背面重叠，遮挡背面「复制发布交易 TxID」按钮的点击点（`elementFromPoint` 命中 `.plate-depth`）。给 `.plate-depth` 与不可见那一面加 `pointer-events: none` 后按钮可点。这是鼠标可用性缺陷，不是测试问题。
- 视角滑块范围由 ±40° 扩到 ±180°，使滑块与翻面状态一致。

验证：模型断言 62 → **69**；词典键 142 → **155**；浏览器检查 421 → **426**（新增翻面可见、单面 a11y、两态文案、TxID 复制、翻回正面）；axe 0 violations、26 项 incomplete。

### round 12 结果（2026-09-09，提交 `6d73ac5`，批 3-b：弹窗可访问性审计）

- **补齐审计盲区**：axe 原先只覆盖页面状态，弹窗打开时从未审计。新增 `audit_dialog()`，在钱包确认、创建确认（320px）、放弃修改三个弹窗打开时各做一次——**violations 全为 0**，incomplete 各 1 项（`color-contrast`）。
- **新增断言**：弹窗具备可访问名称（`aria-labelledby` 指向非空标题）；三个弹窗审计各计 1 项。
- **incomplete 逐条复核**：新增 3 项（弹窗正文浅/深、紧凑头像浅/深共 6 组实测）全部达标——弹窗正文 8.06:1（浅）/7.25:1（深），头像首字母 12.32:1（浅）/10.53:1（深）；复核总表 28 组全部通过，最差仍是 `.eyebrow` 深色 6.37:1。

验证：69 模型断言 + 4 词典契约（155 键）+ 66/66 令牌 + 4 离线 + **430 项浏览器检查**通过；35 份 axe 审计（32 页面 + 3 弹窗）0 violations、29 项 incomplete 全部逐条复核。

### round 13 结果（2026-09-09，提交 `4cb61e5` / `3ae0a6e`：生产替换契约依据核实）

按上轮计划，把 `implementation-handoff.md` 里对 Yours Wallet Provider 的 API 声明逐条对照 `reference/yours-wallet-main/yours-wallet-main/docs/provider-api.md` 核实：

- **更正一处错误**：早期把 `signWithBAP` 写成身份发布的签名替换点。实际它是 `@1sat/actions` 的 `inscribe.execute()` 上的可选字段，只用于内容 Inscription；身份发布/更新/轮换分别由 `publishIdentity`、`updateProfile`、`rotateIdentity` 完成，签名在动作内部处理。
- **补准确入口**：连接/断开/状态/`identityKey` 来自 `useWallet()`（`WalletProvider` 只是包裹层）；所有动作调用前需 `createContext(wallet, {chain, services})`，`services` 为 `@1sat/client` 的 `OneSatServices`；解析身份用 `getProfile.execute(ctx, {})`（返回 `{bapId?, profile?, error?}`）。
- **依据表**：`verification.md` 新增「生产替换契约的依据」，把每项声明映射到参考文件章节或核心认知条款，避免后续凭印象书写。

验证：本轮只改文档（`git diff --name-only` 确认无代码/脚本变更），模型/词典/令牌检查重跑通过（69 / 4 / 66-66）；浏览器与离线结果沿用上一轮干净检出证据，已在 `evidence/clean-checkout-verification.json` 中记录续接依据。

### round 14 结果（2026-09-09，提交 `6e122db` / `62ee251`：文案长度审计）

为「文案精简范围」这个待定项提供数据依据（不改文案，只量测）：

- `check-copy.cjs` 新增信息性长度报告 `evidence/copy-length.json`（排名 + 阈值统计，不作门禁）。
- 155 条键中英文超 100 字符的只有 2 条：`simulatorHint`（115，演示面板专用，生产删除）、`connectBody`（104，钱包确认正文）；超 80 字符的共 8 条，集中在错误与空状态正文。
- 同一键中文普遍只有英文的 1/3～1/4（115/32、104/24、99/25），长度压力只在英文侧。
- **结论**：值得改的是这 8～10 条长正文（错误、空状态、确认弹窗），短标签无需重写；"全站重写"缺乏数据支撑。

验证：模型 69 / 词典契约 4（155 键）/ 令牌 66-66 重跑通过；浏览器 430 与离线 4 沿用上一轮干净检出（本轮无原型代码变更，已在 `evidence/clean-checkout-verification.json` 记录续接依据）。

### round 15 结果（2026-09-10，提交 `f770200`：批 2-b 穹顶指针光）

用户指示「穹顶做」，按其批准的契约实现（此前一直等用户观感，故未动）：

- **指针光**：新增 `.vault-light` 覆盖层（7 条 `.light-line` 与 `.vault-line` 共用几何规则），用 `mask-image: radial-gradient(circle 170px at var(--light-x) var(--light-y))` 把高光限制在指针附近；JS 每帧只写两个 CSS 自定义属性——**不逐条创建动画**（这是与已回退版本 `element.animate()` 做法的关键差异，并有断言守住）。
- **其余输入**：点击/轻触空白天幕与键盘 Enter 触发七线整波；指针离开天空或进入弹窗/偏好面板/演示面板/顶栏/页脚时 300ms 淡出；触摸不跟随。
- **减少动态效果**：不跟随、无位置变量；键盘交互给静态居中提亮。
- 过程中修正一处：切换到减少动效后指针移入仍保留旧光斑（handler 提前 return 未清状态），改为调用 `leave()`；键盘提亮时清除 `--light-x/--light-y`，让静态光居中。

验证：模型 69 / 词典契约 4（155 键）/ 令牌 66-66 通过；浏览器 **430 → 436 项**（新增 6 条穹顶断言）；axe 仍 0 violations、29 项 incomplete。

仍未关闭：**E1 用户视觉复核**；文案精简范围（数据建议只改 8~10 条长正文）。

### round 6 结果（2026-09-09，提交 `765c827`）

- **主题一致性显式断言**：`inspect()` 新增布局签名比对——把所有运行中的动画定格到 `t=0` 后，逐元素比较浅色与深色的矩形，8 屏全部零位移（`en light and dark layouts match`），直接对应 PRD 5.9「切换浅色布局不位移」。
- **状态机移植契约**：`implementation-handoff.md` 补全动作表（17 个动作 → 状态效果）与「原型文件 → 生产模块」对应表，使实现方能按表照搬而不必读 JSX。

验证：`node check-model.cjs` 59 项、`check-tokens.py` 66/66、`OWNWORD_PORT=4312 python3 check-browser.py` **381 项**通过，axe 0 violations、26 项 incomplete。

### round 7 结果（2026-09-09，提交 `b194fa9`）

- **错误路径覆盖**：把 `Storage.prototype.setItem` 改为抛错后切换偏好，断言页面以 `role="alert"` 明示「偏好无法保存」而不是静默失败（`Unwritable storage is announced instead of failing silently`）。

验证：`node check-model.cjs` 59 项、`OWNWORD_PORT=4312 python3 check-browser.py` **382 项**通过，axe 0 violations、26 项 incomplete。

### round 8 结果（2026-09-09，提交 `781c684`）

- **干净检出复现**：`git archive HEAD` 解压到临时目录（不含工作区残留与浏览器缓存），用独立端口 4313 服务，四个脚本结果与工作区完全一致——59 模型断言 / 66-of-66 token 解析 / 4 项离线检查 / 382 项浏览器检查。证明已提交的树自包含，不依赖未跟踪文件或工作区外资源。证据 `evidence/clean-checkout-verification.json`。
- 清掉遗留调试截图 `evidence/review-debug.png`（.gitignore 已忽略，未进版本库）。

验证：见上；工作区干净。

### round 9 结果（2026-09-09，提交 `aeb2cdf`，批 1：文案与断言解耦）

用户批准我的新方案后开工，先做批 1（低风险、且是批 3 文案精简的前提）：

- **词典抽离**：中英双语 142 键从 `app.jsx` 移到 `copy.js`（UMD 形式，node 可 `require`），新增 `check-copy.cjs` 校验两语言键集一致、无空串、无核心认知第 2.3 节禁区用词、无重复长句。
- **断言去文案化**：状态改由 `data-*` 暴露（`data-notice`/`data-error`/`data-busy`/`data-incomplete`/`data-copy-feedback`/`data-field-error`/`data-modal-title`/`data-action`），389 项浏览器断言不再按句子匹配文案；每个状态仍同时断言"文本非空"，保留 PRD「要显示提示」的意图。
- **面板关闭三态**：新增 `useDismissable`——点外点击、Escape（焦点回归触发按钮）、Tab 移出均可关闭；补 `aria-controls`。过程中修掉一个真实缺陷：`focusin` 判断写成 `relatedTarget`（旧焦点）而非 `target`，导致"Tab 移出"晚一次才生效。
- **确认提示 6s 自动消失**：`CLEAR_NOTICE` 动作 + `noticePaused` 暂停；悬停或聚焦暂停倒计时，`Failed` 类错误常驻不消失。模型断言 59 → 62。
- **小屏弹窗实测**：320×800 下创建确认弹窗内容高于视口、弹窗内可滚动；主操作 Cancel/Approve 首屏可见，原型专用的模拟行需滚动。新增断言 `Dialog primary actions stay inside a 320px viewport`，并写入 `implementation-handoff.md` 第 3.1 节作为生产注意项。
- **测试脚本加固**：点击前 `scrollIntoView({behavior:"instant"})`（`scroll-behavior: smooth` 会让坐标点击漂移）；布局签名改用绝对坐标（此前滚动位置不同会误报"深浅布局位移"）。

验证：62 项模型断言、4 项词典契约、66/66 令牌解析、4 项离线检查、**389 项浏览器检查**全部通过；axe 0 violations、26 项 incomplete。

### round 10 结果（2026-09-09，提交 `14f6408`，批 2-a：移动端/容器溢出量测）

用户批准方案后继续批 2 中客观的部分（穹顶交互重写涉及手感，仍等用户观感结论）：

- **新增量测探针**：`CONTAINER_OVERFLOW` 检查文本与控件是否超出父元素内容盒，覆盖 8 屏 × 4 双语/主题组合 × 4 宽度（320/390/768/960）。先用 `OWNWORD_MEASURE=1` 只记录不判定，triage 后再转为永久断言。
- **首轮命中 4 处，全部判为伪影**：都在公开身份卡的 `.plate-person h2/.bio`，且随 3D 旋转角度变化（实测角度 -10° 时 -3.6px，90° 时 +3.1px，180° 时 +51.6px，225° 时 +83.5px）。这是 `rotateY` 变换后的投影差，不是布局缺陷。探针排除 `.identity-object` 子树（该卡仍受视口溢出断言覆盖），复测 **0 处**。
- **转为永久断言**：每屏每组合各一条 `no element overflows its container`（32 条），浏览器检查 389 → **421 项**。量测记录 `evidence/layout-measurements.json`。

验证：62 模型断言 + 4 词典契约 + 66/66 令牌 + 4 离线 + 421 浏览器检查通过；axe 0 violations、26 项 incomplete。

### round 11 结果（2026-09-09，提交 `eb0380a`，批 3-a：链上记录）

用户此前批准我的方案倾向「链上记录做最小两态」，本轮落地：

- **双面公开身份卡**：正面身份；背面「链上记录」显示区块高度、确认状态、发布 TxID（有值才显示）。翻面由「查看链上记录 / 查看身份」按钮或视角滑块跨过 90° 触发；同一时刻只有一面在可访问树里（另一面 `inert` + `aria-hidden`）。
- **数据口径**：`model.js` 新增 `transaction`（fixture：TxID + 区块高度），新建身份为 pending、已发布身份为 confirmed，`DISCONNECT`/`SWITCH` 清空、保存资料保留。核心认知第 12 节第 3 项状态映射未关闭，因此**只显示 pending/confirmed 两态**，不显示 SEEN/ACCEPTED/MINED 等枚举名，也不把 fixture 当事实（写入 `verification.md` 扩展章节与实现交接第 3 节）。
- **修复真实缺陷**：双面卡 180° 时装饰层 `.plate-depth` 与背面重叠，遮挡背面「复制发布交易 TxID」按钮的点击点（`elementFromPoint` 命中 `.plate-depth`）。给 `.plate-depth` 与不可见那一面加 `pointer-events: none` 后按钮可点。这是鼠标可用性缺陷，不是测试问题。
- 视角滑块范围由 ±40° 扩到 ±180°，使滑块与翻面状态一致。

验证：模型断言 62 → **69**；词典键 142 → **155**；浏览器检查 421 → **426**（新增翻面可见、单面 a11y、两态文案、TxID 复制、翻回正面）；axe 0 violations、26 项 incomplete。

### round 12 结果（2026-09-09，提交 `6d73ac5`，批 3-b：弹窗可访问性审计）

- **补齐审计盲区**：axe 原先只覆盖页面状态，弹窗打开时从未审计。新增 `audit_dialog()`，在钱包确认、创建确认（320px）、放弃修改三个弹窗打开时各做一次——**violations 全为 0**，incomplete 各 1 项（`color-contrast`）。
- **新增断言**：弹窗具备可访问名称（`aria-labelledby` 指向非空标题）；三个弹窗审计各计 1 项。
- **incomplete 逐条复核**：新增 3 项（弹窗正文浅/深、紧凑头像浅/深共 6 组实测）全部达标——弹窗正文 8.06:1（浅）/7.25:1（深），头像首字母 12.32:1（浅）/10.53:1（深）；复核总表 28 组全部通过，最差仍是 `.eyebrow` 深色 6.37:1。

验证：69 模型断言 + 4 词典契约（155 键）+ 66/66 令牌 + 4 离线 + **430 项浏览器检查**通过；35 份 axe 审计（32 页面 + 3 弹窗）0 violations、29 项 incomplete 全部逐条复核。

### round 13 结果（2026-09-09，提交 `4cb61e5` / `3ae0a6e`：生产替换契约依据核实）

按上轮计划，把 `implementation-handoff.md` 里对 Yours Wallet Provider 的 API 声明逐条对照 `reference/yours-wallet-main/yours-wallet-main/docs/provider-api.md` 核实：

- **更正一处错误**：早期把 `signWithBAP` 写成身份发布的签名替换点。实际它是 `@1sat/actions` 的 `inscribe.execute()` 上的可选字段，只用于内容 Inscription；身份发布/更新/轮换分别由 `publishIdentity`、`updateProfile`、`rotateIdentity` 完成，签名在动作内部处理。
- **补准确入口**：连接/断开/状态/`identityKey` 来自 `useWallet()`（`WalletProvider` 只是包裹层）；所有动作调用前需 `createContext(wallet, {chain, services})`，`services` 为 `@1sat/client` 的 `OneSatServices`；解析身份用 `getProfile.execute(ctx, {})`（返回 `{bapId?, profile?, error?}`）。
- **依据表**：`verification.md` 新增「生产替换契约的依据」，把每项声明映射到参考文件章节或核心认知条款，避免后续凭印象书写。

验证：本轮只改文档（`git diff --name-only` 确认无代码/脚本变更），模型/词典/令牌检查重跑通过（69 / 4 / 66-66）；浏览器与离线结果沿用上一轮干净检出证据，已在 `evidence/clean-checkout-verification.json` 中记录续接依据。

### round 14 结果（2026-09-09，提交 `6e122db` / `62ee251`：文案长度审计）

为「文案精简范围」这个待定项提供数据依据（不改文案，只量测）：

- `check-copy.cjs` 新增信息性长度报告 `evidence/copy-length.json`（排名 + 阈值统计，不作门禁）。
- 155 条键中英文超 100 字符的只有 2 条：`simulatorHint`（115，演示面板专用，生产删除）、`connectBody`（104，钱包确认正文）；超 80 字符的共 8 条，集中在错误与空状态正文。
- 同一键中文普遍只有英文的 1/3～1/4（115/32、104/24、99/25），长度压力只在英文侧。
- **结论**：值得改的是这 8～10 条长正文（错误、空状态、确认弹窗），短标签无需重写；"全站重写"缺乏数据支撑。

验证：模型 69 / 词典契约 4（155 键）/ 令牌 66-66 重跑通过；浏览器 430 与离线 4 沿用上一轮干净检出（本轮无原型代码变更，已在 `evidence/clean-checkout-verification.json` 记录续接依据）。

### round 15 结果（2026-09-10，提交 `f770200`：批 2-b 穹顶指针光）

用户指示「穹顶做」，按其批准的契约实现（此前一直等用户观感，故未动）：

- **指针光**：新增 `.vault-light` 覆盖层（7 条 `.light-line` 与 `.vault-line` 共用几何规则），用 `mask-image: radial-gradient(circle 170px at var(--light-x) var(--light-y))` 把高光限制在指针附近；JS 每帧只写两个 CSS 自定义属性——**不逐条创建动画**（这是与已回退版本 `element.animate()` 做法的关键差异，并有断言守住）。
- **其余输入**：点击/轻触空白天幕与键盘 Enter 触发七线整波；指针离开天空或进入弹窗/偏好面板/演示面板/顶栏/页脚时 300ms 淡出；触摸不跟随。
- **减少动态效果**：不跟随、无位置变量；键盘交互给静态居中提亮。
- 过程中修正一处：切换到减少动效后指针移入仍保留旧光斑（handler 提前 return 未清状态），改为调用 `leave()`；键盘提亮时清除 `--light-x/--light-y`，让静态光居中。

验证：模型 69 / 词典契约 4（155 键）/ 令牌 66-66 通过；浏览器 **430 → 436 项**（新增 6 条穹顶断言）；axe 仍 0 violations、29 项 incomplete。

仍未关闭：**E1 用户视觉复核**；文案精简范围（数据建议只改 8~10 条长正文）。

### 风险 / 待确认
- 4311 端口被既有快照服务占用，实时预览改用 4312；若用户要求固定 4311，需先停掉既有实例再重启（待确认）。
- 4312 服务是本会话后台任务，会话结束即停止；需要常驻需另行安排。

## 2026-09-01 design-002 美学 P1d 收尾：穹顶降淡 + Review 精简 + 顶栏/Footer 重排（commit b03e5d2）

### 完成项
- 首页穹顶只做“整体降淡 15%”：`.dome-hero` 增加 `opacity: 0.85`，V6 七线结构、位置、颜色完全不变。
- Review 页信息精简：移除 `.panel-head`（类型 label + `S2StatusLight NOT PUBLISHED`），类型只保留在姓名下方的 `.review-type` 一次，避免重复。
- 顶栏/Footer 重排：语言/主题从 Footer 移入 `.topbar-prefs`（两个 `.icon-btn`，aria/title 保留）；Footer 删除 `.footer-main`/`.pref-switch` 体系，改为单行居中（OWNWORD · tagline）；删除 desktop footer 132px 右安全区与移动端旧 footer/pref 规则。

### 验证结果
- 真实 Chrome 1440×900：顶栏 children = brand / topbar-prefs / wallet-slot；Footer 单行文本、中心 x=720；穹顶 opacity=0.85、6 条 `.arc` 不变。
- 语言/主题 icon 切换正常（en↔zh、light↔dark）；320×568 顶栏无横向溢出、CTA top=448 首屏可见。
- Review 实测：无 `.panel-head`、无 NOT PUBLISHED、PERSON 仅出现一次，无横向溢出。
- 性能：1440 下 120 帧 p50=16.7ms / p95=16.8ms / max=17.5ms，0 帧>34ms。
- Babel/ds errors 为空；HTTP 全资源 200。
- 提交 b03e5d2（PRD v0.1_20260901-131244），独立子仓库。

### 待办
- 用户复核本轮三处观感（穹顶降淡、Review 精简、顶栏/Footer 重排）。
- 至此上一轮提出的美学优化项已全部落地；如定稿，下一步可 flip `_d_meta.json` 状态。

## 2026-09-01 design-002 美学 P1b+P1c：字阶/图标/FAB + 页面减负（commit 167dc31）

### 完成项
- P1b 零碎打磨：字号全部对齐 S2 阶（10/11/12/14/16/18/20/22/25/28/32/36），清掉半档；`.kicker`/`.auth-kicker` 字距 0.22→0.18em；`.hero-zh` 0.09→0.05em、hero-sub 行高 2→1.8；Public 返回按钮换 S2 ChevronLeft（新增源图标资产并暴露 `IconChevronLeft`）；Demo FAB 改 40×40 icon-only，保留 aria-label/title。
- P1c 页面减负：`.panel` 去掉 inset 受光边、padding 26→24、只保留 S2 阴影；首页 hero 底部 52→64、welcome-band 底部 64→80、三问 gap 44→48（`--q-gap` 同步，焦点公式自动对齐）、原则行 padding 22→24；review/public 两栏 gap 22/26→24；My 页 hero 不再使用 panel，BAP ID + Bio + Details 合并进单个 `my-identity-panel`（内部 hairline 分区），去掉重复的 ACTIVE 状态胶囊。

### 验证结果
- 真实 Chrome 1440×900 Light：三问焦点 397/720/1043 与列心逐一相等；hero-sub 16px/1.8、hero-zh 22px/0.05em、q-title 22px/q-zh 14px 均符合 S2 阶；Demo FAB 40×40 无文字。
- My 页：面板数由 3 个降为 1 个（`.my-identity-panel`），hero 无 panel 类，无 ACTIVE 胶囊，BAP ID/Bio/Details 同面板内 hairline 分区。
- 320×568：en CTA top=442、zh CTA top=335，均首屏可见；My 页 panel 284px、无横向溢出。
- 性能：1440 下 120 帧 p50=16.7ms / p95=16.9ms / max=17.1ms，0 帧>34ms。
- Babel/ds errors 为空；HTTP 全资源 200（含 ChevronLeft SVG）。
- 提交 167dc31（PRD v0.1_20260901-104821），独立子仓库。

### 待办
- 用户视觉复核“干净清爽”这一版；如对 My 页合并/去状态胶囊不满意，可单独回退或微调。
- 尚未动：顶栏/Footer 重排、Review 页信息减负、首页穹顶透明度等可选优化。

## 2026-08-31 design-002 美学 P1a：仅按钮统一 + 动效 + 阴影（commit 3b6d77f）

### 完成项
- 按用户要求只落“按钮统一 + 动效 + 阴影”这一组，不动字阶/返回图标/Demo FAB/输入框圆角，也不动首页穹顶。
- 按钮统一：删除 `index.html` 的 `.btn/.btn-primary/.btn-secondary/.btn-negative/.btn-quiet/.btn-sm` 整套自定义样式，新增全局 `.s2d-button { min-height:40px; padding:0 22px; gap:8px; font-size:14px; border-radius:999px }`；`app.jsx` 弹窗与授权弹窗、`screens-identity.jsx` 6 处、`screens-public.jsx` 返回按钮全部改 `<S2Button variant=… onPress=…>`；删除 `.hero-actions/.form-actions` 对 S2Button 的 8px 圆角与 padding 覆盖；`.bapid-box/.bapid-line` 选择器迁移到 `.s2d-button`；`.avatar-actions` 加 `align-items:flex-start`。
- 阴影回 S2：`--shadow-card` 保留 1px 接触阴影 + `0 8px 24px .16`（elevated）；dialog/demo-panel `0 12px 28px .22`（dragged）；toast `0 8px 24px .16`。
- 动效：`.view` 0.38s→0.18s 并加 8px 上移；dialog/demo-panel `dialog-in 0.2s→0.18s`。

### 验证结果
- 真实 Chrome 1440×900 Light：首页 CTA、授权弹窗、Setup、My、Public 全部按钮 40px/999px/14px/700；无 `.btn` 类或选择器残留。
- 卡片计算阴影含 `0 8px 24px .16` + 1px 接触边；demo-panel 阴影 `0 12px 28px .22`、动画 0.18s；`.view` 动画 0.18s。
- 320×568：CTA top=442 首屏可见、无横向溢出。
- 性能：1440 下 120 帧采样 p50=16.7ms / p95=17.1ms / max=24ms，0 帧>34ms。
- Babel/ds errors 为空；HTTP 全资源 200。
- 提交 3b6d77f（PRD v0.1_20260831-235334），独立子仓库。

### 待办
- 用户视觉复核本组；确认后再决定是否继续“字阶/字距”“返回图标”“Demo FAB”等第 5 项零碎打磨。

## 2026-08-31 design-002 美学 P0 落地（commit 9182ade）

### 完成项
- 按用户确认落地美学建议第 1/2/3 项（仅 designs/own-word-prototype-002，独立子仓库提交 9182ade）：
  - PageHead 增加 52px 地平线 + 5px 焦点；StateView 由三圈圆环改为“双穹顶弧 + 地平线 + 焦点核心”，图标反白；三原则账目行加 hairline 分隔；3D 卡正面由 1 弧补为 3 弧（透明度 0.55/0.38/0.24）。
  - `.hero-title .dim` 由 ink-strong 改为 ink-dim；zh 态隐藏与 h1 同文的 `.hero-zh`；My Identity 页 PageHead 由姓名改为 `my.title`（en Your identity is live / zh 你的身份已发布），serif 姓名只出现一次。
  - 三问地平线焦点与列心对齐：`.questions-band` 定义 `--q-gap`，`.questions-horizon` 计算 `--q-col-edge`，焦点 left 用该值；≤960px 单列隐藏两侧焦点，保留中间焦点。
- 数据字典新增 en/zh `my.title`。

### 验证结果
- 真实 Chrome（agent-browser）1440×900 Light：三焦点圆心 x=399/720/1041，与三列圆心完全相等（改动前外侧各偏 111px）；hero-title 第二行计算色 light rgb(80,80,80) / dark rgb(175,175,175)，与第一行分层。
- 状态页（连接取消）：state-emblem 结构 arc/arc.r2/horizon-line/core/icon 齐全，88×88 盒内 arc 78×46 与 50×33，地平线 y=52，icon path fill=#fff。
- PageHead line 52×1 + focal 在 Setup/My 均渲染；My 页姓名仅在 `.my-name` 出现一次。
- Public 3D 卡正面 `.dome-arc` 3 条，inset/opacity 符合预期。
- 响应式：960×800 与 320×568 无横向溢出；≤960 可见焦点数 1；320×568 Connect CTA top=442 首屏可见。
- HTTP 200；Babel 全脚本渲染无错误（home/setup/my/public 与取消状态均走通）。

### 待办
- 用户视觉复核本轮改动；确认后再决定是否继续第 4/5 项（S2 一致性按钮/圆角/阴影/动效与零碎打磨）。

## 2026-08-29 design-002 穹顶恢复到 V6（commit bcd886e）

### 完成项
- 用户确认按 V6 恢复。仅回滚首页穹顶区域：
  - `theme.jsx`：移除 Canvas 潮汐实现（Canvas/rAF/ResizeObserver/MutationObserver/DOME_* 参数），改回 V6 的 6 个 `<div class="arc">`，inset 8% 起每条 +6%、opacity 0.70 起每条 -0.05；外圈由 `.dome-hero` border 提供，共 7 条线。
  - `index.html`：`.dome-hero` 背景/边框恢复 V6 写法；`.dome-canvas` 删除；地平线恢复 1px 实线 opacity 0.6；焦点恢复 16px 静态，删除 `focal-breathe` 动画。
- 保留范围外修改：纸纹（无 mix-blend-mode）、字体/材质/三问三原则、3D 停驻旋转、以及全部交互修复；320px 下仍保留穹顶高度 112px 的响应式优化。

### 验证结果
- 真实 Chrome（本地 vendor React/Babel 测试，最终 HTML 已恢复 unpkg 引用）：穹顶 6 个 `.arc`、无 `.dome-canvas`、`focal animationName=none`。
- 性能：360 帧 rAF 采样 p95=16.8ms、0 帧超过 34ms（纯静态，无动画循环）。
- 320×568：无横向溢出、Connect CTA top=442 首屏可见；弧线宽度 207/177/148/118/89/59 等比排列。
- axe home 0 violations；Dark 下弧线 border 计算为 `rgb(68,68,68)`、地平线 opacity 0.6。

### 决策
- 穹顶线条最终回到 V6 静态版；不保留任何线条动画。
- 后续不再对穹顶线条增加逐帧动画；如需要动效，只允许 CSS 过渡/淡入这类低成本方案。

### 待办
- 用户复核静态七线观感；继续整体视觉复核，定稿后 flip `_d_meta.json`。

## 2026-08-29 design-002 穹顶动画卡顿排查与修复（commit 598bc6a）

### 现象与排查
- 用户反馈：首页穹顶线条动画无律动美感，且导致页面卡顿。
- 实测（1440×900 真实 Chrome，rAF 间隔采样 360 帧）：
  - 修复前静止状态 p50=16.7ms / p95=50.0ms / max=66.7ms，20/360 帧超过 34ms；
  - 模拟鼠标扫过穹顶时 max=116.6ms，长期任务出现；DevTools trace 5s 内 Paint 160.9ms、UpdateLayoutTree 162.7ms、Layerize 86.2ms、FunctionCall 279.7ms。
- 根因（两个叠加）：
  1. `theme.jsx` 的 SVG 实现每帧用字符串重建 6 条 path 的 `d` 并 `setAttribute`，且 `.arc-glow` 带 `filter: blur(2px)`，即使静止也在 60fps 全量重绘；鼠标拨弦模型每条弦按最近点独立激励 + 端点反射，相位互相干扰，视觉上“乱”而不是“律动”。
  2. `body::before` 纸纹使用 `mix-blend-mode: multiply`（dark 为 overlay），固定层与动画层叠加时强制全视口重合成；实验：仅把 blend 改为 normal，同样动画 p95 立即降到 16.8ms。

### 修复
- `theme.jsx` 改为 **Canvas 潮汐节律**：6 条弧线共享单一时间相位，内圈先起、按 `DOME_PHASE_STEP=0.62` 向外依次错开；每条弧线叠加两端固定（sin 包络）的 2 波数行进横波；accent 光晕用更宽描边替代 blur。
- 主题切换：MutationObserver 监听 `data-color-scheme`，Canvas 描边颜色从 CSS 变量（`--line` / `--accent`）重新读取；resize 用 ResizeObserver。
- `prefers-reduced-motion`：Canvas 只画一次静态弧线，不再启动 rAF。
- `index.html`：纸纹去色（feColorMatrix saturate=0）、去掉 `mix-blend-mode`，只保留 0.04（dark 0.05）透明度。

### 验证结果
- 修复后（1440×900 真实 Chrome，预热后连续 3 轮 360 帧采样）：p95=16.7 / 16.8 / 16.8ms，0 帧超过 34ms；3s PerformanceObserver（非 buffered）0 个 long task。
- 动画确实变化：Canvas `toDataURL` 间隔 700ms 前后不一致；reduced-motion 下 800ms 前后完全一致（静态）。
- Dark 主题：切到 dark 后 Canvas 非透明像素 25,546 且平均 RGB 偏向 accent 蓝，说明颜色监听生效。
- 320×568：Canvas 尺寸 246×111、无横向溢出、Connect CTA top=442 首屏可见；axe home 0 violations。
- HTTP 全资源 200。

### 决策
- 放弃“鼠标拨弦 + SVG path 逐帧变形”方案：交互不可预期、相位互相干扰，且 DOM 逐帧 path 更新 + blur 无法在满幅穹顶上稳定 60fps。
- Canvas 只负责穹顶装饰层，不参与 DOM/无障碍语义（父级 `aria-hidden`）；主题/尺寸变化通过观察器同步，不重挂载 React。
- 纸纹今后禁用 `mix-blend-mode`，纹理只允许低透明度普通 alpha 合成。

### 待办
- 用户复核新“潮汐”节律的幅度/速度/方向（可调参数：`DOME_OMEGA / DOME_PHASE_STEP / DOME_WAVES / amp`）。
- 继续视觉复核整体质感；定稿后 flip `_d_meta.json`。

## 2026-08-29 design-002 质感与交互打磨（commit bedc658）

### 完成项
- 按“纸上墨线与天光”方向执行 material pass（用户确认按建议执行，方向默认：英文主标保留 sans 800，中文口号与用户话语用 serif；3D 卡 Light=纸页、Dark=墨岩刻字）。
- 材质：body 增加 1–2% SVG 纸纹（light multiply / dark overlay）；面板改为受光边 + 更深纸影；顶栏由玻璃 blur 改为实底纸/墨 + hairline。
- 字体三角色：界面框架 sans；姓名/命题/用户话语 serif（Review/My/3D 姓名加签名线，Bio 改 blockquote 引文块）；BAP ID/TxID/Proof mono。
- 母题重构：三问由三张 qcard 改为“一条两端淡出的地平线 + 三个焦点 + 居中 serif 问题”；三原则改为无卡片账目行（01/02/03）；kicker/q-num/chain-num/demo 标题 accent 蓝收拢为中性，accent 只留给焦点、主行动、品牌签名。
- 穹顶动画调沉：弧线非等距（外疏内密）、透明度指数递减、粗细 0.5→1.4px；波速/幅度下调、阻尼放长、拨动间隔放宽。
- 3D 公共身份卡：自动旋转由连续 360° 改为正面停留 2600ms → 1800ms 转至背面停留 → 转回；`prefers-reduced-motion` 下自动旋转关闭；厚度侧面改为顶部受光/底部落影渐变。
- Proof/卡背改账目式 hairline 分隔；proof-list 由非法 dl 结构改 ul/li（axe definition-list violation 清零），p3d-controls 补 role=group。
- 交互修复（上一轮 P0 一并落地）：phase 变化 scrollTo 顶部；顶栏 cancelled/failed 不再显示 Connected；dialog max-height calc(100dvh-40px)+overflow（568×320 授权可滚动）；name/bio 长度校验进 validate；desktop footer 右侧预留 132px，避免 Demo FAB 遮挡主题按钮。

### 验证结果
- 真实 Chrome（agent-browser）1440/960/720/390/320，Light/Dark：无横向溢出；320×568 Connect CTA top=442 首屏可见；中文 320 body 1840 无重叠。
- 对比度计算：`--ink-faint` 提升到 82%，Light 4.91:1 / Dark 6.02:1；关键文字均 ≥4.5:1（品牌 span 改用 --s2-accent-color-1000 后 Light 4.49→达标）。
- axe：home 0 violations、review 0、public 0（Light/Dark）；仅剩 S2 按钮/oklch 的 incomplete 自动判定项。
- token：104 个 `var(--s2*)` 引用全部解析（含补定义 `--s2-focus-ring-color`）。
- Chrome 冒烟：连接→Setup→Review→Create→My→Public、连接取消顶栏状态、Edit Save、语言/主题、3D 停驻旋转（实测正面/背面各稳定 316px 宽，转场最窄 12px 仅过渡瞬间）、reduced-motion 下 auto-rotate off 且 transform 静止。
- HTTP 全资源 200（index + 6 jsx + bundle + styles）。

### 决策
- 方向 B：英文主标 sans、中文口号/用户话语 serif；比全衬线更贴合 S2 且不会退回 design-001。
- Demo FAB 保留右下；footer 在 ≥721px 视口加右侧安全区，主题按钮实测与 FAB 重叠面积 0。
- 纸纹用 body::before 固定层，不改 token 色板；卡片背面颜色问题（light-dark 在 background 多层列表被解析为 none）用 background-color 单独声明解决。
- design-002 继续 in-progress，等待用户视觉复核后再决定是否 flip `_d_meta.json` 状态。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-002/index.html`（重点：纸纹颗粒浓度、三问地平线构图、serif 签名块、3D 卡正/背停驻节奏、Dark 墨岩质感）。
- 复核后按反馈迭代；定稿后 flip `_d_meta.json` assets 状态并更新 feature_list doneCriteria 证据。


## 2026-08-18 选定 design-002 为最终视觉方向（其他封存）

### 决策
- 用户选定 design-002「穹顶与地平线」为最终视觉方向，design-001（碑铭/印章）、design-003（新大陆/Territory）、styles-001（三版风格探索）暂封存（`feature_list.json` status=archived，目录保留不删）。
- `feature_list.json`：`activeItem` = design-002，design-002 status=in-progress（继续按用户要求迭代，直到定稿版本）；allowedStatuses 新增 `archived`。
- 后续所有视觉迭代只落在 `designs/own-word-prototype-002/`，不再动 -001/-003/styles。

### 待办
- 用户逐条提出 design-002 修改要求，逐条实现、验证、提交，直至定稿。

## 2026-08-18 design-002 迭代：钱包授权 + 穹顶点击动画（commit 6d1058f）

### 完成项
- 钱包授权弹窗（核心认知不变量 11 + §6.3 统一高影响操作流）：所有需钱包签名的操作先经 Wallet 确认，覆盖 v0.1 三个操作：
  - Connect Wallet → 授权连接（Approve → connecting → resolve；Reject → Connection cancelled）
  - Create Identity → 授权身份发布（Approve → creating；Reject → Creation cancelled，保留 profile 值）
  - Save Profile → 授权 Profile 更新（Approve → saving；Reject → Saving cancelled，保留编辑值）
- 新增 `WalletAuthDialog` 组件（app.jsx）：模拟 Yours Wallet 请求，展示操作标题 + Identity（name + 完整 BAP ID 可复制，仅 create/save）+ 影响说明 + Approve/Reject；点 backdrop = Reject（模拟关闭钱包请求）。
- 三个入口改走 `requestAuth('create'|'connect'|'save')`；cancelled/failed 的 Try Again 重试同样重新走授权。
- Demo 注入语义：`fail` = Approve 后处理失败；`reject` = Approve 后钱包层拒绝（保住故障注入测试能力）。
- 首页穹顶点击操作性动画：`.hero-sky` 由纯装饰改为可点击（role=button + tabindex + 键盘 Enter/Space + focus-visible），点击触发「弧线依次点亮（arc-lit，stagger）+ 焦点脉冲（focal-pulse）+ 地平线扫光（horizon-scan）」动画并同时触发连接授权；760ms 后动画归位，可重复点击；`prefers-reduced-motion` 降级。

### 验证结果
- jsdom 冒烟 30/30 PASS（穹顶 role/点击→授权、连接 approve/reject、Create 授权 approve、Save 授权 approve/reject 保留值）。
- HTTP 全资源 200（index + 6 jsx + bundle + 3 css）。
- Token 66 个 `var()` 引用全解析（`--icon` 为注释 `--iconPrimary` 的正则误报，实际已定义）。
- Babel 6 文件转译通过（jsdom 加载时真实转译）。
- 真实 Chrome：授权弹窗亮色（Approve accent 蓝 `rgb(59,99,251)` 白字、居中 480×296、connect 无 BAP ID 块）/ 暗色（Approve `rgb(86,129,255)` 白字、Reject 深灰 `rgb(27,27,27)` 底浅字可见）；穹顶点击后 `rippling` class + `arc-lit`/`focal-pulse` 动画同步触发、800ms 后移除。

### 决策
- 授权范围仅 Connect/Create/Save 三个签名操作；Disconnect、Account Switch、Copy 不需签名授权（PRD 待确认 3 结论：Disconnect 只断开会话）。
- 授权弹窗复用现有 `.dialog` 视觉 + 穹顶 Mark，不引入新设计系统组件（S2 无现成 wallet 授权组件）。

## 2026-08-18 design-003 新大陆（Territory，全新设计，完成）

### 完成项
- 在 `designs/own-word-prototype-003/` 上全新设计第三版，不复制 design-001/002 的 HTML/CSS/JSX 结构：
  - `index.html`：全新 CSS，几何母题「新大陆/制图」贯穿全站（疆域轮廓 + 边界线 + 坐标网格 + 地标 + 等高线，抽象、克制、无具象建筑）。
  - `screens-wallet.jsx`（Welcome 疆域图 hero + 三问三疆域卡 + 三原则 + 连接/解析状态 + TerritoryMap/BrandMark 单一权威定义）、`screens-identity.jsx`（Setup/Review/Create/My/Edit，面板 map-card 坐标角标 + 虚线边界）、`screens-public.jsx`（疆域 3D 身份卡：正面=迷你疆域图、背面=Proof）、`app.jsx`（状态机 + 顶栏疆域品牌标记 + toast + 对话框 + Demo）。
  - 复用共享事实 `data.jsx`（i18n 字典 + 演示数据）、`icons.jsx`（S2 图标 + bundle 组件解构），未改动。
- 视觉方向（新大陆）：
  - 疆域轮廓：Welcome hero 抽象大陆 SVG（`T_LAND` 疆域轮廓 + `T_CLAIM` 被标注疆域 + 等高线 `T_CONTOUR*` + 坐标网格 graticule + 地标点），隐喻 Identity=被标注的疆域。
  - 边界线：面板 map-card 四角坐标角标 + 虚线边框（chain-panel、detail-list、proof-list、banner 均用 dashed），隐喻 Proof=边界可验证。
  - 坐标：BAP ID 视为可验证坐标，mono 展示；全站 faint graticule 网格背景。
  - 地标：疆域图上的 accent 地标点（带同心环）；三问卡用 Q{n}·A/B/C 坐标号。
  - 品牌标记 BrandMark 为小疆域轮廓（替换 design-001 的「W」与 design-002 的几何弧线 Mark）。
  - 颜色/圆角/字体全部来自 S2 token allowlist（:root 级）。
- 3D 身份卡保留：正面=疆域图（轮廓 + 等高线 + 被标注疆域 + 地标）+ 名称/类型/签名/BAP ID，背面=Proof（边界与标注）；preserve-3d 拖拽旋转 + 自动旋转。

### 验证结果
- HTTP 200：index.html / 6 jsx / _ds bundle / semantic.css / s2-tokens.css / components.css 等全资源。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 经 jsdom 解析零错误（无标签闭合问题）。
- Token 合规：页面 26 个 `var(--s2*)` 引用全部可解析（`:root` 级 token：`--s2d-surface-*`/`--s2d-content-*`/`--s2d-action-*`/`--s2d-status-*`/`--s2d-radius-*`/`--s2d-font-*` 与 `--s2-gray-*`/`--s2-accent-color-*`/`--s2-focus-indicator-color`）。
- jsdom 冒烟（React UMD + 设计系统 bundle + Babel 真实加载）：31 项断言全 PASS——主流程（Welcome 疆域图、Connect→Resolving→Setup、表单校验、Review、Create 成功、My Identity、Public 3D 疆域卡、Edit Save、Discard 对话框、语言、主题、Disconnect）+ 故障注入（连接拒绝/失败、解析失败、重置流程）。

### 决策
- 复用 `data.jsx`/`icons.jsx`（共享事实层，非视觉），只重写视觉与展示层。
- token 用 `semantic.css` 与 `s2-tokens.css` 的 `:root` 级 token（同 design-002 结论，规避 `.s2{}` 作用域别名在 `:root` 不解析的问题）。
- 状态语义、边界、术语严格遵循核心认知与 PRD v0.1；Key Rotation 已下放 v0.1.1，本版不含。
- 疆域路径 `T_LAND`/`T_CLAIM`/`T_CONTOUR1`/`T_CONTOUR2` 在 screens-wallet.jsx 单一权威定义，screens-public.jsx 复用（DRY）。

### 布局重构（第二次提交 56e8d7c）
- 用户反馈：初始版布局与 design-002 骨架相同（顶栏 + 1080px 居中 wrap + welcome 双栏 + 三卡片网格 + review/my/public 双栏），要求重新布局。
- 改为「测绘图册」布局，脱离 design-002 骨架：
  - 左图例竖栏（rail，sticky，含品牌标记 + Journey 行程步骤高亮 + 语言/主题/钱包置底），替换 design-002 的顶部导航栏。
  - 主内容为全幅画布（faint graticule 网格底），非居中 wrap。
  - Welcome = 全幅疆域画布（大图作背景 + 中央 cartouche 题注卡 + 连接按钮）+ 三问「图例带 legend-band」+ 三原则「边界注记带 boundary-strip」（替换三卡片网格）。
  - 表单/Review/My/Edit 全部改单列「测绘 sheet」（顶部刻度尺 ruler + 底部图例栏），替换双栏卡片。
  - Review 的「接下来」由侧边 sticky 面板改为水平「航路带 route-strip」。
  - My Identity 由双栏 my-grid 改为单列 my-body 堆叠 sheet。
- 验证：Babel 6 文件通过；token 26 项解析通过；jsdom 冒烟 34 项断言全过（新增 rail 步骤/图例带/航路带断言）。

### 缺陷修复（第三次提交 5d68566）
- 浏览器复核发现：S2Button 按钮（Connect/Review/Create 等）在亮色模式下看不到——`components.css` 的 `--s2d-accent`/`--s2d-text`/`--s2d-border-strong`/`--s2d-layer` 等别名只定义在 `.s2{}` 作用域内，而 bundle 渲染的按钮（`s2d-button s2d-button-accent`）未挂 `.s2` 类，导致 `var(--s2d-accent)` 无法解析、按钮 background 透明 + `color:white` → 白底白字不可见。
- 修复：在 `index.html` 的 `:root` 层补定义这组 `--s2d-*` 别名，值引用 `s2-tokens.css` 的 `:root` 级 token。
- 验证（真实 Chrome）：accent 按钮亮色 `rgb(59,99,251)` 底白字、暗色 `rgb(86,129,255)` 底白字；secondary 按钮暗色 `rgb(27,27,27)` 底 + 边框 `rgb(57,57,57)`；StatusLight 圆点 `rgb(5,131,78)` 正常；37 个 `var(--s2*)` 引用全部解析；jsdom 冒烟 34/34 仍全过。
- 注：此缺陷为 design-001/002/003 三版共有（design-001 的 `--accent: var(--s2d-accent)` 同样失效），本任务仅修复 design-003，未回改 001/002。

### 图标暗黑不可见修复（第四次提交 b70a15f）
- 浏览器暗黑复核发现：26 个 S2 图标（语言/主题/复制/编辑/锁定/旋转/提示等）在暗黑下不可见。根因：图标 SVG 文件内 `fill="var(--iconPrimary, #222)"`，而 `icons.jsx` 用 `<img src>` 加载 SVG，`<img>` 加载的 SVG 是独立文档、CSS 变量不跨 img 边界继承，恒 fallback 深灰 `#222`；且 `--iconPrimary` 在设计系统里根本未定义（它本意配合内联 SVG）。亮色可看，暗黑 `#222` 图标在深底上几乎同色。
- 修复（用户选方案 B）：① `icons.jsx` 由 `<img>` 改为内联 SVG（26 个 SVG 内容生成进 `ICON_SVGS`，`Icon` 组件用 `dangerouslySetInnerHTML` 渲染 `<span class="icon">`，fill 继承页面变量）；② `index.html` `:root` 定义 `--iconPrimary: var(--s2-neutral-content-color-default)`；③ 清理 CSS 图标 `img` 尺寸选择器（改为 `.icon`，保留 `.avatar-preview img` 真实头像图与 `.demo-note/.banner` 间距）。
- 验证（真实 Chrome）：暗黑图标 `path` 计算 fill=`rgb(219,219,219)` 浅灰可见、亮色 `rgb(41,41,41)` 深灰正常；Babel 6 文件通过；37 个 `var(--s2*)` 解析；jsdom 冒烟 34/34 连跑 3 次全过。

### 视觉微调（第五、六次提交 3be82e0 / d7c1c2a）
- 用户反馈刻度尺（`.sheet-ruler` 整条）气质突兀、与「新大陆」制图主题冲突。先改为 sheet 左上角 9×9 小十字坐标标，用户再次反馈连十字标也去掉，最终 sheet 回归干净图纸（无 ruler、无十字标）。删除 JSX 全部 8 处 `<span class="sheet-ruler">` 与 CSS `.sheet-ruler`/`.sheet::before` 规则。
- 验证：Babel 通过；jsdom 冒烟 34/34；浏览器确认 ruler/十字标均已无；37 个 token 解析。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-003/index.html`（桌面 1440px / 移动 320px，重点：测绘图册布局观感、疆域画布、3D 卡旋转、主题/语言切换）。复核后 flip `_d_meta.json` 资产状态（当前 needs-review）。
- 三版原型对照评审：`-001`（碑铭/印章）、`-002`（穹顶/地平线）、`-003`（新大陆）。

### 风险 / 待确认
- 无浏览器环境：320px 重叠、3D 拖拽手感、疆域图 SVG 在窄屏的视觉观感只能 DOM 级验证，需人工确认。

## 2026-08-18 design-003 立项（新大陆，方向已定，未实现）

## 2026-08-18 design-002 穹顶与地平线（全新设计，完成）

### 完成项
- 在 `designs/own-word-prototype-002/` 上全新设计，替换原复制基线，不复制 design-001 的 HTML/CSS/JSX 结构：
  - `index.html`：全新 CSS，几何母题「穹顶 + 地平线 + 焦点」贯穿全站。
  - `screens-wallet.jsx`（Welcome 天穹 hero + 三问三焦点连线 + 三原则 + 连接/解析状态）、`screens-identity.jsx`（Setup/Review/Create/My/Edit）、`screens-public.jsx`（穹顶地平线 3D 身份卡）、`app.jsx`（状态机 + 顶栏 + toast + 对话框 + Demo）。
  - 复用共享事实 `data.jsx`（i18n 字典 + 演示数据）、`icons.jsx`（S2 图标 + bundle 组件解构），未改动。
- 视觉方向（穹顶与地平线）：
  - 穹顶：Welcome 大圆弧天穹（`.dome-hero` + 双层同心弧）；顶栏/页头/页脚/3D 卡背使用纯几何 SVG `Mark`（弧 + 地平线 + 焦点，无字母）。
  - 地平线：hero 天/地分割线、页头 `.horizon-line`、三问「一条地平线上的三个焦点」、3D 卡正面的天（52%）/地分割。
  - 焦点：accent 圆点落在每处地平线上，隐喻「我是谁」= 视野中心的一个点。
  - 克制、抽象、无具象建筑；颜色/圆角/字体全部来自 S2 token allowlist。
- 3D 身份卡保留：正面=天穹天空（弧 + 焦点首字母）+ 地面信息，背面=Proof；preserve-3d 拖拽旋转 + 自动旋转。

### 验证结果
- HTTP 200：index.html / 6 jsx / _ds bundle / semantic.css 等全资源。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 容器标签闭合校验通过。
- Token 合规：页面 24 个 `var(--s2*)` 引用全部可解析（用 `:root` 级 token：`--s2d-surface-*`/`--s2d-content-*`/`--s2d-action-*`/`--s2d-status-*`/`--s2d-radius-*` 与 `--s2-gray-*`/`--s2-accent-color-*`）。
- jsdom 冒烟（React UMD + 设计系统 bundle + Babel 真实加载）：32 项断言全 PASS——主流程 24 项（Welcome/穹顶/三焦点、Connect→Setup、表单校验、Review、Create 成功、My Identity、Edit Save、语言、主题、Public 3D、Disconnect、连接拒绝、解析失败）+ 故障注入 8 项（complete/incomplete 分流、创建拒绝/重试、保存拒绝、Account Switch）。

### 决策
- 复用 `data.jsx`/`icons.jsx`（共享事实层，非视觉），只重写视觉与展示层。
- token 用 `semantic.css` 与 `s2-tokens.css` 的 `:root` 级 token；发现 design-001 使用的 `--s2d-background`/`--s2d-text`/`--s2d-accent` 等别名只在 `components.css` 的 `.s2 {}` 作用域内定义，`<html>`/`<body>` 未挂 `.s2` 类时在 `:root` 层不解析，design-002 改用全局 token 规避此问题（仅记录，未回改 design-001）。
- 状态语义、边界、术语严格遵循核心认知与 PRD v0.1；Key Rotation 已下放 v0.1.1，本版不含。

### 缺陷修复（34bf968，与 design-003 同类问题）
- 用户指出暗黑模式下按钮/图标不展示，排查发现与 design-003 相同的两处根因，一并修复：
  1. S2Button 按钮透明：`components.css` 的 `--s2d-accent`/`--s2d-text`/`--s2d-layer`/`--s2d-border-strong` 等别名只在 `.s2{}` 作用域定义，bundle 渲染的按钮未挂 `.s2` 类 → `var(--s2d-accent)` 无法解析、按钮背景透明 + `color:white` → 白底白字不可见。修复：`index.html` `:root` 补定义这组 `--s2d-*` 别名。
  2. 图标暗黑不可见：26 个图标 SVG `fill="var(--iconPrimary, #222)"` 经 `<img>` 加载，`<img>` 的 SVG 是独立文档、CSS 变量不跨边界继承，恒 fallback 深灰 `#222`，暗黑下与深底同色。修复：`icons.jsx` 由 `<img>` 改为内联 SVG + `:root` 定义 `--iconPrimary: var(--s2-neutral-content-color-default)`；清理 CSS 图标 `img` 尺寸选择器改 `.icon`（保留 `.avatar-preview img`/`.dcard-focal img` 真实图片）。
  3. 顺带补 `S2_Icon_Settings_20_N.svg`（此前 25 个图标缺 Settings，Demo fab 图标 404）。
- 验证（真实 Chrome）：暗黑 Connect 按钮 `rgb(86,129,255)` 底白字、secondary 按钮深灰底浅字、图标 fill=`rgb(219,219,219)` 可见；亮色按钮 `rgb(59,99,251)` 正常；Babel 6 文件通过；36 个 `var(--s2*)` 解析。

### 视觉调整（07f1f84 / abb23fc）
- 用户反馈穹顶弧线太少（原 2 条），要求 7 条。将 Welcome hero `.dome-hero` 的弧线由 2 条（`.arc` + `.arc.arc2`）改为 7 条同心弧：`screens-wallet.jsx` 用 `[0..6].map` 循环生成，内联 `inset` 从 4% 起每条 +6%（4%→40%）内缩、`opacity` 从 0.78 起每条 -0.055 递减；`index.html` 删 `.arc.arc2` 规则、`.arc` 只留基础（position/border/圆角），inset/opacity 由内联 style 控制（DRY）。
- 最终定稿：用户要求「恢复到最初那一版，只是加外圈一共 7 条线（原 8 条多了）」。恢复最初弧线样式 `border: 1px solid var(--line)`（淡色），内弧 6 条（`inset` 8%→38% 每条 +6%，`opacity` 0.7→0.45 递减）+ dome-hero 自身 border 作外圈 = **共 7 条线**。
- 验证：浏览器确认 arcCount=6 + dome border 1px = 7 条线；Babel 通过。

### 待办
- 用户视觉复核 `http://127.0.0.1:4311/own-word-prototype-002/index.html`（桌面 1440px / 移动 320px，重点：天穹/地平线观感、3D 卡旋转、主题/语言切换）。复核后 flip `_d_meta.json` 资产状态（当前 needs-review）。

### 风险 / 待确认
- 无浏览器环境：320px 重叠、3D 拖拽手感、穹顶弧线在窄屏的视觉观感只能 DOM 级验证，需人工确认。

## 2026-08-18 design-002 design-001 对照版（复制基线，已由上方全新设计替代）

### 完成项
- 产出 `designs/own-word-prototype-002/`：design-001 内容一致副本（index.html + 6 jsx + _ds/react-spectrum-s2 + assets/icons + _d_meta.json）。
- 独立 Git 子仓库，commit `30d556d`（(PRD v0.1) 格式）。

### 验证结果
- HTTP 200：index / app.jsx / _ds bundle。
- jsdom 主流程冒烟 35 项断言全过（复用 design-001 测试集，仅路径替换）。

### 决策
- 副本仅作对照基线，内容与 design-001 完全一致；差异化迭代在副本上进行，两版可对照评审。
- 对照差异方向（视觉 / 交互 / 文案等）待用户指定。

### 待办
- 用户指定对照差异方向后，在 own-word-prototype-002 上迭代。

## 2026-08-18 design-001 v0.1 高保真可交互原型

### 完成项
- 产出 `designs/own-word-prototype-001/`：`index.html`（入口）+ `data.jsx`（i18n en/zh + 演示数据）+ `icons.jsx`（S2 workflow 图标 + bundle 组件唯一命名）+ `screens-wallet.jsx` + `screens-identity.jsx` + `screens-public.jsx` + `app.jsx`（状态机 + Demo 控制面板）。
- 导入 react-spectrum-s2 到 `_ds/react-spectrum-s2/`（25 个 S2 workflow 图标复制到 `assets/icons/`），`_d_meta.json` 登记 primaryDesignSystem 与资产。
- 覆盖 PRD v0.1 全部 BDD 场景：Connect 成功/取消/失败、Account Switch、Disconnect、Identity 自动分流（无身份/已发布完整/Profile 不完整）、Setup 表单校验（Name 必填≤100、Bio≤1000、Type、本地图片 Avatar）、Review（完整 BAP ID + Copy + "Your wallet controls this identity."）、Create 成功/取消/失败、My Identity（首屏 BAP ID）、Edit Profile（Saving…/Saved/取消/Discard 对话框）、语言 en/zh（默认 en，持久化，协议值不翻译）、主题 Light/Dark（默认 Light，持久化，状态带图标+文字）。
- 个人身份公共查看：3D 立体身份卡（preserve-3d 正反两面 + 18px 厚度层 + 光泽 + 朱印），自动旋转 + 拖拽旋转 + 重置；右侧 Proof 面板渐进披露完整 BAP ID / TxID / 链上状态。
- 视觉方向：应用主体取版三协议（S2 原生 indigo、新体系感），Welcome 印章卡与 Public 3D 卡取版一碑铭（深色、厚重感、serif 铭文、朱印），融合 styles-001 三版。

### 验证结果
- `http://127.0.0.1:4311/own-word-prototype-001/index.html` 全资源 HTTP 200（7 CSS + bundle + 6 jsx + 25 图标）。
- JSX 语法：Babel standalone 转译 6 文件全部通过；index.html 标签闭合校验 0 错误。
- Token 合规：页面引用 22 个 `var(--s2*)` 全部在设计系统 allowlist 内。
- 运行时冒烟（jsdom + React UMD + 设计系统 bundle 真实加载）：56 项断言全部 PASS——主流程 35 项 + 故障注入 21 项（解析失败、创建取消/失败、保存取消/失败、incomplete 分流、published 分流、Discard 对话框）。
- 修复的真实缺陷：① 多个 `<script>` 顶层 `const {Button}` 重名导致浏览器 SyntaxError → 改为 icons.jsx 统一解构为 `S2*` 前缀；② 视图路由顺序 bug：`resolving` 分支排在 `page==='welcome'` 之后导致解析中显示 Welcome → 调整路由顺序。

### 决策
- 无真实 Wallet/Indexer，连接与发布流程用 Demo 控制面板模拟（右下角 "Demo"）：分流结果三态、注入 7 种故障、Account Switch、Reset。注入在下一次对应操作时生效一次。
- 3D 身份卡为静态深色碑铭质感，不随主题切换（厚重感聚焦）；周边 UI 随 Light/Dark。
- 演示 BAP ID/TxID 为虚构占位值，仅原型演示用，非产品事实。

### 原型对 PRD 与后端设计的影响（需同步事项）
- 无需修改 PRD v0.1：原型严格实现 PRD 范围（Key Rotation 已按待确认结论下放 v0.1.1，不含）。无新增页面、流程或文案禁区违规。
- 后端实现建议（由原型交互揭示，非本任务产出）：
  1. Avatar 本地图片上传：原型为 Data URL 预览；后端需提供上传接口与存储（PRD 待确认已定：本地图片，不支持 URL）。
  2. BAP ID 展示规则：首屏主层级、完整值可复制、缩略 `前4…后8`；后端返回完整原值，展示缩略由前端完成。
  3. 产品状态归一化：原型使用 `Cancelled / Failed / Published / ACTIVE / NOT PUBLISHED` 等产品语义，后端不得直接透出 SDK/Indexer 原始枚举（核心认知 §9）。
  4. 偏好持久化：locale/theme 由前端 localStorage 保存（核心认知不变量 13：不进签名输入、不改链上事实）。
  5. Public Identity 3D 查看依赖 Identity 公开解析数据（BAP ID、Profile、发布交易），与 v0.4 通用 Lookup 解耦，v0.1 仅演示当前钱包身份的公开视图。

### 待办
- 用户视觉复核：桌面/移动视口布局、3D 旋转观感（本环境无浏览器，布局重叠与动画只能 DOM 级验证，视觉观感需人工确认）。
- 用户审阅后按反馈迭代；`_d_meta.json` 资产状态在复核后 flip（approved / changes-requested）。

### 风险 / 待确认
- 无浏览器环境：320px 视口重叠、3D 拖拽手感、主题切换布局位移（CSS 已按断点与固定最小宽度处理，未实机确认）。
- 页面文案为演示性样例（如"立言者"），非产品既定文案。
- Key Rotation 已按 PRD v0.1 待确认结论下放 v0.1.1，原型不含。

## 2026-08-18 styles-001 首页风格探索（三版）

### 完成项
- 产出 `designs/own-word-prototype-styles-001/`：index.html（入口）+ home-ledger.html（版一碑铭）+ home-charter.html（版二宪章）+ home-protocol.html（版三协议）。
- 导入 react-spectrum-s2 设计系统到 `_ds/react-spectrum-s2/`（import-design-system.mjs），并登记 `_d_meta.json`（primaryDesignSystem = react-spectrum-s2，4 个资产）。
- 每版独立自包含 HTML，加载设计系统 7 个 CSS（token 链路），页面仅用 token 变量与页面内定义的局部变量。
- 内容骨架一致：Hero（Own your identity. Own your words.）→ 三问 → 三根原则 → 一段签署话语（BAP ID / TxID / Signature valid / Revision）→ 平台承诺 → Footer。
- 三版视觉方向：
  - 版一 碑铭 The Ledger：暖墨黑底 + 碑金 + serif 铭文 + 印章，深色厚重；
  - 版二 宪章 The Charter：纸色底 + 条款文书 + 签名 + 印泥朱印，浅色信实；
  - 版三 协议 The Protocol：S2 原生 indigo + 卡片 + 等宽协议细节 + 状态徽标，新体系科技感。

### 验证结果
- `python3 -m http.server 4311 --directory designs` 运行中；4 页面 + 7 CSS 均 HTTP 200。
- HTML 标签闭合校验：4 文件全部 OK。
- token 解析检查：页面引用的 `--s2*`/`--s2d*` 系统变量全部存在于 tokens；`--ledger-*`/`--paper` 等为页面内 `:root` 局部变量。
- 修正：`oklch(from ...)` 相对色语法换为 `color-mix`（兼容性）；protocol 版补 `--serif` 局部变量。

### 决策
- 首页指平台 landing page（门户首页），非应用内页面。
- 风格探索阶段页面用静态 HTML + 设计系统 token（未挂 React bundle），符合"html 文件即可，可预览"要求；design-001 高保真交互原型按 bundle 组合组件。

### 待办
- design-001 原型已融合三版方向（见上），styles-001 三版保留供参考。

### 风险 / 待确认
- 字体 `adobe-clean-*` 来自 Adobe Typekit 远程，离线时回退系统字体（设计系统 readme 已知边界）。
- 页面文案（立言者、铭文内容等）为演示性样例，非产品既定文案，需用户确认后进入正式原型。

### round 15 补记（2026-09-10，提交 `4d45231`、`0d83481`、`00b7ecb` 级联：测试稳定性）

干净检出复检暴露两处测试稳定性问题（都不是产品缺陷）：

1. **坐标点击落在过渡中**：翻到卡背面后 150ms 的 transform 过渡尚未结束就点击，`copy-tx` 偶发点空。修法：`click_action` 在点击前 `settle()` 等有限过渡结束。
2. **自动消失提示干扰布局签名**：编辑页的 `saveCancelled` 提示 6 秒后消失，浅色与深色两次测量之间整页上移 124px，被误判为"深浅布局位移"。修法：布局签名改用**相对基准**（绝对 x + 相对首个元素的 y），整页均匀位移被抵消。

验证：工作区与干净检出（端口 4320）均为 69 / 4 / 66-66 / 4 / **436**，axe 0 violations、29 项 incomplete。

### round 16 结果（2026-09-10，提交 `fe35dbf`：批 3-b 文案精简·保守范围）

按 round 14 的数据结论执行精简，只改 **7 条产品长正文**（en+zh 同批），规则：标题已说明的失败不在正文重复、每条保留全部产品事实、术语只用核心认知第 2 节的词。演示面板专用的 `simulatorHint`/`simulatorNote` 属原型脚手架，不在产品界面，未改。

| 键 | 改前 en 字数 | 改后 en 字数 |
| --- | --- | --- |
| `welcomeBody` | 91 | 62 |
| `connectBody` | 104 | 78 |
| `processingBody` | 99 | 82（保留"断开或切换账户会取消本操作"事实，故未压到 80 以下） |
| `connectFailedBody` | 84 | 60 |
| `completeBody` | 84 | 64 |
| `discardBody` | 83 | 62 |
| `resolveFailedBody` | 82 | 56 |

改后超过 80 字符的产品文案只剩 `processingBody`；超过 100 字符的只剩演示面板专用的 `simulatorHint`。中文同步改写。关键事实全部保留：身份未改变、可重试、可断开或切换账户、填写内容保留、可继续编辑、发布需另行确认。

验证：词典契约 4（155 键）、模型 69、令牌 66-66、离线 4、浏览器 **436** 全部通过；干净检出（端口 4321）结果与工作区一致。

仍未关闭：**E1 用户视觉复核**（含本轮改动的文案措辞需目视确认）。

### round 17 结果（2026-09-10，提交 `34eb6de`：瞬时状态审计与卡背面违规修复）

- **扩展审计到卡背面**：`audit_dialog()` 泛化为 `audit_state()`，除三个弹窗，还对**公开身份卡背面**做一次 axe。
- **首次审计即抓到真实违规**：背面标题用 `<h3>`，而正面在卡背面露出时 `aria-hidden`，页面只剩 h1 → `heading-order`（Heading levels should only increase by one）。改为 `<h2>`（与正面姓名同级）后复测 0 violations。
- **incomplete 逐条复核扩充**：新增卡背面 14 组（标题、说明、eyebrow、wordmark、区块高度/确认值、事实标签、TxID，浅深各半），全部达标；复核总表 **42 组**全部通过，最差仍是 6.37:1。
- 证据文件名由 `dialog-*-axe.json` 改为 `state-*-axe.json`（含卡背面后原名不准确）。

验证：模型 69 / 词典契约 4 / 令牌 66-66 / 离线 4 / 浏览器 **437**（+1 卡背面审计）全部通过；36 份 axe 审计（32 页面 + 3 弹窗 + 1 卡背面）0 violations；干净检出（端口 4322）一致。

仍未关闭：**E1 用户视觉复核**。

### round 18 结果（2026-09-10，提交 `15ad354`：瞬时状态审计扩展）

把上轮承诺的三个瞬时状态纳入 axe：

| 状态 | violations | incomplete |
| --- | --- | --- |
| 身份解析中（`identity-resolving`） | 0 | 0 |
| 创建处理中（`processing-create`） | 0 | 1（头像首字母，渐变背景） |
| 存储不可写告警（`storage-error-alert`） | 0 | 2（welcome 正文、地平线说明） |

`audit_state(label, when=…)` 会在审计**前后各校验一次状态**，避免窄窗口状态（解析中仅 850ms）结束后证据被误标。新增 6 组对比度复核（welcome 正文、地平线说明、处理中头像，浅深各半）全部达标；复核总表 **48 组**全部通过，最差仍是 6.37:1。

验证：模型 69 / 词典契约 4（155 键）/ 令牌 66-66 / 离线 4 / 浏览器 **437 → 440**；axe 审计 **39 份**（32 页面 + 7 瞬时状态）0 violations；干净检出（端口 4323）一致。

仍未关闭：**E1 用户视觉复核**。

### round 19 结果（2026-09-10，提交 `bc2580a`：dogfood 探索式测试）

用户批准后按 `agent-browser` 的 dogfood 技能跑了一轮探索式测试（不预设断言），报告 `designs/own-word-prototype-s2-astra-001/evidence/dogfood/report.md`，截图 12 张。共 5 项发现，无 critical/high：

| 编号 | 发现 | 级别 | 处置 |
| --- | --- | --- | --- |
| ISSUE-001 | 浏览器后退键直接离开应用（`about:blank`），会话静默丢失 | medium | 记录为实现边界（原型无路由；生产需路由 + 会话恢复，已写入实现交接「内存态」行） |
| ISSUE-002 | 字符计数按码点而非字素簇：5 个家庭 emoji 显示 `35 / 1000`，15 个被判定超 100 字符 | low | **已修**：`model.js` 新增 `countGraphemes()`（`Intl.Segmenter`，缺支持回退码点），校验与计数器统一 |
| ISSUE-003 | 复制反馈「Copied」永不消失 | low | **已修**：`Identifier` 6 秒后自动清除（与确认提示同节奏） |
| ISSUE-004 | 解析中装饰骨架未标 `aria-hidden` | low | **已修**：骨架容器补 `aria-hidden="true"` |
| ISSUE-005 | 320px 弹窗次级操作被裁出首屏 | low | 记录为实现交接 3.2 的可接受行为（模拟区生产删除；主操作可见性已有断言） |

探索中同时验证通过的项：弹窗焦点陷阱（6 次 Tab / 2 次 Shift+Tab 均在弹窗内）、背面 TxID 复制按钮键盘可达（Shift+Tab 到 `copy-tx`，Enter 触发）、断开连接后无旧身份残留、双击 Approve 不产生重复提交、RTL 名称与超长无空格串在 1440/320 均无溢出。

证据限制：无头浏览器 `agent-browser record` 报 `No frames captured`，无法产出 WebM repro 视频，报告以分步截图替代并注明。

验证：模型断言 69 → **74**；浏览器检查 440 → **443**；词典契约 4（155 键）/ 令牌 66-66 / 离线 4 全部通过；干净检出（端口 4324）一致。

仍未关闭：**E1 用户视觉复核**。

### round 20 结果（2026-09-10，提交 `09c1e7d`：键盘全程定向 dogfood）

在暗色主题下用**纯键盘**走完整流程（连接 → 批准 → 填表 → 复核 → 创建 → 就绪 → 我的身份 → 公开身份 → 翻面 → 复制 TxID），又找到两项：

| 编号 | 发现 | 级别 | 处置 |
| --- | --- | --- | --- |
| ISSUE-006 | 首屏挂载时把焦点抢进 `main h1`，第一次 Tab 直接落在「Connect Wallet」，**跳过 skip link、品牌、偏好设置、穹顶**；要绕整页才能回到顶栏 | medium | **已修**：`app.jsx` 加 `firstPaint` ref，仅首屏跳过焦点搬移，站内换页仍聚焦新 h1；新增断言「首屏焦点在文档起点」「第一次 Tab 到达 skip link」 |
| ISSUE-007 | 键盘翻面后，刚露出的 TxID 复制按钮在 Tab 顺序里位于翻面按钮**之前**，正向 Tab 要绕整页才能到达 | low | **已修**：显式翻面按钮用 `requestAnimationFrame` 把焦点移到背面首个可操作元素；用视角滑块跨 90° 时不搬焦点（有意取舍，已记录） |

探索中验证通过的项：全程 9 个关键操作均可纯键盘到达且焦点环可见（Connect 1 次 Tab、Approve 2 次、Name 2 次、Review 5 次、Create 3 次、Go to My Identity 2 次、Public 3 次、View chain record 1 次）；弹窗焦点陷阱正常；暗色下焦点环清晰；控制台无错误。

验证：模型 74；浏览器 443 → **446**；词典契约 4（155 键）/ 令牌 66-66 / 离线 4 全部通过；干净检出（端口 4325）一致。dogfood 报告已更新为 7 项发现（2 medium、5 low，无 critical/high）。

仍未关闭：**E1 用户视觉复核**。

### round 21 结果（2026-09-10，提交 `bba7343`：320×568 矮屏专项 dogfood）

此前所有响应式断言只覆盖 320×800；本轮用 iPhone SE 一代尺寸 **320×568** 走完整流程（暗色），找到一项真实失守：

| 编号 | 发现 | 级别 | 处置 |
| --- | --- | --- | --- |
| ISSUE-008 | 创建确认弹窗的主操作（Cancel/Approve）在 320×568 下位于 `top=711 / bottom=755`，**完全在首屏之外**，必须先在弹窗内滚动才能确认 | medium | **已修**：新增 `@media (max-height: 640px)`——弹窗操作行 `position: sticky; bottom: 0` 常驻滚动视口底部，矮屏隐藏原型专用的「Simulated wallet confirmation」说明行。修复后实测 459–503（视口 568 内） |

同轮量测确认无问题的项（320×568 暗色）：welcome CTA 486–534 首屏可见、钱包连接弹窗操作 436–480 可见、review 提交按钮 325–369 可见、ready 按钮 315–359 可见、My Identity BAP ID 115–214 首屏可见、卡背面 TxID 432–478 可见且链上事实单列排布、全程无横向溢出、控制台无错误。

验证：模型 74；浏览器 446 → **448**（新增 2 条 320×568 断言）；词典契约 4（155 键）/ 令牌 66-66 / 离线 4 全部通过；干净检出（端口 4326）一致。dogfood 报告更新为 8 项（3 medium、5 low，无 critical/high），6 项已修并补断言。

仍未关闭：**E1 用户视觉复核**。

### round 22 结果（2026-09-10，提交 `6112980`：减少动效专项 dogfood）

用 `prefers-reduced-motion: reduce` 走完整流程，发现并修复一项，同时把一处不稳定证据改造掉：

| 编号 | 发现 | 级别 | 处置 |
| --- | --- | --- | --- |
| ISSUE-009 | 减少动效下点「Rotate identity」：控件变为 `aria-pressed=true`、文案变「Pause rotation」，但实测运行中动画数 **0**、卡片 transform 不变——控件报告了不会发生的状态 | low | **已修**：减少动效下不渲染旋转开关，改显示说明文案「Reduced motion follows your device preference.」（复用此前未使用的 `reducedMotion` 词条）并强制 `rotating=false`；媒体查询变化实时同步。新增断言 `Reduced motion replaces the rotation toggle with an explanation` |

**证据稳定性改造**：`identity-resolving`（仅 850ms）的 axe 审计在复现中出现"审计完成时状态已离开"，会产出描述错误屏幕的证据。改为 3 条针对性断言（busy 状态、`role=status` 具备可访问名、装饰骨架 `aria-hidden`、提供断开出口），axe 审计数由 39 降为 38（32 页面 + 6 瞬时状态），避免不诚实证据。

同轮验证通过：减少动效下提示 6 秒自动消失、复制反馈 6 秒自动清除、运行中动画数 0、控制台无错误。

验证：模型 74；浏览器 448 → **451**；词典契约 4（155 键）/ 令牌 66-66 / 离线 4 全部通过；干净检出（端口 4327）一致。dogfood 报告 9 项（3 medium、6 low，无 critical/high），7 项已修。

仍未关闭：**E1 用户视觉复核**。


## 2026-09-10 design-flash-001 立项与实现（穹顶与地平线·全新设计，不参考现有实现）

用户要求以全新设计另出一版对照原型，需求集合与 design-astra-001 一致，id `design-flash-001`。AskUserQuestion 裁决三项：①交付范围＝注册条目并从零建成完整原型；②design-astra-001 与 design-flash-001 本轮同时保持 in-progress（破例）；③视觉意象沿用「穹顶与地平线：七线穹顶、无刻度地平、3D Public Identity」。

### 完成项

- **立项**：`feature_list.json` 新增 design-flash-001（13 条 doneCriteria，含「不参考任何现有实现代码」自证条），`activeItem` 切至本事项，astra 加 statusNote 记录并行例外。
- **设计概念（本版自有）**：七线穹顶的每条线＝PRD v0.1 第 1 节的一项用户能力，线有三态（`active` 当前在用 / `ready` 可用 / `deferred` 后续版本，画虚线，v0.1 仅密钥轮换）；无刻度地平每页只出现一次（应用页在页头下沿，Welcome 在 hero 底部、穹顶立于其上），不画刻度、标签或百分比；地平线之上＝Bitcoin 可证明的事实，之下＝留在本设备的内容。3D 公开身份卡：正面身份、背面 Proof，可拖拽/方向键/按钮翻转，首次自动翻一次，`prefers-reduced-motion` 下完全静止，隐藏面 `aria-hidden` + `inert`。
- **架构（本版自有）**：纯逻辑层 `src/core/{model,dome,i18n,format,prefs}.js`（UMD-lite，无框架依赖，node 检查直接加载浏览器运行的同一份文件）；视图层 `src/ui/*.jsx`（浏览器内 Babel 转译，命名空间 `window.OW`）；`step(state,event) → {state, effects}` 的「状态＋效果」状态机让取消/失败/切换等时序在 node 中可断言。
- **运行时本地化**：React 18.3.1 与 Babel 7.29.0 下载后按设计系统提示给的三条 sha384 逐一校验通过，落在 `vendor/`；`index.html` 23 条引用全部本地。
- **设计系统一致性**：`import-design-system.mjs` 同步 `_ds/react-spectrum-s2`；引用 56 个自定义属性全部解析（设计系统 47 + 本项目 9），无 `#hex`/`rgb()`/`hsl()`/`oklch()` 自造颜色；阴影改用 `--s2-drop-shadow-*`。
- **文档**：`verification/verification.md`（复现方式、证据索引、BDD 逐条映射、全新设计自证、设计系统缺口表、无障碍/响应式/双语双主题/术语、未关闭项）、`verification/implementation-handoff.md`（11 个模拟点的替换契约、不得丢失的可观察行为、生产替换验收清单、核心认知第 12 节三项待确认的处理）、`README.md`、`vendor/README.md`、`.gitattributes`、`verification/run-all.sh` 一键复现。

### 验证结果

| 套件 | 结果 | 证据 |
| --- | --- | --- |
| 模型（纯逻辑 + BDD + 不变量 + 词典契约） | 53/53 | `evidence/model-results.txt` |
| 设计系统一致性 | 56 引用全解析、0 自造颜色 | `evidence/token-resolution.{txt,json}` |
| 浏览器（BDD、响应式矩阵、axe、对比度、键盘、触控、动效、用词） | 51/51 | `evidence/browser-checks.txt` |
| axe 审计 | 24 份，violations 0、incomplete 0 | `evidence/axe-summary.json` + `axe/*.json` |
| 文字对比度 | 24 组实测，最低 4.81:1（AA 门槛 4.5） | `evidence/contrast.{txt,json}` |
| 离线（阻断全部 https） | 5/5 | `evidence/offline-checks.txt` |

一键复现：`bash designs/own-word-prototype-s2-flash-001/verification/run-all.sh`（本轮在端口 4330 全新拉起服务复跑，四套件全绿）。

### 决策

1. **七线＝七项能力**：让母题承载产品状态而非装饰；穹顶绘制与图例读同一份 `capabilityStates(screen)`，两者不可能互相矛盾（浏览器检查 `welcome: seven dome lines with product state` 断言绘制与图例逐一相等）。
2. **密钥轮换按第 9 节裁决处理**：功能流程完整可验证，界面以 `Planned for v0.1.1` 徽标与虚线穹顶线明确标注，不冒充 v0.1 已交付能力。
3. **状态在 node 可断言**：纯逻辑与浏览器同源，避免「文档一套、实现一套」；模型检查覆盖取消保留草稿、轮换不改 BAP ID、账户切换终止敏感操作与旧回调失效等不变量。
4. **发现并修正设计系统缺陷**：`.s2d-button-accent` 深色下白字对比度 3.51:1 不达 AA；本原型深色改用 accent-700（5.25:1），缺口写入 `verification.md` 缺口表并列入生产交接。
5. **量测必须在过渡结束后取值**：对比度检查加入 settle（双 rAF + 260ms），否则会读到 150ms 颜色过渡的中间值（首次运行即误报 3.51 与 4.81 混读，settle 后稳定为 5.25）。
6. **原型脚手架自我约束**：模拟面板默认只在 ≥960px 视口展开，避免遮挡产品内容；面板带 `Prototype` 标记，其文案在词典中单列 `sim.*`。

### 文件

- 新增子仓库 `designs/own-word-prototype-s2-flash-001`（1065 文件，含 `_ds` 设计系统副本），提交 `d73ab45`（PRD v0.1_20260910-*）。
- 任务文档：`_task/system-design/feature_list.json`、本文件、`session-handoff.md`。

### 风险 / 待确认

- **用户视觉复核未完成**：`_d_meta.json` 的 `assets.status = needs-review`。本模型无图像输入能力，未对截图做视觉判断；布局重叠、3D 翻转手感、母题节奏需用户目视确认后翻为 `approved`。
- 设计系统品牌字体为远程 Typekit，离线回退系统字体（设计系统自身边界，已在离线检查断言降级）。
- 浏览器内 Babel 会在控制台留一条提示（非错误）；生产改预编译。

### 干净检出复验（2026-09-10，端口 4331）

`git clone` 子仓库到 `/tmp/flash-clean/`，`OWNWORD_PORT=4331 bash verification/run-all.sh`：模型 53/53、设计系统一致性 PASS（56 引用全解析、0 自造颜色）、浏览器 51/51、离线 5/5，axe 24 份 0 violations / 0 incomplete。结论：证据只依赖仓库内容与 node/agent-browser，不依赖本机工作区状态。子仓库提交 `fa20ed6` 记录该结果。

## 2026-09-10 design-flash-002 第 1 步：首页风格（等待用户确认）

用户指定交付 `design-flash-002`（目录 `designs/own-word-prototype-s2-flash-002`，13 条 doneCriteria 沿用 design-flash-001），并要求**第一步先给首页风格、提供预览地址、确认后再继续**。

### 完成项

- **立项**：`feature_list.json` 新增 `design-flash-002`（依赖 design-flash-001 的需求集合，非代码依赖；不读取任何现有原型源码），`activeItem` 切至本事项；并行状态在 statusNote 记录。
- **门禁**：已读 `_task/system-design/AGENTS.md`、`CLAUDE.md`、`feature_list.json`、`progress.md`、`session-handoff.md`、`spec/核心认知.md`、`spec/prd/v0.1/设计文档v0.1.md`、`designs/react-spectrum-s2`（readme/SKILL/tokens/components/manifest）。未读取 `_task/system-design/spec/draft`。
- **交付形态**：按用户「一个 html 即可」的要求，首页全部写在 `index.html` 单文件（结构 + 样式 + 交互 + i18n 词典）；设计系统用 `import-design-system.mjs` 同步到 `_ds/react-spectrum-s2/`。
- **首页设计（自有）**：七线穹顶由 7 条经线弧组成，几何由半球正视投影推导（`viewBox 0 0 1000 500`，apex `(500,6)`，`rx = 494·k/7`，`ry = 494`，弧端点落在地平线上）；无刻度地平为 1px 通栏直线，无刻度/标签/百分比；3D Public Identity 示例卡正/背翻面；语言/主题持久化（默认 en/light，PRD 8.8 与第 9 节裁决）；地面层为三根原则。
- **响应式**：桌面两栏（文案左、卡右、穹顶 apex 落在两栏之间），≤1000px 单列（地平线排在 CTA 之后、身份卡落在地平线之下）；穹顶宽度在单列下收窄，保证 apex 不越出视口。
- **提交**：子仓库 `designs/own-word-prototype-s2-flash-002` 提交 `3b1201f`（PRD v0.1_20260910-1501），1012 个文件（含 `_ds` 副本）。

### 验证结果（第 1 步）

| 检查 | 结果 |
| --- | --- |
| axe | 1440 浅/深、320 中文深：violations 0；incomplete 1（10 节点，背景无法自动判定，已人工复核） |
| 对比度 | 正文 14.55:1（浅）/13.64:1（深）；次级 8.06/8.61；CTA 4.81（浅）/5.24（深） |
| token | 44 个引用全解析（34 个 `--s2-*`、4 个 `--s2d-*`、6 个项目布局别名）；0 自造颜色 |
| 无 CDN | 除设计系统 Typekit 字体边界（带回退）外全同源；阻断字体域后无错误、布局正常 |
| 响应式 | 1440/960/768/390/320 横向溢出均为 0；七线 7 条；地平线均 1px 通栏；CTA 首屏可见 |
| 双语双主题 | 切换即时生效、reload 后持久化；示例姓名/BAP ID/TxID 不随语言变化 |
| 运行异常 | page errors 空、console errors 空 |
| 几何 | PNG 像素探针：浅色地平线 rgb(198)@y=752、深色 rgb(68)、keystone rgb(86,129,255)，经线出现在预期坐标 |

证据：`designs/own-word-prototype-s2-flash-002/verification.md` 与 `verification/evidence/`。预览：`http://127.0.0.1:4311/own-word-prototype-s2-flash-002/index.html`（服务在 4311 已拉起）。

### 决策

1. 首页先不接 Wallet：CTA 点击只显示「钱包连接将在本原型的下一步接入」，避免风格评审阶段出现假流程。
2. 示例身份数据（`Avery Chen`、`1SampleDome…`、示例 TxID）硬编码为 sample 且卡面有 `Sample/示例` 标签，不写成产品事实。
3. 深色 CTA 使用 `--s2-accent-color-700`（5.24:1）：设计系统 `--s2-accent-background-color-default` 深色为 4.51:1，过于贴近 AA 下限；该改动只用 S2 token，缺口记入 verification.md。
4. 不引入 React/Babel：第 1 步一个 HTML 可完成；后续是否引入由完整原型架构决策，倾向继续无框架以免原型期技术债。

### 风险 / 待确认

- **用户视觉复核未完成**：模型无图像输入能力，数值探针（地平线/经线像素、对比度、溢出）只覆盖可量化部分；穹顶节奏、字号与留白需用户目视确认。
- 首页为单列 ≤1000px 布局，若用户希望 960 也保持两栏，需要另行调整。
- Typekit 字体为设计系统边界，离线走系统字体回退。

### 唯一下一步

用户打开 `http://127.0.0.1:4311/own-word-prototype-s2-flash-002/index.html` 确认首页风格；确认后进入第 2 步：实现 PRD v0.1 第 5 节（5.1–5.10）、8.8 与第 9 节裁决的全部场景，并逐条补齐 13 条 doneCriteria 的证据。

## 2026-09-10 design-flash-003 第一步：首页风格单页（待用户确认）

### 完成项

- 新增事项 `design-flash-003`（`feature_list.json`，`status=in-progress`，`output=designs/own-word-prototype-s2-flash-003`），激活顺序：`activeItem` 改为 `design-flash-003`。验收标准沿用 design-flash-001 的 13 条。
- 约束：设计过程不读取任何现有原型实现代码（design-001/002/003、styles-001、astra、flash-001/002）；事实依据仅核心认知、PRD v0.1、`designs/react-spectrum-s2`、`reference`。
- 第一步交付 `home.html`（单个 HTML，A/B/C 三种首页构图）与 `_d_meta.json`（`assets.status=needs-review`）；**不做完整实现**，等用户确认风格。
- 视觉命题映射：七条线对应 PRD v0.1 第 1 节七项用户能力，其中 Rotate Key 按第 9 节第 5 项裁决画虚线 deferred；无刻度地平为整页唯一 1px 单线渐变；3D Public Identity 卡正面身份/背面 Proof。

### 验证结果

| 检查 | 结果 |
| --- | --- |
| S2 token | 63/63 个 `var(--s2*)` 解析；设计系统 CSS 定义 2511 token；0 未定义、0 自造色值 |
| axe | 四组合（en/zh × light/dark）violations 0；color-contrast incomplete 26 节点人工复核全部 PASS，最低 4.81:1 |
| 响应式 | 1440/960/768/390/320 横向溢出 0、文案与身份卡无重叠、主 CTA 首屏可见 |
| 交互 | 语言/主题/构图切换与刷新持久化、协议值不变、复制成功与失败、翻转 aria 状态、能力-穹顶联动 |
| 无 CDN | React/ReactDOM 本地化到 `vendor/`；远程字体显式降级为系统字体栈；实测 0 外部请求、console/errors 空 |
| 运行异常 | page errors 空、console 空 |

证据：`designs/own-word-prototype-s2-flash-003/verification/step1-notes.md` 与 `verification/evidence/`。子仓库提交 `e658dd8`。预览：`http://127.0.0.1:4311/own-word-prototype-s2-flash-003/home.html`（4311 已服务 `designs/`）。

### 决策

1. 首页 CTA 暂不接 Wallet：点击只显示占位提示，避免风格评审阶段出现假流程；完整连接流程在下一步实现。
2. 示例 BAP ID `4U5eEMQSUdmPXeqmyQJtvELPNE8E` 由 BAP 测试向量 rootAddress `1wt1buQLx2G39adHovj2QJZnZK9vsXUjC` 确定性派生，页面标注 Sample data，不写成产品事实。
3. 深色主按钮改用 `--s2-accent-color-700`（5.25:1）：设计系统 `.s2d-button-accent` 深色白字仅 3.51:1；只用 S2 token，缺口记入 `step1-notes.md`，需反馈设计系统维护者。
4. 字体：S2 的 Adobe Clean 由 Typekit 远程提供，本步覆盖 `--s2d-font-family` 为系统字体栈，页面 0 外部请求；品牌字体本地化方案留待用户确认许可后处理。

### 风险 / 待确认

- **用户视觉复核未完成**：模型无图像输入能力；像素与几何探针只覆盖可量化部分，穹顶节奏、留白、3D 翻转手感需用户目视确认。
- A/B/C 三构图待用户选择或组合；确认后再继续完整原型。
- 核心认知第 12 节三项待确认不在首页范围，正式交付时须显式标注验证方式。

### 唯一下一步

用户打开 `http://127.0.0.1:4311/own-word-prototype-s2-flash-003/home.html`，确认首页风格（或指定 A/B/C 组合与修改点）；确认后实现 PRD v0.1 §5（5.1–5.10）、§8.8 与 §9 裁决的全部场景，并逐条补齐 13 条 doneCriteria 证据。

## 2026-09-12 design-flash-mini-001 从零全新设计并交付完整原型

用户要求：基于 `feature_list.json` 重新设计一版，不参考任何现有实现代码，全新思考、全新设计；要求仍与 `design-astra-001` 一致，id 为 `design-flash-mini-001`，输出到 `design-flash-mini-001`。

### 完成项

- **立项**：`feature_list.json` 新增 `design-flash-mini-001`（依赖 `design-astra-001` 的需求集合，非代码依赖；输出 `designs/design-flash-mini-001`），`activeItem` 切至本事项；`design-astra-001` 暂置 `blocked`，保持「同时只允许一个 in-progress」。13 条 doneCriteria 沿用 astra 并显式加入「全新设计且不参考实现」。
- **全新设计约束**：设计过程只读核心认知、PRD v0.1、`designs/react-spectrum-s2` 与 reference 协议资料；未读取 astra/design-001/002/003/flash-* 实现代码；`verification/evidence/fresh-design-scan.txt` 扫描产品源码 0 命中。
- **交付形态**：`designs/design-flash-mini-001/`，纯 ESM + DOM，无 React/Babel/外部 CDN；`_ds/react-spectrum-s2` 为自包含设计系统副本；`verification/serve.py` 提供 no-store 预览。
- **视觉**：沿用穹顶与地平线命题但重新实现——7 条非对称宽度比经线弧、keystone 汇聚、1px 无刻度地平、3D Public Identity 正/背面；mini 约束为紧凑单列、≤760px 固定底部操作条、320px 首屏保留完整 BAP ID；穹顶弧与能力图例同读 `capabilityStates(state)`。
- **状态模型**：`src/core/model.js` 纯 `step(state,event)`，覆盖连接 DETECTING→CONNECTING→CONNECTED、取消/失败、四态分流、创建/取消/失败、编辑保存/取消/离开保护、Key Rotation（v0.1.1 徽标）、账户切换取消敏感操作并清旧身份、断开、偏好持久化、reducer 纯度。
- **文档**：`verification.md`（BDD 逐条映射、证据索引、全新设计自证、S2 缺口、axe incomplete 复核）、`verification/implementation-handoff.md`（12 项模拟点生产替换契约、不得丢失行为、核心认知 §12 三项待确认的验证方式）、`README.md`、`_d_meta.json`（asset status=needs-review）。
- **提交**：子仓库 `designs/design-flash-mini-001` 提交 `95490f2`（原型本体，PRD v0.1_20260912-094341）与 `6c3f5c3`（干净检出复验，PRD v0.1_20260912-094621）。

### 关键决策

1. **不用框架**：为满足无 CDN、离线可启动与可断言性，采用纯 ESM + DOM；设计系统以 `_ds` 副本的 token 与组件类组合消费，生产替换为真实 `@react-spectrum/s2` 组件。
2. **七线穹顶重新推导**：使用显式非对称宽度比 `[0.26,0.4,0.53,0.65,0.77,0.89,1]`，使 7 条弧互不重合且全部汇聚于 keystone；不画刻度/百分比。
3. **mini 行为**：320/390 下主 CTA 用固定底部操作条保证首屏可见；完整 BAP ID 放在身份卡正面，保证 320×568 首屏可见。
4. **无障碍缺口修正**：深色主按钮改用 `--s2-accent-color-700`（5.25:1）、negative 按钮改用 `--s2-negative-color-700`（5.24:1）、深色错误文字改用 `--s2-negative-color-1000`（5.55:1）；缺口记入 `verification.md`。
5. **Key Rotation 按 §9 裁决**：完整可交互流程保留评审/批准/取消/失败，但界面始终标注 `Planned for v0.1.1`，不冒充 v0.1 交付。
6. **axe incomplete 处理**：5 条 incomplete（7 个节点）经人工复核——4 个为 aria-hidden 装饰性头像首字母，3 个为钱包弹窗覆盖导致的 heading-order 无法判定；结论写入 `evidence/axe-incomplete-review.json`。

### 验证结果

| 套件 | 结果 | 证据 |
| --- | --- | --- |
| 全新设计扫描 | 0 命中 | `designs/design-flash-mini-001/verification/evidence/fresh-design-scan.txt` |
| 模型 | 28/28 | `evidence/model-results.{txt,json}` |
| S2 token | 28/28 解析，2509 定义 token，0 自造颜色 | `evidence/token-resolution.{txt,json}` |
| 浏览器 | 14/14 | `evidence/browser-checks.{txt,json}` |
| axe | 15 次 0 violations、5 incomplete（7 节点）已复核 | `evidence/axe-summary.json`、`evidence/axe/*.json`、`evidence/axe-incomplete-review.json` |
| 对比度 | 11/11 组合达标（最低 4.81:1） | `evidence/contrast-review.txt` |
| 离线 | 3/3 | `evidence/offline-checks.{txt,json}` |
| 截图 | 18 张 | `evidence/screens/` |
| 干净检出 | `git archive HEAD` 后 4405 端口全绿 | `evidence/clean-checkout.txt` |

一键复现：`cd designs/design-flash-mini-001 && OWNWORD_PORT=4401 bash verification/run-all.sh`。

### 文件与提交

- 子仓库：`designs/design-flash-mini-001`，提交 `95490f2`、`6c3f5c3`；视觉迭代提交 `8c3379c`、`0388301`。
- 任务文档：`_task/system-design/feature_list.json`、`progress.md`、`session-handoff.md`（根仓库提交）。

### 风险 / 待确认

- **用户视觉复核未完成**：`_d_meta.json` asset status 仍为 `needs-review`；自动化证据只覆盖可量化部分，穹顶节奏、留白、3D 翻转手感与四组合观感需用户目视确认。
- 核心认知 §12 三项（Inscription Number endpoint、Artifact 签名封装、Blockchain 状态映射）不在 v0.1 范围，已在交接文档写明验证方式，未写成事实。
- 卡片整体为鼠标点击便利项，键盘用户通过独立 `Flip card` 按钮可达；若要严格等价，需要把卡片改为真正的可聚焦控件。

## 2026-09-12 design-flash-mini-001 视觉迭代：3D 卡片 / 右下角模拟器 / 抽象穹顶光晕

用户反馈：3D 卡片不够立体和精致；原型模拟整合到右下角；穹顶线条抽象点、在下一层、带光晕，并有从屏幕延伸出去的感觉。

### 完成项

- **3D Public Identity 精修**：新增 `identity-depth` 两层景深叠层（translate3d/rotateZ）、卡片正/背面 `translateZ(12px)`、更强层级阴影与内高光、指针移动倾斜（`--tilt-x`/`--tilt-y`，reduced-motion 下不绑定）、保留独立 `Flip card` 按钮与 inactive face `inert`。
- **模拟器整合到右下角**：移除正文内联模拟器；新增固定右下角 `Prototype` 开关与可开合 dock（移动端位于固定底部操作条上方）。`?sim=open` 直接展开；`?sim=1` 只启用模拟路径（如钱包不可用按钮），dock 默认收起，避免遮挡产品内容。
- **穹顶抽象化与光晕**：七条线改为各自独立的 apex 与竖向半径、非对称宽度，放大到 1600×920 并作为固定下层绘制，超出屏幕边缘；加 token 派生的 drop-shadow 光晕与 `horizon--glow` 单线；能力状态图例与线条仍同读 `capabilityStates(state)`。
- **验证更新**：模型 28/28；token 28/28、0 自造颜色；浏览器 14/14；axe 15 次 0 violations、5 条 incomplete（6 节点）人工复核；对比度 11/11；离线 3/3；截图 19 张（含 `simulator-dock-open-1440.png`）；320/390/768/960/1440 无横向溢出，完整 BAP ID 与关键 CTA 首屏可见。

### 决策

1. **模拟器默认收起**：避免 dock 展开时遮挡 320px 首屏身份卡与复制按钮；`Prototype` 按钮始终可发现，点击即开启并同时启用模拟路径。
2. **抽象穹顶仍保持七线可及性**：七条 SVG 线为 `aria-hidden` 装饰层，能力名称与状态仍由独立图例列表承担；绘制与图例数据同源。
3. **3D 卡片保留 reduced-motion 分支**：减少动效时不绑定指针倾斜，翻转 transition 置 none，不引入持续动画。

### 验证结果（迭代后）

| 套件 | 结果 | 证据 |
| --- | --- | --- |
| 模型 | 28/28 | `designs/design-flash-mini-001/verification/evidence/model-results.{txt,json}` |
| S2 token | 28/28 解析、0 自造颜色 | `evidence/token-resolution.{txt,json}` |
| 浏览器 | 14/14 | `evidence/browser-checks.{txt,json}` |
| axe | 15 次 0 violations、5 incomplete（6 节点）已复核 | `evidence/axe-summary.json`、`evidence/axe-incomplete-review.json` |
| 对比度 | 11/11 达标 | `evidence/contrast-review.txt` |
| 离线 | 3/3 | `evidence/offline-checks.{txt,json}` |
| 截图 | 19 张 | `evidence/screens/` |

### 唯一下一步

用户打开 `http://127.0.0.1:4400/index.html`（可点右下角 `Prototype` 查看模拟器），确认 3D 卡立体感、穹顶抽象/光晕/出屏感与 mini 版面；确认后把 `_d_meta.json` 的 `needs-review` 改为 `approved` 并置 `done`。

## 2026-09-12 design-flash-mini-001 第三轮：穹顶线条收拢为「上层隐藏光晕」

用户反馈：穹顶线条主要集中在屏幕上方、紧密一些、更细更短，好似隐藏的。

### 完成项

- **收拢到屏幕上方**：`dome-backdrop` 由全屏 fixed 下层改为顶部居中固定层：`top:-10px; left:-12vw; right:-12vw; height:clamp(160px,24vh,280px)`；1440 下实测图层 1786×216，320 下 397×160，仍超出屏幕宽度以保留延伸感。
- **更紧密**：`domeArcs(1200,300)`，宽度比收窄为 `[0.24,0.32,0.4,0.48,0.56,0.64,0.72]`，apex 偏移系数由 0.018 降到 0.012，七条弧在屏幕上方中心形成紧凑扇形。
- **更细更短**：stroke-width 0.8px（active 1.4px），opacity 0.13（active 0.4、deferred 0.26）；弧线基于 300 高 viewBox 生成，天然只保留短弧，不再从地平线拉满全屏。
- **好似隐藏**：低透明度 + token drop-shadow 微光 + `mask-image` 自上而下淡出；SVG 与容器 `overflow: visible`（避免 axe 把 fixed 容器判为不可判定背景），既保持可发现的微光，又不抢占前景。
- **附带**：`hero__copy` 使用 `--s2d-background` 实体背景，保证文本背景可判定；本次调整后欢迎页 axe 回到 0 violations / 0 incomplete。

### 验证结果

- fresh-design 0 命中；模型 28/28；token 28/28、0 自造颜色；浏览器 14/14；axe 15 次 0 violations、5 条 incomplete（6 节点）人工复核；对比度 11/11；离线 3/3；截图 19 张。
- 320/1440 无横向溢出；欢迎页 axe 0 violations、0 incomplete。

### 提交

- 子仓库：`41b54fb`（第三轮视觉迭代，PRD v0.1_20260912-113026）、`3bc2203`（干净检出复验，PRD v0.1_20260912-113246）。

### 唯一下一步

用户复核屏幕上方穹顶的密度、粗细、长度与隐藏感；确认后把 `_d_meta.json` 改为 `approved` 并置 `done`。

## 2026-09-12 design-flash-mini-001 第四轮：线条语义解耦 + 卡片静态立体化

用户反馈：七条线不代表七个能力，线条不美观，提供优化建议；卡片扁平、没有立体感。

### 完成项

- **线条与能力解耦**：穹顶 SVG 不再带 `data-cap-key`/`data-cap-state`，去掉状态节点与橙色虚线；七条弧改为纯装饰性弧线。能力列表单独读 `capabilityStates(state)`，标题由 `Seven capabilities` 改为 `v0.1 capabilities`/`v0.1 能力`，桌面采用 4+3 网格。
- **线条美化**：弧线改用 SVG 横向渐变描边（两端透明、中心 accent），并用 `nth-of-type` 做对称的粗细/透明度分层（0.55–1px、0.05–0.15 opacity），保留顶部收拢、短、细、薄雾隐藏感。
- **卡片静态立体化**：默认姿态增加 `rotateX(-7deg) rotateY(-10deg)` 预倾斜，静态截图即可看到侧面与厚度；景深叠层、加大层级阴影和内高光；指针移动在预倾斜基础上做 ±10°/±7° 视差；reduced-motion 下不绑定指针倾斜。
- **移动端防溢出**：≤760px 下卡片宽度收 4px、景深偏移减小，320px 横向溢出回到 0。

### 验证结果

- fresh-design 0 命中；模型 28/28；token 29/29、0 自造颜色；浏览器 14/14；axe 15 次 0 violations、4–5 条 incomplete（4–6 节点；装饰性头像首字母，少数运行另含 aria-modal 导致的 heading-order）人工复核；对比度 11/11；离线 3/3；截图 19 张。
- 320/390/768/960/1440 无横向溢出，关键 CTA 与完整 BAP ID 首屏可见；欢迎页 axe 0/0。

### 线条优化备选方向（供用户选择）

1. **单侧流光弧**：3–5 条错落弧线，右侧渐隐，动态感更强。
2. **同心细弧扇**：7 条同心对称弧，均匀间距，最克制、最像传统穹顶。
3. **单一穹顶轮廓 + 辅助细线**：只保留 1 条主轮廓与 2–3 条极淡辅助线，最不抢内容。

### 提交

- 子仓库：`780fdc8`（第四轮视觉迭代，PRD v0.1_20260912-122328）、`2bc6430`（干净检出复验，PRD v0.1_20260912-122612）。

### 唯一下一步

用户复核卡片静态立体感与穹顶线条观感；如选择上述备选方向，可在本事项内继续迭代。
