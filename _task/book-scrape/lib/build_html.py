#!/usr/bin/env python3
"""把章节 Markdown 渲染成单文件、可离线阅读的 HTML。

用法:
  python3 lib/build_html.py <书名目录> [-o 输出文件名]

产物是一个自包含的 HTML：样式、脚本、正文全部内联，不请求任何外部资源，
用手机浏览器直接打开本地文件（file://）即可阅读、检索、跳转。
内容取自各章 `<slug>.md`，目录层级取自 manifest.json。
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit
import scripture

from bookkit import split_bold  # noqa: E402

HEADING_RE = re.compile(r'^(#{1,6})\s+(.*)$')
QUOTE_RE = re.compile(r'^>\s?(.*)$')
LIST_RE = re.compile(r'^(\s*)([-*+]|(\d+)[.)])\s+(.*)$')
HR_RE = re.compile(r'^\s*(-{3,}|\*{3,}|_{3,})\s*$')
AUDIO_RE = re.compile(r'^(朗读音频|音频)\s*[:：]\s*(\S+)\s*$')
ANSWER_RE = re.compile(r'^(答|回答)\s*[:：]')
ENQ_RE = re.compile(r'^(Q\s*[:：])\s*(.*)$', re.S)
ENA_RE = re.compile(r'^(A\s*[:：])\s*(.*)$', re.S)
INLINE_RE = re.compile(
    r'(?P<img>!\[(?P<alt>[^\]]*)\]\((?P<src>[^)\s]+)(?:\s+"[^"]*")?\))'
    r'|(?P<link>\[(?P<text>[^\]]+)\]\((?P<href>[^)\s]+)(?:\s+"[^"]*")?\))'
    r'|(?P<code>`[^`]+`)'
)
INDEX_HEAD_RE = re.compile(r'^解读\s*(\d+)\s*[、，,.:：]?\s*(.*)$')
QUESTION_RE = re.compile(r'^(\d+)\s*问\s*[：:]\s*(.*)$')
VERSE_LINE_RE = re.compile(r'^(\d+)(?:[–\-—](\d+))?\s+(.*)$')


# ---------------------------------------------------------------- Markdown 解析

def parse_list(lines, i):
    """解析一个列表（可嵌套），返回 (块, 下一行下标)。"""
    first = LIST_RE.match(lines[i])
    base_indent = len(first.group(1))
    ordered = first.group(3) is not None
    start = int(first.group(3)) if ordered else 1
    items = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            j = i
            while j < len(lines) and not lines[j].strip():
                j += 1
            nxt = LIST_RE.match(lines[j]) if j < len(lines) else None
            if nxt and len(nxt.group(1)) >= base_indent:
                i = j
                continue
            break
        m = LIST_RE.match(line)
        if not m:
            break
        indent = len(m.group(1))
        if indent < base_indent:
            break
        if indent > base_indent:
            child, i = parse_list(lines, i)
            if items:
                items[-1]['children'].append(child)
            continue
        if (m.group(3) is not None) != ordered:
            break
        text = m.group(4)
        i += 1
        while i < len(lines) and lines[i].strip() and not LIST_RE.match(lines[i]) \
                and not HEADING_RE.match(lines[i]) and not QUOTE_RE.match(lines[i]) \
                and not HR_RE.match(lines[i]):
            text += ' ' + lines[i].strip()
            i += 1
        items.append({'text': text, 'children': []})
    return {'type': 'ol' if ordered else 'ul', 'start': start, 'items': items}, i


def parse_markdown(md):
    """把章节 Markdown 拆成块列表。"""
    lines = md.replace('\r\n', '\n').split('\n')
    blocks = []
    para = []
    para_indent = False

    def flush():
        nonlocal para_indent
        if para:
            text = ' '.join(x.strip() for x in para).strip()
            para.clear()
            if text:
                blocks.append({'type': 'p', 'text': text, 'indent': para_indent})
            para_indent = False

    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            flush()
            i += 1
            continue
        m = HEADING_RE.match(line)
        if m:
            flush()
            blocks.append({'type': f'h{len(m.group(1))}', 'text': m.group(2).strip()})
            i += 1
            continue
        m = QUOTE_RE.match(line)
        if m:
            flush()
            quoted = []
            while i < len(lines):
                q = QUOTE_RE.match(lines[i])
                if not q:
                    break
                quoted.append(q.group(1).strip())
                i += 1
            blocks.append({'type': 'quote', 'text': ' '.join(q for q in quoted if q)})
            continue
        if HR_RE.match(line):
            flush()
            blocks.append({'type': 'hr'})
            i += 1
            continue
        if LIST_RE.match(line):
            flush()
            block, i = parse_list(lines, i)
            blocks.append(block)
            continue
        if not para:
            para_indent = line.startswith('　')
        para.append(line)
        i += 1
    flush()
    return blocks


# ---------------------------------------------------------------- HTML 渲染

def render_inline(text, anchors):
    """行内 Markdown → HTML。粗体规则与 Word 生成器共用 bookkit.split_bold。"""
    out = []
    for seg, bold in split_bold(text):
        pieces = []
        pos = 0
        for m in INLINE_RE.finditer(seg):
            if m.start() > pos:
                pieces.append(render_text(seg[pos:m.start()]))
            if m.group('img'):
                src = m.group('src')
                # 单文件必须自包含：远程图片既不内联（撑大体积）也不留请求，
                # 构建时直接略过，避免标题区出现破图图标
                if not re.match(r'(?:https?://)?//', src):
                    pieces.append(f'<img src="{html.escape(src, quote=True)}" '
                                  f'alt="{html.escape(m.group("alt"), quote=False)}">')
            elif m.group('link'):
                label = html.escape(m.group('text'), quote=False)
                href = m.group('href')
                target = anchors.get(os.path.basename(href))
                if target:
                    pieces.append(f'<a class="jump" href="#{target}">{label}</a>')
                else:
                    pieces.append(
                        f'<a href="{html.escape(href, quote=True)}" target="_blank" '
                        f'rel="noopener noreferrer">{label}</a>')
            else:
                pieces.append(f'<code>{html.escape(m.group(0)[1:-1], quote=False)}</code>')
            pos = m.end()
        if pos < len(seg):
            pieces.append(render_text(seg[pos:]))
        chunk = ''.join(pieces)
        out.append(f'<strong>{chunk}</strong>' if bold else chunk)
    return ''.join(out)


# 圣经引用对照：由 main() 在 manifest 声明 scripture 段时注入
SCRIPTURE = None


def render_text(text):
    """纯文本片段 → HTML，并把其中的「（卷 章:节）」变成可展开的经文对照。

    只处理「整段括号都是出处」的情形（见 scripture.split_reference_block），
    叙述句里的零散引用保持原样。
    """
    if not SCRIPTURE or '（' not in text:
        return html.escape(text, quote=False)
    out = []
    pos = 0
    for m in scripture.BRACKET_REF_RE.finditer(text):
        block = SCRIPTURE.render_block(m.group(1), lambda s: html.escape(s, quote=False))
        if block is None:
            continue
        out.append(html.escape(text[pos:m.start()], quote=False))
        out.append(block)
        pos = m.end()
    if not out:
        return html.escape(text, quote=False)
    out.append(html.escape(text[pos:], quote=False))
    return ''.join(out)


def split_index(text):
    """把「解读3、标题」拆成 (编号, 标题)；不是解读标题则返回 (None, 原文)。"""
    m = INDEX_HEAD_RE.match(text.strip())
    if m and m.group(2).strip():
        return m.group(1), m.group(2).strip()
    return None, text.strip()


def split_question(title):
    """把「12问：标题」拆成 (编号, 标题)；没有编号则原样返回。"""
    m = QUESTION_RE.match(title.strip())
    if m:
        return m.group(1), m.group(2).strip()
    return None, title.strip()


def render_block(block, anchors, hid=None):
    kind = block['type']
    if kind == 'p':
        text = block['text'].lstrip('　')
        inner = render_inline(text, anchors)
        return f'<p>{inner}</p>'
    if kind in ('h2', 'h3', 'h4', 'h5', 'h6'):
        level = min(int(kind[1]), 4)
        attr = f' id="{hid}"' if hid else ''
        if kind == 'h2':
            num, text = split_index(block['text'])
            if num:
                return (f'<h2{attr}><span class="idx">解读 {html.escape(num, quote=False)}</span>'
                        f'<span class="ht">{render_inline(text, anchors)}</span></h2>')
            return f'<h2{attr}><span class="ht">{render_inline(block["text"], anchors)}</span></h2>'
        return f'<h{level}{attr}>{render_inline(block["text"], anchors)}</h{level}>'
    if kind == 'quote':
        text = block['text']
        audio = AUDIO_RE.match(text)
        if audio:
            url = html.escape(audio.group(2), quote=True)
            return ('<div class="audio"><span class="audio-label">朗读音频</span>'
                    f'<audio controls preload="none" src="{url}"></audio></div>')
        return f'<blockquote>{render_inline(text, anchors)}</blockquote>'
    if kind == 'hr':
        return '<hr>'
    if kind in ('ul', 'ol'):
        tag = kind
        start = ''
        if kind == 'ol' and block.get('start', 1) != 1:
            start = f' start="{block["start"]}"'
        parts = [f'<{tag}{start}>']
        for item in block['items']:
            inner = render_inline(item['text'], anchors)
            for child in item['children']:
                inner += render_block(child, anchors)
            parts.append(f'<li>{inner}</li>')
        parts.append(f'</{tag}>')
        return ''.join(parts)
    return ''


def drop_empty_headings(blocks):
    """去掉下面没有任何内容的标题。

    源站偶尔会留一个只有标题的小节（如「简介」章里那个空的「目录」），
    它会在目录与「本章要点」里生成一条点了没反应的空条目。标题之后若
    直到下一个同级或更高级标题都没有内容，就整条略过。
    """
    kept = []
    for idx, block in enumerate(blocks):
        if block['type'] not in ('h2', 'h3', 'h4', 'h5', 'h6'):
            kept.append(block)
            continue
        level = int(block['type'][1])
        empty = True
        for nxt in blocks[idx + 1:]:
            if nxt['type'] in ('h2', 'h3', 'h4', 'h5', 'h6'):
                if int(nxt['type'][1]) <= level:
                    break
                continue
            empty = False
            break
        if not empty:
            kept.append(block)
    return kept


def render_body(blocks, anchors, cid=None, verse_mode=False, ch_index='v1'):
    """渲染章节正文，并把「答」「中英文问答」整理成独立块。"""
    out = []
    sec = 0
    i = 0
    verse_lines = []

    def flush_verses():
        """经文按「一行一节」输出：行首是节号，随后是经文。

        节锚点不写进静态 HTML —— 31,000 个空 span 要 780 KB，
        而这套阅读器的目标环境是浏览器，脚本会按行号生成 <p class="verse">
        与 #v<章>_<节> 锚点，体积与节点数都省下来。
        """
        if verse_lines:
            out.append('<div class="verses">%s</div>' % '\n'.join(verse_lines))
            verse_lines.clear()

    while i < len(blocks):
        block = blocks[i]
        kind = block['type']
        if verse_mode and kind == 'p':
            v = VERSE_LINE_RE.match(block['text'].strip())
            if v:
                start = int(v.group(1))
                end = int(v.group(2) or start)
                label = str(start) if start == end else f'{start}–{end}'
                verse_lines.append(f'{label} '
                                   f'{html.escape(v.group(3), quote=False)}')
                i += 1
                continue
        if verse_lines:
            flush_verses()
        if kind == 'h2' and cid:
            sec += 1
            out.append(render_block(block, anchors, f'{cid}-s{sec}'))
            i += 1
            continue
        if kind == 'p':
            text = block['text'].lstrip('　')
            plain = ''.join(seg for seg, _ in split_bold(text))
            enq = ENQ_RE.match(text)
            ena = ENA_RE.match(text)
            if enq or ena:
                group = []
                while i < len(blocks) and blocks[i]['type'] == 'p':
                    candidate = blocks[i]['text'].lstrip('　')
                    if not (ENQ_RE.match(candidate) or ENA_RE.match(candidate)):
                        break
                    group.append(candidate)
                    i += 1
                rows = []
                for candidate in group:
                    m = ENQ_RE.match(candidate) or ENA_RE.match(candidate)
                    label = 'Q' if ENQ_RE.match(candidate) else 'A'
                    body = m.group(2) if m.lastindex == 2 else ''
                    rows.append(
                        f'<div class="en-row"><span class="en-tag">{label}</span>'
                        f'<span>{render_inline(body, anchors)}</span></div>')
                out.append('<div class="en">' + ''.join(rows) + '</div>')
                continue
            if ANSWER_RE.match(plain):
                inner = [render_inline(text, anchors)]
                i += 1
                while i < len(blocks) and blocks[i]['type'] in ('ul', 'ol'):
                    inner.append(render_block(blocks[i], anchors))
                    i += 1
                out.append('<div class="answer"><span class="answer-tag">答</span>'
                           '<div class="answer-text">' + ''.join(inner) + '</div></div>')
                continue
        out.append(render_block(block, anchors))
        i += 1
    flush_verses()
    return '\n'.join(out), sec


def render_chapter(ch, md, anchors, pager='', nav_top='', summary='', verse_mode=False,
                   ch_index='v1', blocks=None):
    """渲染一章：标题 + 章首导航 + 本章要点 + 正文 + 章末导航。"""
    if blocks is None:
        blocks = drop_empty_headings(parse_markdown(md))
    body = [b for b in blocks if b['type'] != 'h1']
    title = ch['title']
    category = ch.get('category') or ''
    if not category:
        for b in body:
            if b['type'] == 'quote':
                category = b['text']
                break
    # 分类已作为标题上方的标签展示，正文里重复的引述块不再重复
    if body and body[0]['type'] == 'quote' and body[0]['text'] == category:
        body = body[1:]

    cid = 'ch-' + ch['slug']
    verses = []
    if verse_mode:
        for b in body:
            if b['type'] != 'p':
                continue
            v = VERSE_LINE_RE.match(b['text'].strip())
            if v:
                start = int(v.group(1))
                end = int(v.group(2) or start)
                verses.extend(range(start, end + 1))
    content, sec = render_body(body, anchors, cid, verse_mode, ch_index)
    qnum, qtext = split_question(title)
    kicker = f'<p class="kicker">{html.escape(category, quote=False)}</p>' if category else ''
    if qnum:
        head = ('<div class="qmark"><span class="qmark-n">'
                f'{int(qnum):02d}</span><span class="qmark-w">问</span></div>'
                f'<h1 class="chapter-title">{html.escape(qtext, quote=False)}</h1>')
    else:
        head = f'<h1 class="chapter-title">{html.escape(title, quote=False)}</h1>'
    attrs = ''
    count_label = ''
    if verses:
        # 节数静态写在标题下：不执行脚本时也能看到本章共几节
        attrs = (f' data-vmax="{max(verses)}" data-vcount="{len(verses)}"'
                 f' data-vid="{ch_index}"')
        count_label = f'<p class="chapter-count">共 {len(verses)} 节</p>'
    parts = [
        f'<section class="chapter" id="{cid}" data-title="{html.escape(title, quote=True)}"{attrs}>',
        nav_top,
        '<header class="chapter-head">',
        kicker,
        head,
        count_label,
        '</header>',
        summary,
        '<div class="chapter-body">',
        content,
        '</div>',
        pager,
        '</section>',
    ]
    return '\n'.join(parts), sec


# ---------------------------------------------------------------- 页面组装

def build_toc_html(chapters, headings, root_attrs='class="toc" id="toc"',
                   verse_counts=None):
    """目录用静态 HTML 输出，保证无脚本也能看到章节目录。

    经文类（每章只是一段经文）按卷折叠成章号网格：66 卷 1189 章压成一屏
    可扫的卷名列表，点卷名展开章号，点章号直达，每格悬停显示该章节数。
    其他书仍按「章节 → 小节」逐条列出。
    root_attrs 用于生成第二份副本（无脚本菜单面板），避免重复 id。
    """
    parts = [f'<nav {root_attrs}>']
    if verse_counts:
        return _verse_toc(chapters, verse_counts, parts)
    cur_part = None
    cur_cat = None
    for ch in chapters:
        part = ch.get('part') or ''
        cat = ch.get('category') or ''
        if part != cur_part:
            if cur_part is not None:
                parts.append('</div>')
            parts.append(f'<div class="toc-part">{html.escape(part, quote=False)}</div>')
            parts.append('<div class="toc-group">')
            cur_part, cur_cat = part, None
        if cat != cur_cat:
            if cat:
                # 分类名（圣经里是卷名）直接跳到该分类第一章，方便整卷定位
                parts.append(f'<a class="toc-cat" href="#ch-{ch["slug"]}">'
                             f'{html.escape(cat, quote=False)}</a>')
            cur_cat = cat
        cid = 'ch-' + ch['slug']
        parts.append(f'<div class="toc-row" data-target="{cid}">')
        parts.append(f'<a class="toc-item" href="#{cid}">'
                     f'{html.escape(ch["title"], quote=False)}</a>')
        kids = headings.get(cid, [])
        if kids:
            parts.append('<div class="toc-kids">')
            for kid in kids:
                parts.append(f'<a class="toc-sub" href="#{kid["id"]}">'
                             f'{html.escape(kid["t"], quote=False)}</a>')
            parts.append('</div>')
        parts.append('</div>')
    if cur_part is not None:
        parts.append('</div>')
    parts.append('</nav>')
    return '\n'.join(parts)


def _verse_toc(chapters, verse_counts, parts):
    """经文目录：旧约/新约 → 卷（<details> 折叠）→ 章号网格。"""
    per_book = {}
    for ch in chapters:
        per_book[ch.get('category') or ''] = per_book.get(ch.get('category') or '', 0) + 1

    cur_part = cur_book = None
    book_open = part_open = False
    for ch in chapters:
        part = ch.get('part') or ''
        book = ch.get('category') or ''
        if part != cur_part:
            if book_open:
                parts.append('</details></div>')
            if part_open:
                parts.append('</div>')
            parts.append(f'<div class="toc-part">{html.escape(part, quote=False)}</div>')
            parts.append('<div class="toc-books">')
            cur_part, cur_book = part, None
            book_open, part_open = False, True
        if book != cur_book:
            if book_open:
                parts.append('</details></div>')
            parts.append('<div class="toc-book">')
            parts.append(f'<details><summary>{html.escape(book, quote=False)}'
                         f'<span>{per_book[book]} 章</span></summary>'
                         '<div class="toc-chapgrid">')
            cur_book, book_open = book, True
        cid = 'ch-' + ch['slug']
        number = int(ch['slug'].rsplit('-', 1)[1])
        verses = verse_counts.get(cid, 0)
        title = f'{book} 第{number}章 · {verses} 节'
        parts.append(f'<a class="toc-ch" href="#{cid}" title="{title}"'
                     f' data-target="{cid}" data-vmax="{verses}">{number}</a>')
    if book_open:
        parts.append('</details></div>')
    if part_open:
        parts.append('</div>')
    parts.append('</nav>')
    return '\n'.join(parts)


CN_DIGITS = {'零': 0, '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4,
             '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn_to_int(text):
    """解析 1–99 的中文数字（十、十一、二十、三十六…），失败返回 None。"""
    if not text or any(ch not in CN_DIGITS and ch != '十' for ch in text):
        return None
    if '十' not in text:
        if len(text) == 1:
            return CN_DIGITS[text]
        return None
    head, _, tail = text.partition('十')
    if '十' in tail:
        return None
    tens = CN_DIGITS[head] if head else 1
    ones = CN_DIGITS[tail] if tail else 0
    value = tens * 10 + ones
    return value if 1 <= value <= 99 else None


def chapter_number(title):
    """取章节标题开头的序号：阿拉伯数字或中文数字，返回 int 或 None。"""
    m = re.match(r'^(\d+)', title)
    if m:
        return int(m.group(1))
    m = re.match(r'^([一二三四五六七八九十零〇两]+)(?=[、．.，,]|问)', title)
    if m:
        return cn_to_int(m.group(1))
    return None


def build_numgrid(chapters, root_attrs='class="numgrid" id="numgrid" hidden'):
    """按问号跳转的编号网格。root_attrs 供无脚本面板那份用不同的 class。"""
    parts = [f'<div {root_attrs}>']
    cur_part = None
    opened = False
    for ch in chapters:
        num = chapter_number(ch['title'])
        if num is None:
            continue
        part = ch.get('part') or ''
        if part != cur_part:
            if opened:
                parts.append('</div>')
            parts.append(f'<div class="numgrid-part">{html.escape(part, quote=False)}</div>')
            parts.append('<div class="numgrid-body">')
            cur_part, opened = part, True
        cid = 'ch-' + ch['slug']
        parts.append(f'<a class="num" href="#{cid}" data-target="{cid}">{num}</a>')
    if opened:
        parts.append('</div>')
    parts.append('</div>')
    return '\n'.join(parts)


def build_index(chapters, headings):
    """章节索引：给页面内的搜索脚本或外部工具用（可选，未内联进 HTML）。"""
    data = []
    for ch in chapters:
        cid = 'ch-' + ch['slug']
        data.append({
            'id': cid,
            't': ch['title'],
            'part': ch.get('part') or '',
            'cat': ch.get('category') or '',
            'heads': [{'id': h['id'], 't': h['t']} for h in headings.get(cid, [])],
        })
    return json.dumps(data, ensure_ascii=False)


def page(meta, chapters_html, toc_html, numgrid_html, stats, filename, first_id,
         inline_toc_html='', search_hint='搜索问答或解读标题', verse_mode=False,
         cv_height=0):
    title = meta.get('book', '')
    cover_rows = [
        ('作者 / 解读', meta.get('author')),
        ('翻译', meta.get('translator')),
        ('版本', meta.get('edition')),
        ('英文版', meta.get('publisher_en')),
    ]
    rows = ''.join(
        f'<p class="cover-row"><span class="cover-key">{html.escape(k, quote=False)}</span>'
        f'<span class="cover-val">{html.escape(v, quote=False)}</span></p>'
        for k, v in cover_rows if v)
    source = meta.get('source')
    source_html = ''
    if source:
        host = re.sub(r'^https?://(www\.)?', '', source).split('/')[0]
        source_html = (f'<p class="cover-source">来源：<a href="{html.escape(source, quote=True)}" '
                       f'target="_blank" rel="noopener noreferrer">{html.escape(host, quote=False)}</a></p>')
    title_en = (f'<p class="cover-en">{html.escape(meta["title_en"], quote=False)}</p>'
                if meta.get('title_en') else '')

    page_html = TEMPLATE
    # 章数多的书（圣经 1189 章）开启按需渲染：屏幕外的章节不参与布局。
    # 阈值取 200 —— 百章以内的书整页布局本来就在一帧内。
    # 经文类书另标 verse：右下角入口改成「查找」，直接输「约11:35」到节。
    chapter_count = chapters_html.count('<section class="chapter"')
    root_cls = 'nojs' + (' verse' if verse_mode else '')
    root_style = ''
    if chapter_count > 200:
        root_cls += ' cv'
        root_style = ' style="--cvh:%dpx"' % (cv_height or 2800)
    page_html = page_html.replace(
        '<html lang="zh-CN" class="nojs"',
        '<html lang="zh-CN" class="%s"%s' % (root_cls, root_style),
        1)
    page_html = page_html.replace('{{TITLE}}', html.escape(title, quote=False))
    page_html = page_html.replace('{{TITLE_EN}}', title_en)
    page_html = page_html.replace('{{COVER_ROWS}}', rows)
    page_html = page_html.replace('{{COVER_SOURCE}}', source_html)
    page_html = page_html.replace('{{STATS}}', stats)
    page_html = page_html.replace('{{TOC}}', toc_html)
    page_html = page_html.replace('{{INLINE_TOC}}', inline_toc_html)
    page_html = page_html.replace('{{NUMGRID}}', numgrid_html)
    if not numgrid_html:
        # 没有编号章节的书（如圣经按卷章排）不显示「按问号」页签
        page_html = re.sub(r'\s*<button class="tab" data-tab="num"[^>]*>按问号</button>', '',
                           page_html)
    page_html = page_html.replace('{{CHAPTERS}}', chapters_html)
    page_html = page_html.replace('{{FIRST_ID}}', first_id)
    page_html = page_html.replace('{{FILENAME}}', html.escape(filename, quote=False))
    page_html = page_html.replace('{{SEARCH_HINT}}', html.escape(search_hint, quote=False))
    page_html = page_html.replace('{{VERSE_CSS}}', VERSE_CSS if verse_mode else '')
    page_html = page_html.replace('{{VERSE_JS}}', VERSE_JS if verse_mode else '')
    page_html = page_html.replace('{{VERSE_JS_END}}', VERSE_JS_END if verse_mode else '')
    return page_html

# 只有经文类书（manifest.site.verses）才有这些选择器：一行一节的排版、节锚点、
# 「第 N 节」跳转框、卷折叠目录。普通书籍不带这段，省下载与样式匹配。
VERSE_CSS = r"""
/* ---------- 经文模式 ---------- */
.chapter-body .verses{white-space:pre-line;margin:0 0 .92em;color:var(--ink-2)}
.chapter-body p.verse{text-indent:0;padding-left:2.9em;position:relative}
.chapter-body p.verse span[id]{display:inline}
.chapter-body p.verse .vnum{position:absolute;left:0;top:0;min-width:2em;font-family:var(--sans);
  font-size:.7em;font-weight:600;line-height:2.35;color:var(--accent);text-decoration:none;letter-spacing:.02em}
