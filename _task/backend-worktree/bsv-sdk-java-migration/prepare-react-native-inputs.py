#!/usr/bin/env python3
"""冻结固定 ReactNativeWebView.test.ts 全 25 例的真实窗口与公开入口。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/substrates/__tests/ReactNativeWebView.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.substrates.ReactNativeWebViewTest'


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
    source = next(file for file in full['files'] if file['path'] == FILE)
    cases = source['cases']
    require(len(cases) == 25, '固定 ReactNativeWebView 原用例不是 25 例')
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in cases}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(ids) == len(mapping_cases) == 25, 'ReactNativeWebView Java 用例映射不唯一')
    mapped = {case['id']: case for case in mapping_cases}
    reviews = [review for review in all_mapping['siteReviews']
               if review['id'] in {site['id'] for site in source['sites']}]
    require(len(reviews) == len(source['sites']), 'ReactNativeWebView 原站点审阅缺失')
    catalog = {**full, 'files': [source], 'partialImplementationOnly': True}
    mapping = {**all_mapping, 'cases': mapping_cases, 'siteReviews': reviews}
    by_source = {(' '.join(case['names']), case['occurrence']): case for case in cases}
    grouped = defaultdict(list)
    sequence = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == FILE, 'ReactNativeWebView 输入含其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_source, 'ReactNativeWebView 原测试身份未映射')
        sequence[key] += 1
        require(row['sequence'] == sequence[key], 'ReactNativeWebView 原入口顺序不连续')
        case = by_source[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == JAVA, 'ReactNativeWebView Java 身份不唯一')
        sample = f"{FILE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, 'ReactNativeWebView 原用例有公开入口未采集')
    require(sum(map(len, grouped.values())) == 88, 'ReactNativeWebView 固定原入口总数变化')
    plan = {}
    replay = []
    for case in cases:
        case_id = case['id']
        events = grouped[case_id]
        assertions = mapped[case_id]['assertionIds']
        require(assertions, 'ReactNativeWebView 原用例无断言映射')
        plan[case_id] = {'sampleIds': [event['sampleId'] for event in events],
                         'assertionIds': assertions,
                         'assertionSites': {site: site for site in assertions}, 'loopSamples': {}}
        replay.extend(events)
    require(sum(len(value['assertionIds']) for value in plan.values()) == 40,
            'ReactNativeWebView 原断言总数变化')
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=True) + '\n' for event in replay))
    print(json.dumps({'cases': len(cases), 'events': len(replay), 'assertions': 40}))


def emit(args):
    planned = rows(args.replay)
    by_key = {(event['value']['test'], event['value']['source']['line'],
               event['value']['method'], event['value']['preState']['priorEvents']): event
              for event in planned}
    require(len(by_key) == len(planned), 'ReactNativeWebView 输入计划入口重复')
    observed = []
    for row in rows(args.raw):
        key = (row['test'], row['source']['line'], row['method'], row['preState']['priorEvents'])
        event = by_key.get(key)
        require(event is not None and identity(row) == event['value'], 'ReactNativeWebView 本轮原输入与冻结计划不同')
        observed.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                         'caseId': event['caseId'], 'sampleId': event['sampleId'],
                         'value': identity(row)})
    require(len(observed) == len(planned), 'ReactNativeWebView 本轮原入口数量不同')
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=True) + '\n' for row in observed))
    print(json.dumps({'side': 'ts', 'events': len(observed)}))


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
