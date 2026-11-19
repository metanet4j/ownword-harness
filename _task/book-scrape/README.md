# 书籍抓取工具

把一个网页连载的书抓成 Markdown（一章一个文件 + 总目录）、Word 文档和单文件 HTML 阅读版。脚本跨书共用，每本书只维护自己的 `manifest.json`。

## 目录结构

```
_task/book-scrape/
├── README.md                 本文件
├── pylibs/                   依赖（beautifulsoup4、lxml、markdownify、python-docx），不入库
├── lib/
│   ├── bookkit.py            清单与配置加载、粗体解析
│   ├── scripture.py         圣经引用对照：解析「卷 章:节」并从经文库取原文
│   ├── fetch_html.py         抓取章节 HTML
│   ├── convert.py            HTML → 分章 Markdown + 目录.md + book.json
│   ├── build_docx.py         book.json → Word 文档
│   ├── build_html.py         分章 Markdown → 单文件 HTML 阅读版
│   ├── build_epub.py         分章 Markdown → EPUB 3（Apple Books 可读）
│   ├── verify_book.py        核对抓取结果与源页面段落
│   ├── scan_questions.py     统计分类页覆盖的问答编号，检查目录是否漏页
│   ├── bible.py              圣经正典表（66 卷 1189 章）与经文解析
│   └── fetch_bible.py        抓圣经经文：目录页 → manifest、逐章抓取、校验
├── manifest.template.json    新书清单模板
└── <书名-英文名>/             每本书一个目录
    ├── manifest.json
    ├── raw/                  原始 HTML（不入库）
    ├── 目录.md               总目录
    ├── <slug>.md             分章 Markdown
    ├── <书名>.docx
    ├── <书名>.html
    └── <书名>.epub
```

## 抓一本新书

```bash
cd _task/book-scrape
cp manifest.template.json "<书名-英文名>/manifest.json"   # 先建目录
# 填写 manifest.json：书名、作者、site 选择器、chapters 列表
python3 lib/fetch_html.py "<书名-英文名>"
python3 lib/convert.py    "<书名-英文名>"
python3 lib/build_docx.py "<书名-英文名>"
python3 lib/build_html.py "<书名-英文名>"
python3 lib/build_epub.py "<书名-英文名>"
python3 lib/verify_book.py "<书名-英文名>"
```

目录里的链接可能指向错误页面（站点自身的笔误），抓完先用 `scan_questions.py` 看问答编号是否连续，有缺口就按 sitemap 找回正确地址再补抓。

整页导出的书（一个 HTML 装全书，如 31team.org 的 Drupal book export）：把导出的 HTML 放进该书 `raw/` 目录，在 manifest 里写好 `inline` 段与每章的 `selector`，其余步骤相同。

`fetch_html.py` 支持断点续抓：已存在且大于 20 KB 的章节会跳过，可用 `--start N` 指定起始序号、`--limit N` 先抓前几章验证选择器。

## 抓圣经

圣经不适合按「一本普通连载书」抓：66 卷 1189 章，源站偶尔把两节并成一段，个别节在源站本身就漏排。正典表与经文解析放在 `lib/bible.py`，抓取流程放在 `lib/fetch_bible.py`，转换、Word、HTML、EPUB 仍用同一套脚本。

```bash
cd _task/book-scrape
python3 lib/fetch_bible.py "圣经-和合本-bible" manifest   # 读旧约/新约目录页，生成 1189 条 chapters
python3 lib/fetch_bible.py "圣经-和合本-bible" fetch --workers 3
python3 lib/fetch_bible.py "圣经-和合本-bible" verify
python3 lib/fetch_bible.py "圣经-和合本-bible" audit      # 需 pylibs 里装有 pythonbible
python3 lib/convert.py    "圣经-和合本-bible"
python3 lib/build_docx.py "圣经-和合本-bible"
python3 lib/build_html.py "圣经-和合本-bible"
python3 lib/build_epub.py "圣经-和合本-bible"
```

