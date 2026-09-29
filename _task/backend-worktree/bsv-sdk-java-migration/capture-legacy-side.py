#!/usr/bin/env python3
"""evidence-bundle capture 内运行固定 TS 原测试或 Java clean test。"""
import argparse
import os
from pathlib import Path
import importlib.util
import shutil
import sys
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
        # 逐项下标赋值：全量运行的分派表按这种写法解析探针的环境变量。
        environment = dict(os.environ)
        environment['MIGRATION_HEX_OBSERVATIONS'] = str(raw)
        environment['MIGRATION_BN_OBSERVATIONS'] = str(raw)
        environment['MIGRATION_NETWORK_LOG'] = str(network)
        setup = 'capture-hex.cjs' if kind == 'hex' else 'capture-bn-constructor.cjs'
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
                   '--runTestsByPath', replay.FILES[kind], '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
                   str(TASK / setup), '--json', '--outputFile=' + str(report)]
        subprocess.run(command, cwd=TASK, env=environment, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定原测试出现网络调用')
    # 转换改走 CLI（同一实现），全量运行的分派表据此识别本局部的 emit-ts 命令。
    command = [sys.executable, str(TASK / 'prepare-hex-bn-inputs.py'), 'emit-ts',
               '--kind', args.kind, '--plan', str(args.replay),
               '--inputs', os.environ['EVIDENCE_INPUTS_PATH'],
               '--assertions', os.environ['EVIDENCE_ASSERTIONS_PATH'],
               '--run-id', os.environ['EVIDENCE_RUN_ID'], '--side', 'ts']
    if raws.get('hex') is not None:
        command += ['--raw-hex', str(raws['hex'])]
    if raws.get('bn') is not None:
        command += ['--raw-bn', str(raws['bn'])]
    if args.kind != 'both' and raws.get(args.kind) is not None:
        command += ['--raw', str(raws[args.kind])]
    subprocess.run(command, cwd=TASK, check=True)


if __name__ == '__main__':
    main()
