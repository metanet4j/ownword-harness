#!/usr/bin/env python3
"""运行 Hex，可累计加入 BigNumber 构造原测试；对照真实调用，不能验收整模块。"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)
TEST = 'src/primitives/__tests/hex.test.ts'


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def identity():
    config, catalog = audit.read(TASK / 'workspace.json'), audit.read(TASK / 'module-tests.json')
    upstream = TASK.parents[2] / config['upstream']['path']
    sdk = upstream / config['upstream']['packagePath']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    audit.require(commit == config['upstream']['commit'] == catalog['upstreamCommit'], '上游提交不匹配')
    audit.require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(), '上游有修改')
    for name, digest in catalog['moduleFiles'].items():
        audit.require(audit.digest(sdk / name) == digest, f'固定源码不匹配：{name}')
    return sdk, {
        'upstreamCommit': commit, 'javaRevision': audit.java_revision(),
        'files': {name: audit.digest(TASK / name) for name in (
            'module-tests.json', 'test-map.json', 'run-hex-parity.py', 'capture-hex.cjs',
            'capture-bn-constructor.cjs', 'bn-constructor-parity.py',
            'audit-tests.py', 'ts-offline-guard.cjs', 'verify.sh', 'mvn.sh', 'pnpm.sh', 'env.sh', 'workspace.json')}
    }


def tagged(kind, encoded):
    audit.require(kind in ('string', 'null', 'undefined'), f'未知 Java 采集类型：{kind}')
    audit.require(kind == 'string' or not encoded, '非字符串携带了字符串数据')
    return {'type': kind, **({'value': base64.b64decode(encoded, validate=True).decode('utf-8')} if kind == 'string' else {})}


def java_records(path):
    rows = []
    for line in path.read_text().splitlines():
        name, source_line, method, kind, value, outcome, result, error, message = line.split('\t')
        rows.append({'test': name, 'line': int(source_line), 'method': method, 'input': tagged(kind, value),
                     'outcome': {'kind': 'throw', 'name': error, 'message': base64.b64decode(message, validate=True).decode('utf-8')}
                     if outcome == 'throw' else {'kind': 'return', 'value': tagged(outcome, result)}})
    return rows


def compare(folder):
    catalog, mapping = audit.read(TASK / 'module-tests.json'), audit.read(TASK / 'test-map.json')
    file = next(f for f in catalog['files'] if f['path'] == TEST)
    audit.require(len(file['cases']) == 8 and len(file['sites']) == 27, '固定 Hex 清单数量变化，须重新审查')
    case_ids, sites = {c['id'] for c in file['cases']}, {s['id'] for s in file['sites']}
    # 复用已测试的 compare 引擎；这些临时片段只作局部对照，不传入正式 check。
    catalog = {**catalog, 'files': [file], 'partialImplementationOnly': True}
    mapping = {**mapping, 'cases': [c for c in mapping['cases'] if c['id'] in case_ids],
               'siteReviews': [s for s in mapping['siteReviews'] if s['id'] in sites]}
    write(folder / 'hex-only.catalog.json', catalog)
    write(folder / 'hex-only.mapping.json', mapping)
    ts = [json.loads(line) for line in (folder / 'ts.calls.jsonl').read_text().splitlines()]
    java = java_records(folder / 'java.calls.tsv')
    observed = {}
    for label, rows in [('ts', ts), ('java', java)]:
        audit.require(len(rows) == 19, f'{label} 实际调用缺失或重复，应为 19 次')
        by_name = { ' '.join(c['names']): c['id'] for c in file['cases'] }
        indexed = audit.indexed(rows, lambda r: (r['test'], r['line']), f'{label} 实际调用')
        audit.require(set(r['test'] for r in rows) == set(by_name), f'{label} 实际采集用例缺失或多出')
        expected_sites = {s['id'] for s in file['sites'] if s['kind'] == 'assertion'}
        audit.require({f'{TEST}:{r["line"]}:7:assertion' for r in rows} == expected_sites, f'{label} 原断言位置缺失或多出')
        for case in file['cases']:
            name = ' '.join(case['names'])
            calls = sorted((r for (test, _), r in indexed.items() if test == name), key=lambda r: r['line'])
            inputs = [{k: r[k] for k in ('line', 'method', 'input')} for r in calls]
            input_hash = hashlib.sha256(json.dumps(inputs, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            result = observed.setdefault(case['id'], {'id': case['id']})
            result[label + 'InputSha256'] = input_hash
            if label == 'ts':
                result['inputSha256'] = input_hash
            result[label] = [{'id': f'{TEST}:{r["line"]}:7:assertion', 'value': r['outcome']} for r in calls]
    reports = sorted(folder.glob('TEST-*.xml'))
    manifest = audit.read(folder / 'manifest.json')
    write(folder / 'parity-results.json', {
        **{key: manifest['identity'][key] for key in ('upstreamCommit', 'javaRevision')},
        'catalogSha256': audit.digest(folder / 'hex-only.catalog.json'),
        'tsReportSha256': [audit.digest(folder / 'ts.jest.json')],
        'javaReportSha256': [audit.digest(p) for p in reports], 'cases': list(observed.values())})
    result = audit.compare(SimpleNamespace(catalog=folder / 'hex-only.catalog.json', mapping=folder / 'hex-only.mapping.json',
        module=None, ts_report=[folder / 'ts.jest.json'], java_report=reports, observations=folder / 'parity-results.json',
        java_revision=manifest['identity']['javaRevision']))
    return {'scope': 'hex.ts 内部实施项，非完整模块验收', 'formalAcceptance': False, **result, 'reviewedSites': len(sites)}


def verify(folder):
    manifest = audit.read(folder / 'manifest.json')
    audit.require(manifest['identity'] == identity()[1], '源码、映射、采集器或 Java 提交/工作树已变化，须重新执行')
    for name, digest in manifest['reports'].items():
        audit.require(audit.digest(folder / name) == digest, f'原始证据已变化：{name}')
    audit.require(not (folder / 'network.jsonl').read_text().strip(), '存在真实网络调用')
    result = compare(folder)
    if manifest.get('includeBnConstructor'):
        bn = compare_bn(folder)
        result = {'scope': 'Hex + BigNumber 构造内部实施项，非完整模块验收', 'formalAcceptance': False,
                  'files': 2, 'cases': result['cases'] + bn['cases'], 'javaCases': result['javaCases'] + bn['javaCases'],
                  'comparedAssertions': result['comparedAssertions'] + bn['comparedAssertions'],
                  'reviewedSites': result['reviewedSites'] + bn['reviewedSites'], 'byFile': {'hex': result, 'bnConstructor': bn}}
    write(folder / 'summary.json', result)
    print(json.dumps({'evidence': str(folder), **result}, ensure_ascii=False))


def compare_bn(folder):
    spec = importlib.util.spec_from_file_location('bn_parity', TASK / 'bn-constructor-parity.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.compare(folder, SimpleNamespace(audit=audit, TASK=TASK, write=write))


def run(include_bn=False):
    sdk, snapshot = identity()
    folder = Path(tempfile.mkdtemp(prefix='hex-parity-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '-', dir=TASK / '.cache/evidence'))
    print(f'Hex 对照证据：{folder}', flush=True)
    (folder / 'ts.calls.jsonl').touch()
    (folder / 'network.jsonl').touch()
    commands = [
        [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand', '--watchman=false', '--runTestsByPath', TEST,
         '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-hex.cjs'), '--json', '--outputFile=' + str(folder / 'ts.jest.json')],
        [str(TASK / 'verify.sh'), 'bsv-test']]
    labels = ['ts', 'java']
    if include_bn:
        (folder / 'ts.bn.calls.jsonl').touch()
        commands.insert(1, [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand', '--watchman=false',
            '--runTestsByPath', 'src/primitives/__tests/BigNumber.constructor.test.ts', '--setupFilesAfterEnv',
            str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-bn-constructor.cjs'), '--json', '--outputFile=' + str(folder / 'bn.jest.json')])
        labels.insert(1, 'bn')
    env = {**os.environ, 'MIGRATION_HEX_OBSERVATIONS': str(folder / 'ts.calls.jsonl'),
           'MIGRATION_BN_OBSERVATIONS': str(folder / 'ts.bn.calls.jsonl'), 'MIGRATION_NETWORK_LOG': str(folder / 'network.jsonl')}
    write(folder / 'manifest.json', {'status': 'running', 'identity': snapshot, 'commands': commands, 'includeBnConstructor': include_bn})
    for label, command in zip(labels, commands):
        with (folder / f'{label}.log').open('w') as log:
            subprocess.run(command, cwd=TASK, env=env, stdout=log, stderr=subprocess.STDOUT, check=True)
    target = TASK / 'metanet4j-bsv-sdk/target'
    shutil.copyfile(target / 'upstream-observations/hex.tsv', folder / 'java.calls.tsv')
    if include_bn:
        shutil.copyfile(target / 'upstream-observations/bn-constructor.jsonl', folder / 'java.bn.calls.jsonl')
    for report in (target / 'surefire-reports').glob('TEST-*.xml'):
        shutil.copyfile(report, folder / report.name)
    audit.require(identity()[1] == snapshot, '运行期间源码或工具变化，证据无效')
    write(folder / 'manifest.json', {'status': 'captured', 'identity': snapshot, 'commands': commands, 'includeBnConstructor': include_bn,
        'capturedAt': datetime.now(timezone.utc).isoformat(), 'reports': {p.name: audit.digest(p) for p in folder.iterdir() if p.name != 'manifest.json'}})
    verify(folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', type=Path, help='复核已有运行批次，源码与版本必须仍相同')
    parser.add_argument('--bn-constructor', action='store_true', help='累计对照 Hex 与完整 BigNumber 构造原文件')
    args = parser.parse_args()
    if args.verify:
        verify(args.verify.resolve())
    else:
        run(args.bn_constructor)
