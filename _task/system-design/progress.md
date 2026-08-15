# system-design 进度

## 2026-08-15 — design-006 风格样板板（评审辅助）

### 决策

- 用户要求基于现有设计系统推荐三种风格并先看样板再选。样板板作为 design-006 评审辅助，不新建 feature 事项。

### 完成项

- 新建独立仓库 `designs/own-word-prototype-styles-001`：DesignCanvas 并排三张 320×600 样板，同一内容骨架（OWNWORD 顶栏、Wallet 胶囊、Hero 话语、BAP ID 铭牌、Signature valid/ACTIVE、Create my Identity CTA、3D 预览位）。
- 2026-08-15 用户裁决：不复用任何既有方案（穹顶/灯塔/大陆），结合产品特点重给三种。样板板更新为：
- 一 铅字印玺绑定 `react-spectrum4`：纸面细纹 + 衬线压印话语（高光/内影/深影三层）+ 朱砂印章（negative 红）+ 契约式双框铭牌 + 骑缝章。
- 二 账本坐标绑定 `react-spectrum3`：蓝墨格线纸 + 分类账 ticker（BLOCK/PAGE/CH）+ BAP ID 六格坐标 + 链上日志行（BROADCAST/SEEN/ACCEPTED）。
- 三 宣言卷轴绑定 `react-spectrum-s2`（primary）：碑式衬线大字 + 青铜饰线（notice 色）+ 火漆印 + 公开宣言编号铭牌 + 签署栏。
- 三系统经 import-design-system.mjs 导入 `_ds/`，`_d_meta.json` 记录绑定与 primary；资产 4 件 needs-review。

### 验证

- 宿主 in-app Browser：样板板 3 画板 3 iframe 全部渲染；三页 page error 0；accent 实测 一/二=rgb(2,101,220)、三=rgb(86,129,255)（S2 新蓝）；印章、六格坐标、火漆 motif 齐备。
- 独立仓库提交 `353d43b`、`<新提交>` `(PRD v0.1)`。

### 风险

- 本会话模型无图像输入，视觉以 DOM/计算样式断言代替；用户需浏览器目视三张样板。

## 2026-08-15 — design-006 React Spectrum S2 穹顶与地平

### 决策

- 输出全新独立仓库 `designs/own-word-prototype-s2-001`；只以核心认知、PRD v0.1、BAP 协议与 `designs/react-spectrum-s2` 为依据，不读取或复用旧原型实现。
- 视觉采用用户确认的穹顶方案：天蓝光晕、双层穹顶弧、中央刻标、无刻度铁灰地平线、地面阴影、厚重话语；非天文观测台。
- Key Rotation 已移至 PRD v0.1.1；Content、Artifact、Explorer、Relationship 不进入本版。

### 完成项

- Baoyu Design 导入完整 S2 为 primary：namespace `ReactSpectrumS2_ad4872`，应用根节点绑定 `.s2`；使用 Button、ActionButton、Badge、StatusLight、ProgressCircle、S2 Token 与官方 workflow icons。
- 覆盖 PRD v0.1 用户流程：Wallet 全状态；身份解析四分流；Setup 校验、本地头像与身份类型；Review；创建确认/处理/失败/成功；My/Public Identity；Edit 保存/取消/未保存保护；EN/zh-CN、Light/Dark；账户切换与断开。
- Public Identity：八层 CSS 3D 景深，指针旋转 ±9deg；粗指针、≤600px 与 reduced-motion 静态降级。
- `mobile-preview.html` 提供真实 320px iframe 浏览上下文；`preview.png` 为桌面预览图；`_d_meta.json` 已登记 `needs-review`。

### 验证

- 静态：`node verify.mjs` 16/16；S2 + 项目变量闭包无未解析 Token；官方图标均存在；八层深度、320px、粗指针与 reduced-motion 断言通过；`git diff --cached --check` 通过。
- 宿主 in-app Browser：连接钱包→身份解析；无身份 Setup→必填校验→Review→Creating→Ready；Edit 保存/放弃；Wallet/Resolve/Create/Copy 故障；语言/主题、账户切换、断开；页面切换回顶，全部通过。
- 视觉：1280px Welcome、Public 3D、Light/Dark、EN/zh-CN 复核通过；320×680 真实浏览上下文无可见横向溢出或阻塞重叠。
- 独立仓库提交：`48e2926` `feat: design S2 dome identity prototype (PRD v0.1)`。

