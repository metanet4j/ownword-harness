# 书籍抓取工具

把一个网页连载的书抓成 Markdown（一章一个文件 + 总目录）、Word 文档和单文件 HTML 阅读版。脚本跨书共用，每本书只维护自己的 `manifest.json`。

## 目录结构

```
_task/book-scrape/
├── README.md                 本文件
├── pylibs/                   依赖（beautifulsoup4、lxml、markdownify、python-docx），不入库
├── lib/
│   ├── bookkit.py            清单与配置加载、粗体解析
│   ├── fetch_html.py         抓取章节 HTML
│   ├── convert.py            HTML → 分章 Markdown + 目录.md + book.json
│   ├── build_docx.py         book.json → Word 文档
│   ├── build_html.py         分章 Markdown → 单文件 HTML 阅读版
│   ├── verify_book.py        核对抓取结果与源页面段落
│   └── scan_questions.py     统计分类页覆盖的问答编号，检查目录是否漏页
├── manifest.template.json    新书清单模板
└── <书名-英文名>/             每本书一个目录
    ├── manifest.json
    ├── raw/                  原始 HTML（不入库）
    ├── 目录.md               总目录
    ├── <slug>.md             分章 Markdown
    ├── <书名>.docx
    └── <书名>.html
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
python3 lib/verify_book.py "<书名-英文名>"
```

目录里的链接可能指向错误页面（站点自身的笔误），抓完先用 `scan_questions.py` 看问答编号是否连续，有缺口就按 sitemap 找回正确地址再补抓。

整页导出的书（一个 HTML 装全书，如 31team.org 的 Drupal book export）：把导出的 HTML 放进该书 `raw/` 目录，在 manifest 里写好 `inline` 段与每章的 `selector`，其余步骤相同。

`fetch_html.py` 支持断点续抓：已存在且大于 20 KB 的章节会跳过，可用 `--start N` 指定起始序号、`--limit N` 先抓前几章验证选择器。

## manifest.json 字段

| 字段 | 说明 |
| --- | --- |
| `book` / `title_en` / `author` / `translator` / `publisher_en` / `source` | 封面与总目录信息，缺失字段自动省略 |
| `site.content_selector` | 正文容器选择器，默认 `div.entry-content` |
| `site.title_selector` | 章节标题选择器，默认 `h1.entry-title` |
| `site.audio_selector` | 朗读音频地址选择器，默认 `audio source[src]`，命中后写入章节 Markdown 的引用行 |
| `site.drop_selector` | 转换前丢弃的元素，默认 `audio, .wp-audio-shortcode, script, style, .sharedaddy, .jp-relatedposts` |
| `inline` | 整页导出模式（如 Drupal 的 `book/export/html/N`）：全书在一个 HTML 里，按 `selector_field`/`title_selector`/`body_selector` 切章，`fetch_html.py` 会自动跳过网络抓取 |
| `docx` | 排版参数：中英文字体、字号、行距、纸张、页边距、页码、输出文件名 |
| `chapters[]` | `part`（部分标题，可空）、`category`（分类标题，可空，用于问答体这类有二级归类的书）、`title`（章节标题）、`slug`（文件名，建议 `序号-英文短名`）、`url` |

`part` 与 `category` 都为空时，Markdown 与 Word 的目录会扁平列出章节；填了则按层级分组。

## HTML 阅读版

`build_html.py` 把各章 `<slug>.md` 渲染成一个自包含的 HTML：样式、脚本、正文全部内联，不请求任何外部资源，用手机浏览器直接打开本地文件（`file://`）即可阅读。输出文件名取自 `docx.filename`（`.docx` 换成 `.html`）。

页面结构：封面（题名页）→ 逐章正文 → 章末「上一篇 / 下一篇」。正文按 Markdown 结构排版，`答：` 开头的段落进「答」卡片，`Q:` / `A:` 开头的段落进中英文对照块，`> 朗读音频：` 引述行渲染成播放器。章节号从小标题里拆出（`12问：…` → 大号数字 `12` + 问字），`解读N、` 小标题拆成编号胶囊 + 标题。

### 导航

桌面端（≥1024px）左侧目录常驻，手机端同一块区域变成侧滑抽屉：

| 功能 | 说明 |
| --- | --- |
| 目录 | 按 `part` → `category` → 章节分层；当前章节高亮并展开其「解读」小节，抽屉打开时自动定位到当前章 |
| 按问号 | 编号网格，按部分分组，点编号直接跳到该问 |
| 搜索 | 同时匹配章节标题与各章小节标题，命中项可直接跳转，分组标题随命中显隐 |
| 字号 | 四档（15/17/19/21 px），点击「Aa」循环 |
| 主题 | 纸色 / 素白 / 夜间三档，点击主题图标循环 |
| 阅读位置 | 顶栏进度条（可点击跳转）+ 顶栏显示当前章节；上次位置记在 localStorage，封面出现「继续阅读」 |
| 键盘 | `[` `]` 上下章，`T` 开合目录，`Esc` 关闭 |

### 视觉

样式全部由 `:root` 的一组令牌驱动（颜色、字阶、间距、圆角、字体），三套主题只覆盖颜色变量。方向是书籍编辑部式：暖纸底 + 衬线正文 + 单一赭红重音，靠字号、字重、发丝线分层次，不靠卡片堆砌。纸纹是内联的 SVG 噪点，字体走系统字体栈（iOS 苹方/宋体，安卓与 Windows 思源），不加载任何网络字体，因此离线可用。

无障碍与打印：正文对比度 ≥9:1、弱化文字 ≥4.8:1、彩色底上的文字 ≥6:1（三套主题均达标）；焦点有可见轮廓；触摸目标 ≥44px；`prefers-reduced-motion` 下关闭过渡；打印时自动隐藏导航并转为单栏白底。

正文里的 `**粗体**`、裸星号转义与 Word 生成器共用 `bookkit.split_bold`，两处排版一致。

> 这个阅读器不绑定 Spectrum S2：S2 是 React 组件库，绑定它要引入 React 运行时，与「单文件离线、手机直开」冲突；S2 也没有长文阅读排版这套东西。它的视觉令牌自成一套，集中在 `:root`，需要换成 S2 色阶时改这一处即可。

## 抓取注意

- 站点在连发请求后会对当前 IP 返回 429，带浏览器 User-Agent 的请求被 403/429 拦截，**隐藏 User-Agent 的请求返回 200**。`fetch_html.py` 因此不发送 UA，并在每页之间等待 18–26 秒；仍建议一章一章慢慢抓。
- 转换时 `<em>/<i>` 取纯文本、`<a>` 只留可见文字，避免与作为书名号的星号混在一起被 Markdown 误解析；`**粗体**` 之外的裸星号会转义。
- 原始 HTML 与 Word 文档一并入库，便于核对和直接取用；`raw/` 也是断点续抓与重新生成 Word 的依据。

## 依赖

`pylibs/` 由 `get-pip.py --target pylibs` 加 `pip install --target pylibs beautifulsoup4 lxml markdownify python-docx` 装入，脚本运行时会自动加入 `sys.path`，不需要额外设置 `PYTHONPATH`。