- **只取原文**：manifest 里 `"site": {"verses": true}` 让 `convert.py` 走经文模式，每节一行「节号 + 经文」；逐节注解、祷读、朗读音频都不进产物。
- **raw/ 存裁剪后的片段**：`fetch` 只把经文的 `<p>` 写进 `raw/<slug>.html`，整个目录几 MB，重新生成不必再联网。
- **断点续抓**：已落盘的章节直接跳过；`--limit N` 先抓几章验证解析对不对。
- **校验**：`verify` 逐章核对「节号从 1 起连续覆盖到本章末节」，并汇总全书节数（和合本参考值 31104 节）；发现源站缺节时给出可写入 `source_gaps` 的片段。`audit` 再拿独立的经文分节数据（`pythonbible`）逐章比对，能发现连续节号检查看不出来的末节漏排。
- **HTML 跳转**：经文模式下每章、每节都有锚点，章首有「第 N 节」跳转框，节号本身是 `#v-…` 链接。目录按「旧约/新约 → 66 卷（`<details>` 折叠）→ 章号网格」输出，1189 章压到 66 行，每格显示该章「第 N 章 · M 节」；每章标题下静态写着「共 N 节」。窄屏抽屉用 CSS `:target` 打开（`href="#sidebar"`），不依赖脚本；有脚本时仍走原来那套带滚动锁与当前章定位的交互。为控制体积，静态 HTML 只存「一行一节」的经文文本，段落、锚点与跳转框由页面脚本在加载时生成。
- **并节与缺节**：源站把两节并成一段时写作 `【创廿四29~30】`，产物里是一条「29–30」；源站确实漏排的节记进 manifest 的 `source_gaps`，校验时按缺口放行，不再视为解析失败。
- **标题与文件名**：正典序号 + 英文短名 + 章号组成 slug（如 `01-genesis-001`），全 ASCII，EPUB 与阅读器排序都稳；章标题为「创世记 第1章」，目录按旧约/新约 → 书卷 → 章分三层。

## manifest.json 字段

| 字段 | 说明 |
| --- | --- |
| `book` / `title_en` / `author` / `translator` / `publisher_en` / `source` | 封面与总目录信息，缺失字段自动省略 |
| `edition` | 版本说明，写在总目录与 Word 封面上（如和合本的底本与校订） |
| `site.verses` | 经文模式：只输出经文段落，丢弃注释、祷读与音频 |
| `source_gaps` | 源站确实缺的节：`{"章节 slug": [节号…]}`，校验与转换时按缺口放行 |
| `site.content_selector` | 正文容器选择器，默认 `div.entry-content` |
| `site.title_selector` | 章节标题选择器，默认 `h1.entry-title` |
| `site.audio_selector` | 朗读音频地址选择器，默认 `audio source[src]`，命中后写入章节 Markdown 的引用行 |
| `site.drop_selector` | 转换前丢弃的元素，默认 `audio, .wp-audio-shortcode, script, style, .sharedaddy, .jp-relatedposts` |
| `inline` | 整页导出模式（如 Drupal 的 `book/export/html/N`）：全书在一个 HTML 里，按 `selector_field`/`title_selector`/`body_selector` 切章，`fetch_html.py` 会自动跳过网络抓取 |
| `docx` | 排版参数：中英文字体、字号、行距、纸张、页边距、页码、输出文件名 |
| `scripture` | 圣经引用对照：`source` 填经文书目录名（如 `圣经-和合本-bible`），`inline` 决定是否把经文原文内嵌进产物。见「圣经引用对照」 |
| `chapters[]` | `part`（部分标题，可空）、`category`（分类标题，可空，用于问答体这类有二级归类的书）、`title`（章节标题）、`slug`（文件名，建议 `序号-英文短名`）、`url` |

`part` 与 `category` 都为空时，Markdown 与 Word 的目录会扁平列出章节；填了则按层级分组。

## HTML 阅读版

`build_html.py` 把各章 `<slug>.md` 渲染成一个自包含的 HTML：样式、脚本、正文全部内联，不请求任何外部资源，用手机浏览器直接打开本地文件（`file://`）即可阅读；在 iPhone「文件」App 里预览也能翻目录、跳章（脚本被预览禁用，导航走纯 CSS/HTML，见「无脚本兜底」）。输出文件名取自 `docx.filename`（`.docx` 换成 `.html`）。

