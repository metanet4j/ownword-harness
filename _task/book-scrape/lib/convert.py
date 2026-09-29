#!/usr/bin/env python3
"""把 raw/ 里的章节 HTML 转成 Markdown（一章一个文件）并生成总目录。

用法:
  python3 lib/convert.py <书名目录>
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit

bookkit.use_pylibs()

from bs4 import BeautifulSoup  # noqa: E402
from markdownify import MarkdownConverter  # noqa: E402

SITE_DEFAULTS = {
    'content_selector': 'div.entry-content',
    'title_selector': 'h1.entry-title',
    'audio_selector': 'audio source[src]',
    'drop_selector': 'audio, .wp-audio-shortcode, script, style, .sharedaddy, .jp-relatedposts',
}


class ChapterConverter(MarkdownConverter):
    """丢弃音频播放器等站点元素，保留中文全角缩进。"""

    def convert_audio(self, el, text, parent_tags=None, **kw):
        return ''

    def convert_source(self, el, text, parent_tags=None, **kw):
        return ''

    def convert_span(self, el, text, parent_tags=None, **kw):
        return text


def extract(path, site):
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    title_el = soup.select_one(site['title_selector']) if site['title_selector'] else None
    title = title_el.get_text(strip=True) if title_el else ''
    content = soup.select_one(site['content_selector'])
    if content is None:
        return title, '', []
    audio = [a['src'] for a in content.select(site['audio_selector'])]
    for tag in content.select(site['drop_selector']):
        tag.decompose()
    # <em>/<i> 会被转成 *…*，与正文里作为书名号的 * 混在一起造成解析歧义：直接取纯文本
    for tag in content.select('em, i'):
        tag.replace_with(tag.get_text())
    # 标题里再套强调标签会产生 ****文字** 这类畸形标记，标题本身已有层级，直接取纯文本
    for tag in content.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        tag.string = tag.get_text()
    # 正文里的超链接只保留可读文字，链接地址已在页面出处中给出
    for tag in content.find_all('a'):
        tag.replace_with(tag.get_text())
    return title, content.decode_contents(), audio


BOLD_RE = re.compile(r'(?<!\\)\*\*(.+?)(?<!\\)\*\*', re.S)


def align_bold_markers(md):
    """按块（标题、段落、列表项）两两配对 `**`，配不上的按字面文字去掉。

    源站部分段落的强调标签跨越了标题与正文，转换后会出现「段首一个 `**`、
    段中一个 `**`」这种半截标记；只要块内 `**` 个数为奇数，这一块就是错位的，
    整块去标记比留下半截更接近原意。
    """
    out = []
    for line in md.split('\n'):
        runs = list(re.finditer(r'(?<!\\)\*\*', line))
        if len(runs) % 2:
            line = re.sub(r'(?<!\\)\*\*', '', line)
        out.append(line)
    return '\n'.join(out)


def normalize_bold_markers(md):
    """把源页面强调标签造成的畸形粗体标记还原成成对的 `**粗体**`。

    形如 `#### 解读1：****「免我们的债」**意味着什么？**`：三个 `**` 里只有一对
    是真正的粗体。先把按出现顺序能配成对的留下，配不上的交给 align_bold_markers。
    """
    md = re.sub(r'\*{3,}', '**', md)
    runs = [(m.start(), m.end()) for m in re.finditer(r'(?<!\\)\*\*', md)]
    keep = set()
    for i in range(0, len(runs) - 1):
        if i in keep or i + 1 in keep:
            continue
        start, end = runs[i]
        nxt_start, nxt_end = runs[i + 1]
        if not md[end:nxt_start].strip():
            continue                      # 中间没有内容，不成对
        if md[end] in ' \t' or md[nxt_start - 1] in ' \t':
            continue                      # 标记内侧留白，不成对
        keep.update((i, i + 1))
    out, pos = [], 0
    for i, (start, end) in enumerate(runs):
        out.append(md[pos:start])
        out.append(md[start:end] if i in keep else '')
        pos = end
    out.append(md[pos:])
    return ''.join(out)


def escape_stray_asterisks(md):
    """转义 **粗体** 之外的裸星号，避免书名等文字被 Markdown 误解析为强调。"""
    keep = [(m.start(), m.end()) for m in BOLD_RE.finditer(md)]
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
    for m in BOLD_RE.finditer(text):
        if m.start() > pos:
            out.append((text[pos:m.start()], False))
        out.append((m.group(1), True))
        pos = m.end()
    if pos < len(text):
        out.append((text[pos:], False))
    unescape = lambda t: t.replace('\\*', '*')  # noqa: E731  反转义 Markdown 中的 \*
    return [(unescape(t), b) for t, b in out if t] or [(text.replace('\\*', '*'), False)]


def chapter_filename(ch):
    return f"{ch['slug']}.md"


def main():
    bookkit.book_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    mf = bookkit.load_manifest()
    site = {**SITE_DEFAULTS, **mf.get('site', {})}

    doc_parts, missing = [], []
    for ch in mf['chapters']:
        src = f"raw/{ch['slug']}.html"
        if not os.path.exists(src):
            missing.append(ch['slug'])
            continue
        page_title, inner, audio = extract(src, site)
        body = escape_stray_asterisks(align_bold_markers(normalize_bold_markers(
            tidy(ChapterConverter(heading_style='ATX', bullets='-').convert(inner)))))
        heading = f"# {ch['title']}"
        # 页面标题形如「第一章 个人查经是必须的 Personal Bible Study Is a Must」
        subtitle = page_title[len(ch['title']):].strip() if page_title.startswith(ch['title']) else ''
        if subtitle:
            heading += f"\n\n## {subtitle}"
        header = heading + '\n'
        if ch.get('category'):
            header += f"\n> {ch['category']}\n"
        if audio:
            header += f"\n> 朗读音频：{audio[0]}\n"
        md = f"{header}\n{body}"
        open(chapter_filename(ch), 'w', encoding='utf-8').write(md)
        doc_parts.append({'part': ch.get('part'), 'category': ch.get('category'),
                          'title': ch['title'], 'slug': ch['slug'],
                          'audio': audio[0] if audio else None, 'blocks': to_blocks(md)})
        print(f"{ch['slug']:46s} {len(body):7d} chars", flush=True)

    if missing:
        print('MISSING:', missing, file=sys.stderr)
        return 2

    # 总目录：每章一个文件，目录里的链接直接指向该文件
    lines = [f"# {mf['book']}\n"]
    if mf.get('author'):
        lines.append(f"作者：{mf['author']}" + (f"（{mf['title_en']}，{mf['publisher_en']}）  "
                                              if mf.get('title_en') else '  '))
    if mf.get('translator'):
        lines.append(f"翻译：{mf['translator']}  ")
    if mf.get('source'):
        lines.append(f"来源：{mf['source']}\n")
    lines.append('## 目录\n')
    cur, cur_cat = None, None
    for ch in mf['chapters']:
        if ch.get('part') != cur:
            cur, cur_cat = ch.get('part'), None
            if cur:
                lines.append(f"\n**{cur}**\n")
        if ch.get('category') and ch['category'] != cur_cat:
            cur_cat = ch['category']
            lines.append(f"\n*{cur_cat}*\n")
        lines.append(f"- [{ch['title']}]({chapter_filename(ch)})")
    lines.append('')
    open('目录.md', 'w', encoding='utf-8').write('\n'.join(lines).strip() + '\n')

    json.dump({'meta': {k: mf.get(k) for k in
                        ('book', 'author', 'title_en', 'publisher_en', 'translator', 'source')},
               'docx': mf['docx'],
               'chapters': doc_parts},
              open('book.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    total = sum(len(json.dumps(p, ensure_ascii=False)) for p in doc_parts)
    print(f"\n完成：{len(doc_parts)} 章 Markdown + 目录.md + book.json")
    return 0


if __name__ == '__main__':
    sys.exit(main())
