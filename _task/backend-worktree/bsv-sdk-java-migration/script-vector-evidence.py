#!/usr/bin/env python3
"""固定 Script/Spend 向量的独立真实输入采集；支持隔离 Java worktree，不充抵完整 P0。"""
import argparse
from collections import defaultdict
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('full_preflight', TASK / 'full-evidence-preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)
audit = preflight.audit
read, write = preflight.load, preflight.write
CLASSES = ('ScriptVectorsTest', 'SpendValidVectorsTest', 'SpendStandaloneValidVectorsTest')
FILES = ('src/script/__tests/Script.test.ts', 'src/script/__tests/Spend.test.ts',
         'src/script/__tests/SpendValildVectors.test.ts')
RANGES = ((383, 433), (540, 561), (8, 29))
METHODS = ['Script.fromHex'] * 5 + ['Script.fromASM', 'Script.fromHex', 'Script.fromASM']
INVALID_METHODS = ['Script.fromHex'] * 3 + ['Script.fromASM', 'Script.fromHex', 'Script.fromASM']
SDK = TASK.parents[2] / read(TASK / 'workspace.json')['upstream']['path'] / 'packages/sdk'


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def prepare(folder):
    catalog, mapping = read(TASK / 'module-tests.json'), read(TASK / 'test-map.json')
    selected = [case for case in mapping['cases'] if any(java['className'].split('.')[-1] in CLASSES for java in case['java'])]
    audit.require(len(selected) == 1940, '固定向量注册数变化')
    ids = {case['id'] for case in selected}
    files = []
    for name, (start, end) in zip(FILES, RANGES):
        source = next(file for file in catalog['files'] if file['path'] == name)
        files.append(dict(source, cases=[case for case in source['cases'] if case['id'] in ids],
                          sites=[site for site in source['sites'] if start <= site['line'] <= end]))
    catalog = dict(catalog, files=files, partialImplementationOnly=True)
    sites = {site['id'] for file in files for site in file['sites']}
    mapping = dict(mapping, cases=selected, siteReviews=[dict(review, caseIds=[key for key in review['caseIds'] if key in ids])
                    for review in mapping['siteReviews'] if review['id'] in sites])
    plan = {}
    owner = {case['id']: file for file in files for case in file['cases']}
    for case in selected:
        script = case['java'][0]['className'].endswith('.ScriptVectorsTest')
        count = (6 if case['java'][0]['name'].startswith('invalid') else 8) if script else 1
        samples = [f'input#{index:03d}' for index in range(1, count + 1)]
        plan[case['id']] = {'sampleIds': samples, 'assertionIds': case['assertionIds'],
            'assertionSites': {identity: identity for identity in case['assertionIds']},
            'loopSamples': {site['id']: samples for site in owner[case['id']]['sites'] if site['kind'] == 'loop'}}
    preflight.validate_subset(read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), catalog, mapping, plan)
    folder.mkdir(parents=True, exist_ok=False)
    for name, value in [('catalog', catalog), ('mapping', mapping), ('input-plan', plan)]:
        write(folder / (name + '.json'), value)
    print(json.dumps({'cases': len(plan), 'samples': sum(len(row['sampleIds']) for row in plan.values()),
                      'assertions': sum(len(row['assertionIds']) for row in plan.values())}))


