# 当前进展

官方组件改造版位于独立分支 codex/prototype-official-s2，提交 f3f6844。M01–M06 已实现并验证，视觉复核保持 needs-review。当前按用户最新要求优先 M07：逐个检查内容编辑器的每个按钮和动作。

## 已核实结果

M06 对四模块主要页面及相关状态完成 60 张桌面／320px 截图、60 次自动无障碍检查与 11 项交互断言，未发现横向溢出或自动无障碍违规，视频和音频实际播放、暂停通过。完整报告为 ownword-prototype/evidence/official-s2/acceptance-before/verification.json；这不是所有历史 PRD 的全量 BDD 或生产签名验收。

字体核对发现业务别名缺少官方语言字体顺序。ownword-tokens.css 已按 S2 1.6.0 spectrum-theme.ts 的 sans、serif、code 与简体中文顺序修正；中文正文、标题与官方按钮的计算字体一致。补充两种视口的截图和自动无障碍检查通过，无浏览器错误。前后对照为 ownword-prototype/visual-review.html，上轮对照保留 visual-review-v5.html。

构建、来源／产物校验与全部继承模型通过。历史两条中文动态字体失败 URL 当前复查 HTTP 200，最新字体加载成功；仍不能据此宣称外部 CDN 的间歇故障已经解决。

## 当前方案与待处理项

编辑器按实际任务检查：输入与选区 → 每项格式与菜单 → 模式切换 → 文件／保存 → 离开与发布。每项记录可观察正文与焦点结果；发现问题先复现再修复。沿用官方 S2 控件和既有 CodeMirror／Milkdown，不引入新的编辑器或视觉规则。

跨版本文档核对还发现密钥轮换缺少入口与实现（M08），转移 Review 首屏信息过散（M09）。这两项保留，先处理用户新指出的编辑器。

预览 http://127.0.0.1:4315/。原 v0.4.0 worktree 禁止修改，基线 5b3cdf8。