.chapter-body p.verse .vnum:hover{text-decoration:underline}
.chapter-body p.verse:target,.chapter-body p.verse.hit{background:var(--accent-wash);
  box-shadow:0 0 0 .3em var(--accent-wash);border-radius:3px}
.verse-jump{display:flex;flex-wrap:wrap;align-items:center;gap:.55em;margin:.9em 0 0;
  font-family:var(--sans);font-size:12.5px;color:var(--muted)}
.verse-jump input{width:4.4em;padding:.3em .45em;border:1px solid var(--rule);border-radius:var(--r1);
  background:var(--card);color:var(--ink);font:inherit;text-align:center}
.verse-jump button{padding:.3em .8em;border:1px solid var(--rule);border-radius:var(--r1);
  background:var(--card);color:var(--ink);font:inherit;cursor:pointer}
.verse-jump button:hover{border-color:var(--accent-2);color:var(--accent)}
.verse-jump input.miss{border-color:var(--accent);background:var(--accent-wash)}
/* 越界/不存在的说明文字：占整行，出现时才占位，平时不留空白 */
.vjump-tip{display:none;flex:1 1 100%;margin-top:.2em;color:var(--accent);font-size:12px}
.vjump-tip.on{display:block}
.nojs .verse-jump{display:none}
.chapter-count{margin:.5em 0 0;font-family:var(--sans);font-size:12.5px;color:var(--muted)}
/* 经文目录：卷折叠 + 章号网格，66 卷 1189 章压成一屏可扫的列表 */
.toc-book{margin:0}
.toc-book>details{border-bottom:1px solid var(--rule)}
.toc-book>details>summary{display:flex;align-items:center;justify-content:space-between;gap:.6em;
  min-height:40px;padding:.45em 2px;font-family:var(--sans);font-size:14px;color:var(--ink);
  cursor:pointer;list-style:none}
.toc-book>details>summary::-webkit-details-marker{display:none}
.toc-book>details>summary::after{content:"＋";flex:none;color:var(--muted);font-size:12px}
.toc-book>details[open]>summary::after{content:"－"}
.toc-book>details>summary>span{flex:none;margin-left:auto;color:var(--muted);font-size:11.5px}
.toc-book>details>summary:hover{color:var(--accent)}
.toc-chapgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(40px,1fr));gap:5px;
  padding:.2em 0 .7em}
.toc-book[hidden],.toc-ch[hidden],.toc-part[hidden],.toc-empty[hidden]{display:none!important}
.toc-ch{display:flex;align-items:center;justify-content:center;height:36px;border:1px solid var(--rule);
  border-radius:var(--r1);background:var(--card);color:var(--ink);font-family:var(--sans);
  font-size:13px;text-decoration:none}
