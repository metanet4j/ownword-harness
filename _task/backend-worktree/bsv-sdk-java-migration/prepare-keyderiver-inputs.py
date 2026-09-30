#!/usr/bin/env python3
"""冻结 KeyDeriver 原 Jest 的真实构造与公开方法调用。"""
import argparse
import importlib.util
from collections import defaultdict
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/KeyDeriver.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.KeyDeriverTest'
CASES = 17
EVENTS = 49


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


def identity(row):
    return {key: row[key] for key in ('test', 'source', 'className', 'method', 'args', 'preState')}


def freeze(args):
    full = read(TASK / 'module-tests.json')
    source = next(item for item in full['files'] if item['path'] == FILE)
    cases = source['cases']
    require(len(cases) == CASES, f'固定 KeyDeriver 原用例不是 {CASES} 例')
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in cases}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(ids) == len(mapping_cases) == CASES, 'KeyDeriver Java 用例映射不唯一')
    mapped = {case['id']: case for case in mapping_cases}
    site_ids = {site['id'] for site in source['sites']}
    reviews = [item for item in all_mapping['siteReviews'] if item['id'] in site_ids]
    require(len(reviews) == len(source['sites']), 'KeyDeriver 原站点审阅缺失')
    catalog = {**full, 'files': [source], 'partialImplementationOnly': True}
    mapping = {**all_mapping, 'cases': mapping_cases, 'siteReviews': reviews}
    by_source = {(' '.join(case['names']), case['occurrence']): case for case in cases}
    grouped = defaultdict(list)
    sequence = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == FILE, 'KeyDeriver 输入含其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_source, 'KeyDeriver 原测试身份未映射')
        sequence[key] += 1
        require(row['sequence'] == sequence[key], 'KeyDeriver 原入口顺序不连续')
        case = by_source[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == JAVA, 'KeyDeriver Java 身份不唯一')
        sample = f"{FILE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, 'KeyDeriver 原用例有入口未采集')
    require(sum(map(len, grouped.values())) == EVENTS, f'KeyDeriver 固定原入口总数应为 {EVENTS}')
    spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    plan = {}
    replay = []
    for case in cases:
        case_id = case['id']
        events = grouped[case_id]
        assertions = mapped[case_id]['assertionIds']
        require(assertions, 'KeyDeriver 原用例无断言映射')
        entry = {'sampleIds': [event['sampleId'] for event in events],
                 'assertionIds': assertions,
                 'assertionSites': {site: site for site in assertions}, 'loopSamples': {}}
        fixed = audit.semantic_specs(case_id)
        if fixed:
            entry['comparisonRules'] = {identity: fixed[entry['assertionSites'][identity]][0]
                                        for identity in assertions
                                        if entry['assertionSites'][identity] in fixed}
        plan[case_id] = entry
        replay.extend(events)
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=True) + '\n' for event in replay))
    print(json.dumps({'cases': len(cases), 'events': len(replay),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values())}))


def emit(args):
    planned = rows(args.replay)
    observed = rows(args.raw)
    require(len(observed) == len(planned), 'KeyDeriver 本轮原入口数量不同')
    result = []
    for actual, event in zip(observed, planned):
        require(identity(actual) == event['value'], 'KeyDeriver 本轮原输入与冻结计划不同')
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
