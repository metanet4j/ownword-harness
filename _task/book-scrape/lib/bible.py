#!/usr/bin/env python3
"""圣经正典结构与经文解析。

66 卷、1189 章的正典顺序、英文短名与章数集中在这里，抓取与转换共用；改这里
一处，manifest 生成和校验同时生效。

经文页每节写作 `<p><strong>【太一1】「…」</strong></p>`：书名缩写加中文数字
章号、阿拉伯数字节号。解析只认这个标记，注释段落不带标记，因此能自然过滤掉。
"""
import re

PART_OT = "旧约"
PART_NT = "新约"

# (中文名, 英文短名, 章数)；旧约 39 卷在前，新约 27 卷在后
BOOKS = [
    ("创世记", "genesis", 50),
    ("出埃及记", "exodus", 40),
    ("利未记", "leviticus", 27),
    ("民数记", "numbers", 36),
    ("申命记", "deuteronomy", 34),
    ("约书亚记", "joshua", 24),
    ("士师记", "judges", 21),
    ("路得记", "ruth", 4),
    ("撒母耳记上", "1-samuel", 31),
    ("撒母耳记下", "2-samuel", 24),
    ("列王纪上", "1-kings", 22),
    ("列王纪下", "2-kings", 25),
    ("历代志上", "1-chronicles", 29),
    ("历代志下", "2-chronicles", 36),
    ("以斯拉记", "ezra", 10),
    ("尼希米记", "nehemiah", 13),
    ("以斯帖记", "esther", 10),
    ("约伯记", "job", 42),
    ("诗篇", "psalms", 150),
    ("箴言", "proverbs", 31),
    ("传道书", "ecclesiastes", 12),
    ("雅歌", "song-of-songs", 8),
    ("以赛亚书", "isaiah", 66),
    ("耶利米书", "jeremiah", 52),
    ("耶利米哀歌", "lamentations", 5),
    ("以西结书", "ezekiel", 48),
    ("但以理书", "daniel", 12),
    ("何西阿书", "hosea", 14),
    ("约珥书", "joel", 3),
    ("阿摩司书", "amos", 9),
    ("俄巴底亚书", "obadiah", 1),
    ("约拿书", "jonah", 4),
    ("弥迦书", "micah", 7),
    ("那鸿书", "nahum", 3),
    ("哈巴谷书", "habakkuk", 3),
    ("西番雅书", "zephaniah", 3),
    ("哈该书", "haggai", 2),
    ("撒迦利亚书", "zechariah", 14),
    ("玛拉基书", "malachi", 4),
    ("马太福音", "matthew", 28),
    ("马可福音", "mark", 16),
    ("路加福音", "luke", 24),
    ("约翰福音", "john", 21),
    ("使徒行传", "acts", 28),
    ("罗马书", "romans", 16),
    ("哥林多前书", "1-corinthians", 16),
    ("哥林多后书", "2-corinthians", 13),
    ("加拉太书", "galatians", 6),
    ("以弗所书", "ephesians", 6),
    ("腓立比书", "philippians", 4),
    ("歌罗西书", "colossians", 4),
    ("帖撒罗尼迦前书", "1-thessalonians", 5),
    ("帖撒罗尼迦后书", "2-thessalonians", 3),
    ("提摩太前书", "1-timothy", 6),
    ("提摩太后书", "2-timothy", 4),
    ("提多书", "titus", 3),
    ("腓利门书", "philemon", 1),
    ("希伯来书", "hebrews", 13),
    ("雅各书", "james", 5),
    ("彼得前书", "1-peter", 5),
    ("彼得后书", "2-peter", 3),
    ("约翰一书", "1-john", 5),
    ("约翰二书", "2-john", 1),
    ("约翰三书", "3-john", 1),
    ("犹大书", "jude", 1),
    ("启示录", "revelation", 22),
]

OT_BOOKS = 39
# 目录页把约翰一/二/三书写作「壹、贰、叁」，正典名沿用和合本通行写法
ALIASES = {"约翰壹书": "约翰一书", "约翰贰书": "约翰二书", "约翰叁书": "约翰三书"}
TOTAL_CHAPTERS = sum(b[2] for b in BOOKS)
# 和合本沿用钦定本的节号，全书 31102 节；只作核对的参考值，不参与流程控制
REFERENCE_VERSES = 31102

