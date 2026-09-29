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


def extract_element(content):
    """从一个正文容器取出 (音频地址列表, 清洗后的 HTML)。"""
    audio = [a['src'] for a in content.select('audio source[src]')]
    for tag in content.select('audio, .wp-audio-shortcode, script, style, .sharedaddy, .jp-relatedposts'):
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
    return audio, content.decode_contents()


def extract(path, site):
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    title_el = soup.select_one(site['title_selector']) if site['title_selector'] else None
    title = title_el.get_text(strip=True) if title_el else ''
    content = soup.select_one(site['content_selector'])
    if content is None:
        return title, '', []
    audio, inner = extract_element(content)
    return title, inner, audio


BOLD_RE = re.compile(r'(?<!\\)\*\*(.+?)(?<!\\)\*\*', re.S)


def normalize_bold_markers(md):
    """只保留块内成对、且都紧贴文字的 `**`，其余按字面删除。

    畸形标记有两个来源：源页面强调标签跨了块（`****文字**`），以及正文里本来
    就有的裸星号（如 `改革宗信仰*(The Reformed Faith)`）被凑成了假配对。
    健壮的粗体标记两侧都紧贴非空白字符，且块内个数为偶数。
    """
    out = []
    for line in md.split('\n'):
        runs = [(m.start(), m.end()) for m in re.finditer(r'(?<!\\)\*\*', line)]
        keep = []
        if len(runs) % 2 == 0:
            for i in range(0, len(runs) - 1, 2):
                start, end = runs[i]
                nxt_start, nxt_end = runs[i + 1]
                opens = end < len(line) and line[end] not in ' \t'
                closes = nxt_start > 0 and line[nxt_start - 1] not in ' \t'
                if opens and closes and line[end:nxt_start].strip():
                    keep.extend((i, i + 1))
        if len(keep) == len(runs):
            out.append(line)
            continue
        buf, pos = [], 0
        for i, (start, end) in enumerate(runs):
            buf.append(line[pos:start])
            buf.append(line[start:end] if i in keep else '')
            pos = end
        buf.append(line[pos:])
        out.append(''.join(buf))
    return '\n'.join(out)


def escape_literal_asterisks(md):
    """把单星号转义为字面量。

    文档里的裸星号都来自源文（如「改革宗信仰*(The Reformed Faith)」这种原文标注），
    转义后 Markdown 显示为 `*`，Word 生成器再把 `\\*` 还原成字面星号。
    """
    return re.sub(r'(?<!\\)(\*\*|\*)',
                  lambda m: '**' if m.group(0) == '**' else '\\*', md)


def normalize_heading_levels(md):
    """正文标题层级从 h2 起，避免与章节标题（h1）之间跳级。

    源页面里问答标题用 h4，转换后直接是 h4，Word 里层级跳跃。
    """
    def shift(m):
        return '#' * max(2, len(m.group(1)) - 2) + ' ' + m.group(2)
    return re.sub(r'^(#{3,6})\s+(.*)$', shift, md, flags=re.M)


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


def load_inline_parts(manifest):
    """整页导出模式：一本书只有一个 HTML（如 Drupal 的 book/export/html），
    按容器选择器切成多章，返回 [{chapter, page_title, inner, audio}]。"""
    inline = manifest['inline']
    path = f"raw/{inline['file']}"
    if not os.path.exists(path):
        raise SystemExit(f'缺少整页导出文件: {path}')
    soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
    out = []
    for ch in manifest['chapters']:
        node = soup.select_one(ch[inline.get('selector_field', 'selector')])
        if node is None:
            continue
        title_el = node.select_one(inline.get('title_selector', 'h1')) if inline.get('title_selector', 'h1') else None
        page_title = title_el.get_text(strip=True) if title_el else ch['title']
        body_el = node.select_one(inline['body_selector'])
        if body_el is None:
            continue
        audio, inner = extract_element(body_el)
        out.append({'chapter': ch, 'page_title': page_title, 'inner': inner, 'audio': audio})
    return out


def main():
    bookkit.book_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    mf = bookkit.load_manifest()
    site = {**SITE_DEFAULTS, **mf.get('site', {})}
    inline_parts = load_inline_parts(mf) if mf.get('inline') else None

    doc_parts, missing = [], []
    for ch in mf['chapters']:
        if inline_parts is not None:
            part = next((p for p in inline_parts if p['chapter'] is ch), None)
            if part is None:
                missing.append(ch['slug'])
                continue
            page_title, inner, audio = part['page_title'], part['inner'], part['audio']
        else:
            src = f"raw/{ch['slug']}.html"
            if not os.path.exists(src):
                missing.append(ch['slug'])
                continue
            page_title, inner, audio = extract(src, site)
        body = escape_literal_asterisks(normalize_bold_markers(normalize_heading_levels(
            tidy(ChapterConverter(heading_style='ATX', bullets='-').convert(inner)))))
        heading = f"# {ch['title']}"
        # 页面标题形如「第一章 个人查经是必须的 Personal Bible Study Is a Must」
        subtitle = page_title[len(ch['title']):].strip() if page_title.startswith(ch['title']) else ''
        if subtitle:
            heading += f"\n\n## {subtitle}"
        header = heading + '\n'
        if ch.get('category') and ch['category'] != ch['title']:
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
        extra = '，'.join(x for x in (mf.get('title_en'), mf.get('publisher_en')) if x)
        lines.append(f"作者：{mf['author']}" + (f"（{extra}）  " if extra else '  '))
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
            if cur_cat != ch['title']:      # 分类名与章节名相同的书不必重复列一行
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
