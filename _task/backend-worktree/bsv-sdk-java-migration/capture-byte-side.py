#!/usr/bin/env python3
"""在 evidence-bundle capture 中运行 byte utils 参数化原测试与对应 Java clean test。"""
import argparse
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('replay_byte_utils', TASK / 'replay-byte-utils.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)
METHODS = ('binaryToBase58', 'binaryToBase58LeadingOnes',
           'base58Boundary255', 'base58BoundaryFFFF', 'base58BoundaryZeroFF', 'base58Boundary32Bytes')


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
                   'clean', 'test', '-Dtest=UtilsTest#' + '+'.join(METHODS),
                   '-Dmigration.byte.utils.plan=' + str(args.replay.resolve())]
        subprocess.run(command, cwd=TASK, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports/TEST-com.metanet4j.bsv.primitives.UtilsTest.xml'
        shutil.copyfile(source, args.report)
        return
    if args.clean or args.test:
        parser.error('TypeScript 不接受 Maven 阶段')
    evidence = args.report.parent
    raw = evidence / 'byte-utils.raw.jsonl'
    network = evidence / 'network.jsonl'
    env = dict(os.environ, MIGRATION_BYTE_UTILS_OBSERVATIONS=str(raw), MIGRATION_NETWORK_LOG=str(network))
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
               '--watchman=false', '--runTestsByPath', replay.FILE, '--setupFilesAfterEnv',
               str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-byte-utils.cjs'),
               '--json', '--outputFile=' + str(args.report)]
    subprocess.run(command, cwd=TASK, env=env, check=True)
    if network.exists() and network.read_text().strip():
        raise RuntimeError('固定原测试出现网络调用')
    replay.emit_ts(SimpleNamespace(raw=raw, plan=args.replay,
        run_id=os.environ['EVIDENCE_RUN_ID'], side='ts',
        inputs=os.environ['EVIDENCE_INPUTS_PATH'], assertions=os.environ['EVIDENCE_ASSERTIONS_PATH']))


if __name__ == '__main__':
    main()
