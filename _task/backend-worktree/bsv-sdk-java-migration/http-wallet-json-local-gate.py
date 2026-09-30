#!/usr/bin/env python3
"""HTTPWalletJSON 原用例双侧同输入局部门禁：复核汇总，并验证输入/断言篡改被拒。"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

TASK = Path(__file__).resolve().parent
PLAN = TASK / '.cache/evidence/http-wallet-json-plan-20260927'
FILE = 'src/wallet/substrates/__tests/HTTPWalletJSON.test.ts'
CASES = 53
ASSERTIONS = 73
INPUTS = 214


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def execute(run, plan, output):
    command = ['python3', str(TASK / 'evidence-bundle.py'),
               '--catalog', str(plan / 'catalog.json'), '--mapping', str(plan / 'mapping.json'),
               '--input-plan', str(plan / 'input-plan.json'),
               '--ts-inputs', str(run / 'ts-inputs.jsonl'), '--java-inputs', str(run / 'java-inputs.jsonl'),
               '--ts-assertions', str(run / 'ts-assertions.jsonl'),
               '--java-assertions', str(run / 'java-assertions.jsonl'),
               '--output', str(output),
               '--ts-run-manifest', str(run / 'ts-run.json'),
               '--java-run-manifest', str(run / 'java-run.json'),
               '--ts-report', str(run / 'ts-jest.json'), '--java-report', str(run / 'java-surefire.xml')]
    return subprocess.run(command, cwd=TASK, capture_output=True, text=True)


def verify(run, plan):
    output = run / 'parity.json'
    result = execute(run, plan, output)
    require(result.returncode == 0, '局部汇总被拒：' + result.stderr.strip()[-500:])
    parity = read(output)
    jest = read(run / 'ts-jest.json')
    require(jest['success'] is True and jest['numTotalTests'] == jest['numPassedTests'] == CASES
            and all(jest[key] == 0 for key in ('numFailedTests', 'numPendingTests', 'numTodoTests')),
            '固定 HTTPWalletJSON 原 Jest 未完整通过')
    suite = ET.parse(run / 'java-surefire.xml').getroot()
    require(suite.tag == 'testsuite' and int(suite.attrib['tests']) == CASES
            and all(int(suite.attrib[key]) == 0 for key in ('failures', 'errors', 'skipped')),
            'Java 原例未完整通过')
    samples = sum(len(case['inputSamples']['TS']) for case in parity['cases'])
    assertions = sum(len(case['ts']) for case in parity['cases'])
    require(len(parity['cases']) == CASES and samples == INPUTS and assertions == ASSERTIONS,
            '局部汇总用例、样本或断言数量不符')
    require(all(case['inputSha256'] == case['tsInputSha256'] == case['javaInputSha256']
                for case in parity['cases']), '局部汇总存在未比对输入用例')
    for case in parity['cases']:
        require([row['id'] for row in case['ts']] == [row['id'] for row in case['java']],
                '局部汇总断言身份或顺序不符')
    tsm = read(run / 'ts-run.json')
    jvm = read(run / 'java-run.json')
    require(tsm['runId'] != jvm['runId'] and tsm['side'] == 'ts' and jvm['side'] == 'java',
            '两侧运行身份缺失或重复')
    return {'formalAcceptance': False, 'cases': len(parity['cases']), 'inputsCompared': samples,
            'assertionsCompared': assertions, 'tsRunId': tsm['runId'], 'javaRunId': jvm['runId'],
            'javaRevision': jvm['sourceRevision']}


def tamper(run, plan):
    verify(run, plan)
    def retag(rows):
        for row in rows:
            if isinstance(row.get('value'), dict) and 'method' in row['value']:
                row['value']['method'] = row['value']['method'] + '-tampered'
                return
        raise ValueError('篡改目标缺失')

    def rewrite(rows):
        rows[0]['value']['actual'] = {'type': 'string', 'value': 'tampered'}

    for artifact, field, expected, mutate in (
            ('java-inputs.jsonl', 'inputsSha256', 'TS/Java 输入或前置状态不同', retag),
            ('java-assertions.jsonl', 'assertionsSha256', '实际结果不一致', rewrite)):
        with tempfile.TemporaryDirectory(prefix='http-json-tamper-') as folder:
            copy = Path(folder) / 'run'
            shutil.copytree(run, copy)
            path = copy / artifact
            rows = lines(path)
            mutate(rows)
            path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            manifest = copy / 'java-run.json'
            data = read(manifest)
            data[field] = sha(path)
            manifest.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
            result = execute(copy, plan, copy / 'parity.json')
            require(result.returncode != 0 and expected in result.stderr,
                    f'{artifact} 篡改未被拒绝或未走到预期判定：{result.returncode} {result.stderr.strip()[-200:]}')
    return {'tamperedInputRejected': True, 'tamperedAssertionRejected': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'tamper'))
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--plan', type=Path, default=PLAN)
    options = parser.parse_args()
    try:
        outcome = verify(options.run.resolve(), options.plan.resolve()) if options.action == 'verify' else \
            tamper(options.run.resolve(), options.plan.resolve())
        print(json.dumps(outcome, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
