#!/usr/bin/env python3
"""把章节 Markdown 打包成 EPUB 3（Apple Books / iBooks 可直接打开）。

用法:
  python3 lib/build_epub.py <书名目录> [-o 输出文件名]

与 build_html.py 共用同一套 Markdown 解析与行内渲染，保证两种产物的排版语义一致。
EPUB 里每章一个 XHTML，附 nav.xhtml（EPUB3 目录）与 toc.ncx（EPUB2 兼容），
章节间的跳转会改写成跨文件链接，读起来可以正常跳来跳去。
"""
import html
import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit
from build_html import parse_markdown, render_body, split_question

MODIFIED = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

STYLE = """/* 阅读样式：跟随 Apple Books 的 paged 模式，尽量少指定、把排版交还系统 */
body{font-family:serif;line-height:1.85;margin:0 1em;color:#211d18;-webkit-hyphens:auto}
h1.chapter-title{font-size:1.35em;line-height:1.5;margin:.6em 0 1.2em;font-weight:700}
.qmark{display:block;margin:1.4em 0 .2em;color:#9c4a22;font-weight:700}
.qmark-n{font-size:1.9em;margin-right:.15em}
.qmark-w{font-size:.8em;letter-spacing:.3em}
h2{font-size:1.08em;line-height:1.6;margin:1.8em 0 .7em;font-weight:700}
h2 .idx{display:inline-block;margin-right:.5em;padding:.1em .6em;border:1px solid #c2814f;
  border-radius:1em;font-size:.62em;letter-spacing:.1em;color:#9c4a22}
p{margin:0 0 .9em;text-indent:2em;text-align:justify}
.answer{margin:0 0 1.2em;padding:.8em 1em;background:#faf6ec;border:1px solid #e3d9c5;border-radius:8px}
.answer-tag{display:inline-block;margin-bottom:.4em;padding:.05em .45em;background:#9c4a22;
  color:#fffdf8;border-radius:4px;font-size:.72em;font-weight:700}
.answer-text p{text-indent:0;margin:0 0 .5em}
.en{margin:0 0 1.2em;padding:.6em .9em;background:#f7f3e9;border-top:1px solid #e3d9c5;
  border-bottom:1px solid #e3d9c5}
.en-row{display:block;margin:.35em 0;color:#5b5347;font-size:.92em;line-height:1.7}
.en-tag{display:inline-block;width:1.4em;height:1.4em;margin-right:.5em;border-radius:50%;
  background:#f0e6d4;color:#9c4a22;font-size:.72em;text-align:center;line-height:1.4em;font-weight:700}
blockquote{margin:0 0 1em;padding:.6em 1em;color:#6d6353;border-top:1px solid #e3d9c5;
  border-bottom:1px solid #e3d9c5}
ul,ol{margin:0 0 1em;padding-left:1.6em}
li{margin:.3em 0}
a{color:#9c4a22;text-decoration:none}
hr{border:none;border-top:1px solid #e3d9c5;margin:1.6em 0}
.nav{font-size:.8em;color:#6d6353;margin:1.2em 0}
.nav a{color:#9c4a22}
"""

VOID_FIX = [
    (re.compile(r'<img\b([^>]*?)\s*/?>'), r'<img\1/>'),
    (re.compile(r'<hr\b([^>]*?)\s*/?>'), r'<hr\1/>'),
    (re.compile(r'<br\b([^>]*?)\s*/?>'), r'<br\1/>'),
    (re.compile(r'<audio\b.*?</audio>', re.S), ''),
]


def xhtml_escape(text):
    return html.escape(text, quote=False)


def chapter_filename(slug):
    return 'c-' + slug + '.xhtml'


def sanitize(fragment):
    """把 HTML 片段收拾成 XHTML 片段（自闭合空元素、去掉 EPUB 用不到的播放器）。"""
    for pattern, repl in VOID_FIX:
        fragment = pattern.sub(repl, fragment)
    return fragment


def rewrite_links(fragment, cur_slug, cid_files):
    """把 #ch-xxx 的跨章锚点改写成跨文件链接。"""
    for cid, fname in cid_files.items():
        slug = cid[3:]
        if slug == cur_slug:
            continue
        fragment = fragment.replace(f'href="#{cid}-s', f'href="{fname}#{cid}-s')
        fragment = fragment.replace(f'href="#{cid}"', f'href="{fname}#{cid}"')
    return fragment