.toc-ch:hover{border-color:var(--accent-2);color:var(--accent)}
.toc-ch.current{border-color:var(--accent);background:var(--accent-wash);color:var(--accent);font-weight:700}
.toc-books{display:flex;flex-direction:column}
"""

# 经文模式的检索与「第 N 节」跳转：只在 manifest.site.verses 为真时注入。
# 普通书籍的 DOM 里没有 .verses / .toc-ch / p.verse，带上这段只会白下载、白编译。
VERSE_JS = r"""
    // 建一份「卷章 → 节」索引供全文检索，按需构建、只建一次
    var verseIndex = null;
    function buildVerseIndex() {
      if (verseIndex) return verseIndex;
      verseIndex = sections.map(function (sec) {
        var book = sec.querySelector('.kicker');
        var title = sec.getAttribute('data-title') || '';
        return {
          sec: sec,
          id: sec.id,
          vid: sec.getAttribute('data-vid') || '',
          book: book ? book.textContent : '',
          title: title,
          // 章号：从「创世记 第1章」里取
          chap: (function () {
            var m = /第(\d+)章/.exec(title);
            return m ? Number(m[1]) : 0;
          }())
        };
      });
      return verseIndex;
    }

    // 搜卷名、章号，也搜每一节的经文；命中直接列成可点的结果
    verseSearch = function (q, results) {
      var chapters = buildVerseIndex();
      var hits = [];
      var MAX = 200;
      if (!q) {
        results.hidden = true;
        results.innerHTML = '';
        toc.hidden = false;
        return;
      }
      // 「约11:35」这类精确写法直接当一条结果
      var ref = /^([\u4e00-\u9fa5]{1,8})\s*(\d+)\s*[:：\s]\s*(\d+)$/.exec(q);
      if (ref) {
        var hitId = '';
        chapters.some(function (info) {
          if (info.book.toLowerCase().indexOf(ref[1].toLowerCase()) >= 0
              && info.chap === Number(ref[2])
              && document.getElementById(info.vid + '_' + ref[3])) {
            hitId = info.vid + '_' + ref[3];
            return true;
          }
          return false;
        });
        if (hitId) {
          // 取命中那一节的段落：父节点 textContent 自带行首节号（「28 凡劳苦…」），
          // 会和上面的「太11:28」标签叠成「太11:2828」，先剥掉
          var node = document.getElementById(hitId);
          var para = (node.closest && node.closest('p.verse')) || node.parentNode;
          hits.push({
            id: hitId,
            ref: ref[1] + ref[2] + ':' + ref[3],
            text: para.textContent.replace(/^\s*\d+(?:[–\-—]\d+)?\s*/, '')
          });
        }
      }
      // 章级匹配：卷名或「第N章」
      var chapNum = (function () {
        var m = /^第?\s*(\d+)\s*章?$/.exec(q);
        return m ? Number(m[1]) : 0;
      }());
      chapters.forEach(function (info) {
        if (info.book.toLowerCase().indexOf(q) >= 0 || (chapNum && info.chap === chapNum)) {
          hits.push({id: info.id, ref: info.title, text: '', whole: true});
        }
      });
      // 节级匹配：逐章扫经文
      chapters.forEach(function (info) {
        if (hits.length >= MAX) return;
        Array.prototype.forEach.call(info.sec.querySelectorAll('p.verse'), function (p) {
          if (hits.length >= MAX) return;
          var text = p.textContent;
          if (text.toLowerCase().indexOf(q) < 0) return;
          var num = (p.querySelector('.vnum') || {}).textContent || '';
          hits.push({
            id: p.getAttribute('data-verse'),
            ref: info.title + ':' + num,
            text: text
          });
        });
      });

      var parts = ['<p class="sr-head">' + (hits.length
        ? hits.length + ' 处命中' + (hits.length >= MAX ? '（只列前 ' + MAX + ' 处）' : '')
        : '没有找到「' + q.replace(/[<>&]/g, '') + '」') + '</p>'];
      hits.forEach(function (hit) {
        parts.push('<a class="sr-hit" href="#' + hit.id + '">'
          + '<span class="sr-ref">' + hit.ref + '</span>'
          + (hit.whole || !hit.text ? ''
             : '<span class="sr-text">' + markMatch(hit.text, q) + '</span>')
          + '</a>');
      });
      results.innerHTML = parts.join('');
      results.hidden = false;
      toc.hidden = true;
    };
"""

VERSE_JS_END = r"""
    /* 节定位直接复用 jumpTo：落点统一为「顶栏下方」，不垂直居中
       （居中会落在半屏偏下，读的时候还得再往上找）。 */
    function scrollToVerse(target) {
      jumpTo('#' + target.id);
    }
    // 高亮命中那一节；4 秒足够看清，太短会像闪一下就没
    function markHit(block) {
      if (!block) return;
      block.classList.add('hit');
      clearTimeout(hitClear);
      hitClear = setTimeout(function () { block.classList.remove('hit'); }, 4000);
    }
    // 跳转框下方那行小字：越界与不存在都给出具体原因，而不是让输入框闪一下就没了
    function verseHint(box, text) {
      var tip = box.querySelector('.vjump-tip');
      if (!tip) return;
      tip.textContent = text || '';
      tip.classList[text ? 'add' : 'remove']('on');
    }
    // 经文跳转：每章一个「第 N 节」输入框；节号本身也是锚点，可直接分享 #v-… 链接
    function verseJump(box) {
      var input = box.querySelector('.vjump-input');
      var max = parseInt(box.getAttribute('data-max'), 10) || 0;
      var n = parseInt(input.value, 10);
      if (!n || n < 1 || n > max) {
        input.value = '';
        input.focus();
        verseHint(box, max ? '本章共 ' + max + ' 节，请输入 1–' + max + ' 之间的数字' : '请输入节号');
        return;
      }
      var id = box.getAttribute('data-prefix') + n;
      var target = document.getElementById(id);
      if (!target) {
        input.classList.add('miss');
        setTimeout(function () { input.classList.remove('miss'); }, 1200);
        verseHint(box, '本章没有第 ' + n + ' 节');
        return;
      }
      verseHint(box, '');
      if (history.replaceState) { history.replaceState(null, '', '#' + id); }
      scrollToVerse(target);
      markHit((target.closest && target.closest('.verse')) || target.parentNode || target);
      input.blur();
    }
    document.addEventListener('click', function (e) {
      var btn = e.target.closest ? e.target.closest('.vjump-go') : null;
      if (!btn) return;
      var box = btn.closest('.verse-jump');
      if (box) { e.preventDefault(); verseJump(box); }
    });
    document.addEventListener('keydown', function (e) {
      if (e.key !== 'Enter' || !e.target.classList
          || !e.target.classList.contains('vjump-input')) return;
      e.preventDefault();
      var box = e.target.closest('.verse-jump');
      if (box) verseJump(box);
    });

    // 把每章「一行一节」的文本生成段落、节锚点与章首跳转框。
    // 31,000 多节不在静态 HTML 里各写一层标记：静态只存「节号 经文」，
    // 段落、#v<章>_<节> 锚点与可点的节号都由这里生成。
    (function initVerses() {
      var blocks = document.querySelectorAll('.verses');
      if (!blocks.length) return;
      var re = /^(\d+)(?:[–\-—](\d+))?\s+([\s\S]*)$/;
      Array.prototype.forEach.call(blocks, function (block) {
        var sec = block.closest('.chapter');
        var prefix = sec ? (sec.getAttribute('data-vid') || '') + '_' : '';
        // 静态文本按 \n 分行（white-space:pre-line 只是显示效果，textContent 里确有 \n）
        var lines = block.textContent.split(/\n+/);
        var frag = document.createDocumentFragment();
        lines.forEach(function (line) {
          line = line.replace(/^\s+|\s+$/g, '');
          if (!line) return;
          var m = re.exec(line);
          if (!m) {
            var plain = document.createElement('p');
            plain.textContent = line;
            frag.appendChild(plain);
            return;
          }
          var start = Number(m[1]);
          var end = Number(m[2] || start);
          var p = document.createElement('p');
          p.className = 'verse';
          p.setAttribute('data-verse', prefix + start);
          // 并节（如 29–30）共用一个段落，两个锚点都挂在段首
          for (var n = start; n <= end; n += 1) {
            var sp = document.createElement('span');
            sp.id = prefix + n;
            p.appendChild(sp);
          }
          var a = document.createElement('a');
          a.className = 'vnum';
          a.href = '#' + prefix + start;
          a.textContent = start === end ? String(start) : start + '–' + end;
          p.appendChild(a);
          p.appendChild(document.createTextNode(m[3]));
          frag.appendChild(p);
        });
        block.textContent = '';
        block.appendChild(frag);
      });
      Array.prototype.forEach.call(document.querySelectorAll('.chapter[data-vmax]'), function (sec) {
        var head = sec.querySelector('.chapter-head');
        if (!head) return;
        var max = Number(sec.getAttribute('data-vmax')) || 0;
        var count = Number(sec.getAttribute('data-vcount')) || max;
        var box = document.createElement('div');
        box.className = 'verse-jump';
        box.setAttribute('data-prefix', (sec.getAttribute('data-vid') || '') + '_');
        box.setAttribute('data-max', String(max));
        box.innerHTML = '<label>第 <input class="vjump-input" type="number" min="1" max="'
          + max + '" inputmode="numeric" placeholder="节号" aria-label="跳至本章第几节"> 节</label>'
          + '<button type="button" class="vjump-go">跳转</button>'
          + '<span class="verse-count" title="点节号可复制该节链接">共 ' + count + ' 节</span>'
          + '<span class="vjump-tip" role="status" aria-live="polite"></span>';
        head.appendChild(box);
        // 脚本接管后隐去静态节数，避免与跳转框里的「共 N 节」重复
        var staticCount = head.querySelector('.chapter-count');
        if (staticCount) staticCount.style.display = 'none';
      });
      /* 直接打开 #v1008_35 这类节链接：锚点由脚本生成，浏览器的原生跳转
         早已错过。首屏布局在 load 之后才稳定（尤其开了按需渲染），
         这里等 load + 两帧再定位，之后再补一次校正兜底。 */
      if (/^#v\d+_/.test(location.hash)) {
        var goHash = function () {
          var target = document.getElementById(location.hash.slice(1));
          if (!target) return;
          markHit(target.closest ? target.closest('.verse') : null);
          jumpTo(location.hash);
          // 章节真实高度可能要再等一次重排才定下来，补一次校正
          setTimeout(function () { jumpTo(location.hash); }, 260);
        };
        var kick = function () {
          window.requestAnimationFrame(function () { window.requestAnimationFrame(goHash); });
        };
        if (document.readyState === 'complete') kick();
        else window.addEventListener('load', kick);
      }
    })();
"""

TEMPLATE = r"""<!doctype html>
<html lang="zh-CN" class="nojs" data-theme="paper">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<meta name="theme-color" content="#f4efe4">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>{{TITLE}}</title>
<style>
/* ============================================================
   阅读令牌：颜色 / 字阶 / 间距 / 圆角 / 字体
   方向：书籍编辑部式——暖纸底、衬线正文、单一赭红重音
   ============================================================ */
:root{
  --paper:#f4efe4;      --surface:#faf6ec;    --card:#fffdf8;
  --ink:#211d18;        --ink-2:#443c32;      --muted:#6d6353;
  --rule:#e3d9c5;       --rule-2:#d3c6ad;
  --accent:#9c4a22;     --accent-2:#c2814f;   --accent-wash:rgba(156,74,34,.09);
  --on-accent:#fffdf8;
  --shadow:rgba(74,52,28,.13);

  --fs:17px;  --lh:1.95;  --measure:34em;
  --s1:4px; --s2:8px; --s3:12px; --s4:16px; --s5:24px; --s6:32px; --s7:48px;
  --r1:7px; --r2:11px; --r3:15px;

  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC","Source Han Sans SC","Segoe UI",Roboto,sans-serif;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","Noto Serif SC","SimSun","STSong",Georgia,"Times New Roman",serif;
}
html[data-theme="plain"]{
  --paper:#ffffff; --surface:#f7f7f5; --card:#ffffff;
  --ink:#1c1c1b; --ink-2:#3d3d3a; --muted:#66665f;
  --rule:#e6e6e1; --rule-2:#d6d6cf;
  --accent:#8f4520; --accent-2:#b9764a; --accent-wash:rgba(143,69,32,.08);
  --shadow:rgba(0,0,0,.10);
}
html[data-theme="night"]{
  --paper:#131519; --surface:#181b20; --card:#1e222a;
  --ink:#ded9d0; --ink-2:#c2bdb4; --muted:#8d877d;
  --rule:#2b3038; --rule-2:#363c46;
  --accent:#dd9c68; --accent-2:#b9793f; --accent-wash:rgba(221,156,104,.12);
  --on-accent:#241a12;
  --shadow:rgba(0,0,0,.5);
}
/* 无脚本环境（快速查看等）跟随系统深色；脚本能跑时由 JS 决定主题 */
@media (prefers-color-scheme:dark){
  html:not(.js){
    --paper:#131519; --surface:#181b20; --card:#1e222a;
    --ink:#ded9d0; --ink-2:#c2bdb4; --muted:#8d877d;
    --rule:#2b3038; --rule-2:#363c46;
    --accent:#dd9c68; --accent-2:#b9793f; --accent-wash:rgba(221,156,104,.12);
    --on-accent:#241a12;
    --shadow:rgba(0,0,0,.5);
  }
}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;-webkit-tap-highlight-color:transparent}
body{
  margin:0;background:var(--paper);
  color:var(--ink);font-family:var(--serif);font-size:var(--fs);line-height:var(--lh);
  -webkit-font-smoothing:antialiased;overflow-wrap:break-word;
  text-spacing-trim:space-first;
}
a{color:var(--accent)}
img{max-width:100%;height:auto;border-radius:var(--r2);display:block;margin:1.4em auto}
hr{border:none;border-top:1px solid var(--rule);margin:2em 0}
::selection{background:var(--accent-wash)}
:focus-visible{outline:2px solid var(--accent);outline-offset:2px;border-radius:4px}

/* ---------- 顶栏 ---------- */
.progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:70;cursor:pointer}
.progress span{display:block;height:100%;width:0;background:var(--accent);transition:width .12s linear}
/* 顶栏不透明：实时 backdrop-filter 要在几十万字上做高斯模糊，
   低端 Android 掉帧明显，纯色观感几乎没差 */
.bar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:var(--s1);
  height:calc(54px + env(safe-area-inset-top));padding:env(safe-area-inset-top) var(--s2) 0;
  background:var(--paper);border-bottom:1px solid var(--rule)}
.bar-title{flex:1;min-width:0;text-align:center;font-family:var(--sans);font-size:14.5px;font-weight:600;
  letter-spacing:.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--ink)}
.icon{flex:none;display:flex;align-items:center;justify-content:center;width:40px;height:40px;
  border:0;background:transparent;color:var(--muted);border-radius:var(--r1);cursor:pointer;padding:0}
.icon:hover{background:var(--accent-wash);color:var(--accent)}
.icon svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.6;stroke-linecap:round;stroke-linejoin:round}
.icon-text{font-family:var(--serif);font-size:15px;font-weight:600;letter-spacing:.02em}

/* ---------- 操作轻提示：换档后回执，避免「点了没反应」的错觉 ---------- */
.toast{position:fixed;top:calc(58px + env(safe-area-inset-top));left:50%;transform:translate(-50%,-6px);
  z-index:60;padding:6px 14px;border-radius:999px;border:1px solid var(--rule-2);
  background:var(--card);color:var(--ink);font-family:var(--sans);font-size:13px;
  box-shadow:0 3px 14px var(--shadow);opacity:0;pointer-events:none;
  transition:opacity .18s,transform .18s;white-space:nowrap}
.toast.on{opacity:1;transform:translate(-50%,0)}

/* ---------- 字号档位面板：长按「Aa」或 Shift+点击打开 ---------- */
.size-panel{position:fixed;top:calc(54px + env(safe-area-inset-top));right:var(--s3);z-index:60;
  display:flex;align-items:center;gap:2px;padding:5px;border-radius:var(--r2);
  border:1px solid var(--rule-2);background:var(--card);box-shadow:0 3px 14px var(--shadow);
  font-family:var(--sans)}
.size-panel[hidden]{display:none!important}
.size-panel-label{flex:none;padding:0 6px;font-size:11.5px;letter-spacing:.1em;color:var(--muted)}
.size-opt{min-width:34px;height:30px;border:1px solid transparent;border-radius:var(--r1);
  background:transparent;color:var(--ink);font-family:var(--sans);font-size:13px;
  font-variant-numeric:tabular-nums;cursor:pointer}
