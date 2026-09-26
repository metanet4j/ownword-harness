#!/usr/bin/env python3
"""固定 Mnemonic 原入口计划；只读输入轨迹与冻结源码映射，不使用 TS actual。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
TASK = Path(__file__).resolve().parent
VARIANTS = {'original': ('src/compat/__tests/Mnemonic.test.ts', 50, 258, 158, 7),
            'additional': ('src/compat/__tests/Mnemonic.additional.test.ts', 8, 21, 10, 3)}
RULE = 'mnemonic-defined-object-v1'

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=VARIANTS, default='original')
    for name in ('raw', 'directory', 'replay'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    source_file, case_count, input_count, assertion_count, random_count = VARIANTS[args.variant]
    catalog = json.loads((TASK/'module-tests.json').read_text())
    source = next(f for f in catalog['files'] if f['path'] == source_file)
    mapping = json.loads((TASK/'test-map.json').read_text())
    ids = {c['id'] for c in source['cases']}
    mapped = {c['id']: c for c in mapping['cases'] if c['id'] in ids}
    names = {' '.join(c['names']): c['id'] for c in source['cases']}
    assert len(names) == len(mapped) == case_count
    groups = defaultdict(list)
    for line in args.raw.read_text().splitlines():
        row = json.loads(line)
        assert row['source']['file'] == source_file and row['occurrence'] == 1
        groups[names[row['test']]].append(row)
    assert set(groups) == ids
    plan, replay = {}, []
    for case in source['cases']:
        key = case['id']
        method = mapped[key]['java'][0]['name']
        rows = groups[key]
        assert [r['sequence'] for r in rows] == list(range(1, len(rows)+1))
        sites = mapped[key]['assertionIds']
        assertions = sites if method != 'case47' else [sites[0]] + [sites[0]+'#'+str(i) for i in range(2,25)]
        entry = {'sampleIds': [], 'assertionIds': assertions,
                 'assertionSites': {a: a.split('#')[0] for a in assertions}, 'loopSamples': {}}
        if method in ('case00', 'case10', 'case11'):
            entry['comparisonRules'] = {sites[0]: RULE}
        for row in rows:
            sample = f"call-{row['sequence']:04d}"
            entry['sampleIds'].append(sample)
            replay.append({'caseId': key, 'javaMethod': method, 'sampleId': sample, 'value': row})
        if method == 'case47':
            assert len(sites) == 1 and len(rows) == random_count2
            assert sum(r['method']=='fromEntropy' for r in rows) == 24
        plan[key] = entry
    assert len(replay) == input_count and sum(len(p['assertionIds']) for p in plan.values()) == assertion_count
    assert sum(r['value']['method']=='Random' for r in replay) == random_count
    sites = {s['id'] for s in source['sites']}
    write(args.directory/'catalog.json', dict(catalog, files=[source], partialImplementationOnly=True))
    write(args.directory/'mapping.json', dict(mapping, cases=list(mapped.values()),
          siteReviews=[s for s in mapping['siteReviews'] if s['id'] in sites]))
    write(args.directory/'input-plan.json', plan)
    args.replay.parent.mkdir(parents=True, exist_ok=True)
    args.replay.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in replay))
    print(json.dumps({'cases':case_count,'inputs':input_count,'assertions':assertion_count,'randomCalls':random_count,
                      'vectorLoopIterations':24 if args.variant == 'original' else 0}))
if __name__ == '__main__': main()