VERSE_MARK_RE = re.compile(r"^【?([^】]{1,17})】[ \t]*(.+)$", re.S)
ANY_MARK_RE = re.compile(r"【([^】]{1,17})】")
NUM_RE = re.compile(r"\d+")
RANGE_RE = re.compile(r"[~～\-—–]")


def marker_span(mark):
    """从标记文本（不含括号）解析出 (起节, 止节)。

    章号是中文数字、节号是阿拉伯数字；标记里偶尔混进 `2\ne84a\n3` 这类
    断字符（`e84a` 是没用上的字形实体），去掉空白与字母后再拼数字。
    """
    mark = re.sub(r"[A-Za-z][0-9A-Fa-f]*", "", mark)
    nums = NUM_RE.findall(mark)
    if not nums:
        return None
    if len(nums) >= 2 and RANGE_RE.search(mark):
        start, end = int(nums[0]), int(nums[1])
    else:
        start = end = int("".join(nums))
    if start < 1 or end < start:
        return None
    return start, end


def parse_verse(text):
    """把一段文字解析成 (起节, 止节, 经文)；不是经文段就返回 None。

    兼容源站的几种写法：正常的 `【创二十15】「…」`；缺了前括号的
    `创四十二37】「…」`；整节没有起始书名号的 `【出十1】耶和华对摩西说…`；
    以及把两节并成一段的 `【创廿四29~30】「…」`。
    """
    m = VERSE_MARK_RE.match(text)
    if not m:
        return None
    body = m.group(2).strip()
    span = marker_span(m.group(1))
    if not body or not span:
        return None
    return span[0], span[1], unwrap(body)


def parse_paragraph(text):
    """一段文字里的全部节：站点偶尔把两三节排进同一段（`【路六18】… 【路六19】…`）。"""
    marks = list(ANY_MARK_RE.finditer(text))
    if not marks:
        one = parse_verse(text)
        return [one] if one else []
    out = []
    for i, mark in enumerate(marks):
        span = marker_span(mark.group(1))
        if not span:
            continue
        end = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        body = text[mark.end():end].strip()
        if body:
            out.append((span[0], span[1], unwrap(body)))
    return out


def order_of(book):
    """书名 → (正典序号 1-66, 所属约)。"""
    for i, (zh, _en, _n) in enumerate(BOOKS, 1):
        if zh == book:
            return i, (PART_OT if i <= OT_BOOKS else PART_NT)
    raise KeyError(book)


def slug(chapter_order, chapter):
    """章节文件名：正典序号 + 英文短名 + 章号，全部 ASCII，便于 EPUB 与排序。"""
    _zh, en, _n = BOOKS[chapter_order - 1]
    return f"{chapter_order:02d}-{en}-{chapter:03d}"


def title(book, chapter):
    return f"{book} 第{chapter}章"


def iter_chapters():
    """按正典顺序产出 (序号, 约, 书名, 英文短名, 章号)。"""
    order = 0
    for zh, en, n in BOOKS:
        order += 1
        part = PART_OT if order <= OT_BOOKS else PART_NT
        for ch in range(1, n + 1):
            yield order, part, zh, en, ch


def verse_pairs(soup_or_html):
    """从经文页或已裁剪的片段中取 (起节, 止节, 经文) 列表，保持页面顺序。"""
    from bs4 import BeautifulSoup

    soup = (soup_or_html if hasattr(soup_or_html, "find_all")
            else BeautifulSoup(soup_or_html, "lxml"))
    out = []
    for p in soup.find_all("p"):
        out.extend(parse_paragraph(p.get_text(" ", strip=True)))
    return out


def unwrap(text):
    """去掉站点给每一节加的整节书名号，只留经文本身。

    站点把整节经文包在「」里；一节全是对话时内层还有「」，所以只剥一层。
    """
    if len(text) >= 2 and text.startswith("「") and text.endswith("」"):
        inner = text[1:-1]
        if inner.count("「") == inner.count("」"):
            return inner
    return text


def span_problem(pairs, gaps=()):
    """节号必须从 1 起连续覆盖到本章末节；gaps 是源站确实缺的节号。

    返回问题描述或 None。源站偶有整节漏排（如利未记 16 章缺第 21 节），
    这类缺口记在 manifest 的 source_gaps 里，不当作解析失败。
    """
    if not pairs:
        return "没有解析到任何一节"
    skip = set(gaps)
    expected = 1
    for start, end, _ in pairs:
        while expected in skip:
            expected += 1
        if start != expected:
            return f"第 {start} 节处不连续（上一条到第 {expected - 1} 节）"
        expected = end + 1
    return None
