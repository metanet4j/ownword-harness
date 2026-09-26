#!/usr/bin/env python3
"""把固定 WriterUint8Array 原测试的真实入口调用冻结为局部输入计划。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/primitives/__tests/WriterUint8Array.test.ts'
JAVA = 'com.metanet4j.bsv.primitives.WriterUint8ArrayTest'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def identity(row):
    return {key: row[key] for key in ('test', 'source', 'receiverId', 'className', 'method', 'args', 'preState')}


def freeze(args):
    full = read(TASK / 'module-tests.json')
    source = next(file for file in full['files'] if file['path'] == FILE)
    catalog = {**full, 'files': [source], 'partialImplementationOnly': True}
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in source['cases']}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(mapping_cases) == len(ids) == 26, 'WriterUint8Array 冻结映射必须是原 26 例')
    mapping = {**all_mapping, 'cases': mapping_cases}
    cases = {(' '.join(case['names']), case['occurrence']): case for case in source['cases']}
    mapped = {case['id']: case for case in mapping_cases}
    grouped = defaultdict(list)
    seen_sequences = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == FILE, '输入含范围外固定 TS 文件')
        key = (row['test'], row['occurrence'])
        require(key in cases, '输入含范围外固定 TS 用例')
        seen_sequences[key] += 1
        require(row['sequence'] == seen_sequences[key], '固定 TS 事件序号不连续')
        case = cases[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == JAVA, 'Java 用例映射不唯一')
        sample = f"{FILE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, '固定 TS 26 例未全部触达 API 入口')
    require(sum(map(len, grouped.values())) == 92, '固定 TS API 入口数偏离 92')
    plan = {}
    replay = []
    for case in source['cases']:
        case_id = case['id']
        events = grouped[case_id]
        assertion_ids = mapped[case_id]['assertionIds']
        plan[case_id] = {'sampleIds': [event['sampleId'] for event in events],
                         'assertionIds': assertion_ids,
                         'assertionSites': {site: site for site in assertion_ids},
                         'loopSamples': {}}
        replay.extend(events)
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=False) + '\n' for event in replay))
    print(json.dumps({'cases': len(ids), 'events': len(replay), 'assertionSites': sum(
        len(case['assertionIds']) for case in plan.values())}))


def emit(args):
    planned = rows(args.replay)
    fresh = rows(args.raw)
    by_key = {(event['value']['test'], event['value']['source']['file'],
               event['value']['source']['line'], event['value']['method'],
               event['sampleId'].split('#')[-1]): event for event in planned}
    require(len(by_key) == len(planned) == len(fresh), '固定 TS 输入数与计划不同')
    observed = []
    for row in fresh:
        key = (row['test'], row['source']['file'], row['source']['line'],
               row['method'], f"{row['sequence']:04d}")
        event = by_key.get(key)
        require(event is not None and identity(row) == event['value'],
                '本轮固定 TS 实际输入与冻结语料不同')
        observed.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                         'caseId': event['caseId'], 'sampleId': event['sampleId'],
                         'value': identity(row)})
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in observed))
    print(json.dumps({'side': 'ts', 'cases': 26, 'events': len(observed)}))


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
