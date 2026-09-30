#!/usr/bin/env python3
"""核对抓取产物：网页段落是否都进了 Markdown 与 Word，目录链接是否有效。

用法:
  python3 lib/verify_book.py <书名目录>
"""
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.getcwd(), 'pylibs'))
from bs4 import BeautifulSoup  # noqa: E402
from docx import Document  # noqa: E402


def chapter_paragraphs(d, mf, ch, soup_cache):
    """取出该章在源页面里的段落文本（去空白，仅保留有实质内容的段落）。"""
    inline = mf.get('inline')
    if inline:
        key = inline['file']
        if key not in soup_cache:
            soup_cache[key] = BeautifulSoup(
                open(f"{d}/raw/{key}", encoding='utf-8').read(), 'lxml')
        node = soup_cache[key].select_one(ch[inline.get('selector_field', 'selector')])
        if node is None:
            return None
        c = node.select_one(inline['body_selector'])
    else:
        path = f"{d}/raw/{ch['slug']}.html"
        if not os.path.exists(path):
            return None
        c = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml').select_one('div.entry-content')
    if c is None:
        return None
    for t in c.select('audio,script,style'):
        t.decompose()
    out = []
    for p in c.find_all('p'):
        txt = re.sub(r'\s+', '', p.get_text())
        if len(txt) > 30:
            out.append(txt)
    return out


def main():
    d = sys.argv[1]
    mf = json.load(open(f'{d}/manifest.json', encoding='utf-8'))
    doc = Document(f'{d}/' + (mf['docx'].get('filename') or f"{mf['book']}.docx"))
    alltext = ''.join(p.text for p in doc.paragraphs)
    dn = re.sub(r'\s+', '', alltext)

    soup_cache, bad, no_src = {}, [], []
    for ch in mf['chapters']:
        ps = chapter_paragraphs(d, mf, ch, soup_cache)
        if ps is None:
            no_src.append(ch['slug'])
            continue
        md = open(f"{d}/{ch['slug']}.md", encoding='utf-8').read()
        md = re.sub(r'^#+.*$', '', md, flags=re.M)      # 标题行
        md = re.sub(r'^[ \t]*>[ \t]?', '', md, flags=re.M)   # 引用行去掉标记，保留内容
        mdn = re.sub(r'\s+', '', md.replace('**', '').replace('\\*', '*'))
        dn_cmp = dn.replace('*', '')      # Word 里保留源文的字面星号，比对时忽略
        miss_docx = [p[:30] for p in ps if p.replace('*', '') not in dn_cmp]
        miss_md = [p[:30] for p in ps if p.replace('*', '') not in mdn.replace('*', '')]
        if miss_docx or miss_md:
            bad.append((ch['slug'], len(miss_md), len(miss_docx), (miss_md or miss_docx)[0]))

    print('docx 段落:', len(doc.paragraphs), '| 字符:', len(dn), '| 星号:', alltext.count('*'))
    print('逐章核对:', bad if bad else '无缺失（Markdown 与 Word 全部命中）')
    if no_src:
        print('缺源文件的章节:', no_src)
    links = re.findall(r'\]\((.+?\.md)\)', open(f'{d}/目录.md', encoding='utf-8').read())
    print('目录链接:', len(links), '| 失效:', [l for l in links if not os.path.exists(f'{d}/{l}')] or '无')
    print('分章文件:',
          len([f for f in glob.glob(f'{d}/*.md') if os.path.basename(f) not in ('目录.md', 'README.md')]),
          '篇 + 目录.md')
    return 0


if __name__ == '__main__':
    sys.exit(main())
