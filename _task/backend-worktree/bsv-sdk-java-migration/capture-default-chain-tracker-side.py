#!/usr/bin/env python3
"""在一次真实运行中采集固定 DefaultChainTracker 原测试的输入和断言。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE = 'src/transaction/chaintrackers/__tests/DefaultChainTracker.test.ts'
JAVA = 'com.metanet4j.bsv.transaction.chaintrackers.DefaultChainTrackerTest'


def run(*command, env):
    subprocess.run(command, cwd=TASK, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('capture 侧别与环境不同')
    replay = args.replay.resolve()
    report = args.report.resolve()
    folder = report.parent
    raw = folder / 'calls.raw.jsonl'
    assertions = folder / 'assertions.raw.jsonl'
    env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(assertions),
               MIGRATION_NETWORK_LOG=str(folder / 'network.jsonl'))
    plan = replay.parent
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TypeScript 不接受 Maven 阶段')
        env['MIGRATION_DEFAULT_CHAIN_TRACKER_TS_OBSERVATIONS'] = str(raw)
        run(str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
            '--watchman=false', '--runTestsByPath', SOURCE, '--setupFilesAfterEnv',
            str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-default-chain-tracker-inputs.cjs'),
            str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report), env=env)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 DefaultChainTracker 原测试出现网络调用')
        run('python3', str(TASK / 'prepare-default-chain-tracker-inputs.py'), 'emit-ts',
            '--raw', str(raw), '--replay', str(replay), '--output', env['EVIDENCE_INPUTS_PATH'], env=env)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        env['MIGRATION_PARITY_JAVA_OUTPUT'] = str(assertions)
        run(str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
            'clean', 'test', '-Dtest=DefaultChainTrackerTest',
            '-Dmigration.defaultChainTracker.corpus=' + str(replay),
            '-Dmigration.parity.java.output=' + str(assertions), env=env)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + JAVA + '.xml')
        shutil.copyfile(source, report)
    run('python3', str(TASK / 'emit-assertion-observations.py'),
        '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
        '--plan', str(plan / 'input-plan.json'), '--side', args.side,
        '--raw', str(assertions), '--run-id', env['EVIDENCE_RUN_ID'],
        '--output', env['EVIDENCE_ASSERTIONS_PATH'], env=env)


if __name__ == '__main__':
    main()
