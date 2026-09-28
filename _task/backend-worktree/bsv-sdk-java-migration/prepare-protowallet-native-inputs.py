#!/usr/bin/env python3
"""冻结 ProtoWallet.native-hash 原 Jest 的签名与验签入口。"""
import argparse
import importlib.util
from collections import defaultdict
import json
import os
import re
from pathlib import Path

TASK = Path(__file__).resolve().parent
UPSTREAM = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
FILE = 'src/wallet/__tests/ProtoWallet.native-hash.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.ProtoWalletNativeHashTest'
CASES = 6
EVENTS = 19


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def test_spans():
    """按原测试源码的 it(...) 行范围确定每个用例覆盖的循环站点；同名用例按出现次序区分。"""
    lines = (UPSTREAM / FILE).read_text().splitlines()
    marks = []
    for number, text in enumerate(lines, 1):
        # 兼配 it.each([...])(...) 形式：名称仍在 it 之后的第一个字符串字面量。
        match = (re.search(r"\bit(?:\.each\([^)]*\))?\(\s*'([^']*)'", text)
                 or re.search(r'\bit(?:\.each\([^)]*\))?\(\s*"([^"]*)"', text))
        if match:
            marks.append((number, match.group(1)))
    spans = {}
    for index, (line, name) in enumerate(marks):
        end = marks[index + 1][0] - 1 if index + 1 < len(marks) else len(lines)
        spans.setdefault(name, []).append((line, end))
    return spans


def test_span(case):
    name, occurrence = case['names'][-1], case['occurrence']
    if name not in SPANS:
        # it.each 模板名带 %s 等占位符：把模板转成正则匹配展开后的用例名。
        matches = []
        for template, spans in SPANS.items():
            if '%' not in template:
                continue
            pattern = re.compile('^' + re.escape(template).replace('%s', '.*').replace('%i', '.*')
                                 .replace('%p', '.*').replace('%j', '.*') + '$')
            if pattern.match(name):
                matches.extend(spans)
        require(len(matches) == 1, '找不到原测试用例行范围：' + name)
        return matches[0]
    require(len(SPANS[name]) >= occurrence, '找不到原测试用例行范围：' + name)
    return SPANS[name][occurrence - 1]


def identity(row):
    return {key: row[key] for key in ('test', 'source', 'className', 'method', 'args', 'preState')}


def freeze(args):
    full = read(TASK / 'module-tests.json')
    source = next(item for item in full['files'] if item['path'] == FILE)
    cases = source['cases']
    require(len(cases) == CASES, f'固定 ProtoWallet 原用例不是 {CASES} 例')
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in cases}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(ids) == len(mapping_cases) == CASES, 'ProtoWallet Java 用例映射不唯一')
    mapped = {case['id']: case for case in mapping_cases}
    site_ids = {site['id'] for site in source['sites']}
    reviews = [item for item in all_mapping['siteReviews'] if item['id'] in site_ids]
    require(len(reviews) == len(source['sites']), 'ProtoWallet 原站点审阅缺失')
    catalog = {**full, 'files': [source], 'partialImplementationOnly': True}
    mapping = {**all_mapping, 'cases': mapping_cases, 'siteReviews': reviews}
    global SPANS
    SPANS = test_spans()
    loop_lines = {site['id']: int(site['id'].split(':')[1])
                  for site in source['sites'] if site['kind'] == 'loop'}
    covered_loops = set()
    by_source = {(' '.join(case['names']), case['occurrence']): case for case in cases}
    grouped = defaultdict(list)
    sequence = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == FILE, 'ProtoWallet 输入含其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_source, 'ProtoWallet 原测试身份未映射')
        sequence[key] += 1
        require(row['sequence'] == sequence[key], 'ProtoWallet 原入口顺序不连续')
        case = by_source[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == JAVA, 'ProtoWallet Java 身份不唯一')
        sample = f"{FILE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, 'ProtoWallet 原用例有入口未采集')
    require(sum(map(len, grouped.values())) == EVENTS, f'ProtoWallet 固定原入口总数应为 {EVENTS}')
    spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    plan = {}
    replay = []
    for case in cases:
        case_id = case['id']
        events = grouped[case_id]
        assertions = mapped[case_id]['assertionIds']
        require(assertions, 'ProtoWallet 原用例无断言映射')
        entry = {'sampleIds': [event['sampleId'] for event in events],
                 'assertionIds': assertions,
                 'assertionSites': {site: site for site in assertions}, 'loopSamples': {}}
        # 循环站点必须登记驱动它的样本：优先取同源码行的入口，其次取所属用例首个入口
        # （如原测试在 mock 内部忙等的 while 循环，没有自己的边界入口）。
        span = test_span(case)
        for site, line in loop_lines.items():
            if not span[0] <= line <= span[1]:
                continue
            # 循环体入口的调用行紧跟循环头，取循环头之后最早那一行的全部入口。
            after = sorted({event['value']['source']['line'] for event in events
                            if event['value']['source']['line'] > line})
            body = [event['sampleId'] for event in events
                    if after and event['value']['source']['line'] == after[0]]
            entry['loopSamples'][site] = body or [events[0]['sampleId']]
            covered_loops.add(site)
        fixed = audit.semantic_specs(case_id)
        if fixed:
            entry['comparisonRules'] = {identity: fixed[entry['assertionSites'][identity]][0]
                                        for identity in assertions
                                        if entry['assertionSites'][identity] in fixed}
        plan[case_id] = entry
        replay.extend(events)
    require(covered_loops == set(loop_lines), 'ProtoWallet 循环站点未被用例覆盖')
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=True) + '\n' for event in replay))
    print(json.dumps({'cases': len(cases), 'events': len(replay),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values())}))


def emit(args):
    planned = rows(args.replay)
    observed = rows(args.raw)
    require(len(observed) == len(planned), 'ProtoWallet 本轮原入口数量不同')
    result = []
    for actual, event in zip(observed, planned):
        require(identity(actual) == event['value'], 'ProtoWallet 本轮原输入与冻结计划不同')
        result.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                       'caseId': event['caseId'], 'sampleId': event['sampleId'],
                       'value': identity(actual)})
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=True) + '\n' for row in result))
    print(json.dumps({'side': 'ts', 'events': len(result)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    freeze_parser = sub.add_parser('freeze')
    freeze_parser.add_argument('--raw', required=True)
    for option in ('catalog', 'mapping', 'input-plan', 'replay'):
        freeze_parser.add_argument('--' + option, required=True)
    emit_parser = sub.add_parser('emit-ts')
    for option in ('raw', 'replay', 'output'):
        emit_parser.add_argument('--' + option, required=True)
    args = parser.parse_args()
    (freeze if args.mode == 'freeze' else emit)(args)


if __name__ == '__main__':
    main()
