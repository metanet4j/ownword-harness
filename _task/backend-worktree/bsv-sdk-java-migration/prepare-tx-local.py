#!/usr/bin/env python3
"""transaction 局部的清单/映射/样本编号：冻结与把本轮探针轨迹转成 TS 输入。

样本编号按探针记录的入口顺序生成（`<入口>-<序号>`）；样本值只保留可比对的
`method/args/result`，源码行号留在探针原始轨迹里。值由标准双侧采集当场比较，
不复制一份语料。"""
import argparse
import importlib.util
import json
import os
import re
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('tx_local_locals', TASK / 'tx-local-locals.py')
locals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locals_module)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fragment(entry):
    """同一原文件的多个局部：按登记允许的 Java 类裁出本局部的用例与站点子集。

    Transaction.test.ts 同时承载 659 条向量（transaction-shared-vectors 专用局部）
    与 61 条普通用例（本局部）；不裁剪会让冻结计划要求向量用例也出现在本局部。"""
    catalog = read(TASK / 'module-tests.json')
    source = next(file for file in catalog['files'] if file['path'] == entry['file'])
    mapping_all = read(TASK / 'test-map.json')
    require(len({case['id'] for case in source['cases']}) == len(source['cases']),
            '固定清单用例 ID 重复：' + entry['file'])
    allowed = set(entry.get('java_classes') or [entry['java_class']])
    by_id = {case['id']: case for case in mapping_all['cases']}
    kept, mapping_cases = [], []
    for case in source['cases']:
        mapping = by_id[case['id']]
        require(len(mapping['java']) == 1, 'Java 用例未独立注册：' + case['id'])
        if mapping['java'][0]['className'] not in allowed:
            continue
        kept.append(case)
        mapping_cases.append(mapping)
    require(bool(kept), '本局部未裁出任何用例：' + entry['file'])
    for case in mapping_cases:
        require(case['java'][0]['className'] in allowed, 'Java 用例不属于本局部：' + case['id'])
    ids = {case['id'] for case in kept}
    assertion_sites = {site for case in mapping_cases for site in case['assertionIds']}
    source_sites = {site['id']: site for site in source['sites']}
    require(all(site in source_sites for site in assertion_sites), '映射断言站点不在固定清单：' + entry['file'])
    reviews = [review for review in mapping_all['siteReviews'] if review['id'] in source_sites]
    require(len(reviews) == len(source_sites), '站点审阅缺失：' + entry['file'])
    # 断言站点严格按本局部映射保留（validate_plan 要求全部被计划覆盖）；
    # 循环、条件与注册站点按审阅记录的归属用例保留。
    kept_ids = {review['id'] for review in reviews
                if review['id'] in assertion_sites
                or set(review.get('caseIds') or []) & ids}
    sites = [source_sites[site] for site in source_sites if site in kept_ids]
    reviews = [review for review in reviews if review['id'] in kept_ids]
    return ({**catalog, 'files': [dict(source, cases=kept, sites=sites)],
             'partialImplementationOnly': True},
            {**mapping_all, 'cases': mapping_cases, 'siteReviews': reviews},
            {case['id']: case for case in kept},
            {case['id']: case for case in mapping_cases})


