#!/usr/bin/env python3
"""正式采集 toOriginHeader 固定五例的双端实际输入与断言。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE = 'src/wallet/substrates/__tests/toOriginHeader.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.substrates.utils.ToOriginHeaderTest'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('采集侧别不同')
    replay = args.replay.resolve()
    report = args.report.resolve()
    raw = report.parent / 'calls.raw.jsonl'
    assertions = report.parent / 'assertions.raw.jsonl'
    env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(assertions),
               MIGRATION_NETWORK_LOG=str(report.parent / 'network.jsonl'))
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven 阶段')
        env['MIGRATION_ORIGIN_HEADER_TS_OBSERVATIONS'] = str(raw)
        subprocess.run([str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                        '--watchman=false', '--runTestsByPath', SOURCE, '--setupFilesAfterEnv',
                        str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-origin-header-inputs.cjs'),
                        str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)],
                       cwd=TASK, env=env, check=True)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('toOriginHeader 原测试发生真实网络调用')
        subprocess.run(['python3', str(TASK / 'prepare-origin-header-inputs.py'), 'emit-ts',
                        '--raw', str(raw), '--replay', str(replay),
                        '--output', env['EVIDENCE_INPUTS_PATH']], cwd=TASK, env=env, check=True)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        subprocess.run([str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                        'clean', 'test', '-Dtest=ToOriginHeaderTest',
                        '-Dmigration.origin-header.corpus=' + str(replay),
                        '-Dmigration.parity.java.output=' + str(assertions)], cwd=TASK, env=env, check=True)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + JAVA + '.xml')
        shutil.copyfile(source, report)
    subprocess.run(['python3', str(TASK / 'emit-assertion-observations.py'),
                    '--catalog', str(replay.parent / 'catalog.json'),
                    '--mapping', str(replay.parent / 'mapping.json'),
                    '--plan', str(replay.parent / 'input-plan.json'),
                    '--side', args.side, '--raw', str(assertions),
                    '--run-id', env['EVIDENCE_RUN_ID'], '--output', env['EVIDENCE_ASSERTIONS_PATH']],
                   cwd=TASK, env=env, check=True)


if __name__ == '__main__':
    main()
