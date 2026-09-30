#!/usr/bin/env python3
"""冻结 toOriginHeader 五个参数化原用例的实际调用。"""
import argparse
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
SOURCE = 'src/wallet/substrates/__tests/toOriginHeader.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.substrates.utils.ToOriginHeaderTest'


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def freeze(args):
    full = json.loads((TASK / 'module-tests.json').read_text())
    source = next(file for file in full['files'] if file['path'] == SOURCE)
    assert len(source['cases']) == 5
    mapping = json.loads((TASK / 'test-map.json').read_text())
    ids = {case['id'] for case in source['cases']}
    mapped = {case['id']: case for case in mapping['cases'] if case['id'] in ids}
    names = {' '.join(case['names']): case for case in source['cases']}
    assert len(mapped) == len(names) == 5
    events = {}
    for row in rows(args.raw):
        assert row['test'] in names and row['occurrence'] == row['sequence'] == 1
        assert row['source']['file'] == SOURCE and row['source']['line'] in (26, 31)
        assert row['method'] == 'toOriginHeader' and len(row['args']) == 2
        case = names[row['test']]
        assert case['id'] not in events
        events[case['id']] = row
    assert set(events) == ids
    plan, replay = {}, []
    for case in source['cases']:
        case_id = case['id']
        java = mapped[case_id]['java']
        assert len(java) == 1 and java[0]['className'] == JAVA
        assertion_ids = mapped[case_id]['assertionIds']
        assert len(assertion_ids) == 1
        sample = f'{SOURCE}:{events[case_id]["source"]["line"]}:call:case{case["occurrence"]}#{java[0]["name"]}'
        plan[case_id] = {'sampleIds': [sample], 'assertionIds': assertion_ids,
                         'assertionSites': {item: item for item in assertion_ids}, 'loopSamples': {}}
        replay.append({'caseId': case_id, 'sampleId': sample,
                       'javaMethod': java[0]['name'], 'value': events[case_id]})
    sites = {site['id'] for site in source['sites']}
    write(args.directory / 'catalog.json', dict(full, files=[source], partialImplementationOnly=True))
    write(args.directory / 'mapping.json', dict(mapping, cases=list(mapped.values()),
                                               siteReviews=[site for site in mapping['siteReviews'] if site['id'] in sites]))
    write(args.directory / 'input-plan.json', plan)
    args.replay.parent.mkdir(parents=True, exist_ok=True)
    args.replay.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in replay))
    print(json.dumps({'cases': 5, 'inputs': 5, 'assertions': 5}))


def emit(args):
    planned = {row['value']['test']: row for row in rows(args.replay)}
    observed = []
    for actual in rows(args.raw):
        assert actual['test'] in planned
        expected = planned.pop(actual['test'])
        assert actual == expected['value']
        observed.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                         'caseId': expected['caseId'], 'sampleId': expected['sampleId'], 'value': actual})
    assert not planned and len(observed) == 5
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in observed))
    print(json.dumps({'side': 'ts', 'cases': 5, 'inputs': 5}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('freeze')
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--replay', type=Path, required=True)
    p = sub.add_parser('emit-ts')
    p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--replay', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    (freeze if args.mode == 'freeze' else emit)(args)


if __name__ == '__main__':
    main()
