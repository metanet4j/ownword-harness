#!/usr/bin/env python3
"""依据固定 DRBG 源码、固定 NIST 向量与原入口轨迹生成计划；不导出 TS 结果作为重放输入。"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
SOURCE_FILE = 'src/primitives/__tests/DRBG.test.ts'
VECTORS_FILE = 'src/primitives/__tests/DRBG.vectors.ts'
SOURCE_SHA = '8359f4f5fa218206c6be2ecff259a61d290ed989d14ca9d991d5fa4a53b312e9'
VECTORS_SHA = 'be1f1971750f3e4ac99bff7a18dce3f3f39ec263d35431eb9c6c5e692fb921b4'
UPSTREAM = 'f999e0c1aad9a7afd0cbadaaf23841d049af9d5a'
GUARD = SOURCE_FILE + ':15:9:conditional'
THROW_SITE = SOURCE_FILE + ':16:11:assertion'
UNEXECUTED = (SOURCE_FILE + ':26:9:assertion', SOURCE_FILE + ':27:9:assertion')
RULE = 'drbg-nist-invalid-input-v1'
NIST_PREFIX = 'handlesNistStyleVector'
LOOP_SITE = SOURCE_FILE + ':164:7:loop'
LOOP_METHODS = {'reproducesRfc6979KForSample', 'reproducesRfc6979KForTest',
                'isDeterministicForSameRfc6979KeyAndMessage'}
CASE_COUNT, SAMPLE_COUNT, ASSERTION_COUNT, BRANCH_COUNT = 29, 72, 30, 15


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--assertions', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--replay', required=True)
    parser.add_argument('--plan', required=True)
    args = parser.parse_args()
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    assert catalog['upstreamCommit'] == UPSTREAM
    assert catalog['moduleFiles'].get(VECTORS_FILE) == VECTORS_SHA
    file = next(f for f in catalog['files'] if f['path'] == SOURCE_FILE)
    assert file['sha256'] == SOURCE_SHA
    all_mapping = json.loads((TASK / 'test-map.json').read_text())
    ids = {case['id'] for case in file['cases']}
    cases = {case['id']: case for case in all_mapping['cases'] if case['id'] in ids}
    names = {' '.join(case['names']): case['id'] for case in file['cases']}
    assert len(names) == len(cases) == CASE_COUNT
    sites = {site['id'] for site in file['sites']}
    assert GUARD in {site['id'] for site in file['sites'] if site['kind'] == 'conditional'}
    groups = defaultdict(list)
    for line in Path(args.raw).read_text().splitlines():
        row = json.loads(line)
        groups[names[row['test']]].append(row)
    assert set(groups) == ids
    observed = defaultdict(list)
    for line in Path(args.assertions).read_text().splitlines():
        row = json.loads(line)
        observed[names[row['test']]].append(row)
    assert set(observed) == ids
    plan, replay = {}, []
    branches = 0
    for case in file['cases']:
        key = case['id']
        rows = groups[key]
        method = cases[key]['java'][0]['name']
        assert [row['sequence'] for row in rows] == list(range(1, len(rows) + 1))
        entry = {'sampleIds': [], 'assertionIds': [], 'assertionSites': {}, 'loopSamples': {}}
        branch_sample = None
        for row in rows:
            value = row['value']
            prefix = 'branch' if value['kind'] == 'branch' else 'call'
            sample_id = f"{prefix}-{row['sequence']:04d}"
            entry['sampleIds'].append(sample_id)
            replay.append({'caseId': key, 'javaMethod': method, 'value': value, 'sampleId': sample_id})
            if prefix == 'branch':
                branches += 1
                assert set(value) == {'kind', 'guardSiteId', 'entropyHex', 'nonceHex', 'taken', 'controlFlow'}
                assert value['guardSiteId'] == GUARD and value['taken'] is True and value['controlFlow'] == 'return'
                branch_sample = sample_id
        expected = cases[key]['assertionIds']
        assert expected, key
        assert len(observed[key]) == len(expected), key
        entry['assertionIds'] = list(expected)
        entry['assertionSites'] = {identity: identity for identity in expected}
        if method.startswith(NIST_PREFIX):
            assert expected == [THROW_SITE] and len(rows) == 2
            assert rows[1]['value']['method'] == 'DRBG.constructor'
            assert [row['matcher'] for row in observed[key]] == ['toThrow']
            assert branch_sample is not None
            entry['unexecutedSites'] = {site: {'ruleId': RULE, 'guardSiteId': GUARD, 'sampleId': branch_sample}
                                        for site in UNEXECUTED}
        else:
            assert branch_sample is None, key
        if method in LOOP_METHODS:
            assert LOOP_SITE in {site['id'] for site in file['sites'] if site['kind'] == 'loop'}
            constructor = next(row for row in rows
                               if row['value']['kind'] == 'call' and row['value']['method'] == 'DRBG.constructor')
            entry['loopSamples'][LOOP_SITE] = [f"call-{constructor['sequence']:04d}"]
        plan[key] = entry
    total_assertions = sum(len(entry['assertionIds']) for entry in plan.values())
    total_unexecuted = sum(len(entry['unexecutedSites']) for entry in plan.values() if 'unexecutedSites' in entry)
    assert sum(len(entry['sampleIds']) for entry in plan.values()) == SAMPLE_COUNT
    assert total_assertions == ASSERTION_COUNT
    assert branches == BRANCH_COUNT
    assert total_unexecuted == 2 * BRANCH_COUNT
    directory = Path(args.directory)
    write(directory / 'catalog.json', {**catalog, 'files': [file], 'partialImplementationOnly': True})
    write(directory / 'mapping.json', {**all_mapping, 'cases': list(cases.values()),
           'siteReviews': [site for site in all_mapping['siteReviews'] if site['id'] in sites]})
    write(directory / 'input-plan.json', plan)
    write(args.plan, plan)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in replay))
    print(json.dumps({'cases': CASE_COUNT, 'inputs': SAMPLE_COUNT, 'assertions': total_assertions,
                      'branches': branches, 'unexecuted': total_unexecuted}))


if __name__ == '__main__':
    main()
