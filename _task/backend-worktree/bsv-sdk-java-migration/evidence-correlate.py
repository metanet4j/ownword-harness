#!/usr/bin/env python3
"""只读关联 task-parity 报告与原始 JSONL；证据不足时保持未关联。"""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path

from importlib.util import module_from_spec, spec_from_file_location
TASK = Path(__file__).resolve().parent
spec = spec_from_file_location('evidence_inventory', TASK/'evidence-inventory.py')
inventory_module = module_from_spec(spec)
spec.loader.exec_module(inventory_module)
parity_spec = spec_from_file_location('task_parity', TASK/'task-parity.py')
task_parity = module_from_spec(parity_spec)
parity_spec.loader.exec_module(task_parity)


def read(path):
    return json.loads(Path(path).read_text())


def traces(root):
    """每份原始轨迹只读一次；只保存身份与行数，不改写实际值。"""
    result = []
    for path in sorted(root.rglob('*parity*.jsonl')):
        counts = Counter()
        side = None
        missing_identity = 0
        total = 0
        try:
            for line in path.read_text().splitlines():
                if not line.strip():
                    continue
                row = json.loads(line)
                row_side = 'java' if 'method' in row else 'ts' if 'test' in row else None
                if row_side is None or (side is not None and side != row_side):
                    raise ValueError('轨迹侧别混合或未知')
                side = row_side
                test = row.get('test')
                if not isinstance(test, str):
                    missing_identity += 1
                    continue
                key = (test,) if side == 'java' else (test, str(row.get('file', '')).replace('\\', '/'), row.get('occurrence'))
                counts[key] += 1
                total += 1
        except (OSError, ValueError, KeyError, TypeError):
            continue
        if side and total:
            result.append({'path': path, 'side': side, 'counts': counts, 'rows': total,
                           'missingIdentity': missing_identity})
    return result


def case_lookup(catalog, mapping, task):
    fixed_files = set(task['testFiles'])
    cases = [case for file in catalog['files'] if file['path'] in fixed_files for case in file['cases']]
    file_for = {case['id']: file['path'] for file in catalog['files'] if file['path'] in fixed_files for case in file['cases']}
    ts = defaultdict(list)
    for case in cases:
        ts[' '.join(case['names'])].append(case['id'])
    java = {}
    for mapped in mapping['cases']:
        if mapped['id'] not in file_for:
            continue
        for item in mapped['java']:
            key = item['className']+'#'+item['name']
            if key in java:
                raise ValueError(f'Java 映射身份重复：{key}')
            java[key] = mapped['id']
    return cases, file_for, ts, java


def trace_counts(trace, file_for, ts_names, java_names):
    """返回可唯一对应的固定用例计数；重名且无文件/occurrence 时拒绝推断。"""
    counts = Counter()
    ambiguous = 0
    unknown = 0
    for key, amount in trace['counts'].items():
        if trace['side'] == 'java':
            case_id = java_names.get(key[0])
        else:
            name, source, occurrence = key
            options = ts_names.get(name, [])
            if source:
                options = [cid for cid in options if source == file_for[cid] or source.endswith('/'+file_for[cid])]
            if occurrence is not None:
                # 固定用例 occurrence 由清单保存；同名行按文件与序号匹配。
                options = [cid for cid in options if occurrence == ts_names['__occurrence__'][cid]]
            if len(options) > 1:
                ambiguous += amount
                continue
            case_id = options[0] if options else None
        if case_id is None:
            unknown += amount
        else:
            counts[case_id] += amount
    return counts, ambiguous, unknown


