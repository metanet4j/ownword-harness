#!/usr/bin/env python3
"""在 evidence-bundle capture 内执行固定 AuthFetch.property 原测试及 Java 重放。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
FILE = 'src/auth/clients/__tests__/AuthFetch.property.test.ts'
CASE = '8f54eb07d59bc510d411e6a0414613947e6093be3eb591db45d0614a5df41cb9'
TS_NAME = 'AuthFetch authenticated response boundary properties arbitrary bounded response fields always settle and release request state'
JAVA_NAME = 'com.metanet4j.bsv.auth.clients.AuthFetchPropertyTest#boundedResponseFieldsAlwaysSettleAndReleaseState'
JAVA_CLASS = 'com.metanet4j.bsv.auth.clients.AuthFetchPropertyTest'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def emit(args, raw):
    plan = read(args.plan)[CASE]
    corpus = rows(args.corpus)
    fixture = read(TASK / 'fixtures/auth-fetch-property-20260926.json')
    require(hashlib.sha256(Path(args.corpus).read_bytes()).hexdigest() == fixture['corpusSha256']
            and fixture['numRuns'] == 300 and fixture['seed'] == 20260926,
            '版本管理的固定 TS 原输入语料变化')
    consumed = rows(raw / 'inputs.jsonl')
    assertions = rows(raw / 'assertions.jsonl')
    require(len(corpus) == len(consumed) == len(plan['sampleIds']) == 300,
            '固定原输入或 Java 消费不是 300 轮')
    require(consumed == corpus, '当前运行未按固定 TS 原输入逐轮消费')
    require([item['index'] for item in consumed] == list(range(1, 301))
            and all(item['phase'] == 'generate' for item in consumed), '生成顺序或 shrink 阶段变化')
    require(len(assertions) == len(plan['assertionIds']) == 600, '原断言不足 600 条')
    expected_name = TS_NAME if args.side == 'ts' else JAVA_NAME
    for index, assertion in enumerate(assertions):
        require(assertion['test'] == expected_name, '性质测试断言来源变化')
        require(assertion['matcher'] == ('toHaveBeenCalledWith' if index % 2 == 0 else 'toBe')
                and assertion['negated'] is False, '性质测试断言顺序或 matcher 变化')
        if args.side == 'ts':
            require(assertion.get('pass') is True, '原 TS 断言未通过')
    if args.side == 'ts':
        meta = read(raw / 'meta.json')
        require(meta['status'] == 'passed' and meta['calls'] == 300 and meta['shrinkCalls'] == 0
                and meta['configuration']['numRuns'] == 300
                and meta['configuration']['seed'] == 20260926
                and meta['fastCheckVersion'] == fixture['fastCheckVersion']
                and not meta['configuration'].get('path'), 'fast-check 300 轮配置或运行状态变化')
        report = read(args.report)
        require(report['success'] is True and report['numPassedTests'] == report['numTotalTests'] == 1
                and report['numFailedTests'] == report['numPendingTests'] == report['numTodoTests'] == 0,
                '固定 TS 原测试未通过')
    else:
        suite = ET.parse(args.report).getroot()
        tests = suite.findall('testcase')
        require(suite.tag == 'testsuite' and len(tests) == int(suite.get('tests', '-1')) == 1
                and tests[0].get('classname') == JAVA_CLASS
                and tests[0].get('name') == JAVA_NAME.split('#')[1]
                and all(int(suite.get(key, '0')) == 0 for key in ('failures', 'errors', 'skipped')),
                'Java Surefire 原映射测试未通过')
    with Path(os.environ['EVIDENCE_INPUTS_PATH']).open('w') as output:
        for sample_id, value in zip(plan['sampleIds'], consumed):
            output.write(json.dumps({'runId': args.run_id, 'side': args.side, 'caseId': CASE,
                                     'sampleId': sample_id, 'value': value}, ensure_ascii=False) + '\n')
    with Path(os.environ['EVIDENCE_ASSERTIONS_PATH']).open('w') as output:
        for assertion_id, value in zip(plan['assertionIds'], assertions):
            output.write(json.dumps({'runId': args.run_id, 'side': args.side, 'caseId': CASE,
                                     'assertionId': assertion_id, 'value': {
                                         'kind': 'assertion',
                                         **{key: value[key] for key in ('matcher', 'negated', 'actual', 'expected')}}},
                                    ensure_ascii=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    for field in ('plan', 'corpus', 'report', 'raw-dir'):
        parser.add_argument('--' + field, required=True)
    args = parser.parse_args()
    args.run_id = os.environ.get('EVIDENCE_RUN_ID')
    require(args.run_id and args.side == os.environ.get('EVIDENCE_SIDE'),
            '缺少本次 evidence-bundle 运行身份或侧别')
    raw = Path(args.raw_dir).resolve()
    raw.mkdir(parents=True, exist_ok=False)
    report = Path(args.report).resolve()
    if args.side == 'ts':
        require(args.clean is None and args.test is None, 'TS 运行不得伪装 Maven clean test')
        environment = dict(os.environ,
            MIGRATION_AUTH_FETCH_PROPERTY_TS_INPUTS=str(raw / 'inputs.jsonl'),
            MIGRATION_AUTH_FETCH_PROPERTY_TS_META=str(raw / 'meta.json'),
            MIGRATION_PARITY_TS_OBSERVATIONS=str(raw / 'assertions.jsonl'),
            MIGRATION_NETWORK_LOG=str(raw / 'network.jsonl'),
            FAST_CHECK_SEED='20260926', FAST_CHECK_NUM_RUNS='300')
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-parity.cjs'),
                   str(TASK / 'capture-auth-fetch-property.cjs'), '--json',
                   '--outputFile=' + str(raw / 'jest.json')]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
        shutil.copyfile(raw / 'jest.json', report)
    else:
        require((args.clean, args.test) == ('clean', 'test'), 'Java 必须运行 clean test')
        environment = dict(os.environ)
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=AuthFetchPropertyTest',
                   '-Dmigration.authFetch.property.corpus=' + str(Path(args.corpus).resolve()),
                   '-Dmigration.authFetch.property.manifest='
                       + str((TASK / 'fixtures/auth-fetch-property-20260926.json').resolve()),
                   '-Dmigration.authFetch.property.inputs=' + str(raw / 'inputs.jsonl'),
                   '-Dmigration.parity.java.output=' + str(raw / 'assertions.jsonl')]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports/TEST-com.metanet4j.bsv.auth.clients.AuthFetchPropertyTest.xml'
        shutil.copyfile(source, report)
    require(not (raw / 'network.jsonl').exists() or not (raw / 'network.jsonl').read_text().strip(),
            '性质测试触发了外部网络访问')
    emit(args, raw)


if __name__ == '__main__':
    main()
