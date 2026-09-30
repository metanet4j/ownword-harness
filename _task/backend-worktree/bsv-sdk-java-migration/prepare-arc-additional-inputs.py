#!/usr/bin/env python3
"""冻结 ARC 补充原测试的真实构造、随机、序列化、HTTP 和循环输入。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path
TASK = Path(__file__).resolve().parent
SOURCE = 'src/transaction/broadcasters/__tests/ARC.additional.test.ts'
JAVA = 'com.metanet4j.bsv.transaction.broadcasters.ARCAdditionalTest'
def read(path): return json.loads(Path(path).read_text())
def rows(path): return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
def freeze(args):
    full, mapping = read(TASK/'module-tests.json'), read(TASK/'test-map.json')
    source = next(f for f in full['files'] if f['path'] == SOURCE)
    ids = {c['id'] for c in source['cases']}
    mapped = {c['id']:c for c in mapping['cases'] if c['id'] in ids}
    names = {' '.join(c['names']):c['id'] for c in source['cases']}
    assert len(ids) == len(mapped) == 30
    grouped, assertions = defaultdict(list), defaultdict(list)
    for row in rows(args.raw):
        assert row['source']['file'] == SOURCE and row['occurrence'] == 1
        grouped[names[row['test']]].append(row)
    for row in rows(args.assertions_raw):
        assert row['file'].endswith('/'+SOURCE) and row['pass'] is True
        assertions[names[row['test']]].append(row)
    assert set(grouped) == set(assertions) == ids
    random = rows(args.random_raw)
    assert len(random) == 30 and len({r['test'] for r in random}) == 30
    by_test = {r['test']:r for r in random}
    plan, replay = {}, []
    for case in source['cases']:
        key = case['id']; events = grouped[key]; sites = mapped[key]['assertionIds']
        assert mapped[key]['java'] == [{'className': JAVA, 'name': mapped[key]['java'][0]['name']}]
        assert [r['sequence'] for r in events] == list(range(1,len(events)+1))
        assert events[0]['method'] == 'ARC.constructor' and events[1]['method'] == 'Random'
        frozen = by_test[events[0]['test']]
        assert frozen['length'] == 16 and len(frozen['hex']) == 32 and events[1]['bytesHex'] == frozen['hex']
        assert events[1]['args'] == [{'type':'number','value':16}]
        actual_sites = sites[:]
        loops = [r for r in events if r['method'] == 'loop.value']
        if mapped[key]['java'][0]['name'] == 'case27':
            assert len(loops) == 2 and [r['source']['line'] for r in loops] == [533,533]
            actual_sites += [site+'#2' for site in sites[1:]]
        else: assert not loops
        assert len(assertions[key]) == len(actual_sites)
        entry = {'sampleIds':[], 'assertionIds':actual_sites,
                 'assertionSites':{site:site.split('#')[0] for site in actual_sites}, 'loopSamples':{}}
        for event in events:
            sample = f"call-{event['sequence']:04d}"
            entry['sampleIds'].append(sample)
            replay.append({'caseId':key, 'javaMethod':mapped[key]['java'][0]['name'], 'sampleId':sample, 'value':event})
        if loops: entry['loopSamples'][SOURCE+':533:7:loop'] = [f"call-{r['sequence']:04d}" for r in loops]
        plan[key] = entry
    assert len(replay) == 179 and sum(len(p['assertionIds']) for p in plan.values()) == 78
    site_ids = {s['id'] for s in source['sites']}
    directory = Path(args.directory)
    write(directory/'catalog.json', dict(full, files=[source], partialImplementationOnly=True))
    write(directory/'mapping.json', dict(mapping, cases=list(mapped.values()), siteReviews=[r for r in mapping['siteReviews'] if r['id'] in site_ids]))
    write(directory/'input-plan.json', plan)
    write(args.input_plan, plan)
    write(directory/'random.json', random)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in replay))
    print(json.dumps({'cases':30,'inputs':179,'assertions':78,'random':30,'loopIterations':2}))
def emit(args):
    planned, fresh = rows(args.replay), rows(args.raw)
    assert len(planned) == len(fresh) == 179
    assert rows(args.random_raw) == read(args.random_replay)
    expected = {(r['value']['test'],r['value']['sequence']):r for r in planned}
    result = []
    for row in fresh:
        entry = expected.pop((row['test'],row['sequence']))
        assert row == entry['value'], '本轮 ARC 补充真实入口与冻结输入不同：'+entry['sampleId']
        result.append({'runId':os.environ['EVIDENCE_RUN_ID'],'side':'ts','caseId':entry['caseId'],
                       'sampleId':entry['sampleId'],'value':row})
    assert not expected
    Path(args.output).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in result))
    print(json.dumps({'side':'ts','cases':30,'inputs':179}))
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    p = sub.add_parser('freeze')
    for key in ('raw','assertions-raw','random-raw','directory','input-plan','replay'): p.add_argument('--'+key, required=True)
    p = sub.add_parser('emit-ts')
    for key in ('raw','replay','random-raw','random-replay','output'): p.add_argument('--'+key, required=True)
    args = parser.parse_args(); (freeze if args.mode == 'freeze' else emit)(args)
if __name__ == '__main__': main()
