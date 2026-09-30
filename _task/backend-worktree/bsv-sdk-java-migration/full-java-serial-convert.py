#!/usr/bin/env python3
"""A2 raw-convert 局部的 Maven 后置转换：原始调用轨迹 → 标准输入行（追加进 java-inputs.jsonl）。

`java-serial-entries.json` 里 `shape = raw-convert` 的局部，Java 侧不直接写标准行，而是把
**该次运行真实消费到的原始调用**写到各自入口（`-Dmigration.*` / 自有 env）；必须再由当年跑通的
那个 Python 转换函数映射成 `{runId, side, caseId, sampleId, value}` 才算最终行。本脚本只做这一步，
转换逻辑**直接 import 当年那个模块**，不重新实现：

  * validation-helpers（147 例）：`replay-validation-helpers.py::input_rows()`，计划取该局部冻结的
    `--plan` 目录（147 例逐样本 sampleId 与全量 input-plan 逐字段相同）；
  * auth-fetch-property（1 例 × 300 样本）、utils-property（3 例）：各自适配器里的 `emit()`，
    它原本的数量与顺序校验（300 / 600+76+976）原样生效。

`emit()` 还要读本类的原始断言轨迹：全量运行的原始断言轨迹是**一份**全局文件
（`<runDir>/java-assertions.raw.jsonl`），这里按 `test` 前缀筛出本类的行当作该类的轨迹——
不是新造数据，而是同一轮运行轨迹的子集（筛选后的行数由 `emit()` 自行校验）。

用法：
    python3 full-java-serial-convert.py --run-dir <runDir> [--report <路径>]
"""
import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
ENTRIES = TASK / 'java-serial-entries.json'
PROJECT = TASK / 'metanet4j-bsv-sdk'
SUREFIRE = PROJECT / 'target/surefire-reports'
# emit() 需要的测试类（与冻结 SDK 测试源码里的常量一致；数量不符时 emit 会自己报错）。
EMIT_CLASSES = {'auth-fetch-property': 'com.metanet4j.bsv.auth.clients.AuthFetchPropertyTest',
                'utils-property': 'com.metanet4j.bsv.primitives.UtilsPropertyTest'}
EMIT_MODULES = {'auth-fetch-property': 'capture-auth-fetch-property-side.py',
                'utils-property': 'capture-utils-property-side.py'}


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(path, values):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n'
                                  for value in values))


def load_module(name, script):
    spec = importlib.util.spec_from_file_location(name, TASK / script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def options_of(command):
    result = {}
    for index, part in enumerate(command):
        if part.startswith('--') and index + 1 < len(command) and not command[index + 1].startswith('--'):
            result[part] = command[index + 1]
    return result


def resolve(value, run_dir):
    return Path(value.replace('{runDir}', str(run_dir)))


def surefire(class_name):
    matches = sorted(SUREFIRE.glob('TEST-*' + class_name.rsplit('.', 1)[-1] + '.xml'))
    if len(matches) != 1:
        raise ValueError(f'找不到唯一的 Surefire 报告：{class_name} → {matches}')
    return matches[0]


def convert_validation_helpers(entry, run_dir, run_id):
    replay = load_module('replay_validation_helpers', 'replay-validation-helpers.py')
    catalog, file, mapping = replay.source()
    options = options_of(entry['captureCommand'])
    plan = read(Path(options['--plan']) / 'input-plan.json')
    raw_calls = resolve(entry['properties']['migration.validation.input.output']['value'], run_dir)
    if not raw_calls.is_file():
        raise ValueError('缺少 ValidationHelpers 原始调用轨迹：' + str(raw_calls))
    inputs = replay.input_rows(replay.rows(raw_calls), file, mapping, plan)
    return [{'runId': run_id, 'side': 'java', 'caseId': row['caseId'],
             'sampleId': row['sampleId'], 'value': row['value']} for row in inputs]


def convert_via_emit(local, entry, run_dir, run_id):
    adapter = load_module('convert_' + local.replace('-', '_'), EMIT_MODULES[local])
    class_name = EMIT_CLASSES[local]
    options = options_of(entry['captureCommand'])
    raw = run_dir / 'java-serial' / local
    raw.mkdir(parents=True, exist_ok=True)
    every = rows(run_dir / 'java-assertions.raw.jsonl')
    selected = [row for row in every if str(row.get('test', '')).startswith(class_name + '#')]
    write_rows(raw / 'assertions.jsonl', selected)
    staging = run_dir / 'java-serial' / local / 'emit-staging'
    staging.mkdir(parents=True, exist_ok=True)
    arguments = SimpleNamespace(side='java', run_id=run_id, plan=options.get('--plan'),
                                catalog=options.get('--catalog'), corpus=options.get('--corpus'),
                                report=str(surefire(class_name)), raw_dir=str(raw))
    previous = {key: os.environ.get(key) for key in ('EVIDENCE_INPUTS_PATH', 'EVIDENCE_ASSERTIONS_PATH')}
    os.environ['EVIDENCE_INPUTS_PATH'] = str(staging / 'inputs.jsonl')
    os.environ['EVIDENCE_ASSERTIONS_PATH'] = str(staging / 'assertions.jsonl')
    try:
        adapter.emit(arguments, raw)
        return rows(staging / 'inputs.jsonl')
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def append(run_dir, produced, existing):
    inputs = run_dir / 'java-inputs.jsonl'
    with inputs.open('a') as stream:
        for row in produced:
            key = (row['caseId'], row['sampleId'])
            if key in existing:
                raise ValueError(f'转换结果与既有 Java 输入重复：{key[0]}/{key[1]}')
            existing.add(key)
            stream.write(json.dumps(row, ensure_ascii=False) + '\n')
    return len(produced)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--entries', type=Path, default=ENTRIES)
    parser.add_argument('--run-id')
    parser.add_argument('--report', type=Path)
    parser.add_argument('--local', action='append', default=[],
                        help='只转换指定局部（聚焦验证用）；缺省处理全部 raw-convert 局部')
    options = parser.parse_args()
    run_dir = options.run_dir.resolve()
    table = read(options.entries)
    run_id = options.run_id or os.environ.get('EVIDENCE_RUN_ID')
    if not run_id:
        raise SystemExit('缺少本轮运行身份（--run-id 或 EVIDENCE_RUN_ID）')
    results, problems = {}, []
    existing = set()
    inputs = run_dir / 'java-inputs.jsonl'
    if inputs.is_file():
        existing = {(row['caseId'], row['sampleId']) for row in rows(inputs)}
    for local, entry in sorted(table['entries'].items()):
        if entry['shape'] != 'raw-convert':
            continue
        if options.local and local not in options.local:
            continue
        try:
            if local == 'validation-helpers':
                produced = convert_validation_helpers(entry, run_dir, run_id)
            else:
                produced = convert_via_emit(local, entry, run_dir, run_id)
            appended = append(run_dir, produced, existing)
            results[local] = {'cases': entry['cases'], 'rowsAppended': appended,
                              'distinctCases': len({row['caseId'] for row in produced})}
        except (ValueError, OSError, KeyError, AttributeError) as error:
            problems.append(f'{local} 转换失败：{type(error).__name__}: {error}')
    results['problems'] = problems
    if options.report:
        options.report.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(results, ensure_ascii=False))
    for problem in problems:
        print('JAVA-SERIAL-CONVERT-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
