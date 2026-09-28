#!/usr/bin/env python3
"""在 evidence-bundle capture 内执行固定 KeyDeriver 原测试及 Java clean test。"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE = 'src/wallet/__tests/CachedKeyDeriver.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.CachedKeyDeriverTest'


def run(command, env=None):
    subprocess.run(command, cwd=TASK, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('CachedKeyDeriver 采集侧别与运行环境不同')
    plan = args.plan.resolve()
    report = args.report.resolve()
    evidence = report.parent
    # 两侧共用同一运行目录：原始与标准轨迹都按侧别分开命名。
    raw = evidence / f'{args.side}-calls.raw.jsonl'
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    replay = plan / 'replay-inputs.jsonl'
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven 阶段')
        env = dict(os.environ, MIGRATION_CACHED_KEYDERIVER_TS_INPUTS=str(raw),
                   MIGRATION_PARITY_TS_OBSERVATIONS=str(parity),
                   MIGRATION_NETWORK_LOG=str(evidence / 'ts-network.jsonl'))
        run([str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
             '--watchman=false', '--runTestsByPath', SOURCE, '--setupFilesAfterEnv',
             str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-cached-keyderiver-inputs.cjs'),
             str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)], env=env)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 CachedKeyDeriver 原测试出现网络调用')
        run(['python3', str(TASK / 'prepare-cached-keyderiver-inputs.py'), 'emit-ts', '--raw', str(raw),
             '--replay', str(replay), '--output', os.environ['EVIDENCE_INPUTS_PATH']], env=env)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        env = dict(os.environ, MIGRATION_PARITY_JAVA_OUTPUT=str(parity))
        run([str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
             'clean', 'test', '-Dtest=CachedKeyDeriverTest',
             '-Dmigration.cached.keyderiver.plan=' + str(replay),
             '-Dmigration.parity.java.output=' + str(parity)], env=env)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + JAVA + '.xml')
        shutil.copyfile(source, report)
    run(['python3', str(TASK / 'emit-assertion-observations.py'),
         '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
         '--plan', str(plan / 'input-plan.json'), '--side', args.side,
         '--raw', str(parity), '--run-id', os.environ['EVIDENCE_RUN_ID'],
         '--output', os.environ['EVIDENCE_ASSERTIONS_PATH']], env=env)


if __name__ == '__main__':
    main()