def make_xhtml(title, body, css_href='style.css'):
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE html>\n'
            '<html xmlns="http://www.w3.org/1999/xhtml" '
            'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="zh-CN" lang="zh-CN">\n'
            '<head>\n<meta charset="utf-8"/>\n'
            f'<title>{xhtml_escape(title)}</title>\n'
            f'<link rel="stylesheet" type="text/css" href="{css_href}"/>\n'
            '</head>\n<body>\n' + body + '\n</body>\n</html>\n')


def build_nav(manifest, chapters, cid_files):
    """EPUB3 导航文档：按 part → category → 章节 分三层，用栈保证标签闭合顺序。"""
    out = ['<nav epub:type="toc" id="toc">', '<h1>目录</h1>']
    stack = []          # 当前打开的结构：'ol' 或 'li'
    cur_part, cur_cat = None, None

    def close_to(level):
        """关到只剩 level 层结构（0=根 ol 之外）。"""
        nonlocal stack
        while len(stack) > level:
            top = stack.pop()
            out.append('</li>' if top == 'li' else '</ol>')

    for ch in chapters:
        part = ch.get('part') or ''
        cat = ch.get('category') or ''
        fname = chapter_filename(ch['slug'])
        title = xhtml_escape(ch['title'])
        if part != cur_part:
            close_to(0)
            out.append('<ol>')
            stack = ['ol']
            if part:
                out.append(f'<li><span>{xhtml_escape(part)}</span>')
                stack.append('li')
                out.append('<ol>')
                stack.append('ol')
            cur_part, cur_cat = part, None
        if cat != cur_cat:
            # 关到「part 的 ol」这一层（有 part 时是 3 层，没有则 1 层）
            base = 3 if cur_part else 1
            close_to(base)
            if cat:
                out.append(f'<li><span>{xhtml_escape(cat)}</span>')
                stack.append('li')
                out.append('<ol>')
                stack.append('ol')
            cur_cat = cat
        out.append(f'<li><a href="{fname}">{title}</a></li>')
    close_to(0)
    out.append('</nav>')
    return '\n'.join(out)


def build_ncx(manifest, chapters):
    """EPUB2 目录（Apple Books 新版不需要，老设备会读这个）。"""
    book = xhtml_escape(manifest.get('book', 'Book'))
    points, n = [], 0

    def add(title, src):
        nonlocal n
        n += 1
        points.append(
            f'<navPoint id="np{n}" playOrder="{n}">'
            f'<navLabel><text>{xhtml_escape(title)}</text></navLabel>'
            f'<content src="{src}"/></navPoint>')

    for ch in chapters:
        add(ch['title'], chapter_filename(ch['slug']))
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1" xml:lang="zh-CN">\n'
            f'<head><meta name="dtb:uid" content="{book}"/></head>\n'
            f'<docTitle><text>{book}</text></docTitle>\n'
            f'<navMap>{"".join(points)}</navMap>\n'
            '</ncx>\n')


def build_opf(manifest, chapters, cid_files, book_id):
    book = xhtml_escape(manifest.get('book', 'Book'))
    items = ['<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
             '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
             '<item id="css" href="style.css" media-type="text/css"/>',
             '<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>']
    spine = ['<itemref idref="cover"/>']
    for i, ch in enumerate(chapters):
        iid = f'ch{i:04d}'
        items.append(f'<item id="{iid}" href="{chapter_filename(ch["slug"])}" '
                     'media-type="application/xhtml+xml"/>')
        spine.append(f'<itemref idref="{iid}"/>')
    meta = [f'<dc:identifier id="bookid">{book_id}</dc:identifier>',
            f'<dc:title>{book}</dc:title>',
            '<dc:language>zh-CN</dc:language>',
            '<dc:creator>' + xhtml_escape(manifest.get('author') or '佚名') + '</dc:creator>']
    if manifest.get('translator'):
        meta.append('<dc:contributor>' + xhtml_escape(manifest['translator']) + '</dc:contributor>')
    if manifest.get('source'):
        meta.append('<dc:source>' + xhtml_escape(manifest['source']) + '</dc:source>')
    return ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
            'unique-identifier="bookid" xml:lang="zh-CN">\n'
            '<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            + '\n'.join(meta) + '\n'
            f'<meta property="dcterms:modified">{MODIFIED}</meta>\n'
            '</metadata>\n<manifest>\n' + '\n'.join(items) + '\n</manifest>\n'
            '<spine toc="ncx">\n' + '\n'.join(spine) + '\n</spine>\n</package>\n')


