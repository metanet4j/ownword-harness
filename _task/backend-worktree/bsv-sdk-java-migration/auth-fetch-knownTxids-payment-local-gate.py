#!/usr/bin/env python3
"""固定 knownTxids 六例付款入口的双侧原输入与原断言局部门禁。"""
import argparse
import copy
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
spec = importlib.util.spec_from_file_location('known_parse_gate', TASK / 'auth-fetch-knownTxids-parse-local-gate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
audit, read, lines, sha, require, execute, assertions = (base.audit, base.read, base.lines,
                                                        base.sha, base.require, base.execute, base.assertions)
FILE, CLASS, PLAN, PROBE = base.FILE, base.CLASS, base.PLAN, base.PROBE
METHODS = {
    'forwardsDeclaredTxidsToFreshPayment', 'absentHeaderOmitsKnownTxidsOption',
    'malformedHeaderDoesNotBlockPayment', 'changedKnownTxidsHintReusesPayment',
    'missingKnownTxidsHintReusesPayment', 'repricedPaymentUsesNewKnownTxids',
}


def sources(worktree):
    catalog, mapping, complete = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    mapped = [item for item in mapping['cases'] if item['java'][0]['className'] == CLASS
              and item['java'][0]['name'] in METHODS]
    ids = {item['id'] for item in mapped}
    cases = [case for case in file['cases'] if case['id'] in ids]
    require(len(file['cases']) == 17 and len(mapped) == len(ids) == len(cases) == len(METHODS) == 6
            and {item['java'][0]['name'] for item in mapped} == METHODS
            and set(complete) == {case['id'] for case in file['cases']},
            '固定 knownTxids 六个付款原例或结构计划变化')
    plan = {case_id: complete[case_id] for case_id in ids}
    reviews = [item for item in mapping['siteReviews']
               if item['id'].startswith(FILE + ':') and set(item['caseIds']) & ids]
    reviewed_sites = {item['id'] for item in reviews}
    fragment_file = {**file, 'cases': cases,
                     'sites': [site for site in file['sites'] if site['id'] in reviewed_sites]}
    audit.validate_plan({**catalog, 'files': [fragment_file]},
                        {**mapping, 'cases': mapped, 'siteReviews': reviews}, plan)
    config = read(TASK / 'workspace.json')['upstream']
    upstream = TASK.parents[2] / config['path']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['commit'] == catalog['upstreamCommit']
            and not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip()
            and sha(upstream / config['packagePath'] / FILE) == file['sha256'], '固定 TS 来源变化')
    identity = {'upstreamCommit': commit,
                'javaRevision': audit.java_revision({'metanet4j-bsv-sdk': str(worktree)}),
                'frozenSha256': {name: sha(TASK / name) for name in (
                    'module-tests.json', 'test-map.json', 'workspace.json', PLAN.name, PROBE.name,
                    'capture-parity.cjs', 'auth-fetch-knownTxids-payment-local-gate.py', 'audit-tests.py')}}
    return file, cases, plan, mapped, identity


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, cases, plan, mapped, identity = sources(worktree)
    output.mkdir(parents=True)
    config = read(TASK / 'workspace.json')['upstream']
    sdk = TASK.parents[2] / config['path'] / config['packagePath']
    manifest = {'scope': 'AuthFetch.knownTxids 6/17 付款原例及8次付款入口同输入',
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
                       str(TASK / 'ts-offline-guard.cjs'), str(PROBE), str(TASK / 'capture-parity.cjs'),
                       '--json', '--outputFile=' + str(output / 'ts-jest.json')]
        else:
            env['MIGRATION_AUTH_FETCH_KNOWN_TXIDS_TS_INPUTS'] = str(output / 'ts-inputs.jsonl')
            command = [str(TASK / 'mvn.sh'), '-f', str(worktree / 'pom.xml'), 'clean', 'test',
                       '-Dtest=AuthFetchKnownTxidsTest,RecordingAssertionsSemanticsTest',
                       '-Dmigration.parity.java.output=' + str(worktree / 'target/upstream-observations/parity-java.jsonl')]
        manifest['runs'][side] = {'runId': run_id, 'command': command, 'startedAtNs': time.time_ns(),
                                  'sourceRevision': identity['upstreamCommit'] if side == 'ts' else identity['javaRevision']}
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        execute(command, env, output / f'{side}.log')
        if side == 'java':
            shutil.copyfile(worktree / 'target/upstream-observations/parity-java.jsonl', output / 'java-parity-raw.jsonl')
            shutil.copyfile(worktree / 'target/surefire-reports' / f'TEST-{CLASS}.xml', output / 'java-surefire.xml')
            shutil.copyfile(worktree / 'target/surefire-reports' /
                            'TEST-com.metanet4j.bsv.support.RecordingAssertionsSemanticsTest.xml',
                            output / 'java-support-surefire.xml')
        assertions(output / f'{side}-parity-raw.jsonl', side, output / f'{side}-assertions.jsonl',
                   run_id, cases, plan, mapped)
        require(sources(worktree)[4] == identity, '采集期间来源变化')
        names = [f'{side}-inputs.jsonl', f'{side}-assertions.jsonl', f'{side}-parity-raw.jsonl',
                 f'{side}-network.jsonl', f'{side}.log', 'ts-jest.json' if side == 'ts' else 'java-surefire.xml']
        if side == 'java': names.append('java-support-surefire.xml')
        manifest['runs'][side].update(finishedAtNs=time.time_ns(), exitCode=0,
                                      sourceRevisionAfter=manifest['runs'][side]['sourceRevision'],
                                      artifactSha256={name: sha(output / name) for name in names})
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    return verify(worktree, output)


