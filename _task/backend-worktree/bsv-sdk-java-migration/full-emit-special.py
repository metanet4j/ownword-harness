#!/usr/bin/env python3
"""特殊旧局部的本轮转换器：逐局部复用适配器里的转换函数（不导入适配器本身，避免其 main 副作用）。

目前只有 ValidationHelpers：两侧的输入行与断言行都由 replay-validation-helpers.py 提供，
适配器只是把它们写进 EVIDENCE_* 路径。
"""
import importlib.util
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_rows(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                                  for row in rows))


def emit_validation_helpers(options):
    replay = load_module(TASK / 'replay-validation-helpers.py', 'full_emit_validation_helpers')
    _, file, mapping = replay.source()
    plan = replay.read(options.plan)
    inputs = replay.input_rows(replay.rows(options.raw), file, mapping, plan)
    rows = [{'runId': options.run_id, 'side': 'ts', 'caseId': row['caseId'],
             'sampleId': row['sampleId'], 'value': row['value']} for row in inputs]
    write_rows(options.output, rows)
    print(json.dumps({'side': 'ts', 'local': options.local, 'inputs': len(rows)}, ensure_ascii=False))


def run(options):
    variant = options.variant or options.local
    if variant == 'validation-helpers':
        emit_validation_helpers(options)
    else:
        raise SystemExit('full-emit-special 不支持的变体：' + variant)
