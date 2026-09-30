#!/usr/bin/env python3
"""标准 capture 中执行 Point.additional 全部原用例及相同输入的 Java 重放。"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2]/'reference/ts-stack/packages/sdk'

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('side', choices=('ts','java'))
    parser.add_argument('--variant', choices=('additional','jacobian','point11'), default='additional')
    parser.add_argument('clean', nargs='?')
    parser.add_argument('test', nargs='?')
    for name in ('catalog','mapping','report','replay'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    source, java_class, prefix = {
        'additional': ('src/primitives/__tests/Point.additional.test.ts', 'PointAdditionalTest', 'point-additional'),
        'jacobian': ('src/primitives/__tests/JacobianPoint.test.ts', 'JacobianPointTest', 'jacobian'),
        'point11': ('src/primitives/__tests/Point.test.ts', 'PointTest', 'point11'),
    }[args.variant]
    if args.side != os.environ.get('EVIDENCE_SIDE') or not os.environ.get('EVIDENCE_RUN_ID'):
        parser.error('缺少本轮 capture 侧别或 runId')
    if args.side == 'java' and (args.clean,args.test) != ('clean','test'):
        parser.error('Java 必须 clean test')
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    raw = report.parent/'assertions.raw.jsonl'
    env = dict(os.environ)
    if args.side == 'java':
        command = [str(TASK/'mvn.sh'), '-f', str(TASK/'metanet4j-bsv-sdk/pom.xml'), 'clean','test',
                   '-Dtest='+java_class, '-Dmigration.'+prefix+'.corpus='+str(args.replay.resolve()),
                   '-Dmigration.parity.java.output='+str(raw)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        shutil.copyfile(TASK/('metanet4j-bsv-sdk/target/surefire-reports/TEST-com.metanet4j.bsv.primitives.'+java_class+'.xml'), report)
    else:
        if args.clean or args.test: parser.error('TS 不接受 Java 阶段参数')
        inputs = report.parent/'inputs.raw.jsonl'
        env.update(MIGRATION_POINT_ADDITIONAL_TS_OBSERVATIONS=str(inputs),
                   MIGRATION_PARITY_TS_OBSERVATIONS=str(raw),
                   MIGRATION_NETWORK_LOG=str(report.parent/'network.jsonl'))
        command = [str(TASK/'pnpm.sh'), '--dir', str(SDK), 'exec','jest','--runInBand','--watchman=false',
                   '--runTestsByPath',source,'--setupFilesAfterEnv',str(TASK/'ts-offline-guard.cjs'),
                   str(TASK/'capture-point-additional-inputs.cjs'),str(TASK/'capture-parity.cjs'),
                   '--json','--outputFile='+str(report)]
        subprocess.run(command, cwd=TASK, env=env, check=True)
        network = report.parent/'network.jsonl'
        if network.exists() and network.read_text().strip(): raise ValueError('原测试发生网络调用')
        planned = [json.loads(line) for line in args.replay.read_text().splitlines()]
        observed = [json.loads(line) for line in inputs.read_text().splitlines()]
        if len(planned) != len(observed): raise ValueError('原输入数量改变')
        emitted = []
        for actual, expected in zip(observed, planned):
            if actual != expected['value']: raise ValueError('本轮真实 TS 输入与固定语料不同')
            emitted.append({'runId':os.environ['EVIDENCE_RUN_ID'],'side':'ts','caseId':expected['caseId'],
                            'sampleId':expected['sampleId'],'value':actual})
        Path(os.environ['EVIDENCE_INPUTS_PATH']).write_text(''.join(json.dumps(r)+'\n' for r in emitted))
    subprocess.run(['python3',str(TASK/'emit-assertion-observations.py'), '--catalog',str(args.catalog.resolve()),
                    '--mapping',str(args.mapping.resolve()), '--plan',os.environ['EVIDENCE_INPUT_PLAN'],
                    '--side',args.side,'--raw',str(raw),'--run-id',os.environ['EVIDENCE_RUN_ID'],
                    '--output',os.environ['EVIDENCE_ASSERTIONS_PATH']], cwd=TASK,check=True)
if __name__ == '__main__': main()
