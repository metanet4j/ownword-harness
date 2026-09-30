#!/usr/bin/env python3
"""把共享向量局部的 Java 原始输入轨迹归一化进本轮 `java-inputs.jsonl`（A1）。

背景：两个共享向量局部（`script-spend-shared-vectors` 1940 例、`transaction-shared-vectors`
659 例）的 Java 侧走的是**原始记录接口**——`support/VectorInputRecorder.java` 把每次调用写成
`{runId, side, test, input}` 追加到 `MIGRATION_VECTOR_JAVA_INPUTS`，必须再按各自 catalog/mapping
映射成 `{runId, side, caseId, sampleId, value}` 才算最终行。全量 Java 阶段此前两件事都没做，
所以这 2599 个用例的 Java 输入缺失（`evidence-bundle` 报「Java 输入用例缺失」）。

本脚本只做「原始轨迹 → 最终行」这一步，口径与 `script-vector-evidence.py` /
`transaction-vector-evidence.py` 的 `normalize()` **逐字段一致**（同样按 mapping 的 Java 注册
身份映射 caseId、按计划 `sampleIds` 顺序 zip 记录值、同样要求计数相符）。

用法（接线时由 run-full-java-capture.py 在 Maven 结束后调用）：
    python3 java-vector-inputs.py --run-dir <runDir> [--raw <runDir>/java-vector-inputs.raw.jsonl]
    # 追加写入 <runDir>/java-inputs.jsonl，并写 <runDir>/java-vector-inputs.json 摘要
"""
import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
VECTOR_LOCALS = ('script-spend-shared-vectors', 'transaction-shared-vectors')


def read(path):
    return json.loads(Path(path).read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def rows(path):
    result = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f'{path}:{number} 不是 JSON：{error}') from error
    return result


def family(local):
    """一个向量局部的计划、清单、映射与「Java 注册身份 → caseId」表。"""
    item = next(entry for entry in read(CONFIG)['locals'] if entry['name'] == local)
    folder = (TASK / item['input_plan']).parent
    catalog, mapping, plan = (read(folder / (name + '.json')) for name in ('catalog', 'mapping', 'input-plan'))
    by_test = {}
    for case in mapping['cases']:
        for java in case['java']:
            identity = java['className'] + '#' + java['name']
            require(identity not in by_test, 'Java 注册身份重复：' + identity)
            by_test[identity] = case['id']
    for case in mapping['cases']:
        require(case['id'] in plan, '计划缺少向量用例：' + case['id'])
    return {'local': local, 'folder': folder, 'catalog': catalog, 'mapping': mapping,
            'plan': plan, 'by_test': by_test}


def normalize(families, raw, run_id):
    """原始行按家族分组 → 计划顺序 zip 出最终行；返回 (最终行, 逐家族统计)。"""
    grouped = {family['local']: defaultdict(list) for family in families}
    owner = {}
    for family in families:
        for identity, case_id in family['by_test'].items():
            owner[identity] = family['local']
    unknown, foreign_side = 0, 0
    for row in rows(raw):
        if row.get('runId') != run_id or row.get('side') != 'java':
            foreign_side += 1
            continue
        local = owner.get(row.get('test'))
        if local is None:
            unknown += 1
            continue
        grouped[local][row['test']].append(row['input'])
    output, summary = [], {}
    for family in families:
        inputs = grouped[family['local']]
        plan = family['plan']
        by_case = defaultdict(list)
        for identity, values in inputs.items():
            by_case[family['by_test'][identity]].extend(values)
        missing, mismatch = [], []
        emitted = 0
        for case_id, expected in plan.items():
            values = by_case.get(case_id, [])
            if not values:
                missing.append(case_id)
                continue
            if len(values) != len(expected['sampleIds']):
                mismatch.append({'caseId': case_id, 'plan': len(expected['sampleIds']), 'recorded': len(values)})
                continue
            for sample_id, value in zip(expected['sampleIds'], values):
                output.append({'runId': run_id, 'side': 'java', 'caseId': case_id,
                               'sampleId': sample_id, 'value': value})
            emitted += 1
        summary[family['local']] = {'cases': len(plan), 'casesEmitted': emitted,
                                    'samplesEmitted': sum(len(v['sampleIds']) for v in plan.values())
                                    if not mismatch and not missing else None,
                                    'missingCases': missing[:5], 'missingCount': len(missing),
                                    'countMismatch': mismatch[:5]}
    return output, summary, {'unknownTests': unknown, 'foreignSideRows': foreign_side}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--raw', type=Path)
    parser.add_argument('--run-id')
    parser.add_argument('--inputs', type=Path, help='默认 <runDir>/java-inputs.jsonl')
    parser.add_argument('--report', type=Path, help='默认 <runDir>/java-vector-inputs.json')
    options = parser.parse_args()
    run_dir = options.run_dir.resolve()
    raw = (options.raw or run_dir / 'java-vector-inputs.raw.jsonl').resolve()
    inputs = (options.inputs or run_dir / 'java-inputs.jsonl').resolve()
    report = (options.report or run_dir / 'java-vector-inputs.json').resolve()
    run_id = options.run_id or os.environ.get('EVIDENCE_RUN_ID')
    require(bool(run_id), '缺少本轮运行身份（--run-id 或 EVIDENCE_RUN_ID）')
    if not raw.is_file() or not raw.stat().st_size:
        summary = {'raw': str(raw), 'skipped': '缺少向量原始输入轨迹（该轮没有运行向量测试）'}
        report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps(summary, ensure_ascii=False))
        return 0
    families = [family(local) for local in VECTOR_LOCALS]
    output, per_family, notes = normalize(families, raw, run_id)
    with inputs.open('a') as stream:
        for row in output:
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    problems = []
    for local, entry in per_family.items():
        if entry['missingCount']:
            problems.append(f'{local} 缺 {entry["missingCount"]} 个用例的 Java 输入')
        if entry['countMismatch']:
            problems.append(f'{local} 有 {len(entry["countMismatch"])} 个用例的记录条数与计划不符')
    if notes['foreignSideRows']:
        problems.append(f'原始轨迹里有 {notes["foreignSideRows"]} 行不属于本轮 runId/side=java')
    summary = {'runId': run_id, 'raw': str(raw), 'rawBytes': raw.stat().st_size,
               'inputs': str(inputs), 'rowsAppended': len(output),
               'families': per_family, 'unknownTests': notes['unknownTests'], 'problems': problems}
    report.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: summary[key] for key in ('rowsAppended', 'families', 'unknownTests')},
                     ensure_ascii=False))
    for problem in problems:
        print('JAVA-VECTOR-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
