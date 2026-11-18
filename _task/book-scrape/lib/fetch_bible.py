#!/usr/bin/env python3
"""抓取《圣经综合解读》的经文原文，接入 book-scrape 流程。

用法:
  python3 lib/fetch_bible.py <书名目录> manifest        # 读两个目录页，生成 manifest.json
  python3 lib/fetch_bible.py <书名目录> fetch [--start N] [--limit N] [--workers N]
  python3 lib/fetch_bible.py <书名目录> verify          # 核对章数、节号连续性与总节数

站点挂在 WordPress.com 上：带 SNI 的握手会被中间设备直接回 403，不带 SNI、靠
Host 头路由反而稳定 200。抓取先走这条无 SNI 通道，失败再退回普通 HTTPS，两种
方式都只取公开页面。每章只留经文的 <p>，注释、祷读、音频都不入 raw/。
"""
import argparse
import datetime
import json
import os
import random
import re
import socket
import ssl
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bible
import bookkit

bookkit.use_pylibs()

SITE = "https://cmcbiblereading.net"
HOST = "cmcbiblereading.net"
INDEX_PAGES = {
    "旧约": "/%e6%97%a7%e7%ba%a6%e7%bb%bc%e5%90%88%e8%a7%a3%e8%af%bb/",
    "新约": "/%e6%96%b0%e7%ba%a6%e7%bb%bc%e5%90%88%e8%a7%a3%e8%af%bb/",
}
# WordPress.com 边缘节点；靠 Host 头落到本站，不依赖对本域名的 DNS 解析
EDGE_IPS = ["192.0.78.24", "192.0.78.9", "192.0.78.10",
            "192.0.78.11", "192.0.78.12", "192.0.78.25"]
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
MIN_RAW_BYTES = 200


def _split(url):
    rest = url.split("://", 1)[1]
    host, _, path = rest.partition("/")
    return host, "/" + path


def normalize_url(url):
    """目录页里偶尔夹着未编码的中文或空白，统一转成可发送的百分号编码。"""
    from urllib.parse import quote, urlsplit, urlunsplit

    parts = urlsplit(re.sub(r"\s+", "", url))
    return urlunsplit((parts.scheme, parts.netloc, quote(parts.path, safe="/%"), "", ""))


def _decode_body(raw, headers):
    """按 Content-Length / chunked 还原响应体。

    边缘节点对同一本书可能回 Content-Length，也可能回 chunked；不认分块
    编码会把十六进制长度头混进正文，导致个别节随机丢失。
    """
    import gzip
    import zlib

    if headers.get("transfer-encoding", "").lower() == "chunked":
        out, rest = b"", raw
        while True:
            line_end = rest.find(b"\r\n")
            if line_end < 0:
                break
            size = int(rest[:line_end].split(b";")[0] or b"0", 16)
            if size == 0:
                break
            start = line_end + 2
            out += rest[start:start + size]
            rest = rest[start + size + 2:]
        raw = out
    elif headers.get("content-length", "").isdigit():
        expected = int(headers["content-length"])
        if len(raw) < expected:
            raise OSError(f"响应不完整：{len(raw)}/{expected} 字节")
        raw = raw[:expected]
    encoding = headers.get("content-encoding", "").lower()
    if encoding == "gzip":
        raw = gzip.decompress(raw)
    elif encoding == "deflate":
        raw = zlib.decompress(raw)
    if b"</html>" not in raw:
        raise OSError("响应缺少 </html>，按不完整处理")
    return raw


def _edge_get(url, timeout=60):
    """不带 SNI 握手，按 Host 头取页面。"""
    host, path = _split(url)
    last = None
    for ip in EDGE_IPS:
        try:
            sock = socket.create_connection((ip, 443), timeout)
        except OSError as exc:
            last = exc
            continue
        try:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            tls = ctx.wrap_socket(sock)
            req = (f"GET {path} HTTP/1.1\r\nHost: {host}\r\n"
                   f"User-Agent: {UA}\r\nAccept: text/html\r\n"
                   "Accept-Encoding: identity\r\nConnection: close\r\n\r\n")
            tls.sendall(req.encode())
            chunks = []
            while True:
                data = tls.recv(65536)
                if not data:
                    break
                chunks.append(data)
            tls.close()
        except (OSError, ssl.SSLError) as exc:
            last = exc
            continue
        raw = b"".join(chunks)
        head, _, body = raw.partition(b"\r\n\r\n")
        lines = head.split(b"\r\n")
        status = int(lines[0].split()[1]) if len(lines[0].split()) > 1 else 0
        headers = {}
        for line in lines[1:]:
            key, _, value = line.partition(b":")
            headers[key.strip().lower().decode("latin-1")] = value.strip().decode("latin-1")
        try:
            body = _decode_body(body, headers)
        except (OSError, ValueError) as exc:
            last = exc
            continue
        return status, headers, body
    raise OSError(f"所有边缘节点都连不上：{last}")


