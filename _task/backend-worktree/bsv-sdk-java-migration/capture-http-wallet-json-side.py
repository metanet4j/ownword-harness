#!/usr/bin/env python3
"""固定 HTTPWalletJSON 原 Jest 与 Java HTTPWalletJSONTest 的同输入采集。"""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE = 'src/wallet/substrates/__tests/HTTPWalletJSON.test.ts'
JAVA = 'com.metanet4j.bsv.wallet.substrates.HTTPWalletJSONTest'


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
        parser.error('HTTPWalletJSON 采集侧别与运行环境不同')
    replay = args.replay.resolve()
    report = args.report.resolve()
    evidence = report.parent
    # 两侧共用同一运行目录，所有原始轨迹按侧别分开命名，避免把另一侧的记录并进本轮来源。
    raw = evidence / f'{args.side}-inputs.raw.jsonl'
    wire = evidence / 'ts-requests.wire.jsonl'
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(parity),
               MIGRATION_NETWORK_LOG=str(evidence / f'{args.side}-network.jsonl'))
    plan = replay.parent
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven 阶段')
        env['MIGRATION_HTTP_WALLET_JSON_TS_OBSERVATIONS'] = str(raw)
        env['MIGRATION_HTTP_WALLET_JSON_TS_WIRE'] = str(wire)
        run(str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
            '--watchman=false', '--runTestsByPath', SOURCE, '--setupFilesAfterEnv',
            str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-http-wallet-json-inputs.cjs'),
            str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report), env=env)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 HTTPWalletJSON 原测试出现网络调用')
        run('python3', str(TASK / 'prepare-http-wallet-json-inputs.py'), 'emit-ts', '--raw', str(raw),
            '--replay', str(replay), '--output', env['EVIDENCE_INPUTS_PATH'], env=env)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        env['MIGRATION_PARITY_JAVA_OUTPUT'] = str(parity)
        run(str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
            'clean', 'test', '-Dtest=HTTPWalletJSONTest',
            '-Dmigration.httpwalletjson.corpus=' + str(replay),
            '-Dmigration.httpwalletjson.wire=' + str(wire),
            '-Dmigration.parity.java.output=' + str(parity), env=env)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + JAVA + '.xml')
        shutil.copyfile(source, report)
    run('python3', str(TASK / 'emit-assertion-observations.py'),
        '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
        '--plan', str(plan / 'input-plan.json'), '--side', args.side,
        '--raw', str(parity), '--run-id', env['EVIDENCE_RUN_ID'],
        '--output', env['EVIDENCE_ASSERTIONS_PATH'], env=env)


if __name__ == '__main__':
    main()
