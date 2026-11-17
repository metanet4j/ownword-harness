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
                pieces.append(html.escape(seg[pos:m.start()], quote=False))
            if m.group('img'):
                src = html.escape(m.group('src'), quote=True)
                alt = html.escape(m.group('alt'), quote=False)
                pieces.append(f'<img src="{src}" alt="{alt}" loading="lazy">')
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
            pieces.append(html.escape(seg[pos:], quote=False))
        chunk = ''.join(pieces)
        out.append(f'<strong>{chunk}</strong>' if bold else chunk)
    return ''.join(out)


def render_block(block, anchors, hid=None):
    kind = block['type']
    if kind == 'p':
        text = block['text'].lstrip('　')
        inner = render_inline(text, anchors)
        cls = '' if block.get('indent') else ' class="no-indent"'
        return f'<p{cls}>{inner}</p>'
    if kind in ('h2', 'h3', 'h4', 'h5', 'h6'):
        level = min(int(kind[1]), 4)
        attr = f' id="{hid}"' if hid else ''
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


def render_body(blocks, anchors, cid=None):
    """渲染章节正文，并把「答」「中英文问答」整理成独立块。"""
    out = []
    sec = 0
    i = 0
    while i < len(blocks):
        block = blocks[i]
        kind = block['type']
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
                out.append(f'<div class="answer">{render_inline(text, anchors)}</div>')
                i += 1
                while i < len(blocks) and blocks[i]['type'] in ('ul', 'ol'):
                    out.append(render_block(blocks[i], anchors))
                    i += 1
                continue
        out.append(render_block(block, anchors))
        i += 1
    return '\n'.join(out), sec


def render_chapter(ch, md, anchors, pager=''):
    """渲染一章：标题 + 正文 + 章末导航 + 小节锚点。"""
    blocks = parse_markdown(md)
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
    content, sec = render_body(body, anchors, cid)
    kicker = f'<p class="kicker">{html.escape(category, quote=False)}</p>' if category else ''
    parts = [
        f'<section class="chapter" id="{cid}" data-title="{html.escape(title, quote=True)}">',
        '<header class="chapter-head">',
        kicker,
        f'<h1 class="chapter-title">{html.escape(title, quote=False)}</h1>',
        '</header>',
        '<div class="chapter-body">',
        content,
        '</div>',
        pager,
        '</section>',
    ]
    return '\n'.join(parts), sec


# ---------------------------------------------------------------- 页面组装

def build_toc_html(chapters):
    """目录（抽屉）用静态 HTML 输出，保证无脚本也能看到章节目录。"""
    parts = ['<nav class="toc" id="toc">']
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
                parts.append(f'<div class="toc-cat">{html.escape(cat, quote=False)}</div>')
            cur_cat = cat
        cid = 'ch-' + ch['slug']
        parts.append(f'<a class="toc-item" href="#{cid}" data-target="{cid}">'
                     f'{html.escape(ch["title"], quote=False)}</a>')
    if cur_part is not None:
        parts.append('</div>')
    parts.append('</nav>')
    return '\n'.join(parts)


def build_index(chapters, headings):
    """搜索索引：章节 + 各章小节标题。"""
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


