#!/usr/bin/env python3
"""统计各分类页覆盖的问答编号，用于确认目录是否完整。

用法:
  python3 lib/scan_questions.py <书名目录>
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit

bookkit.use_pylibs()

from bs4 import BeautifulSoup  # noqa: E402


def main():
    bookkit.book_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    mf = bookkit.load_manifest()
    site = mf.get('site', {})
    sel = site.get('content_selector', 'div.entry-content')

    rows, covered = [], []
    for ch in mf['chapters']:
        path = f"raw/{ch['slug']}.html"
        if not os.path.exists(path):
            rows.append((ch['slug'], None))
            continue
        soup = BeautifulSoup(open(path, encoding='utf-8').read(), 'lxml')
        content = soup.select_one(sel)
        text = html.unescape(content.get_text(' ')) if content else ''
        nums = [int(n) for n in re.findall(r'(\d+)\s*问\s*[：:]', text)]
        rows.append((ch['slug'], nums))
        covered.extend(nums)

    seen, dup = set(), []
    for n in covered:
        if n in seen:
            dup.append(n)
        seen.add(n)

    missing = [n for n in range(1, max(covered or [0]) + 1) if n not in seen]
    print(f'页面数: {len(rows)} | 覆盖问答: {len(seen)} 个，编号 {min(seen, default=0)}-{max(seen, default=0)}')
    print(f'重复出现的编号: {sorted(set(dup)) or "无"}')
    print(f'区间内缺口: {missing or "无"}')
    multi = [(slug, nums) for slug, nums in rows if nums and len(nums) > 1]
    print(f'含多问的页面: {len(multi)}')
    for slug, nums in multi[:10]:
        print(f'  {slug}: {nums}')
    empty = [slug for slug, nums in rows if nums == []]
    if empty:
        print(f'未识别到问答编号的页面: {empty}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
