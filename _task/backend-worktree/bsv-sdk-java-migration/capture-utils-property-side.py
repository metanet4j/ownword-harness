#!/usr/bin/env python3
"""在 evidence-bundle capture 内执行固定 utils.property 原测试与 Java 重放。"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('utils_property_corpus', TASK / 'utils-property-corpus.py')
corpus = importlib.util.module_from_spec(spec)
spec.loader.exec_module(corpus)
FILE = 'src/primitives/__tests/utils.property.test.ts'


def emit(args, raw):
    plan = json.loads(Path(args.plan).read_text())
    catalog = json.loads(Path(args.catalog).read_text())
    source = next(file for file in catalog['files'] if file['path'] == FILE)
    samples = corpus.rows(raw / 'inputs.jsonl')
    boundaries = corpus.rows(raw / 'boundaries.jsonl')
    assertions = corpus.rows(raw / 'assertions.jsonl')
    if args.side == 'ts':
        corpus.validate_ts(raw)
        boundaries = boundaries[:-1] + [{**boundaries[-1],
            'calls': [boundaries[-1]['calls'][1], boundaries[-1]['calls'][3]]}]
    else:
        if len(samples) != 600 or len(boundaries) != 76 or len(assertions) != 976:
            raise ValueError('Java property 原始消费数量不完整')
    inputs, outcomes = [], []
    for index, case in enumerate(source['cases']):
        case_id = case['id']
        name = corpus.NAMES[index] if args.side == 'ts' else (
            'com.metanet4j.bsv.primitives.UtilsPropertyTest#' + corpus.JAVA[index])
        source_samples = ([row for row in samples if row['test'] == corpus.NAMES[index]]
                          if index < 2 else boundaries)
        source_assertions = [row for row in assertions if row['test'] == name]
        ids = plan[case_id]
        if len(source_samples) != len(ids['sampleIds']) or len(source_assertions) != len(ids['assertionIds']):
            raise ValueError('固定原用例逐样本或逐断言数量与运行前计划不同：' + name)
        for sample_id, value in zip(ids['sampleIds'], source_samples):
            inputs.append({'runId': args.run_id, 'side': args.side,
                           'caseId': case_id, 'sampleId': sample_id, 'value': value})
        for assertion_id, value in zip(ids['assertionIds'], source_assertions):
            outcomes.append({'runId': args.run_id, 'side': args.side, 'caseId': case_id,
                             'assertionId': assertion_id, 'value': {
                                 'kind': 'assertion', **{key: value[key] for key in
                                                        ('matcher', 'negated', 'actual', 'expected')}}})
    Path(os.environ['EVIDENCE_INPUTS_PATH']).write_text(''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in inputs))
    Path(os.environ['EVIDENCE_ASSERTIONS_PATH']).write_text(''.join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n' for row in outcomes))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    for name in ('catalog', 'plan', 'corpus', 'report', 'raw-dir'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    args.run_id = os.environ.get('EVIDENCE_RUN_ID')
    if args.side != os.environ.get('EVIDENCE_SIDE') or not args.run_id:
        parser.error('缺少本次证据采集运行身份或侧别')
    raw = Path(args.raw_dir).resolve()
    raw.mkdir(parents=True, exist_ok=False)
    report = Path(args.report).resolve()
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven clean test 参数')
        environment = dict(os.environ,
            MIGRATION_UTILS_PROPERTY_TS_INPUTS=str(raw / 'inputs.jsonl'),
            MIGRATION_UTILS_PROPERTY_TS_META=str(raw / 'meta.json'),
            MIGRATION_UTILS_PROPERTY_TS_BOUNDARIES=str(raw / 'boundaries.jsonl'),
            MIGRATION_PARITY_TS_OBSERVATIONS=str(raw / 'assertions.jsonl'),
            MIGRATION_NETWORK_LOG=str(raw / 'network.jsonl'),
            FAST_CHECK_SEED='20260926', FAST_CHECK_NUM_RUNS='300')
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest',
            '--runInBand', '--watchman=false', '--runTestsByPath', FILE,
            '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
            str(TASK / 'capture-parity.cjs'), str(TASK / 'capture-utils-property.cjs'),
            '--json', '--outputFile=' + str(raw / 'jest.json')]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
        shutil.copyfile(raw / 'jest.json', report)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        environment = dict(os.environ,
            MIGRATION_UTILS_PROPERTY_JAVA_INPUTS=str(raw / 'inputs.jsonl'),
            MIGRATION_UTILS_PROPERTY_JAVA_BOUNDARIES=str(raw / 'boundaries.jsonl'))
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
            'clean', 'test', '-Dtest=UtilsPropertyTest',
            '-Dmigration.utils.property.corpus=' + str(Path(args.corpus).resolve()),
            '-Dmigration.parity.java.output=' + str(raw / 'assertions.jsonl')]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports/TEST-com.metanet4j.bsv.primitives.UtilsPropertyTest.xml'
        shutil.copyfile(source, report)
    emit(args, raw)


if __name__ == '__main__':
    main()