def validate_inputs(case, values):
    script = case['java'][0]['className'].endswith('.ScriptVectorsTest')
    methods = (INVALID_METHODS if case['java'][0]['name'].startswith('invalid') else METHODS) if script else ['Spend.constructor']
    audit.require([value.get('method') for value in values] == methods, '真实 SDK 输入调用顺序或数量不同：' + case['id'])
    if script:
        audit.require(all(set(value) == {'method', 'args'} and len(value['args']) == 1
                          and isinstance(value['args'][0], str) for value in values), 'Script 实际参数类型变化')
        args = [value['args'][0] for value in values]
        same = (args[0] == args[1] == args[4] and args[2] == args[3] == args[6]) if methods == METHODS else (
            args[0] == args[2] and args[1] == args[4])
        audit.require(same, '固定 Script 向量消费顺序变化')
    else:
        fields = {'sourceTXID', 'sourceOutputIndex', 'sourceSatoshis', 'lockingScriptHex', 'transactionVersion',
                  'otherInputs', 'outputs', 'inputIndex', 'unlockingScriptHex', 'inputSequence', 'lockTime'}
        audit.require(set(values[0]) == {'method', 'args'} and len(values[0]['args']) == 1
                      and set(values[0]['args'][0]) == fields, 'Spend 前置字段不完整')
        params = values[0]['args'][0]
        audit.require(params['otherInputs'] == params['outputs'] == [] and params['sourceTXID'] == '0' * 64,
                      'Spend 固定前置状态变化')
        for name, expected in [('sourceOutputIndex', '0'), ('sourceSatoshis', '1'), ('transactionVersion', '1'),
                               ('inputIndex', '0'), ('inputSequence', '4294967295'), ('lockTime', '0')]:
            audit.require(params[name] == expected, 'Spend 固定数值变化：' + name)
        audit.require(all(isinstance(params[key], str) for key in ('lockingScriptHex', 'unlockingScriptHex')),
                      'Spend 缺少实际脚本序列化')


def normalize(folder, plan_folder, side, run_id, emit=True):
    catalog, mapping, plan = (read(plan_folder / (name + '.json')) for name in ('catalog', 'mapping', 'input-plan'))
    by_test = {java['className'] + '#' + java['name']: case['id'] for case in mapping['cases'] for java in case['java']}
    ts_names = {(file['path'], ' '.join(case['names']), case['occurrence']): case['id']
                for file in catalog['files'] for case in file['cases']}
    inputs, assertions = defaultdict(list), defaultdict(list)
    for raw in rows(folder / 'inputs.raw.jsonl'):
        audit.require(raw.get('runId') == run_id and raw.get('side') == side, '实际输入的运行身份或侧别不符')
        identity = raw['caseId'] if side == 'ts' else by_test[raw['test']]
        inputs[identity].append(raw['input'])
    for raw in rows(folder / 'assertions.raw.jsonl'):
        if side == 'ts':
            key = ('src/' + raw['file'].split('/src/', 1)[1], raw['test'], raw['occurrence'])
            if key not in ts_names:
                continue
            audit.require(raw['pass'] is True, '固定 TS 断言未通过')
            identity = ts_names[key]
        else:
            audit.require(raw['test'] in by_test, 'Java 出现计划外断言身份')
            identity = by_test[raw['test']]
        assertions[identity].append({'kind': 'assertion', **{key: raw[key] for key in ('matcher', 'negated', 'actual', 'expected')}})
    audit.same_keys(plan, inputs, '真实输入用例')
    audit.same_keys(plan, assertions, '真实断言用例')
    input_rows, assertion_rows = [], []
    for case in mapping['cases']:
        identity = case['id']
        expected = plan[identity]
        validate_inputs(case, inputs[identity])
        audit.require(len(inputs[identity]) == len(expected['sampleIds'])
                      and len(assertions[identity]) == len(expected['assertionIds']), '逐样本/断言计数不符：' + identity)
        for key, values, ids, out in [('sampleId', inputs[identity], expected['sampleIds'], input_rows),
                                     ('assertionId', assertions[identity], expected['assertionIds'], assertion_rows)]:
            out.extend({'runId': run_id, 'side': side, 'caseId': identity, key: item, 'value': value}
                       for item, value in zip(ids, values))
    normalized = {'inputs.jsonl': input_rows, 'assertions.jsonl': assertion_rows}
    if emit:
        for name, values in normalized.items():
            write_rows(folder / name, values)
    return normalized


