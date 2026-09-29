#!/usr/bin/env python3
"""抓取一本书的所有章节 HTML 到 <书名目录>/raw/。

用法:
  python3 lib/fetch_html.py <书名目录> [--start N] [--limit N]

说明：站点会对浏览器 User-Agent 的自动请求返回 403/429，隐藏 UA 反而稳定返回
200；脚本因此不发送 UA，并在每页之间等待 18-26 秒。
"""
import json
import os
import random
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bookkit


def curl(url, out):
    cmd = ['curl', '-sSL', '--compressed', '--max-time', '90',
           '-o', out, '-w', '%{http_code}', url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip()


def fetch(ch, out, start_delay=20):
    delay = start_delay
    for attempt in range(1, 12):
        code, err = curl(ch['url'], out)
        size = os.path.getsize(out) if os.path.exists(out) else 0
        if code == '200' and size > 20000:
            return size, attempt
        print(f"    {ch['slug']}: HTTP {code} size={size} {err[:80]} -> sleep {delay}s", flush=True)
        time.sleep(delay)
        delay = min(int(delay * 1.8), 300)
    raise RuntimeError(f'gave up on {ch["url"]}')


def parse_opt(flag, default):
    """读取 --flag N 形式的可选参数。"""
    if flag in sys.argv:
        i = sys.argv.index(flag)
        if i + 1 < len(sys.argv) and sys.argv[i + 1].isdigit():
            return int(sys.argv[i + 1])
    return default


def main():
    start = parse_opt('--start', 0)
    limit = parse_opt('--limit', 0)
    bookkit.book_dir(sys.argv[1] if len(sys.argv) > 1 else None)
    mf = bookkit.load_manifest()
    os.makedirs('raw', exist_ok=True)

    chapters = mf['chapters'][start:]
    pending = [c for c in chapters
               if not (os.path.exists(f"raw/{c['slug']}.html")
                       and os.path.getsize(f"raw/{c['slug']}.html") > 20000)]
    if limit:
        pending = pending[:limit]
    print(f'{len(pending)} pages to fetch', flush=True)
    for i, ch in enumerate(pending, 1):
        t0 = time.time()
        size, attempts = fetch(ch, f"raw/{ch['slug']}.html")
        print(f"[{i}/{len(pending)}] {ch['slug']:46s} {size:7d}B tries={attempts} {time.time()-t0:.1f}s",
              flush=True)
        if i < len(pending):
            time.sleep(random.uniform(18, 26))
    print('DONE', flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
