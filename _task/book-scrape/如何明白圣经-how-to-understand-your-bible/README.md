# 如何明白圣经（How to Understand Your Bible）

《如何明白圣经》朗读版全书抓取结果，来源 <https://cmchurch.org/how-to-understand-your-bible/>，共序言加 22 章。

抓取、转换与排版流程见[上级说明](../README.md)，本书的章节目录、来源 URL 与排版参数见 [manifest.json](manifest.json)。

## 本书要点

- 站点以 WordPress 承载，正文在 `div.entry-content`，页首附朗读音频，地址保留在各章 Markdown 的引用行。
- 站点对带浏览器 User-Agent 的自动请求返回 403/429，抓取时隐藏 UA 并保持 18–26 秒间隔。

## 产物

| 文件 | 说明 |
| --- | --- |
| `目录.md` | 总目录，链接指向各章 Markdown |
| `00-preface.md` … `22-responding-to-gods-word.md` | 分章 Markdown，共 23 篇 |
| `如何明白圣经.docx` | 全书 Word 文档 |

## 校验

在 `_task/book-scrape` 下执行 `python3 lib/verify_book.py "如何明白圣经-how-to-understand-your-bible"`，核对网页段落与产物：

- 23 章共 662 个段落全部命中 Markdown 与 Word，无缺失
- Word 900 段、93,250 正文字符，无星号或链接语法残留
- 总目录 23 条链接全部有效
