#!/usr/bin/env python3
"""从固定 TS API 参数轨迹生成输入计划，并核对本轮 TS/Java 逐样本重放。"""
import argparse
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILES = {'hex': 'src/primitives/__tests/hex.test.ts',
         'bn': 'src/primitives/__tests/BigNumber.constructor.test.ts'}


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def samples(kind, source):
    file = next(item for item in read(TASK / 'module-tests.json')['files'] if item['path'] == FILES[kind])
    names = {' '.join(case['names']): case for case in file['cases']}
    by_case = {case['id']: [] for case in file['cases']}
    for raw in rows(source):
        case = names[raw['test']]
        line, occurrence = raw['line'], raw.get('occurrence', 1)
        site = next(site['id'] for site in file['sites'] if site['kind'] == 'assertion' and site['line'] == line)
        assertion = site + (f'#{occurrence}' if kind == 'bn' and line == 139 else '')
        calls = ([{'method': raw['method'], 'args': [raw['input']]}] if kind == 'hex' else
                 [{'method': call['method'], 'args': call['args']} for call in raw['calls']])
        previous = [item['sampleId'] for item in by_case[case['id']]]
        by_case[case['id']].append({'caseId': case['id'], 'sampleId': assertion,
                                    'value': {'test': raw['test'], 'source': {'file': FILES[kind], 'line': line,
                                            'occurrence': occurrence},
                                            'preState': {'caseOccurrence': case['occurrence'],
                                                         'priorSampleIds': previous}, 'calls': calls}})
    return file, by_case


def prepare(args):
    file, by_case = samples(args.kind, args.raw)
    catalog = read(TASK / 'module-tests.json')
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    mapping = read(TASK / 'test-map.json')
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in by_case]
    mapping['siteReviews'] = [site for site in mapping['siteReviews']
                              if site['id'] in {item['id'] for item in file['sites']}]
    plan = {}
    for case in mapping['cases']:
        current = by_case[case['id']]
        ids = [item['sampleId'] for item in current]
        assert ids == case['assertionIds'], case['id']
        plan[case['id']] = {'sampleIds': ids, 'assertionIds': ids,
                            'assertionSites': {identity: identity.split('#')[0] for identity in ids},
                            'loopSamples': {}}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', [item for case in mapping['cases'] for item in by_case[case['id']]])
    print(json.dumps({'cases': len(by_case), 'samples': sum(map(len, by_case.values())), 'output': str(folder)}))


def emit_ts(args):
    file, by_case = samples(args.kind, args.raw)
    planned = rows(args.plan)
    actual = [item for case in file['cases'] for item in by_case[case['id']]]
    assert planned == actual, '本轮 TS 实际输入与运行前计划不同'
    run_id = args.run_id
    assert run_id and args.side == 'ts'
    write_rows(args.inputs, [dict(item, runId=run_id, side='ts') for item in actual])
    raw = rows(args.raw)
    names = {' '.join(case['names']): case['id'] for case in file['cases']}
    write_rows(args.assertions, [{'runId': run_id, 'side': 'ts', 'caseId': names[item['test']],
              'assertionId': actual_site(file, item, args.kind), 'value': item['outcome'] if args.kind == 'hex'
              else {'calls': [{'method': call['method'], 'outcome': call['outcome']} for call in item['calls']],
                    'matcher': item['matcher'], 'actual': item['actual']}} for item in raw])


def actual_site(file, item, kind):
    site = next(site['id'] for site in file['sites'] if site['kind'] == 'assertion' and site['line'] == item['line'])
    return site + (f"#{item['occurrence']}" if kind == 'bn' and item['line'] == 139 else '')


def verify(args):
    plan = rows(args.plan)
    ts, java = rows(args.ts), rows(args.java)
    key = lambda row: (row['caseId'], row['sampleId'])
    planned = {key(row): row['value'] for row in plan}
    assert len(planned) == len(plan) == len(ts) == len(java), '输入样本数量或唯一性错误'
    assert {key(row): row['value'] for row in ts} == planned, 'TS 实际输入不同于计划'
    assert {key(row): row['value'] for row in java} == planned, 'Java 实际输入不同于 TS 计划'
    for name, records in [('ts', ts), ('java', java)]:
        hashes = {key(row): hashlib.sha256(json.dumps(row['value'], sort_keys=True, ensure_ascii=False,
                    separators=(',', ':')).encode()).hexdigest() for row in records}
        assert len(hashes) == len(plan), name
    print(json.dumps({'samples': len(plan), 'tsJavaInputExact': True}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts', 'verify'))
    parser.add_argument('--kind', choices=FILES)
    parser.add_argument('--raw')
    parser.add_argument('--output')
    parser.add_argument('--plan')
    parser.add_argument('--run-id')
    parser.add_argument('--side')
    parser.add_argument('--inputs')
    parser.add_argument('--assertions')
    parser.add_argument('--ts')
    parser.add_argument('--java')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts, 'verify': verify}[args.action](args)