def source_revision(side, java):
    if side == 'java':
        return audit.java_revision({'metanet4j-bsv-sdk': str(java)})
    revision = subprocess.check_output(['git', '-C', str(SDK), 'rev-parse', 'HEAD'], text=True).strip()
    audit.require(revision == read(TASK / 'module-tests.json')['upstreamCommit'], 'TS 不是固定上游版本')
    audit.require(not subprocess.check_output(['git', '-C', str(SDK), 'status', '--porcelain'], text=True).strip(),
                  '固定 TS 工作区有修改')
    return revision


def fingerprints(plan_folder):
    return {str(path): audit.digest(path) for path in [Path(__file__), TASK / 'capture-script-vector-inputs.cjs',
        TASK / 'capture-parity.cjs', TASK / 'ts-offline-guard.cjs',
        TASK / 'audit-tests.py', TASK / 'evidence-bundle.py', TASK / 'full-evidence-preflight.py',
        *(plan_folder / (name + '.json') for name in ('catalog', 'mapping', 'input-plan'))]}


def capture(side, folder, plan_folder, java):
    folder.mkdir(parents=True, exist_ok=False)
    run_id = uuid.uuid4().hex
    source = source_revision(side, java)
    fixed = fingerprints(plan_folder)
    environment = dict(os.environ, EVIDENCE_RUN_ID=run_id, EVIDENCE_SIDE=side,
        MIGRATION_VECTOR_CATALOG=str(plan_folder / 'catalog.json'),
        MIGRATION_VECTOR_TS_INPUTS=str(folder / 'inputs.raw.jsonl'),
        MIGRATION_VECTOR_JAVA_INPUTS=str(folder / 'inputs.raw.jsonl'),
        MIGRATION_PARITY_TS_OBSERVATIONS=str(folder / 'assertions.raw.jsonl'),
        MIGRATION_NETWORK_LOG=str(folder / 'network.jsonl'))
    if side == 'ts':
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
            '--runTestsByPath', *FILES, '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
            str(TASK / 'capture-parity.cjs'), str(TASK / 'capture-script-vector-inputs.cjs'),
            '--json', '--outputFile=' + str(folder / 'jest.json')]
    else:
        command = [str(TASK / 'mvn.sh'), '-f', str(java / 'pom.xml'), 'clean', 'test', '-Dtest=' + ','.join(CLASSES),
                   '-Dmigration.parity.java.output=' + str(folder / 'assertions.raw.jsonl')]
    manifest = {'schemaVersion': 1, 'formalAcceptance': False, 'side': side, 'runId': run_id,
                'sourceRevision': source, 'javaWorktree': str(java), 'fixedInputs': fixed,
                'command': command, 'startedAtNs': time.time_ns(), 'exitCode': None}
    write(folder / 'manifest.json', manifest)
    try:
        with (folder / 'run.log').open('w') as log:
            result = subprocess.run(command, cwd=TASK, env=environment, stdout=log, stderr=subprocess.STDOUT)
        manifest.update(exitCode=result.returncode, sourceRevisionAfter=source_revision(side, java))
        audit.require(result.returncode == 0, '实际测试失败，见 ' + str(folder / 'run.log'))
        audit.require(source == manifest['sourceRevisionAfter'] and fixed == fingerprints(plan_folder), '采集期间来源变化')
        if side == 'java':
            for name in CLASSES:
                shutil.copyfile(java / 'target/surefire-reports' / ('TEST-com.metanet4j.bsv.script.' + name + '.xml'),
                                folder / (name + '.xml'))
        normalize(folder, plan_folder, side, run_id)
        manifest['artifacts'] = {path.name: audit.digest(path) for path in folder.iterdir() if path.name != 'manifest.json'}
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        manifest['captureError'] = str(error)
        raise
    finally:
        manifest['finishedAtNs'] = time.time_ns()
        write(folder / 'manifest.json', manifest)
    print(json.dumps({'side': side, 'runId': run_id, 'sourceRevision': source, 'formalAcceptance': False}))


