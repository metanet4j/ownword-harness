#!/usr/bin/env python3
"""固定 WalletError.test.ts 的 39 例公开入口输入及 79 条原断言。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/WalletError.test.ts'
JAVA_CLASS = 'com.metanet4j.bsv.wallet.WalletErrorTest'
LOOP_METHOD = 'allCodesFitUint8'
LOOP_SITE = FILE + ':97:7:loop'


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
    mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in file['cases']}
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in ids]
    site_ids = {site['id'] for site in file['sites']}
    mapping['siteReviews'] = [review for review in mapping['siteReviews'] if review['id'] in site_ids]
    assert len(file['cases']) == len(mapping['cases']) == 39
    return catalog, file, mapping


def assertion_instances(mapped):
    sites = mapped['assertionIds']
    if mapped['java'][0]['name'] != LOOP_METHOD:
        return sites, {site: site for site in sites}
    assert len(sites) == 2
    identities = [f'{sites[ordinal]}#{index:03d}' for index in range(1, 8) for ordinal in (0, 1)]
    return identities, {identity: sites[position % 2] for position, identity in enumerate(identities)}


def input_plan(raw, parity):
    _, file, mapping = source()
    observed, assertions = rows(raw), rows(parity)
    assert len(observed) == 54 and len(assertions) == 79
    by_test = {}
    for row in observed:
        assert row['method'] in ('WalletError', 'unknownToJson', 'walletErrors.get')
        by_test.setdefault(row['test'], []).append(row)
    mapped = {case['id']: case for case in mapping['cases']}
    assert len(by_test) == 39
    result = []
    for case in file['cases']:
        test = ' '.join(case['names'])
        calls = by_test[test]
        checks = [row for row in assertions if row['test'] == test]
        assert len(checks) == len(assertion_instances(mapped[case['id']])[0])
        assert all(row['pass'] is True for row in checks)
        java = mapped[case['id']]['java']
        assert len(java) == 1 and java[0]['className'] == JAVA_CLASS
        for index, row in enumerate(calls, 1):
            assert isinstance(row['line'], int) and row['line'] > 0
            result.append({'caseId': case['id'],
                           'sampleId': f'{FILE}:{row["line"]}:{row["method"]}#{index:04d}',
                           'value': {'test': test, 'source': {'file': FILE, 'line': row['line'],
                                                            'occurrence': index},
                                     'preState': {'javaMethod': java[0]['name'], 'callIndex': index},
                                     'calls': [{'method': row['method'], 'args': row['args']}]}})
    assert len(result) == 54
    return result


def prepare(args):
    catalog, file, mapping = source()
    inputs = input_plan(args.raw, args.parity)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    mapped = {case['id']: case for case in mapping['cases']}
    plan = {}
    for case in file['cases']:
        method = mapped[case['id']]['java'][0]['name']
        sample_ids = [row['sampleId'] for row in inputs if row['caseId'] == case['id']]
        identities, sites = assertion_instances(mapped[case['id']])
        plan[case['id']] = {'sampleIds': sample_ids, 'assertionIds': identities,
                            'assertionSites': sites,
                            'loopSamples': {LOOP_SITE: sample_ids} if method == LOOP_METHOD else {}}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', inputs)
    print(json.dumps({'cases': 39, 'inputSamples': 54, 'assertions': 79, 'output': str(folder)}))


def assertions_for(side, raw, mapping, run_id):
    reports = rows(raw)
    by_method = {case['java'][0]['name']: case for case in mapping['cases']}
    file = next(item for item in read(TASK / 'module-tests.json')['files'] if item['path'] == FILE)
    by_test = {' '.join(case['names']): case for case in file['cases']}
    mapped = {case['id']: case for case in mapping['cases']}
    output, positions = [], {}
    for item in reports:
        case = by_test[item['test']] if side == 'ts' else by_method[item['method']]
        if side == 'java':
            assert item['test'] == JAVA_CLASS + '#' + item['method']
        position = positions.get(case['id'], 0)
        positions[case['id']] = position + 1
        if side == 'java':
            assert item['index'] == position + 1
        identity = assertion_instances(mapped[case['id']])[0][position]
        output.append({'runId': run_id, 'side': side, 'caseId': case['id'], 'assertionId': identity,
                       'value': {'matcher': item['matcher'], 'negated': item['negated'], 'actual': item['actual']}})
    assert len(output) == 79
    return output


def emit_ts(args):
    planned = rows(args.plan)
    assert planned == input_plan(args.raw, args.parity), '固定 TS 本轮输入与运行前计划不同'
    write_rows(args.inputs, [dict(item, runId=args.run_id, side='ts') for item in planned])
    write_rows(args.assertions, assertions_for('ts', args.parity, source()[2], args.run_id))


def emit_java(args):
    write_rows(args.assertions, assertions_for('java', args.parity, source()[2], args.run_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts', 'emit-java'))
    for name in ('raw', 'parity', 'output', 'plan', 'side', 'run-id', 'inputs', 'assertions'):
        parser.add_argument('--' + name, required=name == 'parity')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts, 'emit-java': emit_java}[args.action](args)
