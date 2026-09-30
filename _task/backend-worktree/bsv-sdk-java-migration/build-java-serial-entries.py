#!/usr/bin/env python3
"""生成「局部 → Java 入口」映射表 `java-serial-entries.json`（A2）。

背景：全量 Java 阶段只把 `MIGRATION_*_TS_INPUTS` 指向本轮 `ts-inputs.jsonl`，而有一批局部
（A2，743 例）的 Java 重放**不读**这些变量，而是走各自的旧接口：

  * `-Dmigration.<x>.corpus|plan=<冻结语料>` —— 重放据此启用，并把标准行直接追加到
    `EVIDENCE_INPUTS_PATH`（本轮 = `<runDir>/java-inputs.jsonl`）；
  * 自有环境变量（如 `MIGRATION_WALLET_WIRE_*`、`MIGRATION_UTILS_PROPERTY_JAVA_*`）；
  * 少数局部把**原始调用**写到 `-Dmigration.<x>.input(s).output`，再由 Python 转换器映射成
    标准行（`shape = raw-convert`）。

本脚本**不猜**：每个局部的入口都从它已跑通的单局部 Java 采集记录里提取——
  1. `full-evidence-locals.json[local].java_run_manifest` 里的 `command`（当时真实的适配器
     调用，含 `--replay` / `--plan` / `--corpus` 等实参）；
  2. 该适配器源码里 java 分支的 `-Dmigration.*` 与环境变量赋值（入口名与取值表达式）；
  3. 取值表达式按上述实参解析成绝对路径或 `{runDir}` 占位符。

逐条核实（任一不成立即记入 `unresolved`，不写入条目）：
  * 属性名确实被该局部的 Java 源码读取（`System.getProperty("<名>")`，含连字符属性）；
  * 语料／计划文件真实存在（占位符路径除外）；
  * 局部登记表里的 `java_inputs` 确实覆盖该局部计划内的用例（即该入口当年跑通过）。

用法：
    python3 build-java-serial-entries.py [--check]
    # --check 只比对现有 java-serial-entries.json 是否需要重写
"""
import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
LOCALS = TASK / 'full-evidence-locals.json'
CATALOG = TASK / 'module-tests.json'
MISSING = TASK / '.cache/evidence/full-run-14-20260901/missing-java-input-cases.json'
JAVA_TEST_ROOT = TASK / 'metanet4j-bsv-sdk/src/test/java'
OUTPUT = TASK / 'java-serial-entries.json'
# A1（共享向量局部）由 java-vector-inputs.py 负责，本表不重复登记。
VECTOR_FILES = ('src/script/__tests/Script.test.ts', 'src/script/__tests/Spend.test.ts',
                'src/script/__tests/SpendValildVectors.test.ts',
                'src/transaction/__tests/Transaction.test.ts')
# wallet-wire 的 4 项必须一起给（详见 run-full-java-capture.py 的注释）。
WALLET_WIRE_ENVS = ('MIGRATION_WALLET_WIRE_ASSERTION_INDEX',
                    'MIGRATION_WALLET_WIRE_JAVA_LARGE_ACTUALS')
# utils.test.ts 的 9 个局部共用同一个 `migration.utils.corpus`：语料按局部拆分且 javaMethod 互不
# 重叠，因此全量阶段把 9 份冻结语料合并成一份（见 mergedFiles）。
UTILS_CORPUS_PROPERTY = 'migration.utils.corpus'
SKIP_PROPERTIES = {'migration.parity.java.output', 'migration.parity.largeArrays'}
# 这三个入口是**原始调用**的落点（不是语料）：Maven 跑完后必须再由对应转换器映射成标准行。
RAW_CONVERT_OUTPUTS = {
    'migration.validation.input.output': 'validation-helpers',
    'migration.authFetch.property.inputs': 'auth-fetch-property',
    'MIGRATION_UTILS_PROPERTY_JAVA_INPUTS': 'utils-property',
    'MIGRATION_UTILS_PROPERTY_JAVA_BOUNDARIES': 'utils-property',
}
# Java 侧在 Maven 期间**写出**的文件（本轮必须是新文件；不是本地转换器的输入）。
JAVA_WRITTEN = set(RAW_CONVERT_OUTPUTS) | {'MIGRATION_WALLET_WIRE_JAVA_LARGE_ACTUALS'}
# 必须与某个入口同时给出的伴生属性（缺一项就静默退化成另一种行为，实测有坑）。
COMPANION_PROPERTIES = {
    'migration.walletWire.plan': [
        ('migration.parity.largeArrays', 'true',
         'Boolean.getBoolean("migration.parity.largeArrays")',
         'WalletWire 大型 actual 走摘要通道：只给 walletWire.plan 而不开 largeArrays，'
         '839 MB 的 java-assertions.raw.jsonl 会复现 OOM；只开 largeArrays 而不给 walletWire.plan，'
         'largeActual 因 PLAN == null 直接 return、见证文件不产出。四项必须一起给。'),
    ],
}


