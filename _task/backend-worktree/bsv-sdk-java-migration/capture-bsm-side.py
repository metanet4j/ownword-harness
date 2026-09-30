#!/usr/bin/env python3
"""在本轮 evidence-bundle capture 中运行固定 BSM 六个原用例。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess


TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
FILE = 'src/compat/__tests/BSM.test.ts'
CLASS = 'com.metanet4j.bsv.compat.BSMTest'


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
        parser.error('Java BSM 必须执行 clean test 并提供本轮 TS 输入')
    if args.side == 'ts' and (args.clean or args.test or args.replay):
        parser.error('TS BSM 不接受 Java 阶段或重放参数')
    args.report = args.report.resolve()
    folder = args.report.parent
    raw = folder / 'assertions.raw.jsonl'
    env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(raw))
    if args.side == 'ts':
        network = folder / 'network.jsonl'
        env['MIGRATION_NETWORK_LOG'] = str(network)
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', FILE, '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-bsm-inputs.cjs'),
                   str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(args.report)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        if network.exists() and network.read_text().strip():
            raise RuntimeError('BSM 原用例发生网络调用')
    else:
        env.pop('MIGRATION_PARITY_TS_OBSERVATIONS')
        env['MIGRATION_BSM_TS_INPUTS'] = str(args.replay.resolve())
        env['MIGRATION_PARITY_JAVA_OUTPUT'] = str(raw)
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=BSMTest', '-Dmigration.parity.java.output=' + str(raw)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / ('TEST-' + CLASS + '.xml')
        shutil.copyfile(source, args.report)
    converter = [str(TASK / 'emit-assertion-observations.py'), '--catalog', str(args.catalog.resolve()),
                 '--mapping', str(args.mapping.resolve()), '--plan', os.environ['EVIDENCE_INPUT_PLAN'],
                 '--side', args.side, '--raw', str(raw), '--run-id', os.environ['EVIDENCE_RUN_ID'],
                 '--output', os.environ['EVIDENCE_ASSERTIONS_PATH']]
    subprocess.run(['python3', *converter], cwd=TASK, check=True)


if __name__ == '__main__':
    main()
