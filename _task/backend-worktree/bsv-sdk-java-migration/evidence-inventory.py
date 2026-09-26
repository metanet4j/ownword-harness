#!/usr/bin/env python3
"""核对现有任务级真实对照报告与全量验收还缺的原始证据。"""
import argparse
import hashlib
import json
from pathlib import Path
import re

TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def complete_report(report, feature, catalog, expected):
    """只认可字段及逐项计数自洽的历史报告；不追认为当前运行证据。"""
    rows = report.get('cases')
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        return False
    observed = [row.get('id') for row in rows]
    revision = report.get('javaRevision')
    if (not all(isinstance(identity, str) for identity in observed)
            or len(observed) != len(set(observed)) or set(observed) != expected
            or report.get('upstreamCommit') != catalog['upstreamCommit']
            or not isinstance(revision, str) or re.fullmatch(r'[0-9a-f]{64}', revision) is None
            or report.get('testFiles') != feature['testFiles']
            or report.get('casesTotal') != len(expected) or report.get('casesCompared') != len(expected)
            or report.get('missingCases') != 0 or report.get('missingAssertions') != 0
            or report.get('uncompared') != 0 or report.get('taskAcceptancePassed') is not True):
        return False
    files = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    matched = extra = 0
    for row in rows:
        counts = [row.get(name) for name in ('tsAssertions', 'javaAssertions', 'matchedAssertions',
                                            'missingAssertions', 'extraJavaAssertions')]
        if (not all(type(value) is int and value >= 0 for value in counts)
                or row.get('file') != files[row['id']]):
            return False
        ts, java, compared, missing, additional = counts
        if ts != compared or ts <= 0 or java != compared + additional or missing != 0:
            return False
        matched += compared
        extra += additional
    return (type(report.get('assertionsCompared')) is int and report['assertionsCompared'] == matched
            and type(report.get('extraJavaAssertions')) is int and report['extraJavaAssertions'] == extra)


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
            if complete_report(report, feature, catalog, expected):
                valid.append((path, report))
        chosen = max(valid, key=lambda x: x[0].stat().st_mtime) if valid else None
        rows.append({'taskId': feature['id'], 'expectedCases': len(expected),
                     'report': str(chosen[0].relative_to(task)) if chosen else None,
                     'reportSha256': digest(chosen[0]) if chosen else None,
                     'evidenceStatus': 'historical-report-structure-only' if chosen else 'missing-valid-report',
                     'runtimeProvenanceVerified': False,
                     'javaRevision': chosen[1].get('javaRevision') if chosen else None,
                     'assertionsCompared': chosen[1].get('assertionsCompared') if chosen else None})
    mapped = read(task/'test-map.json'); mapped_ids={case['id'] for case in mapped['cases']}
    all_cases = set().union(*cases_by_file.values())
    all_sites = {site['id'] for file in catalog['files'] for site in file['sites']}
    reviewed_sites = {site['id'] for site in mapped['siteReviews']}
    api_catalog, api_map = read(task/'api-catalog.json'), read(task/'api-map.json')
    api_ids={entry['id'] for entry in api_catalog['entries']}
    mapped_api={entry['id']:entry for entry in api_map['entries']}
    return {'upstreamCommit': catalog['upstreamCommit'], 'tasks': rows, 'formalAcceptance': False,
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