def read(path):
    return json.loads(Path(path).read_text())


def source_articles():
    """A2 的用例集合：全量运行缺失 Java 输入、且不属于 A1 向量文件的用例。"""
    catalog = read(CATALOG)
    missing = set(read(MISSING))
    case_file = {case['id']: item['path'] for item in catalog['files'] for case in item['cases']}
    return {case for case in missing if case_file[case] not in VECTOR_FILES}, case_file


def script_of(entry):
    """局部当年跑通的 Java 采集脚本：优先取 java_run_manifest 的 command[capture-*.py]。"""
    manifest = entry.get('java_run_manifest')
    if manifest and (TASK / manifest).is_file():
        command = read(TASK / manifest).get('command') or []
        for part in command:
            if part.endswith(('-side.py', '-local.py', '-replay.py')):
                return Path(part).name, [str(item) for item in command]
    name = entry.get('capture')
    return (name, []) if name else (None, [])


def java_branch(text):
    block = re.search(r"if args\.side == 'java':(.*?)(?:\n    else:|\Z)", text, re.S)
    return block.group(1) if block else text


def logical_lines(segment):
    """只把显式续写的赋值并成一行（上一行以 `=`／`+` 结尾，或下一行以 `+` 开头）。

    不能按括号配平来合并：`run(a, b,\\n  '-Dx=' + v,\\n  env=env)` 这类调用整体括号不配平，
    按配平合并会把整条命令并成一行，取值表达式就被后面的参数污染了。
    """
    lines = segment.splitlines()
    joined, index = [], 0
    while index < len(lines):
        line = lines[index]
        while line.rstrip().endswith(('=', '+')) or (
                index + 1 < len(lines) and lines[index + 1].lstrip().startswith('+')):
            index += 1
            if index >= len(lines):
                break
            line = line.rstrip() + ' ' + lines[index].strip()
        joined.append(line)
        index += 1
    return joined


# 取值表达式只可能是路径表达式；这些记号只出现在同一 argv 元素之后的参数里，遇到即截断。
EXPRESSION_END = (", env=", ", cwd=", "), '", "),'", ")]", ")]", ", check=")


def clean(expression):
    text = expression.strip()
    for marker in EXPRESSION_END:
        position = text.find(marker)
        if position >= 0:
            text = text[:position + (1 if marker.startswith(')') else 0)]
    text = text.strip().rstrip(',').strip().rstrip(']').strip()
    while text.endswith(')') and text.count(')') > text.count('('):
        text = text[:-1].strip()  # 去掉 `dict(..., X=str(raw / 'a.jsonl'))` 多出来的收尾括号
    return text


def property_lines(segment):
    result = []
    for line in logical_lines(segment):
        match = re.search(r"'-D(migration\.[A-Za-z0-9_.-]+)='?\s*\+?\s*(.*)", line)
        if match:
            result.append((match.group(1), clean(match.group(2))))
    return result


def env_lines(segment):
    result, seen = [], set()
    for pattern in (r"env\[['\"](MIGRATION_[A-Z0-9_]+)['\"]\]\s*=\s*([^\n]+)",
                    r",\s*(MIGRATION_[A-Z0-9_]+)=([^,\n]+)"):
        for name, expression in re.findall(pattern, segment):
            if name in seen:
                continue
            seen.add(name)
            result.append((name, clean(expression)))
    return result