def build_cover(manifest, chapters):
    book = xhtml_escape(manifest.get('book', 'Book'))
    rows = []
    for key, label in (('author', '作者 / 解读'), ('translator', '翻译'),
                       ('publisher_en', '英文版')):
        if manifest.get(key):
            rows.append(f'<p class="nav">{label}：{xhtml_escape(manifest[key])}</p>')
    body = ('<div class="qmark"><span class="qmark-w">問</span></div>'
            f'<h1 class="chapter-title">{book}</h1>'
            + (f'<p class="nav">{xhtml_escape(manifest["title_en"])}</p>'
               if manifest.get('title_en') else '')
            + ''.join(rows)
            + '<p class="nav"><a href="' + chapter_filename(chapters[0]['slug'])
            + '">开始阅读</a></p>')
    return make_xhtml(manifest.get('book', 'Book'), body)


def build_chapter_xhtml(ch, md, cid_files, chapters):
    blocks = [b for b in parse_markdown(md) if b['type'] != 'h1']
    title = ch['title']
    category = ch.get('category') or ''
    if not category:
        for b in blocks:
            if b['type'] == 'quote':
                category = b['text']
                break
    if blocks and blocks[0]['type'] == 'quote' and blocks[0]['text'] == category:
        blocks = blocks[1:]
    cid = 'ch-' + ch['slug']
    anchors = {f'{c["slug"]}.md': 'ch-' + c['slug'] for c in chapters}
    content, _ = render_body(blocks, anchors, cid)
    content = rewrite_links(content, ch['slug'], cid_files)
    content = sanitize(content)

    qnum, qtext = split_question(title)
    if qnum:
        head = (f'<p class="qmark"><span class="qmark-n">{int(qnum):02d}</span>'
                '<span class="qmark-w">问</span></p>'
                f'<h1 class="chapter-title">{xhtml_escape(qtext)}</h1>')
    else:
        head = f'<h1 class="chapter-title">{xhtml_escape(title)}</h1>'
    kicker = f'<p class="nav">{xhtml_escape(category)}</p>' if category else ''
    body = f'<section epub:type="chapter" id="{cid}">\n{kicker}\n{head}\n{content}\n</section>'
    return make_xhtml(title, body)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('-')]
    bookkit.book_dir(args[0] if args else None)
    manifest = json.load(open('manifest.json', encoding='utf-8'))
    chapters = manifest['chapters']

    out_name = (manifest.get('docx', {}).get('filename') or manifest.get('book', 'book'))
    out_name = os.path.splitext(out_name)[0] + '.epub'

    cid_files = {'ch-' + ch['slug']: chapter_filename(ch['slug']) for ch in chapters}
    book_id = 'urn:uuid:' + str(uuid.uuid5(uuid.NAMESPACE_URL,
                                          manifest.get('book', 'book') + '|epub'))

    parts = []
    for ch in chapters:
        path = f"{ch['slug']}.md"
        if not os.path.exists(path):
            raise SystemExit(f'缺少章节文件: {path}')
        with open(path, encoding='utf-8') as f:
            md = f.read()
        parts.append((chapter_filename(ch['slug']),
                      build_chapter_xhtml(ch, md, cid_files, chapters)))

    container = ('<?xml version="1.0" encoding="utf-8"?>\n'
                 '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
                 '<rootfiles><rootfile full-path="OEBPS/content.opf" '
                 'media-type="application/oebps-package+xml"/></rootfiles>\n</container>\n')

    with zipfile.ZipFile(out_name, 'w') as zf:
        # mimetype 必须是第一个条目且不压缩
        info = zipfile.ZipInfo('mimetype')
        info.compress_type = zipfile.ZIP_STORED
        zf.writestr(info, 'application/epub+zip')
        zf.writestr('META-INF/container.xml', container)
        zf.writestr('OEBPS/content.opf', build_opf(manifest, chapters, cid_files, book_id),
                    compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/nav.xhtml', make_xhtml('目录', build_nav(manifest, chapters, cid_files)),
                    compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/toc.ncx', build_ncx(manifest, chapters),
                    compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/style.css', STYLE, compress_type=zipfile.ZIP_DEFLATED)
        zf.writestr('OEBPS/cover.xhtml', build_cover(manifest, chapters),
                    compress_type=zipfile.ZIP_DEFLATED)
        for fname, content in parts:
            zf.writestr('OEBPS/' + fname, content, compress_type=zipfile.ZIP_DEFLATED)

    print(f'saved {out_name}  chapters={len(chapters)}  size={os.path.getsize(out_name) // 1024}KB')
    return 0


if __name__ == '__main__':
    sys.exit(main())
