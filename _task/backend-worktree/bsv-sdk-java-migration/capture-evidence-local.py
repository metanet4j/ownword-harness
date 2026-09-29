#!/usr/bin/env python3
"""结构补强局部的标准双侧采集适配器：按局部计划运行 TS 探针与 Java 聚焦测试。

与 capture-transaction-local.py 同一套逻辑，只把登记表换成 evidence-locals.py。"""
import argparse
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('evidence_locals', TASK / 'evidence-locals.py')
locals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locals_module)


def run(command, env=None):
    subprocess.run(command, cwd=TASK, env=env, check=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--local')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('结构补强采集侧别与运行环境不同')
    name = args.local
    if name is None:
        # 计划目录名形如 <局部>-plan-<日期>，按登记名反查。
        folder = args.plan.name
        candidates = [key for key in locals_module.LOCALS if folder.startswith(key)]
        if len(candidates) != 1:
            parser.error('无法从计划目录推断局部：' + folder)
        name = candidates[0]
    entry = locals_module.local(name)
    plan = args.plan.resolve()
    report = args.report.resolve()
    evidence = report.parent
    # 两侧共用同一运行目录：原始轨迹按侧别分开命名。
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    if args.side == 'ts':
        if args.clean or args.test:
            parser.error('TS 不接受 Maven 阶段')
        env = dict(os.environ, MIGRATION_PARITY_TS_OBSERVATIONS=str(parity),
                   MIGRATION_NETWORK_LOG=str(evidence / 'ts-network.jsonl'))
        env[entry['ts_observations_env']] = str(evidence / 'ts-calls.raw.jsonl')
        run([str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
             '--watchman=false', '--runTestsByPath', entry['file'], '--setupFilesAfterEnv',
             str(TASK / 'ts-offline-guard.cjs'), str(entry['probe_path']),
             str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(report)], env=env)
        network = Path(env['MIGRATION_NETWORK_LOG'])
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定原测试出现网络调用：' + entry['file'])
        run(['python3', str(TASK / 'prepare-evidence-local.py'), 'emit-ts', '--local', name,
             '--raw', env[entry['ts_observations_env']], '--plan', str(plan / 'input-plan.json'),
             '--output', os.environ['EVIDENCE_INPUTS_PATH']], env=env)
    else:
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        env = dict(os.environ, MIGRATION_PARITY_JAVA_OUTPUT=str(parity))
        env[entry['inputs_env']] = str(evidence / 'ts-inputs.jsonl')
        run([str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
             'clean', 'test', '-Dtest=' + entry['test'],
             '-Dmigration.parity.java.output=' + str(parity)], env=env)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/TEST-' + entry['java_class'] + '.xml')
        shutil.copyfile(source, report)
    run(['python3', str(TASK / 'emit-assertion-observations.py'),
         '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
         '--plan', str(plan / 'input-plan.json'), '--side', args.side,
         '--raw', str(parity), '--run-id', os.environ['EVIDENCE_RUN_ID'],
         '--output', os.environ['EVIDENCE_ASSERTIONS_PATH'],
         '--allow-ts-extra' if args.side == 'ts' else '--allow-java-extra'], env=env)


if __name__ == '__main__':
    main()
