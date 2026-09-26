#!/usr/bin/env python3
"""按 implementation-slice 对照 TS/Jest 与 Java/JUnit 的逐断言实际结果。

确定性用例精确比较实际值；Random.* 的随机字节用例按契约只比较断言语义
（matcher、期望长度/边界、pass）并单列为 nondeterministic。Java 测试中
额外断言作为额外回归单列，不冒充上游断言。
"""
import argparse
import importlib.util
import json
import subprocess
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

RANDOM_FILES = {
    'src/primitives/__tests/Random.test.ts',
    'src/primitives/__tests/Random.additional.test.ts',
}


def value_key(value):
    if not isinstance(value, dict):
        return ('scalar', str(value))
    kind = value.get('type')
    if kind in ('number', 'string', 'boolean', 'bigNumber'):
        return (kind, str(value.get('value')))
    if kind == 'null':
        return ('null',)
    if kind == 'undefined':
        return ('undefined',)
    if kind == 'map':
        return ('map', tuple(sorted((str(key), value_key(item)) for key, item in value.get('value', {}).items())))
    if kind == 'array':
        return ('array', tuple(value_key(item) for item in value.get('value', [])))
    return (str(kind), json.dumps(value.get('value'), sort_keys=True, ensure_ascii=False))


def matcher_class(matcher):
    return {
        'toHaveLength': 'equal',
        'toHaveBeenCalledTimes': 'equal',
        'toEqual': 'equal',
        'toBe': 'equal',
        'not.toEqual': 'notEqual',
        'toBeGreaterThanOrEqual': 'gte',
        'toBeLessThanOrEqual': 'lte',
        'toThrow': 'throw',
        'not.toThrow': 'notThrow',
    }.get(matcher, matcher)


def is_random_task(file_path):
    return file_path in RANDOM_FILES


def expected_value(row):
    value = row.get('expected')
    if isinstance(value, dict) and value.get('type') in ('number', 'string', 'boolean'):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    if isinstance(value, list):
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    return ''


def row_key(file_path, row):
    matcher = str(row.get('matcher', ''))
    negated = bool(row.get('negated', False))
    passed = bool(row.get('pass', True))
    if is_random_task(file_path):
        category = matcher_class(matcher)
        expected = expected_value(row) if category in ('equal', 'gte', 'lte') else ''
        return ('nondet', category, negated, passed, expected)
    actual = row.get('actual')
    if isinstance(actual, dict) and actual.get('kind') == 'return':
        return ('return', value_key(actual.get('value')))
    if isinstance(actual, dict) and actual.get('kind') == 'throw':
        return ('throw', str(actual.get('name')), str(actual.get('message')))
    if matcher in ('not.toThrow', 'toThrow'):
        return ('return', value_key(actual))
    return ('value', value_key(actual))


def align(file_path, ts_rows, java_rows):
    """小用例按最长公共子序列对齐；原规模循环按顺序线性核对。"""
    n, m = len(ts_rows), len(java_rows)
    ts_keys = [row_key(file_path, row) for row in ts_rows]
    java_keys = [row_key(file_path, row) for row in java_rows]
    if n == m and ts_keys == java_keys:
        return [], list(zip(range(n), range(n))), 0
    if n * m > 2_000_000:
        limit = min(n, m)
        matched = [(i, i) for i in range(limit) if ts_keys[i] == java_keys[i]]
        unmatched = [ts_rows[i] for i in range(limit) if ts_keys[i] != java_keys[i]]
        unmatched.extend(ts_rows[limit:])
        return unmatched, matched, m - len(matched)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            best = max(dp[i + 1][j], dp[i][j + 1])
            if ts_keys[i] == java_keys[j]:
                best = max(best, 1 + dp[i + 1][j + 1])
            dp[i][j] = best
    unmatched_ts, matched, i, j = [], [], 0, 0
    while i < n and j < m:
        if ts_keys[i] == java_keys[j]:
            matched.append((i, j))
            i += 1
            j += 1
        elif dp[i + 1][j] >= dp[i][j + 1]:
            unmatched_ts.append(ts_rows[i])
            i += 1
        else:
            j += 1
    while i < n:
        unmatched_ts.append(ts_rows[i])
        i += 1
    return unmatched_ts, matched, m - len(matched)


