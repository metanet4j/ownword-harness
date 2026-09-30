#!/usr/bin/env python3
"""hex-bn 旧管线的 CLI 转换入口：把本轮 TS 原始轨迹转成标准输入与断言行。

旧适配器 `capture-legacy-side.py` 直接调用 `replay-legacy-inputs.emit_ts`，全量运行
无法复用；这里提供同一实现的 CLI 形态（供 `run-full-ts-capture.py` 与适配器共同调用）。
"""
import argparse
import importlib.util
import os
from pathlib import Path
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent


def legacy():
    spec = importlib.util.spec_from_file_location('replay_legacy_inputs', TASK / 'replay-legacy-inputs.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    emit = sub.add_parser('emit-ts')
    emit.add_argument('--kind', choices=('hex', 'bn', 'both'), required=True)
    emit.add_argument('--raw', type=Path)
    emit.add_argument('--raw-hex', type=Path)
    emit.add_argument('--raw-bn', type=Path)
    emit.add_argument('--plan', type=Path, required=True)
    emit.add_argument('--inputs', type=Path, required=True)
    emit.add_argument('--assertions', type=Path, required=True)
    emit.add_argument('--run-id', help='缺省时取环境变量 EVIDENCE_RUN_ID（全量运行的分派表只替换 runDir/local/output）')
    emit.add_argument('--side', default='ts')
    options = parser.parse_args()
    if not options.run_id:
        options.run_id = os.environ.get('EVIDENCE_RUN_ID')
    if not options.run_id:
        parser.error('缺少本轮运行身份：请传 --run-id 或设置 EVIDENCE_RUN_ID')
    legacy().emit_ts(SimpleNamespace(kind=options.kind, raw=options.raw, raw_hex=options.raw_hex,
        raw_bn=options.raw_bn, plan=options.plan, run_id=options.run_id, side=options.side,
        inputs=options.inputs, assertions=options.assertions))


if __name__ == '__main__':
    main()
