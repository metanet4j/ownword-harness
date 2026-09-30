#!/usr/bin/env python3
"""全量 Java 采集：把本轮 TS 汇总输入接到全部 Java 重放，跑无过滤 clean test，收全部 Surefire 报告。

用法（全量运行的 javaCommand）：
    python3 run-full-java-capture.py --run-dir <runDir> --reports java-surefire.xml clean test

命令尾部的 clean test 是固定阶段声明（evidence-bundle 与 preflight 都要求最终 Java 命令里出现
无过滤的 clean test）；脚本内部始终执行无过滤 clean test。

环境变量由 evidence-bundle capture 注入；Java 断言原始轨迹写到 EVIDENCE_ASSERTIONS_PATH 旁的
java-assertions.raw.jsonl，再用 emit-assertion-observations.py 转成最终断言观察。
"""
import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK / 'metanet4j-bsv-sdk'
SUREFIRE = PROJECT / 'target/surefire-reports'
LOCK = TASK / '.cache/run.lock'
JAVA_TEST_ROOT = PROJECT / 'src/test/java'


def read_json(path):
    return json.loads(Path(path).read_text())


def java_ts_input_envs():
    """Java 测试源码里读的全部 MIGRATION_*_TS_INPUTS：本轮都要指向同一份 ts-inputs.jsonl。"""
    envs = set()
    for path in JAVA_TEST_ROOT.rglob('*.java'):
        envs.update(re.findall(r'System\.getenv\("(MIGRATION_[A-Z0-9_]*_TS_INPUTS)"\)',
                               path.read_text(errors='replace')))
    return sorted(envs)


def java_property_replays():
    """仍靠 -Dmigration.* 冻结语料驱动的 Java 重放：本轮不消费 ts-inputs.jsonl，需要登记说明。"""
    rows = {}
    for path in JAVA_TEST_ROOT.rglob('*.java'):
        text = path.read_text(errors='replace')
        for prop in sorted(set(re.findall(r'System\.getProperty\("(migration\.[A-Za-z0-9_.]+)"', text))):
            rows.setdefault(prop, []).append(str(path.relative_to(PROJECT)))
    return {prop: sorted(set(files)) for prop, files in sorted(rows.items())}


