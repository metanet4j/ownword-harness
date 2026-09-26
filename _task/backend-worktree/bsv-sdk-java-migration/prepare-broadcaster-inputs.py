#!/usr/bin/env python3
"""冻结固定 Broadcaster 原测试的守卫与接口属性输入、结果。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
SOURCE = 'src/transaction/__tests/Broadcaster.test.ts'
JAVA = 'com.metanet4j.bsv.transaction.BroadcasterTest'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(row):
    return {key: row[key] for key in ('test', 'source', 'method', 'args', 'result')}


def freeze(args):
    full = read(TASK / 'module-tests.json')
    source = next(file for file in full['files'] if file['path'] == SOURCE)
    require(len(source['cases']) == 11, '原测试用例数不同')
    catalog = {**full, 'files': [source], 'partialImplementationOnly': True}
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in source['cases']}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(mapping_cases) == len(ids), 'Java 映射用例数不同')
    sites = {site['id'] for site in source['sites']}
    reviews = [review for review in all_mapping['siteReviews'] if review['id'] in sites]
    require(len(reviews) == len(sites), '站点审阅缺失')
    mapping = {**all_mapping, 'cases': mapping_cases, 'siteReviews': reviews}
    cases = {(' '.join(case['names']), case['occurrence']): case for case in source['cases']}
    mapped = {case['id']: case for case in mapping_cases}
    grouped = defaultdict(list)
    sequence = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == SOURCE, '入口输入来自其他文件')
        require(row['method'] in ('isBroadcastResponse', 'isBroadcastFailure', 'interfaceProperty') and (isinstance(row['result'], bool) or row['method'] == 'interfaceProperty' and row['result'] is None), '守卫入口或结果不正确')
        key = (row['test'], row['occurrence'])
        require(key in cases, '入口输入来自未登记用例')
        sequence[key] += 1
        require(row['sequence'] == sequence[key], '入口顺序不连续')
        case = cases[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == JAVA, 'Java 用例未独立注册')
        sample = f"{SOURCE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, '固定 TS 原用例未全部触达守卫入口')
    require([len(grouped[case['id']]) for case in source['cases']] == [1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 4], '守卫入口实际调用数不同')
    plan, replay = {}, []
    for case in source['cases']:
        events = grouped[case['id']]
        assertion_ids = mapped[case['id']]['assertionIds']
        plan[case['id']] = {'sampleIds': [event['sampleId'] for event in events],
                            'assertionIds': assertion_ids,
                            'assertionSites': {site: site for site in assertion_ids},
                            'loopSamples': {}}
        replay.extend(events)
    require(sum(len(row['assertionIds']) for row in plan.values()) == 22, '原断言数不同')
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=False) + '\n' for event in replay))
    print(json.dumps({'cases': 11, 'events': 16, 'assertions': 22}))


def emit(args):
    planned, fresh = rows(args.replay), rows(args.raw)
    require(len(planned) == len(fresh) == 16, '本轮实际入口与属性读取数不同')
    by_test = defaultdict(list)
    for row in planned:
        by_test[row['value']['test']].append(row)
    seen = defaultdict(int)
    observed = []
    for row in fresh:
        test = row['test']
        index = seen[test]
        require(index < len(by_test[test]), '出现计划外实际入口')
        expected = by_test[test][index]
        require(identity(row) == expected['value'], '本轮固定 TS 实际输入或结果与冻结语料不同')
        observed.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                         'caseId': expected['caseId'], 'sampleId': expected['sampleId'],
                         'value': identity(row)})
        seen[test] += 1
    require(all(seen[test] == len(items) for test, items in by_test.items()), '固定 TS 守卫入口缺失')
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in observed))
    print(json.dumps({'side': 'ts', 'cases': 11, 'events': len(observed)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('freeze')
    p.add_argument('--raw', required=True)
    for key in ('catalog', 'mapping', 'input-plan', 'replay'):
        p.add_argument('--' + key, required=True)
    p = sub.add_parser('emit-ts')
    for key in ('raw', 'replay', 'output'):
        p.add_argument('--' + key, required=True)
    args = parser.parse_args()
    (freeze if args.mode == 'freeze' else emit)(args)


if __name__ == '__main__':
    main()