def verify(worktree, output):
    file, cases, plan, mapped, identity = sources(worktree)
    manifest = read(output / 'manifest.json')
    require(manifest.get('formalAcceptance') is False
            and all(manifest.get(key) == value for key, value in identity.items()), '局部来源 manifest 与当前文件不同')
    require(set(manifest['runs']) == {'ts', 'java'}
            and manifest['runs']['ts']['runId'] != manifest['runs']['java']['runId'], '双侧运行身份缺失或相同')
    for side in ('ts', 'java'):
        entry = manifest['runs'][side]
        require(entry['exitCode'] == 0 and entry['finishedAtNs'] > entry['startedAtNs']
                and entry['sourceRevisionAfter'] == entry['sourceRevision']
                and all(sha(output / name) == digest for name, digest in entry['artifactSha256'].items())
                and not (output / f'{side}-network.jsonl').read_text().strip(), f'{side} 原运行或来源无效')
    jest = read(output / 'ts-jest.json')
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == 17
            and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
            '固定 knownTxids 原 Jest 17 例未完整通过')
    require(Counter(tuple(row['ancestorTitles'] + [row['title']])
                    for result in jest['testResults'] for row in result['assertionResults'])
            == Counter(tuple(case['names']) for case in file['cases']), '固定 Jest 身份变化')
    for name, count in (('java-surefire.xml', 17), ('java-support-surefire.xml', 21)):
        suite = ET.parse(output / name).getroot()
        require(suite.tag == 'testsuite' and int(suite.attrib['tests']) >= count
                and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
                'Java 原例或断言表示层回归未通过')
    ids = {case['id'] for case in cases}
    ts_inputs = lines(output / 'ts-inputs.jsonl')
    java_inputs = lines(output / 'java-inputs.jsonl')
    ts_selected = [row for row in ts_inputs if row['caseId'] in ids]
    java_selected = [row for row in java_inputs if row['caseId'] in ids]
    require(len(ts_inputs) == 17 and len(java_inputs) == 16
            and len(ts_selected) == len(java_selected) == 6,
            '六例真实付款输入覆盖数量错误')
    for side, rows in (('ts', ts_selected), ('java', java_selected)):
        require(set(row['caseId'] for row in rows) == ids and all(row['side'] == side
                and row['runId'] == manifest['runs'][side]['runId'] and row['sampleId'] == 'call-0'
                for row in rows), f'{side} 付款输入身份错误')
    left = {row['caseId']:row['value'] for row in ts_selected}
    right = {row['caseId']:row['value'] for row in java_selected}
    for case_id, original in left.items():
        replay = copy.deepcopy(right[case_id])
        require(original['kind'] == replay['kind'] == 'AuthFetch.knownTxidsInput'
                and original['parseCalls'] == replay['parseCalls'] == []
                and len(original['paymentCalls']) == len(replay['paymentCalls']),
                '付款原例入口次数或解析入口不同')
        for call in original['paymentCalls']:
            require(call['response']['bodyUsed'] is False, '固定 TS 响应正文已消费')
        for call in replay['paymentCalls']:
            require('bodyUsed' not in call['response'], 'Java 伪造 Response.bodyUsed')
            call['response']['bodyUsed'] = False
        require(original == replay, '双侧付款 URL/config/Response 真输入不同')
    ts_assertions, java_assertions = lines(output / 'ts-assertions.jsonl'), lines(output / 'java-assertions.jsonl')
    require(len(ts_assertions) == len(java_assertions) == 25, '固定六例原断言次数错误')
    for side, rows in (('ts', ts_assertions), ('java', java_assertions)):
        require(all(row['side'] == side and row['runId'] == manifest['runs'][side]['runId']
                    for row in rows), f'{side} 断言运行身份错误')
        for case in cases:
            require([row['assertionId'] for row in rows if row['caseId'] == case['id']]
                    == plan[case['id']]['assertionIds'], f'{side} 断言身份或顺序错误：{case["id"]}')
    for left_row, right_row in zip(ts_assertions, java_assertions):
        require((left_row['caseId'], left_row['assertionId']) ==
                (right_row['caseId'], right_row['assertionId']), '原断言身份不同')
        audit.compare_actuals(left_row['caseId'], plan[left_row['caseId']], left_row['assertionId'],
                              left_row['value'], right_row['value'])
    return {'formalAcceptance': False, 'fileCases': 17, 'casesWithActualInput': 6,
            'inputSamplesCompared': 6, 'paymentCallsCompared': 8, 'assertionsCompared': 25,
            'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    for artifact, expected_error, mutate in (
            ('java-inputs.jsonl', '双侧付款 URL/config/Response 真输入不同',
             lambda rows: next(row for row in rows if row['caseId'].startswith('6efec5be'))
             ['value']['paymentCalls'][0]['response']['headers'].update(
                 {'x-bsv-payment-known-txids': 'tampered'})),
            ('java-assertions.jsonl', '实际结果不一致',
             lambda rows: rows[0]['value'].update(actual={'type': 'string', 'value': 'tampered'}))):
        with tempfile.TemporaryDirectory(prefix='known-payment-tamper-') as folder:
            target = Path(folder) / 'evidence'
            shutil.copytree(output, target)
            path = target / artifact
            rows = lines(path)
            mutate(rows)
            path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            manifest = read(target / 'manifest.json')
            manifest['runs']['java']['artifactSha256'][artifact] = sha(path)
            (target / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
            try:
                verify(worktree, target)
            except ValueError as error:
                require(expected_error in str(error), f'篡改未进入目标比较：{artifact}')
            else:
                raise ValueError(f'单字段篡改未被拒绝：{artifact}')
    return {'tamperedPaymentInputRejected': True, 'tamperedAssertionRejected': True}


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
