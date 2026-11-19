#!/usr/bin/env python3
"""圣经引用对照：把正文里的「卷 章:节」解析成结构化引用，并从经文库里取出原文。

跨书共用。任何书籍只要在 manifest 里声明经文源，就能让引用变成可点击、
可展开的经文对照：

    "scripture": {
        "source": "圣经-和合本-bible",
        "inline": true
    }

`source` 是经文书目录名（相对 book-scrape 根目录）。`inline` 为真时把经文
原文内嵌进产物（单文件、离线可读）；为假时只保留跳转链接，不内嵌文字。

经文源本身用同一套 manifest（`site.verses` 为真），每章一个 `<slug>.md`，
正文一行一节、行首是节号。
"""
import json
import os
import re

import bookkit

ROOT = bookkit.ROOT

# ---------------------------------------------------------------- 卷名映射

# 66 卷正典，按书序。索引即经卷序号。
CANON = [
    '创世记', '出埃及记', '利未记', '民数记', '申命记', '约书亚记', '士师记',
    '路得记', '撒母耳记上', '撒母耳记下', '列王纪上', '列王纪下', '历代志上',
    '历代志下', '以斯拉记', '尼希米记', '以斯帖记', '约伯记', '诗篇', '箴言',
    '传道书', '雅歌', '以赛亚书', '耶利米书', '耶利米哀歌', '以西结书',
    '但以理书', '何西阿书', '约珥书', '阿摩司书', '俄巴底亚书', '约拿书',
    '弥迦书', '那鸿书', '哈巴谷书', '西番雅书', '哈该书', '撒迦利亚书',
    '玛拉基书', '马太福音', '马可福音', '路加福音', '约翰福音', '使徒行传',
    '罗马书', '哥林多前书', '哥林多后书', '加拉太书', '以弗所书', '腓立比书',
    '歌罗西书', '帖撒罗尼迦前书', '帖撒罗尼迦后书', '提摩太前书',
    '提摩太后书', '提多书', '腓利门书', '希伯来书', '雅各书', '彼得前书',
    '彼得后书', '约翰一书', '约翰二书', '约翰三书', '犹大书', '启示录',
]

# 全书里实际出现的缩写。中文圣经约定俗成的简写，不是简单取首字：
# 「帖前」是帖撒罗尼迦前书、「约壹」是约翰一书、「来」是希伯来书。
ALIASES = {
    '创': '创世记', '出': '出埃及记', '利': '利未记', '民': '民数记',
    '申': '申命记', '书': '约书亚记', '士': '士师记', '得': '路得记',
    '撒上': '撒母耳记上', '撒下': '撒母耳记下', '王上': '列王纪上',
    '王下': '列王纪下', '代上': '历代志上', '代下': '历代志下',
    '拉': '以斯拉记', '尼': '尼希米记', '斯': '以斯帖记', '伯': '约伯记',
    '诗': '诗篇', '箴': '箴言', '传': '传道书', '歌': '雅歌',
    '赛': '以赛亚书', '耶': '耶利米书', '哀': '耶利米哀歌', '结': '以西结书',
    '但': '但以理书', '何': '何西阿书', '珥': '约珥书', '摩': '阿摩司书',
    '俄': '俄巴底亚书', '拿': '约拿书', '弥': '弥迦书', '鸿': '那鸿书',
    '哈': '哈巴谷书', '番': '西番雅书', '该': '哈该书', '亚': '撒迦利亚书',
    '玛': '玛拉基书', '太': '马太福音', '可': '马可福音', '路': '路加福音',
    '约': '约翰福音', '徒': '使徒行传', '罗': '罗马书', '林前': '哥林多前书',
    '林后': '哥林多后书', '加': '加拉太书', '弗': '以弗所书',
    '腓': '腓立比书', '西': '歌罗西书', '帖前': '帖撒罗尼迦前书',
    '帖后': '帖撒罗尼迦后书', '提前': '提摩太前书', '提后': '提摩太后书',
    '多': '提多书', '门': '腓利门书', '来': '希伯来书', '雅': '雅各书',
    '彼前': '彼得前书', '彼后': '彼得后书', '约壹': '约翰一书',
    '约一': '约翰一书', '约贰': '约翰二书', '约二': '约翰二书',
    '约叁': '约翰三书', '约三': '约翰三书', '犹': '犹大书', '启': '启示录',
}

