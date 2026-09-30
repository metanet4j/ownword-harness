#!/usr/bin/env python3
"""旧管线局部的本轮转换器（全量运行专用，只读冻结语料，不改任何既有适配器）。

全量运行把 133 个原文件塞进同一次 Jest 运行，旧管线局部（探针自己记录原断言、或要按局部
冻结计划目录解析用例）不能照搬逐局部采集的适配器入口，因此这里提供统一的转换入口：

    python3 full-emit.py --mode replay|prepare|inline --module <既有脚本> --local <局部> \
        --run-dir <本轮目录> --plan <局部冻结计划／语料> --raw <本轮原始轨迹> \
        [--parity <共享断言轨迹>] --output <输入行输出> [--assertions <断言行输出>] \
        [--variant <变体>] [--argv-tail <JSON>] [--outputs <JSON>]

mode：
    replay   导入既有模块并调用它的 emit_ts／emit（参数按 emit_ts 签名逐个解析：
             raw／parity／plan／inputs／assertions／run-id／side，其余形参按名从 --outputs
             的探针输出环境变量里反查，例如 frames／entropy／clock／meta）；
    prepare  调用 prepare-*.py 的 emit-ts 子命令，参数由 --argv-tail 给出（占位已替换）；
    inline   委托 full-emit-inline.py 处理内联折算（BigNumber／DRBG／Point／Mnemonic／向量）。

既有模块只被导入、不执行 main；两侧共用同一运行目录的约定不变。
"""
import argparse
import importlib.util
import inspect
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def write_rows(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=False, sort_keys=True) + '\n'
                                  for row in rows))


def outputs_by_name(raw_outputs):
    """探针输出环境变量 → 形参名：MIGRATION_WALLET_WIRE_TS_FRAMES → frames／ts_frames／…"""
    table = {}
    for env, path in (raw_outputs or {}).items():
        stem = env.removeprefix('MIGRATION_').lower()
        parts = stem.split('_')
        for start in range(len(parts)):
            table.setdefault('_'.join(parts[start:]), path)
    return table


def build_options(argv):
    named = outputs_by_name(json.loads(argv.outputs or '{}'))
    plan_path = Path(argv.plan)
    options = SimpleNamespace(
        run_id=os.environ['EVIDENCE_RUN_ID'], side='ts', local=argv.local, task=TASK,
        run_dir=Path(argv.run_dir), variant=argv.variant or argv.local,
        raw=Path(argv.raw), parity=Path(argv.parity) if argv.parity else None,
        plan=plan_path, replay=plan_path,
        plan_json=json.loads(plan_path.read_text()) if plan_path.is_file()
        and plan_path.suffix == '.json' else {},
        replay_rows=read_rows(plan_path) if plan_path.is_file()
        and plan_path.suffix == '.jsonl' else [],
        inputs=Path(argv.output), output=Path(argv.output),
        assertions=Path(argv.assertions) if argv.assertions else None)
    # 其余形参（frames／entropy／clock／meta…）按名字从探针输出反查。
    for name, path in named.items():
        if not hasattr(options, name):
            setattr(options, name, Path(path))
    return options


def call_emit(module, options):
    """按 emit_ts／emit 的形参名逐个取用；缺参数时给出明确报错。"""
    function = getattr(module, 'emit_ts', None) or getattr(module, 'emit', None)
    if function is None:
        raise SystemExit('模块没有 emit_ts／emit：' + str(getattr(module, '__file__', module)))
    parameters = list(inspect.signature(function).parameters)
    # `def emit(args)` / `def emit(options)`：单形参且不是可解析字段名 → 直接传整个参数对象。
    if len(parameters) == 1 and not hasattr(options, parameters[0]):
        return function(options)
    if not parameters:
        return function(options)
    missing = [name for name in parameters if getattr(options, name, None) is None]
    if missing:
        raise SystemExit('emit_ts 需要但本轮没有提供的参数：' + ','.join(missing))
    return function(**{name: getattr(options, name) for name in parameters})


def emit_replay(argv):
    module_path = TASK / argv.module
    module = load_module(module_path, 'full_emit_' + module_path.stem.replace('-', '_'))
    call_emit(module, build_options(argv))


def emit_prepare(argv):
    tail = [part.replace('{runDir}', argv.run_dir).replace('{local}', argv.local)
            .replace('{output}', argv.output).replace('{assertions}', argv.assertions or '')
            .replace('{raw}', argv.raw).replace('{parity}', argv.parity or '')
            .replace('{plan}', argv.plan).replace('{replay}', argv.plan)
            .replace('{planDir}', str(Path(argv.run_dir) / 'plans' / argv.local))
            for part in json.loads(argv.argv_tail or '[]')]
    command = [sys.executable, str(TASK / argv.module), 'emit-ts', *tail]
    result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit('prepare emit-ts 失败：' + (result.stderr or result.stdout)[-2000:])
    print(result.stdout.strip())


def emit_inline(argv):
    module = load_module(TASK / 'full-emit-inline.py', 'full_emit_inline')
    module.run(build_options(argv))


def emit_special(argv):
    module = load_module(TASK / 'full-emit-special.py', 'full_emit_special')
    module.run(build_options(argv))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=('replay', 'prepare', 'inline', 'special'), required=True)
    parser.add_argument('--module', required=True)
    parser.add_argument('--local', required=True)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--raw', required=True)
    parser.add_argument('--parity')
    parser.add_argument('--output', required=True)
    parser.add_argument('--assertions')
    parser.add_argument('--variant')
    parser.add_argument('--argv-tail', default='[]')
    parser.add_argument('--outputs', default='{}')
    args = parser.parse_args()
    {'replay': emit_replay, 'prepare': emit_prepare, 'inline': emit_inline,
     'special': emit_special}[args.mode](args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