页面结构：封面（题名页）→ 逐章正文 → 章末「上一篇 / 下一篇」。正文按 Markdown 结构排版，`答：` 开头的段落进「答」卡片，`Q:` / `A:` 开头的段落进中英文对照块，`> 朗读音频：` 引述行渲染成播放器。章节号从小标题里拆出（`12问：…` → 大号数字 `12` + 问字），`解读N、` 小标题拆成编号胶囊 + 标题。

### 导航

桌面端（≥1024px）左侧目录常驻，手机端同一块区域变成侧滑抽屉：

| 功能 | 说明 |
| --- | --- |
| 目录 | 按 `part` → `category` → 章节分层；当前章节高亮并展开其「解读」小节，抽屉打开时自动定位到当前章 |
| 按问号 | 编号网格，按部分分组，点编号直接跳到该问（章节标题里的阿拉伯数字与中文数字都能识别） |
| 搜索 | 先匹配章节标题与各章小节标题，命中项可直接跳转，分组标题随命中显隐；标题与小节都没命中时扫全文正文（惰性索引，命中词前后带上下文片段）。输入防抖 120ms |
| 书签 | 抽屉底部「☆ 收藏本章」，抽屉里「书签」页列出全部收藏，可跳转或删除（localStorage） |
| 字号 | 六档（15/17/19/21/23/25 px）。点「Aa」依次换档并弹出「字号 21px」轻提示；长按「Aa」（桌面 Shift+点击）打开档位面板直接选；键盘 `+` / `-` 微调 |
| 主题 | 纸色 / 素白 / 夜间三档，点击主题图标循环并提示；**没选过时跟随系统深色**，选过就听用户的 |
| 阅读位置 | 顶栏进度条 + 顶栏显示「百分比 · 当前章」；抽屉底部显示「百分比 · 第几章 / 共几章 · 剩约几分钟」；上次位置记在 localStorage，封面出现「继续阅读」。进度条可点击跳转，但触摸设备上不接管点击——它只有 3px 高，点不准还抢状态栏下拉手势 |
| 章首导航 | 每章开头一排「‹ 上一章 · 目录 · 下一章 ›」，不用滚到章末 |
| 悬浮「下一章」 | 窄屏右下角固定在「目录」上方，目标与提示取自该章自带 pager；最后一章没有下一篇就隐藏。无脚本时隐藏（没有脚本写目标地址） |
| 手势 | 窄屏从屏幕左缘右滑拉出目录，抽屉内左滑关闭；只认横向位移且要求明显大于纵向，不与纵向滚动抢手势 |
| 本章要点 | 章首列出该章各「解读」小节的锚点，直达每个解读点 |
| 键盘 | `[` `]` 上下章，`T` 开合目录，`Esc` 关闭 |

### 窄屏与无脚本导航

iPhone「文件」App 里点 `.html` 走快速查看预览，它**只渲染 HTML/CSS、不执行 JavaScript**（Apple 从 iOS 13 起禁掉本地文件预览脚本），表单控件的交互同样不可靠。所以窄屏下不放任何"点一下才出现"的目录：

| 场景 | 表现 |
| --- | --- |
| 窄屏（< 1024px，含手机与窄窗口）无脚本 | 普通书籍：**目录直接排在正文最前面**，打开就在顶栏下方，无需点击；最前面是紧凑编号网格（一屏内点号直达），下面按部分列出章节。经文类书（圣经）的目录是 66 卷折叠结构、单份就近 170 KB，正文里不再存副本，靠抽屉的 CSS `:target` 打开。条目都是原生 `a[href="#"]`，跳转有 `scroll-margin-top` 不会被吸顶栏挡住 |
| 窄屏 + 有脚本 | 正文里那份目录隐去，打开即见封面；顶栏菜单按钮与右下角「目录」唤起侧滑抽屉（锁滚动、当前章定位、阅读进度） |
| 宽屏（≥ 1024px） | 左侧目录常驻，正文不重复 |

窄屏右下角常驻入口：普通书籍是「目录」（`#btnToToc`，固定在视口右下、位于「回到顶部」上方），有脚本时点它唤起侧滑抽屉并定位到当前章，无脚本时就是个普通锚点，跳回正文顶部的目录；经文类书（圣经）则改成「查找」，点开抽屉并聚焦搜索框，直接输「约11:35」就到该节。因此读到任何一章都能一键回目录，或随时跳到任意一节。

