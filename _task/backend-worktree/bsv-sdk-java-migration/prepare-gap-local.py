#!/usr/bin/env python3
"""结构覆盖率缺口局部的清单/映射/样本编号：冻结与把本轮探针轨迹转成 TS 输入。

样本编号按探针记录的入口顺序生成（`<入口>-<序号>`）；样本值只保留可比对的
`method/args/result`，源码行号留在探针原始轨迹里。值由标准双侧采集当场比较，
不复制一份语料。"""
import argparse
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('gap_locals', TASK / 'gap-locals.py')
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
    catalog = read(TASK / 'module-tests.json')
    source = next(file for file in catalog['files'] if file['path'] == entry['file'])
    mapping_all = read(TASK / 'test-map.json')
    ids = {case['id'] for case in source['cases']}
    mapping_cases = [case for case in mapping_all['cases'] if case['id'] in ids]
    require(len(mapping_cases) == len(ids), 'Java 映射用例数不同：' + entry['file'])
    for case in mapping_cases:
        require(len(case['java']) == 1 and case['java'][0]['className'] == entry['java_class'],
                'Java 用例未独立注册：' + entry['file'])
    sites = {site['id'] for site in source['sites']}
    reviews = [review for review in mapping_all['siteReviews'] if review['id'] in sites]
    require(len(reviews) == len(sites), '站点审阅缺失：' + entry['file'])
    return ({**catalog, 'files': [source], 'partialImplementationOnly': True},
            {**mapping_all, 'cases': mapping_cases, 'siteReviews': reviews},
            {case['id']: case for case in source['cases']},
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


def plan_for(mapped, grouped, runs, loops):
    plan = {}
    for case_id, items in grouped.items():
        site_ids = mapped[case_id]['assertionIds']
        count = runs[case_id]
        require(count > 0 and count % len(site_ids) == 0,
                f'断言执行次数与冻结站点数不整除，需登记循环语义：{case_id}／{count}／{len(site_ids)}')
        instances, sites = [], {}
        for round_index in range(1, count // len(site_ids) + 1):
            for site in site_ids:
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
    plan = plan_for(mapped, grouped, assertion_runs(entry, options.assertions, identities), loops)
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