def trace_events(trace, file_for, ts_names, java_names):
    """只在身份唯一时返回行引用；文件中的原始实际值保持只读。"""
    by_case = defaultdict(list)
    for ordinal, line in enumerate(trace['path'].read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if trace['side'] == 'java':
            case_id = java_names.get(row.get('test'))
        else:
            source = str(row.get('file', '')).replace('\\', '/')
            options = ts_names.get(row.get('test'), [])
            if source:
                options = [cid for cid in options if source == file_for[cid] or source.endswith('/'+file_for[cid])]
            occurrence = row.get('occurrence')
            if occurrence is not None:
                options = [cid for cid in options if occurrence == ts_names['__occurrence__'][cid]]
            case_id = options[0] if len(options) == 1 else None
        if case_id is not None:
            by_case[case_id].append((ordinal, row))
    return by_case


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(task_root=TASK):
    inventory = inventory_module.inventory(task_root)
    catalog = read(task_root/'module-tests.json')
    mapping = read(task_root/'test-map.json')
    features = {item['id']: item for item in read(task_root/'feature_list.json')['features']}
    mapped = {item['id']: item for item in mapping['cases']}
    raw = traces(task_root/'.cache/evidence')
    rows = []
    totals = Counter()
    linked = []
    gaps = defaultdict(set)
    all_cases = {case['id'] for file in catalog['files'] for case in file['cases']}
    for item in inventory['tasks']:
        task_id = item['taskId']
        if item['report'] is None:
            task = features[task_id]
            for file in catalog['files']:
                if file['path'] in task['testFiles']:
                    for case in file['cases']:
                        gaps[case['id']].add('noCompleteTaskReport')
            rows.append({'taskId': task_id, 'cases': item['expectedCases'], 'tier': 'noCompleteTaskReport'})
            totals['noCompleteTaskReportCases'] += item['expectedCases']
            continue
        report = read(task_root/item['report'])
        task = features[task_id]
        cases, file_for, ts_names, java_names = case_lookup(catalog, mapping, task)
        ts_names['__occurrence__'] = {case['id']: case.get('occurrence', 1) for case in cases}
        expected = {case['id']: case for case in report['cases']}
        exact_site = [cid for cid, row in expected.items()
                      if row['tsAssertions'] == row['javaAssertions'] == row['matchedAssertions']
                      == len(mapped[cid]['assertionIds'])]
        dynamic = set(expected)-set(exact_site)
        single_site = [cid for cid in exact_site if len(mapped[cid]['assertionIds']) == 1]
        order_only = set(exact_site)-set(single_site)
        for cid in dynamic:
            gaps[cid].add('siteCardinalityMismatchOrRepeatedSite')
        for cid in order_only:
            gaps[cid].add('multipleSitesWithoutCallsite')
        for cid in report.get('nondeterministicCases', []):
            gaps[cid].add('nondeterministicValueComparison')
        totals['taskReportCases'] += len(expected)
        totals['taskReportAssertions'] += sum(row['matchedAssertions'] for row in expected.values())
        totals['siteCardinalityExactCases'] += len(exact_site)
        totals['siteCardinalityAmbiguousCases'] += len(dynamic)
        totals['singleSiteCases'] += len(single_site)
        totals['multiSiteOrderUnprovenCases'] += len(order_only)
        candidates = {'ts': [], 'java': []}
        for trace in raw:
            side = trace['side']
            counts, ambiguous, unknown = trace_counts(trace, file_for, ts_names, java_names)
            if ambiguous:
                continue
            field = 'tsAssertions' if side == 'ts' else 'javaAssertions'
            if all(counts.get(cid, 0) == row[field] for cid, row in expected.items()):
                candidates[side].append({'path': str(trace['path'].relative_to(task_root)),
                                         'extraRows': unknown, 'rows': trace['rows']})
        for side in ('ts', 'java'):
            candidates[side].sort(key=lambda x: (x['extraRows'], x['path']))
        if candidates['ts'] and candidates['java']:
            totals['rawCountMatchedCases'] += len(expected)
            if len(candidates['ts']) == len(candidates['java']) == 1:
                totals['rawUniquePairCases'] += len(expected)
        else:
            totals['rawMissingCases'] += len(expected)
        for side in ('ts', 'java'):
            if not candidates[side]:
                for cid in expected:
                    gaps[cid].add(f'missingExactCount{side.upper()}Trace')
            elif len(candidates[side]) > 1:
                for cid in expected:
                    gaps[cid].add(f'duplicate{side.upper()}TraceCandidates')
        if len(candidates['ts']) == len(candidates['java']) == 1:
            selected = {side: next(trace for trace in raw if str(trace['path'].relative_to(task_root)) == candidates[side][0]['path'])
                        for side in ('ts', 'java')}
            events = {side: trace_events(selected[side], file_for, ts_names, java_names)
                      for side in ('ts', 'java')}
            for cid in single_site:
                ts_events, java_events = events['ts'][cid], events['java'][cid]
                site_ids = mapped[cid]['assertionIds']
                if len(ts_events) != len(java_events) or len(ts_events) != len(site_ids):
                    continue
                if any(task_parity.row_key(file_for[cid], cid, left[1]) != task_parity.row_key(file_for[cid], cid, right[1])
                       for left, right in zip(ts_events, java_events)):
                    totals['rawValueMismatchCases'] += 1
                    gaps[cid].add('rawValueMismatch')
                    continue
                linked.append({'caseId': cid, 'taskId': task_id,
                               'tsTrace': candidates['ts'][0]['path'], 'tsSha256': digest(selected['ts']['path']),
                               'javaTrace': candidates['java'][0]['path'], 'javaSha256': digest(selected['java']['path']),
                               'assertions': [{'siteId': site_ids[0], 'tsLine': ts_events[0][0],
                                               'javaLine': java_events[0][0]}]})
                totals['siteLinkedCases'] += 1
                totals['siteLinkedAssertions'] += len(site_ids)
        rows.append({'taskId': task_id, 'cases': len(expected), 'assertions': sum(c['matchedAssertions'] for c in expected.values()),
                     'siteCardinalityExact': len(exact_site), 'siteCardinalityAmbiguous': len(dynamic),
                     'singleSite': len(single_site), 'multiSiteOrderUnproven': len(order_only),
                     'tsTraceCandidates': candidates['ts'], 'javaTraceCandidates': candidates['java'],
                     'rawPairUnique': len(candidates['ts']) == len(candidates['java']) == 1})
    totals['fixedCases'] = sum(row['expectedCases'] for row in inventory['tasks'])
    totals['standardInputLedgers'] = 0
    totals['evidenceBundleReadyCases'] = 0
    return {'upstreamCommit': catalog['upstreamCommit'], 'totals': dict(totals), 'tasks': rows,
            'linkedEvents': linked,
            'missingInputLedgerCaseIds': sorted(all_cases),
            'caseGaps': [{'caseId': cid, 'reasons': sorted(reasons)} for cid, reasons in sorted(gaps.items())],
            'limits': ['原始 task-parity JSONL 没有 caseId、断言 siteId 和统一输入样本账本。',
                       'siteCardinalityExact 只证明固定映射与报告计数相等；多个断言站点缺少原始调用站点，按行序配对不构成精确 siteId 关联。',
                       '同一用例内循环重复同一断言站点时，按序号不能证明样本边界；不得生成 inputSha。']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    result=analyze()
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'totals':result['totals'],'ambiguousTasks':[
        row['taskId'] for row in result['tasks'] if row.get('tier')!='noCompleteTaskReport' and not row['rawPairUnique']]},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