def lock_held():
    if not LOCK.exists():
        return False
    with open(LOCK, 'a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
        return False


def maven_command(report_path):
    command = [str(TASK / 'lock.sh'), str(TASK / 'mvn.sh'), '-f', str(PROJECT / 'pom.xml'),
               'clean', 'test', '-Dmigration.parity.java.output=' + str(report_path)]
    if lock_held():
        # 外层（evidence-bundle capture 序列）已经持有同一把锁；flock 不可重入，这里不能再套一层。
        command = command[1:]
        print('LOCK-ALREADY-HELD 外层已持锁，直接运行 Maven（仍受同一把锁保护）', file=sys.stderr)
    return command


def run_maven(command, env, run_dir):
    log = run_dir / 'java-maven.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=TASK, env=env, stdout=stream, stderr=subprocess.STDOUT)
    print(log.read_text()[-4000:], file=sys.stderr)
    return result


def suite_report(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
    problems = []
    for suite in suites:
        if any(int(suite.get(key, '0')) for key in ('failures', 'errors')):
            problems.append('Surefire 存在失败或错误：' + str(path))
        if int(suite.get('skipped', '0')):
            problems.append('Surefire 存在跳过用例：' + str(path))
    return suites, problems


def collect_reports(run_dir, requested):
    """把 target/surefire-reports 收进运行目录；requested 里的汇总名生成合并 XML。"""
    if not SUREFIRE.is_dir():
        return [], ['缺少 Surefire 报告目录：' + str(SUREFIRE)]
    sources = sorted(SUREFIRE.glob('TEST-*.xml'))
    if not sources:
        return [], ['Surefire 没有产出任何 TEST-*.xml']
    copied = run_dir / 'surefire'
    copied.mkdir(parents=True, exist_ok=True)
    suites, problems, total = [], [], 0
    for path in sources:
        parsed, found = suite_report(path)
        problems.extend(found)
        suites.extend(parsed)
        total += sum(int(suite.get('tests', '0')) for suite in parsed)
        shutil.copyfile(path, copied / path.name)
    if not total:
        problems.append('Surefire 报告里没有执行任何用例')
    aggregate = ET.Element('testsuites', {'name': 'metanet4j-bsv-sdk', 'tests': str(total),
                                          'failures': str(sum(int(s.get('failures', '0')) for s in suites)),
                                          'errors': str(sum(int(s.get('errors', '0')) for s in suites)),
                                          'skipped': str(sum(int(s.get('skipped', '0')) for s in suites))})
    for suite in suites:
        aggregate.append(suite)
    produced = []
    for name in requested:
        source = SUREFIRE / name
        target = run_dir / name
        if source.is_file():
            shutil.copyfile(source, target)
        else:
            ET.ElementTree(aggregate).write(target, encoding='utf-8', xml_declaration=True)
        produced.append(str(target))
    return produced, problems


def emit_assertions(run_dir, env, raw, summary):
    output = env.get('EVIDENCE_ASSERTIONS_PATH')
    if not output:
        summary['assertions'] = {'skipped': '缺少 EVIDENCE_ASSERTIONS_PATH'}
        return
    plan = env.get('EVIDENCE_INPUT_PLAN')
    catalog = Path(env.get('EVIDENCE_CATALOG', TASK / 'module-tests.json'))
    mapping = Path(env.get('EVIDENCE_MAPPING', TASK / 'test-map.json'))
    if not plan or not Path(plan).is_file():
        plan = run_dir / 'input-plan.json'
    command = ['python3', str(TASK / 'emit-assertion-observations.py'),
               '--catalog', str(catalog), '--mapping', str(mapping), '--plan', str(plan),
               '--side', 'java', '--raw', str(raw), '--run-id', env.get('EVIDENCE_RUN_ID', ''),
               '--output', output, '--allow-java-extra']
    result = subprocess.run(command, cwd=TASK, env=env, capture_output=True, text=True)
    if result.returncode:
        summary['assertions'] = {'error': (result.stderr or result.stdout)[-800:], 'argv': command}
    else:
        summary['assertions'] = json.loads(result.stdout.strip().splitlines()[-1])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--reports', action='append', default=[])
    parser.add_argument('--probes', type=Path, default=TASK / 'full-run-probes.json')
    parser.add_argument('stages', nargs='*', help='固定阶段声明，只接受 clean test')
    options = parser.parse_args()
    if options.stages and options.stages != ['clean', 'test']:
        parser.error('最终 Java 命令只接受无过滤的 clean test 阶段')
    options.run_dir = options.run_dir.resolve()
    options.run_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    ts_inputs = options.run_dir / 'ts-inputs.jsonl'
    if not ts_inputs.is_file():
        raise SystemExit('缺少本轮 TS 汇总输入：' + str(ts_inputs))
    table = read_json(options.probes) if options.probes.is_file() else {'envs': {}, 'locals': {}}
    configured = sorted({name for name in table.get('envs', {}) if name.endswith('_TS_INPUTS')})
    discovered = java_ts_input_envs()
    targets = sorted(set(configured) | set(discovered))
    for name in targets:
        env[name] = str(ts_inputs)
    raw_assertions = options.run_dir / 'java-assertions.raw.jsonl'
    if not env.get('MIGRATION_PARITY_JAVA_OUTPUT'):
        env['MIGRATION_PARITY_JAVA_OUTPUT'] = str(raw_assertions)
    if not env.get('EVIDENCE_SIDE'):
        env['EVIDENCE_SIDE'] = 'java'

    command = maven_command(raw_assertions)
    print(json.dumps({'maven': command, 'tsInputs': str(ts_inputs), 'tsInputEnvs': len(targets)},
                     ensure_ascii=False))
    result = run_maven(command, env, options.run_dir)
    summary = {'runId': env.get('EVIDENCE_RUN_ID'), 'runDir': str(options.run_dir),
               'maven': command, 'mavenExitCode': result.returncode,
               'tsInputs': str(ts_inputs), 'tsInputEnvs': targets,
               'tsInputEnvsNotInProbeTable': sorted(set(discovered) - set(configured)),
               'propertyDrivenReplays': java_property_replays()}
    problems = []
    if result.returncode:
        problems.append(f'Maven clean test 退出码非零：{result.returncode}；日志 '
                        + str(options.run_dir / 'java-maven.log'))
    produced, report_problems = collect_reports(options.run_dir, options.reports or ['java-surefire.xml'])
    summary['reports'] = produced
    problems.extend(report_problems)
    emit_assertions(options.run_dir, env, raw_assertions, summary)
    summary['problems'] = problems
    (options.run_dir / 'java-capture-report.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reports': produced, 'problems': len(problems),
                      'tsInputEnvs': len(targets)}, ensure_ascii=False))
    for problem in problems:
        print('JAVA-CAPTURE-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
