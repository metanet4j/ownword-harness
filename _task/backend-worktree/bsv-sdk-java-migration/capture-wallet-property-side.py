#!/usr/bin/env python3
"""在 evidence-bundle capture 内运行固定 BRC-100 fast-check 原测试及 Java clean test。"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('replay_wallet_property', TASK / 'replay-wallet-property.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    args.report = args.report.resolve()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('capture 侧别与运行环境不同')
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=BRC100ByteEncodingPropertyTest',
                   '-Dmigration.wallet.property.plan=' + str(args.replay.resolve())]
        subprocess.run(command, cwd=TASK, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports/TEST-com.metanet4j.bsv.wallet.BRC100ByteEncodingPropertyTest.xml'
        shutil.copyfile(source, args.report)
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    evidence = args.report.parent
    raw = evidence / 'property.raw.jsonl'
    metadata = evidence / 'property.metadata.json'
    # 两侧共用同一运行目录：原始断言轨迹按侧别分开命名，避免混装。
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    network = evidence / 'network.jsonl'
    env = dict(os.environ, FAST_CHECK_SEED='20260926', FAST_CHECK_NUM_RUNS='300',
               MIGRATION_WALLET_PROPERTY_TS_INPUTS=str(raw), MIGRATION_WALLET_PROPERTY_TS_META=str(metadata),
               MIGRATION_PARITY_TS_OBSERVATIONS=str(parity), MIGRATION_NETWORK_LOG=str(network))
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
               '--watchman=false', '--runTestsByPath', replay.FILE, '--setupFilesAfterEnv',
               str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-wallet-property.cjs'),
               str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(args.report)]
    subprocess.run(command, cwd=TASK, env=env, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定原测试出现网络调用')
    replay.emit_ts(SimpleNamespace(raw=raw, meta=metadata, parity=parity, plan=args.replay,
        run_id=os.environ['EVIDENCE_RUN_ID'], side='ts',
        inputs=os.environ['EVIDENCE_INPUTS_PATH'], assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))


if __name__ == '__main__':
    main()
