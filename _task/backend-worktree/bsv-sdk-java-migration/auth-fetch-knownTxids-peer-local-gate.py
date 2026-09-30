#!/usr/bin/env python3
"""固定 knownTxids 真实 Peer 付款原例的双侧原输入与原断言局部门禁。"""
import argparse
import copy
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
spec = importlib.util.spec_from_file_location('known_payment_gate', TASK / 'auth-fetch-knownTxids-payment-local-gate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
audit, read, lines, sha, require, execute, assertions = (base.audit, base.read, base.lines,
                                                         base.sha, base.require, base.execute, base.assertions)
FILE, CLASS, PLAN = base.FILE, base.CLASS, base.PLAN
PROBE = TASK / 'capture-auth-fetch-knownTxids-peer-inputs.cjs'
ENTRY_PROBE = TASK / 'capture-auth-fetch-knownTxids-inputs.cjs'
CASE = '189790cbac0f42250b37519c090b906ad9619403b2b3dd8f02ee0be3fe1e1b09'
METHOD = 'authenticatedPeerHintSurvivesPaidRetry'
KIND = 'AuthFetch.knownTxidsPeerInput'


def sources(worktree):
    catalog, mapping, complete = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), read(PLAN)
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    mapped = [item for item in mapping['cases'] if item['java'][0]['className'] == CLASS
              and item['java'][0]['name'] == METHOD]
    cases = [case for case in file['cases'] if case['id'] == CASE]
    require(len(file['cases']) == 17 and len(mapped) == len(cases) == 1
            and mapped[0]['id'] == CASE and set(complete) == {case['id'] for case in file['cases']},
            '固定 knownTxids Peer 原例或结构计划变化')
    plan = {CASE: complete[CASE]}
    reviews = [item for item in mapping['siteReviews']
               if item['id'].startswith(FILE + ':') and CASE in item['caseIds']]
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
                    ENTRY_PROBE.name, 'capture-parity.cjs',
                    'auth-fetch-knownTxids-peer-local-gate.py', 'audit-tests.py')}}
    return file, cases, plan, mapped, identity


