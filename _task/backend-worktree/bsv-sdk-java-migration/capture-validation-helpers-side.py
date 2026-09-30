#!/usr/bin/env python3
"""在 evidence-bundle capture 内执行固定 ValidationHelpers 原测试与 Java clean test。

两侧都把原始观察转换成标准输入/断言行（runId/side/caseId/sampleId|assertionId/value），
使该文件可以作为标准双侧局部登记，而不是专用局部。
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
spec = importlib.util.spec_from_file_location('replay_validation_helpers', TASK / 'replay-validation-helpers.py')
replay = importlib.util.module_from_spec(spec)
spec.loader.exec_module(replay)


def write_rows(path, values):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n'
                                  for value in values))


def standard_inputs(rows, side, run_id):
    return [{'runId': run_id, 'side': side, 'caseId': row['caseId'], 'sampleId': row['sampleId'],
             'value': row['value']} for row in rows]


def ordered_assertions(file, mapping, plan, rows, side, run_id):
    indexed = {(row['caseId'], row['assertionId']): row for row in rows}
    if len(indexed) != len(rows):
        raise ValueError('ValidationHelpers 断言身份重复')
    ordered = [indexed[(case['id'], identity)] for case in file['cases']
               for identity in plan[case['id']]['assertionIds']]
    return [{'runId': run_id, 'side': side, 'caseId': row['caseId'], 'assertionId': row['assertionId'],
             'value': row['value']} for row in ordered]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts', 'java'))
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    args.report = args.report.resolve()
    if args.side != os.environ.get('EVIDENCE_SIDE'):
        parser.error('capture 侧别与运行环境不同')
    evidence = args.report.parent
    # 两侧共用同一运行目录：原始与标准轨迹都按侧别分开命名。
    raw = evidence / f'{args.side}-calls.raw.jsonl'
    parity = evidence / f'{args.side}-assertions.raw.jsonl'
    network = evidence / f'{args.side}-network.jsonl'
    plan_dir = args.plan.resolve()
    catalog, file, mapping = replay.source()
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    (evidence / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    (evidence / 'mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
    plan = replay.read(plan_dir / 'input-plan.json')
    if args.side == 'java':
        if (args.clean, args.test) != ('clean', 'test'):
            parser.error('Java 必须执行 clean test')
        command = [str(TASK / 'mvn.sh'), '-f', str(TASK / 'metanet4j-bsv-sdk/pom.xml'),
                   'clean', 'test', '-Dtest=ValidationHelpersTest',
                   '-Dmigration.validation.input.output=' + str(raw),
                   '-Dmigration.parity.java.output=' + str(parity)]
        subprocess.run(command, cwd=TASK, check=True)
        source = TASK / ('metanet4j-bsv-sdk/target/surefire-reports/'
                         'TEST-com.metanet4j.bsv.wallet.ValidationHelpersTest.xml')
        shutil.copyfile(source, args.report)
    else:
        if args.clean or args.test:
            parser.error('TypeScript 不接受 Maven 阶段')
        env = dict(os.environ, MIGRATION_VALIDATION_TS_INPUTS=str(raw),
                   MIGRATION_PARITY_TS_OBSERVATIONS=str(parity), MIGRATION_NETWORK_LOG=str(network))
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', replay.FILE, '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'), str(TASK / 'capture-validation-helpers.cjs'),
                   str(TASK / 'capture-parity.cjs'), '--json', '--outputFile=' + str(args.report)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        if network.exists() and network.read_text().strip():
            raise RuntimeError('固定 ValidationHelpers 原测试出现网络调用')
    inputs = replay.input_rows(replay.rows(raw), file, mapping, plan)
    assertions = ordered_assertions(file, mapping, plan,
                                    replay.assertions_for(args.side, parity, file, mapping),
                                    args.side, os.environ['EVIDENCE_RUN_ID'])
    write_rows(os.environ['EVIDENCE_INPUTS_PATH'], standard_inputs(inputs, args.side, os.environ['EVIDENCE_RUN_ID']))
    write_rows(os.environ['EVIDENCE_ASSERTIONS_PATH'], assertions)
    print(json.dumps({'side': args.side, 'cases': len(plan), 'samples': len(inputs),
                      'assertions': len(assertions)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