.size-opt:hover{background:var(--accent-wash);color:var(--accent)}
.size-opt.on{border-color:var(--accent);background:var(--accent-wash);color:var(--accent);font-weight:700}

/* ---------- 布局 ---------- */
.layout{display:block}
/* 抽屉高度必须贴合可视视口：iOS 上 bottom:0 取的是布局视口，会让固定层超出窗口，
   而超出窗口的固定元素在 iOS Safari 收不到触摸事件 */
.sidebar{display:flex;flex-direction:column;position:fixed;top:0;left:0;width:min(87vw,364px);z-index:50;
  height:calc(100vh - env(safe-area-inset-top));height:calc(100dvh - env(safe-area-inset-top));
  background:var(--surface);border-right:1px solid var(--rule);transform:translateX(-102%);
  transition:transform .3s cubic-bezier(.32,.72,0,1);padding-top:env(safe-area-inset-top);
  touch-action:pan-y;overscroll-behavior:contain}
.sidebar.on{transform:none;box-shadow:0 0 60px var(--shadow)}
.content{min-width:0}
.scrim{position:fixed;inset:0;background:rgba(24,16,8,.44);z-index:45;opacity:0;pointer-events:none;transition:opacity .25s}
.scrim.on{opacity:1;pointer-events:auto}

/* ---------- 侧栏 ---------- */
.side-head{display:flex;align-items:center;justify-content:space-between;gap:var(--s2);
  padding:var(--s3) var(--s2) var(--s2) var(--s4)}
.tabs{display:inline-flex;gap:2px;padding:3px;border-radius:var(--r2);background:var(--paper);border:1px solid var(--rule)}
.tab{padding:6px 13px;border:0;border-radius:8px;background:transparent;color:var(--muted);
  font-family:var(--sans);font-size:13px;cursor:pointer}
.tab.active{background:var(--card);color:var(--accent);font-weight:600;box-shadow:0 1px 2px var(--shadow)}
.search-wrap{position:relative;padding:0 var(--s3) var(--s2)}
.search{width:100%;padding:9px 12px 9px 34px;border-radius:var(--r2);border:1px solid var(--rule);
  background:var(--card);color:var(--ink);font-family:var(--sans);font-size:14.5px}
.search::placeholder{color:var(--muted)}
.search:focus{outline:none;border-color:var(--accent-2);box-shadow:0 0 0 3px var(--accent-wash)}
.search-icon{position:absolute;left:22px;top:50%;transform:translateY(-50%);width:16px;height:16px;
  fill:none;stroke:var(--muted);stroke-width:1.7;stroke-linecap:round;pointer-events:none}
.toc{flex:1;overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y;padding:0 var(--s2) var(--s3) var(--s3)}
.toc-part{margin:var(--s4) 0 var(--s1);padding-top:var(--s3);border-top:1px solid var(--rule);
  font-family:var(--sans);font-size:11.5px;font-weight:700;letter-spacing:.16em;color:var(--accent)}
.toc-cat{margin:var(--s3) 0 2px;padding-left:2px;font-family:var(--sans);font-size:12.5px;color:var(--muted)}
.toc-cat{display:block;text-decoration:none;border-radius:var(--r1)}
.toc-cat:hover{color:var(--accent);background:var(--accent-wash)}
.toc-item{position:relative;display:flex;align-items:center;min-height:44px;padding:8px 10px 8px 12px;
  border-radius:var(--r1);font-family:var(--sans);font-size:14.5px;line-height:1.5;color:var(--ink);text-decoration:none}
.toc-item:hover{background:var(--accent-wash)}
.toc-row.current>.toc-item{color:var(--accent);font-weight:600}
.toc-row.current>.toc-item::before{content:"";position:absolute;left:0;top:8px;bottom:8px;width:2px;
  border-radius:2px;background:var(--accent)}
.toc-kids{display:none;margin:0 0 var(--s2) 14px;padding-left:10px;border-left:1px solid var(--rule)}
.toc-row.current>.toc-kids{display:block}
.toc-sub{display:block;padding:6px 8px;border-radius:6px;font-family:var(--sans);font-size:12.5px;line-height:1.5;
  color:var(--muted);text-decoration:none}
.toc-sub:hover{color:var(--ink)}
.toc-sub.current{color:var(--accent);font-weight:600}
.toc-empty{padding:var(--s5) var(--s3);font-family:var(--sans);font-size:13.5px;color:var(--muted)}
.numgrid{flex:1;overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y;padding:0 var(--s3) var(--s3)}
.numgrid-part{margin:var(--s4) 0 var(--s2);font-family:var(--sans);font-size:11.5px;font-weight:700;
  letter-spacing:.16em;color:var(--accent)}
.numgrid-body{display:grid;grid-template-columns:repeat(auto-fill,minmax(48px,1fr));gap:6px;margin-bottom:var(--s2)}
.num{display:flex;align-items:center;justify-content:center;height:44px;border-radius:var(--r1);
  border:1px solid var(--rule);background:var(--card);color:var(--ink);font-family:var(--sans);font-size:14px;
  font-variant-numeric:tabular-nums;text-decoration:none}
.num:hover{border-color:var(--accent-2);color:var(--accent)}
.num.current{border-color:var(--accent);background:var(--accent-wash);color:var(--accent);font-weight:700}
.side-foot{flex:none;display:flex;align-items:center;justify-content:space-between;gap:var(--s2);
  padding:var(--s3) var(--s4) calc(var(--s3) + env(safe-area-inset-bottom));border-top:1px solid var(--rule);
  font-family:var(--sans);font-size:11.5px;color:var(--muted)}
.side-foot button{border:1px solid var(--rule);background:var(--card);color:var(--muted);border-radius:var(--r1);
  padding:6px 11px;font-family:var(--sans);font-size:12px;cursor:pointer}
.side-foot button:hover{color:var(--accent);border-color:var(--accent-2)}
.marks{flex:1;overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y;padding:0 var(--s3) var(--s3)}
.marks-empty{padding:var(--s5) var(--s3);font-family:var(--sans);font-size:13px;color:var(--muted);line-height:1.8}
.marks .toc-item{padding-left:var(--s3)}
.mark-row{display:flex;align-items:center;gap:var(--s2)}
.mark-row .del{flex:none;border:0;background:transparent;color:var(--muted);cursor:pointer;
  font-size:15px;padding:8px 10px;border-radius:var(--r1)}
.mark-row .del:hover{color:var(--accent);background:var(--accent-wash)}

/* ---------- 封面（题名页） ---------- */
/* 纸感靠一层静态径向渐变：只绘制一次，不随滚动重绘（原先铺满 body 的
   feTurbulence 噪点每帧都要重新栅格化，是移动端滚动的主要开销） */
.cover{min-height:calc(100svh - 54px);display:flex;flex-direction:column;justify-content:center;align-items:center;
  text-align:center;padding:var(--s7) var(--s5) calc(var(--s6) + env(safe-area-inset-bottom));
  background-image:radial-gradient(circle at 50% 30%,var(--surface),transparent 70%)}
.seal{width:50px;height:50px;border-radius:var(--r1);background:var(--accent);color:var(--on-accent);display:flex;
  align-items:center;justify-content:center;font-family:var(--serif);font-size:21px;font-weight:600;
  letter-spacing:.05em;margin-bottom:var(--s5);box-shadow:0 2px 10px var(--accent-wash)}
.cover h1{font-family:var(--serif);font-size:1.72em;line-height:1.45;font-weight:600;margin:0;
  padding:var(--s4) 0;letter-spacing:.02em;
  border-top:1px solid var(--rule-2);border-bottom:3px double var(--rule-2)}
.cover-en{font-family:var(--sans);font-size:.72em;letter-spacing:.22em;text-transform:uppercase;
  color:var(--muted);margin:var(--s4) 0 var(--s5)}
.cover-meta{margin:0 0 var(--s5);padding:var(--s3) 0;width:min(100%,30em);
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.cover-row{margin:0;padding:6px 0;display:flex;gap:var(--s3);text-align:left;
  font-family:var(--sans);font-size:13.5px;line-height:1.6}
.cover-row+.cover-row{border-top:1px dotted var(--rule)}
.cover-key{flex:none;width:5.2em;color:var(--muted);font-size:12.5px}
.cover-val{flex:1;color:var(--ink-2)}
.cover-source{font-family:var(--sans);font-size:11.5px;color:var(--muted);margin:var(--s3) 0 0;word-break:break-all}
.cover-source a{color:var(--muted);text-decoration:none;border-bottom:1px solid var(--rule)}
.cover-stats{display:flex;gap:var(--s4);margin:0 0 var(--s5);font-family:var(--sans);font-size:12.5px;color:var(--muted)}
.cover-stats b{font-family:var(--serif);color:var(--accent);font-size:1.5em;font-weight:600;margin-right:.3em;
  font-variant-numeric:tabular-nums}
.cover-actions{display:flex;flex-direction:column;gap:var(--s2);width:min(100%,300px)}
.btn{display:block;padding:13px 20px;border-radius:var(--r2);border:1px solid var(--rule-2);background:var(--card);
  color:var(--ink);font-family:var(--sans);font-size:14.5px;font-weight:600;text-decoration:none;text-align:center;cursor:pointer}
.btn:hover{border-color:var(--accent-2)}
.btn.primary{background:var(--accent);border-color:var(--accent);color:var(--on-accent)}
.btn.primary:hover{filter:brightness(1.06)}
.cover-foot{margin-top:var(--s5);font-family:var(--sans);font-size:11.5px;color:var(--muted);line-height:1.9}

/* ---------- 正文 ---------- */
main{max-width:var(--measure);margin:0 auto;padding:0 var(--s5) calc(var(--s7) + env(safe-area-inset-bottom))}
/* 锚点定位要躲开顶栏：顶栏高 54px + 刘海安全区，写死 64px 在刘海屏上会被遮住 */
.chapter{padding:var(--s7) 0 var(--s4);border-top:1px solid var(--rule);
  scroll-margin-top:calc(54px + env(safe-area-inset-top) + 10px)}
.chapter-head{margin-bottom:var(--s5)}
/* 章节超过 ~200 时开启按需渲染：屏幕外的章节跳过样式与布局，首屏能快一倍。
   contain-intrinsic-size 取该书的平均章高，否则滚动条长度会明显偏。
   未渲染章节的高度只是估算，跳转后由 jumpTo 再校正一次落点。 */
.cv .chapter{content-visibility:auto;contain-intrinsic-size:auto var(--cvh,2800px)}
/* 被跳转命中的章节退出按需渲染：它的高度一旦是估算值，落到节就会偏，
   而且恢复按需渲染的瞬间位置还会再变一次。 */
.cv .chapter.pin{content-visibility:visible}
.kicker{margin:0 0 var(--s3);font-family:var(--sans);font-size:11.5px;font-weight:700;letter-spacing:.16em;
  color:var(--accent)}
.qmark{display:flex;align-items:baseline;gap:.34em;margin:0 0 .1em}
.qmark-n{font-family:var(--serif);font-size:2.3em;line-height:1;color:var(--accent);font-weight:600;
  letter-spacing:.01em;font-variant-numeric:lining-nums}
.qmark-w{font-family:var(--sans);font-size:.78em;font-weight:700;letter-spacing:.32em;color:var(--muted)}
.chapter-title{margin:0;font-family:var(--sans);font-size:1.26em;line-height:1.55;font-weight:700;letter-spacing:.01em}
.chapter-body p{margin:0 0 .92em;text-indent:2em;text-align:justify;line-break:strict;color:var(--ink-2)}
/* 全文检索结果：卷章 + 命中节的经文片段，点一条直接落到该节 */
.search-results{flex:1;overflow-y:auto;overscroll-behavior:contain;touch-action:pan-y;
  padding:0 var(--s2) var(--s3) var(--s3);font-family:var(--sans)}
.search-results[hidden]{display:none!important}
.sr-head{margin:var(--s2) 0 var(--s2);font-size:11.5px;letter-spacing:.1em;color:var(--muted)}
.sr-hit{display:block;padding:.5em .6em;margin:0 0 4px;border:1px solid var(--rule);border-radius:var(--r1);
  background:var(--card);text-decoration:none;color:var(--ink)}
.sr-hit:hover{border-color:var(--accent-2)}
.sr-ref{display:block;font-size:12px;font-weight:700;color:var(--accent)}
.sr-text{display:block;margin-top:2px;font-family:var(--serif);font-size:13px;line-height:1.65;color:var(--ink-2);
  overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.sr-text mark{background:var(--accent-wash);color:var(--accent);padding:0 .1em}
.sr-more{margin:.3em 0 0;font-size:11.5px;color:var(--muted)}
.chapter-body h2{display:flex;flex-wrap:wrap;align-items:baseline;gap:.7em;
  margin:2.1em 0 .85em;padding-top:1.15em;border-top:1px solid var(--rule);
  font-family:var(--sans);font-size:1.14em;font-weight:700;line-height:1.6;
  scroll-margin-top:calc(54px + env(safe-area-inset-top) + 14px)}
.chapter-body h2 .idx{flex:none;padding:.2em .72em;border:1px solid var(--accent-2);border-radius:999px;
  font-size:.62em;font-weight:700;letter-spacing:.14em;color:var(--accent);line-height:1.5}
.chapter-body h2 .ht{flex:1 1 auto}
.chapter-body h3{font-family:var(--sans);font-size:.99em;font-weight:700;margin:1.5em 0 .6em}
.chapter-body ul,.chapter-body ol{margin:0 0 1em;padding-left:1.6em;color:var(--ink-2)}
.chapter-body li{margin:.36em 0}
.chapter-body ul ul{list-style:circle;margin:.3em 0}
.chapter-body ul ul ul{list-style:square}
.chapter-body ol>li::marker{color:var(--accent);font-weight:600;font-family:var(--sans)}
.chapter-body li>p{margin:.3em 0}
.chapter-body blockquote{margin:0 0 1.1em;padding:.15em 0 .15em 1.1em;color:var(--muted);
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);padding-top:.7em;padding-bottom:.7em}
.answer{margin:0 0 1.4em;padding:var(--s4) var(--s4) var(--s3);background:var(--card);
  border:1px solid var(--rule);border-radius:var(--r2)}
.answer-tag{display:inline-flex;align-items:center;justify-content:center;width:1.95em;height:1.95em;
  border-radius:var(--r1);background:var(--accent);color:var(--on-accent);font-family:var(--sans);font-size:.74em;
  font-weight:700;margin-bottom:var(--s2)}
.answer-text{color:var(--ink);line-height:1.9}
.answer-text p{margin:0 0 .5em;text-indent:0;text-align:justify}
.answer-text p:last-child{margin-bottom:0}
.answer-text strong{font-weight:700}
.en{margin:0 0 1.4em;padding:var(--s3) var(--s4);background:var(--surface);
  border-top:1px solid var(--rule);border-bottom:1px solid var(--rule)}
.en-row{display:flex;gap:.7em;margin:.4em 0;color:var(--muted);font-size:.92em;line-height:1.75}
.en-tag{flex:none;width:1.5em;height:1.5em;border-radius:50%;background:var(--accent-wash);color:var(--accent);
  font-family:var(--sans);font-size:.7em;font-weight:700;display:flex;align-items:center;justify-content:center;
  margin-top:.3em}
.audio{display:flex;align-items:center;gap:.7em;margin:0 0 1.1em;padding:.6em .9em;background:var(--card);
  border:1px solid var(--rule);border-radius:var(--r2)}
.audio-label{flex:none;font-family:var(--sans);font-size:11.5px;color:var(--muted)}
.audio audio{flex:1;min-width:0;height:34px}
.jump{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-2)}

