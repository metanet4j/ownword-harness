#!/usr/bin/env python3
"""把两端独立采集的输入和断言轨迹绑定到原始 Jest/Surefire 报告。"""
import argparse
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fail(message):
    raise ValueError(message)


def lines(path):
    result = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as error:
                fail(f'{path}:{number} 不是 JSON：{error}')
    return result


def grouped(path, field):
    by_case = {}
    for row in lines(path):
        case_id = row.get('caseId')
        if not isinstance(case_id, str) or not isinstance(row.get(field), str):
            fail(f'{path} 缺少 caseId 或 {field}')
        by_case.setdefault(case_id, []).append(row)
    return by_case


def same(expected, actual, label):
    if set(expected) != set(actual):
        fail(f'{label}：缺失 {sorted(set(expected)-set(actual))[:4]}；多余 {sorted(set(actual)-set(expected))[:4]}')


def unique(rows, field, label):
    keys = [row[field] for row in rows]
    if len(keys) != len(set(keys)):
        fail(f'{label} 重复 {field}')


def build(args):
    catalog, mapping, plan = read(args.catalog), read(args.mapping), read(args.input_plan)
    cases = {case['id']: case for file in catalog['files'] for case in file['cases']}
    mapped = {case['id']: case for case in mapping['cases']}
    if len(cases) != sum(len(file['cases']) for file in catalog['files']) or len(mapped) != len(mapping['cases']):
        fail('用例 ID 重复')
    same(cases, mapped, '映射用例')
    same(cases, plan, '输入计划用例')
    ts_inputs, java_inputs = grouped(args.ts_inputs, 'sampleId'), grouped(args.java_inputs, 'sampleId')
    ts_results, java_results = grouped(args.ts_assertions, 'assertionId'), grouped(args.java_assertions, 'assertionId')
    for label, rows in [('TS 输入', ts_inputs), ('Java 输入', java_inputs), ('TS 断言', ts_results), ('Java 断言', java_results)]:
        same(cases, rows, label + '用例')
    output = []
    for case_id in cases:
        expected_samples = plan[case_id].get('sampleIds')
        expected_assertions = plan[case_id].get('assertionIds')
        if not isinstance(expected_samples, list) or not expected_samples or not all(isinstance(x, str) for x in expected_samples):
            fail(f'输入计划为空或格式错误：{case_id}')
        if len(set(expected_samples)) != len(expected_samples):
            fail(f'输入计划样本重复：{case_id}')
        if not isinstance(expected_assertions, list) or not expected_assertions or len(set(expected_assertions)) != len(expected_assertions):
            fail(f'独立断言计划为空或重复：{case_id}')
        if expected_assertions != mapped[case_id]['assertionIds']:
            fail(f'映射断言与独立计划不符：{case_id}')
        inputs = {}
        for label, rows in [('TS', ts_inputs[case_id]), ('Java', java_inputs[case_id])]:
            unique(rows, 'sampleId', label + ' 输入')
            if [row['sampleId'] for row in rows] != expected_samples:
                fail(f'{label} 输入样本顺序、数量或 ID 不符：{case_id}')
            if any('value' not in row for row in rows):
                fail(f'{label} 输入缺少实际值：{case_id}')
            inputs[label] = [{'sampleId': row['sampleId'], 'value': row['value']} for row in rows]
        ts_hash = hashlib.sha256(canonical(inputs['TS']).encode()).hexdigest()
        java_hash = hashlib.sha256(canonical(inputs['Java']).encode()).hexdigest()
        if ts_hash != java_hash:
            fail(f'TS/Java 输入或前置状态不同：{case_id}')
        results = {}
        for label, rows in [('TS', ts_results[case_id]), ('Java', java_results[case_id])]:
            unique(rows, 'assertionId', label + ' 断言')
            if [row['assertionId'] for row in rows] != expected_assertions:
                fail(f'{label} 断言顺序、数量或 ID 不符：{case_id}')
            if any('value' not in row for row in rows):
                fail(f'{label} 断言缺少实际值：{case_id}')
            results[label] = [{'id': row['assertionId'], 'value': row['value']} for row in rows]
        for left, right in zip(results['TS'], results['Java']):
            if canonical(left['value']) != canonical(right['value']):
                fail(f'实际结果不一致：{case_id} / {left["id"]}')
        output.append({'id': case_id, 'inputSha256': ts_hash, 'tsInputSha256': ts_hash,
                       'javaInputSha256': java_hash, 'inputSamples': inputs,
                       'ts': results['TS'], 'java': results['Java']})
    capture_paths = {'inputPlan': args.input_plan, 'tsInputs': args.ts_inputs,
                     'javaInputs': args.java_inputs, 'tsAssertions': args.ts_assertions,
                     'javaAssertions': args.java_assertions}
    return {'upstreamCommit': catalog['upstreamCommit'], 'javaRevision': args.java_revision,
            'catalogSha256': digest(args.catalog),
            'tsReportSha256': sorted(digest(p) for p in args.ts_report),
            'javaReportSha256': sorted(digest(p) for p in args.java_report),
            'captureSha256': {key: digest(path) for key, path in capture_paths.items()},
            'cases': output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog', 'mapping', 'input-plan', 'ts-inputs', 'java-inputs',
                 'ts-assertions', 'java-assertions', 'java-revision', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--ts-report', action='append', required=True)
    parser.add_argument('--java-report', action='append', required=True)
    args = parser.parse_args()
    try:
        result = build(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cases': len(result['cases']), 'assertions': sum(len(c['ts']) for c in result['cases']),
                      'output': args.output}, ensure_ascii=False))


if __name__ == '__main__':
    main()
