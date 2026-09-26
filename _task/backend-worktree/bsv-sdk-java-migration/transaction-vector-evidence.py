#!/usr/bin/env python3
"""记录固定交易向量的实际 SDK 输入和原断言；此局部证据不充抵 P0 全量门禁。"""
import argparse
from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import uuid

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('script_vector_evidence', TASK / 'script-vector-evidence.py')
common = importlib.util.module_from_spec(spec)
spec.loader.exec_module(common)
audit, preflight = common.audit, common.preflight
read, write, rows, write_rows = common.read, common.write, common.rows, common.write_rows
source_revision = common.source_revision
SDK = common.SDK
FILE = 'src/transaction/__tests/Transaction.test.ts'
CLASS = 'com.metanet4j.bsv.transaction.TransactionCompleteVectorsTest'


def prepare(folder):
    catalog, mapping = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json')
    selected = [case for case in mapping['cases'] if any(java['className'] == CLASS for java in case['java'])]
    audit.require(len(selected) == 659, '固定 Transaction 向量注册数变化')
    ids = {case['id'] for case in selected}
    source = next(file for file in catalog['files'] if file['path'] == FILE)
    local_file = dict(source, cases=[case for case in source['cases'] if case['id'] in ids],
                      sites=[site for site in source['sites'] if 909 <= site['line'] <= 914
                             or 995 <= site['line'] <= 1066])
    local_catalog = dict(catalog, files=[local_file], partialImplementationOnly=True)
    sites = {site['id'] for site in local_file['sites']}
    local_mapping = dict(mapping, cases=selected, siteReviews=[
        dict(review, caseIds=[key for key in review['caseIds'] if key in ids])
        for review in mapping['siteReviews'] if review['id'] in sites])
    plan = {case['id']: {'sampleIds': ['input#1', 'input#2'] if case['java'][0]['name'].startswith('sighashVector')
             else ['input#1'], 'assertionIds': case['assertionIds'],
             'assertionSites': {identity: identity for identity in case['assertionIds']}, 'loopSamples': {}}
            for case in selected}
    preflight.validate_subset(catalog, mapping, local_catalog, local_mapping, plan)
    folder.mkdir(parents=True, exist_ok=False)
    for name, value in [('catalog', local_catalog), ('mapping', local_mapping), ('input-plan', plan)]:
        write(folder / (name + '.json'), value)
    print(json.dumps({'cases': len(plan), 'samples': sum(len(row['sampleIds']) for row in plan.values()),
                      'assertions': sum(len(row['assertionIds']) for row in plan.values())}))


def fingerprints(plan_folder):
    paths = [Path(__file__), TASK / 'capture-transaction-vector-inputs.cjs', TASK / 'capture-parity.cjs',
             TASK / 'ts-offline-guard.cjs', TASK / 'module-tests.json', TASK / 'test-map.json',
             *(plan_folder / (name + '.json') for name in ('catalog', 'mapping', 'input-plan'))]
    return {str(path): audit.digest(path) for path in paths}


def validate_inputs(method, values):
    if method.startswith('sighashVector'):
        audit.require(len(values) == 2 and values[0].get('method') == 'Transaction.fromBinary'
                      and values[1].get('operation') == 'sighash-format', 'sighash 实际 SDK 调用不同')
        params = values[1].get('args', [None])[0]
        fields = {'sourceTXID', 'sourceOutputIndex', 'sourceSatoshis', 'transactionVersion',
                  'otherInputs', 'outputs', 'inputIndex', 'subscriptHex', 'inputSequence',
                  'lockTime', 'scope', 'ignoreChronicle'}
        audit.require(isinstance(params, dict) and set(params) == fields
                      and params['ignoreChronicle'] is True and all(isinstance(params[key], str)
                      for key in fields - {'ignoreChronicle'}), 'sighash 实际参数不完整')
        version = int(params['transactionVersion'])
        audit.require(0 <= version <= 0xffff_ffff, 'transactionVersion 须保留原 32 位无符号值')
    else:
        expected = 'Transaction.fromHex' if method == 'largeTransactionTxid' else 'Transaction.fromBinary'
        audit.require(len(values) == 1 and values[0].get('method') == expected,
                      '交易序列化实际 SDK 调用不同')
    audit.require(all(isinstance(value.get('args'), list) and len(value['args']) == 1 for value in values),
                  '交易向量参数数量变化')
    audit.require(isinstance(values[0]['args'][0], str)
                  and len(values[0]['args'][0]) % 2 == 0
                  and all(letter in '0123456789abcdef' for letter in values[0]['args'][0]),
                  '交易向量实际二进制输入不是小写 hex')