def replay_path(script, argv):
    """适配器里 `replay` 变量的取值：`--replay` 实参，或 `--plan` 目录下的 replay-inputs.jsonl。"""
    text = (TASK / script).read_text() if (TASK / script).is_file() else ''
    option = lambda flag: (argv[argv.index(flag) + 1] if flag in argv else None)  # noqa: E731
    explicit = option('--replay')
    if re.search(r"replay\s*=\s*plan\s*/\s*'replay-inputs\.jsonl'", text):
        plan = option('--plan')
        if plan is None:
            return None, '适配器按 --plan 取语料，但采集记录里没有 --plan'
        return str((TASK / plan).resolve() / 'replay-inputs.jsonl'), 'plan/replay-inputs.jsonl'
    if explicit is not None:
        return str((TASK / explicit).resolve()), '--replay'
    return None, '既无 --replay 也无 --plan'


def resolve(expression, script, argv, local, text):
    """把适配器里的取值表达式解析成绝对路径或 `{runDir}` 占位符。"""
    option = lambda flag: (argv[argv.index(flag) + 1] if flag in argv else None)  # noqa: E731
    raw_match = re.fullmatch(r"str\(raw(?: / '([^']+)')?\)", expression)
    if raw_match:
        leaf = raw_match.group(1) or raw_variable_leaf(text, local)
        return f'{{runDir}}/java-serial/{local}/{leaf}', '本轮运行目录原始轨迹'
    if expression in ('str(parity)', 'str(assertions)', 'str(calls)'):
        return None, 'run-dir 原始轨迹（由本轮运行目录提供）'
    if expression == 'str(assertion_index)':
        path, _ = replay_path(script, argv)
        return (str(Path(path).parent / 'assertion-index.json') if path else None), '--replay 同目录'
    if expression == 'str(large)':
        return '{runDir}/java-large-actuals.jsonl', '本轮运行目录大型 actual 见证'
    if expression == 'str(wire)':
        # http-wallet-json 的 wire 是 TS 探针在本轮运行目录里产出的观测文件。
        return f'{{runDir}}/local/{local}/ts-requests.wire.jsonl', '本轮 TS 探针产物'
    if expression in ('str(replay)', 'str(replay.resolve())', 'str(args.replay)',
                      'str(args.replay.resolve())'):
        path, how = replay_path(script, argv)
        return path, how
    if expression == 'str(Path(args.corpus).resolve())':
        corpus = option('--corpus')
        return (str((TASK / corpus).resolve()) if corpus else None), '--corpus'
    match = re.fullmatch(r"str\(\(TASK / '([^']+)'\)\.resolve\(\)\)", expression)
    if match:
        return str((TASK / match.group(1)).resolve()), 'TASK 内固定资源'
    literal = re.fullmatch(r"'([^']*)'", expression)
    if literal:
        return literal.group(1), '字面量'
    return None, '未识别的取值表达式：' + expression


def raw_variable_leaf(text, local):
    """`raw` 变量在适配器里的定义（`raw = evidence / f'{args.side}-calls.raw.jsonl'`）→ 文件名。"""
    match = re.search(r"^\s*raw\s*=\s*[\w. ]*?/\s*f?'([^']+)'", text, re.M)
    leaf = match.group(1) if match else local + '.raw.jsonl'
    return leaf.replace('{args.side}', 'java')


def readers_of_literal(marker):
    """`Boolean.getBoolean("...")` 这类读取点所在文件。"""
    literal = marker.split('"')[1] if '"' in marker else marker
    hits = []
    for path in sorted(JAVA_TEST_ROOT.rglob('*.java')):
        if literal in path.read_text(errors='replace'):
            hits.append(str(path.relative_to(TASK / 'metanet4j-bsv-sdk')))
    return hits


def kind_of(value):
    if value.startswith('{runDir}'):
        return 'runDir'
    return 'file' if value.startswith('/') else 'literal'


def readers(property_name):
    """属性名确实被哪些 Java 源码读取（连字符属性也要匹配）。"""
    hits = []
    pattern = re.compile(r'System\.getProperty\("' + re.escape(property_name) + r'"')
    for path in sorted(JAVA_TEST_ROOT.rglob('*.java')):
        if pattern.search(path.read_text(errors='replace')):
            hits.append(str(path.relative_to(TASK / 'metanet4j-bsv-sdk')))
    return hits