def verify_manifest(folder, side, plan_folder, java):
    manifest = read(folder / 'manifest.json')
    audit.require(manifest['side'] == side and manifest['exitCode'] == 0 and not manifest.get('captureError'), '运行侧别、状态或采集失败')
    audit.require(manifest['fixedInputs'] == fingerprints(plan_folder), '采集器或输入计划版本变化')
    audit.require(manifest['sourceRevision'] == manifest['sourceRevisionAfter'] == source_revision(side, java), '源码版本与真实运行不同')
    audit.require(manifest['artifacts'] == {path.name: audit.digest(path) for path in folder.iterdir()
                  if path.name != 'manifest.json'}, '运行原始证据校验值不同')
    audit.require(manifest['startedAtNs'] < manifest['finishedAtNs'] and len(manifest['runId']) == 32, '运行身份或时间缺失')
    for name, values in normalize(folder, plan_folder, side, manifest['runId'], emit=False).items():
        audit.require(audit.canonical(values) == audit.canonical(rows(folder / name)), '规范化轨迹与原始实际采集不同：' + name)
    return manifest


def compare(plan_folder, ts_folder, java_folder, java, output):
    manifests = {side: verify_manifest(folder, side, plan_folder, java)
                 for side, folder in [('ts', ts_folder), ('java', java_folder)]}
    audit.require(manifests['ts']['runId'] != manifests['java']['runId'], '两侧运行身份重复')
    catalog, mapping, plan = (read(plan_folder / (name + '.json')) for name in ('catalog', 'mapping', 'input-plan'))
    preflight.validate_subset(read(TASK / 'module-tests.json'), read(TASK / 'test-map.json'), catalog, mapping, plan)
    full_catalog = read(TASK / 'module-tests.json')
    audit.compare_ts(dict(full_catalog, files=[file for file in full_catalog['files'] if file['path'] in FILES]),
                     [ts_folder / 'jest.json'])
    registration = preflight.java_registrations(mapping, catalog, list(java_folder.glob('*.xml')))
    audit.require(registration['surefireCases'] == 1940 and not registration['missingMappedIdentities']
                  and not registration['duplicateReferences'] and not registration['duplicateSurefireIdentities'], 'Java 实际注册不完整')
    for name, key in [('inputs.jsonl', 'sampleId'), ('assertions.jsonl', 'assertionId')]:
        audit.require(not (ts_folder / name).samefile(java_folder / name), '两侧不能共用同一轨迹文件')
        values = {}
        for side, folder in [('ts', ts_folder), ('java', java_folder)]:
            normalized = audit.capture_rows(folder / name, key)
            audit.same_keys(plan, normalized, side + ' 实际用例')
            for identity, entries in normalized.items():
                audit.require([row[key] for row in entries] == plan[identity]['sampleIds' if key == 'sampleId' else 'assertionIds'],
                              side + ' 样本/断言遗漏或顺序不同')
                audit.require(all(row['side'] == side and row['runId'] == manifests[side]['runId'] for row in entries), '轨迹身份不同')
            values[side] = {identity: [row['value'] for row in entries] for identity, entries in normalized.items()}
        for identity in plan:
            audit.require(audit.canonical(values['ts'][identity]) == audit.canonical(values['java'][identity]),
                          name + ' 两侧实际值不同：' + identity)
    result = {'formalAcceptance': False, 'localParityPassed': True, 'cases': len(plan),
              'samplesCompared': sum(len(row['sampleIds']) for row in plan.values()),
              'assertionsCompared': sum(len(row['assertionIds']) for row in plan.values()),
              'javaRevision': manifests['java']['sourceRevision'], 'javaWorktree': str(java),
              'manifestSha256': {side: audit.digest(folder / 'manifest.json') for side, folder in [('ts', ts_folder), ('java', java_folder)]}}
    write(output, result)
    print(json.dumps(result, ensure_ascii=False))


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