def normalize(folder, plan_folder, side, run_id, emit=True):
    mapping, plan = read(plan_folder / 'mapping.json'), read(plan_folder / 'input-plan.json')
    by_java = {java['className'] + '#' + java['name']: case['id']
               for case in mapping['cases'] for java in case['java']}
    by_name = {(' '.join(case['names']), case['occurrence']): case['id']
               for file in read(plan_folder / 'catalog.json')['files'] for case in file['cases']}
    methods = {case['id']: case['java'][0]['name'] for case in mapping['cases']}
    inputs, assertions = defaultdict(list), defaultdict(list)
    for raw in rows(folder / 'inputs.raw.jsonl'):
        audit.require(raw.get('side') == side and raw.get('runId') == run_id, '输入运行身份不同')
        identity = raw['caseId'] if side == 'ts' else by_java[raw['test']]
        inputs[identity].append(raw['input'])
    for raw in rows(folder / 'assertions.raw.jsonl'):
        if side == 'ts':
            if not raw['file'].endswith('/' + FILE):
                continue
            identity = by_name.get((raw['test'], raw['occurrence']))
            if identity is None:
                continue
            audit.require(raw['pass'] is True, '固定 TS 原断言失败')
        else:
            audit.require(raw['test'] in by_java, 'Java 出现计划外向量断言')
            identity = by_java[raw['test']]
        assertions[identity].append({'kind': 'assertion', **{key: raw[key]
                                    for key in ('matcher', 'negated', 'actual', 'expected')}})
    audit.same_keys(plan, inputs, '交易向量输入用例')
    audit.same_keys(plan, assertions, '交易向量断言用例')
    result = {'inputs.jsonl': [], 'assertions.jsonl': []}
    for case in mapping['cases']:
        identity, expected = case['id'], plan[case['id']]
        validate_inputs(methods[identity], inputs[identity])
        audit.require(len(inputs[identity]) == len(expected['sampleIds'])
                      and len(assertions[identity]) == len(expected['assertionIds']),
                      '逐输入/断言数量不同：' + identity)
        for name, key, values, identifiers in [('inputs.jsonl', 'sampleId', inputs[identity], expected['sampleIds']),
                                               ('assertions.jsonl', 'assertionId', assertions[identity], expected['assertionIds'])]:
            result[name].extend({'runId': run_id, 'side': side, 'caseId': identity, key: marker, 'value': value}
                                for marker, value in zip(identifiers, values))
    if emit:
        for name, values in result.items():
            write_rows(folder / name, values)
    return result


def capture(side, folder, plan_folder, java):
    folder.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    revision = source_revision(side, java)
    fixed = fingerprints(plan_folder)
    environment = dict(os.environ, EVIDENCE_RUN_ID=run_id, EVIDENCE_SIDE=side,
        MIGRATION_VECTOR_CATALOG=str(TASK / 'module-tests.json'),
        MIGRATION_VECTOR_MAPPING=str(TASK / 'test-map.json'),
        MIGRATION_VECTOR_TS_INPUTS=str(folder / 'inputs.raw.jsonl'),
        MIGRATION_VECTOR_JAVA_INPUTS=str(folder / 'inputs.raw.jsonl'),
        MIGRATION_PARITY_TS_OBSERVATIONS=str(folder / 'assertions.raw.jsonl'),
        MIGRATION_NETWORK_LOG=str(folder / 'network.jsonl'))
    if side == 'ts':
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
                   '--runTestsByPath', FILE, '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
                   str(TASK / 'capture-parity.cjs'), str(TASK / 'capture-transaction-vector-inputs.cjs'),
                   '--json', '--outputFile=' + str(folder / 'jest.json')]
    else:
        command = [str(TASK / 'mvn.sh'), '-f', str(java / 'pom.xml'), 'clean', 'test',
                   '-Dtest=TransactionCompleteVectorsTest',
                   '-Dmigration.parity.java.output=' + str(folder / 'assertions.raw.jsonl')]
    manifest = {'schemaVersion': 1, 'formalAcceptance': False, 'side': side, 'runId': run_id,
                'sourceRevision': revision, 'javaWorktree': str(java), 'fixedInputs': fixed,
                'command': command, 'startedAtNs': time.time_ns(), 'exitCode': None}
    write(folder / 'manifest.json', manifest)
    try:
        with (folder / 'run.log').open('w') as log:
            result = subprocess.run(command, cwd=TASK, env=environment, stdout=log, stderr=subprocess.STDOUT)
        manifest.update(exitCode=result.returncode, sourceRevisionAfter=source_revision(side, java))
        audit.require(result.returncode == 0, '真实测试失败，见 ' + str(folder / 'run.log'))
        audit.require(revision == manifest['sourceRevisionAfter'] and fixed == fingerprints(plan_folder), '采集期间源码或计划变化')
        if side == 'java':
            source = java / 'target/surefire-reports' / ('TEST-' + CLASS + '.xml')
            shutil.copyfile(source, folder / 'surefire.xml')
        normalize(folder, plan_folder, side, run_id)
        manifest['artifacts'] = {path.name: audit.digest(path) for path in folder.iterdir() if path.name != 'manifest.json'}
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        manifest['captureError'] = str(error)
        raise
    finally:
        manifest['finishedAtNs'] = time.time_ns()
        write(folder / 'manifest.json', manifest)
    print(json.dumps({'side': side, 'runId': run_id, 'sourceRevision': revision, 'formalAcceptance': False}))


