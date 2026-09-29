#!/usr/bin/env python3
"""LivePolicy 标准双侧采集适配器：按局部计划运行 TS 探针与 Java 聚焦测试。"""
import argparse
import os
import shutil
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
SOURCE = 'src/transaction/fee-models/__tests/LivePolicy.test.ts'
JAVA = 'com.metanet4j.bsv.transaction.fee_models.LivePolicyTest'


def run(command, env=None):
    subprocess.run(command, cwd=TASK, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('LivePolicy 采集侧别与运行环境不同')
    plan = args.plan.resolve()
    report = args.report.resolve()
    evidence = report.parent
    # 两侧共用同一运行目录：原始轨迹按侧别分开命名。
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven 阶段')
        env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(parity),
                   MIGRATION_LIVE_POLICY_TS_OBSERVATIONS=str(evidence / 'ts-calls.raw.jsonl'),
                   MIGRATION_NETWORK_LOG=str(evidence / 'ts-network.jsonl'))
        run([str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
             '--watchman=false', '--runTestsByPath', SOURCE, '--setupFilesAfterEnv',
             str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-live-policy-inputs.cjs'),
             str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)], env=env)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 LivePolicy 原测试出现网络调用')
        # 探针只记入口样本身份；用计划冻结的编号顺序核对。
        subprocess.run(['python3', str(TASK / 'prepare-live-policy-local.py'), 'emit-ts',
                        '--raw', str(env['MIGRATION_LIVE_POLICY_TS_OBSERVATIONS']),
                        '--plan', str(plan / 'input-plan.json'),
                        '--output', os.environ['EVIDENCE_INPUTS_PATH']], cwd=TASK, env=env, check=True)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        env = dict(os.environ, MIGRATION_PARITY_JAVA_OUTPUT=str(parity),
                   MIGRATION_LIVE_POLICY_TS_INPUTS=str(evidence / 'ts-inputs.jsonl'))
        run([str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
             'clean', 'test', '-Dtest=LivePolicyTest',
             '-Dmigration.parity.java.output=' + str(parity)], env=env)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + JAVA + '.xml')
        shutil.copyfile(source, report)
    run(['python3', str(TASK / 'emit-assertion-observations.py'),
         '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
         '--plan', str(plan / 'input-plan.json'), '--side', args.side,
         '--raw', str(parity), '--run-id', os.environ['EVIDENCE_RUN_ID'],
         '--output', os.environ['EVIDENCE_ASSERTIONS_PATH'],
         '--allow-ts-extra' if args.side == 'ts' else '--allow-java-extra'], env=env)


if __name__ == '__main__':
    main()
