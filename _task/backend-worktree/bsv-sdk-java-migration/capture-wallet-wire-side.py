#!/usr/bin/env python3
"""在 evidence-bundle capture 中运行固定 WalletWire 双侧集成测试。"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('replay_wallet_wire_inputs', TASK / 'replay-wallet-wire-inputs.py')
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
    evidence = args.report.parent
    parity = evidence / 'assertions.raw.jsonl'
    assertion_index = args.replay.resolve().parent / 'assertion-index.json'
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        large = evidence / 'large-actuals.jsonl'
        env = dict(os.environ, MIGRATION_WALLET_WIRE_ASSERTION_INDEX=str(assertion_index),
                   MIGRATION_WALLET_WIRE_JAVA_LARGE_ACTUALS=str(large))
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=WalletWireIntegrationTest',
                   '-Dmigration.walletWire.plan=' + str(args.replay.resolve()),
                   '-Dmigration.parity.largeArrays=true',
                   '-Dmigration.parity.java.output=' + str(parity)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/'
                         'TEST-com.metanet4j.bsv.wallet.substrates.WalletWireIntegrationTest.xml')
        shutil.copyfile(source, args.report)
        if len(replay.rows(large)) != 4:
            raise RuntimeError('Java 四条大型 BEEF 原断言缺完整实际字节')
        replay.emit_java(SimpleNamespace(side='java', run_id=os.environ['EVIDENCE_RUN_ID'], parity=parity,
            assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    frames = evidence / 'frames.raw.jsonl'
    entropy = evidence / 'entropy.raw.jsonl'
    clock = evidence / 'clock.raw.jsonl'
    large = evidence / 'large-actuals.jsonl'
    network = evidence / 'network.jsonl'
    env = dict(os.environ, MIGRATION_WALLET_WIRE_TS_FRAMES=str(frames),
               MIGRATION_WALLET_WIRE_TS_ENTROPY=str(entropy),
               MIGRATION_WALLET_WIRE_TS_CLOCK=str(clock),
               MIGRATION_WALLET_WIRE_TS_LARGE_ACTUALS=str(large),
               MIGRATION_WALLET_WIRE_ASSERTION_INDEX=str(assertion_index),
               MIGRATION_PARITY_TS_OBSERVATIONS=str(parity), MIGRATION_NETWORK_LOG=str(network))
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
               '--watchman=false', '--runTestsByPath', replay.FILE, '--setupFilesAfterEnv',
               str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-wallet-wire-frames.cjs'),
               str(TASK / 'capture-wallet-wire-parity.cjs'), '--json', '--outputFile=' + str(args.report)]
    subprocess.run(command, cwd=TASK, env=env, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定 WalletWire 原测试出现网络调用')
    if len(replay.rows(large)) != 4:
        raise RuntimeError('TS 四条大型 BEEF 原断言缺完整实际字节')
    replay.emit_ts(SimpleNamespace(frames=frames, entropy=entropy, clock=clock,
        parity=parity, plan=args.replay,
        side='ts', run_id=os.environ['EVIDENCE_RUN_ID'], inputs=os.environ['EVIDENCE_INPUTS_PATH'],
        assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))


if __name__ == '__main__':
    main()