def samples(entry, raw):
    catalog, mapping, cases, mapped = fragment(entry)
    by_identity = {(' '.join(case['names']), case['occurrence']): case for case in cases.values()}
    grouped = defaultdict(list)
    identities = {}
    seen = defaultdict(int)
    for row in rows(raw):
        require(row['source']['file'] == entry['file'], '入口输入来自其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_identity, '入口输入来自未登记用例')
        seen[key] += 1
        require(row['sequence'] == seen[key], '入口顺序不连续')
        case_id = by_identity[key]['id']
        identities[case_id] = key
        grouped[case_id].append({'sampleId': f"{row['method']}-{row['sequence']:02d}",
                                 'value': {'method': row['method'], 'args': row['args'], 'result': row['result']}})
    require(set(grouped) == set(cases), '固定 TS 原用例未全部触达公开入口：' + entry['file'])
    return catalog, mapping, mapped, grouped, identities


def assertion_runs(entry, raw, identities):
    """本轮每个用例实际执行的断言次数；辅助函数与循环会让同一站点执行多次。"""
    counts = defaultdict(int)
    for row in rows(raw):
        require(row['file'].endswith(entry['file']), '固定断言来自其他文件：' + str(row.get('file')))
        counts[(row['test'], row['occurrence'])] += 1
    return {case_id: counts[key] for case_id, key in identities.items()}


def site_matcher(source_lines, site, known):
    """冻结站点对应的 Jest matcher：本行最后一个 matcher，跨行 expect 时向下找链式调用。"""
    parts = site.rsplit(':', 3)
    require(len(parts) == 4, '断言站点身份格式无效：' + site)
    line = int(parts[-3])
    for offset in range(0, 12):
        index = line - 1 + offset
        if index >= len(source_lines):
            break
        names = [name for name in re.findall(r'\.([A-Za-z_$][\w$]*)\s*\(', source_lines[index])
                 if name in known]
        if names:
            return names[-1] if offset == 0 else names[0]
        if offset > 0 and not source_lines[index].strip().startswith((')', '.', '}')):
            break
    return None


def upstream_lines(entry):
    config = read(TASK / 'workspace.json')['upstream']
    source = TASK.parents[2] / config['path'] / config['packagePath'] / entry['file']
    return source.read_text().splitlines()


def assertion_matchers_of(entry, raw, identities, mapping_cases):
    """本轮每个用例的断言行 matcher 序列，以及各冻结站点的 matcher（未知为 None）。"""
    observed = rows(raw)
    known = {row['matcher'] for row in observed}
    lines = upstream_lines(entry)
    frozen = {case['id']: [site_matcher(lines, site, known) for site in case['assertionIds']]
              for case in mapping_cases}
    by_test = defaultdict(list)
    for row in observed:
        by_test[(row['test'], row['occurrence'])].append(row['matcher'])
    return frozen, {case_id: by_test[key] for case_id, key in identities.items()}


def spread_instances(site_ids, matchers, rows):
    """站点数与执行次数不整除时，按 matcher 把逐次执行对齐到各站点。

    同一个站点在循环里连续执行，因此每个站点的实例是一段连续区间；先按 matcher
    精确匹配，再在可行解里取各段长度最均匀的一组。"""
    total = len(rows)
    if total < len(site_ids):
        return None
    share = total / len(site_ids)
    memo = {}

    def solve(index, position):
        if index == len(site_ids):
            return (0.0, ()) if position == total else None
        if total - position < len(site_ids) - index:
            return None
        key = (index, position)
        if key in memo:
            return memo[key]
        best = None
        length = 1
        while position + length <= total and total - (position + length) >= len(site_ids) - index - 1:
            if matchers[index] is not None and rows[position + length - 1] != matchers[index]:
                break
            rest = solve(index + 1, position + length)
            if rest is not None:
                cost = (length - share) ** 2 + rest[0]
                if best is None or cost < best[0] - 1e-9:
                    best = (cost, (length,) + rest[1])
            length += 1
        memo[key] = best
        return best

    result = solve(0, 0)
    return None if result is None else result[1]


def plan_for(mapped, grouped, runs, loops, matchers, assertion_matchers_by_case):
    plan = {}
    for case_id, items in grouped.items():
        site_ids = mapped[case_id]['assertionIds']
        count = runs[case_id]
        require(count > 0, f'固定原用例没有实际断言：{case_id}')
        instances, sites = [], {}
        if count % len(site_ids) == 0:
            for round_index in range(1, count // len(site_ids) + 1):
                for site in site_ids:
                    identity = site if round_index == 1 else f'{site}#{round_index}'
                    instances.append(identity)
                    sites[identity] = site
        else:
            rows = matchers[case_id]
            require(len(rows) == count, '断言轨迹条数与实际执行次数不符：' + case_id)
            spread = spread_instances(site_ids, assertion_matchers_by_case[case_id], rows)
            require(spread is not None,
                    f'断言执行次数与冻结站点数不整除，需登记循环语义：{case_id}／{count}／{len(site_ids)}')
            for site, length in zip(site_ids, spread):
                for round_index in range(1, length + 1):
                    identity = site if round_index == 1 else f'{site}#{round_index}'
                    instances.append(identity)
                    sites[identity] = site
        # 循环站点只做结构覆盖：原测试的循环在辅助函数或 hooks 中执行时没有逐用例样本，
        # 统一按该用例实际采集到的入口样本登记（与 bn-arithmetic 的登记方式一致）。
        plan[case_id] = {'sampleIds': [sample['sampleId'] for sample in items],
                         'assertionIds': instances, 'assertionSites': sites,
                         'loopSamples': {site: [sample['sampleId'] for sample in items]
                                         for site in loops}}
    return plan


def freeze(options):
    entry = locals_module.local(options.local)
    catalog, mapping, mapped, grouped, identities = samples(entry, options.raw)
    loops = {site['id'] for file in catalog['files'] for site in file['sites'] if site['kind'] == 'loop'}
    frozen, actual = assertion_matchers_of(entry, options.assertions, identities, mapping['cases'])
    plan = plan_for(mapped, grouped, assertion_runs(entry, options.assertions, identities), loops,
                    actual, frozen)
    audit.validate_plan(catalog, mapping, plan)
    directory = Path(options.directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (('catalog.json', catalog), ('mapping.json', mapping), ('input-plan.json', plan)):
        (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'local': options.local, 'file': entry['file'], 'cases': len(plan),
                      'samples': sum(len(value['sampleIds']) for value in plan.values()),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values())},
                     ensure_ascii=False))


def emit_ts(options):
    entry = locals_module.local(options.local)
    _, _, _, grouped, _ = samples(entry, options.raw)
    plan = read(options.plan)
    require(set(plan) == set(grouped), '本轮用例集合与冻结计划不同')
    output = []
    for case_id, items in grouped.items():
        require([sample['sampleId'] for sample in items] == plan[case_id]['sampleIds'],
                '本轮样本编号与冻结计划不同：' + case_id)
        output.extend({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts', 'caseId': case_id,
                       'sampleId': sample['sampleId'], 'value': sample['value']} for sample in items)
    Path(options.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in output))
    print(json.dumps({'side': 'ts', 'local': options.local, 'cases': len(grouped), 'samples': len(output)},
                     ensure_ascii=False))


if __name__ == '__main__':
    audit_spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(audit_spec)
    audit_spec.loader.exec_module(audit)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('freeze', 'emit-ts'):
        command = sub.add_parser(name)
        command.add_argument('--local', required=True)
        command.add_argument('--raw', type=Path, required=True)
        if name == 'freeze':
            command.add_argument('--assertions', type=Path, required=True)
            command.add_argument('--directory', type=Path, required=True)
        else:
            command.add_argument('--plan', type=Path, required=True)
            command.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    (freeze if options.mode == 'freeze' else emit_ts)(options)
