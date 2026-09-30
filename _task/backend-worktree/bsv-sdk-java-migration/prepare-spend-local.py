#!/usr/bin/env python3
"""spend 批局部的清单/映射/样本编号：按 Java 类裁剪冻结条目，冻结并把本轮探针轨迹转成 TS 输入。

一个原文件可能被多个 Java 测试类覆盖（Spend.test.ts 的有效向量与 SpendCoreTest、
SpendValildVectors.test.ts 的 Chronicle 向量与 Standalone 向量），因此清单只保留
登记类名下的用例，并把站点裁剪到计划实际引用的范围。样本编号按探针记录的入口顺序
生成（`<入口>-<序号>`）；样本值只保留可比对的 `method/args/result`，源码行号留在
探针原始轨迹里。值由标准双侧采集当场比较，不复制一份语料。"""
import argparse
import importlib.util
import json
import os
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('spend_locals', TASK / 'spend-locals.py')
locals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locals_module)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def selection(entry):
    """本 Java 类名下的用例：原文件条目与全局映射都必须逐字保留。"""
    catalog_all = read(TASK / 'module-tests.json')
    source_all = next(file for file in catalog_all['files'] if file['path'] == entry['file'])
    mapping_all = read(TASK / 'test-map.json')
    mapped_all = {case['id']: case for case in mapping_all['cases']}
    selected = []
    for case in source_all['cases']:
        mapped = mapped_all[case['id']]
        if len(mapped['java']) == 1 and mapped['java'][0]['className'] == entry['java_class']:
            selected.append(case)
    require(selected, '登记类名没有对应冻结用例：' + entry['file'] + ' / ' + entry['java_class'])
    return catalog_all, source_all, mapping_all, selected


def fragment(entry, selected, plan=None):
    catalog_all, source_all, mapping_all, _ = selection(entry)
    ids = [case['id'] for case in selected]
    sites = set()
    referenced = set()
    if plan is not None:
        referenced.update(site for row in plan.values() for site in row['assertionSites'].values())
        referenced.update(site for row in plan.values() for site in row.get('loopSamples', {}))
        # 恒假哨兵同样是计划的一部分：证明本身引用这些站点，清单必须保留它们。
        referenced.update(site for row in plan.values() for site in row.get('unexecutedSites', {}))
        sites.update(referenced)
    # 只保留计划实际执行到或已登记的断言站点：原测试里存在永不执行的断言（如 try 中先抛错），
    # 它们没有对应 Java 断言实例；有豁免证明的按证明保留，无证明的纳入清单会破坏“冻结断言站点覆盖”。
    sites.update(review['id'] for review in mapping_all['siteReviews']
                 if review.get('caseIds') and set(review['caseIds']) <= set(ids)
                 and not (plan is not None and review['id'].endswith(':assertion')
                          and review['id'] not in referenced))
    file = {**source_all, 'cases': [case for case in source_all['cases'] if case['id'] in set(ids)],
            'sites': [site for site in source_all['sites'] if site['id'] in sites]}
    mapped_all = {case['id']: case for case in mapping_all['cases']}
    catalog = {**catalog_all, 'files': [file], 'partialImplementationOnly': True}
    mapping = {**mapping_all, 'cases': [mapped_all[identity] for identity in ids],
               'siteReviews': [review for review in mapping_all['siteReviews'] if review['id'] in sites]}
    return catalog, mapping


def samples(entry, raw):
    catalog_all, source_all, mapping_all, selected = selection(entry)
    cases = {case['id']: case for case in selected}
    by_identity = {(' '.join(case['names']), case['occurrence']): case for case in cases.values()}
    grouped = defaultdict(list)
    identities = {}
    seen = defaultdict(int)
    for row in rows(raw):
        require(row['source']['file'] == entry['file'], '入口输入来自其他文件')
        key = (row['test'], row['occurrence'])
        require(key in by_identity, '入口输入来自未登记用例：' + ' / '.join(str(part) for part in key))
        seen[key] += 1
        require(row['sequence'] == seen[key], '入口顺序不连续')
        case_id = by_identity[key]['id']
        identities[case_id] = key
        grouped[case_id].append({'sampleId': f"{row['method']}-{row['sequence']:02d}",
                                 'value': {'method': row['method'], 'args': row['args'], 'result': row['result']}})
    require(set(grouped) == set(cases), '固定 TS 原用例未全部触达公开入口：' + entry['file'])
    return cases, grouped, identities


def assertion_runs(entry, raw, identities):
    """本轮每个用例实际执行的断言次数；辅助函数与循环会让同一站点执行多次。"""
    counts = defaultdict(int)
    for row in rows(raw):
        require(row['file'].endswith(entry['file']), '固定断言来自其他文件：' + str(row.get('file')))
        counts[(row['test'], row['occurrence'])] += 1
    return {case_id: counts[key] for case_id, key in identities.items()}


