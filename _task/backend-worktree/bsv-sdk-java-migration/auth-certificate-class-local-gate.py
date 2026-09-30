#!/usr/bin/env python3
"""固定 Certificate 原测试 15/15 的熵、API 输入和实际断言局部门禁。"""
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
FILE = 'src/auth/certificates/__tests/Certificate.test.ts'
CLASS = 'com.metanet4j.bsv.auth.certificates.CertificateTest'
PLAN = TASK / 'auth-certificate-class-plan.json'
METHODS = {
    'e8b66126d21454f747bb9f00b97b085f074325b29dd2703778b82013507b69d8': 'constructsWithValidData',
    '2246bd1a527a2e8517221f1de658ce49a93e4b9863c913aa69ad1482e775120b': 'serializesWithoutSignature',
    '34cd68ff9e9505194c110eb95afafd968f04e51e3b7505623cf93b86a04c8e86': 'serializesWithSignature',
    '1d2196c8be4c42410c827f935e9b016a6abc19316b27719f66afe844c70f2ca9': 'signsAndVerifies',
    '045278fb2257782ced9049d59cc98e55e5ddc204e2d21b2f02a386df72a594ff': 'rejectsTamperedCertificate',
    '5a3ae11b39819d617b0d1bd095ef04525815d16224ec88ebab4ca6941b9dc5ca': 'rejectsMissingSignature',
    '8fdbcb89080c5c7d7a25e50171dccb7533350de366d966877d609c907016bdef': 'rejectsIncorrectSignature',
    '250b89d07965dfa75bfa77282ba497024ecb7c512b64ac6ce068a49df55c9aff': 'handlesEmptyFields',
    '760a39a07db5ca9629f6afe9af2cd886e82f12fad717fbd7b7fb2bd4bd11e4a3': 'excludesSignature',
    '91d7b28b912babc447df41cf219fb197f86b10f4b1171307372af640185236df': 'handlesLongFields',
    '08de563f5c5d36ac5eb9b4f7a2e7effa5684cfeea2efac5239d0fe2fd15ead83': 'roundTripsRevocationOutpoint',
    '9edf2d8cd7bfc281f68c01d368ce82424490a8ea972b78ffd9d398494d294374': 'handlesNoFields',
    '4088cc12a4513718a204525e9cdf8eeba07fe78701e35a59f69f10c8fefaca03': 'rejectsAlreadySignedAndUpdatesCertifier',
    'fe290bf3642f450334d1e21d96bf4168928cb8b85f855a4124a9d744fa5952b2': 'createsFromObject',
    '00b20e32a76fe0d6773933dca70fa31410aba1a74ccde26c69b3c4f8ccd1e642': 'createsFromObjectWithoutSignature',
}


def sources(worktree):
    catalog, mapping, plan = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    cases = {case['id']: case for case in file['cases']}
    require(set(cases) == set(METHODS) == set(plan), '固定 Certificate 用例或计划变化')
    mapped = {case['id']: case for case in mapping['cases'] if case['id'] in cases}
    require(set(mapped) == set(cases), 'Certificate Java 映射缺失')
    for case_id, method in METHODS.items():
        require(mapped[case_id]['java'] == [{'className': CLASS, 'name': method}], 'Certificate Java 身份变化')
        require(mapped[case_id]['assertionIds'] == plan[case_id]['assertionIds'], '固定断言计划变化')
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
                    'capture-auth-certificate-class.cjs', 'capture-parity.cjs',
                    'auth-certificate-class-local-gate.py', 'audit-tests.py')}}
    return file, cases, plan, identity


def assertions(raw, side, destination, run_id, cases, plan):
    titles = {' '.join(case['names']): case_id for case_id, case in cases.items()}
    methods = {method: case_id for case_id, method in METHODS.items()}
    grouped = {case_id: [] for case_id in cases}
    for row in lines(raw):
        case_id = titles.get(row.get('test')) if side == 'ts' else methods.get(row.get('method'))
        if case_id is not None:
            require(row.get('pass', True) is True, '原 TS 断言采集显示失败')
            grouped[case_id].append(row)
    with destination.open('w') as stream:
        for case_id in cases:
            ids = plan[case_id]['assertionIds']
            require(len(grouped[case_id]) == len(ids), f'{side} 实际断言次数变化：{case_id}')
            for identifier, row in zip(ids, grouped[case_id]):
                value = {'kind': 'assertion', 'matcher': row['matcher'], 'negated': row['negated'],
                         'actual': row['actual'], 'expected': row['expected']}
                stream.write(json.dumps({'runId': run_id, 'side': side, 'caseId': case_id,
                                         'assertionId': identifier, 'value': value}, ensure_ascii=False) + '\n')


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, cases, plan, identity = sources(worktree)
    output.mkdir(parents=True)
    config = read(TASK / 'workspace.json')['upstream']
    sdk = TASK.parents[2] / config['path'] / config['packagePath']
    manifest = {'scope': 'Certificate 原文件 15/15；证书任务 15/50 用例同输入',
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
                       str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-auth-certificate-class.cjs'),
                       str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(output / 'ts-jest.json')]
        else:
            env['MIGRATION_AUTH_CERTIFICATE_CLASS_TS_INPUTS'] = str(output / 'ts-inputs.jsonl')
            command = [str(TASK / 'mvn.sh'), '-f', str(worktree / 'pom.xml'), 'clean', 'test',
                       '-Dtest=CertificateTest',
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
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == len(file['cases']) == 15
            and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
            'Certificate 原 Jest 15 例未全部通过')
    require(Counter(tuple(row['ancestorTitles'] + [row['title']])
                    for result in jest['testResults'] for row in result['assertionResults'])
            == Counter(tuple(case['names']) for case in file['cases']), '原 Jest 用例身份不完整')
    suite = ET.parse(output / 'java-surefire.xml').getroot()
    java = suite.findall('testcase')
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == len(java) == 15
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped'))
            and {row.attrib['name'] for row in java} == set(METHODS.values()), 'Java Surefire 15 例不完整')
    for side in ('ts', 'java'):
        actual_inputs = lines(output / f'{side}-inputs.jsonl')
        actual_assertions = lines(output / f'{side}-assertions.jsonl')
        require(all(row['side'] == side and row['runId'] == manifest['runs'][side]['runId']
                    for row in actual_inputs + actual_assertions), '采集缺少本轮身份')
        require(len(actual_inputs) == 42 and len(actual_assertions) == 51, '实际输入或断言数不同')
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
    return {'formalAcceptance': False, 'taskCases': 50, 'casesWithActualInput': 15,
            'taskAssertions': 128, 'assertionsCompared': 51, 'inputSamplesCompared': 42,
            'originalTsCases': 15, 'originalJavaCases': 15, 'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    with tempfile.TemporaryDirectory(prefix='auth-certificate-class-tamper-') as folder:
        copy = Path(folder) / 'evidence'
        shutil.copytree(output, copy)
        path = copy / 'java-inputs.jsonl'
        rows = lines(path)
        row = next(row for row in rows if row['sampleId'] == 'constructor-0')
        row['value']['type'] = 'tampered'
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
    return {'tamperedConstructorInputRejected': True}


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
