#!/usr/bin/env python3
"""核对现有任务级真实对照报告与全量验收还缺的原始证据。"""
import argparse
import hashlib
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(task=TASK):
    state, catalog = read(task/'feature_list.json'), read(task/'module-tests.json')
    cases_by_file = {file['path']: {case['id'] for case in file['cases']} for file in catalog['files']}
    reports = {}
    for path in (task/'.cache/evidence').rglob('*.json'):
        try:
            with path.open() as source:
                head = source.read(3000)
            if 'taskId' not in head or 'casesTotal' not in head:
                continue
            item = read(path)
            if isinstance(item, dict) and isinstance(item.get('cases'), list) and 'assertionsCompared' in item:
                reports.setdefault(item['taskId'], []).append((path, item))
        except (OSError, ValueError, KeyError):
            continue
    rows = []
    for feature in state['features']:
        if feature.get('kind') != 'implementation-slice':
            continue
        expected = set().union(*(cases_by_file[file] for file in feature['testFiles']))
        valid = []
        for path, report in reports.get(feature['id'], []):
            observed = [case.get('id') for case in report['cases']]
            if (len(observed) == len(set(observed)) == len(expected)
                    and set(observed) == expected and report.get('casesTotal') == len(expected)
                    and report.get('casesCompared') == len(expected)
                    and report.get('missingCases') == report.get('missingAssertions') == report.get('uncompared') == 0
                    and report.get('taskAcceptancePassed') is True):
                valid.append((path, report))
        chosen = max(valid, key=lambda x: x[0].stat().st_mtime) if valid else None
        rows.append({'taskId': feature['id'], 'expectedCases': len(expected),
                     'report': str(chosen[0].relative_to(task)) if chosen else None,
                     'reportSha256': digest(chosen[0]) if chosen else None,
                     'javaRevision': chosen[1].get('javaRevision') if chosen else None,
                     'assertionsCompared': chosen[1].get('assertionsCompared') if chosen else None})
    mapped = read(task/'test-map.json'); mapped_ids={case['id'] for case in mapped['cases']}
    all_cases = set().union(*cases_by_file.values())
    all_sites = {site['id'] for file in catalog['files'] for site in file['sites']}
    reviewed_sites = {site['id'] for site in mapped['siteReviews']}
    api_catalog, api_map = read(task/'api-catalog.json'), read(task/'api-map.json')
    api_ids={entry['id'] for entry in api_catalog['entries']}
    mapped_api={entry['id']:entry for entry in api_map['entries']}
    return {'upstreamCommit': catalog['upstreamCommit'], 'tasks': rows,
            'taskReportsComplete': sum(row['report'] is not None for row in rows),
            'taskReportsTotal': len(rows),
            'taskReportCases': sum(row['expectedCases'] for row in rows if row['report'] is not None),
            'taskReportAssertions': sum(row['assertionsCompared'] for row in rows if row['report'] is not None),
            'distinctTaskReportJavaRevisions': len({row['javaRevision'] for row in rows if row['javaRevision']}),
            'unmappedCases': len(all_cases-mapped_ids),
            'unreviewedSites': len(all_sites-reviewed_sites),
            'unmappedApi': len(api_ids-set(mapped_api)),
            'pendingApi': sum(entry.get('review')!='reviewed' for entry in mapped_api.values()),
            'globalInputPlan': (task/'.cache/evidence/input-replay-plan.json').exists(),
            'globalObservations': (task/'.cache/evidence/parity-results.json').exists(),
            'scopeReview': read(task/'module-scope.json')['scopeReview']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='可选：保存完整只读核查结果')
    args=parser.parse_args()
    result=inventory()
    if args.output:
        args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({key:value for key,value in result.items() if key!='tasks'},ensure_ascii=False,indent=2))
    for row in result['tasks']:
        if row['report'] is None:
            print(f"缺少完整任务级报告：{row['taskId']}（{row['expectedCases']} 用例）")


if __name__=='__main__':
    main()