def run(worktree, output):
    require(not output.exists(), '证据目录已存在，必须使用新目录')
    file, cases, plan, mapped, identity = sources(worktree)
    output.mkdir(parents=True)
    config = read(TASK / 'workspace.json')['upstream']
    sdk = TASK.parents[2] / config['path'] / config['packagePath']
    manifest = {'scope': 'AuthFetch.knownTxids 1/17 真实 Peer 付款原例及同输入',
                'formalAcceptance': False, **identity, 'runs': {}}
    for side in ('ts', 'java'):
        run_id = uuid.uuid4().hex
        env = dict(os.environ, EVIDENCE_RUN_ID=run_id, EVIDENCE_SIDE=side,
                   EVIDENCE_INPUTS_PATH=str(output / f'{side}-inputs.jsonl'),
                   EVIDENCE_ASSERTIONS_PATH=str(output / f'{side}-assertions.jsonl'),
                   MIGRATION_NETWORK_LOG=str(output / f'{side}-network.jsonl'))
        (output / f'{side}-network.jsonl').touch()
        if side == 'ts':
            # 入口探针与 Peer 探针都占用模块工厂，只能分两次运行同一固定文件后合并语料。
            entry_id = uuid.uuid4().hex
            entry_env = dict(env, EVIDENCE_RUN_ID=entry_id,
                             EVIDENCE_INPUTS_PATH=str(output / 'ts-entry-inputs.jsonl'),
                             EVIDENCE_ASSERTIONS_PATH=str(output / 'ts-entry-assertions.jsonl'),
                             MIGRATION_PARITY_TS_OBSERVATIONS=str(output / 'ts-parity-raw.jsonl'))
            entry_command = [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand',
                             '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                             str(TASK / 'ts-offline-guard.cjs'), str(ENTRY_PROBE),
                             str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(output / 'ts-jest.json')]
            peer_id = uuid.uuid4().hex
            peer_env = dict(env, EVIDENCE_RUN_ID=peer_id,
                            EVIDENCE_INPUTS_PATH=str(output / 'ts-peer-inputs.jsonl'),
                            EVIDENCE_ASSERTIONS_PATH=str(output / 'ts-peer-assertions.jsonl'),
                            MIGRATION_NETWORK_LOG=str(output / 'ts-peer-network.jsonl'))
            (output / 'ts-peer-network.jsonl').touch()
            peer_command = [str(TASK / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--runInBand',
                            '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                            str(TASK / 'ts-offline-guard.cjs'), str(PROBE),
                            '--json', '--outputFile=' + str(output / 'ts-peer-jest.json')]
            command = entry_command
        else:
            env['MIGRATION_AUTH_FETCH_KNOWN_TXIDS_TS_INPUTS'] = str(output / 'ts-inputs.jsonl')
            command = [str(TASK / 'mvn.sh'), '-f', str(worktree / 'pom.xml'), 'clean', 'test',
                       '-Dtest=AuthFetchKnownTxidsTest,RecordingAssertionsSemanticsTest',
                       '-Dmigration.parity.java.output=' + str(worktree / 'target/upstream-observations/parity-java.jsonl')]
        manifest['runs'][side] = {'runId': run_id, 'command': command, 'startedAtNs': time.time_ns(),
                                  'sourceRevision': identity['upstreamCommit'] if side == 'ts' else identity['javaRevision']}
        (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        if side == 'ts':
            manifest['runs']['ts']['runId'] = entry_id
            manifest['runs']['ts']['command'] = entry_command
            manifest['runs']['tsPeer'] = {'runId': peer_id, 'command': peer_command,
                                          'startedAtNs': time.time_ns(),
                                          'sourceRevision': identity['upstreamCommit']}
            (output / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
            execute(entry_command, entry_env, output / 'ts.log')
            execute(peer_command, peer_env, output / 'ts-peer.log')
            (output / 'ts-inputs.jsonl').write_text(
                (output / 'ts-entry-inputs.jsonl').read_text() + (output / 'ts-peer-inputs.jsonl').read_text())
            manifest['runs']['tsPeer'].update(finishedAtNs=time.time_ns(), exitCode=0,
                                              sourceRevisionAfter=identity['upstreamCommit'],
                                              artifactSha256={name: sha(output / name) for name in (
                                                  'ts-peer-inputs.jsonl', 'ts-peer-jest.json',
                                                  'ts-peer-network.jsonl', 'ts-peer.log')})
        else:
            execute(command, env, output / f'{side}.log')
            shutil.copyfile(worktree / 'target/upstream-observations/parity-java.jsonl', output / 'java-parity-raw.jsonl')
            shutil.copyfile(worktree / 'target/surefire-reports' / f'TEST-{CLASS}.xml', output / 'java-surefire.xml')
            shutil.copyfile(worktree / 'target/surefire-reports' /
                            'TEST-com.metanet4j.bsv.support.RecordingAssertionsSemanticsTest.xml',
                            output / 'java-support-surefire.xml')
        assertions(output / f'{side}-parity-raw.jsonl', side, output / f'{side}-assertions.jsonl',
                   run_id if side == 'java' else entry_id, cases, plan, mapped)
        require(sources(worktree)[4] == identity, '采集期间来源变化')
        names = [f'{side}-inputs.jsonl', f'{side}-assertions.jsonl', f'{side}-parity-raw.jsonl',
                 f'{side}-network.jsonl', f'{side}.log', 'ts-jest.json' if side == 'ts' else 'java-surefire.xml']
        if side == 'ts':
            names += ['ts-entry-inputs.jsonl', 'ts-peer-inputs.jsonl', 'ts-peer-jest.json', 'ts-peer.log']
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
    runs = manifest['runs']
    require(set(runs) == {'ts', 'java', 'tsPeer'}
            and len({runs[name]['runId'] for name in runs}) == 3, '运行身份缺失或重复')
    for name in ('ts', 'java', 'tsPeer'):
        entry = runs[name]
        require(entry['exitCode'] == 0 and entry['finishedAtNs'] > entry['startedAtNs']
                and entry['sourceRevisionAfter'] == entry['sourceRevision']
                and all(sha(output / artifact) == digest for artifact, digest in entry['artifactSha256'].items())
                and not (output / ('ts-peer-network.jsonl' if name == 'tsPeer' else f'{name}-network.jsonl')
                         ).read_text().strip(), f'{name} 原运行或来源无效')
    for report in ('ts-jest.json', 'ts-peer-jest.json'):
        jest = read(output / report)
        require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == 17
                and jest['numFailedTests'] == jest['numPendingTests'] == jest['numTodoTests'] == 0,
                f'固定 knownTxids 原 Jest 17 例未完整通过：{report}')
    suite = ET.parse(output / 'java-surefire.xml').getroot()
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == 17
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
            'Java 原例未完整通过')
    ts_rows = lines(output / 'ts-inputs.jsonl')
    java_rows = lines(output / 'java-inputs.jsonl')
    ts_peer = [row for row in ts_rows if row['value'].get('kind') == KIND]
    java_peer = [row for row in java_rows if row['value'].get('kind') == KIND]
    require(len(ts_peer) == len(java_peer) == 1 and ts_peer[0]['caseId'] == java_peer[0]['caseId'] == CASE,
            'Peer 原例真实输入条数或身份错误')
    require(all(row['side'] == 'ts' and row['runId'] == runs['tsPeer']['runId'] for row in ts_peer)
            and all(row['side'] == 'ts' and row['runId'] == runs['ts']['runId']
                    for row in ts_rows if row['value'].get('kind') != KIND), 'TS 输入运行身份错误')
    require(all(row['side'] == 'java' and row['runId'] == runs['java']['runId'] for row in java_rows),
            'Java 输入运行身份错误')
    require(ts_peer[0]['value'] == java_peer[0]['value'], '双侧 Peer 随机源/发送/回调真输入不同')
    ts_assertions = [row for row in lines(output / 'ts-assertions.jsonl') if row['caseId'] == CASE]
    java_assertions = [row for row in lines(output / 'java-assertions.jsonl') if row['caseId'] == CASE]
    expected_ids = plan[CASE]['assertionIds']
    require([row['assertionId'] for row in ts_assertions] == expected_ids
            and [row['assertionId'] for row in java_assertions] == expected_ids,
            'Peer 原例断言身份或顺序错误')
    require(all(row['runId'] == runs['ts']['runId'] for row in ts_assertions)
            and all(row['runId'] == runs['java']['runId'] for row in java_assertions), '断言运行身份错误')
    for left, right in zip(ts_assertions, java_assertions):
        audit.compare_actuals(CASE, plan[CASE], left['assertionId'], left['value'], right['value'])
    return {'formalAcceptance': False, 'fileCases': 17, 'casesWithActualInput': 1,
            'peerInputsCompared': 1, 'assertionsCompared': len(expected_ids),
            'javaRevision': identity['javaRevision']}


def tamper(worktree, output):
    verify(worktree, output)
    for artifact, expected_error, mutate in (
            ('java-inputs.jsonl', '双侧 Peer 随机源/发送/回调真输入不同',
             lambda rows: [row for row in rows if row['value'].get('kind') == KIND][0]['value']
             ['delivered'][0]['payload'].__setitem__(0, 255)),
            ('java-assertions.jsonl', '实际结果不一致',
             lambda rows: [row for row in rows if row['caseId'] == CASE][0]['value']
             .update(actual={'type': 'string', 'value': 'tampered'}))):
        with tempfile.TemporaryDirectory(prefix='known-peer-tamper-') as folder:
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
                require(expected_error in str(error), f'篡改未走到预期判定：{error}')
            else:
                raise ValueError('篡改未被局部门禁拒绝')
    return {'tamperedPeerInputRejected': True, 'tamperedAssertionRejected': True}


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
