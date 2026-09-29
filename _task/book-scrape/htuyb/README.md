# 《如何明白圣经》抓取任务

把 cmchurch.org 的《如何明白圣经》朗读版全书（序言 + 22 章）抓成 Markdown，一章一个文件并配总目录，另生成 Word 文档。

## 产物

| 文件 | 说明 |
| --- | --- |
| `目录.md` | 总目录，链接指向各章 Markdown 文件 |
| `00-preface.md` … `22-responding-to-gods-word.md` | 分章 Markdown，共 23 篇 |
| `如何明白圣经.docx` | 全书 Word 文档，A4、宋体正文、黑体标题、首行缩进 2 字符、页脚页码 |
| `book.json` | 章节结构（供 docx 生成器使用） |
| `manifest.json` | 书名、作者、章节与来源 URL 清单 |

## 脚本

| 脚本 | 作用 |
| --- | --- |
| `fetch_html.py` | 串行抓取章节 HTML 到 `raw/`，遇 429 指数退避 |
| `convert.py` | HTML → 分章 Markdown，生成 `book.json` 与 `目录.md` |
| `build_docx.py` | `book.json` → `如何明白圣经.docx` |

执行顺序：

```bash
python3 fetch_html.py
PYTHONPATH=pylibs python3 convert.py
PYTHONPATH=pylibs python3 build_docx.py
```

## 抓取要点

- 站点在连发请求后会对当前 IP 返回 429；带浏览器 User-Agent 的请求被 403/429 拦截，**隐藏 User-Agent 的请求返回 200**。`fetch_html.py` 因此不发送 UA，并在每页之间等待 18–26 秒。
- 正文取自页面 `div.entry-content`，页首朗读音频地址保留为引用行。
- 正文中的 `<em>/<i>` 按纯文本处理，`<a>` 只保留可见文字，避免与作为书名号的星号混在一起被 Markdown 误解析。

## 校验

- 逐章比对网页段落与 Markdown、Word 文本：23 章共 662 个段落全部命中，无缺失、无星号或链接语法残留。
- 总目录 23 条链接全部指向存在的章节文件。
- Word 文档：900 段（含封面、目录与分页空段）、93,250 正文字符、386 处粗体 run。

## 中间数据

`raw/`（章节 HTML）与 `pylibs/`（依赖，含 get-pip.py）为中间数据，未纳入版本管理。
