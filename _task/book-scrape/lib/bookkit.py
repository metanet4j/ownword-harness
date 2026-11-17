#!/usr/bin/env python3
"""跨书共用的工具：目录定位、清单与配置加载、粗体解析。"""
import json
import os
import re
import sys

LIB = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(LIB)

DEFAULT_DOCX = {
    'body_cn': '宋体',
    'head_cn': '黑体',
    'body_en': 'Times New Roman',
    'head_en': 'Arial',
    'body_size': 12,
    'line_spacing': 1.5,
    'page': 'A4',
    'margin_cm': [2.5, 2.8],
    'page_number': True,
}


def use_pylibs():
    """把随仓库携带的依赖目录加入 sys.path。"""
    path = os.path.join(ROOT, 'pylibs')
    if os.path.isdir(path) and path not in sys.path:
        sys.path.insert(0, path)


def book_dir(arg):
    """解析书名目录，并把工作目录切到那里。"""
    if not arg and len(sys.argv) > 1:
        arg = sys.argv[1]
    if not arg:
        names = [d for d in sorted(os.listdir(ROOT))
                 if os.path.isdir(os.path.join(ROOT, d)) and d != 'pylibs' and not d.startswith('.')]
        raise SystemExit('用法: python3 %s <书名目录>\n可选目录: %s'
                         % (os.path.basename(sys.argv[0]), '、'.join(names) or '（无）'))
    path = arg if os.path.isabs(arg) else os.path.join(ROOT, arg)
    if not os.path.isdir(path):
        raise SystemExit(f'目录不存在: {path}')
    os.chdir(path)
    return path


def load_manifest():
    mf = json.load(open('manifest.json', encoding='utf-8'))
    for key in ('book', 'chapters'):
        if key not in mf:
            raise SystemExit(f'manifest.json 缺少字段: {key}')
    mf.setdefault('docx', {})
    mf['docx'] = {**DEFAULT_DOCX, **mf['docx']}
    return mf


BOLD_RE = re.compile(r'(?<!\\)\*\*(.+?)(?<!\\)\*\*', re.S)


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
