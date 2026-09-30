#!/usr/bin/env python3
"""把若干标准双侧局部汇总成 implementation-slice 的任务级逐断言报告。

输入是 `full-evidence-locals.json` 登记的标准局部：每个局部有自己的冻结输入计划
（`input_plan`，含断言站点与比较规则）、双侧逐断言观察行和已经封存的原始报告。
本脚本不重新运行测试，而是：

1. 复用 `audit-tests.py` 的 `compare_actuals`（固定语义规则的唯一实现）逐断言比较
   两侧实际值，并核对同一用例的输入摘要与断言身份顺序一致；
2. 按任务 `testFiles` 的冻结清单核对用例覆盖：每个用例恰好被一个局部覆盖；
3. 绑定当前 Java 工作树来源摘要，工作树必须干净。

产出的报告键与 `task-parity.py` 一致，便于 `feature_list.json` 的 taskAcceptance
直接引用；`formalAcceptance` 仍由完整模块门禁决定，不在这里通过。

用法：
    python3 local-task-parity.py --task migration-impl-auth-certificates \
        --local auth-certificate-class --local auth-verifiable-certificate \
        --output .cache/evidence/auth-certificates-same-source-20260929
"""
import argparse
import importlib.util
import json
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


audit = load('audit_tests', TASK / 'audit-tests.py')


def read(path):
    return json.loads(Path(path).read_text())


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def set_config(path):
    global CONFIG
    CONFIG = Path(path)


def local_entry(name):
    for item in read(CONFIG)['locals']:
        if item['name'] == name:
            for key in ('input_plan', 'ts_assertions', 'java_assertions', 'java_run_manifest'):
                require(key in item, f'{name} 不是标准双侧局部，缺少 {key}')
            return item
    raise ValueError('未登记局部：' + name)


def frozen_cases(task_id):
    features = read(TASK / 'feature_list.json')
    task = next(item for item in features['features'] if item['id'] == task_id)
    catalog = read(TASK / 'module-tests.json')
    files = {item['path']: item for item in catalog['files']}
    missing = sorted(set(task['testFiles']) - set(files))
    require(not missing, '冻结清单缺少任务测试文件：' + str(missing))
    cases = {}
    for path in task['testFiles']:
        for case in files[path]['cases']:
            cases[case['id']] = path
    return task, catalog, cases


def compare_local(name, cases, seen):
    """逐断言比较一个局部；返回该局部的用例覆盖与断言数。"""
    item = local_entry(name)
    plan = read(TASK / item['input_plan'])
    ts_rows = read_jsonl(TASK / item['ts_assertions'])
    java_rows = read_jsonl(TASK / item['java_assertions'])
    by_case = {'ts': {}, 'java': {}}
    for side, rows in (('ts', ts_rows), ('java', java_rows)):
        for row in rows:
            by_case[side].setdefault(row['caseId'], []).append(row)
    require(set(plan) == set(by_case['ts']) == set(by_case['java']),
            f'{name} 的观察行与冻结计划用例不一致')
    revision = read(TASK / item['java_run_manifest'])['sourceRevision']

    assertions = 0
    for case_id, expected in plan.items():
        require(case_id in cases, f'{name} 的用例不在任务冻结清单内：{case_id}')
        require(case_id not in seen, f'用例被多个局部重复覆盖：{case_id}')
        seen[case_id] = name
        left, right = by_case['ts'][case_id], by_case['java'][case_id]
        require([row['assertionId'] for row in left] == [row['assertionId'] for row in right],
                f'{name} 的断言身份或顺序不符：{case_id}')
        require(set(expected['assertionIds']) == {row['assertionId'] for row in left},
                f'{name} 的实际断言与冻结计划不符：{case_id}')
        for ts_row, java_row in zip(left, right):
            audit.compare_actuals(case_id, expected, ts_row['assertionId'],
                                  ts_row['value'], java_row['value'])
            assertions += 1
    return revision, assertions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--local', action='append', required=True)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--java-worktree', type=Path, default=TASK / 'metanet4j-bsv-sdk')
    parser.add_argument('--config', type=Path, default=None, help='局部登记表，测试反例时可指向副本')
    options = parser.parse_args()

    if options.config is not None:
        set_config(options.config)

    task, catalog, cases = frozen_cases(options.task)
    worktree = options.java_worktree.resolve()
    dirty = subprocess.check_output(['git', '-C', str(worktree), 'status', '--porcelain'], text=True)
    require(not dirty.strip(), f'验收 Java worktree 存在未提交源码：{worktree}')
    revision = audit.java_revision()
    target = subprocess.check_output(['git', '-C', str(worktree), 'rev-parse', 'HEAD'], text=True).strip()

    seen, assertions, revisions = {}, 0, set()
    for name in options.local:
        local_revision, count = compare_local(name, cases, seen)
        require(local_revision == revision,
                f'{name} 的运行来源 {local_revision[:8]} 与当前源码 {revision[:8]} 不一致')
        revisions.add(local_revision)
        assertions += count

    missing = sorted(set(cases) - set(seen))
    report = {
        'taskId': options.task,
        'upstreamCommit': catalog['upstreamCommit'],
        'javaRevision': revision,
        'javaTargetCommit': target,
        'testFiles': task['testFiles'],
        'locals': options.local,
        'casesTotal': len(cases),
        'casesCompared': len(seen),
        'assertionsCompared': assertions,
        'missingCases': len(missing),
        'missingAssertions': 0,
        'uncompared': 0,
        'extraJavaAssertions': 0,
        'nondeterministicCases': [],
        'nondeterministicPolicy': '逐断言复用 audit-tests.py 的固定比较规则；本任务无随机或耗时语义用例。',
        'cases': [{'id': case_id, 'file': cases[case_id], 'local': seen.get(case_id)}
                  for case_id in sorted(cases)],
        'missingCaseIds': missing,
        'taskAcceptancePassed': False,
    }
    report['taskAcceptancePassed'] = (
        report['casesCompared'] == report['casesTotal']
        and report['missingCases'] == 0 and report['missingAssertions'] == 0
        and report['uncompared'] == 0 and report['casesTotal'] > 0)
    output = options.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    (output / 'task-parity.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    summary = {key: report[key] for key in
               ('taskId', 'casesTotal', 'casesCompared', 'assertionsCompared', 'missingCases',
                'missingAssertions', 'uncompared', 'extraJavaAssertions', 'taskAcceptancePassed',
                'javaRevision', 'javaTargetCommit')}
    summary['locals'] = options.local
    print(json.dumps(summary, ensure_ascii=False))
    require(report['taskAcceptancePassed'], '任务级对照未通过，缺失用例：' + str(missing))


if __name__ == '__main__':
    main()
