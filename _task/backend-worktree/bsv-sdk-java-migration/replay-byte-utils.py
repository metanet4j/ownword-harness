#!/usr/bin/env python3
"""固定 utils.test.ts 六个 base58 用例：从运行时 API 参数生成局部输入计划。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/primitives/__tests/utils.test.ts'
TEST = 'utils binary to base58 string round-trips boundary byte values'
SELECTED = {
    'utils binary to base58 string Converts to base58 as expected': (128, 1),
    'utils binary to base58 string Converts to base58 as expected with 1s': (134, 1),
    TEST: (142, 4),
}


def site(line):
    return f'{FILE}:{line}:7:assertion'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def source_cases():
    catalog = read(TASK / 'module-tests.json')
    source = next(file for file in catalog['files'] if file['path'] == FILE)
    cases = [case for case in source['cases'] if ' '.join(case['names']) in SELECTED]
    assert len(cases) == 6
    assert {site(line) for line, _ in SELECTED.values()} <= {item['id'] for item in source['sites'] if item['kind'] == 'assertion'}
    for name, (_, count) in SELECTED.items():
        assert sorted(case['occurrence'] for case in cases if ' '.join(case['names']) == name) == list(range(1, count + 1))
    return catalog, source, cases


def observations(path):
    actual = rows(path)
    assert len(actual) == 6, '选中的六个原用例必须全部运行'
    seen = set()
    for item in actual:
        test, line, occurrence = item['test'], item['line'], item['occurrence']
        assert test in SELECTED and line == SELECTED[test][0] and 1 <= occurrence <= SELECTED[test][1]
        assert item['matcher'] == 'toEqual' and (test, occurrence) not in seen
        seen.add((test, occurrence))
        calls = item['calls']
        assert [call['method'] for call in calls] == (['toBase58', 'fromBase58'] if test == TEST else ['toBase58'])
        assert all(len(call['args']) == 1 for call in calls) and calls[0]['args'][0]['type'] == 'array'
        if test == TEST:
            assert calls[1]['args'][0]['type'] == 'string'
            assert calls[0]['outcome']['value'] == calls[1]['args'][0], '原测试第二次调用不对应第一次实际返回'
        assert calls[-1]['outcome']['value'] == item['actual'], '原断言实参不对应最后一次实际返回'
    assert len(seen) == 6
    return actual


def planned(path):
    _, _, cases = source_cases()
    by_key = {(item['test'], item['occurrence']): item for item in observations(path)}
    return [{'caseId': case['id'], 'sampleId': site(SELECTED[' '.join(case['names'])][0]),
             'value': {'test': ' '.join(case['names']), 'source': {'file': FILE,
                       'line': SELECTED[' '.join(case['names'])][0], 'occurrence': case['occurrence']},
                       'preState': {'caseOccurrence': case['occurrence'], 'priorSampleIds': []},
                       'calls': [{'method': call['method'], 'args': call['args']}
                                 for call in by_key[(' '.join(case['names']), case['occurrence'])]['calls']]}}
            for case in cases]


def prepare(args):
    catalog, source, cases = source_cases()
    plan_rows = planned(args.raw)
    case_ids = {case['id'] for case in cases}
    sites = {site(line) for line, _ in SELECTED.values()}
    sites.update({FILE + ':121:5:registration', FILE + ':132:5:registration', FILE + ':136:5:registration'})
    catalog['files'] = [dict(source, cases=cases, sites=[item for item in source['sites'] if item['id'] in sites])]
    catalog['partialImplementationOnly'] = True
    mapping = read(TASK / 'test-map.json')
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in case_ids]
    mapping['siteReviews'] = [review for review in mapping['siteReviews'] if review['id'] in sites]
    assert len(mapping['cases']) == 6
    assert all(case['assertionIds'] == [site(SELECTED[' '.join(next(c for c in cases if c['id'] == case['id'])['names'])][0])]
               for case in mapping['cases'])
    plan = {case['id']: {'sampleIds': [site(SELECTED[' '.join(case['names'])][0])],
                         'assertionIds': [site(SELECTED[' '.join(case['names'])][0])],
                         'assertionSites': {site(SELECTED[' '.join(case['names'])][0]):
                                            site(SELECTED[' '.join(case['names'])][0])},
                         'loopSamples': {}} for case in cases}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', plan_rows)
    print(json.dumps({'cases': len(cases), 'samples': len(plan_rows), 'scope': 'partial-file', 'output': str(folder)}))


def emit_ts(args):
    actual = planned(args.raw)
    raw = {(item['test'], item['occurrence']): item for item in observations(args.raw)}
    assert rows(args.plan) == actual, '本轮固定 TS 实际输入与运行前计划不同'
    assert args.side == 'ts' and args.run_id, '缺少本轮 TS 运行身份'
    write_rows(args.inputs, [dict(row, runId=args.run_id, side='ts') for row in actual])
    write_rows(args.assertions, [
        {'runId': args.run_id, 'side': 'ts', 'caseId': row['caseId'], 'assertionId': row['sampleId'],
         'value': {'kind': 'assertion', 'matcher': 'toEqual',
                   'actual': raw[(row['value']['test'], row['value']['source']['occurrence'])]['actual'],
                   'calls': [{'method': call['method'], 'outcome': call['outcome']}
                             for call in raw[(row['value']['test'], row['value']['source']['occurrence'])]['calls']]}}
        for row in actual])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts'))
    parser.add_argument('--raw', required=True)
    parser.add_argument('--output')
    parser.add_argument('--plan')
    parser.add_argument('--side')
    parser.add_argument('--run-id')
    parser.add_argument('--inputs')
    parser.add_argument('--assertions')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts}[args.action](args)