### 对 PRD / 后端设计的同步事项

- 无新同步项：未引入核心认知与 PRD v0.1 之外的新实体、关系、术语或链上流程。
- 状态保持 `in-progress`：资产为 `needs-review`，等待用户视觉复核后再标 `done`。

## 2026-08-14 — design-005 天蓝光晕+铁灰地平+厚重感原版（007-002）

### 决策

- 用户确认地平基准线无刻度（继承 design-004 2026-08-14 裁决）；feature_list 的 doneCriteria 与 description 冲突已按 description 修正。
- 风格：穹顶天幕（天蓝色光晕）+ 地平基准线（铁灰色阴影、无刻度）+ 配色厚重感；非天文观测台。
- 全新构建 `designs/own-word-prototype-007-002`，独立 Git 仓库，不读取任何现有原型实现；功能行为以核心认知 + PRD v0.1 BDD 为准。

### 完成项

- 隐喻系统：天幕 Sky band（天蓝渐变+径向光晕+穹顶主弧/回响弧/中央刻标）承载话语（衬线碑铭），地平基准线（铁灰粗线+两端帽+地面投影）分隔出地基 Ground 承载事实（等宽读数、表单、铭牌）。
- 功能：覆盖 PRD v0.1 BDD 全部流程（Wallet 全状态、解析分流、Setup 校验、Review、创建生命周期、My Identity、Public 3D 卡、Edit Profile、EN/zh-CN、Light/Dark）。
- 技术：React 18.3.1/ReactDOM/Babel 7.29.0 本地 vendor（npm 下载，无 CDN）；React Spectrum S2 设计系统 primary（import-design-system.mjs 绑定，Button/StatusLight/Badge + --rs-* 令牌）。
- 契约：`data-ow-test` 测试钩子（DS Button 不透传自定义 props，钩子放 OwT 包装层）；故障注入 URL 参数 walletFail/resolveFail/noIdentity/incompleteProfile/createFail/copyFail。
- 验证全绿（提权宿主环境）：`_verify.mjs` 27/27（CDP 9262）、`_audit.mjs` 11/11（CDP 9264）、console/runtime/network error 0、320px 无溢出、双主题对比度 AA、3D 8 层视差、reduced-motion 静态。截图 6 张。
- 独立 Git 仓库提交 `bebe37f` `(PRD v0.1)`；`_d_meta.json` 资产 needs-review，等待用户复核。
- 预览：`http://127.0.0.1:4313/own-word-prototype-007-002/index.html`（服务 job pwsh-2：`python -m http.server 4313 --directory C:\haodev\ownword\designs`）。

### 风险

- 本会话模型无图像输入，截图未回读模型；视觉检查由 `_audit.mjs` 计算样式断言代替，用户需在浏览器复核视觉效果。
- 无头 Chrome 不触发 `:focus-visible` 启发式（CDP 键盘模拟无效）；焦点环改为样式表规则存在性断言（DS components.css + 应用层 styles.css 各有 2px outline 规则）。
- CDP 调试中发现的坑已记录在验证脚本注释：CSSRuleList 不可 for...of、CSSOM shorthand outline 不展开 outlineWidth、CSSStyleRule 也有空 cssRules、navigate 需等 Page.loadEventFired 防竞态。
- 007-002 CDP 端口 9262/9264，与其他原型仓库端口（9222/9224、9232/9234、9242/9244、9252/9254）互斥。

### 对 PRD / 后端设计的同步事项

- 无新同步项：007-002 严格按核心认知与 PRD v0.1 BDD 实现，未引入新术语、状态或流程。

## 2026-08-14 — design-004 修订：话语厚重感 + 地平线去刻度

### 决策

- 用户要求：话语增加厚重感，用阴影表达；地平线不要带刻度。

### 完成项

- 衬线话语元素（Hero/标题/品牌/名字/刻字预览/3D 卡名/对话框标题）统一 `--ow-word-shadow`（light 压印三层、dark 深影三层）。
- Scene 地平基准线去刻度：仅主线+两端帽；删 21 刻度线与刻度数字；刻字预览线去刻度渐变；删未用 centerMark/axisUnit 文案键。
- 验证重跑全绿：`_verify.mjs` 82/82、`_audit.mjs` 27/27（断言更新：基线仅 3 线、无刻度数字、话语 text-shadow 非 none）。
- Git 提交 `a617387` `(PRD v0.1)`；资产仍 needs-review。

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
