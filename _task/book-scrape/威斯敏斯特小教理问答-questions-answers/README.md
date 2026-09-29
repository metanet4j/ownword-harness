# 威斯敏斯特小教理问答（The Westminster Shorter Catechism Explained）

《威斯敏斯特小教理问答》解读抓取结果，来源 <https://cmchurch.org/《威斯敏斯特小教理问答》/>，共 107 问，另含卷首简介。

问答原文为威斯敏斯特会议 1647 年制定，解读据托马斯·文森特（Thomas Vincent, 1634-1678）《The Shorter Catechism Explained and from Scripture》编撰，中译底本为美国正信长老会（OPC）1956 年版。

抓取、转换与排版流程见[上级说明](../README.md)，本书条目与排版参数见 [manifest.json](manifest.json)。

## 结构

| 文件 | 说明 |
| --- | --- |
| `目录.md` | 总目录：简介、三个部分、36 个分类、107 问 |
| `000-简介.md` | 卷首简介（威斯敏斯特会议与本问答的由来） |
| `001-…` … `107-主祷文的结语教导我们什么.md` | 逐问解读，共 107 篇 |
| `威斯敏斯特小教理问答解读.docx` | 全书 Word 文档 |

目录页把 107 问按「部分 → 分类 → 问答」三层组织，`manifest.json` 里的 `part` 与 `category` 字段承载这一层级，Markdown 与 Word 的目录都会照此分组。

## 本书要点

- 每问页面正文以「答：…（和合本经文出处）」开头，随后是中英对照的问与答，再往下是编号的「解读」段落；这些都在 `div.entry-content` 内，与上一本书同构，选择器无需改动。
- 页首无朗读音频，`audio_selector` 未命中，各章 Markdown 因此没有音频引用行。
- 部分「解读」标题里嵌了强调标签，转换后一度出现 `****文字**` 这类畸形粗体标记；现由 `lib/convert.py` 的 `normalize_bold_markers` 与 `align_bold_markers` 规整，正文无残留星号。

## 校验

在 `_task/book-scrape` 下执行 `python3 lib/verify_book.py "威斯敏斯特小教理问答-questions-answers"`：

- 108 章全部命中 Markdown 与 Word，无缺失段落
- Word 2,861 段、178,395 正文字符，865 处粗体，无星号残留
- 总目录 108 条链接全部有效

## 未收录

目录页正文里另有一篇独立文章《我们应当花力气学习威斯敏斯特小教理问答吗？》（<https://cmchurch.org/2016/12/10/我们应当花力气学习威斯敏斯特小教理问答吗？/>），不在 107 问目录内，本次未抓取。
