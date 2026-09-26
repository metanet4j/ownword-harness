#!/usr/bin/env python3
"""采集固定 ScriptEvaluationError 原测试的构造输入与原断言。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess


TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
FILE = 'src/script/__tests/ScriptEvaluationError.test.ts'
CLASS = 'com.metanet4j.bsv.script.ScriptEvaluationErrorTest'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--mapping', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE') or not os.environ.get('EVIDENCE_RUN_ID'):
        parser.error('缺少本轮 capture 侧别或 runId')
    if args.side == 'java' and ((args.clean, args.test) != ('clean', 'test') or args.replay is None):
        parser.error('Java 必须 clean test 并提供本轮 TS 构造输入')
    if args.side == 'ts' and (args.clean or args.test or args.replay):
        parser.error('TS 不接受 Java 阶段或重放参数')
    report = args.report.resolve()
    raw = report.parent / 'assertions.raw.jsonl'
    env = dict(os.environ)
    if args.side == 'ts':
        env['MIGRATION_PARITY_TS_OBSERVATIONS'] = str(raw)
        env['MIGRATION_NETWORK_LOG'] = str(report.parent / 'network.jsonl')
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'),
                   str(TASK / 'capture-script-evaluation-error-inputs.cjs'),
                   str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        network = report.parent / 'network.jsonl'
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 ScriptEvaluationError 原测试发生网络调用')
    else:
        env['MIGRATION_SCRIPT_ERROR_TS_INPUTS'] = str(args.replay.resolve())
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=ScriptEvaluationErrorTest',
                   '-Dmigration.parity.java.output=' + str(raw)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / ('TEST-' + CLASS + '.xml')
        shutil.copyfile(source, report)
    converter = [str(TASK / 'emit-assertion-observations.py'), '--catalog', str(args.catalog.resolve()),
                 '--mapping', str(args.mapping.resolve()), '--plan', os.environ['EVIDENCE_INPUT_PLAN'],
                 '--side', args.side, '--raw', str(raw), '--run-id', os.environ['EVIDENCE_RUN_ID'],
                 '--output', os.environ['EVIDENCE_ASSERTIONS_PATH']]
    subprocess.run(['python3', *converter], cwd=TASK, check=True)


if __name__ == '__main__':
    main()
