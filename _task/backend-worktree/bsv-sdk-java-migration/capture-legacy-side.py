#!/usr/bin/env python3
"""evidence-bundle capture 内运行固定 TS 原测试或 Java clean test。"""
import argparse
import os
from pathlib import Path
import importlib.util
import shutil
import subprocess
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('replay_legacy_inputs', TASK / 'replay-legacy-inputs.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--kind', choices=('hex', 'bn'), required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('capture 侧别与运行环境不同')
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        name = 'HexTest' if args.kind == 'hex' else 'BigNumberConstructorTest'
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=' + name, '-Dmigration.input.plan=' + str(args.replay)]
        subprocess.run(command, cwd=TASK, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / f'TEST-com.metanet4j.bsv.primitives.{name}.xml'
        shutil.copyfile(source, args.report)
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    evidence = args.report.parent
    raw = evidence / (args.kind + '.raw.jsonl')
    network = evidence / 'network.jsonl'
    environment = dict(os.environ, MIGRATION_HEX_OBSERVATIONS=str(raw), MIGRATION_BN_OBSERVATIONS=str(raw),
                       MIGRATION_NETWORK_LOG=str(network))
    setup = 'capture-hex.cjs' if args.kind == 'hex' else 'capture-bn-constructor.cjs'
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
               '--runTestsByPath', replay.FILES[args.kind], '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
               str(TASK / setup), '--json', '--outputFile=' + str(args.report)]
    subprocess.run(command, cwd=TASK, env=environment, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定原测试出现网络调用')
    replay.emit_ts(SimpleNamespace(kind=args.kind, raw=raw, plan=args.replay,
        run_id=os.environ['EVIDENCE_RUN_ID'], side='ts', inputs=os.environ['EVIDENCE_INPUTS_PATH'],
        assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))


if __name__ == '__main__':
    main()
