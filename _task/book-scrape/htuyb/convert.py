#!/usr/bin/env python3
"""把抓取到的章节 HTML 转换为 Markdown，并生成合并稿与目录。

用法:
  PYTHONPATH=pylibs python3 convert.py
"""
import html as H
import json
import os
import re
import sys

from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)

mf = json.load(open('manifest.json', encoding='utf-8'))
os.makedirs('md', exist_ok=True)


class ChapterConverter(MarkdownConverter):
    """保留中文全角缩进，丢弃音频播放器等站点元素。"""

    def convert_audio(self, el, text, parent_tags=None, **kw):
        return ''

    def convert_source(self, el, text, parent_tags=None, **kw):
        return ''

    def convert_span(self, el, text, parent_tags=None, **kw):
        return text


def extract(path):
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    title_el = soup.select_one('h1.entry-title')
    title = title_el.get_text(strip=True) if title_el else ''
    content = soup.select_one('div.entry-content')
    if content is None:
        return title, '', []
    audio = [a['src'] for a in content.select('audio source[src]')]
    for tag in content.select('audio, .wp-audio-shortcode, script, style, .sharedaddy, .jp-relatedposts'):
        tag.decompose()
    # <em>/<i> 会被转成 *…*，与正文里作为书名号的 * 混在一起造成解析歧义：直接取纯文本
    for tag in content.select('em, i'):
        tag.replace_with(tag.get_text())
    # 正文里的超链接只保留可读文字，链接地址已在页面出处中给出
    for tag in content.find_all('a'):
        tag.replace_with(tag.get_text())
    return title, content.decode_contents(), audio


def escape_stray_asterisks(md):
    """转义 **粗体** 之外的裸星号，避免书名等文字被 Markdown 误解析为强调。"""
    keep = [(m.start(), m.end()) for m in re.finditer(r'\*\*(.+?)\*\*', md, re.S)]
    out, pos = [], 0
    for start, end in keep:
        out.append(md[pos:start].replace('*', '\\*'))
        out.append(md[start:end])
        pos = end
    out.append(md[pos:].replace('*', '\\*'))
    return ''.join(out)


def tidy(md):
    md = md.replace('\u00a0', ' ')
    md = re.sub(r'[ \t]+\n', '\n', md)
    md = re.sub(r'\n{3,}', '\n\n', md)
    return md.strip() + '\n'


def to_blocks(md):
    """把章节 Markdown 拆成块列表，供 docx 生成器使用。

    段落保留 **粗体** 标记，由 docx 生成器按 run 拆分。
    """
    blocks = []
    para = []

    def flush():
        if para:
            blocks.append({'type': 'p', 'text': ' '.join(para).strip()})
            para.clear()

    for raw in md.split('\n'):
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        m = re.match(r'^(#{1,6})\s+(.*)$', line)
        if m:
            flush()
            blocks.append({'type': f'h{len(m.group(1))}', 'text': m.group(2).strip()})
            continue
        if line.startswith('> '):
            flush()
            blocks.append({'type': 'quote', 'text': line[2:].strip()})
            continue
        m = re.match(r'^[-*]\s+(.*)$', line)
        if m:
            flush()
            blocks.append({'type': 'li', 'text': m.group(1).strip()})
            continue
        m = re.match(r'^(\d+)\.\s+(.*)$', line)
        if m:
            flush()
            blocks.append({'type': 'li', 'text': m.group(2).strip()})
            continue
        para.append(line.strip())
    flush()
    return blocks


def split_bold(text):
    """把 '前 **粗** 后' 拆成 [(片段, 是否粗体)]，其余星号按字面处理。"""
    out = []
    pos = 0
    for m in re.finditer(r'\*\*(.+?)\*\*', text, re.S):
        if m.start() > pos:
            out.append((text[pos:m.start()], False))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], False))
    unescape = lambda t: t.replace('\\*', '*')  # noqa: E731  反转义 Markdown 中的 \*
    return [(unescape(t), b) for t, b in out if t] or [(text, False)]


def main():
    parts = []
    toc = []
    missing = []
    doc_parts = []
    for ch in mf['chapters']:
        src = f"raw/{ch['slug']}.html"
        if not os.path.exists(src):
            missing.append(ch['slug'])
            continue
        page_title, inner, audio = extract(src)
        body = escape_stray_asterisks(
            tidy(ChapterConverter(heading_style='ATX', bullets='-').convert(inner)))
        heading = f"# {ch['title']}"
        # 页面标题形如「第一章 个人查经是必须的 Personal Bible Study Is a Must」
        subtitle = page_title[len(ch['title']):].strip() if page_title.startswith(ch['title']) else ''
        if subtitle:
            heading += f"\n\n## {subtitle}"
        header = heading + '\n'
        if audio:
            header += f"\n> 朗读音频：{audio[0]}\n"
        md = f"{header}\n{body}"
        open(f"md/{ch['slug']}.md", 'w', encoding='utf-8').write(md)
        parts.append((ch, md))
        doc_parts.append({'part': ch['part'], 'title': ch['title'], 'slug': ch['slug'],
                          'audio': audio[0] if audio else None, 'blocks': to_blocks(md)})
        toc.append((ch['part'], ch['title'], ch['slug']))
        print(f"{ch['slug']:46s} {len(body):7d} chars", flush=True)

    if missing:
        print('MISSING:', missing, file=sys.stderr)
        return 2

    # 目录
    lines = [f"# {mf['book']}\n",
             f"作者：{mf['author']}（{mf['title_en']}，{mf['publisher_en']}）  ",
             f"翻译：{mf['translator']}  ",
             f"来源：{mf['source']}\n",
             '## 目录\n']
    cur = None
    for part, title, slug in toc:
        if part != cur:
            if part:
                lines.append(f"\n**{part}**\n")
            cur = part
        lines.append(f"- [{title}](#{slug})")
    lines.append('')

    # 合并稿：加锚点，便于 Markdown 目录内跳转
    book = ['\n'.join(lines)]
    cur = None
    for ch, md in parts:
        if ch['part'] and ch['part'] != cur:
            book.append(f"\n---\n\n<a id=\"part-{len(book)}\"></a>\n\n## {ch['part']}\n")
            cur = ch['part']
        book.append(f"\n---\n\n<a id=\"{ch['slug']}\"></a>\n\n" + md)
    open('如何明白圣经-全文.md', 'w', encoding='utf-8').write('\n'.join(book).strip() + '\n')
    open('目录.md', 'w', encoding='utf-8').write('\n'.join(lines).strip() + '\n')
    json.dump({'meta': {k: mf[k] for k in ('book', 'author', 'title_en', 'publisher_en',
                                           'translator', 'source')},
               'chapters': doc_parts},
              open('book.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(len(m) for _, m in parts)
    print(f"\n合并完成：{len(parts)} 篇，{total} 字符")
    return 0


if __name__ == '__main__':
    sys.exit(main())
