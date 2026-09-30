#!/usr/bin/env python3
"""原 MasterCertificate 15 例完整执行；其中 2 个构造例的同输入局部证据。"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time
import uuid
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent
PLAN = TASK / 'auth-certificate-master-constructor-plan.json'
FILE = 'src/auth/certificates/__tests/MasterCertificate.test.ts'
CLASS = 'com.metanet4j.bsv.auth.certificates.MasterCertificateTest'
CASE_METHODS = {
    '13b4b968a38bc16a436bda799dabd933901d1802c28b8eb3e898e12ef11772f4': 'constructsValidMaster',
    '7255afac01b0569e34c3fc01905bbda39c7f56a64f256bc85ed1dbb65fe3594e': 'rejectsMissingMasterKey',
}

spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sources(worktree):
    catalog, mapping, plan = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    selected = {case['id']: case for case in file['cases'] if case['id'] in CASE_METHODS}
    require(set(selected) == set(CASE_METHODS) == set(plan), '固定构造用例或计划变化')
    mapped = {case['id']: case for case in mapping['cases'] if case['id'] in selected}
    require(set(mapped) == set(selected), '构造用例映射缺失')
    for case_id, method in CASE_METHODS.items():
        require(mapped[case_id]['java'] == [{'className': CLASS, 'name': method}], 'Java 用例映射变化')
        require(plan[case_id]['assertionIds'] == mapped[case_id]['assertionIds'], '断言计划与固定映射不同')
    sites = {site for case in mapped.values() for site in case['assertionIds']}
    sites |= {review['id'] for review in mapping['siteReviews'] if set(review['caseIds']) <= set(selected)
              and review['id'].startswith(FILE + ':')}
    fragment = {**catalog, 'files': [{**file, 'cases': list(selected.values()),
                                       'sites': [site for site in file['sites'] if site['id'] in sites]}]}
    review = {**mapping, 'cases': list(mapped.values()),
              'siteReviews': [item for item in mapping['siteReviews'] if item['id'] in sites]}
    audit.validate_plan(fragment, review, plan)
    config = read(TASK / 'workspace.json')['upstream']
    upstream = TASK.parents[2] / config['path']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['commit'] == catalog['upstreamCommit'], '固定 TS 提交变化')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(),
            '固定 TS 工作树有修改')
    require(sha(upstream / config['packagePath'] / FILE) == file['sha256'], '固定 TS 文件校验值变化')
    revision = audit.java_revision({'metanet4j-bsv-sdk': str(worktree)})
    frozen = {name: sha(TASK / name) for name in (
        'module-tests.json', 'test-map.json', 'workspace.json', PLAN.name,
        'capture-auth-certificate-master-constructor.cjs', 'capture-parity.cjs',
        'auth-certificate-constructor-local-gate.py', 'audit-tests.py')}
    return file, selected, plan, {'upstreamCommit': commit, 'javaRevision': revision, 'frozenSha256': frozen}


def assertions(raw, side, destination, run_id, selected, plan):
    names = {' '.join(case['names']): case_id for case_id, case in selected.items()}
    java_methods = {method: case_id for case_id, method in CASE_METHODS.items()}
    grouped = {case_id: [] for case_id in selected}
    for row in lines(raw):
        case_id = names.get(row.get('test')) if side == 'ts' else java_methods.get(row.get('method'))
        if case_id is not None:
            require(row.get('pass', True) is True, '原 TS 断言采集显示失败')
            grouped[case_id].append(row)
    with destination.open('w') as stream:
        for case_id in selected:
            identifiers = plan[case_id]['assertionIds']
            require(len(grouped[case_id]) == len(identifiers), f'{side} 构造断言次数变化：{case_id}')
            for identifier, row in zip(identifiers, grouped[case_id]):
                value = {'kind': 'assertion', 'matcher': row['matcher'], 'negated': row['negated'],
                         'actual': row['actual'], 'expected': row['expected']}
                stream.write(json.dumps({'runId': run_id, 'side': side, 'caseId': case_id,
                                         'assertionId': identifier, 'value': value}, ensure_ascii=False) + '\n')


def execute(command, environment, log):
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=TASK, env=environment, stdout=stream, stderr=subprocess.STDOUT)
    require(result.returncode == 0, f'原测试失败：{command}；日志 {log}')


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, selected, plan, identity = sources(worktree)
    output.mkdir(parents=True)
    sdk = TASK.parents[2] / read(TASK / 'workspace.json')['upstream']['path'] / 'packages/sdk'
    manifest = {'scope': 'MasterCertificate 原文件 15/15 执行；证书任务仅 2/50 用例同输入',
                'formalAcceptance': False, **identity, 'runs': {}}
    for side in ('ts', 'java'):
        run_id = uuid.uuid4().hex
        started = time.time_ns()
        env = dict(os.environ, EVIDENCE_RUN_ID=run_id, EVIDENCE_SIDE=side,
                   EVIDENCE_INPUTS_PATH=str(output / f'{side}-inputs.jsonl'),
                   EVIDENCE_ASSERTIONS_PATH=str(output / f'{side}-assertions.jsonl'),
                   MIGRATION_NETWORK_LOG=str(output / f'{side}-network.jsonl'))
        (output / f'{side}-network.jsonl').touch()
        if side == 'ts':
            env['MIGRATION_PARITY_TS_OBSERVATIONS'] = str(output / 'ts-parity-raw.jsonl')
            command = [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand',
                       '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                       str(TASK / 'ts-offline-guard.cjs'),
                       str(TASK / 'capture-auth-certificate-master-constructor.cjs'),
                       str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(output / 'ts-jest.json')]
        else:
            env['MIGRATION_AUTH_CERTIFICATE_TS_INPUTS'] = str(output / 'ts-inputs.jsonl')
            command = [str(TASK / 'mvn.sh'), '-f', str(worktree / 'pom.xml'), 'clean', 'test',
                       '-Dtest=MasterCertificateTest',
                       '-Dmigration.parity.java.output=' + str(worktree / 'target/upstream-observations/parity-java.jsonl')]
        manifest['runs'][side] = {'runId': run_id, 'command': command, 'startedAtNs': started,
                                  'sourceRevision': identity['upstreamCommit'] if side == 'ts' else identity['javaRevision']}
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        execute(command, env, output / f'{side}.log')
        if side == 'java':
            shutil.copyfile(worktree / 'target/upstream-observations/parity-java.jsonl', output / 'java-parity-raw.jsonl')
            shutil.copyfile(worktree / 'target/surefire-reports' / f'TEST-{CLASS}.xml', output / 'java-surefire.xml')
        assertions(output / f'{side}-parity-raw.jsonl', side, output / f'{side}-assertions.jsonl',
                   run_id, selected, plan)
        after = sources(worktree)[3]
        require(after == identity, '采集期间源码、映射或工具变化')
        paths = [f'{side}-inputs.jsonl', f'{side}-assertions.jsonl', f'{side}-parity-raw.jsonl',
                 f'{side}-network.jsonl', f'{side}.log',
                 'ts-jest.json' if side == 'ts' else 'java-surefire.xml']
        manifest['runs'][side].update(finishedAtNs=time.time_ns(), exitCode=0,
                                      sourceRevisionAfter=after['upstreamCommit'] if side == 'ts' else after['javaRevision'],
                                      artifactSha256={name: sha(output / name) for name in paths})
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return verify(worktree, output)


def verify(worktree, output):
    file, selected, plan, identity = sources(worktree)
    manifest = read(output / 'manifest.json')
    require(all(manifest.get(key) == identity[key] for key in identity), '当前来源与执行时 manifest 不同')
    require(manifest.get('formalAcceptance') is False, '局部证据不得标记为正式验收')
    require(set(manifest['runs']) == {'ts', 'java'}, '缺少独立 TS/Java 运行')
    require(manifest['runs']['ts']['runId'] != manifest['runs']['java']['runId'], '两端运行身份相同')
    for side in ('ts', 'java'):
        entry = manifest['runs'][side]
        require(entry['exitCode'] == 0 and entry['finishedAtNs'] > entry['startedAtNs']
                and entry['sourceRevisionAfter'] == entry['sourceRevision'], '原测试未完整运行或源码发生变化')
        require(all(sha(output / name) == digest for name, digest in entry['artifactSha256'].items()),
                f'{side} 原始产物校验值变化')
        require(not (output / f'{side}-network.jsonl').read_text().strip(), f'{side} 意外网络调用')
    jest = read(output / 'ts-jest.json')
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == len(file['cases']) == 15
            and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
            'MasterCertificate 原 Jest 15 例未全部通过')
    require(Counter(tuple(row['ancestorTitles'] + [row['title']])
                    for result in jest['testResults'] for row in result['assertionResults'])
            == Counter(tuple(case['names']) for case in file['cases']), '原 Jest 用例身份不完整')
    suite = ET.parse(output / 'java-surefire.xml').getroot()
    java = [row for row in suite.findall('testcase')]
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == len(java) == 15
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
            'MasterCertificate Java Surefire 15 例未全部通过')
    require({row.attrib['name'] for row in java} == {mapping['java'][0]['name'] for mapping in
            read(TASK / 'test-map.json')['cases'] if mapping['id'] in
            {case['id'] for case in file['cases']}}, 'Java 原用例身份不完整')
    for side in ('ts', 'java'):
        inputs = lines(output / f'{side}-inputs.jsonl')
        assertions_ = lines(output / f'{side}-assertions.jsonl')
        require(all(row['side'] == side and row['runId'] == manifest['runs'][side]['runId']
                    for row in inputs + assertions_), '实际采集缺少本轮身份')
        grouped_inputs = {case_id: [row for row in inputs if row['caseId'] == case_id] for case_id in selected}
        grouped_assertions = {case_id: [row for row in assertions_ if row['caseId'] == case_id] for case_id in selected}
        require(sum(map(len, grouped_inputs.values())) == len(inputs) == 7, '输入存在额外或缺失用例')
        require(sum(map(len, grouped_assertions.values())) == len(assertions_) == 6, '断言存在额外或缺失用例')
        for case_id in selected:
            require([row['sampleId'] for row in grouped_inputs[case_id]] == plan[case_id]['sampleIds'],
                    f'{side} 实际输入顺序或数量不同')
            require([row['assertionId'] for row in grouped_assertions[case_id]] == plan[case_id]['assertionIds'],
                    f'{side} 实际断言顺序或数量不同')
    ts_inputs, java_inputs = lines(output / 'ts-inputs.jsonl'), lines(output / 'java-inputs.jsonl')
    ts_assertions, java_assertions = lines(output / 'ts-assertions.jsonl'), lines(output / 'java-assertions.jsonl')
    require([row['value'] for row in ts_inputs] == [row['value'] for row in java_inputs], '两端实际输入不同')
    for left, right in zip(ts_assertions, java_assertions):
        require(left['caseId'] == right['caseId'] and left['assertionId'] == right['assertionId'], '断言身份不同')
        audit.compare_actuals(left['caseId'], plan[left['caseId']], left['assertionId'], left['value'], right['value'])
    return {'formalAcceptance': False, 'taskCases': 50, 'casesWithActualInput': 2,
            'taskAssertions': 128, 'assertionsCompared': 6, 'originalMasterTsCases': 15,
            'originalMasterJavaCases': 15, 'inputSamplesCompared': 7, 'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    with tempfile.TemporaryDirectory(prefix='auth-certificate-tamper-') as folder:
        copy = Path(folder) / 'evidence'
        shutil.copytree(output, copy)
        path = copy / 'java-inputs.jsonl'
        rows = lines(path)
        value = rows[0]['value']['bytesHex']
        rows[0]['value']['bytesHex'] = ('00' if value[:2] != '00' else '01') + value[2:]
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
        manifest = read(copy / 'manifest.json')
        manifest['runs']['java']['artifactSha256']['java-inputs.jsonl'] = sha(path)
        (copy / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        try:
            verify(worktree, copy)
        except ValueError as error:
            require('两端实际输入不同' in str(error), '篡改反例未走到逐输入比较')
        else:
            raise ValueError('单字节篡改未被局部门禁拒绝')
    return {'tamperedJavaRandomByteRejected': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'verify', 'tamper'))
    parser.add_argument('--java-worktree', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    try:
        worktree, output = options.java_worktree.resolve(), options.output.resolve()
        result = run(worktree, output) if options.action == 'run' else (
            verify(worktree, output) if options.action == 'verify' else tamper(worktree, output))
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.error(str(error))