无脚本时仍可用的：页顶常驻目录、紧凑编号索引、章首「上一章/目录/下一章」、本章要点小节索引、跟随系统深色。需要脚本的功能（字号、主题开关、搜索、阅读进度、书签）在无脚本时整块隐去，不留点不动的按钮。实现方式：`<html class="nojs">` 是产物默认状态，脚本能跑时移除它换成 `js`，样式按 `js` / `nojs` 两支分支；目录在构建期生成两份（侧栏一份 + 正文兜底一份 `.toc-copy`，后者无 id），有脚本时正文那份隐藏、抽屉直接用侧栏原装目录，因此不会出现重复 id，也不必在运行时克隆节点。抽屉高度跟随可视视口（`dvh` + `visualViewport`），滚动锁用 `position:fixed` 定位锁而非 `overflow:hidden`——iOS 上 `overflow:hidden` 会让固定层内的点击失活。

滚动联动（当前章高亮、顶栏标题、阅读进度）在加载与 `resize` 时把各章与小节的位置量一次存成数组，滚动时只做二分查找，不在每帧读 `offsetTop` —— 这样 500K 字的文档每帧省掉两次强制回流。抽屉底部的「百分比 · 章节 · 剩余分钟」每半秒最多刷新一次，因为它滚动时本来也看不见。

章数超过 200 的书（目前只有圣经，1189 章）额外启用 `content-visibility:auto`，屏幕外的章节跳过样式与布局，首屏快约 5 倍。它的位置会随渲染变化，所以这两类书在滚动停下 300ms 后重测一次位置，跳转后再按真实位置校正一次落点。

> 早期版本试过 checkbox + label 做"点开目录"的开关，快速查看里这类交互不响应，已去掉；目录改为常驻。

### 视觉

样式全部由 `:root` 的一组令牌驱动（颜色、字阶、间距、圆角、字体），三套主题只覆盖颜色变量。方向是书籍编辑部式：暖纸底 + 衬线正文 + 单一赭红重音，靠字号、字重、发丝线分层次，不靠卡片堆砌。纸感由封面一层静态径向渐变提供；不复用 `feTurbulence` 噪点铺满 `body`（每帧重新栅格化）、不用 `backdrop-filter` 做顶栏实时模糊（几十万字上做高斯模糊，低端机掉帧明显）。字体走系统字体栈（iOS 苹方/宋体，安卓与 Windows 思源），不加载任何网络字体，因此离线可用。

产物是严格单文件：样式、脚本、正文全部内联，不请求任何外部资源。Markdown 里的远程图片在构建期直接跳过——既不内联成 base64（会显著撑大体积），也不留外链（离线打开会破图）。

无障碍与打印：正文对比度 ≥9:1、弱化文字 ≥4.8:1、彩色底上的文字 ≥6:1（三套主题均达标）；焦点有可见轮廓；触摸目标 ≥44px；`prefers-reduced-motion` 下关闭过渡；打印时自动隐藏导航并转为单栏白底。

正文里的 `**粗体**`、裸星号转义与 Word 生成器共用 `bookkit.split_bold`，两处排版一致。

只有标题、下面没有任何内容的小节会在构建期剔除（`build_html.drop_empty_headings`）：源站偶尔留一个空的「目录」小节，它会在目录与「本章要点」里生成一条点了没反应的空条目。小节锚点在剔除之后才编号，正文与目录因此始终一一对应。

> 这个阅读器不绑定 Spectrum S2：S2 是 React 组件库，绑定它要引入 React 运行时，与「单文件离线、手机直开」冲突；S2 也没有长文阅读排版这套东西。它的视觉令牌自成一套，集中在 `:root`，需要换成 S2 色阶时改这一处即可。

## 圣经引用对照

神学类书籍的正文里到处是「（诗86:9；赛60:21；罗11:36）」这样的出处。`lib/scripture.py` 把它们变成可点击的编号，点一下在原地展开和合本原文，方便对照。

在书的 manifest 里声明经文源即可，与书目无关：

```json
"scripture": { "source": "圣经-和合本-bible", "inline": true }
```

