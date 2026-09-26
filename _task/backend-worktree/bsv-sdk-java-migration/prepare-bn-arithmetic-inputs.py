#!/usr/bin/env python3
"""依据固定 BigNumber 源码与完整入口轨迹生成计划；不读取 TS actual 结果。"""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
VARIANTS = {
    'arithmetic': ('src/primitives/__tests/BigNumber.arithmatic.test.ts', 52, 1178, 176),
    'binary': ('src/primitives/__tests/BigNumber.binary.test.ts', 20, 854, 521),
    'serializers': ('src/primitives/__tests/BigNumber.serializers.test.ts', 16, 106, 55),
}
BINARY_ITERATIONS = {92: 8 + 256, 96: 2, 112: int('23478905234580795234378912401239784125643978256123048348957342').bit_length()}
# 原源码四处循环的控制规模，固定全部迭代和方法调用次数。
LOOPS = {'addNumbers': (13, 'add', 258), 'addHandlesCarryInPlace': (24, 'iadd', 257),
         'mulNumbersOfDifferentSigns': (192, 'ishln', 4), 'mulWithCarry': (206, 'mul', 4)}


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=VARIANTS, default='arithmetic')
    parser.add_argument('--raw', required=True)
    parser.add_argument('--directory', required=True)
    parser.add_argument('--replay', required=True)
    args = parser.parse_args()
    source_file, case_count, input_count, assertion_count = VARIANTS[args.variant]
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    file = next(f for f in catalog['files'] if f['path'] == source_file)
    all_mapping = json.loads((TASK / 'test-map.json').read_text())
    ids = {case['id'] for case in file['cases']}
    cases = {case['id']: case for case in all_mapping['cases'] if case['id'] in ids}
    names = {' '.join(case['names']): case['id'] for case in file['cases']}
    assert len(names) == len(cases) == case_count
    sites = {site['id'] for site in file['sites']}
    assertions = {site['line']: site['id'] for site in file['sites'] if site['kind'] == 'assertion'}
    groups = defaultdict(list)
    for line in Path(args.raw).read_text().splitlines():
        row = json.loads(line)
        assert row['source']['file'] == source_file
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
        if args.variant == 'arithmetic':
            assert set(occurrences.values()) == {expected_occurrences}
        elif method == 'supportTestSpecificBit':
            assert occurrences == {assertions[line]: count for line, count in BINARY_ITERATIONS.items()}
        else:
            assert set(occurrences.values()) == {1}
        if method in LOOPS:
            line, api, expected = LOOPS[method]
            assert sum(row.get('method') == api for row in rows) == expected
            loop = next(site for site in file['sites'] if site['kind'] == 'loop' and site['line'] == line)
            entry['loopSamples'][loop['id']] = entry['sampleIds'][:]
        if args.variant == 'binary' and method == 'supportTestSpecificBit':
            for line, call_lines, count in [(91, {92}, 264), (111, {111, 112}, 409)]:
                loop = next(site for site in file['sites'] if site['kind'] == 'loop' and site['line'] == line)
                samples = [f"call-{row['sequence']:04d}" for row in rows
                           if row['kind'] == 'call' and row['source']['line'] in call_lines]
                assert len(samples) == count
                entry['loopSamples'][loop['id']] = samples
        plan[key] = entry
    assert sum(len(x['sampleIds']) for x in plan.values()) == input_count
    assert sum(len(x['assertionIds']) for x in plan.values()) == assertion_count
    directory = Path(args.directory)
    write(directory / 'catalog.json', {**catalog, 'files': [file], 'partialImplementationOnly': True})
    write(directory / 'mapping.json', {**all_mapping, 'cases': list(cases.values()),
           'siteReviews': [site for site in all_mapping['siteReviews'] if site['id'] in sites]})
    write(directory / 'input-plan.json', plan)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in replay))
    print(json.dumps({'cases': case_count, 'inputs': input_count, 'assertions': assertion_count,
                      'loops': sum(len(entry['loopSamples']) for entry in plan.values())}))


if __name__ == '__main__':
    main()
