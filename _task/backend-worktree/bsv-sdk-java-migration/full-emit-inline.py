#!/usr/bin/env python3
"""内联 emit：把探针的原始入口轨迹折算成本轮标准输入行（复刻各适配器 TS 分支的逻辑）。

调用方是 full-emit.py（--mode inline）与其登记在 full-run-overrides.json 里的 argv。
按 --variant 分派：

  point:<原文件>    三点局部共用 capture-point-additional-inputs.cjs，按 source.file 过滤本局部的入口；
  mnemonic:<原文件> 两个助记词局部共用 capture-mnemonic-inputs.cjs，同样按 source.file 过滤；
  drbg              DRBG 原入口轨迹（value 即计划中的输入值）；
  arithmetic|binary|serializers|utils
                    BigNumber 四变体：入口事件与冻结语料逐行核对后取 kind=call 的事件。
"""
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
BIGNUMBER_VARIANTS = ('arithmetic', 'binary', 'serializers', 'utils')


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                                  for row in rows))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def source_cases(source_file):
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    return next(file for file in catalog['files'] if file['path'] == source_file)


def emit_by_source_file(options, source_file, occurrence_key):
    """按原测试身份（文件 + 用例名 + occurrence）把原入口配对到计划样本。"""
    source = source_cases(source_file)
    by_identity = {(' '.join(case['names']), case['occurrence']): case['id'] for case in source['cases']}
    plan = options.plan_json
    grouped, leftovers = {}, {}
    for row in read_rows(options.raw):
        # 多个局部共用同一探针与同一轨迹文件（三点局部、两个助记词局部），本局部只认自己的行。
        if row['source']['file'] != source_file:
            continue
        key = (row['test'], row.get(occurrence_key, 1))
        case_id = by_identity.get(key)
        require(case_id is not None, f'{options.local}: 原入口身份未映射：{key}')
        require(case_id in plan, f'{options.local}: 原用例不在冻结计划内：{key}')
        grouped.setdefault(case_id, []).append(row)
        leftovers.setdefault(case_id, 0)
    result = []
    for case_id, expected in plan.items():
        items = grouped.get(case_id, [])
        require(len(items) == len(expected['sampleIds']),
                f'{options.local}: 原入口数与计划样本数不符（{case_id[:12]}…：{len(items)} vs '
                f'{len(expected["sampleIds"])}）')
        require([item['sequence'] for item in items] == list(range(1, len(items) + 1)),
                f'{options.local}: 原入口序号不连续（{case_id[:12]}…）')
        result.extend({'runId': options.run_id, 'side': 'ts', 'caseId': case_id,
                       'sampleId': sample_id, 'value': item}
                      for sample_id, item in zip(expected['sampleIds'], items))
    require(set(grouped) == set(plan),
            f'{options.local}: 计划外或缺失的原用例：{sorted(set(grouped) ^ set(plan))[:4]}')
    write_rows(options.output, result)
    print(json.dumps({'side': 'ts', 'local': options.local, 'inputs': len(result)}))


def emit_drbg(options):
    planned = read_rows(options.plan)
    observed = read_rows(options.raw)
    require(len(observed) == len(planned), '本轮 DRBG 原入口数与固定计划不同')
    result = []
    for actual, expected in zip(observed, planned):
        require(actual['value'] == expected['value'],
                '本轮真实 TS 入口与固定语料不同：' + str(actual['sequence']))
        result.append({'runId': options.run_id, 'side': 'ts', 'caseId': expected['caseId'],
                       'sampleId': expected['sampleId'], 'value': actual['value']})
    write_rows(options.output, result)
    print(json.dumps({'side': 'ts', 'local': options.local, 'inputs': len(result)}))


