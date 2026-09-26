#!/usr/bin/env python3
"""在标准 capture 中执行 BigNumber 算术/位运算原测试和独立 Java 重放。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
VARIANTS = {
    'arithmetic': ('src/primitives/__tests/BigNumber.arithmatic.test.ts', 'BigNumberArithmeticTest'),
    'binary': ('src/primitives/__tests/BigNumber.binary.test.ts', 'BigNumberBinaryTest'),
    'serializers': ('src/primitives/__tests/BigNumber.serializers.test.ts', 'BigNumberSerializersTest'),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('--variant', choices=VARIANTS, default='arithmetic')
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    for name in ('catalog', 'mapping', 'report', 'replay'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    source_file, java_class = VARIANTS[args.variant]
    if args.side != os.environ.get('EVIDENCE_SIDE') or not os.environ.get('EVIDENCE_RUN_ID'):
        parser.error('缺少本轮 capture 侧别或 runId')
    if args.side == 'java' and (args.clean, args.test) != ('clean', 'test'):
        parser.error('Java arithmetic 必须 clean test')
    if args.side == 'ts' and (args.clean or args.test):
        parser.error('TS arithmetic 不接受 Java 阶段参数')
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    raw = report.parent / 'assertions.raw.jsonl'
    env = dict(os.environ, MIGRATION_BN_VARIANT=args.variant)
    if args.side == 'java':
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=' + java_class,
                   '-Dmigration.bn.' + args.variant + '.corpus=' + str(args.replay.resolve()),
                   '-Dmigration.parity.java.output=' + str(raw)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        source = TASK / 'metanet4j-bsv-sdk/target/surefire-reports' / ('TEST-com.metanet4j.bsv.primitives.' + java_class + '.xml')
        shutil.copyfile(source, report)
        if args.variant in ('binary', 'serializers'):
            # 原 Java 测试主体仍执行动态循环；核对其全部原断言与输入 replay 的独立结果。
            original = report.parent / 'original-assertions.jsonl'
            convert(args, raw, original)
            def values(path):
                rows = [json.loads(line) for line in path.read_text().splitlines()]
                return {(row['caseId'], row['assertionId']): row['value'] for row in rows}
            if values(original) != values(Path(os.environ['EVIDENCE_ASSERTIONS_PATH'])):
                raise ValueError('原 Java 测试主体的动态断言与独立输入 replay 不同')
        return
    inputs_raw = report.parent / 'inputs.raw.jsonl'
    env['MIGRATION_BN_ARITHMETIC_RAW'] = str(inputs_raw)
    env['MIGRATION_PARITY_TS_OBSERVATIONS'] = str(raw)
    env['MIGRATION_NETWORK_LOG'] = str(report.parent / 'network.jsonl')
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
               '--watchman=false', '--runTestsByPath', source_file, '--setupFilesAfterEnv',
               str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-bn-arithmetic-inputs.cjs'),
               str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)]
    subprocess.run(command, cwd=TASK, env=env, check=True)
    network = report.parent / 'network.jsonl'
    if network.exists() and network.read_text().strip():
        raise RuntimeError('BigNumber 算术原用例发生网络调用')
    planned = [json.loads(line) for line in args.replay.read_text().splitlines()]
    observed = [json.loads(line) for line in inputs_raw.read_text().splitlines()]
    if len(observed) != len(planned):
        raise ValueError('本轮原入口/断言数与固定计划不同')
    emitted = []
    for actual, expected in zip(observed, planned):
        if actual != expected['value']:
            raise ValueError('本轮真实 TS 输入/断言引用与固定语料不同：' + str(actual['sequence']))
        if actual['kind'] != 'call':
            continue
        value = {key: value for key, value in actual.items() if key != 'result'}
        emitted.append({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts',
                        'caseId': expected['caseId'], 'sampleId': expected['sampleId'], 'value': value})
    Path(os.environ['EVIDENCE_INPUTS_PATH']).write_text(''.join(json.dumps(row) + '\n' for row in emitted))
    convert(args, raw, Path(os.environ['EVIDENCE_ASSERTIONS_PATH']))


def convert(args, raw, output):
    subprocess.run(['python3', str(TASK / 'emit-assertion-observations.py'),
                    '--catalog', str(args.catalog.resolve()), '--mapping', str(args.mapping.resolve()),
                    '--plan', os.environ['EVIDENCE_INPUT_PLAN'], '--side', args.side, '--raw', str(raw),
                    '--run-id', os.environ['EVIDENCE_RUN_ID'],
                    '--output', str(output)], cwd=TASK, check=True)


if __name__ == '__main__':
    main()