/* ---------- 圣经引用对照 ----------
   默认只显示出处（「诗篇 86:9」），点一下在下方展开和合本原文。
   经文默认用 display:none 收起，展开时才参与布局，不占阅读空间。 */
.refs{display:inline;font-family:var(--sans);font-size:.86em;line-height:1.6;color:var(--accent)}
.ref{display:inline-block;padding:0 .22em;border-radius:4px;cursor:pointer;
  border-bottom:1px dotted var(--accent-2);white-space:nowrap}
.ref:hover{background:var(--accent-wash)}
/* 源文写了和合本没有的节（本书 4 处，均为原文笔误）：标灰不可点 */
.ref-miss{display:inline-block;padding:0 .22em;color:var(--muted);cursor:help;
  border-bottom:1px dotted var(--rule-2);white-space:nowrap}
.refs.open .ref{background:var(--accent-wash);border-bottom-style:solid}
.ref-body{display:none}
.refs.open+.ref-body{display:block}
.ref-text-wrap{margin:.7em 0 1em;padding:var(--s3) var(--s4);background:var(--surface);
  border-left:3px solid var(--accent-2);border-radius:0 var(--r1) var(--r1) 0;
  font-family:var(--serif);font-size:.94em;line-height:1.85;color:var(--ink-2)}
.ref-text{display:block;margin:.1em 0}
.ref-v{display:block}
.ref-v b{display:inline-block;min-width:1.7em;margin-right:.3em;color:var(--accent);
  font-family:var(--sans);font-size:.78em;font-weight:700}
.ref-text+.ref-text{border-top:1px dotted var(--rule);padding-top:.3em;margin-top:.3em}

/* ---------- 章首导航条 ---------- */
.chapter-nav{display:flex;align-items:center;gap:var(--s2);margin:0 0 var(--s5);padding:0 0 var(--s3);
  border-bottom:1px solid var(--rule);font-family:var(--sans);font-size:12.5px}
