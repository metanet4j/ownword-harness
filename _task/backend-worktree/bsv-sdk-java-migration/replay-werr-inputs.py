#!/usr/bin/env python3
"""固定 WERR.test.ts 32 个构造器用例的真实输入和 40 条原断言重放计划。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/WERR.test.ts'


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
    assert len(file['cases']) == len(mapping['cases']) == 32
    return catalog, file, mapping


def input_plan(raw, parity):
    _, file, mapping = source()
    raw_rows, assertions = rows(raw), rows(parity)
    assert len(raw_rows) == 32 and len(assertions) == 40
    input_by_test = {row['test']: row for row in raw_rows}
    assert len(input_by_test) == 32
    mapped = {case['id']: case for case in mapping['cases']}
    result = []
    for case in file['cases']:
        test = ' '.join(case['names'])
        assert test in input_by_test
        observed = input_by_test[test]
        assert observed['method'] in ('WERR_REVIEW_ACTIONS', 'WERR_INSUFFICIENT_FUNDS', 'WERR_INVALID_PARAMETER')
        assert isinstance(observed['line'], int) and observed['line'] > 0
        checks = [row for row in assertions if row['test'] == test]
        assert len(checks) == len(mapped[case['id']]['assertionIds'])
        assert all(row['pass'] is True for row in checks)
        java = mapped[case['id']]['java']
        assert len(java) == 1 and java[0]['className'] == 'com.metanet4j.bsv.wallet.WERRTest'
        result.append({'caseId': case['id'], 'sampleId': FILE + f":{observed['line']}:constructor",
                       'value': {'test': test, 'source': {'file': FILE, 'line': observed['line'], 'occurrence': 1},
                                 'preState': {'caseOccurrence': 1, 'javaMethod': java[0]['name']},
                                 'calls': [{'method': observed['method'], 'args': observed['args']}]}})
    return result


def prepare(args):
    catalog, file, mapping = source()
    inputs = input_plan(args.raw, args.parity)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    by_case = {item['caseId']: item for item in inputs}
    mapped = {case['id']: case for case in mapping['cases']}
    plan = {case['id']: {'sampleIds': [by_case[case['id']]['sampleId']],
                         'assertionIds': mapped[case['id']]['assertionIds'],
                         'assertionSites': {identity: identity for identity in mapped[case['id']]['assertionIds']},
                         'loopSamples': {}} for case in file['cases']}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write_rows(folder / 'replay-inputs.jsonl', inputs)
    print(json.dumps({'cases': 32, 'inputSamples': len(inputs), 'assertions': 40, 'output': str(folder)}))


def assertions_for(side, raw, mapping, run_id):
    reports = rows(raw)
    by_method = {case['java'][0]['name']: case for case in mapping['cases']}
    frozen_file = next(file for file in read(TASK / 'module-tests.json')['files'] if file['path'] == FILE)
    by_test = {' '.join(case['names']): case for case in frozen_file['cases']}
    output = []
    positions = {}
    for item in reports:
        if side == 'ts':
            case = by_test[item['test']]
        else:
            case = by_method[item['method']]
            assert item['test'] == 'com.metanet4j.bsv.wallet.WERRTest#' + item['method']
        position = positions.get(case['id'], 0)
        positions[case['id']] = position + 1
        if side == 'java':
            assert item['index'] == position + 1
        identities = case['assertionIds'] if side == 'java' else \
            next(entry for entry in mapping['cases'] if entry['id'] == case['id'])['assertionIds']
        identity = identities[position]
        output.append({'runId': run_id, 'side': side, 'caseId': case['id'], 'assertionId': identity,
                       'value': {'matcher': item['matcher'], 'negated': item['negated'], 'actual': item['actual']}})
    assert len(output) == 40
    return output


def emit_ts(args):
    planned = rows(args.plan)
    assert planned == input_plan(args.raw, args.parity), '本轮固定 TS 构造器输入与运行前计划不同'
    assert args.side == 'ts' and args.run_id
    mapping = source()[2]
    write_rows(args.inputs, [dict(item, runId=args.run_id, side='ts') for item in planned])
    write_rows(args.assertions, assertions_for('ts', args.parity, mapping, args.run_id))


def emit_java(args):
    assert args.side == 'java' and args.run_id
    mapping = source()[2]
    write_rows(args.assertions, assertions_for('java', args.parity, mapping, args.run_id))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts', 'emit-java'))
    parser.add_argument('--raw')
    parser.add_argument('--parity', required=True)
    parser.add_argument('--output')
    parser.add_argument('--plan')
    parser.add_argument('--side')
    parser.add_argument('--run-id')
    parser.add_argument('--inputs')
    parser.add_argument('--assertions')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts, 'emit-java': emit_java}[args.action](args)