- `source`：经文书目录名，其 manifest 需带 `site.verses`。`inline` 为真时把经文内嵌进产物（单文件、离线可读）。
- 构建结束会打印命中情况，如「引用块 1645 处，经文 107233 字」。未命中的出处会单独列出。

**能处理的写法**（都来自真实语料）：

| 写法 | 例子 | 说明 |
| --- | --- | --- |
| 卷 章:节 | `诗86:9` | 缩写与全名都认，66 卷各有一套别名；分节符半角冒号、全角冒号与比例号「∶」都认（《基督教要义》朗读版通篇用 ∶） |
| 连引省略书名 | `诗16:5-11；73:24-26；144:15` | 后两项沿用「诗」 |
| 逗号分节 | `诗66:8,9`、`雅1:22，25` | 中英文逗号都算 |
| 顿号分节 | `约壹3:11、23` | 沿用上一个章号 |
| 节范围 | `诗95:6-7`、`结1:4-27` | |
| 裸数字歧义 | `诗67:1-3；99:3；145` | 145 超出上一章节数，判为章号 |
| 单章书 | `约叁12` | 整卷只有一章时，数字当节号 |
| 并节 | `弗6:2-3` | 源站把两节并成一段，两节都能取到 |
| 干扰项 | `（如：申4:24）`、次经 | 剥掉「如：」等引导词；次经不在和合本里，标灰不可点 |

**体积与性能**：经文不以 DOM 节点预置，只存成一处 `data-text`（每行「节号\t经文」），首次点击时才切片插入，收起只隐藏不重建。威斯敏斯特小教理问答因此从 12,849 个节点、1,440 KB 的成品开始读，而不是把 1,640 个对照面板全铺进文档。

## EPUB 版

`build_epub.py` 把同样的 Markdown 打成 EPUB 3：每章一个 XHTML，附 `nav.xhtml`（EPUB3 目录）与 `toc.ncx`（旧设备兼容），章节之间的跳转改写成跨文件链接。iPhone 上装进「图书」（或任何 EPUB 阅读器）即可——原生翻页、调字号、深色模式、书签、全文搜索都由系统提供，比浏览器打开 HTML 省心。

```bash
python3 lib/build_epub.py "<书名-英文名>"     # 输出 <书名>.epub
```

依赖为零：只用标准库 `zipfile` 写包，复用 `build_html.py` 的 Markdown 解析与行内渲染，所以正文的「答」卡片、Q/A 对照块与 HTML 版一致。

> 校验：`build_epub.py` 产出的包需满足 mimetype 首条目不压缩、OPF manifest 与实际文件一一对应、所有 XHTML 为合法 XML。改了模板后建议解包抽查，或用一个外部 epubcheck 跑一遍。

## 抓取注意

- 站点在连发请求后会对当前 IP 返回 429，带浏览器 User-Agent 的请求被 403/429 拦截，**隐藏 User-Agent 的请求返回 200**。`fetch_html.py` 因此不发送 UA，并在每页之间等待 18–26 秒；仍建议一章一章慢慢抓。
- `cmcbiblereading.net` 挂在 WordPress.com 上，同一本书的响应可能在 `Content-Length` 与 `chunked` 之间切换：不按分块编码解码，十六进制长度头会混进正文，个别节会随机丢失。`fetch_bible.py` 还原分块、核对 `Content-Length` 与 `</html>`，不完整就重试；抓完仍要用 `verify` 逐章核对节号。
- 该站的 HTTPS 握手带 SNI 时会被中间设备直接回 403，不带 SNI、靠 Host 头路由反而稳定 200。`fetch_bible.py` 先走这条通道，失败再退回普通 HTTPS；两条路都只读公开页面。
- 转换时 `<em>/<i>` 取纯文本、`<a>` 只留可见文字，避免与作为书名号的星号混在一起被 Markdown 误解析；`**粗体**` 之外的裸星号会转义。
- 原始 HTML 与 Word 文档一并入库，便于核对和直接取用；`raw/` 也是断点续抓与重新生成 Word 的依据。

## 依赖

`pylibs/` 由 `get-pip.py --target pylibs` 加 `pip install --target pylibs beautifulsoup4 lxml markdownify python-docx` 装入，脚本运行时会自动加入 `sys.path`，不需要额外设置 `PYTHONPATH`。
