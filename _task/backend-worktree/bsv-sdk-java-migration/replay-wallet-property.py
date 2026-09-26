#!/usr/bin/env python3
"""从固定 BRC-100 fast-check predicate 实际输入生成 300×2 轮重放计划。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/BRC100ByteEncoding.property.test.ts'
TESTS = {
    'BRC-100 JSON compatibility properties preserves every ordinary JSON value exactly': 21,
    'BRC-100 JSON compatibility properties serializes actual typed arrays portably without reinterpreting adjacent JSON': 32,
}


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def source():
    catalog = read(TASK / 'module-tests.json')
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    assert len(file['cases']) == 2 and {' '.join(c['names']) for c in file['cases']} == set(TESTS)
    return catalog, file


def site(test):
    return f'{FILE}:{TESTS[test]}:{9 if TESTS[test] == 21 else 11}:assertion'


def sample_id(test, index):
    return site(test) + f'#{index:04d}'


def capture(raw, meta, assertions):
    entries, details, checks = rows(raw), read(meta), rows(assertions)
    config = details.get('configuration')
    assert config == {'numRuns': 300, 'seed': 20260926}, '原 fast-check 次数、seed 或 path 变化'
    assert details.get('fastCheckVersion') == '4.9.0', '原 fast-check 版本变化'
    assert len(entries) == len(checks) == 600 and len(details['runs']) == 2
    for run in details['runs']:
        assert run['test'] in TESTS and run['calls'] == 300 and run['status'] == 'passed'
        assert run['firstFailure'] is None and run['shrinkCalls'] == 0
    for test in TESTS:
        actual = [entry for entry in entries if entry['test'] == test]
        observed = [entry for entry in checks if entry['test'] == test]
        assert len(actual) == len(observed) == 300
        for index, (entry, check) in enumerate(zip(actual, observed), 1):
            assert entry['index'] == check['index'] == index and entry['phase'] == 'generate'
            assert len(entry['inputs']) == (1 if TESTS[test] == 21 else 2)
            assert check['matcher'] == 'toBe' and check['negated'] is False and check['pass'] is True
            assert check['actual'] == check['expected'] and check['actual']['type'] == 'string'
    return entries, config, checks


def planned(raw, meta, assertions):
    _, file = source()
    entries, config, _ = capture(raw, meta, assertions)
    by_test = {test: [item for item in entries if item['test'] == test] for test in TESTS}
    return [{'caseId': case['id'], 'sampleId': sample_id(test, entry['index']),
             'value': {'test': test, 'source': {'file': FILE, 'line': TESTS[test], 'occurrence': 1},
                       'preState': {'caseOccurrence': 1, 'fastCheck': config,
                                    'index': entry['index'], 'phase': entry['phase']},
                       'inputs': entry['inputs']}}
            for case in file['cases'] for test in [' '.join(case['names'])] for entry in by_test[test]]


def prepare(args):
    catalog, file = source()
    actual = planned(args.raw, args.meta, args.parity)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in file['cases']}
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in ids]
    mapping['siteReviews'] = [review for review in mapping['siteReviews']
                              if review['id'] in {item['id'] for item in file['sites']}]
    assert len(mapping['cases']) == 2
    assert all(case['assertionIds'] == [site(' '.join(next(source_case for source_case in file['cases']
                                             if source_case['id'] == case['id'])['names']))]
               for case in mapping['cases'])
    plan = {}
    for case in file['cases']:
        test = ' '.join(case['names'])
        ids_for_case = [row['sampleId'] for row in actual if row['caseId'] == case['id']]
        plan[case['id']] = {'sampleIds': ids_for_case, 'assertionIds': ids_for_case,
                            'assertionSites': {identity: site(test) for identity in ids_for_case},
                            'loopSamples': {}}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', actual)
    print(json.dumps({'cases': 2, 'samples': len(actual), 'output': str(folder)}))


def emit_ts(args):
    actual = planned(args.raw, args.meta, args.parity)
    assert actual == rows(args.plan), '本轮固定 TS 生成样本与输入计划不同'
    assert args.side == 'ts' and args.run_id
    checks = capture(args.raw, args.meta, args.parity)[2]
    grouped = {test: [item for item in checks if item['test'] == test] for test in TESTS}
    write_rows(args.inputs, [dict(row, runId=args.run_id, side='ts') for row in actual])
    write_rows(args.assertions, [
        {'runId': args.run_id, 'side': 'ts', 'caseId': row['caseId'], 'assertionId': row['sampleId'],
         'value': {'kind': 'assertion', 'matcher': 'toBe', 'negated': False,
                   'actual': grouped[row['value']['test']][row['value']['preState']['index'] - 1]['actual'],
                   'expected': grouped[row['value']['test']][row['value']['preState']['index'] - 1]['expected'],
                   'pass': True}}
        for row in actual])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts'))
    parser.add_argument('--raw', required=True)
    parser.add_argument('--meta', required=True)
    parser.add_argument('--parity', required=True)
    parser.add_argument('--output')
    parser.add_argument('--plan')
    parser.add_argument('--side')
    parser.add_argument('--run-id')
    parser.add_argument('--inputs')
    parser.add_argument('--assertions')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts}[args.action](args)
