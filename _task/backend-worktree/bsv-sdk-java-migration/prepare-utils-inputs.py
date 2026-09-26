#!/usr/bin/env python3
"""冻结固定 utils.test.ts 的真实公开入口；可按独立用例组建立局部计划。"""
import argparse
from collections import defaultdict
import json
import os
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/primitives/__tests/utils.test.ts'
EXCLUDED = {
    'utils binary to base58 string Converts to base58 as expected',
    'utils binary to base58 string Converts to base58 as expected with 1s',
    'utils binary to base58 string round-trips boundary byte values',
}
GROUPS = {
    'constant-time': ('constantTimeEquals ', 5, 5),
    'base64': ('toArray base64 ', 7, 13),
    'simple': (('constantTimeEquals ', 'toArray base64 '), 12, 18),
    'null-check': ('verifyNotNull ', 5, 8),
    'utf8-decode': ('toUTF8 UTF-8 decoding ', 9, 9),
    'utf8-encode': (('utils should encode ', 'utils should return an empty array ',
                     'utils should replace lone surrogates ', "toArray('utf8') UTF-8 encoding "), 9, 10),
    'utf8': (('toUTF8 UTF-8 decoding ', 'utils should encode ',
              'utils should return an empty array ', 'utils should replace lone surrogates ',
              "toArray('utf8') UTF-8 encoding "), 18, 19),
    'misc': ('', 6, 16),
    'utf8-misc': ('', 24, 35),
    'utf8-bounds': ('toUTF8 bounds checks ', 3, 6),
    'diagnostic': ('utils formats unknown diagnostic values ', 1, 15),
    'remaining': ('', 56, 116),
}
MISC_NAMES = {
    'utils should convert to array',
    'utils decodes hex directly to Uint8Array with legacy odd-length handling',
    'utils should zero pad byte to hex',
    'utils should convert to hex',
    'utils should convert to hex without a global Buffer implementation',
    'utils should encode',
}


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write(path, value):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, ensure_ascii=True, indent=2) + '\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def selected(case, group):
    name = ' '.join(case['names'])
    if group == 'misc':
        return name in MISC_NAMES
    if group == 'utf8-misc':
        return name in MISC_NAMES or name.startswith(GROUPS['utf8'][0])
    return name not in EXCLUDED and name.startswith(GROUPS[group][0])


def identity(row):
    return {key: row[key] for key in
            ('test', 'source', 'receiverId', 'className', 'method', 'args', 'preState')}


def freeze(args):
    _, case_count, event_count = GROUPS[args.group]
    full = read(TASK / 'module-tests.json')
    source = next(file for file in full['files'] if file['path'] == FILE)
    cases = [case for case in source['cases'] if selected(case, args.group)]
    require(len(cases) == case_count, '固定 utils 用例数变化')
    all_mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in cases}
    mapping_cases = [case for case in all_mapping['cases'] if case['id'] in ids]
    require(len(mapping_cases) == len(ids), 'Java 映射用例缺失')
    mapped = {case['id']: case for case in mapping_cases}
    source_sites = {site['id']: site for site in source['sites']}
    registration_sites = sorted((site for site in source['sites'] if site['kind'] == 'registration'),
                                key=lambda site: site['line'])
    site_ids = set()
    for case in cases:
        assertion_ids = mapped[case['id']]['assertionIds']
        require(assertion_ids and all(site in source_sites for site in assertion_ids),
                '原断言站点未冻结')
        site_ids.update(assertion_ids)
        first = min(source_sites[site]['line'] for site in assertion_ids)
        previous = [site for site in registration_sites if site['line'] < first]
        require(previous, '原测试缺注册站点')
        site_ids.add(previous[-1]['id'])
    catalog = {**full, 'files': [{**source, 'cases': cases,
                                  'sites': [site for site in source['sites'] if site['id'] in site_ids]}],
               'partialImplementationOnly': True}
    reviews = [review for review in all_mapping['siteReviews'] if review['id'] in site_ids]
    require(len(reviews) == len(site_ids), '站点审阅缺失')
    mapping = {**all_mapping, 'cases': mapping_cases, 'siteReviews': reviews}
    by_source = {(' '.join(case['names']), case['occurrence']): case for case in cases}
    grouped = defaultdict(list)
    sequences = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == FILE, '输入含其他文件')
        key = (row['test'], row['occurrence'])
        if key not in by_source:
            continue
        sequences[key] += 1
        require(row['sequence'] == sequences[key], '原测试调用序号不连续')
        case = by_source[key]
        java = mapped[case['id']]['java']
        require(len(java) == 1 and java[0]['className'] == 'com.metanet4j.bsv.primitives.UtilsTest',
                'Java 注册身份不唯一')
        sample = f"{FILE}:{row['source']['line']}:{row['method']}:case{row['occurrence']}#{row['sequence']:04d}"
        grouped[case['id']].append({'caseId': case['id'], 'sampleId': sample,
                                    'javaMethod': java[0]['name'], 'value': identity(row)})
    require(set(grouped) == ids, '原测试有用例未触达公开入口')
    require(sum(map(len, grouped.values())) == event_count, '原测试公开入口数量变化')
    plan = {}
    replay = []
    for case in cases:
        case_id = case['id']
        events = grouped[case_id]
        assertion_ids = mapped[case_id]['assertionIds']
        plan[case_id] = {'sampleIds': [event['sampleId'] for event in events],
                         'assertionIds': assertion_ids,
                         'assertionSites': {site: site for site in assertion_ids}, 'loopSamples': {}}
        replay.extend(events)
    write(args.catalog, catalog)
    write(args.mapping, mapping)
    write(args.input_plan, plan)
    Path(args.replay).parent.mkdir(parents=True, exist_ok=True)
    Path(args.replay).write_text(''.join(json.dumps(event, ensure_ascii=True) + '\n' for event in replay))
    print(json.dumps({'group': args.group, 'cases': len(cases), 'events': len(replay),
                      'assertionSites': sum(len(case['assertionIds']) for case in plan.values())}))


def emit(args):
    planned = rows(args.replay)
    fresh = rows(args.raw)
    by_key = {(event['value']['test'], event['value']['source']['line'],
               event['value']['method'], event['value']['preState']['priorCalls']): event
              for event in planned}
    require(len(by_key) == len(planned), '计划入口身份重复')
    observed = []
    for row in fresh:
        key = (row['test'], row['source']['line'], row['method'], row['preState']['priorCalls'])
        event = by_key.get(key)
        if event is None:
            continue
        require(identity(row) == event['value'], '本轮原测试实际输入与冻结计划不同')
        observed.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                         'caseId': event['caseId'], 'sampleId': event['sampleId'],
                         'value': identity(row)})
    require(len(observed) == len(planned), '本轮原测试入口缺失')
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=True) + '\n' for row in observed))
    print(json.dumps({'side': 'ts', 'events': len(observed)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    freeze_parser = sub.add_parser('freeze')
    freeze_parser.add_argument('--group', choices=GROUPS, required=True)
    freeze_parser.add_argument('--raw', required=True)
    for option in ('catalog', 'mapping', 'input-plan', 'replay'):
        freeze_parser.add_argument('--' + option, required=True)
    emit_parser = sub.add_parser('emit-ts')
    for option in ('raw', 'replay', 'output'):
        emit_parser.add_argument('--' + option, required=True)
    args = parser.parse_args()
    (freeze if args.mode == 'freeze' else emit)(args)


if __name__ == '__main__':
    main()
