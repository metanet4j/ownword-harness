#!/usr/bin/env python3
"""LivePolicy.test.ts 的局部计划：冻结清单/映射/样本编号，并把探针原始轨迹转成本轮 TS 输入。

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
SOURCE = 'src/transaction/fee-models/__tests/LivePolicy.test.ts'
JAVA = 'com.metanet4j.bsv.transaction.fee_models.LivePolicyTest'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fragment():
    catalog = read(TASK / 'module-tests.json')
    source = next(file for file in catalog['files'] if file['path'] == SOURCE)
    require(len(source['cases']) == 8, 'LivePolicy 原用例数不同')
    mapping_all = read(TASK / 'test-map.json')
    ids = {case['id'] for case in source['cases']}
    mapping_cases = [case for case in mapping_all['cases'] if case['id'] in ids]
    require(len(mapping_cases) == len(ids), 'Java 映射用例数不同')
    for case in mapping_cases:
        require(len(case['java']) == 1 and case['java'][0]['className'] == JAVA, 'Java 用例未独立注册')
    sites = {site['id'] for site in source['sites']}
    reviews = [review for review in mapping_all['siteReviews'] if review['id'] in sites]
    require(len(reviews) == len(sites), '站点审阅缺失')
    return ({**catalog, 'files': [source], 'partialImplementationOnly': True},
            {**mapping_all, 'cases': mapping_cases, 'siteReviews': reviews},
            {case['id']: case for case in source['cases']},
            {case['id']: case for case in mapping_cases})


def samples(args):
    """按探针原始轨迹还原每个用例的样本身份与值。"""
    catalog, mapping, cases, mapped = fragment()
    by_identity = {(' '.join(case['names']), case['occurrence']): case for case in cases.values()}
    grouped = defaultdict(list)
    seen = defaultdict(int)
    for row in rows(args.raw):
        require(row['source']['file'] == SOURCE, '入口输入来自其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_identity, '入口输入来自未登记用例')
        seen[key] += 1
        require(row['sequence'] == seen[key], '入口顺序不连续')
        case_id = by_identity[key]['id']
        grouped[case_id].append({'sampleId': f"{row['method']}-{row['sequence']:02d}",
                                 'value': {'method': row['method'], 'args': row['args'], 'result': row['result']}})
    require(set(grouped) == set(cases), '固定 TS 原用例未全部触达公开入口')
    return catalog, mapping, cases, mapped, grouped


def plan_for(mapped, grouped):
    return {case_id: {'sampleIds': [sample['sampleId'] for sample in items],
                      'assertionIds': mapped[case_id]['assertionIds'],
                      'assertionSites': {site: site for site in mapped[case_id]['assertionIds']},
                      'loopSamples': {}} for case_id, items in grouped.items()}


def freeze(args):
    catalog, mapping, _, mapped, grouped = samples(args)
    plan = plan_for(mapped, grouped)
    audit.validate_plan(catalog, mapping, plan)
    directory = Path(args.directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (('catalog.json', catalog), ('mapping.json', mapping), ('input-plan.json', plan)):
        (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'file': SOURCE, 'cases': len(plan),
                      'samples': sum(len(value['sampleIds']) for value in plan.values()),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values())},
                     ensure_ascii=False))


def emit_ts(args):
    _, _, _, _, grouped = samples(args)
    plan = read(args.plan)
    require(set(plan) == set(grouped), '本轮用例集合与冻结计划不同')
    output = []
    for case_id, items in grouped.items():
        require([sample['sampleId'] for sample in items] == plan[case_id]['sampleIds'],
                '本轮样本编号与冻结计划不同：' + case_id)
        output.extend({'runId': os.environ['EVIDENCE_RUN_ID'], 'side': 'ts', 'caseId': case_id,
                       'sampleId': sample['sampleId'], 'value': sample['value']} for sample in items)
    Path(args.output).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in output))
    print(json.dumps({'side': 'ts', 'cases': len(grouped), 'samples': len(output)}, ensure_ascii=False))


if __name__ == '__main__':
    spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('freeze', 'emit-ts'):
        command = sub.add_parser(name)
        command.add_argument('--raw', type=Path, required=True)
        if name == 'freeze':
            command.add_argument('--directory', type=Path, required=True)
        else:
            command.add_argument('--plan', type=Path, required=True)
            command.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    (freeze if options.mode == 'freeze' else emit_ts)(options)
