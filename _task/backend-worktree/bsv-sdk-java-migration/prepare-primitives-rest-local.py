#!/usr/bin/env python3
"""primitives 剩余局部的清单/映射/样本编号：冻结与把本轮探针轨迹转成 TS 输入。

与 prepare-transaction-local.py 同一套逻辑，只有两处差别：

1. 登记表换成 primitives-rest-locals.py；
2. 本轮原文件里有 audit-tests.py 已固定的语义规则站点（Random／Random.additional／
   AsyncCryptoBackend），这些站点的随机字节、长度和 undefined/null 观测只能按原断言
   语义比较，因此把 audit-tests.py 的固定规则写进计划的 `comparisonRules`，
   不新增任何规则。

样本编号按探针记录的入口顺序生成（`<入口>-<序号>`）；样本值只保留可比对的
`method/args/result`，源码行号留在探针原始轨迹里。值由标准双侧采集当场比较，
不复制一份语料。"""
import argparse
import importlib.util
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('primitives_rest_locals', TASK / 'primitives-rest-locals.py')
locals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locals_module)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(',', ':'), allow_nan=False)


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


def assertion_rows(entry, raw, identities):
    """本轮每个用例实际执行的断言轨迹；辅助函数与循环会让同一站点执行多次。"""
    grouped = defaultdict(list)
    for row in rows(raw):
        require(row['file'].endswith(entry['file']), '固定断言来自其他文件：' + str(row.get('file')))
        grouped[(row['test'], row['occurrence'])].append(row)
    return {case_id: grouped[key] for case_id, key in identities.items()}


def uniform_instances(count, site_ids):
    """原测试的循环结构：每轮依次执行全部站点；执行次数必须整除站点数。"""
    if count % len(site_ids):
        return None
    instances, sites = [], {}
    for round_index in range(1, count // len(site_ids) + 1):
        for site in site_ids:
            identity = site if round_index == 1 else f'{site}#{round_index}'
            instances.append(identity)
            sites[identity] = site
    return instances, sites


def run_instances(observed, site_ids):
    """按观测签名（matcher + 期望值）分组：同一站点连续执行多次时分组数与站点数相同。"""
    runs = []
    for row in observed:
        signature = (row.get('matcher'), canonical(row.get('expected')))
        if runs and runs[-1][0] == signature:
            runs[-1][1] += 1
        else:
            runs.append([signature, 1])
    if len(runs) != len(site_ids):
        return None
    instances, sites = [], {}
    for site, (_, count) in zip(site_ids, runs):
        for round_index in range(1, count + 1):
            identity = site if round_index == 1 else f'{site}#{round_index}'
            instances.append(identity)
            sites[identity] = site
    return instances, sites


def guarded_instances(observed, site_ids, fixed):
    """按固定语义规则逐行归属：用规则给出的原 matcher 与固定边界识别每一行属于哪个站点。

    随机字节、长度这类站点的原断言在循环里是交错的（同一字节先断言下界再断言上界），
    既不是“每轮全部站点”，也不是“同一站点连续执行”，只能按规则识别。
    """
    if not fixed or any(site not in fixed for site in site_ids):
        return None
    signatures = {site: (fixed[site][1], canonical({'type': 'number', 'value': str(fixed[site][2])}))
                  for site in site_ids}
    counts = dict.fromkeys(site_ids, 0)
    instances, sites = [], {}
    for row in observed:
        matched = [site for site in site_ids
                   if signatures[site] == (row.get('matcher'), canonical(row.get('expected')))
                   and counts[site] < fixed[site][3]]
        if len(matched) != 1:
            return None
        site = matched[0]
        counts[site] += 1
        identity = site if counts[site] == 1 else f'{site}#{counts[site]}'
        instances.append(identity)
        sites[identity] = site
    if any(counts[site] != fixed[site][3] for site in site_ids):
        return None
    return instances, sites


def semantic_fit(sites, fixed):
    """固定语义规则要求站点执行次数精确；等次数与观测分组都可能满足，按次数判优。"""
    counts = Counter(sites.values())
    return all(counts[site] == rule[3] for site, rule in fixed.items())


def plan_for(mapped, grouped, observed, loops, rules_for=None):
    plan = {}
    for case_id, items in grouped.items():
        site_ids = mapped[case_id]['assertionIds']
        rows_for_case = observed[case_id]
        count = len(rows_for_case)
        fixed = (rules_for or {}).get(case_id, {})
        # 先按原测试的循环结构（每轮执行全部站点）归属；不整除或与固定语义次数不符时，
        # 再按本轮实际观测签名分组，避免把连续执行多次的站点摊到别的站点上。
        candidates = [candidate for candidate in (uniform_instances(count, site_ids),
                                                  run_instances(rows_for_case, site_ids),
                                                  guarded_instances(rows_for_case, site_ids, fixed))
                      if candidate]
        require(bool(candidates), f'断言执行次数无法归属到冻结站点：{case_id}／{count}／{len(site_ids)}')
        chosen = next((candidate for candidate in candidates if semantic_fit(candidate[1], fixed)), None)
        require(chosen is not None,
                f'断言执行次数与固定语义规则不符，需人工登记：{case_id}／{count}／{len(site_ids)}')
        instances, sites = chosen
        # 循环站点只做结构覆盖：原测试的循环在辅助函数或 hooks 中执行时没有逐用例样本，
        # 统一按该用例实际采集到的入口样本登记（与 bn-arithmetic 的登记方式一致）。
        plan[case_id] = {'sampleIds': [sample['sampleId'] for sample in items],
                         'assertionIds': instances, 'assertionSites': sites,
                         'loopSamples': {site: [sample['sampleId'] for sample in items]
                                         for site in loops}}
        if fixed:
            # 只登记 audit-tests.py 已固定的规则站点；其余站点的比较规则保持缺省。
            plan[case_id]['comparisonRules'] = {
                identity: fixed[site][0] for identity, site in sites.items() if site in fixed}
    return plan


def freeze(options):
    entry = locals_module.local(options.local)
    catalog, mapping, mapped, grouped, identities = samples(entry, options.raw)
    loops = {site['id'] for file in catalog['files'] for site in file['sites'] if site['kind'] == 'loop'}
    rules_for = {case_id: {entry[0] + ':' + position + ':assertion': rule
                           for position, rule in entry[2].items()}
                 for case_id, entry in audit.SEMANTIC_CASES.items()}
    plan = plan_for(mapped, grouped, assertion_rows(entry, options.assertions, identities), loops, rules_for)
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