def unreachable_exclusions(catalog_all, source_all, mapping_all, plan):
    """冻结源码里的恒假哨兵：按清点器同一条规则为每个站点生成豁免证明。

    站点必须本文件内、属于唯一计划的用例，且形态是 `try` 内紧跟一次调用之后的
    `expect(<字面量>).toBe(<逻辑反面>)`；样本取该用例的第一个冻结样本，
    逐样本的异常观测由清点器在采集汇总时核对（这里不推断运行结果）。"""
    sites = {site['id']: site for site in source_all['sites'] if site['kind'] == 'assertion'}
    executed = {site for row in plan.values() for site in row['assertionSites'].values()}
    owners = defaultdict(set)
    for review in mapping_all['siteReviews']:
        owners[review['id']].update(case_id for case_id in review['caseIds'] if case_id in plan)
    lines, exclusions = None, defaultdict(dict)
    for site_id in sorted(sites):
        if site_id in executed:
            continue
        cases = sorted(owners.get(site_id, set()))
        if len(cases) != 1:
            continue
        if lines is None:
            lines = audit.frozen_source_lines(catalog_all, source_all, 'spend 局部恒假哨兵源码不符')
        shape = audit.unreachable_guard_shape(source_all['path'], lines, sites[site_id], sites)
        if shape is None:
            continue
        exclusions[cases[0]][site_id] = {'ruleId': audit.UNREACHABLE_RULE,
                                         'guardSiteId': shape['guardSiteId'],
                                         'sampleId': plan[cases[0]]['sampleIds'][0]}
    return exclusions


def plan_for(entry, mapped, grouped, runs, loops):
    plan = {}
    for case_id, items in grouped.items():
        site_ids = mapped[case_id]['assertionIds']
        count = runs[case_id]
        require(count > 0, f'固定用例未执行任何断言：{case_id}')
        # 原测试的公共辅助函数会在同一用例内重复执行未单独归属的断言站点，
        # 因此按站点顺序循环登记实例：同一站点第 2 次执行起记为 `<站点>#<轮次>`，
        # assertionSites 仍指回原站点。
        instances, sites, used = [], {}, defaultdict(int)
        for position in range(count):
            site = site_ids[position % len(site_ids)]
            used[site] += 1
            identity = site if used[site] == 1 else f'{site}#{used[site]}'
            instances.append(identity)
            sites[identity] = site
        # 循环站点只做结构覆盖：按该用例实际采集到的入口样本登记（与 bn-arithmetic 一致）。
        plan[case_id] = {'sampleIds': [sample['sampleId'] for sample in items],
                         'assertionIds': instances, 'assertionSites': sites,
                         'loopSamples': {site: [sample['sampleId'] for sample in items]
                                         for site in loops}}
    return plan


def freeze(options):
    entry = locals_module.local(options.local)
    catalog_all, source_all, mapping_all, selected = selection(entry)
    mapped_all = {case['id']: case for case in mapping_all['cases']}
    mapped = {case['id']: mapped_all[case['id']] for case in selected}
    _, grouped, identities = samples(entry, options.raw)
    sites_all = source_all['sites']
    loops = {site['id'] for site in sites_all if site['kind'] == 'loop'}
    plan = plan_for(entry, mapped, grouped, assertion_runs(entry, options.assertions, identities), loops)
    for case_id, proofs in unreachable_exclusions(catalog_all, source_all, mapping_all, plan).items():
        require(bool(proofs), '恒假哨兵豁免不能为空：' + case_id)
        plan[case_id]['unexecutedSites'] = proofs
    catalog, mapping = fragment(entry, selected, plan)
    audit.validate_plan(catalog, mapping, plan)
    directory = Path(options.directory)
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (('catalog.json', catalog), ('mapping.json', mapping), ('input-plan.json', plan)):
        (directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'local': options.local, 'file': entry['file'], 'cases': len(plan),
                      'samples': sum(len(value['sampleIds']) for value in plan.values()),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values()),
                      'unexecuted': sum(len(value.get('unexecutedSites', {})) for value in plan.values())},
                     ensure_ascii=False))


def emit_ts(options):
    entry = locals_module.local(options.local)
    _, grouped, _ = samples(entry, options.raw)
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


def catalog_only(options):
    """冻结前先落一份带用例身份的清单，供探针按局部用例过滤（只有 cases 被读取）。"""
    entry = locals_module.local(options.local)
    catalog, mapping = fragment(entry, selection(entry)[3])
    directory = Path(options.directory)
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
    (directory / 'mapping.json').write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'local': options.local, 'file': entry['file'],
                      'cases': len(catalog['files'][0]['cases'])}, ensure_ascii=False))


if __name__ == '__main__':
    audit_spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    audit = importlib.util.module_from_spec(audit_spec)
    audit_spec.loader.exec_module(audit)
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    for name in ('freeze', 'emit-ts', 'catalog'):
        command = sub.add_parser(name)
        command.add_argument('--local', required=True)
        if name != 'catalog':
            command.add_argument('--raw', type=Path, required=True)
        if name == 'freeze':
            command.add_argument('--assertions', type=Path, required=True)
            command.add_argument('--directory', type=Path, required=True)
        elif name == 'catalog':
            command.add_argument('--directory', type=Path, required=True)
        else:
            command.add_argument('--plan', type=Path, required=True)
            command.add_argument('--output', type=Path, required=True)
    options = parser.parse_args()
    {'freeze': freeze, 'emit-ts': emit_ts, 'catalog': catalog_only}[options.mode](options)
