# 基督教预定论（The Reformed Doctrine of Predestination）

《基督教预定论》抓取结果，来源 <http://31team.org/book/export/html/2663>，共 30 章。

作者劳瑞•伯特纳（Loraine Boettner），赵中辉译。原书英文版 The Reformed Doctrine of Predemption，1932 年。

抓取、转换与排版流程见[上级说明](../README.md)，本书条目与排版参数见 [manifest.json](manifest.json)。

## 结构

| 文件 | 说明 |
| --- | --- |
| `目录.md` | 总目录：题记 + 30 章 |
| `000-题记.md` | 作者与译者信息 |
| `01-导论.md` … `30-结论.md` | 30 章正文 |
| `基督教预定论.docx` | 全书 Word 文档 |

## 本站与前面几本不同之处

这是 Drupal 站点的「book export」整页导出：**全书 30 章都在同一个 HTML 文件里**（`book/export/html/2663`，约 31 万字节），章与章之间用 `<h1 class="book-heading">` 分隔，每章正文在 `div.field-item` 里。因此 manifest 用 `inline` 段声明按选择器切章：

```json
"inline": {
  "file": "基督教预定论.html",
  "selector_field": "selector",
  "title_selector": "h1",
  "body_selector": "div.field-item"
}
```

每章条目用 `selector` 指定容器（`#node-2664` 起依次到 `#node-2693`），`convert.py` 据此从同一份 HTML 中切出各章，`fetch_html.py` 遇到此类书只需把导出的 HTML 放进 `raw/`。

章号沿用页面原样，只把「第廿一章」这类旧写法统一成「第二十一章」。

## 正文里保留的原文标注

源文用单个星号标注原文词语，例如「改革宗信仰\*(The Reformed Faith)」、「福音派\*(evangelical)」，全书共 47 处。这些星号按字面保留：Markdown 里转义成 `\*`，Word 里原样显示，不做强调处理。

## 校验

在 `_task/book-scrape` 下执行 `python3 lib/verify_book.py "基督教预定论-reformed-doctrine-of-predestination"`：

- 31 章全部命中 Markdown 与 Word，无缺失段落
- Word 1,739 段、28.8 万正文字符，其中 47 个星号与源文一一对应
- 总目录 31 条链接全部有效