def page(meta, chapters_html, toc_html, index_json, stats, filename, first_id):
    title = meta.get('book', '')
    cover_rows = [
        ('作者 / 解读', meta.get('author')),
        ('翻译', meta.get('translator')),
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
    page_html = page_html.replace('{{TITLE}}', html.escape(title, quote=False))
    page_html = page_html.replace('{{TITLE_EN}}', title_en)
    page_html = page_html.replace('{{COVER_ROWS}}', rows)
    page_html = page_html.replace('{{COVER_SOURCE}}', source_html)
    page_html = page_html.replace('{{STATS}}', stats)
    page_html = page_html.replace('{{TOC}}', toc_html)
    page_html = page_html.replace('{{CHAPTERS}}', chapters_html)
    page_html = page_html.replace('{{INDEX}}', index_json)
    page_html = page_html.replace('{{FIRST_ID}}', first_id)
    page_html = page_html.replace('{{FILENAME}}', html.escape(filename, quote=False))
    return page_html


TEMPLATE = r"""<!doctype html>
<html lang="zh-CN" data-theme="sepia">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="format-detection" content="telephone=no">
<meta name="theme-color" content="#f3ead9">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<title>{{TITLE}}</title>
<style>
:root{
  --fs:17px; --lh:1.92;
  --bg:#f2e9d8; --surface:#faf4e8; --surface2:#fffdf7; --text:#2c2721; --muted:#7c7160;
  --line:#e0d3ba; --accent:#9a5b2c; --accent-weak:rgba(154,91,44,.10); --shadow:rgba(60,40,20,.16);
  --sans:-apple-system,BlinkMacSystemFont,"PingFang SC","Hiragino Sans GB","Microsoft YaHei","Noto Sans CJK SC","Source Han Sans SC","Segoe UI",sans-serif;
  --serif:"Songti SC","Source Han Serif SC","Noto Serif CJK SC","Noto Serif SC","SimSun","STSong",Georgia,"Times New Roman",serif;
}
html[data-theme="plain"]{--bg:#ffffff;--surface:#f6f6f4;--surface2:#ffffff;--text:#1f1f1e;--muted:#6b6b68;--line:#e5e5e1;--accent:#2f5d8a;--accent-weak:rgba(47,93,138,.09);--shadow:rgba(0,0,0,.10)}
html[data-theme="night"]{--bg:#14161a;--surface:#1b1e24;--surface2:#21252c;--text:#d6d2ca;--muted:#8e8a82;--line:#2d323a;--accent:#d6a26a;--accent-weak:rgba(214,162,106,.13);--shadow:rgba(0,0,0,.45)}
*,*::before,*::after{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--bg);color:var(--text);font-family:var(--serif);font-size:var(--fs);line-height:var(--lh);-webkit-font-smoothing:antialiased;overflow-wrap:break-word}
a{color:var(--accent)}
img{max-width:100%;height:auto;border-radius:8px;display:block;margin:1.2em auto}
hr{border:none;border-top:1px solid var(--line);margin:1.8em 0}

/* 顶栏 */
.progress{position:fixed;top:0;left:0;right:0;height:3px;z-index:70;pointer-events:none}
.progress span{display:block;height:100%;width:0;background:var(--accent);transition:width .12s linear}
.bar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:4px;
  height:calc(52px + env(safe-area-inset-top));padding:env(safe-area-inset-top) 6px 0;
  background:var(--bg);background:color-mix(in srgb,var(--bg) 88%,transparent);
  -webkit-backdrop-filter:saturate(180%) blur(14px);backdrop-filter:saturate(180%) blur(14px);
  border-bottom:1px solid var(--line)}
.bar-title{flex:1;min-width:0;text-align:center;font-family:var(--sans);font-size:15px;font-weight:600;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;color:var(--text)}
.icon{flex:none;width:40px;height:40px;border:0;background:transparent;color:var(--muted);
  font-size:17px;border-radius:10px;cursor:pointer;font-family:var(--sans);line-height:1}
.icon:active{background:var(--accent-weak)}
html[data-theme="night"] .icon{color:#cfc9bf}

/* 抽屉 */
.scrim{position:fixed;inset:0;background:rgba(20,15,8,.42);z-index:45;opacity:0;pointer-events:none;transition:opacity .25s}
.scrim.on{opacity:1;pointer-events:auto}
.drawer{position:fixed;top:0;left:0;bottom:0;width:min(86vw,380px);z-index:50;display:flex;flex-direction:column;
  background:var(--surface);border-right:1px solid var(--line);transform:translateX(-102%);
  transition:transform .28s cubic-bezier(.32,.72,0,1);box-shadow:0 0 0 transparent}
.drawer.on{transform:none;box-shadow:0 0 48px var(--shadow)}
.drawer-head{display:flex;align-items:center;justify-content:space-between;gap:8px;
  padding:calc(10px + env(safe-area-inset-top)) 10px 6px 16px;border-bottom:1px solid var(--line)}
.drawer-head strong{font-family:var(--sans);font-size:16px}
.search{width:calc(100% - 24px);margin:10px 12px;padding:9px 12px;border-radius:10px;border:1px solid var(--line);
  background:var(--surface2);color:var(--text);font-family:var(--sans);font-size:15px}
.search:focus{outline:none;border-color:var(--accent)}
.toc{flex:1;overflow-y:auto;overscroll-behavior:contain;padding:0 10px calc(28px + env(safe-area-inset-bottom)) 12px;-webkit-overflow-scrolling:touch}
.toc-part{margin:16px 0 4px;font-family:var(--sans);font-size:12.5px;font-weight:700;letter-spacing:.08em;
  color:var(--accent);text-transform:none}
.toc-cat{margin:10px 0 2px;padding-left:6px;font-family:var(--sans);font-size:13px;color:var(--muted)}
.toc-item{display:block;padding:8px 10px;border-radius:9px;font-family:var(--sans);font-size:14.5px;line-height:1.45;
  color:var(--text);text-decoration:none}
.toc-item:active{background:var(--accent-weak)}
.toc-item.current{background:var(--accent-weak);color:var(--accent);font-weight:600}
.toc-sub{display:block;padding:6px 10px 6px 22px;font-family:var(--sans);font-size:13px;color:var(--muted);text-decoration:none}
.toc-empty{padding:24px 12px;font-family:var(--sans);font-size:14px;color:var(--muted)}

/* 封面 */
.cover{min-height:calc(100svh - 52px);display:flex;flex-direction:column;justify-content:center;align-items:center;
  text-align:center;padding:56px 26px calc(48px + env(safe-area-inset-bottom));gap:0}
.cover-mark{width:52px;height:52px;border-radius:14px;background:var(--accent);color:#fff;display:flex;align-items:center;
  justify-content:center;font-family:var(--sans);font-size:22px;font-weight:700;margin-bottom:26px}
.cover h1{font-family:var(--sans);font-size:1.62em;line-height:1.4;font-weight:700;margin:0 0 8px;letter-spacing:.01em}
.cover-en{font-family:var(--serif);font-size:.92em;color:var(--muted);margin:0 0 26px;letter-spacing:.02em}
.cover-meta{margin:0 0 26px;padding:20px 0;border-top:1px solid var(--line);border-bottom:1px solid var(--line);max-width:34em}
.cover-row{margin:0 0 8px;font-family:var(--sans);font-size:14px;line-height:1.6;display:flex;gap:10px;text-align:left}
.cover-key{flex:none;width:5.6em;color:var(--muted);font-size:13px}
.cover-val{flex:1;color:var(--text)}
.cover-source{font-family:var(--sans);font-size:12px;color:var(--muted);margin:14px 0 0;word-break:break-all}
.cover-source a{color:var(--muted)}
.cover-stats{display:flex;gap:10px;margin:0 0 30px;font-family:var(--sans);font-size:13px;color:var(--muted)}
.cover-stats b{color:var(--accent);font-size:1.25em;font-weight:700;margin-right:4px}
.cover-actions{display:flex;flex-direction:column;gap:10px;width:min(100%,320px)}
.btn{display:block;padding:13px 20px;border-radius:12px;border:1px solid var(--line);background:var(--surface2);
  color:var(--text);font-family:var(--sans);font-size:15px;font-weight:600;text-decoration:none;text-align:center;cursor:pointer}
.btn.primary{background:var(--accent);border-color:var(--accent);color:#fff}
.cover-foot{margin-top:34px;font-family:var(--sans);font-size:12px;color:var(--muted);line-height:1.8}

/* 正文 */
main{max-width:44em;margin:0 auto;padding:0 20px calc(96px + env(safe-area-inset-bottom))}
.chapter{padding:34px 0 8px;scroll-margin-top:60px}
.chapter-head{margin-bottom:20px}
.kicker{margin:0 0 8px;font-family:var(--sans);font-size:12.5px;font-weight:700;letter-spacing:.1em;color:var(--accent)}
.chapter-title{margin:0;font-family:var(--sans);font-size:1.34em;line-height:1.42;font-weight:700;letter-spacing:.01em}
.chapter-body p{margin:0 0 .9em;text-indent:2em;text-align:justify}
.chapter-body p.no-indent{text-indent:0}
.chapter-body h2{position:relative;margin:1.9em 0 .8em;padding-left:.72em;font-family:var(--sans);font-size:1.02em;
  font-weight:700;line-height:1.5;scroll-margin-top:64px}
.chapter-body h2::before{content:"";position:absolute;left:0;top:.28em;bottom:.28em;width:3px;border-radius:2px;background:var(--accent)}
.chapter-body h3{font-family:var(--sans);font-size:.98em;font-weight:700;margin:1.4em 0 .6em}
.chapter-body h4{font-family:var(--sans);font-size:.94em;font-weight:700;margin:1.2em 0 .5em}
.chapter-body ul,.chapter-body ol{margin:0 0 1em;padding-left:1.55em}
.chapter-body li{margin:.34em 0}
.chapter-body ul ul{list-style:circle;margin:.3em 0}
.chapter-body ul ul ul{list-style:square}
.chapter-body li>p{margin:.3em 0}
.chapter-body blockquote{margin:0 0 1em;padding:.1em 0 .1em .95em;border-left:3px solid var(--line);color:var(--muted)}
.answer{margin:0 0 1.1em;padding:.85em 1em;background:var(--accent-weak);border-left:3px solid var(--accent);
  border-radius:0 10px 10px 0;line-height:1.85}
.en{margin:0 0 1.2em;padding:.2em 0 .2em .9em;border-left:2px solid var(--line);color:var(--muted);font-size:.92em;line-height:1.7}
.en-row{display:flex;gap:.6em;margin:.35em 0}
.en-tag{flex:none;width:1.5em;height:1.5em;border-radius:5px;background:var(--accent-weak);color:var(--accent);
  font-family:var(--sans);font-size:.72em;font-weight:700;display:flex;align-items:center;justify-content:center;margin-top:.28em}
.audio{display:flex;align-items:center;gap:.7em;margin:0 0 1em;padding:.6em .8em;background:var(--surface2);
  border:1px solid var(--line);border-radius:10px}
.audio-label{flex:none;font-family:var(--sans);font-size:12px;color:var(--muted)}
.audio audio{flex:1;min-width:0;height:34px}
.jump{color:var(--accent);text-decoration:none;border-bottom:1px solid var(--accent-weak)}

/* 章末导航 */
.pager{display:flex;gap:10px;margin:2.6em 0 0;padding-top:1.4em;border-top:1px solid var(--line)}
.pager a{flex:1;min-width:0;padding:.72em .85em;border:1px solid var(--line);border-radius:11px;background:var(--surface2);
  text-decoration:none;font-family:var(--sans);font-size:13px;line-height:1.4;color:var(--text)}
.pager a span{display:block;color:var(--muted);font-size:11.5px;margin-bottom:3px}
.pager a.next{text-align:right}
.pager a:active{border-color:var(--accent)}
@media (max-width:420px){.pager a{font-size:12.5px;padding:.65em .7em}}

@media (min-width:860px){
  body{font-size:calc(var(--fs) + 1px)}
  .drawer{width:340px}
  main{padding:0 28px 120px}
  .chapter{padding-top:46px}
}
</style>
</head>
<body>
<div class="progress"><span id="bar"></span></div>

<header class="bar">
  <button class="icon" id="btnMenu" aria-label="目录" title="目录">☰</button>
  <div class="bar-title" id="barTitle"></div>
  <button class="icon" id="btnSize" aria-label="字号" title="字号">Aa</button>
  <button class="icon" id="btnTheme" aria-label="主题" title="主题">◐</button>
</header>

<div class="scrim" id="scrim"></div>
<aside class="drawer" id="drawer" aria-label="目录">
  <div class="drawer-head">
    <strong>目录</strong>
    <button class="icon" id="btnClose" aria-label="关闭">✕</button>
  </div>
  <input class="search" id="search" type="search" placeholder="搜索问答或解读标题" autocomplete="off">
  {{TOC}}
</aside>

<main>
  <section class="cover">
    <div class="cover-mark">問</div>
    <h1>{{TITLE}}</h1>
    {{TITLE_EN}}
    <div class="cover-meta">{{COVER_ROWS}}{{COVER_SOURCE}}</div>
    <div class="cover-stats">{{STATS}}</div>
    <div class="cover-actions">
      <a class="btn primary" href="#{{FIRST_ID}}">开始阅读</a>
      <a class="btn" id="resumeBtn" href="#{{FIRST_ID}}" style="display:none">继续阅读</a>
    </div>
    <p class="cover-foot">离线单文件版 · 可直接用手机浏览器打开<br>{{FILENAME}}</p>
  </section>
  {{CHAPTERS}}
</main>

<script>window.__INDEX__ = {{INDEX}};</script>
<script>
(function () {
  var doc = document.documentElement;
  var store = {
    get: function (k, d) { try { var v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };
  var THEMES = ['sepia', 'plain', 'night'];
  var SIZES = [15, 17, 19, 21];
  var FONT_KEY = 'ow_book_theme', SIZE_KEY = 'ow_book_size', POS_KEY = 'ow_book_pos';

  function applyTheme(t) {
    doc.setAttribute('data-theme', t);
    var btn = document.getElementById('btnTheme');
    if (btn) btn.textContent = t === 'night' ? '☾' : (t === 'plain' ? '☀' : '◐');
  }
  function applySize(i) {
    doc.style.setProperty('--fs', SIZES[i] + 'px');
  }
  var theme = THEMES.indexOf(store.get(FONT_KEY, 'sepia'));
  if (theme < 0) theme = 0;
  applyTheme(THEMES[theme]);
  var size = SIZES.indexOf(parseInt(store.get(SIZE_KEY, '17'), 10));
  if (size < 0) size = 1;
  applySize(size);

  document.getElementById('btnTheme').addEventListener('click', function () {
    theme = (theme + 1) % THEMES.length;
    applyTheme(THEMES[theme]);
    store.set(FONT_KEY, THEMES[theme]);
  });
  document.getElementById('btnSize').addEventListener('click', function () {
    size = (size + 1) % SIZES.length;
    applySize(size);
    store.set(SIZE_KEY, String(SIZES[size]));
  });

  var drawer = document.getElementById('drawer');
  var scrim = document.getElementById('scrim');
  function openDrawer(on) {
    drawer.classList.toggle('on', on);
    scrim.classList.toggle('on', on);
    document.body.style.overflow = on ? 'hidden' : '';
  }
  document.getElementById('btnMenu').addEventListener('click', function () { openDrawer(!drawer.classList.contains('on')); });
  document.getElementById('btnClose').addEventListener('click', function () { openDrawer(false); });
  scrim.addEventListener('click', function () { openDrawer(false); });

  var INDEX = window.__INDEX__ || [];
  var toc = document.getElementById('toc');
  var tocItems = Array.prototype.slice.call(toc.querySelectorAll('.toc-item'));
  var search = document.getElementById('search');
  var query = '';

  function markCurrent(id) {
    tocItems.forEach(function (a) { a.classList.toggle('current', a.getAttribute('data-target') === id); });
  }

  function renderSearch(q) {
    query = q.trim();
    if (!query) {
      tocItems.forEach(function (a) { a.style.display = ''; });
      toc.querySelectorAll('.toc-sub').forEach(function (n) { n.remove(); });
      toc.querySelectorAll('.toc-empty').forEach(function (n) { n.remove(); });
      toc.querySelectorAll('.toc-part,.toc-cat').forEach(function (n) { n.style.display = ''; });
      return;
    }
    var lower = q.toLowerCase();
    toc.querySelectorAll('.toc-sub').forEach(function (n) { n.remove(); });
    toc.querySelectorAll('.toc-empty').forEach(function (n) { n.remove(); });
    var hits = 0;
    INDEX.forEach(function (ch) {
      var item = toc.querySelector('.toc-item[data-target="' + ch.id + '"]');
      if (!item) return;
      var titleHit = ch.t.toLowerCase().indexOf(lower) >= 0;
      var heads = ch.heads.filter(function (h) { return h.t.toLowerCase().indexOf(lower) >= 0; });
      var show = titleHit || heads.length;
      item.style.display = show ? '' : 'none';
      if (show) hits++;
      heads.forEach(function (h) {
        var a = document.createElement('a');
        a.className = 'toc-sub';
        a.href = '#' + h.id;
        a.textContent = h.t;
        item.parentNode.insertBefore(a, item.nextSibling);
      });
    });
    toc.querySelectorAll('.toc-part,.toc-cat').forEach(function (n) { n.style.display = 'none'; });
    if (!hits) {
      var empty = document.createElement('p');
      empty.className = 'toc-empty';
      empty.textContent = '没有找到「' + q + '」';
      toc.appendChild(empty);
    }
  }
  search.addEventListener('input', function () { renderSearch(this.value); });
  toc.addEventListener('click', function (e) {
    if (e.target.closest('a')) openDrawer(false);
  });

  var sections = Array.prototype.slice.call(document.querySelectorAll('.chapter'));
  var bar = document.getElementById('bar');
  var barTitle = document.getElementById('barTitle');
  var resumeBtn = document.getElementById('resumeBtn');
  var lastId = null, ticking = false;

  function currentSection() {
    var top = window.scrollY + 70;
    var found = sections[0];
    for (var i = 0; i < sections.length; i++) {
      if (sections[i].offsetTop <= top) found = sections[i]; else break;
    }
    return found;
  }
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      var h = document.documentElement.scrollHeight - window.innerHeight;
      bar.style.width = (h > 0 ? Math.min(100, window.scrollY / h * 100) : 0) + '%';
      var sec = currentSection();
      if (sec && sec.id !== lastId) {
        lastId = sec.id;
        barTitle.textContent = sec.getAttribute('data-title') || '';
        markCurrent(sec.id);
        store.set(POS_KEY, sec.id);
      }
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
  window.addEventListener('resize', onScroll);

  var saved = store.get(POS_KEY, '');
  if (saved) {
    var target = document.getElementById(saved);
    if (target) {
      resumeBtn.style.display = '';
      resumeBtn.textContent = '继续阅读：' + (target.getAttribute('data-title') || '');
      resumeBtn.setAttribute('href', '#' + saved);
    }
  }

  document.addEventListener('keydown', function (e) {
    if (e.target.tagName === 'INPUT') return;
    if (e.key === 'Escape') openDrawer(false);
    if (e.key === '[' || e.key === ']') {
      var sec = currentSection(), i = sections.indexOf(sec), next = null;
      if (e.key === '[') next = sections[i - 1]; else next = sections[i + 1];
      if (next) {
        e.preventDefault();
        next.scrollIntoView({ behavior: 'smooth' });
      }
    }
  });

  onScroll();
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

    anchors = {f"{ch['slug']}.md": 'ch-' + ch['slug'] for ch in chapters}

    parts, headings = [], {}
    questions = 0
    for idx, ch in enumerate(chapters):
        path = f"{ch['slug']}.md"
        if not os.path.exists(path):
            raise SystemExit(f'缺少章节文件: {path}')
        md = open(path, encoding='utf-8').read()

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

        rendered, _ = render_chapter(ch, md, anchors, pager)
        cid = 'ch-' + ch['slug']
        heads = []
        for b in parse_markdown(md):
            if b['type'] == 'h2':
                heads.append({'id': f'{cid}-s{len(heads) + 1}', 't': b['text']})
        headings[cid] = heads
        if '问' in ch['title']:
            questions += 1
        parts.append(rendered)

    stats = ('<span><b>%d</b>章</span><span><b>%d</b>问</span><span><b>%d</b>节解读</span>'
             % (len(chapters), questions, sum(len(v) for v in headings.values())))
    filename = (manifest.get('docx', {}).get('filename') or meta['book']).replace('.docx', '') + '.html'
    out = page(meta, '\n'.join(parts), build_toc_html(chapters),
               build_index(chapters, headings), stats, filename, 'ch-' + chapters[0]['slug'])
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(out)
    print(f'saved {filename}  chapters={len(chapters)}  size={os.path.getsize(filename) // 1024}KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
