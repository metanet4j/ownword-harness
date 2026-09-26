#!/usr/bin/env python3
"""依据固定算术源码与完整入口轨迹生成 52 例计划；不读取 TS actual 结果。"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/primitives/__tests/BigNumber.arithmatic.test.ts'
# 原源码四处循环的控制规模，固定全部迭代和方法调用次数。
LOOPS = {'addNumbers': (13, 'add', 258), 'addHandlesCarryInPlace': (24, 'iadd', 257),
         'mulNumbersOfDifferentSigns': (192, 'ishln', 4), 'mulWithCarry': (206, 'mul', 4)}


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--replay', required=True)
    args = parser.parse_args()
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    file = next(f for f in catalog['files'] if f['path'] == FILE)
    all_mapping = json.loads((TASK / 'test-map.json').read_text())
    ids = {case['id'] for case in file['cases']}
    cases = {case['id']: case for case in all_mapping['cases'] if case['id'] in ids}
    names = {' '.join(case['names']): case['id'] for case in file['cases']}
    assert len(names) == len(cases) == 52
    sites = {site['id'] for site in file['sites']}
    assertions = {site['line']: site['id'] for site in file['sites'] if site['kind'] == 'assertion'}
    groups = defaultdict(list)
    for line in Path(args.raw).read_text().splitlines():
        row = json.loads(line)
        assert row['source']['file'] == FILE
        groups[names[row['test']]].append(row)
    assert set(groups) == ids
    plan, replay = {}, []
    for case in file['cases']:
        key = case['id']
        rows = groups[key]
        method = cases[key]['java'][0]['name']
        assert [row['sequence'] for row in rows] == list(range(1, len(rows) + 1))
        entry = {'sampleIds': [], 'assertionIds': [], 'assertionSites': {}, 'loopSamples': {}}
        occurrences = Counter()
        for row in rows:
            event = {'caseId': key, 'javaMethod': method, 'value': row}
            if row['kind'] == 'call':
                sample_id = f"call-{row['sequence']:04d}"
                event['sampleId'] = sample_id
                entry['sampleIds'].append(sample_id)
            else:
                site = assertions[row['source']['line']]
                assert site in cases[key]['assertionIds']
                occurrences[site] += 1
                identity = site if occurrences[site] == 1 else f'{site}#{occurrences[site]}'
                event['assertionId'] = identity
                entry['assertionIds'].append(identity)
                entry['assertionSites'][identity] = site
            replay.append(event)
        expected_occurrences = 4 if method == 'mulNumbersOfDifferentSigns' else 1
        assert set(occurrences) == set(cases[key]['assertionIds'])
        assert set(occurrences.values()) == {expected_occurrences}
        if method in LOOPS:
            line, api, expected = LOOPS[method]
            assert sum(row.get('method') == api for row in rows) == expected
            loop = next(site for site in file['sites'] if site['kind'] == 'loop' and site['line'] == line)
            entry['loopSamples'][loop['id']] = entry['sampleIds'][:]
        plan[key] = entry
    assert sum(len(x['sampleIds']) for x in plan.values()) == 1178
    assert sum(len(x['assertionIds']) for x in plan.values()) == 176
    directory = Path(args.directory)
    write(directory / 'catalog.json', {**catalog, 'files': [file], 'partialImplementationOnly': True})
    write(directory / 'mapping.json', {**all_mapping, 'cases': list(cases.values()),
           'siteReviews': [site for site in all_mapping['siteReviews'] if site['id'] in sites]})
    write(directory / 'input-plan.json', plan)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in replay))
    print(json.dumps({'cases': 52, 'inputs': 1178, 'assertions': 176, 'loops': 4}))


if __name__ == '__main__':
    main()
