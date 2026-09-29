#!/usr/bin/env python3
"""用 curl 串行抓取 cmchurch.org《如何明白圣经》全部章节，遇到 429 自动退避。

用法:
  python3 fetch_html.py [起始序号]
"""
import json
import os
import random
import subprocess
import sys
import time

BASE = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE)
mf = json.load(open('manifest.json', encoding='utf-8'))
os.makedirs('raw', exist_ok=True)

# 该站对浏览器 UA 的自动请求返回 403/429，隐藏 UA 反而稳定返回 200。
def curl(url, out):
    cmd = ['curl', '-sS', '--compressed', '--max-time', '90',
           '-o', out, '-w', '%{http_code}', url]
    r = subprocess.run(cmd, capture_output=True, text=True)
    return r.stdout.strip(), r.stderr.strip()


def fetch(ch, start_delay=20):
    out = f"raw/{ch['slug']}.html"
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


chapters = mf['chapters']
start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
pending = [c for c in chapters[start:]
           if not (os.path.exists(f"raw/{c['slug']}.html")
                   and os.path.getsize(f"raw/{c['slug']}.html") > 20000)]
print(f'{len(pending)} pages to fetch', flush=True)
for i, ch in enumerate(pending, 1):
    t0 = time.time()
    size, attempts = fetch(ch)
    print(f"[{i}/{len(pending)}] {ch['slug']:46s} {size:7d}B tries={attempts} {time.time()-t0:.1f}s", flush=True)
    if i < len(pending):
        time.sleep(random.uniform(18, 26))
print('DONE', flush=True)
