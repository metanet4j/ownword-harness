#!/usr/bin/env python3
"""以固定 Point 原测试真实入口轨迹建立局部输入计划，不携带 TS 输出。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path
TASK = Path(__file__).resolve().parent
VARIANTS = {'additional': ('Point.additional.test.ts', 60, 259, 87),
            'jacobian': ('JacobianPoint.test.ts', 35, 184, 37),
            'point11': ('Point.test.ts', 11, 29, 11)}

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--variant', choices=VARIANTS, default='additional')
    for name in ('raw', 'directory', 'replay'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    filename, case_count, input_count, assertion_count = VARIANTS[args.variant]
    source_file = 'src/primitives/__tests/' + filename
    catalog = json.loads((TASK/'module-tests.json').read_text())
    source = next(f for f in catalog['files'] if f['path'] == source_file)
    mapping = json.loads((TASK/'test-map.json').read_text())
    ids = {c['id'] for c in source['cases']}
    mapped = {c['id']:c for c in mapping['cases'] if c['id'] in ids}
    names = {' '.join(c['names']):c['id'] for c in source['cases']}
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
        rows = groups[key]
        assert [r['sequence'] for r in rows] == list(range(1,len(rows)+1))
        sites = mapped[key]['assertionIds']
        assert sites == sorted(sites, key=lambda s:tuple(map(int,s.split(':')[-3:-1]))), '原断言映射顺序错误：'+mapped[key]['java'][0]['name']
        entry = {'sampleIds':[], 'assertionIds':sites, 'assertionSites':{s:s for s in sites}, 'loopSamples':{}}
        for row in rows:
            sample = f"call-{row['sequence']:04d}"
            entry['sampleIds'].append(sample)
            replay.append({'caseId':key,'javaMethod':mapped[key]['java'][0]['name'],'sampleId':sample,'value':row})
        for line in ((53,74) if args.variant == 'additional' else ()):
            samples = [f"call-{r['sequence']:04d}" for r in rows if r['method']=='BigNumber.constructor' and r['source']['line']==line+1]
            if samples:
                entry['loopSamples'][f'{source_file}:{line}:7:loop'] = samples
                assert [r['args'][0]['value'] for r in rows if r['method']=='BigNumber.constructor' and r['source']['line']==line+1] == list(range(2,2+len(samples)))
        plan[key] = entry
    assert len(replay) == input_count
    assert sum(len(e['assertionIds']) for e in plan.values()) == assertion_count
    expected_loops = [1,5] if args.variant == 'additional' else []
    assert sorted(len(v) for e in plan.values() for v in e['loopSamples'].values()) == expected_loops
    site_ids = {s['id'] for s in source['sites']}
    write(args.directory/'catalog.json',dict(catalog,files=[source],partialImplementationOnly=True))
    write(args.directory/'mapping.json',dict(mapping,cases=list(mapped.values()),siteReviews=[s for s in mapping['siteReviews'] if s['id'] in site_ids]))
    write(args.directory/'input-plan.json',plan)
    args.replay.parent.mkdir(parents=True,exist_ok=True)
    args.replay.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in replay))
    print(json.dumps({'cases':case_count,'inputs':len(replay),'assertions':assertion_count,'loopIterations':expected_loops}))
if __name__ == '__main__': main()