.chapter-nav a{flex:none;padding:6px 10px;border:1px solid var(--rule);border-radius:999px;
  color:var(--muted);text-decoration:none;max-width:38%;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.chapter-nav a:hover{color:var(--accent);border-color:var(--accent-2)}
.chapter-nav .toc-jump{margin-left:auto;margin-right:auto;font-weight:600;color:var(--ink)}
.chapter-nav .next{margin-left:auto}
.chapter-nav .prev{margin-right:auto}
.chapter-nav span.gap{flex:none}

/* ---------- 本章要点（小节索引） ---------- */
.chapter-sum{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 10px;margin:0 0 var(--s5);
  padding:var(--s3) var(--s4);background:var(--card);border:1px solid var(--rule);border-radius:var(--r2)}
.chapter-sum .sum-label{flex:none;font-family:var(--sans);font-size:11.5px;font-weight:700;
  letter-spacing:.14em;color:var(--accent)}
.chapter-sum a{font-family:var(--sans);font-size:12.5px;color:var(--muted);text-decoration:none;
  padding:2px 8px;border-radius:999px;background:var(--surface)}
.chapter-sum a:hover{color:var(--accent);background:var(--accent-wash)}

/* ---------- 章末导航 ---------- */
.pager{display:flex;gap:var(--s3);margin:var(--s6) 0 0;padding-top:var(--s4);border-top:1px solid var(--rule)}
.pager a{flex:1;min-width:0;padding:.8em .9em;border:1px solid var(--rule);border-radius:var(--r2);
  background:var(--card);text-decoration:none;font-family:var(--sans);font-size:13px;line-height:1.5;color:var(--ink)}
.pager a span{display:block;color:var(--muted);font-size:11px;letter-spacing:.1em;margin-bottom:4px}
.pager a.next{text-align:right}
.pager a:hover{border-color:var(--accent-2)}
.pager a:hover span{color:var(--accent)}

/* ---------- 回到顶部 ---------- */
.to-top{position:fixed;right:var(--s4);bottom:calc(var(--s4) + env(safe-area-inset-bottom));z-index:35;
  width:44px;height:44px;border-radius:50%;border:1px solid var(--rule-2);background:var(--card);
  color:var(--muted);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 14px var(--shadow);
  opacity:0;pointer-events:none;transition:opacity .2s;cursor:pointer}
.to-top.show{opacity:1;pointer-events:auto}
.to-top svg{width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:1.7;stroke-linecap:round;stroke-linejoin:round}

/* ---------- 常驻「目录」入口：窄屏一直可见，读完一章也能一键回目录 ---------- */
.to-toc{position:fixed;right:var(--s4);bottom:calc(var(--s4) + 56px + env(safe-area-inset-bottom));
  z-index:35;display:none;align-items:center;justify-content:center;height:44px;padding:0 16px;
  border-radius:999px;border:1px solid var(--rule-2);background:var(--card);color:var(--ink);
  font-family:var(--sans);font-size:13px;font-weight:600;text-decoration:none;
  box-shadow:0 3px 14px var(--shadow)}
/* 章末的「下一章」固定在右下：手机翻页不必先滑到章尾再找 pager，
   和「查找/目录」「回到顶部」竖着排，两两相隔 52px 不重叠 */
.to-next{position:fixed;right:var(--s4);bottom:calc(var(--s4) + 108px + env(safe-area-inset-bottom));
  z-index:35;display:none;align-items:center;justify-content:center;height:44px;padding:0 16px;
  border-radius:999px;border:1px solid var(--rule-2);background:var(--card);color:var(--accent);
  font-family:var(--sans);font-size:13px;font-weight:600;text-decoration:none;
  box-shadow:0 3px 14px var(--shadow);max-width:40vw;overflow:hidden;
  white-space:nowrap;text-overflow:ellipsis}
.to-next[hidden]{display:none!important}
.inline-toc{scroll-margin-top:64px}

/* ---------- 桌面端：侧栏常驻 ---------- */
@media (min-width:1024px){
  body{font-size:calc(var(--fs) + 1px)}
  .layout{display:grid;grid-template-columns:336px minmax(0,1fr);align-items:start}
  .sidebar{position:sticky;top:0;height:100vh;width:auto;transform:none!important;box-shadow:none!important}
  .side-head{padding-top:var(--s4)}
  #btnMenu{display:none}
  .menu-link,.close-link{display:none!important}
  .scrim{display:none}
  .bar-title{text-align:left;padding-left:var(--s2)}
  main{max-width:calc(var(--measure) + 2em);padding:0 var(--s6) var(--s7)}
  .chapter{padding-top:var(--s7)}  .cover{min-height:calc(100svh - 54px)}
  .to-top{right:var(--s6)}
}
@media (max-width:420px){
  main{padding-left:var(--s4);padding-right:var(--s4)}
  .pager{gap:var(--s2)}
  .pager a{font-size:12.5px;padding:.7em .75em}
}
@media (prefers-reduced-motion:reduce){
  *{animation-duration:.01ms!important;transition-duration:.01ms!important;scroll-behavior:auto!important}
}

/* ---------- 无脚本兜底 ----------
   iPhone「文件」App 的快速查看只渲染 HTML/CSS、不执行 JavaScript，连表单控件的
   交互也不可靠。因此这里不放任何需要"点一下才出现"的东西：
   窄屏下目录直接排进正文最前面（不论脚本能否运行），跳转是原生 a[href="#"]。
   必须有脚本的功能（字号/主题/搜索/阅读进度/编号网格）整块隐去，不留死按钮。 */
/* [hidden] 要靠作者样式兜住：下面几条 display 规则会把它覆盖掉 */
.numgrid[hidden],.toc[hidden]{display:none!important}
.nojs #btnMenu{display:none}
/* 无脚本时改用锚点开合抽屉：<a href="#sidebar"> 靠 :target 滑出 */
.menu-link{display:none}
.nojs .menu-link{display:flex}
.nojs .close-link{display:flex}
.close-link{display:none}
.inline-toc{display:none}
.inline-toc-head{display:flex;align-items:baseline;gap:var(--s3);margin:0 0 var(--s3);
  font-family:var(--sans);font-size:12px;font-weight:700;letter-spacing:.16em;color:var(--accent)}
.inline-toc-head span{font-size:11px;font-weight:400;letter-spacing:.02em;color:var(--muted)}
.nojs #numgrid{display:none!important}
.nojs .tab,.nojs .search-wrap,.nojs .to-top,.nojs .progress,
.nojs .toast,.nojs .size-panel,
.nojs #btnSize,.nojs #btnTheme{display:none!important}
.nojs .side-foot{display:none}
@media (max-width:1023px){
  /* 抽屉用 CSS :target 打开：#sidebar 命中时侧栏滑出，不依赖脚本。
     有脚本时仍走 .on 那套（能带当前章定位、锁滚动），两者互不冲突。 */
  .sidebar{display:none}
  .sidebar:target,.sidebar.on{display:flex;transform:none;box-shadow:0 0 60px var(--shadow)}
  /* 遮罩同样只靠 CSS：:has() 得到支持就显示，没支持也不影响抽屉本身 */
  body:has(.sidebar:target) .scrim{display:block;opacity:1;pointer-events:auto}
  /* 窄屏（放不下常驻侧栏）在无脚本时把目录排进正文最前面：
     快速查看里打开就能看到。有脚本时抽屉已经能开，正文这份只会挡住封面。 */
  .inline-toc{display:block;margin:0 0 var(--s5);padding:var(--s4) 0 var(--s5);
    border-bottom:1px solid var(--rule)}
  .js .inline-toc{display:none}
  .to-toc{display:flex}
  .to-next{display:flex}
  /* 无脚本时「下一章」没有脚本写入目标地址，留着就是个点了不动的按钮 */
  .nojs .to-next{display:none!important}
  .inline-toc .toc{display:block;overflow:visible;padding:0;flex:none}
  .inline-toc .numgrid{flex:none;overflow:visible;padding:0;margin:0 0 var(--s3)}
  .inline-toc .numgrid-body{grid-template-columns:repeat(auto-fill,minmax(38px,1fr));gap:4px}
  .inline-toc .num{height:38px;font-size:13px}
  .inline-toc .toc-item{min-height:40px}
  /* 抽屉里已有同一份目录，正文这份够用即可 */
  .inline-toc .toc-kids{display:none}
}
@media print{
  .sidebar,.bar,.progress,.scrim,.to-top,.pager,.cover-actions,.side-foot,
  .inline-toc,.verse-jump{display:none!important}
  .to-toc{display:none!important}
  .to-next{display:none!important}
  body{background:#fff;color:#000;font-size:11pt}
  main{max-width:none;padding:0}
  .chapter{page-break-inside:avoid;padding-top:1.5em}
  .answer,.card{background:#fff}
}
{{VERSE_CSS}}</style>
</head>
<body>
<div class="progress" id="progress"><span id="bar"></span></div>

<div class="layout">
  <aside class="sidebar" id="sidebar" aria-label="目录">
    <div class="side-head">
      <div class="tabs" role="tablist">
        <button class="tab active" data-tab="toc" role="tab" aria-selected="true">目录</button>
        <button class="tab" data-tab="num" role="tab" aria-selected="false">按问号</button>
        <button class="tab" data-tab="mark" role="tab" aria-selected="false">书签</button>
      </div>
      <button class="icon" id="btnClose" aria-label="关闭目录">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </button>
      <a class="icon close-link" href="#close" aria-label="关闭目录">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>
      </a>
    </div>
    <div class="search-wrap">
      <svg class="search-icon" viewBox="0 0 24 24" aria-hidden="true">
        <circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/></svg>
      <input class="search" id="search" type="search" placeholder="{{SEARCH_HINT}}" autocomplete="off">
    </div>
    <div class="search-results" id="searchResults" hidden aria-live="polite"></div>
    {{TOC}}
    {{NUMGRID}}
    <div class="marks" id="marks" hidden></div>
    <div class="side-foot">
      <span id="posText">—</span>
      <button id="btnMark">☆ 收藏本章</button>
      <button id="btnTop">回到顶部</button>
    </div>
  </aside>

  <div class="content">
    <header class="bar">
      <button class="icon" id="btnMenu" aria-label="打开目录" title="目录 (T)">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg>
      </button>
      <a class="icon menu-link" href="#sidebar" aria-label="打开目录">
        <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10"/></svg>
      </a>
      <div class="bar-title" id="barTitle"></div>
      <button class="icon" id="btnSize" aria-label="调整字号" title="字号（点击换档，长按选档）">
        <span class="icon-text">Aa</span>
      </button>
      <button class="icon" id="btnTheme" aria-label="切换主题" title="主题">
        <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8"/>
          <path d="M12 4a8 8 0 010 16z" fill="currentColor" stroke="none"/></svg>
      </button>
    </header>
    <div class="toast" id="toast" role="status" aria-live="polite"></div>
    <div class="size-panel" id="sizePanel" hidden aria-label="选择字号">
      <span class="size-panel-label">字号</span>
      <button type="button" class="size-opt" data-size="15">15</button>
      <button type="button" class="size-opt" data-size="17">17</button>
      <button type="button" class="size-opt" data-size="19">19</button>
      <button type="button" class="size-opt" data-size="21">21</button>
      <button type="button" class="size-opt" data-size="23">23</button>
      <button type="button" class="size-opt" data-size="25">25</button>
    </div>

    <main>
      {{INLINE_TOC}}
      <section class="cover">
        <div class="seal">問</div>
        <h1>{{TITLE}}</h1>
        {{TITLE_EN}}
        <div class="cover-meta">{{COVER_ROWS}}{{COVER_SOURCE}}</div>
        <div class="cover-stats">{{STATS}}</div>
        <div class="cover-actions">
          <a class="btn primary" href="#{{FIRST_ID}}" data-jump>开始阅读</a>
          <a class="btn" id="resumeBtn" href="#{{FIRST_ID}}" data-jump style="display:none">继续阅读</a>
        </div>
        <p class="cover-foot">离线单文件版 · 可直接用手机浏览器打开<br>{{FILENAME}}</p>
      </section>
      {{CHAPTERS}}
    </main>
  </div>
</div>

<div class="scrim" id="scrim"></div>

<a class="to-toc" id="btnToToc" href="#inline-toc" aria-label="回到目录">目录</a>
<a class="to-next" id="btnNextFloat" href="#" aria-label="下一章" hidden>下一章 ›</a>
<button class="to-top" id="btnTopFloat" aria-label="回到顶部">
  <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 19V5M6 11l6-6 6 6"/></svg>
</button>

<script>
(function () {
  var doc = document.documentElement;
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var THEMES = ['paper', 'plain', 'night'];
  /* 字号档位：从 15 到 25 px。上限比常见阅读器更宽一点 ——
     视力不佳的读者需要更大的字，「Aa 点三下才回到起点」也不该是唯一入口。 */
  var SIZES = [15, 17, 19, 21, 23, 25];
  var FONT_KEY = 'ow_book_theme', SIZE_KEY = 'ow_book_size', POS_KEY = 'ow_book_pos';
  var DESKTOP = '(min-width:1024px)';

  function $(id) { return document.getElementById(id); }
  // 脚本能跑：撤掉无脚本兜底的菜单按钮，改由 drawer 那套交互接管
  doc.classList.remove('nojs');
  doc.classList.add('js');
  function fail(what, e) {
    if (window.console && console.error) console.error(what, e);
    var t = $('barTitle');
    if (t) t.textContent = what + '出错';
  }
  // 任一模块出错都不影响其他模块：分段执行，异常就地捕获
  function safe(what, fn) { try { fn(); } catch (e) { fail(what, e); } }
  window.addEventListener('error', function (ev) {
    fail('脚本', ev.error || new Error(ev.message));
  });

  /* 触摸能力判定：'ontouchstart' 在部分桌面 Chromium（如 headless、安卓平板
     的桌面模式）上不暴露，maxTouchPoints 更可靠，两者取或。
     放在最前面：设置模块的长按监听要用到它。 */
  var HAS_TOUCH = ('ontouchstart' in window) || navigator.maxTouchPoints > 0;

  /* ---------- 主题与字号 ---------- */
  safe('设置', function () {
    // 用户没选过主题时跟随系统深色，选过则以用户为准
    var saved = store.get(FONT_KEY, '');
    var theme = saved ? THEMES.indexOf(saved) : -1;
    if (theme < 0) {
      var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
      theme = dark ? 2 : 0;
    }
    doc.setAttribute('data-theme', THEMES[theme]);
    var size = SIZES.indexOf(parseInt(store.get(SIZE_KEY, '17'), 10));
    if (size < 0) size = 2;
    doc.style.setProperty('--fs', SIZES[size] + 'px');

    /* 轻提示：点击后短暂显示当前档位，让「变了没有」有明确回执 */
    var toast = $('toast');
    var toastTimer = 0;
    function say(text) {
      if (!toast) return;
      toast.textContent = text;
      toast.classList.add('on');
      clearTimeout(toastTimer);
      toastTimer = setTimeout(function () { toast.classList.remove('on'); }, 1400);
    }

    $('btnTheme').addEventListener('click', function () {
      var i = THEMES.indexOf(doc.getAttribute('data-theme'));
      i = (i + 1) % THEMES.length;
      doc.setAttribute('data-theme', THEMES[i]);
      store.set(FONT_KEY, THEMES[i]);
      say({ paper: '纸色', plain: '素白', night: '夜间' }[THEMES[i]]);
    });

    /* 字号：点「Aa」依次换档并提示当前 px；长按或点开面板可直接选档 */
    function applySize(i) {
      i = Math.max(0, Math.min(SIZES.length - 1, i));
      doc.style.setProperty('--fs', SIZES[i] + 'px');
      store.set(SIZE_KEY, String(SIZES[i]));
      say('字号 ' + SIZES[i] + 'px');
      var panel = $('sizePanel');
      if (panel && !panel.hidden) {
        Array.prototype.forEach.call(panel.querySelectorAll('.size-opt'), function (b) {
          b.classList[Number(b.getAttribute('data-size')) === SIZES[i] ? 'add' : 'remove']('on');
        });
      }
    }
    $('btnSize').addEventListener('click', function (e) {
      if (e && e.shiftKey) return openSizePanel();
      var i = SIZES.indexOf(parseInt(doc.style.getPropertyValue('--fs'), 10));
      applySize((i + 1) % SIZES.length);
    });
    // 长按「Aa」直接开档位面板，省得连点四五次
    if (HAS_TOUCH) {
      var pressTimer = 0;
      var sizeBtn = $('btnSize');
      sizeBtn.addEventListener('touchstart', function () {
        clearTimeout(pressTimer);
        pressTimer = setTimeout(openSizePanel, 550);
      }, { passive: true });
      ['touchend', 'touchmove', 'touchcancel'].forEach(function (ev) {
        sizeBtn.addEventListener(ev, function () { clearTimeout(pressTimer); }, { passive: true });
      });
    }

    function openSizePanel() {
      var panel = $('sizePanel');
      if (!panel) return;
      panel.hidden = !panel.hidden;
      if (!panel.hidden) {
        Array.prototype.forEach.call(panel.querySelectorAll('.size-opt'), function (b) {
          b.classList[Number(b.getAttribute('data-size'))
            === parseInt(doc.style.getPropertyValue('--fs'), 10) ? 'add' : 'remove']('on');
        });
      }
    }
    var sizePanel = $('sizePanel');
    if (sizePanel) {
      Array.prototype.forEach.call(sizePanel.querySelectorAll('.size-opt'), function (b) {
        b.addEventListener('click', function (e) {
          if (e && e.preventDefault) e.preventDefault();
          applySize(SIZES.indexOf(Number(b.getAttribute('data-size'))));
          sizePanel.hidden = true;
        });
      });
      // 点面板与「Aa」之外的任何地方都收起，别让它一直盖在正文上
      document.addEventListener('click', function (e) {
        if (sizePanel.hidden) return;
        var t = e.target;
        if (t && (t.closest ? (t.closest('#sizePanel') || t.closest('#btnSize')) : false)) return;
        sizePanel.hidden = true;
      });
    }
    document.addEventListener('keydown', function (e) {
      if (e.target && e.target.tagName === 'INPUT') return;
      if (e.key === '+' || e.key === '=') applySize(SIZES.indexOf(parseInt(doc.style.getPropertyValue('--fs'), 10)) + 1);
      if (e.key === '-') applySize(SIZES.indexOf(parseInt(doc.style.getPropertyValue('--fs'), 10)) - 1);
    });
  });

  /* ---------- 目录侧栏、跳转、编号网格 ---------- */
  var sidebar, scrim, toc, numgrid, search, toTop, resumeBtn, mq;

  /* iOS 上只绑 click 会受 300ms 延迟与滚动取消影响：优先用触摸事件动作，
     触摸期间只要发生过位移就整段忽略（滚动结束不再当成点击） */
  /* 章数多的书（见 page() 里的 .cv）开了 content-visibility，
     章节位置会随渲染变化，滚动停下后必须重测。 */
  var HAS_CV = doc.classList.contains('cv');
  /* 经文类书（见 page() 里的 .verse）：有按节定位这套东西 */
  var VERSE = doc.classList.contains('verse');
  /* 节高亮的定时器：跳转框与搜索结果共用，连续点击时只保留最后一次 */
  var hitClear = 0;
  var TAP_SLOP = 10;
  var TOUCH_CLICK = false;
  function bindTap(node, action) {
    if (!node) return;
    if (!HAS_TOUCH) { node.addEventListener('click', action); return; }
    var x = 0, y = 0, moved = false;
    node.addEventListener('touchstart', function (e) {
      var t = e.changedTouches[0];
      x = t.clientX; y = t.clientY; moved = false;
      TOUCH_CLICK = false;
    }, { passive: true });
    node.addEventListener('touchmove', function (e) {
      var t = e.changedTouches[0];
      if (Math.abs(t.clientX - x) > TAP_SLOP || Math.abs(t.clientY - y) > TAP_SLOP) moved = true;
    }, { passive: true });
    node.addEventListener('touchend', function (e) {
      TOUCH_CLICK = true;
      if (moved) return;
      var t = e.changedTouches[0];
      if (Math.abs(t.clientX - x) > TAP_SLOP || Math.abs(t.clientY - y) > TAP_SLOP) return;
      action(e);
    });
    // 动作已经在 touchend 执行；这次合成 click 必须吃掉，否则一次点击触发两遍
    node.addEventListener('click', function (e) {
      if (TOUCH_CLICK) { e.preventDefault(); return; }
      action(e);
    });
  }
  // 触摸序列结束后（含滚动）Safari 才会补发合成 click，故在下一轮再清标记
  document.addEventListener('touchstart', function () { TOUCH_CLICK = false; }, { passive: true });

  /* iOS 不支持 fixed 元素内部的 overflow:hidden 锁滚动，用 body 定位锁 */
  var bodyLock = { on: false, y: 0, prev: '' };
  function lockBody(on) {
    if (on === bodyLock.on) return;
    bodyLock.on = on;
    if (on) {
      bodyLock.y = window.pageYOffset || 0;
      bodyLock.prev = document.body.style.cssText;
      document.body.style.position = 'fixed';
      document.body.style.top = -bodyLock.y + 'px';
      document.body.style.left = '0';
      document.body.style.right = '0';
      document.body.style.width = '100%';
    } else {
      var back = bodyLock.y;
      document.body.style.cssText = bodyLock.prev;
      if (back) window.scrollTo(0, back);
    }
  }
  function hideTop(on) {
    var t = $('btnTopFloat');
    if (t) t.classList[on ? 'remove' : 'add']('show');
  }
  /* 滚动锁把 body 变成 fixed，window.scrollY 会读成 0；
     阅读位置必须走这里，否则锁住期间章节定位会跳回第一章 */
  function scrollPos() {
    return bodyLock.on ? bodyLock.y : (window.pageYOffset || 0);
  }
  function scrollToY(top, smooth) {
    try {
      window.scrollTo({ top: top, behavior: smooth ? 'smooth' : 'auto' });
    } catch (e) {
      window.scrollTo(0, top);
    }
  }
  /* 跳转与经文深链都要用：放在模块作用域，别藏在某个 safe() 闭包里。

     content-visibility 让屏幕外章节的高度只是估算值，直接算落点会偏几百
     像素。做法：先给目标章节挂 .pin 让它真实排版，量准位置再跳，
     跳完摘掉 .pin —— 该章节已在视口内，浏览器会记住它的真实高度
     （contain-intrinsic-size:auto 就是干这个的）。 */
  function jumpTo(hash) {
    var id = decodeURIComponent(String(hash).replace(/^#/, ''));
    var el = document.getElementById(id);
    if (!el) return;
    var root = document.documentElement;
    var sec = el.closest ? el.closest('.chapter') : null;
    if (sec && root.classList.contains('cv')) {
      // 让目标章节退出按需渲染并强制整页重排，之后量到的才是真实位置
      sec.classList.add('pin');
      void document.body.offsetHeight;
    }
    var barH = document.querySelector('.bar').offsetHeight;
    var top = el.getBoundingClientRect().top + scrollPos() - barH - 18;
    scrollToY(Math.max(top, 0), false);
    if (sec) {
      /* 摘 pin 后这章退回按需渲染，占位高度与刚才不同会让落点偏移几百像素。
         把真实高度写进 contain-intrinsic-size 让它一致，再补一次校正兜底。 */
      sec.style.containIntrinsicSize = 'auto ' + sec.offsetHeight + 'px';
      window.requestAnimationFrame(function () {
        sec.classList.remove('pin');
        setTimeout(function () {
          var fix = el.getBoundingClientRect().top - barH - 18;
          if (Math.abs(fix) > 2) scrollToY(Math.max(scrollPos() + fix, 0), false);
        }, 80);
      });
    }
  }
  /* 键盘弹出时可视视口会变矮，抽屉高度跟着可视视口走 */
  function syncViewport() {
    if (!sidebar || !window.visualViewport) return;
    var vh = window.visualViewport.height;
    if (vh) sidebar.style.height = vh + 'px';
  }
  /* 关闭是幂等的，键盘快捷键与跳转都要用，放在模块作用域共享 */
  function isDesktop() { return !!(mq && mq.matches); }
  function closeSidebar() {
    if (!sidebar || isDesktop()) return;
    sidebar.classList.remove('on');
    scrim.classList.remove('on');
    lockBody(false);
    hideTop(false);
  }
  function toggleSidebar() {
    if (!sidebar || isDesktop()) return;
    if (sidebar.classList.contains('on')) closeSidebar(); else openSidebar(true);
  }
  function openSidebar(on) {
    if (!sidebar || isDesktop()) return;
    sidebar.classList[on ? 'add' : 'remove']('on');
    scrim.classList[on ? 'add' : 'remove']('on');
    lockBody(on);
    hideTop(on);
    if (on) { syncViewport(); revealCurrent(); }
  }
  function revealCurrent() {
    if (!toc) return;
    var cur = toc.querySelector('.toc-row.current, .toc-ch.current');
    if (!cur) return;
    var top = cur.offsetTop - toc.clientHeight / 2 + cur.offsetHeight / 2;
    if (top > 0) toc.scrollTop = top;
  }

  /* ---------- 圣经引用对照：点出处展开原文 ----------
     经文不预置在 DOM 里（1,640 处会多出上万节点），只以纯文本存在
     data-text 上；首次展开时才切成段落插入，收起时只隐藏、不重建。 */
  safe('引用', function () {
    var wrap = document.querySelector('main');
    if (!wrap || !document.querySelector('.refs')) return;

    function panelFor(box) {
      var body = box.nextElementSibling;
      if (body && body.classList && body.classList.contains('ref-body')) return body;
      var raw = box.getAttribute('data-text');
      if (!raw) return null;
      body = document.createElement('span');
      body.className = 'ref-body';
      var inner = document.createElement('span');
      inner.className = 'ref-text-wrap';
      raw.split('\n').forEach(function (line) {
        var tab = line.indexOf('\t');
        if (tab < 0) return;
        var row = document.createElement('span');
        row.className = 'ref-v';
        var num = document.createElement('b');
        num.textContent = line.slice(0, tab);
        row.appendChild(num);
        row.appendChild(document.createTextNode(line.slice(tab + 1)));
        var para = document.createElement('span');
        para.className = 'ref-text';
        para.appendChild(row);
        inner.appendChild(para);
      });
      body.appendChild(inner);
      box.parentNode.insertBefore(body, box.nextSibling);
      return body;
    }

    bindTap(wrap, function (e) {
      var node = (e && e.target) || null;
      while (node && node.nodeType !== 1) node = node.parentNode;
      if (!node || !node.closest) return;
      var tag = node.closest('.ref');
      if (!tag) return;
      var box = tag.parentNode;                    // .refs
      if (!box.classList.contains('refs')) return;
      // 同一处只保留一个展开面板
      Array.prototype.forEach.call(document.querySelectorAll('.refs.open'), function (o) {
        if (o !== box) o.classList.remove('open');
      });
      var body = panelFor(box);
      if (!body) return;
      box.classList.toggle('open');
    });
  });

  safe('导航', function () {
    sidebar = $('sidebar');
    scrim = $('scrim');
    toc = $('toc');
    numgrid = $('numgrid');
    search = $('search');
    toTop = $('btnTopFloat');
    resumeBtn = $('resumeBtn');
    mq = window.matchMedia(DESKTOP);

    /* 宽屏侧栏常驻（.on），窄屏必须收起来 —— 否则从宽屏缩窄窗口后，
       抽屉会一直盖住页面，而且遮罩没开，点哪儿都像卡住。 */
    function syncLayout() {
      if (isDesktop()) {
        sidebar.classList.add('on');
        scrim.classList.remove('on');
        sidebar.style.height = '';
        lockBody(false);
        hideTop(false);
      } else {
        sidebar.classList.remove('on');
        scrim.classList.remove('on');
        sidebar.style.height = '';
        lockBody(false);
      }
    }
    // 旧版 Safari 只有 addListener；这一步若抛错会连带后面全部失效，必须做回退
    if (mq.addEventListener) mq.addEventListener('change', syncLayout);
    else if (mq.addListener) mq.addListener(syncLayout);
    syncLayout();

    if (window.visualViewport) {
      window.visualViewport.addEventListener('resize', function () {
        if (sidebar.classList.contains('on') && !isDesktop()) syncViewport();
      });
    }

    /* 边缘手势：从屏幕左缘右滑拉出目录，抽屉内左滑关掉。
       只看横向位移且要求明显大于纵向（否则会跟纵向滚动抢手势），
       抽屉本身已设 touch-action:pan-y，纵向滚动照旧由浏览器处理。 */
    if (HAS_TOUCH) {
      var gx = 0, gy = 0, gOK = false;
      document.addEventListener('touchstart', function (e) {
        gOK = false;
        if (isDesktop()) return;
        var t = e.touches[0];
        var open = sidebar.classList.contains('on');
        // 关抽屉只认抽屉范围内的左滑；开抽屉只认屏幕左缘 24px 内的右滑
        if (open && sidebar.contains(e.target)) gOK = true;
        else if (!open && t.clientX <= 24) gOK = true;
        gx = t.clientX; gy = t.clientY;
      }, { passive: true });
      document.addEventListener('touchend', function (e) {
        if (!gOK) return;
        gOK = false;
        var t = e.changedTouches[0];
        var dx = t.clientX - gx, dy = t.clientY - gy;
        if (Math.abs(dx) < 60 || Math.abs(dx) < Math.abs(dy) * 1.5) return;
        if (dx > 0) openSidebar(true); else closeSidebar();
      }, { passive: true });
    }

    bindTap($('btnMenu'), toggleSidebar);
    /* 常驻入口（右下角）：
       · 普通书籍是「目录」—— 开抽屉并定位当前章，无脚本时是普通锚点
       · 经文类书是「查找」—— 开抽屉并聚焦搜索框，那里能直接输
         「约11:35 / 创1:1 / 诗篇 23」到任意一节，比翻回章首用跳转框快 */
    var toTocBtn = $('btnToToc');
    if (VERSE && toTocBtn) {
      toTocBtn.textContent = '查找';
      toTocBtn.setAttribute('aria-label', '查找经文');
    }
    bindTap(toTocBtn, function (e) {
      if (isDesktop()) return;
      if (e && e.preventDefault) e.preventDefault();
      openSidebar(true);
      // 聚焦搜索框并选中原内容，接着就能直接输入引用
      if (VERSE && search) {
        setTimeout(function () {
          search.focus();
          search.select();
        }, 320);
      }
    });
    bindTap($('btnClose'), function () { openSidebar(false); });
    bindTap(scrim, function () { openSidebar(false); });
    // 每章顶部的「目录」：窄屏开抽屉，宽屏回顶部（侧栏本来就常驻）
    Array.prototype.forEach.call(document.querySelectorAll('.toc-jump'), function (a) {
      bindTap(a, function (e) {
        if (e && e.preventDefault) e.preventDefault();
        if (isDesktop()) scrollToY(0, true); else openSidebar(true);
      });
    });

    var tabs = Array.prototype.slice.call(document.querySelectorAll('.tab'));
    var marksBox = $('marks');
    Array.prototype.forEach.call(tabs, function (tab) {
      bindTap(tab, function () {
        Array.prototype.forEach.call(tabs, function (t) {
          var on = t === tab;
          t.classList[on ? 'add' : 'remove']('active');
          t.setAttribute('aria-selected', on ? 'true' : 'false');
        });
        var kind = tab.getAttribute('data-tab');
        var isNum = kind === 'num', isMark = kind === 'mark';
        toc.hidden = isNum || isMark;
        numgrid.hidden = !isNum;
        if (marksBox) marksBox.hidden = !isMark;
        search.parentNode.style.display = (isNum || isMark) ? 'none' : '';
        if (isMark) renderMarks();
      });
    });

    /* ---------- 书签 ---------- */
    var MARKS_KEY = 'ow_book_marks';
    function getMarks() {
      try { var v = JSON.parse(store.get(MARKS_KEY, '[]')); return Array.isArray(v) ? v : []; }
      catch (e) { return []; }
    }
    function setMarks(list) { store.set(MARKS_KEY, JSON.stringify(list)); }
    function curChapter() {
      var id = store.get(POS_KEY, '');
      if (id && document.getElementById(id)) return document.getElementById(id);
      return document.querySelector('.chapter');
    }
    function syncMarkBtn() {
      var btn = $('btnMark'), ch = curChapter();
      if (!btn || !ch) return;
      var on = getMarks().indexOf(ch.id) >= 0;
      btn.textContent = on ? '\u2605 已收藏' : '\u2606 收藏本章';
      btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    }
    function renderMarks() {
      if (!marksBox) return;
      var list = getMarks(), parts = [];
      if (!list.length) {
        parts.push('<p class="marks-empty">还没有书签。\u9605读时点左下角「收藏本章」，' +
                   '\u4e0b次就能在这里一键回到。</p>');
      } else {
        list.forEach(function (id) {
          var ch = document.getElementById(id);
          if (!ch) return;
          parts.push('<div class="mark-row"><a class="toc-item" href="#' + id + '">'
                     + (ch.getAttribute('data-title') || id) + '</a>'
                     + '<button class="del" data-id="' + id + '" aria-label="删除书签">\u00d7</button></div>');
        });
      }
      marksBox.innerHTML = parts.join('');
      syncMarkBtn();
    }
    bindTap($('btnMark'), function () {
      var ch = curChapter();
      if (!ch) return;
      var list = getMarks(), i = list.indexOf(ch.id);
      if (i >= 0) list.splice(i, 1); else list.push(ch.id);
      setMarks(list);
      syncMarkBtn();
      if (marksBox && !marksBox.hidden) renderMarks();
    });
    if (marksBox) {
      bindTap(marksBox, function (e) {
        var node = (e && e.target) || null;
        while (node && node.nodeType !== 1) node = node.parentNode;
        if (!node || !node.closest) return;
        var del = node.closest('button.del');
        if (del) {
          if (e.preventDefault) e.preventDefault();
          var id = del.getAttribute('data-id');
          var list = getMarks().filter(function (x) { return x !== id; });
          setMarks(list); renderMarks();
          return;
        }
        var a = node.closest('a[href^="#"]');
        if (a) { handleJump(e); }
      });
    }
    syncMarkBtn();

    function handleJump(e) {
      var node = (e && e.target) || null;
      while (node && node.nodeType !== 1) node = node.parentNode;
      if (!node || !node.closest) return;
      var a = node.closest('a[href^="#"]');
      if (!a) return;
      if (e.preventDefault) e.preventDefault();
      // 必须先恢复 body 滚动再定位：解锁时会把页面移回原位，反过来会覆盖跳转结果
      openSidebar(false);
      var href = a.getAttribute('href');
      jumpTo(href);
      // 目录与编号网格的跳转改地址栏的 hash，章节链接才能直接分享
      var id = decodeURIComponent(String(href).replace(/^#/, ''));
      if (document.getElementById(id) && history.replaceState) {
        history.replaceState(null, '', '#' + id);
      }
      // 落到某一节时高亮那一节，否则从搜索结果跳过去只见页面移动、不知落在哪
      if (/^v\d+_/.test(id)) {
        var el = document.getElementById(id);
        var block = el && el.closest ? el.closest('.verse') : null;
        if (block) {
          block.classList.add('hit');
          clearTimeout(hitClear);
          hitClear = setTimeout(function () { block.classList.remove('hit'); }, 4000);
        }
      }
    }
    bindTap(toc, handleJump);
    bindTap(numgrid, handleJump);
    // 搜索结果里的每条也是 #锚点：点它同样要落到目标节，并收起抽屉
    var searchResults = $('searchResults');
    if (searchResults) bindTap(searchResults, handleJump);
    var coverActions = document.querySelector('.cover-actions');
    if (coverActions) bindTap(coverActions, handleJump);

    // 顶部进度条在手机上只有 3px 高，点不准还抢状态栏下拉手势：窄屏不接管点击
    var progress = $('progress');
    function backToTop() { openSidebar(false); scrollToY(0, true); }
    bindTap($('btnTop'), backToTop);
    bindTap(toTop, backToTop);
    if (!HAS_TOUCH) {
      bindTap(progress, function (e) {
        var r = progress.getBoundingClientRect();
        var ratio = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
        var max = document.documentElement.scrollHeight - window.innerHeight;
        scrollToY(ratio * max, false);
      });
    }

    // 阅读位置只在封面给入口，而封面在最顶上：直接跳到某章再回来就再也见不到。
    // 章节之间停住时给一条悬浮的「继续上次」，点了回上次停的位置，几秒后自己退场。
    var saved = store.get(POS_KEY, '');
    if (saved) {
      var savedEl = document.getElementById(saved);
      if (savedEl && resumeBtn) {
        resumeBtn.style.display = '';
        resumeBtn.textContent = '继续阅读：' + (savedEl.getAttribute('data-title') || '');
        resumeBtn.setAttribute('href', '#' + saved);
      }
    }
  });

  /* ---------- 键盘快捷键：上下章、关抽屉 ---------- */
  safe('快捷键', function () {
    function sections() { return Array.prototype.slice.call(document.querySelectorAll('.chapter')); }
    function current() {
      var list = sections(), top = scrollPos() + 72, found = list[0];
      for (var i = 0; i < list.length; i++) {
        if (list[i].offsetTop <= top) found = list[i]; else break;
      }
      return found;
    }
    document.addEventListener('keydown', function (e) {
      if (e.target && e.target.tagName === 'INPUT') return;
      if (e.key === 'Escape') closeSidebar();
      // 顶栏菜单按钮 title 一直写着「目录 (T)」，这里补上真实按键
      if (e.key === 't' || e.key === 'T') { e.preventDefault(); toggleSidebar(); return; }
      if (e.key === '[' || e.key === ']') {
        var list = sections(), i = list.indexOf(current());
        var next = e.key === '[' ? list[i - 1] : list[i + 1];
        if (next) {
          e.preventDefault();
          var barH = document.querySelector('.bar').offsetHeight;
          var top = next.getBoundingClientRect().top + scrollPos() - barH - 14;
          scrollToY(top, true);
        }
      }
    });
  });

  /* ---------- 搜索与滚动联动 ---------- */
  safe('索引', function () {
    var rows = Array.prototype.slice.call(toc.querySelectorAll('.toc-row'));
    var groups = Array.prototype.slice.call(toc.querySelectorAll('.toc-group'));
    var parts = Array.prototype.slice.call(toc.querySelectorAll('.toc-part'));
    var sections = Array.prototype.slice.call(document.querySelectorAll('.chapter'));
    var heads = Array.prototype.slice.call(document.querySelectorAll('.chapter-body h2[id]'));
    var bar = $('bar');
    var barTitle = $('barTitle');
    var posText = $('posText');
    var nextBtn = $('btnNextFloat');
    var lastId = null, lastHead = null, ticking = false;
    // 经文类书把自己的全文检索挂在这里；普通书籍走下面的 buildTextIndex
    var verseSearch = null;
    {{VERSE_JS}}

    /* 正文全文索引：惰性构建，只建一次。
       每章只存「小节锚点 + 该小节起的纯文本」，不重复存 DOM 节点；
       50 万字的书索引约 50 万字符的字符串量，能接受，但不该在首屏付这笔钱。 */
    var textIndex = null;
    function buildTextIndex() {
      if (textIndex) return textIndex;
      textIndex = [];
      sections.forEach(function (sec) {
        var title = sec.getAttribute('data-title') || '';
        var body = sec.querySelector('.chapter-body');
        if (!body) return;
        // 按 h2 切段：每段记住自己的锚点，命中时直接跳过去
        var anchor = sec.id, buf = [];
        var flush = function () {
          var text = buf.join(' ').replace(/\s+/g, ' ').trim();
          if (text) {
            textIndex.push({ id: anchor, ch: sec.id, title: title, text: text, lower: text.toLowerCase() });
          }
          buf = [];
        };
        Array.prototype.forEach.call(body.children, function (node) {
          if (node.tagName === 'H2') {
            flush();
            if (node.id) anchor = node.id;
            buf.push(node.textContent);
            return;
          }
          var t = node.textContent;
          if (t) buf.push(t);
        });
        flush();
      });
      return textIndex;
    }

    function renderTextSearch(q, results) {
      var MAX = 60;
      if (!q) {
        results.hidden = true;
        results.innerHTML = '';
        toc.hidden = false;
        return 0;
      }
      var index = buildTextIndex();
      var hits = [];
      for (var i = 0; i < index.length && hits.length < MAX; i++) {
        var at = index[i].lower.indexOf(q);
        if (at < 0) continue;
        hits.push({ id: index[i].id, ref: index[i].title, text: index[i].text, at: at });
      }
      if (!hits.length) {
        results.hidden = true;
        results.innerHTML = '';
        return 0;
      }
      var parts = ['<p class="sr-head">' + (hits.length >= MAX
        ? '只列前 ' + MAX + ' 处命中' : hits.length + ' 处命中') + '</p>'];
      hits.forEach(function (hit) {
        // 命中位置前后各留一点上下文，比从头截断更能看出命中在哪
        var from = Math.max(0, hit.at - 24);
        var snip = (from > 0 ? '…' : '') + hit.text.slice(from, hit.at + q.length + 40) + '…';
        parts.push('<a class="sr-hit" href="#' + hit.id + '">'
          + '<span class="sr-ref">' + escapeHtml(hit.ref) + '</span>'
          + '<span class="sr-text">' + markMatch(snip, q) + '</span></a>');
      });
      results.innerHTML = parts.join('');
      results.hidden = false;
      toc.hidden = true;
      return hits.length;
    }

    function escapeHtml(text) {
      return String(text).replace(/[&<>]/g, function (c) {
        return {'&': '&amp;', '<': '&lt;', '>': '&gt;'}[c];
      });
    }

    /* 命中词高亮：先转义再按小写定位，切片用原文长度，避免转义后的
       实体（&amp; 等）把位置算错。经文检索共用这一份。 */
    function markMatch(text, q) {
      var esc = escapeHtml(text);
      var at = String(text).toLowerCase().indexOf(q);
      if (at < 0) return esc;
      // 转义只可能让字符串更长，用原文切片再分别转义更稳妥
      return escapeHtml(text.slice(0, at)) + '<mark>' + escapeHtml(text.slice(at, at + q.length))
        + '</mark>' + escapeHtml(text.slice(at + q.length));
    }

    function renderSearch(q) {
      q = q.trim().toLowerCase();
      var results = $('searchResults');
      if (verseSearch && results) { verseSearch(q, results); return; }
      // 先在目录标题里找；一个都没有时再扫正文（避免每次都读 50 万字）
      var hit = 0;
      rows.forEach(function (row) {
        var item = row.querySelector('.toc-item');
        var kids = Array.prototype.slice.call(row.querySelectorAll('.toc-sub'));
        var titleHit = !!q && item.textContent.toLowerCase().indexOf(q) >= 0;
        var kidHit = 0;
        kids.forEach(function (kid) {
          var on = !!q && kid.textContent.toLowerCase().indexOf(q) >= 0;
          kid.style.display = on ? '' : 'none';
          if (on) kidHit++;
        });
        var show = q ? (titleHit || kidHit) : true;
        row.style.display = show ? '' : 'none';
        if (show && q) hit++;
        var box = row.querySelector('.toc-kids');
        if (box) box.style.display = (q && kidHit) ? '' : (row.classList.contains('current') ? '' : 'none');
      });
      groups.forEach(function (g) {
        var any = Array.prototype.some.call(g.querySelectorAll('.toc-row'), function (r) {
          return r.style.display !== 'none';
        });
        g.style.display = any ? '' : 'none';
        var cat = g.querySelector('.toc-cat');
        if (cat) {
          var anyCat = Array.prototype.some.call(g.querySelectorAll('.toc-item'), function (i) {
            return i.closest('.toc-row').style.display !== 'none';
          });
          cat.style.display = anyCat ? '' : 'none';
        }
      });
      parts.forEach(function (p) {
        var any = false;
        var sib = p.nextElementSibling;
        while (sib && !sib.classList.contains('toc-part')) {
          if (sib.classList.contains('toc-group') && sib.style.display !== 'none') any = true;
          sib = sib.nextElementSibling;
        }
        p.style.display = any ? '' : 'none';
      });
      // 目录没命中时才扫正文；目录有命中就够用了，不必再花时间读 50 万字。
      // 正文命中仍然切成结果面板，两者不同时铺开，避免一次搜索出现两套列表。
      var textHit = 0;
      if (q && !hit) {
        var results = $('searchResults');
        if (results) textHit = renderTextSearch(q, results);
        if (textHit) return;
      }
      var empty = toc.querySelector('.toc-empty');
      if (q && !hit) {
        if (!empty) {
          empty = document.createElement('p');
          empty.className = 'toc-empty';
          toc.appendChild(empty);
        }
        empty.textContent = '没有找到「' + q + '」';
        empty.style.display = '';
      } else if (empty) {
        empty.style.display = 'none';
      }
    }
    // 输入防抖：50 万字的正文扫描不该每次按键都跑一遍
    var searchTimer = 0;
    search.addEventListener('input', function () {
      var value = this.value;
      clearTimeout(searchTimer);
      searchTimer = setTimeout(function () { renderSearch(value); }, 120);
    });
    search.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') {
        clearTimeout(searchTimer);
        this.value = '';
        renderSearch('');
      }
    });

    function markCurrent(id) {
      rows.forEach(function (row) {
        var on = row.getAttribute('data-target') === id;
        row.classList[on ? 'add' : 'remove']('current');
        var box = row.querySelector('.toc-kids');
        if (box) box.style.display = on ? '' : 'none';
      });
      Array.prototype.forEach.call(document.querySelectorAll('.num'), function (n) {
        n.classList[n.getAttribute('data-target') === id ? 'add' : 'remove']('current');
      });
    }
    function markHead(el) {
      Array.prototype.forEach.call(document.querySelectorAll('.toc-sub'), function (s) {
        var on = el && s.getAttribute('href') === '#' + el.id;
        s.classList[on ? 'add' : 'remove']('current');
      });
    }

    /* 滚动联动的性能关键：章节与小节的位置只量一次，之后滚动只做二分查找。
       原先每帧都读 offsetTop —— 500K 字的文档一次强制回流要十几毫秒，
       再叠加同帧内的 DOM 写入，手机上滑动静止帧率就掉下去了。

       例外：章数多的书启用了 content-visibility，屏幕外章节的高度只是估算，
       滚动经过时会逐段变成真实高度，缓存随之失效。这里在滚动停止后
       重测一次（滚动进行中不测，避免卡顿），再校正当前章。 */
    var secTop = [], headTop = [], measuredAt = 0, remeasureTimer = 0;
    function measure() {
      secTop = sections.map(function (el) { return el.offsetTop; });
      headTop = heads.map(function (el) { return el.offsetTop; });
      measuredAt = Date.now();
      posText.setAttribute('data-chars',
        Math.max(1, (document.querySelector('main') || document.body).textContent.length));
    }
    // 最后一项满足 top <= y 的下标；都不满足返回 -1
    function lastAt(list, y) {
      var lo = 0, hi = list.length - 1, ans = -1;
      while (lo <= hi) {
        var mid = (lo + hi) >> 1;
        if (list[mid] <= y) { ans = mid; lo = mid + 1; } else { hi = mid - 1; }
      }
      return ans;
    }
    /* 悬浮「下一章」：章末 pager 的手机替代品。目标直接取该章自带的
       pager，不另存一份映射；最后一章没有下一篇就隐藏，不留死按钮。 */
    var shownNext = '';
    function syncNext(sec) {
      if (!nextBtn) return;
      var link = sec.querySelector('.pager a.next');
      if (!link) {
        if (shownNext) { shownNext = ''; nextBtn.hidden = true; }
        return;
      }
      var href = link.getAttribute('href');
      if (href === shownNext) return;
      shownNext = href;
      nextBtn.setAttribute('href', href);
      // pager 里除标题外还有「下一篇」小字，这里把它去掉当提示文案
      nextBtn.setAttribute('title',
        link.textContent.replace(/^\s*下一篇\s*/, '').trim());
      nextBtn.removeAttribute('hidden');
    }

    // 上一次写进 DOM 的值：值没变就不碰，避免无谓的样式与重排
    var shownTitle = '', shownPos = '', posAt = 0;
    function onScroll() {
      if (ticking) return;
      ticking = true;
      window.requestAnimationFrame(function () {
        ticking = false;
        var y = scrollPos();
        var max = document.documentElement.scrollHeight - window.innerHeight;
        var ratio = max > 0 ? Math.min(1, Math.max(0, y / max)) : 0;
        var pct = Math.round(ratio * 100);

        bar.style.width = (ratio * 100) + '%';
        toTop.classList[y > 600 ? 'add' : 'remove']('show');

        var si = lastAt(secTop, y + 72);
        var sec = sections[si >= 0 ? si : 0];
        if (!sec) return;
        var title = sec.getAttribute('data-title') || '';
        if (sec.id !== lastId) {
          lastId = sec.id;
          markCurrent(sec.id);
          store.set(POS_KEY, sec.id);
          syncNext(sec);
        }
        var titleText = pct + '% · ' + title;
        if (titleText !== shownTitle) { shownTitle = titleText; barTitle.textContent = titleText; }

        // 进度条在抽屉底部，滚动时根本看不见：每半秒才刷新一次就够
        var now = Date.now();
        if (now - posAt > 500) {
          posAt = now;
          var chars = Number(posText.getAttribute('data-chars')) || 1;
          var pos = pct + '% · ' + (si + 1) + '/' + sections.length
            + (ratio < 0.999 ? ' · 剩约 ' + Math.round((1 - ratio) * chars / 400) + ' 分钟' : ' · 读完了');
          if (pos !== shownPos) { shownPos = pos; posText.textContent = pos; }
        }

        var hi = lastAt(headTop, y + 96);
        var head = hi >= 0 ? heads[hi] : null;
        var hid = head ? head.id : null;
        if (hid !== lastHead) { lastHead = hid; markHead(head); }

        // content-visibility：滚动停下 300ms 后重测一次，让缓存跟上
        // 逐段渲染出来的真实高度；不重测的话越往后章节标题越对不上。
        if (HAS_CV) {
          clearTimeout(remeasureTimer);
          remeasureTimer = setTimeout(function () {
            measure();
            onScroll();
          }, 300);
        }
      });
    }
{{VERSE_JS_END}}

    window.addEventListener('scroll', onScroll, { passive: true });
    window.addEventListener('resize', function () { measure(); onScroll(); });
    measure();
    onScroll();
  });
})();
</script>
</body>
</html>
"""


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    bookkit.book_dir(args[0] if args else None)
    manifest = json.load(open('manifest.json', encoding='utf-8'))
    meta = {k: v for k, v in manifest.items() if k in
            ('book', 'title_en', 'author', 'translator', 'publisher_en', 'source')}
    chapters = manifest['chapters']
    verse_mode = bool(manifest.get('site', {}).get('verses'))

    # 圣经引用对照：manifest 里声明 scripture 段时启用（见 lib/scripture.py）
    global SCRIPTURE
    SCRIPTURE = scripture.load(manifest)
    if SCRIPTURE:
        print(f'经文对照：{SCRIPTURE.source.dir}')

    anchors = {f"{ch['slug']}.md": 'ch-' + ch['slug'] for ch in chapters}

    parts, headings = [], {}
    verse_counts = {}
    questions = 0
    cv_chars = cv_chapters = 0
    for idx, ch in enumerate(chapters):
        path = f"{ch['slug']}.md"
        if not os.path.exists(path):
            raise SystemExit(f'缺少章节文件: {path}')
        md = open(path, encoding='utf-8').read()
        # 整章只解析一次：编号、小节锚点与正文都从这一份 blocks 出发，
        # 去掉空标题后再编号，目录与小节锚点因此不会错位
        blocks = drop_empty_headings(parse_markdown(md))

        cid = 'ch-' + ch['slug']
        if verse_mode:
            total = 0
            for b in blocks:
                if b['type'] != 'p':
                    continue
                v = VERSE_LINE_RE.match(b['text'].strip())
                if v:
                    total += int(v.group(2) or v.group(1)) - int(v.group(1)) + 1
            verse_counts[cid] = total

        prev_html = next_html = ''
        if idx > 0:
            p = chapters[idx - 1]
            prev_html = (f'<a class="prev" href="#ch-{p["slug"]}"><span>上一篇</span>'
                         f'{html.escape(p["title"], quote=False)}</a>')
        if idx < len(chapters) - 1:
            n = chapters[idx + 1]
            next_html = (f'<a class="next" href="#ch-{n["slug"]}"><span>下一篇</span>'
                         f'{html.escape(n["title"], quote=False)}</a>')
        pager = f'<nav class="pager">{prev_html}{next_html}</nav>' if (prev_html or next_html) else ''

        cid = 'ch-' + ch['slug']
        # 小节锚点与正文的 h2 顺序一一对应，先算出再传给渲染器做「本章要点」
        heads = [{'id': f'{cid}-s{n}', 't': b['text']}
                 for n, b in enumerate((x for x in blocks if x['type'] == 'h2'), 1)]
        headings[cid] = heads

        nav_top = ['<nav class="chapter-nav" aria-label="章节导航">']
        if idx > 0:
            nav_top.append('<a class="prev" href="#ch-%s">‹ 上一章</a>' % chapters[idx - 1]['slug'])
        nav_top.append('<a class="toc-jump" href="#inline-toc">目录</a>')
        if idx < len(chapters) - 1:
            nav_top.append('<a class="next" href="#ch-%s">下一章 ›</a>' % chapters[idx + 1]['slug'])
        nav_top.append('</nav>')
        summary = ''
        if len(heads) >= 2:
            links = ''.join('<a href="#%s">%s</a>' % (h['id'], html.escape(h['t'], quote=False))
                            for h in heads)
            summary = ('<nav class="chapter-sum" aria-label="本章要点">'
                       '<span class="sum-label">本章要点</span>' + links + '</nav>')

        rendered, _ = render_chapter(ch, md, anchors, pager, ''.join(nav_top), summary,
                                     verse_mode, 'v%d' % (idx + 1), blocks)
        if '问' in ch['title']:
            questions += 1
        parts.append(rendered)
        # 平均章高：只用来给 content-visibility 的占位估算一个接近的值，
        # 按「每章标题 + 正文文本量」粗算即可（真实高度由浏览器渲染后接管）
        cv_chars += len(md)
        cv_chapters += 1

    head_count = sum(len(v) for v in headings.values())
    stats = '<span><b>%d</b>章</span>' % len(chapters)
    if questions:
        stats += '<span><b>%d</b>问</span>' % questions
    if head_count:
        stats += '<span><b>%d</b>节解读</span>' % head_count
    filename = (manifest.get('docx', {}).get('filename') or meta['book']).replace('.docx', '') + '.html'
    has_numbers = any(chapter_number(ch['title']) is not None for ch in chapters)
    numgrid_inline = (build_numgrid(chapters, 'class="numgrid" id="numgrid-inline"')
                      if has_numbers else '')
    # 经文类书（圣经）的卷-章目录本身就有 150 KB 以上，正文里再存一份副本
    # 纯粹是重复：它的窄屏抽屉本来就能用 CSS :target 打开，不依赖这份兜底。
    # 但 #inline-toc 这个锚点被章首「目录」与右下角按钮引用，留一个空占位，
    # 无脚本时按它仍能跳回目录位置（有脚本时这些入口改开抽屉）。
    inline_toc = '<span id="inline-toc"></span>' if verse_mode else (
        '<section class="inline-toc" id="inline-toc" aria-label="目录">'
        '<p class="inline-toc-head">目录 <span>%s</span></p>'
        % ('点标题或问号即可跳转' if has_numbers else '点卷名展开章号')
        + numgrid_inline + build_toc_html(chapters, headings, 'class="toc toc-copy"', verse_counts)
        + '</section>')
    # 平均章高估算：正文每 1,000 字符约 2,400px（17px/1.95 行高、手机宽度），
    # 加上章首标题与上下留白约 500px。只影响滚动条长度的初值。
    cv_height = 0
    if cv_chapters:
        cv_height = int(min(6000, max(800, cv_chars / cv_chapters / 1000 * 2400 + 500)))
    out = page(meta, '\n'.join(parts),
               build_toc_html(chapters, headings, verse_counts=verse_counts),
               build_numgrid(chapters) if has_numbers else '',
               stats, filename,
               'ch-' + chapters[0]['slug'], inline_toc,
               search_hint='搜索经文或卷章' if verse_mode else '搜索问答或解读标题',
               verse_mode=verse_mode, cv_height=cv_height)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'saved {filename}  chapters={len(chapters)}  size={os.path.getsize(filename) // 1024}KB')
    if SCRIPTURE:
        note = SCRIPTURE.report()
        if note:
            print('  ' + note)
    return 0


if __name__ == '__main__':
    sys.exit(main())