def _plain_get(url, timeout=60):
    """普通 HTTPS（带 SNI）。在不受干扰的网络上是主通道，在这里通常被回 403。"""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, dict(resp.headers), resp.read()


def get(url, retries=4):
    """取页面正文，返回 bytes；两种通道都失败时按 4 次退避重试。"""
    url = normalize_url(url)
    delay, last = 3, None
    for _attempt in range(1, retries + 1):
        for method in (_edge_get, _plain_get):
            try:
                status, headers, body = method(url)
            except Exception as exc:  # noqa: BLE001
                last = exc
                continue
            if status in (301, 302, 307, 308) and headers.get("location"):
                location = headers["location"]
                return get(location if location.startswith("http") else SITE + location,
                           retries=retries)
            if status == 200 and len(body) > MIN_RAW_BYTES:
                return body
            last = RuntimeError(f"HTTP {status}")
        time.sleep(delay)
        delay = min(delay * 2, 60)
    raise RuntimeError(f"{url} 取不到：{last}")


def fragment(html_bytes, url):
    """只留经文段落，产出可离线重跑的最小 HTML。"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_bytes.decode("utf-8", "replace"), "lxml")
    content = soup.select_one("div.entry-content") or soup
    kept = [str(p) for p in content.find_all("p")
            if bible.parse_paragraph(p.get_text(" ", strip=True))]
    stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    head = (f"<!-- source: {url} -->\n<!-- fetched: {stamp} -->\n"
            "<!-- 只保留经文段落；注释、祷读、音频已丢弃 -->\n")
    return (head + '<html><head><meta charset="utf-8"></head><body>\n'
            '<div class="entry-content">\n' + "\n".join(kept) +
            "\n</div>\n</body></html>\n")


def parse_index(html_bytes):
    """目录页是单段长文：书名加粗、章号是数字链接，按出现顺序配对。"""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html_bytes.decode("utf-8", "replace"), "lxml")
    content = soup.select_one("div.entry-content") or soup
    names = {zh for zh, _en, _n in bible.BOOKS}
    rows, book, buf = [], None, []
    for node in content.descendants:
        if getattr(node, "name", None) == "a":
            text = node.get_text(strip=True)
            if text.isdigit() and book:
                rows.append((book, int(text), node.get("href", "")))
            continue
        if not isinstance(node, str):
            continue
        buf.append(node)
        found = re.search(r"([^\s：:]{1,10})[：:]", "".join(buf))
        if found:
            name = bible.ALIASES.get(found.group(1), found.group(1))
            if name in names:
                book = name
            buf = []
    return rows


def clean_url(href):
    """目录页的链接偶尔夹带未编码的中文、`2deb9` 式断字符或坏掉的主机名，
    统一改写成按本站主机名 + 百分号编码的路径。"""
    from urllib.parse import quote, urlsplit

    raw = re.sub(r"\s+", "", href)
    raw = re.sub(r"(?<=%[0-9a-fA-F]{2})[0-9a-fA-F]{4,8}(?=%[0-9a-fA-F]{2})", "", raw)
    path = re.sub(r"/{2,}", "/", urlsplit(raw).path or "/")
    if not path.startswith("/"):
        path = "/" + path
    return SITE + quote(path, safe="/%")


def build_manifest(order_dir):
    rows = []
    for part, path in INDEX_PAGES.items():
        page_rows = parse_index(get(SITE + path))
        print(f"{part}目录：{len(page_rows)} 个章链接", flush=True)
        rows.extend((part,) + row for row in page_rows)

    books = [b[0] for b in bible.BOOKS]
    chapters_of = {zh: n for zh, _en, n in bible.BOOKS}
    counts = {zh: 0 for zh in books}
    current, seen_order = None, 0
    chapters = []

    for part, book, chapter, href in rows:
        if book != current:
            if current is not None and counts[current] != chapters_of[current]:
                raise SystemExit(f"{current} 章数不足：{counts[current]}/{chapters_of[current]}")
            index = books.index(book) + 1
            if index != seen_order + 1:
                raise SystemExit(f"目录顺序不对：期望 {books[seen_order]}，实际 {book}")
            seen_order, current = index, book
        counts[book] += 1
        if chapter != counts[book]:
            raise SystemExit(f"{book} 章号不连续：第 {counts[book]} 个链接是 {chapter}")
        if counts[book] > chapters_of[book]:
            raise SystemExit(f"{book} 章数超出正典 {chapters_of[book]} 章")
        url = clean_url(href)
        chapters.append({
            "part": part,
            "category": book,
            "title": bible.title(book, chapter),
            "slug": bible.slug(seen_order, chapter),
            "url": url,
        })

    if counts[books[-1]] != chapters_of[books[-1]]:
        raise SystemExit(f"{books[-1]} 章数不足：{counts[books[-1]]}/{chapters_of[books[-1]]}")
    if len(chapters) != bible.TOTAL_CHAPTERS:
        raise SystemExit(f"目录共 {len(chapters)} 章，应为 {bible.TOTAL_CHAPTERS} 章")

    manifest = {
        "book": "圣经（和合本）",
        "title_en": "Holy Bible, Chinese Union Version",
        "edition": "新标点和合本（香港圣经公会），文字据《圣经综合解读》经文整理",
        "source": SITE + "/",
        "docx": {"filename": "圣经.docx"},
        "site": {"content_selector": "div.entry-content", "verses": True},
        "chapters": chapters,
    }
    path = os.path.join(order_dir, "manifest.json")
    if os.path.exists(path):
        previous = json.load(open(path, encoding="utf-8"))
        if previous.get("source_gaps"):
            manifest["source_gaps"] = previous["source_gaps"]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print(f"写入 {path}：{len(chapters)} 章 / {len(books)} 卷", flush=True)
    return manifest


def chapter_path(raw_dir, slug):
    return os.path.join(raw_dir, f"{slug}.html")


def candidate_urls(ch):
    """坏链接的兜底：按「书名第N章逐节注解、祷读」重建，日期沿用目录页。"""
    import urllib.parse

    prefix = re.match(r"(https://[^/]+)/(\d{4}/\d{2}/\d{2})/", ch["url"])
    title = re.match(r"(.+?)\s*第(\d+)章", ch["title"])
    if not (prefix and title):
        return []
    slug = urllib.parse.quote(f"{title.group(1)}第{title.group(2)}章逐节注解、祷读")
    return [f"{prefix.group(1)}/{prefix.group(2)}/{slug}/"]


def fetch_chapter(ch, raw_dir, gaps=()):
    target = chapter_path(raw_dir, ch["slug"])
    if os.path.exists(target) and os.path.getsize(target) > MIN_RAW_BYTES:
        return ch["slug"], None
    time.sleep(random.uniform(0, 0.4))
    try:
        html = get(ch["url"])
    except Exception:  # noqa: BLE001  目录页链接坏掉时按标题重建一次
        for candidate in candidate_urls(ch):
            html = get(candidate)
            break
        else:
            raise
    frag = fragment(html, ch["url"])
    problem = bible.span_problem(bible.verse_pairs(frag), gaps)
    if problem:
        return ch["slug"], problem
    tmp = target + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(frag)
    os.replace(tmp, target)
    return ch["slug"], None


def cmd_fetch(order_dir, manifest, start, limit, workers):
    raw_dir = os.path.join(order_dir, "raw")
    os.makedirs(raw_dir, exist_ok=True)
    chapters = manifest["chapters"][start:]
    pending = [c for c in chapters
               if not (os.path.exists(chapter_path(raw_dir, c["slug"]))
                       and os.path.getsize(chapter_path(raw_dir, c["slug"])) > MIN_RAW_BYTES)]
    have = len(chapters) - len(pending)
    if limit:
        pending = pending[:limit]
    print(f"待抓 {len(pending)} 章（本段已有 {have} 章落盘），{workers} 并发", flush=True)

    done, failures, t0 = 0, [], time.time()
    gaps = manifest.get("source_gaps") or {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(fetch_chapter, c, raw_dir, gaps.get(c["slug"], ())): c
                   for c in pending}
        for future in as_completed(futures):
            chapter = futures[future]
            try:
                slug, problem = future.result()
            except Exception as exc:  # noqa: BLE001
                failures.append((chapter["slug"], str(exc)))
                print(f"FAIL {chapter['slug']}: {exc}", flush=True)
                continue
            done += 1
            if problem:
                failures.append((slug, problem))
                print(f"BAD  {slug}: {problem}", flush=True)
            rate = done / max(time.time() - t0, 1e-6)
            print(f"[{done}/{len(pending)}] {chapter['title']:14s} {rate:4.1f} 章/秒", flush=True)

    print(f"完成 {done} 章，失败 {len(failures)} 章，用时 {time.time() - t0:.0f}s", flush=True)
    for slug, why in failures:
        print(f"  {slug}: {why}", flush=True)
    return 1 if failures else 0


def cmd_verify(order_dir, manifest, write_gaps=False):
    raw_dir = os.path.join(order_dir, "raw")
    declared = manifest.get("source_gaps") or {}
    total, merged, problems, missing_files = 0, 0, [], []
    per_book, suspects = {}, {}
    for ch in manifest["chapters"]:
        path = chapter_path(raw_dir, ch["slug"])
        if not os.path.exists(path):
            missing_files.append(ch["slug"])
            continue
        pairs = bible.verse_pairs(open(path, encoding="utf-8").read())
        declared_gaps = declared.get(ch["slug"], ())
        issue = bible.span_problem(pairs, declared_gaps)
        if issue:
            problems.append(f"{ch['title']}：{issue}")
        covered = set()
        for start, end, _ in pairs:
            covered.update(range(start, end + 1))
        absent = sorted(set(range(1, max(covered) + 1)) - covered)
        if absent and absent != sorted(declared_gaps):
            suspects[ch["slug"]] = absent
        merged += sum(1 for start, end, _ in pairs if end > start)
        total += len(covered)
        stat = per_book.setdefault(ch["category"], [0, 0])
        stat[0] += 1
        stat[1] += len(covered)

    print(f"章数：{len(manifest['chapters']) - len(missing_files)}/{bible.TOTAL_CHAPTERS}")
    print(f"节数：{total}（参考值 {bible.REFERENCE_VERSES}，差 {total - bible.REFERENCE_VERSES}）")
    print(f"合并两节以上的段落：{merged} 处")
    for book, (chapters, verses) in per_book.items():
        print(f"  {book:8s} {chapters:3d} 章 {verses:5d} 节")
    if missing_files:
        print(f"缺 {len(missing_files)} 章：{missing_files[:10]}", file=sys.stderr)
    if problems:
        print(f"节号问题 {len(problems)} 处：", file=sys.stderr)
        for item in problems[:20]:
            print("  " + item, file=sys.stderr)
    if suspects:
        print(f"源站缺节 {len(suspects)} 章，可写入 manifest 的 source_gaps：", file=sys.stderr)
        print(json.dumps(suspects, ensure_ascii=False, indent=1), file=sys.stderr)
        if write_gaps:
            path = os.path.join(order_dir, "manifest.json")
            fresh = json.load(open(path, encoding="utf-8"))
            merged = dict(fresh.get("source_gaps") or {})
            merged.update(suspects)
            fresh["source_gaps"] = merged
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(fresh, fh, ensure_ascii=False, indent=1)
                fh.write("\n")
            print(f"已写入 {path} 的 source_gaps", file=sys.stderr)
    ok = not missing_files and not problems and not suspects
    return 0 if ok else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("book_dir")
    parser.add_argument("command", choices=["manifest", "fetch", "verify"])
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--write-gaps", action="store_true",
                        help="verify 时把源站缺节写入 manifest 的 source_gaps")
    args = parser.parse_args()

    order_dir = bookkit.book_dir(args.book_dir)
    if args.command == "manifest":
        build_manifest(order_dir)
        return 0
    manifest = bookkit.load_manifest()
    if args.command == "fetch":
        return cmd_fetch(order_dir, manifest, args.start, args.limit, args.workers)
    return cmd_verify(order_dir, manifest, args.write_gaps)


if __name__ == "__main__":
    sys.exit(main())
