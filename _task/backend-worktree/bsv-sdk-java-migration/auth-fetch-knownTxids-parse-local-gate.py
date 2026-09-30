#!/usr/bin/env python3
"""固定 knownTxids 前十个解析原例的真实双侧输入与原断言局部门禁。"""
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
spec = importlib.util.spec_from_file_location('certificate_constructor_gate', TASK / 'auth-certificate-constructor-local-gate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
audit, read, lines, sha, require, execute = base.audit, base.read, base.lines, base.sha, base.require, base.execute
FILE = 'src/auth/clients/__tests__/AuthFetch.knownTxids.test.ts'
CLASS = 'com.metanet4j.bsv.auth.clients.AuthFetchKnownTxidsTest'
PLAN = TASK / 'auth-fetch-knownTxids-input-plan.json'
PROBE = TASK / 'capture-auth-fetch-knownTxids-inputs.cjs'


def sources(worktree):
    catalog, mapping, complete = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    cases = file['cases'][:10]
    ids = {case['id'] for case in cases}
    require(len(file['cases']) == 17 and len(ids) == 10 and set(complete) == {case['id'] for case in file['cases']},
            '固定 knownTxids 原例或结构计划变化')
    plan = {case_id: complete[case_id] for case_id in ids}
    mapped = [item for item in mapping['cases'] if item['id'] in ids]
    require(len(mapped) == 10 and all(item['java'][0]['className'] == CLASS for item in mapped),
            '固定 knownTxids Java 用例映射变化')
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
    require(commit == config['commit'] == catalog['upstreamCommit'], '固定 TS 提交变化')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(),
            '固定 TS 工作树有修改')
    require(sha(upstream / config['packagePath'] / FILE) == file['sha256'], '固定 TS 原文件校验值变化')
    identity = {'upstreamCommit': commit,
                'javaRevision': audit.java_revision({'metanet4j-bsv-sdk': str(worktree)}),
                'frozenSha256': {name: sha(TASK / name) for name in (
                    'module-tests.json', 'test-map.json', 'workspace.json', PLAN.name, PROBE.name,
                    'capture-parity.cjs', 'auth-fetch-knownTxids-parse-local-gate.py', 'audit-tests.py')}}
    return file, cases, plan, mapped, identity


def assertions(raw, side, destination, run_id, cases, plan, mapped):
    names = {' '.join(case['names']): case['id'] for case in cases}
    methods = {item['java'][0]['name']: item['id'] for item in mapped}
    grouped = {case['id']: [] for case in cases}
    for row in lines(raw):
        case_id = names.get(row.get('test')) if side == 'ts' else methods.get(row.get('method'))
        if case_id is not None:
            require(row.get('pass', True) is True, '原始断言失败')
            grouped[case_id].append(row)
    with destination.open('w') as stream:
        for case in cases:
            case_id = case['id']
            ids = plan[case_id]['assertionIds']
            require(len(grouped[case_id]) == len(ids), f'{side} 断言执行次数变化：{case_id}')
            for identity, row in zip(ids, grouped[case_id]):
                value = {key: row[key] for key in ('matcher', 'negated', 'actual', 'expected')}
                value['kind'] = 'assertion'
                if side == 'ts':
                    require(row.get('pass') is True, 'TS 原断言必须实际通过')
                stream.write(json.dumps({'runId': run_id, 'side': side, 'caseId': case_id,
                                         'assertionId': identity, 'value': value}, ensure_ascii=False) + '\n')


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, cases, plan, mapped, identity = sources(worktree)
    output.mkdir(parents=True)
    config = read(TASK / 'workspace.json')['upstream']
    sdk = TASK.parents[2] / config['path'] / config['packagePath']
    manifest = {'scope': 'knownTxids 解析 10/17 原例；Auth 传输局部同输入',
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
    require(manifest.get('formalAcceptance') is False and all(manifest.get(key) == value for key, value in identity.items()),
            '局部来源 manifest 与当前文件不同')
    require(set(manifest['runs']) == {'ts', 'java'} and manifest['runs']['ts']['runId'] != manifest['runs']['java']['runId'],
            '双侧运行身份缺失或相同')
    for side in ('ts', 'java'):
        run_entry = manifest['runs'][side]
        require(run_entry['exitCode'] == 0 and run_entry['finishedAtNs'] > run_entry['startedAtNs']
                and run_entry['sourceRevisionAfter'] == run_entry['sourceRevision'], '原测试未完整执行')
        require(all(sha(output / name) == digest for name, digest in run_entry['artifactSha256'].items()),
                f'{side} 原始产物摘要变化')
        require(not (output / f'{side}-network.jsonl').read_text().strip(), f'{side} 意外网络调用')
    jest = read(output / 'ts-jest.json')
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == len(file['cases']) == 17
            and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
            '固定 knownTxids 原 Jest 17 例未完整通过')
    require(Counter(tuple(row['ancestorTitles'] + [row['title']])
                    for result in jest['testResults'] for row in result['assertionResults'])
            == Counter(tuple(case['names']) for case in file['cases']), '固定 Jest 身份变化')
    suite = ET.parse(output / 'java-surefire.xml').getroot()
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == 17
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
            'Java knownTxids 17 例未完整通过')
    support = ET.parse(output / 'java-support-surefire.xml').getroot()
    require(support.tag == 'testsuite' and int(support.attrib['tests']) >= 2
            and all(int(support.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
            '断言表示层反例未通过')
    ts_inputs, java_inputs = lines(output / 'ts-inputs.jsonl'), lines(output / 'java-inputs.jsonl')
    ids = {case['id'] for case in cases}
    ts_selected = [row for row in ts_inputs if row['caseId'] in ids]
    require(len(ts_inputs) == 17 and len(ts_selected) == len(java_inputs) == 10,
            '双侧真实输入覆盖数量错误')
    for side, rows in (('ts', ts_selected), ('java', java_inputs)):
        require(set(row['caseId'] for row in rows) == ids and all(row['side'] == side
                and row['runId'] == manifest['runs'][side]['runId'] and row['sampleId'] == 'call-0'
                for row in rows), f'{side} 输入身份错误')
    left = {(row['caseId'], row['sampleId']): row['value'] for row in ts_selected}
    right = {(row['caseId'], row['sampleId']): row['value'] for row in java_inputs}
    require(left == right, '双侧真实解析输入不同')
    ts_assertions, java_assertions = lines(output / 'ts-assertions.jsonl'), lines(output / 'java-assertions.jsonl')
    expected_assertions = sum(len(plan[case['id']]['assertionIds']) for case in cases)
    require(len(ts_assertions) == len(java_assertions) == expected_assertions == 12,
            '固定原断言次数错误')
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
    return {'formalAcceptance': False, 'fileCases': 17, 'casesWithActualInput': 10,
            'inputSamplesCompared': 10, 'parserCallsCompared': 12, 'assertionsCompared': 12,
            'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    for artifact, expected_error, mutate in (
            ('java-inputs.jsonl', '双侧真实解析输入不同',
             lambda rows: rows[0]['value']['parseCalls'][0].update(header='tampered')),
            ('java-assertions.jsonl', '实际结果不一致',
             lambda rows: rows[0]['value'].update(actual={'type': 'string', 'value': 'tampered'}))):
        with tempfile.TemporaryDirectory(prefix='known-txids-tamper-') as folder:
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
    return {'tamperedInputRejected': True, 'tamperedAssertionRejected': True}


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
