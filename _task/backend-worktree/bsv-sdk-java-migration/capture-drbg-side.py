#!/usr/bin/env python3
"""在标准 capture 中执行 DRBG 原测试和独立 Java 重放。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE_FILE = 'src/primitives/__tests/DRBG.test.ts'
JAVA_CLASS = 'com.metanet4j.bsv.primitives.DrbgTest'
UNDEFINED = {'type': 'undefined'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    for name in ('catalog', 'mapping', 'report', 'replay'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE') or not os.environ.get('EVIDENCE_RUN_ID'):
        parser.error('缺少本轮 capture 侧别或 runId')
    if args.side == 'java' and (args.clean, args.test) != ('clean', 'test'):
        parser.error('Java DRBG 必须 clean test')
    if args.side == 'ts' and (args.clean or args.test):
        parser.error('TS DRBG 不接受 Java 阶段参数')
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    raw_inputs = report.parent / 'inputs.raw.jsonl'
    raw_assertions = report.parent / 'assertions.raw.jsonl'
    if args.side == 'java':
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=' + JAVA_CLASS,
                   '-Dmigration.drbg.corpus=' + str(args.replay.resolve()),
                   '-Dmigration.parity.java.output=' + str(raw_assertions)]
        subprocess.run(command, cwd=TASK, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / ('TEST-' + JAVA_CLASS + '.xml')
        shutil.copyfile(source, report)
    else:
        env = dict(os.environ)
        env['MIGRATION_DRBG_TS_OBSERVATIONS'] = str(raw_inputs)
        env['MIGRATION_PARITY_TS_OBSERVATIONS'] = str(raw_assertions)
        env['MIGRATION_NETWORK_LOG'] = str(report.parent / 'network.jsonl')
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', SOURCE_FILE, '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-drbg-inputs.cjs'),
                   str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        network = report.parent / 'network.jsonl'
        if network.exists() and network.read_text().strip():
            raise RuntimeError('DRBG 原用例发生网络调用')
        collect_inputs(args, raw_inputs)
    convert_assertions(args, raw_assertions)


def collect_inputs(args, raw_inputs):
    planned = [json.loads(line) for line in args.replay.read_text().splitlines()]
    observed = [json.loads(line) for line in raw_inputs.read_text().splitlines()]
    if len(observed) != len(planned):
        raise ValueError('本轮原入口数与固定计划不同')
    emitted = []
    for actual, expected in zip(observed, planned):
        if actual['value'] != expected['value']:
            raise ValueError('本轮真实 TS 入口与固定语料不同：' + str(actual['sequence']))
        emitted.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                        'caseId': expected['caseId'], 'sampleId': expected['sampleId'],
                        'value': actual['value']})
    Path(os.environ['EVIDENCE_INPUTS_PATH']).write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in emitted))


def convert_assertions(args, raw_assertions):
    # 固定 Jest toThrow()（任意异常）与 Java assertThrowsAny 都以空实参记录；
    # 统一按类型化 undefined 表示“无期望”，两端一致；原始轨迹保持原样。
    normalized = raw_assertions.with_name('assertions.normalized.jsonl')
    with normalized.open('w') as stream:
        for line in raw_assertions.read_text().splitlines():
            row = json.loads(line)
            if row.get('matcher') == 'toThrow' and row.get('expected') == []:
                row['expected'] = dict(UNDEFINED)
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    subprocess.run(['python3', str(TASK / 'emit-assertion-observations.py'),
                    '--catalog', str(args.catalog.resolve()), '--mapping', str(args.mapping.resolve()),
                    '--plan', os.environ['EVIDENCE_INPUT_PLAN'], '--side', args.side, '--raw',
                    str(normalized), '--run-id', os.environ['EVIDENCE_RUN_ID'],
                    '--output', os.environ['EVIDENCE_ASSERTIONS_PATH']], cwd=TASK, check=True)


if __name__ == '__main__':
    main()
