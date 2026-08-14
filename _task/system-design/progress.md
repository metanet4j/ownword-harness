# system-design 进度

## 2026-08-14（四）— 006-4 地平与穹顶（全新设计）

### 决策

- 用户新增第四风格候选：地平+穹顶，代表「话语的基准和秩序」；明确要求不参考前三套风格，重新设计结构、交互与页面风格。
- 方向：天文观测台。全页常驻穹顶天幕（同心高度圈+子午线+方位角刻度+北极星+闪烁恒星）+ 地平基准线；话语如恒星，秩序如刻线与子午线。
- 从 006 仅继承功能状态机、BDD 文案、`data-screen-label`/`data-testid` 契约、3D 卡 DOM、DS 组件与令牌；未读取 006-2/006-3 实现。

### 完成项

- 结构：Header + 常驻 Scene（SVG 穹顶/基准线/标旗/游标）+ 各视图；三标旗（01 身份/02 复核/03 上链）立在基准线上作步进，仅流程页显示。
- 交互：基准线游标——指针沿线移动显示方位角读数（离开即隐）；姓名星座化——setup/edit/review/identity/公共卡五处把字符映射为星点+连线；创建观测弧 0%→50%→100% + 链上日志；3D 公共卡改穹顶卡（半圆穹+星野+基线+星座+金色定位星头像）。
- 皮肤：细字重宽字距无衬线仪表字（EN/zh 行距 1.8）、等宽读数、金铜游标/北极星/标旗、靛蓝深空暗主题。
- 验证全绿：`_verify.mjs` 32/32（CDP 9242）、`_audit.mjs` 17/17（CDP 9244）、console/runtime/network error 0、320px 无溢出、双主题对比度 AA、reduced-motion 静态。
- 独立 Git 仓库提交 `e46cdc3` `(PRD v0.1)`；`_d_meta.json` 资产 needs-review；截图 8 张重新生成。
- 预览：`http://127.0.0.1:4311/own-word-prototype-006-4/index.html`。

### 风险

- 四套对比中，三套功能验证脚本沿用同一契约；006-4 的 `_audit.mjs` 按新风格断言（穹顶/游标/准星头像）。
- 006-4 CDP 端口 9242/9244，与 006-2（9222/9224）、006-3（9232/9234）互斥，并行验证前确认唯一。

---

## 2026-08-14（三）— 006-2 / 006-3 全面重设计

### 决策

- 用户要求另外两套「整体布局、结构、交互都有新的风格，与主题一致」——不再共用 006 的 DOM 与布局，各自重写视图结构。
- 保持跨仓库不变：功能状态机、BDD 文案、`data-screen-label`/`data-testid` 契约、3D 公共卡 DOM、DS 组件与令牌。

### 完成项

- 006-2 信号控制台方向：控制台顶栏+连接读数、雷达扫描欢迎页、双栏控制台表单+输入信号表、传输票据复核、信号灯创建序列、仪表盘身份页、雷达屏 3D 卡、右上角等宽 toast。
- 006-3 航海日志方向：天空/大地欢迎页+指针视差、航程步进轨（01/02/03）、船只沿线行进创建序列、地平线地标身份页、契约坐标铭牌、底部 toast。
- 两仓库验证全绿：`_verify.mjs` 32/32、`_audit.mjs` 17/17、console/runtime/network error 0、320px 无溢出、双主题对比度 AA。

### 风险与教训

- verify/audit 脚本硬编码 CDP 端口（9222/9224）导致两套并行跑时串台，按钮消失、断言错乱、无 console 错误。已区分端口（006-2: 9222/9224，006-3: 9232/9234）；后续并行验证必须先确认端口唯一。
- 三仓库 app.jsx/styles.css 各自独立：后续功能迭代三份同步（等待用户选定风格后收敛）。

---

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