# 次经／伪经：中文和合本不含这些卷，命中就跳过（不静默错配到正典）
APOCRYPHA = ('马加比', '巴录书', '多比传', '便西拉', '所罗门智训', '以斯得拉')

# 书名前面常粘的叙述性文字，解析前先剥掉（含「如：」「见」「参」这类引导词）
_LEAD_NOISE = re.compile(
    r'^(?:(?:如|例如|见|参见|参|比较|引自|引自於|代替|是|就是|原文|主耶稣就是'
    r'|和|同|及|又|另见)\s*[:：]?\s*)+')


def resolve_book(name):
    """把书名的任意写法归一成 66 卷的正式名；认不出返回 None。"""
    if not name:
        return None
    name = _LEAD_NOISE.sub('', name).strip()
    if not name:
        return None
    if any(k in name for k in APOCRYPHA):
        return None
    if name in CANON:
        return name
    if name in ALIASES:
        return ALIASES[name]
    # 「箴言」「希」这类长短混写：找唯一的正式名前缀
    hits = [b for b in CANON if b.startswith(name)]
    if len(hits) == 1:
        return hits[0]
    # 拉丁式简写（「约一」）再按别名表兜一次
    return ALIASES.get(name)


# ---------------------------------------------------------------- 引用解析

# 一个引用块里的分隔符：中英文分号、逗号、顿号、空格
# 引用之间的分隔符：只按分号／顿号切。中文逗号有两种用途 ——
# 「诗66:8,9」是同一节的并列（逗号分节），「雅1:22，25」同理；
# 而「提前6:15，16」这类也是分节。真正的引用分隔只用分号与顿号。
SPLIT_RE = re.compile(r'[；;、]')
# 节范围的分隔符：半角连字符、全角连字符（－ U+FF0D）、长短破折号、波浪号
DASH = r'[-–—－~～]'
# 「卷 章:节」或「章:节」（省略卷名，沿用上一个）
ONE_RE = re.compile(
    r'^(?:(?P<book>[\u4e00-\u9fa5]{1,8}?)\s*)?'
    r'(?P<chap>\d+)'
    r'(?:\s*[:：]\s*(?P<verse>\d+)'
    r'(?:\s*' + DASH + r'\s*(?P<verse_end>\d+))?'
    r'(?:\s*[,，]\s*(?P<more>\d+(?:\s*' + DASH + r'\s*\d+)?'
    r'(?:\s*[,，]\s*\d+(?:\s*' + DASH + r'\s*\d+)?)*))?'
    r')?$'
)
DASH_RE = re.compile(DASH)


def parse_refs(inner, verse_count=None):
    """解析一个括号里的出处串，返回 [(卷, 章, 起始节, 结束节)]。

    能处理本书实际出现的写法：
      诗86:9                     卷+章:节
      诗16:5-11； 73:24-26；144:15 后两项省略卷名，沿用上一个
      诗66:8,9 / 雅1:22，25      逗号分节
      约壹3:11、23               顿号分节（沿用章号）
      诗67:1-3；99:3；100:3-4；145 纯数字也可能是章号（第 145 篇）
      结1:4-27                   节范围
      赛 43:7                    书名与章号之间有空格
    认不出的片段直接跳过，不影响其余部分。

    verse_count(book, chap) 可选：给定章有多少节，用来判断裸数字是节还是章。
    """
    out = []
    book = None
    last_chap = None
    # 顿号既是分节也是分引用：「约壹3:11、23」是同一章的两节，
    # 「出15:3、诗24:10」后者另起书名。按 token 逐个尝试，认不出的忽略。
    for token in re.split(r'[；;、]', inner.strip()):
        token = token.strip()
        if not token:
            continue
        # 裸数字：「约壹3:11、23」的 23 是节；「诗67:1-3；…；145」的 145 是章
        plain = re.match(r'^(\d+)(?:\s*' + DASH + r'\s*(\d+))?$', token)
        if plain and book:
            s = int(plain.group(1))
            e = int(plain.group(2) or s)
            total = verse_count(book, last_chap) if (verse_count and last_chap) else 0
            if total and s > total:
                # 超出上一章的节数：当作新的一章
                last_chap = s
                out.append((book, s, 1, None))
            else:
                out.append((book, last_chap, s, e))
            continue
        m = ONE_RE.match(token)
        if not m:
            continue
        if m.group('book'):
            resolved = resolve_book(m.group('book'))
            if resolved is None:
                # 认不出的书名（次经、叙述文字）：跳过这一片
                book = None
                continue
            book = resolved
        if book is None or not m.group('chap'):
            continue
        chap = int(m.group('chap'))
        last_chap = chap
        if not m.group('verse'):
            # 只给章号（如「诗23」）：整章
            out.append((book, chap, 1, None))
            continue
        start = int(m.group('verse'))
        end = int(m.group('verse_end') or start)
        out.append((book, chap, start, end))
        # 逗号分节：诗66:8,9 / 雅1:22，25 → 追加后续各节
        more = m.group('more')
        if more:
            for piece in re.split(r'[,，]', more):
                piece = piece.strip()
                if not piece:
                    continue
                pm = re.match(r'^(\d+)(?:\s*' + DASH + r'\s*(\d+))?$', piece)
                if not pm:
                    continue
                s = int(pm.group(1))
                e = int(pm.group(2) or s)
                out.append((book, chap, s, e))
    return out


