#!/usr/bin/env python3
"""固定证书验证原测试 8/8 的钱包 mock 输入重放与实际断言局部门禁。"""
import argparse
from collections import Counter
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
spec = importlib.util.spec_from_file_location('certificate_constructor_gate', TASK / 'auth-certificate-constructor-local-gate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
audit, read, lines, sha, require, execute = base.audit, base.read, base.lines, base.sha, base.require, base.execute
FILE = 'src/auth/utils/__tests/validateCertificates.test.ts'
CLASS = 'com.metanet4j.bsv.auth.utils.ValidateCertificatesTest'
PLAN = TASK / 'auth-certificate-validate-plan.json'
METHODS = {
    '07a5dbdce1f6d9f8c7cf13e2e2c12109004de34ab68186fde3e000b0910ee7d0': 'completesForValidInput',
    '8f2b06fb4bac7d2fa27c954289f66801fb2040eea34809930de969d622eac12a': 'rejectsMismatchedIdentity',
    '50be58fc7e604324292df73350ecd0407df30f4cc622793d9b306637944b7fae': 'rejectsInvalidSignature',
    '277465f431806550f2d40562615e591d2abc0a0e60c577cd3f04bc976dfd3ffd': 'rejectsUnrequestedCertifier',
    'a3395b245234950d0b1f062970584e44ecd349cd7dd90dc49bc9655e879db1ae': 'rejectsUnrequestedType',
    'd7c84d782a644801d5697f2676a786714ad43a1999e2d3bd26bfe8b2cc67a9d2': 'decryptsFields',
    '1800d7778017c44690035a8d2505605c296b0b79e6d4724aa21e6515e9f8305d': 'propagatesDecryptionError',
    '4c3b952ad3546f2aa72a27b21cc960ae4cf10925bc9346822aefec05fe0b44c5': 'handlesMultipleCertificates',
}


def sources(worktree):
    catalog, mapping, plan = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    cases = {case['id']: case for case in file['cases']}
    require(set(cases) == set(METHODS) == set(plan), '固定证书验证用例或计划变化')
    mapped = {case['id']: case for case in mapping['cases'] if case['id'] in cases}
    require(set(mapped) == set(cases), '证书验证 Java 映射缺失')
    for case_id, method in METHODS.items():
        require(mapped[case_id]['java'] == [{'className': CLASS, 'name': method}], '证书验证 Java 身份变化')
        require(mapped[case_id]['assertionIds'] == [identifier for identifier in plan[case_id]['assertionIds']
                                                    if not identifier.endswith('#2')], '固定断言计划变化')
    fragment = {**catalog, 'files': [file]}
    review = {**mapping, 'cases': list(mapped.values()), 'siteReviews': [item for item in mapping['siteReviews']
              if item['id'].startswith(FILE + ':')]}
    audit.validate_plan(fragment, review, plan)
    config = read(TASK / 'workspace.json')['upstream']
    upstream = TASK.parents[2] / config['path']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['commit'] == catalog['upstreamCommit'], '固定 TS 提交变化')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(),
            '固定 TS 工作树有修改')
    require(sha(upstream / config['packagePath'] / FILE) == file['sha256'], '固定 TS 原文件校验值变化')
    identity = {'upstreamCommit': commit, 'javaRevision': audit.java_revision({'metanet4j-bsv-sdk': str(worktree)}),
                'frozenSha256': {name: sha(TASK / name) for name in (
                    'module-tests.json', 'test-map.json', 'workspace.json', PLAN.name,
                    'capture-auth-certificate-validate.cjs', 'capture-parity.cjs',
                    'auth-certificate-validate-local-gate.py', 'audit-tests.py')}}
    return file, cases, plan, identity


