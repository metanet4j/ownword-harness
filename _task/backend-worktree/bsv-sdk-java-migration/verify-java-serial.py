#!/usr/bin/env python3
"""聚焦验证：用全量 Java 阶段**同一套注入**只跑指定的几个测试类，核对 Java 输入是否补齐。

它复用 `run-full-java-capture.py::serial_plan()`（全量阶段的真实注入点）与两个后置转换器，
所以验证的接线与全量运行完全一致，只是把 Maven 的用例范围收窄到 `-Dtest=<类>`。

判定标准（任一不满足即非零退出）：
  1. 目标类在 `test-map.json` 里的每个 caseId 都出现在本轮 `java-inputs.jsonl`；
  2. 每个 caseId 的 `sampleId` 序列与 `module-tests.json` 的冻结计划逐项相同；
  3. 目标类的 caseId 全部属于各自的 TS 原文件（防止错配）。

用法：
    python3 verify-java-serial.py --classes ValidationHelpersTest,WalletErrorTest \\
        --run-dir .cache/evidence/java-serial-focus-<日期>
    # 需要向量侧时加 --vector（同时跑 4 个共享向量类并调用 java-vector-inputs.py）
"""
import argparse
import importlib.util
import json
import os
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK / 'metanet4j-bsv-sdk'
SUREFIRE = PROJECT / 'target/surefire-reports'
# A1 共享向量局部的四个 Java 测试类（身份取自各局部 mapping.json 的 java.className）。
VECTOR_CLASSES = ('ScriptVectorsTest', 'SpendValidVectorsTest', 'SpendStandaloneValidVectorsTest',
                  'TransactionCompleteVectorsTest')


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def java_classes():
    """TS 原文件 → Java 测试类（来自冻结映射表）。"""
    result = {}
    for case in read(TASK / 'test-map.json')['cases']:
        for item in case['java']:
            result.setdefault(item['className'].rsplit('.', 1)[-1], set()).add(case['id'])
    return result