# ---------------------------------------------------------------- 经文库

class VerseSource:
    """经文库：按「卷 章」载入 markdown，提供按节取原文。

    经文书的 manifest 里 `site.verses` 为真，目录内每章一个 `<slug>.md`，
    `category` 是卷名、`title` 是「某卷 第N章」，正文一行一节。
    """

    def __init__(self, book_name):
        path = book_name if os.path.isabs(book_name) else os.path.join(ROOT, book_name)
        if not os.path.isdir(path):
            raise SystemExit(f'经文源目录不存在: {path}')
        self.dir = path
        manifest = json.load(open(os.path.join(path, 'manifest.json'), encoding='utf-8'))
        self.by_book = {}       # 卷名 -> {章号: slug}
        for ch in manifest['chapters']:
            book = ch.get('category') or ''
            m = re.search(r'第\s*(\d+)\s*章', ch.get('title') or '')
            if not book or not m:
                continue
            self.by_book.setdefault(book, {})[int(m.group(1))] = ch['slug']
        self._cache = {}

    def verses(self, book, chap):
        """返回 {节号: 经文}；该章不存在返回 None。

        源站会把两节并成一段（`2–3 『要孝敬父母…』`），这里把范围行拆开，
        让 2 与 3 都能取到同一段文字 —— 否则 `弗6:2` 这类引用会取空。
        """
        slug = self.by_book.get(book, {}).get(chap)
        if not slug:
            return None
        path = os.path.join(self.dir, slug + '.md')
        if path in self._cache:
            return self._cache[path]
        found = {}
        if os.path.exists(path):
            for line in open(path, encoding='utf-8'):
                m = re.match(r'^\s*(\d+)(?:\s*' + DASH + r'\s*(\d+))?\s+(.*\S)\s*$', line)
                if not m:
                    continue
                text = m.group(3)
                start = int(m.group(1))
                end = int(m.group(2) or start)
                for n in range(start, end + 1):
                    found[n] = text
        self._cache[path] = found
        return found

    def single_chapter(self, book):
        """该卷是否只有一章（约二、约三、犹大、腓利门）。"""
        return len(self.by_book.get(book, {})) == 1

    def fetch(self, book, chap, start, end=None):
        """取一节或一段的原文，返回 [(节号, 经文)]。"""
        table = self.verses(book, chap)
        if not table:
            return []
        last = end if end is not None else (start if start else max(table))
        first = start or 1
        return [(n, table[n]) for n in range(first, last + 1) if n in table]


# ---------------------------------------------------------------- 与渲染器协作

BRACKET_REF_RE = re.compile(r'（([^（）]{0,120})）')


def split_reference_block(inner):
    """判断一段括号内容是否「纯出处」，是则返回原文，否则 None。

    判据是：按分号切开后，每一片都能被 ONE_RE 认出来。这样「如：申4:24」
    「（见上文）」这类叙述句不会被误当成可展开的引用块。
    """
    body = _LEAD_NOISE.sub('', inner.strip()).strip()
    if not body:
        return None
    pieces = [p for p in re.split(r'[；;]', body) if p.strip()]
    if not pieces:
        return None
    for piece in pieces:
        # 「约壹3:11、23」这类顿号分节：拆开逐个校验，任一片认不出就不算纯出处
        for sub in re.split(r'、', piece):
            if sub.strip() and not ONE_RE.match(sub.strip()):
                return None
    return body