def verify_manifest(folder, side, plan_folder, java):
    manifest = read(folder / 'manifest.json')
    audit.require(manifest['side'] == side and manifest['exitCode'] == 0 and not manifest.get('captureError'), '采集失败或侧别不同')
    audit.require(manifest['fixedInputs'] == fingerprints(plan_folder), '采集器或计划版本变化')
    audit.require(manifest['sourceRevision'] == manifest['sourceRevisionAfter'] == source_revision(side, java), '源码版本不是本轮运行版本')
    audit.require(manifest['artifacts'] == {path.name: audit.digest(path) for path in folder.iterdir()
                  if path.name != 'manifest.json'}, '原始证据摘要不同')
    audit.require(manifest['startedAtNs'] < manifest['finishedAtNs'] and len(manifest['runId']) == 32, '运行身份或时间缺失')
    for name, values in normalize(folder, plan_folder, side, manifest['runId'], emit=False).items():
        audit.require(audit.canonical(values) == audit.canonical(rows(folder / name)), '归一化与真实原始轨迹不同：' + name)
    return manifest


def compare(plan_folder, ts_folder, java_folder, java, output):
    manifests = {side: verify_manifest(folder, side, plan_folder, java)
                 for side, folder in [('ts', ts_folder), ('java', java_folder)]}
    audit.require(manifests['ts']['runId'] != manifests['java']['runId'], '两侧运行身份相同')
    full_catalog, full_mapping = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json')
    catalog, mapping, plan = (read(plan_folder / (name + '.json')) for name in ('catalog', 'mapping', 'input-plan'))
    preflight.validate_subset(full_catalog, full_mapping, catalog, mapping, plan)
    audit.compare_ts(dict(full_catalog, files=[file for file in full_catalog['files'] if file['path'] == FILE]),
                     [ts_folder / 'jest.json'])
    registration = preflight.java_registrations(mapping, catalog, [java_folder / 'surefire.xml'])
    audit.require(registration['surefireCases'] == 659 and not registration['missingMappedIdentities']
                  and not registration['duplicateReferences'] and not registration['duplicateSurefireIdentities'],
                  'Java 固定向量注册不完整')
    for name, key in [('inputs.jsonl', 'sampleId'), ('assertions.jsonl', 'assertionId')]:
        audit.require(not (ts_folder / name).samefile(java_folder / name), '两侧不能共用同一轨迹文件')
        values = {}
        for side, folder in [('ts', ts_folder), ('java', java_folder)]:
            normalized = audit.capture_rows(folder / name, key)
            audit.same_keys(plan, normalized, side + ' 用例')
            for identity, entries in normalized.items():
                expected = plan[identity]['sampleIds' if key == 'sampleId' else 'assertionIds']
                audit.require([row[key] for row in entries] == expected, '样本/断言遗漏或顺序不同：' + identity)
                audit.require(all(row['side'] == side and row['runId'] == manifests[side]['runId'] for row in entries), '原始轨迹身份不同')
            values[side] = {identity: [row['value'] for row in entries] for identity, entries in normalized.items()}
        for identity in plan:
            audit.require(audit.canonical(values['ts'][identity]) == audit.canonical(values['java'][identity]),
                          name + ' 两侧实际值不同：' + identity)
    report = {'formalAcceptance': False, 'localParityPassed': True, 'cases': 659, 'samplesCompared': 1159,
              'assertionsCompared': 1159, 'javaRevision': manifests['java']['sourceRevision'],
              'manifestSha256': {side: audit.digest(folder / 'manifest.json') for side, folder in [('ts', ts_folder), ('java', java_folder)]}}
    write(output, report)
    print(json.dumps(report, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'ts', 'java', 'compare'))
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--ts', type=Path)
    parser.add_argument('--java', type=Path)
    parser.add_argument('--java-worktree', type=Path, default=TASK / 'metanet4j-bsv-sdk')
    args = parser.parse_args()
    args.plan, args.java_worktree = args.plan.resolve(), args.java_worktree.resolve()
    try:
        if args.command == 'prepare':
            prepare(args.plan)
        elif args.command == 'compare':
            compare(args.plan, args.ts.resolve(), args.java.resolve(), args.java_worktree, args.output.resolve())
        else:
            capture(args.command, args.output.resolve(), args.plan, args.java_worktree)
    except (ValueError, KeyError, OSError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
