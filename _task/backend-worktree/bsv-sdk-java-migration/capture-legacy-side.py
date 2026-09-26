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
    parser.add_argument('--kind', choices=('hex', 'bn', 'both'), required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--report', type=Path, action='append', required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('capture 侧别与运行环境不同')
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        names = ['HexTest' if kind == 'hex' else 'BigNumberConstructorTest' for kind in replay.kinds(args.kind)]
        if len(names) != len(args.report):
            parser.error('Java 报告数与原测试文件数不同')
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=' + ','.join(names), '-Dmigration.input.plan=' + str(args.replay)]
        subprocess.run(command, cwd=TASK, check=True)
        for name, report in zip(names, args.report):
            source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / f'TEST-com.metanet4j.bsv.primitives.{name}.xml'
            shutil.copyfile(source, report)
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    if len(replay.kinds(args.kind)) != len(args.report):
        parser.error('TS 报告数与原测试文件数不同')
    evidence = args.report[0].parent
    network = evidence / 'network.jsonl'
    raws = {}
    for kind, report in zip(replay.kinds(args.kind), args.report):
        raw = evidence / (kind + '.raw.jsonl')
        raws[kind] = raw
        environment = dict(os.environ, MIGRATION_HEX_OBSERVATIONS=str(raw), MIGRATION_BN_OBSERVATIONS=str(raw),
                           MIGRATION_NETWORK_LOG=str(network))
        setup = 'capture-hex.cjs' if kind == 'hex' else 'capture-bn-constructor.cjs'
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
                   '--runTestsByPath', replay.FILES[kind], '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
                   str(TASK / setup), '--json', '--outputFile=' + str(report)]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定原测试出现网络调用')
    replay.emit_ts(SimpleNamespace(kind=args.kind, raw=raws.get(args.kind), raw_hex=raws.get('hex'),
        raw_bn=raws.get('bn'), plan=args.replay,
        run_id=os.environ['EVIDENCE_RUN_ID'], side='ts', inputs=os.environ['EVIDENCE_INPUTS_PATH'],
        assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))


if __name__ == '__main__':
    main()