class Scripture:
    """给一本书用的引用解析 + 取经入口。

    典型用法（build_html.py）：
        scr = scripture.load()          # 读 manifest 的 scripture 段，没有则返回 None
        html = scr.render_block(inner)   # 括号内部 → 可展开的标记
        scr.report()                    # 构建结束时打印命中率
    """

    def __init__(self, source, inline=True):
        self.source = source
        self.inline = inline
        self.hits = 0
        self.misses = []
        self.verse_chars = 0

    def lookup(self, refs):
        """refs -> [(标签, [(节号, 经文)])]，按引用顺序。"""
        out = []
        for book, chap, start, end in refs:
            # 单章书（约二、约三、犹大、腓利门、俄巴底亚）整卷只有一章：
            # 「犹4」是第 4 节，「约叁12」是第 12 节，都不是章号。
            # 「约贰5:17」这种把节写成章的，按「第 5 节」解释（该卷没有第 5 章）。
            single = self.source.single_chapter(book)
            if single:
                if start is None:
                    chap, start, end = 1, chap, chap
                elif chap > 1:
                    # 章号超出单章书范围：原来的「章」就是节号，:后面那截忽略
                    chap, start, end = 1, chap, None
            rows = self.source.fetch(book, chap, start, end)
            label = f'{book} {chap}:{start}' if not single else f'{book} {start}'
            if end and end != start:
                label += f'-{end}'
            if not rows:
                self.misses.append(label)
                out.append((label, []))
                continue
            self.verse_chars += sum(len(t) for _, t in rows)
            out.append((label, rows))
        return out

    def verse_count(self, book, chap):
        """某章有多少节，用于判断裸数字是节号还是章号。"""
        table = self.source.verses(book, chap)
        return max(table) if table else 0

    def render_block(self, inner, escape):
        """把括号内部渲染成可展开的引用块；不是纯出处则返回 None。"""
        body = split_reference_block(inner)
        if body is None:
            return None
        refs = parse_refs(body, self.verse_count)
        if not refs:
            return None
        self.hits += 1
        groups = self.lookup(refs)
        if not groups:
            return None
        return render_reference(groups, escape, self.inline)

    def report(self):
        if not self.hits and not self.misses:
            return ''
        msg = f'引用块 {self.hits} 处，经文 {self.verse_chars} 字'
        if self.misses:
            uniq = sorted(set(self.misses))
            msg += f'，未命中 {len(uniq)} 处: {", ".join(uniq[:6])}'
        return msg


def render_reference(groups, escape, inline=True):
    """生成一处引用块：出处标签 + 经文。

    经文不预置成 DOM 节点：本书 1,640 处引用块若全部铺开要多出约 1.3 万
    个节点、首屏慢一倍，而用户是「点了才看」。这里只存一份纯文本，
    点开时由页面脚本切成段落插进文档。

    data-text 里每节占一行（「节号\\t经文」），比嵌套标签省得多。
    """
    tags = []
    lines = []
    for label, rows in groups:
        # 取不到经文的出处不加 .ref（不可点），否则点了没反应
        if rows:
            tags.append(f'<span class="ref">{escape(label)}</span>')
        else:
            tags.append(f'<span class="ref-miss" title="和合本无此节">{escape(label)}</span>')
        for n, text in rows:
            lines.append(f'{n}\t{text}')
    if not lines or not inline:
        # 没取到经文（或配置为不内嵌）：只留出处，不造空面板
        return '<span class="refs">' + '；'.join(tags) + '</span>'
    payload = escape('\n'.join(lines))
    return ('<span class="refs" data-text="' + payload + '">'
            + '；'.join(tags) + '</span>')


def load(manifest=None):
    """读 manifest 的 scripture 段；未配置返回 None。"""
    if manifest is None:
        manifest = bookkit.load_manifest()
    cfg = manifest.get('scripture')
    if not cfg:
        return None
    source = cfg.get('source')
    if not source:
        raise SystemExit('manifest.scripture 缺少 source（经文书目录名）')
    return Scripture(VerseSource(source), inline=bool(cfg.get('inline', True)))