def assertions(raw, side, destination, run_id, cases, plan):
    titles = {' '.join(case['names']): case_id for case_id, case in cases.items()}
    methods = {method: case_id for case_id, method in METHODS.items()}
    grouped = {case_id: [] for case_id in cases}
    for row in lines(raw):
        case_id = titles.get(row.get('test')) if side == 'ts' else methods.get(row.get('method'))
        if case_id is not None:
            if side == 'ts':
                require(row.get('pass') is True, '原 TS 断言缺少真实通过结果')
            grouped[case_id].append(row)
    with destination.open('w') as stream:
        for case_id in cases:
            ids = plan[case_id]['assertionIds']
            require(len(grouped[case_id]) == len(ids), f'{side} 实际断言次数变化：{case_id}')
            for identifier, row in zip(ids, grouped[case_id]):
                value = {'kind': 'assertion', 'matcher': row['matcher'], 'negated': row['negated'],
                         'actual': row['actual'], 'expected': row['expected']}
                if side == 'ts' and plan[case_id].get('comparisonRules', {}).get(identifier) == \
                        'void-completion-null-adapter-v1':
                    value['pass'] = row['pass']
                stream.write(json.dumps({'runId': run_id, 'side': side, 'caseId': case_id,
                                         'assertionId': identifier, 'value': value}, ensure_ascii=False) + '\n')


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, cases, plan, identity = sources(worktree)
    output.mkdir(parents=True)
    config = read(TASK / 'workspace.json')['upstream']
    sdk = TASK.parents[2] / config['path'] / config['packagePath']
    manifest = {'scope': '证书验证原文件 8/8；证书任务 8/50 用例同输入',
                'formalAcceptance': False, **identity, 'runs': {}}
    for side in ('ts', 'java'):
        run_id = uuid.uuid4().hex
        env = dict(os.environ, EVIDENCE_RUN_ID=run_id, EVIDENCE_SIDE=side,
                   EVIDENCE_INPUTS_PATH=str(output / f'{side}-inputs.jsonl'),
                   EVIDENCE_ASSERTIONS_PATH=str(output / f'{side}-assertions.jsonl'),
                   MIGRATION_NETWORK_LOG=str(output / f'{side}-network.jsonl'))
        (output / f'{side}-network.jsonl').touch()
        if side == 'ts':
            env['MIGRATION_PARITY_TS_OBSERVATIONS'] = str(output / 'ts-parity-raw.jsonl')
            command = [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand',
                       '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                       str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-auth-certificate-validate.cjs'),
                       str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(output / 'ts-jest.json')]
        else:
            env['MIGRATION_AUTH_CERTIFICATE_VALIDATE_TS_INPUTS'] = str(output / 'ts-inputs.jsonl')
            command = [str(TASK / 'mvn.sh'), '-f', str(worktree / 'pom.xml'), 'clean', 'test',
                       '-Dtest=ValidateCertificatesTest',
                       '-Dmigration.parity.java.output=' + str(worktree / 'target/upstream-observations/parity-java.jsonl')]
        manifest['runs'][side] = {'runId': run_id, 'command': command, 'startedAtNs': time.time_ns(),
                                  'sourceRevision': identity['upstreamCommit'] if side == 'ts' else identity['javaRevision']}
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        execute(command, env, output / f'{side}.log')
        if side == 'java':
            shutil.copyfile(worktree / 'target/upstream-observations/parity-java.jsonl', output / 'java-parity-raw.jsonl')
            shutil.copyfile(worktree / 'target/surefire-reports' / f'TEST-{CLASS}.xml', output / 'java-surefire.xml')
        assertions(output / f'{side}-parity-raw.jsonl', side, output / f'{side}-assertions.jsonl',
                   run_id, cases, plan)
        after = sources(worktree)[3]
        require(after == identity, '采集期间源码、映射或工具变化')
        names = [f'{side}-inputs.jsonl', f'{side}-assertions.jsonl', f'{side}-parity-raw.jsonl',
                 f'{side}-network.jsonl', f'{side}.log', 'ts-jest.json' if side == 'ts' else 'java-surefire.xml']
        manifest['runs'][side].update(finishedAtNs=time.time_ns(), exitCode=0,
                                      sourceRevisionAfter=after['upstreamCommit'] if side == 'ts' else after['javaRevision'],
                                      artifactSha256={name: sha(output / name) for name in names})
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return verify(worktree, output)


