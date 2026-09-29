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


def emit_assertions(plan, side, raw):
    """标准断言发射器：按本侧原始断言轨迹写冻结身份的实际观察。"""
    subprocess.run(['python3', str(TASK / 'emit-assertion-observations.py'),
                    '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
                    '--plan', str(plan / 'input-plan.json'), '--side', side, '--raw', str(raw),
                    '--run-id', os.environ['EVIDENCE_RUN_ID'],
                    '--output', os.environ['EVIDENCE_ASSERTIONS_PATH'],
                    '--allow-ts-extra' if side == 'ts' else '--allow-java-extra'],
                   cwd=TASK, check=True)


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
    plan = args.replay.resolve().parent
    evidence = args.report.parent
    # 两侧共用同一运行目录：原始轨迹与网络日志按侧别分开命名。
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    assertion_index = plan / 'assertion-index.json'
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        large = evidence / 'java-large-actuals.jsonl'
        env = dict(os.environ, MIGRATION_WALLET_WIRE_ASSERTION_INDEX=str(assertion_index),
                   MIGRATION_WALLET_WIRE_JAVA_LARGE_ACTUALS=str(large),
                   MIGRATION_PARITY_JAVA_OUTPUT=str(parity))
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
        emit_assertions(plan, 'java', parity)
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    frames = evidence / 'ts-frames.raw.jsonl'
    entropy = evidence / 'ts-entropy.raw.jsonl'
    clock = evidence / 'ts-clock.raw.jsonl'
    large = evidence / 'ts-large-actuals.jsonl'
    network = evidence / 'ts-network.jsonl'
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
        parity=parity, plan=args.replay.resolve(),
        run_id=os.environ['EVIDENCE_RUN_ID'], inputs=os.environ['EVIDENCE_INPUTS_PATH']))
    emit_assertions(plan, 'ts', parity)


if __name__ == '__main__':
    main()