def plan_of(case_ids, plan):
    return {case: plan[case] for case in case_ids if case in plan}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classes', required=True, help='逗号分隔的 Java 测试类简单名')
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--vector', action='store_true', help='同时跑 4 个共享向量类')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--plan-reference', type=Path,
                        default=TASK / '.cache/evidence/full-run-14-20260901/input-plan.json',
                        help='权威逐用例 sampleIds（bundle 会按它校验）；缺省用上一轮全量计划')
    options = parser.parse_args()
    run_dir = options.run_dir.resolve()
    run_dir.mkdir(parents=True, exist_ok=True)
    capture = load(TASK / 'run-full-java-capture.py', 'run_full_java_capture')
    classes = [name for name in options.classes.split(',') if name]
    if options.vector:
        classes += [name for name in VECTOR_CLASSES if name not in classes]

    # 1) 与全量阶段同一套 A2 注入（合并语料、校验引用、清理输出落点）。
    properties, serial_env, serial_summary, problems = capture.serial_plan(run_dir)
    if problems:
        for problem in problems:
            print('VERIFY-PROBLEM ' + problem, file=sys.stderr)
        return 2
    inputs = run_dir / 'java-inputs.jsonl'
    for stale in (inputs, run_dir / 'java-vector-inputs.raw.jsonl', run_dir / 'java-assertions.raw.jsonl'):
        if stale.exists():
            stale.unlink()
    env = dict(os.environ)
    env.update(serial_env)
    env.update({capture.VECTOR_INPUTS_ENV: str(run_dir / 'java-vector-inputs.raw.jsonl'),
                'EVIDENCE_RUN_ID': uuid.uuid4().hex, 'EVIDENCE_SIDE': 'java',
                'EVIDENCE_INPUTS_PATH': str(inputs),
                'EVIDENCE_ASSERTIONS_PATH': str(run_dir / 'java-assertions.jsonl'),
                'MIGRATION_PARITY_JAVA_OUTPUT': str(run_dir / 'java-assertions.raw.jsonl')})
    env.pop('EVIDENCE_INPUT_PLAN', None)
    inputs.touch()

    # 2) 收窄到目标类的 clean test，属性与全量阶段逐字相同。
    command = [str(TASK / 'lock.sh'), str(TASK / 'mvn.sh'), '-f', str(PROJECT / 'pom.xml'),
               'clean', 'test', '-Dtest=' + ','.join(classes),
               '-Dmigration.parity.java.output=' + str(run_dir / 'java-assertions.raw.jsonl')]
    for name, value in sorted(properties.items()):
        command.append(f'-D{name}={value}')
    log = run_dir / 'focus-maven.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=TASK, env=env, stdout=stream, stderr=subprocess.STDOUT)
    tail = log.read_text()[-1500:]
    report = {'classes': classes, 'maven': command, 'mavenExitCode': result.returncode,
              'log': str(log), 'logTail': tail, 'serialEntries': serial_summary}
    problems = [] if result.returncode == 0 else [f'Maven 退出码 {result.returncode}，见 {log}']

    # 3) 与全量阶段同一套后置转换。
    raw_convert = _locals_for(classes)
    converter = ['python3', str(TASK / 'full-java-serial-convert.py'), '--run-dir', str(run_dir)]
    for local in raw_convert:
        converter += ['--local', local]
    if raw_convert:
        done = subprocess.run(converter, cwd=TASK, env=env, capture_output=True, text=True)
        report['serialInputs'] = {'argv': converter, 'exitCode': done.returncode,
                                  'stdout': done.stdout.strip()[-800:], 'stderr': done.stderr[-800:]}
        if done.returncode:
            problems.append('raw-convert 转换失败：' + done.stderr.strip()[-400:])
    if options.vector:
        done = subprocess.run(['python3', str(TASK / capture.VECTOR_INPUTS_SCRIPT),
                               '--run-dir', str(run_dir)], cwd=TASK, env=env,
                              capture_output=True, text=True)
        report['vectorInputs'] = {'exitCode': done.returncode, 'stdout': done.stdout.strip()[-1200:],
                                  'stderr': done.stderr[-400:]}
        if done.returncode:
            problems.append('向量归一化失败：' + done.stderr.strip()[-400:])

    # 4) 逐类核对 caseId 与 sampleId。
    plan = read(TASK / 'module-tests.json')
    complete = {case['id']: case for item in plan['files'] for case in item['cases']}
    reference = options.plan_reference if options.plan_reference.is_file() else None
    frozen = read(reference) if reference else None
    report['planReference'] = str(reference) if reference else None
    owners = java_classes()
    actual = {}
    for row in rows(inputs):
        actual.setdefault(row['caseId'], []).append(row['sampleId'])
    checked = {}
    for name in classes:
        case_ids = owners.get(name, set())
        covered = [case for case in case_ids if case in actual]
        mismatched = [case for case in covered if len(actual[case]) != len(set(actual[case]))]
        checked[name] = {'cases': len(case_ids), 'casesWithJavaInput': len(covered),
                         'missing': len(case_ids) - len(covered),
                         'duplicateSampleIds': len(mismatched),
                         'missingExamples': sorted(case_ids - set(covered))[:3]}
        if len(covered) != len(case_ids) or mismatched:
            problems.append(f'{name} 的 Java 输入不完整：{checked[name]}')
    if frozen:
        faults = [case for case in actual
                  if case in frozen and actual[case] != frozen[case]['sampleIds']]
        report['sampleIdMismatchAgainstFrozenPlan'] = len(faults)
        if faults:
            problems.append(f'{len(faults)} 个用例的 sampleId 与冻结计划不同，例如 {faults[0]}')
    report['classesChecked'] = checked
    report['javaInputsRows'] = sum(len(value) for value in actual.values())
    report['javaInputsCases'] = len(actual)
    report['surefire'] = sorted(path.name for path in SUREFIRE.glob('TEST-*.xml'))
    report['problems'] = problems
    if options.report:
        options.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in
                      ('classes', 'mavenExitCode', 'javaInputsRows', 'javaInputsCases',
                       'classesChecked', 'problems')}, ensure_ascii=False, indent=1))
    return 1 if problems else 0


def _locals_for(classes):
    """目标类对应哪些 A2 局部（用映射表的 files → test-map 的 Java 类反查）。"""
    mapping = read(TASK / 'test-map.json')
    wanted = set(classes)
    case_ids = {case['id'] for case in mapping['cases']
                if any(item['className'].rsplit('.', 1)[-1] in wanted for item in case['java'])}
    table = read(TASK / 'java-serial-entries.json')['entries']
    result = []
    for local, entry in table.items():
        plan_path = TASK / 'full-evidence-locals.json'
        if entry['shape'] != 'raw-convert':
            continue
        for item in read(plan_path)['locals']:
            if item['name'] == local and item.get('input_plan') \
                    and (TASK / item['input_plan']).is_file():
                if set(read(TASK / item['input_plan'])) & case_ids:
                    result.append(local)
    return result


if __name__ == '__main__':
    sys.exit(main())
