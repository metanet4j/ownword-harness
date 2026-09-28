#!/usr/bin/env python3
"""标准局部证据门禁：按 full-evidence-locals.json 重跑双侧汇总，并验证输入/断言篡改被拒。

只适用于两侧共享一个运行目录的标准 capture 局部；专用局部（captureKind=specialized-local）
没有标准来源，本门禁拒绝处理。"""
import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
KEYS = ('catalog', 'mapping', 'input_plan', 'ts_inputs', 'ts_assertions', 'ts_run_manifest',
        'java_inputs', 'java_assertions', 'java_run_manifest')


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def lines(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def local(name):
    for item in read(CONFIG)['locals']:
        if item['name'] == name:
            require(item.get('captureKind') != 'specialized-local' and all(key in item for key in KEYS),
                    f'{name} 不是标准双侧采集局部，不能用本门禁')
            return item
    raise ValueError('未登记局部：' + name)


def resolve(item, run=None):
    """运行目录内的产物指向副本，清单类资料仍用原路径。"""
    home = Path(item['java_run_manifest']).resolve().parent
    paths = {}
    for key in KEYS:
        path = Path(item[key])
        paths[key] = (run / path.resolve().relative_to(home)) if run is not None and path.resolve(
        ).is_relative_to(home) else path
    paths['ts_report'] = [(run / Path(p).resolve().relative_to(home)) if run is not None and Path(
        p).resolve().is_relative_to(home) else Path(p) for p in item['ts_report']]
    paths['java_report'] = [(run / Path(p).resolve().relative_to(home)) if run is not None and Path(
        p).resolve().is_relative_to(home) else Path(p) for p in item['java_report']]
    return paths


def execute(paths, output):
    command = ['python3', str(TASK / 'evidence-bundle.py'),
               '--catalog', str(paths['catalog']), '--mapping', str(paths['mapping']),
               '--input-plan', str(paths['input_plan']),
               '--ts-inputs', str(paths['ts_inputs']), '--java-inputs', str(paths['java_inputs']),
               '--ts-assertions', str(paths['ts_assertions']),
               '--java-assertions', str(paths['java_assertions']),
               '--output', str(output),
               '--ts-run-manifest', str(paths['ts_run_manifest']),
               '--java-run-manifest', str(paths['java_run_manifest'])]
    for path in paths['ts_report']:
        command += ['--ts-report', str(path)]
    for path in paths['java_report']:
        command += ['--java-report', str(path)]
    return subprocess.run(command, cwd=TASK, capture_output=True, text=True)


def verify(name, output=None):
    item = local(name)
    paths = resolve(item)
    plan = read(paths['input_plan'])
    output = Path(output) if output else Path(item['java_run_manifest']).resolve().parent / 'parity.json'
    result = execute(paths, output)
    require(result.returncode == 0, '局部汇总被拒：' + result.stderr.strip()[-400:])
    parity = read(output)
    require(len(parity['cases']) == len(plan), '局部汇总用例数与固定计划不符')
    for report in paths['ts_report']:
        jest = read(report)
        require(jest.get('success') is True and jest['numTotalTests'] == jest['numPassedTests']
                and all(jest[key] == 0 for key in ('numFailedTests', 'numPendingTests', 'numTodoTests')),
                f'固定 TS 原报告未完整通过：{report}')
    for report in paths['java_report']:
        root = ET.parse(report).getroot()
        suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
        require(all(int(suite.attrib.get(key, '0')) == 0
                    for suite in suites for key in ('failures', 'errors', 'skipped'))
                and sum(int(suite.attrib['tests']) for suite in suites) > 0,
                f'Java 原报告未完整通过：{report}')
    samples = sum(len(case['inputSamples']['TS']) for case in parity['cases'])
    assertions = sum(len(case['ts']) for case in parity['cases'])
    require(all(case['inputSha256'] == case['tsInputSha256'] == case['javaInputSha256']
                for case in parity['cases']), '局部汇总存在未比对输入用例')
    for case in parity['cases']:
        require([row['id'] for row in case['ts']] == [row['id'] for row in case['java']],
                '局部汇总断言身份或顺序不符')
    ts = read(paths['ts_run_manifest'])
    java = read(paths['java_run_manifest'])
    require(ts['runId'] != java['runId'], '两侧运行身份重复')
    return {'formalAcceptance': False, 'name': name, 'cases': len(parity['cases']),
            'inputsCompared': samples, 'assertionsCompared': assertions,
            'tsRunId': ts['runId'], 'javaRunId': java['runId'], 'javaRevision': java['sourceRevision']}


def tamper(name):
    verify(name)
    item = local(name)

    def retag(rows):
        for row in rows:
            if isinstance(row.get('value'), dict):
                row['value'] = dict(row['value'], tampered=True)
                return
        raise ValueError('篡改目标缺失')

    def rewrite(rows):
        rows[0]['value']['actual'] = {'type': 'string', 'value': 'tampered'}

    for artifact, field, expected, mutate in (
            ('java_inputs', 'inputsSha256', 'TS/Java 输入或前置状态不同', retag),
            ('java_assertions', 'assertionsSha256', '实际结果不一致', rewrite)):
        home = Path(item['java_run_manifest']).resolve().parent
        with tempfile.TemporaryDirectory(prefix='local-gate-tamper-') as folder:
            copy = Path(folder) / 'run'
            shutil.copytree(home, copy)
            paths = resolve(item, copy)
            path = paths[artifact]
            rows = lines(path)
            mutate(rows)
            path.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
            manifest = paths['java_run_manifest']
            data = read(manifest)
            data[field] = sha(path)
            write(manifest, data)
            result = execute(paths, copy / 'parity.json')
            require(result.returncode != 0 and expected in result.stderr,
                    f'{artifact} 篡改未被拒绝或未走到预期判定：{result.stderr.strip()[-200:]}')
    return {'tamperedInputRejected': True, 'tamperedAssertionRejected': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('verify', 'tamper'))
    parser.add_argument('--name', required=True)
    options = parser.parse_args()
    try:
        outcome = verify(options.name) if options.action == 'verify' else tamper(options.name)
        print(json.dumps(outcome, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
