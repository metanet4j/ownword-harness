"""BigNumber 构造原文件的实际轨迹对照；复用原有整模块比较引擎，不改变正式门禁。"""
import hashlib
import json
from types import SimpleNamespace

TEST = 'src/primitives/__tests/BigNumber.constructor.test.ts'


def compare(folder, runner):
    audit, task = runner.audit, runner.TASK
    catalog, mapping = audit.read(task / 'module-tests.json'), audit.read(task / 'test-map.json')
    file = next(f for f in catalog['files'] if f['path'] == TEST)
    audit.require(len(file['cases']) == 28 and len(file['sites']) == 74, 'BigNumber 构造冻结清单变化')
    case_ids = {c['id'] for c in file['cases']}
    sites = {s['id'] for s in file['sites']}
    catalog = {**catalog, 'files': [file], 'partialImplementationOnly': True}
    mapping = {**mapping, 'cases': [c for c in mapping['cases'] if c['id'] in case_ids],
               'siteReviews': [s for s in mapping['siteReviews'] if s['id'] in sites]}
    runner.write(folder / 'bn-only.catalog.json', catalog)
    runner.write(folder / 'bn-only.mapping.json', mapping)
    observed = {}
    assertion_sites = {s['line']: s['id'] for s in file['sites'] if s['kind'] == 'assertion'}
    for label, name in [('ts', 'ts.bn.calls.jsonl'), ('java', 'java.bn.calls.jsonl')]:
        rows = [json.loads(line) for line in (folder / name).read_text().splitlines()]
        audit.require(len(rows) == 52, f'{label} 构造实际断言缺失或重复，应为 52 次')
        audit.require(sum(len(r['calls']) for r in rows) == 92, f'{label} API 调用轨迹缺失或多出，应为 92 次')
        indexed = audit.indexed(rows, lambda r: (r['test'], r['line'], r['occurrence']), f'{label} 断言执行')
        audit.require({r['test'] for r in rows} == {' '.join(c['names']) for c in file['cases']}, '采集用例名称缺失或多出')
        expected = {(line, occurrence) for line in assertion_sites for occurrence in range(1, 9 if line == 139 else 2)}
        audit.require({(r['line'], r['occurrence']) for r in rows} == expected, '原断言或循环样本未完整采集')
        for case in file['cases']:
            calls = sorted((r for (test, _, _), r in indexed.items() if test == ' '.join(case['names'])), key=lambda r: (r['line'], r['occurrence']))
            inputs = [{'line': r['line'], 'occurrence': r['occurrence'],
                       'calls': [{'method': c['method'], 'args': c['args']} for c in r['calls']]} for r in calls]
            digest = hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            result = observed.setdefault(case['id'], {'id': case['id']})
            result[label + 'InputSha256'] = digest
            if label == 'ts':
                result['inputSha256'] = digest
            result[label] = [{'id': assertion_sites[r['line']] + (f'#{r["occurrence"]}' if r['line'] == 139 else ''),
                              'value': {'calls': [{'method': c['method'], 'outcome': c['outcome']} for c in r['calls']],
                                        'matcher': r['matcher'], 'actual': r['actual']}} for r in calls]
    reports = sorted(folder.glob('TEST-*.xml'))
    manifest = audit.read(folder / 'manifest.json')
    runner.write(folder / 'bn-parity-results.json', {
        **{key: manifest['identity'][key] for key in ('upstreamCommit', 'javaRevision')},
        'catalogSha256': audit.digest(folder / 'bn-only.catalog.json'),
        'tsReportSha256': [audit.digest(folder / 'bn.jest.json')],
        'javaReportSha256': [audit.digest(p) for p in reports], 'cases': list(observed.values())})
    result = audit.compare(SimpleNamespace(catalog=folder / 'bn-only.catalog.json', mapping=folder / 'bn-only.mapping.json',
        module=None, ts_report=[folder / 'bn.jest.json'], java_report=reports, observations=folder / 'bn-parity-results.json',
        java_revision=manifest['identity']['javaRevision']))
    return {'scope': 'BigNumber 构造内部实施项，非完整模块验收', 'formalAcceptance': False, **result,
            'staticAssertions': 45, 'reviewedSites': 74, 'comparedApiCalls': 92}