def plan_cases(entry):
    plan = entry.get('input_plan')
    if not plan or not (TASK / plan).is_file():
        return set()
    return set(read(TASK / plan))


def java_input_coverage(entry, ids):
    path = entry.get('java_inputs')
    if not path or not (TASK / path).is_file():
        return 0
    text = (TASK / path).read_text(errors='replace')
    return sum(1 for case in ids if f'"{case}"' in text)


def build():
    articles, case_file = source_articles()
    entries, unresolved, merged = {}, [], {}
    locals_ = read(LOCALS)['locals']
    utils_members = []
    for entry in sorted(locals_, key=lambda item: item['name']):
        name = entry['name']
        ids = plan_cases(entry) & articles
        if not ids:
            continue
        script, argv = script_of(entry)
        base = {'local': name, 'cases': len(ids),
                'files': sorted({case_file[case] for case in ids})}
        if not script or not (TASK / script).is_file():
            unresolved.append({**base, 'reason': '没有可核实的单局部 Java 采集记录（未登记 capture / manifest）'})
            continue
        covered = java_input_coverage(entry, ids)
        if covered != len(ids):
            unresolved.append({**base, 'script': script,
                               'reason': f'登记的单局部 java-inputs.jsonl 只覆盖 {covered}/{len(ids)} 例'})
            continue
        text = (TASK / script).read_text()
        segment = java_branch(text)
        java_sources = [path.read_text(errors='replace') for path in JAVA_TEST_ROOT.rglob('*.java')]
        all_java = ''.join(java_sources)
        properties, env = {}, {}
        problems = []
        for property_name, expression in property_lines(segment):
            if property_name in SKIP_PROPERTIES:
                continue
            value, how = resolve(expression, script, argv, name, text)
            hit = readers(property_name)
            if not hit:
                problems.append(f'没有 Java 源码读取 {property_name}')
                continue
            if value is None:
                problems.append(f'{property_name} 无法解析（{how}）')
                continue
            if not value.startswith('{runDir}') and not Path(value).is_file():
                problems.append(f'{property_name} 引用文件不存在：{value}')
                continue
            record = {'value': value, 'kind': kind_of(value),
                      'role': 'output' if property_name in RAW_CONVERT_OUTPUTS else 'input',
                      'from': how, 'readers': hit}
            if expression == 'str(wire)':
                # 本轮 TS 探针产物；若本轮目录里没有，回退该局部当年冻结的那份并记 substitutions。
                report = argv[argv.index('--report') + 1] if '--report' in argv else None
                frozen = (TASK / report).resolve().parent / 'ts-requests.wire.jsonl' if report else None
                if frozen and frozen.is_file():
                    record['fallback'] = str(frozen)
            properties[property_name] = record
        for env_name, expression in env_lines(segment):
            if env_name in ('MIGRATION_PARITY_JAVA_OUTPUT', 'MIGRATION_PARITY_TS_OBSERVATIONS',
                            'MIGRATION_NETWORK_LOG') or env_name.endswith('_TS_OBSERVATIONS'):
                continue
            if env_name.startswith('MIGRATION_') and env_name.endswith('_TS_INPUTS'):
                continue  # 标准接口，全量阶段已统一注入
            if env_name not in all_java:
                continue  # 采集期专用变量（探针/断言索引），Java 侧不读
            value, how = resolve(expression, script, argv, name, text)
            if value is None:
                problems.append(f'{env_name} 无法解析（{how}）')
                continue
            if not value.startswith('{runDir}') and not Path(value).is_file():
                problems.append(f'{env_name} 引用文件不存在：{value}')
                continue
            env[env_name] = {'value': value, 'kind': kind_of(value),
                             'role': 'output' if env_name in JAVA_WRITTEN else 'input',
                             'from': how}
        # 伴生属性：读了源码确认存在对应读取点才登记，否则记问题。
        for trigger, companions in COMPANION_PROPERTIES.items():
            if trigger not in properties and trigger not in env:
                continue
            for property_name, value, marker, reason in companions:
                if marker not in all_java:
                    problems.append(f'伴生属性 {property_name} 的读取点不存在：{marker}')
                    continue
                properties[property_name] = {'value': value, 'kind': kind_of(value),
                                             'role': 'input',
                                             'from': 'wallet-wire recipe 伴生项',
                                             'readers': readers_of_literal(marker), 'reason': reason}
        if problems:
            unresolved.append({**base, 'script': script, 'reason': '；'.join(problems)})
            continue
        names = set(properties) | set(env)
        shape = 'raw-convert' if names & set(RAW_CONVERT_OUTPUTS) else 'property-corpus'
        if UTILS_CORPUS_PROPERTY in properties:
            utils_members.append({'local': name, 'corpus': properties[UTILS_CORPUS_PROPERTY]['value'],
                                  'cases': len(ids)})
        entries[name] = {**base, 'script': script, 'shape': shape,
                         'captureCommand': [item for item in argv],
                         'properties': properties, 'env': env}
    # utils.test.ts 的 9 份冻结语料合并成一份（javaMethod 互不重叠，逐样本归属单一用例）。
    if utils_members:
        merged[UTILS_CORPUS_PROPERTY] = {
            'output': '{runDir}/java-serial/utils-corpus.jsonl',
            'members': utils_members,
            'cases': sum(item['cases'] for item in utils_members),
            'reason': '同一属性被 9 个局部各指向一份语料，全量阶段只能取一个值；按局部冻结语料拼接'
                      '（UtilsInputReplay 按 javaMethod 分组消费，9 份语料的 javaMethod 互不重叠，'
                      '拼接后每个用例的样本仍唯一）'}
    # 两个无法靠注入接通的局部：原因已定位，人工复核后固定写明（不猜、不编造入口）。
    curated = {
        'auth-fetch-peer':
            'AuthFetchPeerTest 没有任何输入重放入口（无 System.getProperty("migration.*")、'
            '无 MIGRATION_*_TS_INPUTS、不写 EVIDENCE_INPUTS_PATH）；全部 .cache/evidence 里也搜不到'
            '这些 caseId 的 java-inputs 记录 → 需要改冻结 SDK 测试源码才能产出，超出 A2 范围',
        'auth-fetch-known-txids':
            'AuthFetchKnownTxidsPeerInputReplay 在注入的 TS 汇总里要求 '
            'value.kind = AuthFetch.knownTxidsPeerInput 的行，而本轮 ts-inputs.jsonl 该用例只有 '
            'kind = AuthFetch.knownTxidsInput（付款探针）一行 → 属 TS 侧聚合缺口，注入 -D/env 无法补齐'}
    for item in unresolved:
        if item['local'] in curated:
            item['reason'] = curated[item['local']]
    seen = set()
    unresolved = [item for item in unresolved
                  if not (item['local'] in seen or seen.add(item['local']))]
    document = {'revision': 'java-serial-entries-v1',
                'source': {'locals': str(LOCALS.relative_to(TASK)),
                           'missingCases': str(MISSING.relative_to(TASK)),
                           'javaInputsVerifiedAgainst': 'full-evidence-locals.json[local].java_inputs'},
                'articleCases': len(articles),
                'entries': entries, 'mergedFiles': merged, 'unresolved': unresolved,
                'summary': {'entries': len(entries), 'cases': sum(item['cases'] for item in entries.values()),
                            'unresolvedLocals': len(unresolved),
                            'unresolvedCases': sum(item['cases'] for item in unresolved)}}
    return document


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='只比对现有映射表，不写入')
    options = parser.parse_args()
    document = build()
    text = json.dumps(document, ensure_ascii=False, indent=2) + '\n'
    if options.check:
        current = OUTPUT.read_text() if OUTPUT.is_file() else ''
        print(json.dumps({'upToDate': current == text, **document['summary']}, ensure_ascii=False))
        return 0 if current == text else 1
    OUTPUT.write_text(text)
    print(json.dumps(document['summary'], ensure_ascii=False))
    for item in document['unresolved']:
        print('JAVA-SERIAL-UNRESOLVED ' + item['local'] + '：' + item['reason'], file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