def load_task(task_id):
    features = json.loads((TASK / 'feature_list.json').read_text())
    task = next(item for item in features['features'] if item['id'] == task_id)
    upstream = json.loads((TASK / 'module-tests.json').read_text())
    mapping = json.loads((TASK / 'test-map.json').read_text())
    test_files = list(task.get('testFiles', []))
    file_objects = {item['path']: item for item in upstream['files'] if item['path'] in test_files}
    if set(file_objects) != set(test_files):
        missing = sorted(set(test_files) - set(file_objects))
        raise SystemExit(f'冻结清单缺少任务测试文件：{missing}')
    case_by_ts, case_by_java, case_file = {}, {}, {}
    for test_file in test_files:
        file_obj = file_objects[test_file]
        for case in file_obj['cases']:
            full_name = ' '.join(case['names'])
            case_by_ts[(test_file, full_name, case.get('occurrence', 1))] = case['id']
            case_file[case['id']] = test_file
    for case in mapping['cases']:
        for java in case.get('java', []):
            case_by_java[(java['className'], java['name'])] = case['id']
    return task, test_files, case_by_ts, case_by_java, case_file


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def compare(task_id, ts_path, java_path):
    task, test_files, case_by_ts, case_by_java, case_file = load_task(task_id)
    ts_rows, java_rows = read_jsonl(ts_path), read_jsonl(java_path)
    ts_by_case, java_by_case = defaultdict(list), defaultdict(list)
    names_without_file = defaultdict(list)
    for (file_path, full_name, occurrence), case_id in case_by_ts.items():
        names_without_file[full_name].append(case_id)
    for row in ts_rows:
        source = str(row.get('file', '')).replace('\\', '/')
        matches = [file_path for file_path in test_files if source == file_path or source.endswith('/' + file_path)]
        if source and len(matches) != 1:
            raise ValueError(f'TS 轨迹文件不能唯一定位：{source}')
        if matches:
            occurrence = row.get('occurrence')
            if occurrence is None and sum(1 for file_path, name, _ in case_by_ts if file_path == matches[0] and name == row.get('test')) > 1:
                raise ValueError(f'TS 同名参数行缺少 occurrence：{matches[0]} / {row.get("test")}')
            case_id = case_by_ts.get((matches[0], row.get('test'), occurrence or 1))
        else:
            candidates = names_without_file.get(row.get('test'), [])
            if len(candidates) > 1:
                raise ValueError(f'TS 同名用例缺少文件定位：{row.get("test")}')
            case_id = candidates[0] if candidates else None
        if case_id is not None:
            ts_by_case[case_id].append(row)
    for row in java_rows:
        identity = tuple(str(row.get('test', '')).split('#', 1))
        case_id = case_by_java.get(identity)
        if case_id is not None:
            java_by_case[case_id].append(row)

    cases = []
    total_ts = total_java = total_matched = total_missing = total_extra = missing_cases = 0
    nondeterministic = []
    for case_id, test_file in sorted(case_file.items()):
        ts_sequence, java_sequence = ts_by_case.get(case_id, []), java_by_case.get(case_id, [])
        unmatched, matched, extra = align(test_file, ts_sequence, java_sequence)
        if not ts_sequence or not java_sequence:
            missing_cases += 1
        case = {
            'id': case_id,
            'file': test_file,
            'tsAssertions': len(ts_sequence),
            'javaAssertions': len(java_sequence),
            'matchedAssertions': len(matched),
            'missingAssertions': len(unmatched),
            'extraJavaAssertions': extra,
        }
        if is_random_task(test_file) and (ts_sequence or java_sequence):
            case['nondeterministic'] = True
            nondeterministic.append(case_id)
        if unmatched:
            case['missing'] = [{'matcher': row.get('matcher'), 'actual': row.get('actual')} for row in unmatched]
        cases.append(case)
        total_ts += len(ts_sequence)
        total_java += len(java_sequence)
        total_matched += len(matched)
        total_missing += len(unmatched)
        total_extra += extra
    report = {
        'taskId': task_id,
        'upstreamCommit': json.loads((TASK / 'module-tests.json').read_text())['upstreamCommit'],
        'javaRevision': audit.java_revision(),
        'testFiles': test_files,
        'casesTotal': len(cases),
        'casesCompared': len(cases) - missing_cases,
        'assertionsCompared': total_matched,
        'missingCases': missing_cases,
        'missingAssertions': total_missing,
        'uncompared': total_missing,
        'extraJavaAssertions': total_extra,
        'nondeterministicCases': nondeterministic,
        'nondeterministicPolicy': 'Random.* 随机字节用例比较 matcher/期望边界/pass，不比较跨语言随机字节本身。',
        'cases': cases,
    }
    report['taskAcceptancePassed'] = (
        report['missingCases'] == 0
        and report['missingAssertions'] == 0
        and report['uncompared'] == 0
        and report['casesCompared'] == report['casesTotal']
        and report['casesTotal'] > 0
    )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--task', required=True)
    parser.add_argument('--ts', required=True, type=Path)
    parser.add_argument('--java', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = compare(args.task, args.ts, args.java)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: report[key] for key in (
        'taskId', 'casesTotal', 'casesCompared', 'assertionsCompared',
        'missingAssertions', 'uncompared', 'extraJavaAssertions',
        'nondeterministicCases', 'taskAcceptancePassed')}, ensure_ascii=False))
    return 0 if report['taskAcceptancePassed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
