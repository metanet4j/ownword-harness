#!/usr/bin/env python3
"""将本轮原始 matcher 轨迹按冻结身份映射为逐断言实际观察。"""
import argparse
from collections import defaultdict
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_case_index(catalog, mapping, plan):
    ts, java = {}, {}
    mapped = {case['id']: case for case in mapping['cases']}
    require(set(plan) <= set(mapped), '计划包含未知 Java 映射用例')
    for file in catalog['files']:
        for case in file['cases']:
            if case['id'] not in plan:
                continue
            name = ' '.join(case['names'])
            key = (file['path'], name, case['occurrence'])
            require(key not in ts, '重复 TS 用例身份：' + str(key))
            ts[key] = case['id']
            for registration in mapped[case['id']]['java']:
                identity = registration['className'] + '#' + registration['name']
                require(identity not in java, 'Java 注册身份重复：' + identity)
                java[identity] = case['id']
    require(set(plan) == set(ts.values()) == set(java.values()), '计划与冻结用例身份不一致')
    return ts, java


def file_name(raw_path, paths):
    matches = [path for path in paths if raw_path == path or raw_path.endswith('/' + path)]
    require(len(matches) == 1, '原始 TS 轨迹文件不在唯一冻结范围：' + raw_path)
    return matches[0]


def observations(catalog, mapping, plan, side, raw, run_id, allow_java_extra=False):
    require(side in ('ts', 'java') and run_id, '采集侧别或 runId 无效')
    ts, java = source_case_index(catalog, mapping, plan)
    grouped = defaultdict(list)
    ts_matcher_counts = defaultdict(int)
    extras = 0
    for number, line in enumerate(Path(raw).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        if side == 'ts':
            path = file_name(row['file'], {key[0] for key in ts})
            case_id = ts.get((path, row['test'], row['occurrence']))
            require(case_id is not None, f'范围外 TS 断言：{raw}:{number}')
            require(row.get('pass') is True, f'固定 TS 原断言失败：{raw}:{number}')
        else:
            identity = row['test']
            require(identity.endswith('#' + row['method']), f'Java 方法身份矛盾：{raw}:{number}')
            case_id = java.get(identity)
            if case_id is None and allow_java_extra:
                extras += 1
                continue
            require(case_id is not None, f'范围外 Java 断言：{raw}:{number}')
        planned = plan[case_id]['assertionIds']
        position = len(grouped[case_id])
        require(position < len(planned), f'原断言次数多于计划：{case_id}')
        if side == 'ts':
            # 固定 Jest 采集器的 index 按文件、测试名和 matcher 累计；
            # 同名注册的 occurrence 不会重置这个计数。
            counter = (path, row['test'], row['matcher'])
            ts_matcher_counts[counter] += 1
            require(row['index'] == ts_matcher_counts[counter], f'原 TS matcher 序号不连续：{case_id}')
        else:
            require(row['index'] == position + 1, f'原 Java 断言序号不连续：{case_id}')
        require(isinstance(row['matcher'], str) and isinstance(row['negated'], bool)
                and 'actual' in row and 'expected' in row, f'原断言缺少真实值：{raw}:{number}')
        value = {key: row[key] for key in ('matcher', 'negated', 'actual', 'expected')}
        if side == 'ts' and isinstance(value['expected'], list) and value['expected']:
            # Jest 把多个 matcher 实参记为裸 JSON 数组；Java 记录器以 typed array
            # 表示同一参数序列。只规范容器，不改动原始参数的元素和值。
            value['expected'] = {'type': 'array', 'value': value['expected']}
        value['kind'] = 'assertion'
        rule = plan[case_id].get('comparisonRules', {}).get(planned[position])
        if rule in ('void-completion-null-adapter-v1', 'async-ready-null-adapter-v1',
                    'native-null-absence-v1') and 'pass' in row:
            value['pass'] = row['pass']
        grouped[case_id].append({'runId': run_id, 'side': side, 'caseId': case_id,
                                 'assertionId': planned[position], 'value': value})
    require(set(grouped) == set(plan), f'{side} 原断言缺少用例 {len(set(plan) - set(grouped))}')
    for case_id, expected in plan.items():
        require(len(grouped[case_id]) == len(expected['assertionIds']),
                f'{side} 原断言次数与计划不符：{case_id}')
    output = [row for case_id in plan for row in grouped[case_id]]
    return output, extras


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog', 'mapping', 'plan', 'side', 'raw', 'run-id', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--allow-java-extra', action='store_true')
    args = parser.parse_args()
    rows, extras = observations(read(args.catalog), read(args.mapping), read(args.plan),
                                args.side, args.raw, args.run_id, args.allow_java_extra)
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    print(json.dumps({'side': args.side, 'cases': len(set(row['caseId'] for row in rows)),
                      'assertions': len(rows), 'ignoredJavaExtraAssertions': extras}))


if __name__ == '__main__':
    main()