def verify(worktree, output):
    file, cases, plan, identity = sources(worktree)
    manifest = read(output / 'manifest.json')
    require(manifest.get('formalAcceptance') is False and all(manifest.get(key) == identity[key] for key in identity),
            '局部 manifest 与当前来源不同')
    require(set(manifest['runs']) == {'ts', 'java'}
            and manifest['runs']['ts']['runId'] != manifest['runs']['java']['runId'], '两端运行身份缺失或相同')
    for side in ('ts', 'java'):
        entry = manifest['runs'][side]
        require(entry['exitCode'] == 0 and entry['finishedAtNs'] > entry['startedAtNs']
                and entry['sourceRevisionAfter'] == entry['sourceRevision'], '原测试未完整执行')
        require(all(sha(output / name) == digest for name, digest in entry['artifactSha256'].items()),
                f'{side} 原始产物摘要变化')
        require(not (output / f'{side}-network.jsonl').read_text().strip(), f'{side} 意外网络调用')
    jest = read(output / 'ts-jest.json')
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == len(file['cases']) == 8
            and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
            '证书验证原 Jest 8 例未全部通过')
    require(Counter(tuple(row['ancestorTitles'] + [row['title']])
                    for result in jest['testResults'] for row in result['assertionResults'])
            == Counter(tuple(case['names']) for case in file['cases']), '原 Jest 用例身份不完整')
    suite = ET.parse(output / 'java-surefire.xml').getroot()
    java = suite.findall('testcase')
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == len(java) == 8
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped'))
            and {row.attrib['name'] for row in java} == set(METHODS.values()), 'Java Surefire 8 例不完整')
    for side in ('ts', 'java'):
        actual_inputs = lines(output / f'{side}-inputs.jsonl')
        actual_assertions = lines(output / f'{side}-assertions.jsonl')
        require(all(row['side'] == side and row['runId'] == manifest['runs'][side]['runId']
                    for row in actual_inputs + actual_assertions), '采集缺少本轮身份')
        require(len(actual_inputs) == 21 and len(actual_assertions) == 16, '实际输入或断言数不同')
        for case_id in cases:
            require([row['sampleId'] for row in actual_inputs if row['caseId'] == case_id]
                    == plan[case_id]['sampleIds'], f'{side} 样本身份或顺序不同')
            require([row['assertionId'] for row in actual_assertions if row['caseId'] == case_id]
                    == plan[case_id]['assertionIds'], f'{side} 断言身份或顺序不同')
    ts_inputs, java_inputs = lines(output / 'ts-inputs.jsonl'), lines(output / 'java-inputs.jsonl')
    ts_assertions, java_assertions = lines(output / 'ts-assertions.jsonl'), lines(output / 'java-assertions.jsonl')
    require([(row['caseId'], row['sampleId'], row['value']) for row in ts_inputs]
            == [(row['caseId'], row['sampleId'], row['value']) for row in java_inputs], '两端实际输入不同')
    for left, right in zip(ts_assertions, java_assertions):
        require(left['caseId'] == right['caseId'] and left['assertionId'] == right['assertionId'], '断言身份不同')
        audit.compare_actuals(left['caseId'], plan[left['caseId']], left['assertionId'], left['value'], right['value'])
    return {'formalAcceptance': False, 'taskCases': 50, 'casesWithActualInput': 8,
            'taskAssertions': 128, 'assertionsCompared': 16, 'inputSamplesCompared': 21,
            'originalTsCases': 8, 'originalJavaCases': 8, 'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    with tempfile.TemporaryDirectory(prefix='auth-certificate-validate-tamper-') as folder:
        copy = Path(folder) / 'evidence'
        shutil.copytree(output, copy)
        path = copy / 'java-inputs.jsonl'
        rows = lines(path)
        row = next(row for row in rows if row['sampleId'] == 'verify-0'
                   and row['value']['outcome']['kind'] == 'return'
                   and row['value']['outcome']['value'] is True)
        row['value']['outcome']['value'] = False
        path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
        manifest = read(copy / 'manifest.json')
        manifest['runs']['java']['artifactSha256']['java-inputs.jsonl'] = sha(path)
        (copy / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        try:
            verify(worktree, copy)
        except ValueError as error:
            require('两端实际输入不同' in str(error), '篡改未走到逐输入比较')
        else:
            raise ValueError('单字段篡改未被局部门禁拒绝')
    return {'tamperedVerifyResponseRejected': True}


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
