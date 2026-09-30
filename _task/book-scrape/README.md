# 书籍抓取工具

把一个网页连载的书抓成 Markdown（一章一个文件 + 总目录）和 Word 文档。脚本跨书共用，每本书只维护自己的 `manifest.json`。

## 目录结构

```
_task/book-scrape/
├── README.md                 本文件
├── pylibs/                   依赖（beautifulsoup4、lxml、markdownify、python-docx），不入库
├── lib/
│   ├── bookkit.py            清单与配置加载
│   ├── fetch_html.py         抓取章节 HTML
│   ├── convert.py            HTML → 分章 Markdown + 目录.md + book.json
│   ├── build_docx.py         book.json → Word 文档
│   ├── verify_book.py        核对抓取结果与源页面段落
│   └── scan_questions.py     统计分类页覆盖的问答编号，检查目录是否漏页
├── manifest.template.json    新书清单模板
└── <书名-英文名>/             每本书一个目录
    ├── manifest.json
    ├── raw/                  原始 HTML（不入库）
    ├── 目录.md               总目录
    ├── <slug>.md             分章 Markdown
    └── <书名>.docx
```

## 抓一本新书

```bash
cd _task/book-scrape
cp manifest.template.json "<书名-英文名>/manifest.json"   # 先建目录
# 填写 manifest.json：书名、作者、site 选择器、chapters 列表
python3 lib/fetch_html.py "<书名-英文名>"
python3 lib/convert.py    "<书名-英文名>"
python3 lib/build_docx.py "<书名-英文名>"
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

## 抓取注意

- 站点在连发请求后会对当前 IP 返回 429，带浏览器 User-Agent 的请求被 403/429 拦截，**隐藏 User-Agent 的请求返回 200**。`fetch_html.py` 因此不发送 UA，并在每页之间等待 18–26 秒；仍建议一章一章慢慢抓。
- 转换时 `<em>/<i>` 取纯文本、`<a>` 只留可见文字，避免与作为书名号的星号混在一起被 Markdown 误解析；`**粗体**` 之外的裸星号会转义。
- 原始 HTML 与 Word 文档一并入库，便于核对和直接取用；`raw/` 也是断点续抓与重新生成 Word 的依据。

## 依赖

`pylibs/` 由 `get-pip.py --target pylibs` 加 `pip install --target pylibs beautifulsoup4 lxml markdownify python-docx` 装入，脚本运行时会自动加入 `sys.path`，不需要额外设置 `PYTHONPATH`。