def emit_vector(options):
    """共享向量局部：原始行已带 caseId，按计划样本顺序折算输入（行内 input 即最终值）。"""
    plan = options.plan_json
    require(plan, f'{options.local}: 缺少局部冻结计划')
    grouped = {}
    for row in read_rows(options.raw):
        grouped.setdefault(row['caseId'], []).append(row)
    result = []
    for case_id, expected in plan.items():
        items = grouped.pop(case_id, [])
        require(len(items) == len(expected['sampleIds']),
                f'{options.local}: 原入口数与计划样本数不符（{case_id[:12]}…：{len(items)} vs '
                f'{len(expected["sampleIds"])}）')
        result.extend({'runId': options.run_id, 'side': 'ts', 'caseId': case_id,
                       'sampleId': sample_id, 'value': item['input']}
                      for sample_id, item in zip(expected['sampleIds'], items))
    require(not grouped, f'{options.local}: 计划外用例外：{sorted(grouped)[:4]}')
    write_rows(options.output, result)
    print(json.dumps({'side': 'ts', 'local': options.local, 'inputs': len(result)}))


def emit_bignumber(options):
    variant = options.variant
    require(variant in BIGNUMBER_VARIANTS, '未知 BigNumber 变体：' + str(variant))
    if not Path(options.plan).is_file() or Path(options.plan).suffix == '.json':
        # 没有冻结语料的变体（serializers）：按计划样本顺序与本轮真实入口逐一对齐。
        return emit_bignumber_planmap(options, variant)
    planned = read_rows(options.plan)
    observed = read_rows(options.raw)
    require(len(observed) == len(planned),
            f'{variant} 原入口/断言数与固定计划不同（{len(observed)} vs {len(planned)}）')
    result = []
    for actual, expected in zip(observed, planned):
        require(actual == expected['value'],
                f'{variant} 本轮真实 TS 输入/断言引用与固定语料不同：' + str(actual.get('sequence')))
        if actual['kind'] != 'call':
            continue
        value = {key: item for key, item in actual.items() if key != 'result'}
        result.append({'runId': options.run_id, 'side': 'ts', 'caseId': expected['caseId'],
                       'sampleId': expected['sampleId'], 'value': value})
    write_rows(options.output, result)
    print(json.dumps({'side': 'ts', 'local': options.local, 'variant': variant, 'inputs': len(result)}))


def emit_bignumber_planmap(options, variant):
    require(options.plan_json, f'{variant}: 缺少局部冻结计划')
    grouped = {}
    for row in read_rows(options.raw):
        key = (row['test'], row.get('occurrence', 1))
        grouped.setdefault(key, []).append(row)
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    source = next((file for file in catalog['files'] if 'BigNumber' in file['path']
                   and variant.rstrip('s') in file['path'].lower()), None)
    require(source is not None, f'{variant}: 原文件定位失败')
    identities = {}
    for case in source['cases']:
        identities[(' '.join(case['names']), case['occurrence'])] = case['id']
    result = []
    for case_id, expected in options.plan_json.items():
        rows = []
        for key, items in list(grouped.items()):
            if identities.get(key) != case_id:
                continue
            rows.extend([item for item in items if item.get('kind') == 'call'])
            grouped.pop(key)
        require(len(rows) == len(expected['sampleIds']),
                f'{variant}: 原入口数与计划样本数不符（{case_id[:12]}…：{len(rows)} vs '
                f'{len(expected["sampleIds"])}）')
        result.extend({'runId': options.run_id, 'side': 'ts', 'caseId': case_id,
                       'sampleId': sample_id,
                       'value': {k: v for k, v in item.items() if k != 'result'}}
                      for sample_id, item in zip(expected['sampleIds'], rows))
    write_rows(options.output, result)
    print(json.dumps({'side': 'ts', 'local': options.local, 'variant': variant,
                      'inputs': len(result), 'corpus': 'plan-order'}))


def run(options):
    variant = options.variant or options.local
    if variant.startswith('point:'):
        emit_by_source_file(options, variant.split(':', 1)[1], 'occurrence')
    elif variant.startswith('mnemonic:'):
        emit_by_source_file(options, variant.split(':', 1)[1], 'occurrence')
    elif variant == 'drbg':
        emit_drbg(options)
    elif variant in BIGNUMBER_VARIANTS:
        emit_bignumber(options)
    elif variant == 'vector':
        emit_vector(options)
    else:
        raise SystemExit('full-emit-inline 不支持的变体：' + variant)
