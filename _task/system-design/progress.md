# 任务进度

## 当前状态

- 最后更新：2026-08-13
- 当前事项：`design-003`（`in-progress`），原型完成，等待用户对比复核
- 状态：第三套原型已交付并验证，三套方案齐备，等待挑选

## 已完成

- [x] 建立任务级工作规则与开工门禁。
- [x] 建立事项状态与跨会话交接机制。
- [x] 明确本目录只保存设计文档，不承担编码任务。
- [x] 初始化 `feature_list.json`，保留一个待开始设计事项。

## 下一步

1. 接收具体 PRD 或实现设计目标。
2. 将 `design-001` 替换为具体事项，并设为唯一 `in-progress` 项。
3. 查阅相关 `spec`、`reference`、代码、日志和数据后开始设计。

## 阻塞与风险

- 当前无具体业务目标，不能录入业务事实或产出设计结论。

## 决策

- 不维护核心认知模板、PRD 模板、实现设计模板或独立评审清单。
- 同时只推进一个事项，完成必须附验证证据。

## 本次文件

- `AGENTS.md`：任务规则。
- `feature_list.json`：事项状态。
- `progress.md`、`session-handoff.md`：进度与交接。

## 验证证据

- [x] 保留文档存在且非空；`feature_list.json` 可解析；最多一个 `in-progress` 事项。
- [x] `init.sh` 已删除；目录无启动或测试脚本。

## 2026-08-13 · design-002

- 当前事项：`design-002`，状态 `in-progress`；`design-001` 暂停为 `blocked`，保证唯一进行项。
- 从零建立 `designs/own-word-prototype-002`；未读取、复制或借鉴 `designs/own-word-prototype`。
- 设计方向：以“身份文档/公开凭证”为主视觉，避免常规卡片后台；使用 React Spectrum 中性色、边框、紧凑控件、语义状态与焦点规范。
- 覆盖：Welcome、Wallet 请求/取消/失败、Identity 解析、Setup、表单校验、Review、创建中、成功、My Identity、完整 BAP ID Copy、Edit Profile、保存/取消、未保存离开保护、Account Switch、Disconnect、中文/英文、Light/Dark、解析失败。
- Key Rotation 依据 PRD 待确认结论下放到 v0.1.1，本原型不包含。
- HTTP：`http://127.0.0.1:4311/own-word-prototype-002/index.html` 返回 200。
- 浏览器：主流程可操作；React Spectrum bundle error 为空；console error 为 0。
- 响应式：1440px 桌面通过；320×740 移动视口 `scrollWidth <= innerWidth`，无横向溢出；移动端隐藏内部“Prototype states”入口，避免遮挡正文。
- 偏好：切换中文和 Dark 后刷新，`lang=zh-CN`、`data-theme=dark` 保留；协议值与用户内容不变。
- 资产：`designs/own-word-prototype-002/_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 待办：用户对比复核后，记录选择结果；复核通过才将 `design-002` 标记 `done`。

## 2026-08-13 · design-003 启动

- 当前唯一事项：`design-003`（`in-progress`）；`design-002` 改为 `blocked`，作为等待对比评审的候选。
- 执行者：下一位 Agent。
- 输出：`designs/own-word-prototype-003`；当前不预建目录，保证下一位 Agent 从零开始。
- 输入只限核心认知、PRD v0.1、React Spectrum；禁止读取两套既有原型的代码、截图、资产、元数据和设计方向。
- 第三套必须独立形成视觉层级、布局结构和交互表达；不得覆盖前两套原型。
- 唯一下一步：下一位 Agent 按门禁读取任务文件，再使用 Baoyu Design 与 React Spectrum 创建、验证第三套原型。

## 2026-08-13 · design-003 实现与验证

- 当前唯一事项：`design-003`（`in-progress`）；`design-002` 保持 `blocked`。
- 输出：`designs/own-word-prototype-003`；从零建立，未读取、复制或借鉴 `designs/own-word-prototype` 与 `designs/own-word-prototype-002` 的代码、截图、资产、元数据或设计方向。
- 方法：按门禁先读 `AGENTS.md`、`feature_list.json`、`progress.md`、`session-handoff.md`，再读核心认知与 PRD v0.1；使用 Baoyu Design 技能，导入脚本绑定 React Spectrum S2 到 `_ds/react-spectrum/`，按 `_ds_prompt.md` 绑定规则用 `--rs-*` 与 `--spectrum-*` 令牌、官方图标资产。
- 第三套视觉与交互独立：工作台应用壳（顶栏 + 状态侧轨 + 右侧身份旅程时间线），BAP ID 用等宽大字号 ledger 展示；不沿用“身份文档/公开凭证”隐喻；Setup 为两步 Profile→Review 向导。
- 覆盖：Welcome、连接取消/失败、解析中/失败、Setup（新建/资料不全）、表单校验、Review、创建中/成功/取消/失败、My Identity、Public Identity、Edit Profile 保存/取消/失败、未保存离开保护、Account Switch、Disconnect、EN/zh-CN、Light/Dark。Key Rotation 不进入本原型（PRD 已下放 v0.1.1）。
- 术语与不变量遵守核心认知：BAP ID 不可编辑、缩略显示但 Copy 返回完整值、取消显示 Cancelled、异常显示 Failed、Wallet 连接不称注册/登录、Locale/Theme 不影响链上值。
- 验证：本地 HTTP `http://127.0.0.1:4311/own-word-prototype-003/index.html` 返回 200；无头 Chrome CDP 自动化 `_verify.mjs` 37/37 通过；React Spectrum bundle `__errors` 为 0；浏览器 console/runtime error 为 0；1440px 桌面 BAP ID 首屏可见；320px 视口 `scrollWidth <= innerWidth` 无横向溢出；语言与主题刷新后持久，BAP ID 跨语言主题不变；复制完整 BAP ID 断言通过。截图：`preview-desktop.png`、`preview-mobile.png`。视觉像素复核跳过（本会话不支持读取图片），以 DOM 几何与计算样式检查替代。
- 资产：`_d_meta.json` 已登记 `index.html`，状态 `needs-review`。
- 待办：用户并排对比三套方案后反馈选择；复核通过前 `design-003` 不标记 `done`。
