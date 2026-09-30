#!/usr/bin/env python3
"""固定 BRC100ByteEncoding.test.ts 23 例的真实 API 入参、replacer holder 和原断言。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/BRC100ByteEncoding.test.ts'
JAVA_CLASS = 'com.metanet4j.bsv.wallet.BRC100ByteEncodingTest'
LOOP_METHOD = 'rejectsPrimitivesAndHostileRecordsWithoutThrowing'
LOOP_SITE = FILE + ':60:5:loop'


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
    mapping['siteReviews'] = [review for review in mapping['siteReviews']
                              if review['id'] in {site['id'] for site in file['sites']}]
    assert len(file['cases']) == len(mapping['cases']) == 23
    return catalog, file, mapping


def assertion_instances(mapped):
    sites = mapped['assertionIds']
    if mapped['java'][0]['name'] != LOOP_METHOD:
        return sites, {site: site for site in sites}
    assert len(sites) == 3
    identities = [f'{sites[ordinal]}#{index:03d}'
                  for index in range(1, 9) for ordinal in (0, 1)] + [sites[2]]
    return identities, {identity: sites[(position % 2) if position < 16 else 2]
                        for position, identity in enumerate(identities)}


def input_plan(raw, parity):
    _, file, mapping = source()
    observed, assertions = rows(raw), rows(parity)
    assert len(observed) == 57 and len(assertions) == 62
    by_test = {}
    for row in observed:
        assert row['method'] in ('brc100JsonReplacer', 'normalizeBRC100ByteArray', 'normalizeBRC100ByteFields', 'normalizeBRC100WalletByteFields', 'stringifyBRC100', 'toBRC100PortableByteArray')
        by_test.setdefault(row['test'], []).append(row)
    mapped = {case['id']: case for case in mapping['cases']}
    result = []
    for case in file['cases']:
        test = ' '.join(case['names'])
        calls = by_test[test]
        assert len([row for row in assertions if row['test'] == test]) == len(assertion_instances(mapped[case['id']])[0])
        java = mapped[case['id']]['java']
        assert len(java) == 1 and java[0]['className'] == JAVA_CLASS
        for index, row in enumerate(calls, 1):
            assert isinstance(row['line'], int) and row['line'] > 0
            call = {'method': row['method'], 'args': row['args']}
            if row['method'] == 'brc100JsonReplacer':
                assert 'holder' in row
                call['holder'] = row['holder']
            result.append({'caseId': case['id'],
                           'sampleId': f'{FILE}:{row["line"]}:{row["method"]}#{index:04d}',
                           'value': {'test': test, 'source': {'file': FILE, 'line': row['line'],
                                                            'occurrence': index},
                                     'preState': {'javaMethod': java[0]['name'], 'callIndex': index},
                                     'calls': [call]}})
    assert len(result) == 57
    return result


def prepare(args):
    catalog, file, mapping = source()
    inputs = input_plan(args.raw, args.parity)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    mapped = {case['id']: case for case in mapping['cases']}
    plan = {}
    for case in file['cases']:
        java_method = mapped[case['id']]['java'][0]['name']
        sample_ids = [row['sampleId'] for row in inputs if row['caseId'] == case['id']]
        identities, sites = assertion_instances(mapped[case['id']])
        plan[case['id']] = {'sampleIds': sample_ids, 'assertionIds': identities,
                            'assertionSites': sites,
                            'loopSamples': {LOOP_SITE: sample_ids[:16]} if java_method == LOOP_METHOD else {}}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', inputs)
    print(json.dumps({'cases': 23, 'inputSamples': 57, 'assertions': 62, 'output': str(folder)}))


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
    assert len(output) == 62
    return output


def emit_ts(args):
    planned = rows(args.plan)
    assert planned == input_plan(args.raw, args.parity), '固定 TS 本轮输入与运行前计划不同'
    assert args.side == 'ts' and args.run_id
    mapping = source()[2]
    write_rows(args.inputs, [dict(item, runId=args.run_id, side='ts') for item in planned])
    write_rows(args.assertions, assertions_for('ts', args.parity, mapping, args.run_id))


def emit_java(args):
    assert args.side == 'java' and args.run_id
    write_rows(args.assertions, assertions_for('java', args.parity, source()[2], args.run_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts', 'emit-java'))
    for name in ('raw', 'parity', 'output', 'plan', 'side', 'run-id', 'inputs', 'assertions'):
        parser.add_argument('--' + name, required=name == 'parity')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts, 'emit-java': emit_java}[args.action](args)
