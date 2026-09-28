#!/usr/bin/env python3
"""在当前 Java 版本与当前采集执行器下重采一个标准双侧局部，并按需更新登记路径。

用法：
    python3 recapture-local.py --name json-byte-encoding --run .cache/evidence/json-byte-formal-20260929
    python3 recapture-local.py --name json-byte-encoding --run <新目录> --update

每个新运行目录只能执行一次（evidence-bundle capture 拒绝已有产物）；
--update 只在该局部通过汇总与来源校验后改写 full-evidence-locals.json。
"""
import argparse
import json
import subprocess
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'


def read(path):
    return json.loads(Path(path).read_text())


def local(name):
    for item in read(CONFIG)['locals']:
        if item['name'] == name:
            if item.get('captureKind') == 'specialized-local' or 'catalog' not in item:
                raise ValueError(f'{name} 不是标准双侧采集局部')
            return item
    raise ValueError('未登记局部：' + name)


def run(command):
    result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f'命令失败：{" ".join(str(part) for part in command)}\n'
                         + (result.stderr or result.stdout).strip()[-600:])
    return result.stdout.strip()


def plan_replay(item):
    """清单、映射与重放语料都在登记给出的计划目录里；不按 input_plan 的父目录猜。"""
    catalog, mapping = Path(item['catalog']), Path(item['mapping'])
    folder = catalog.parent
    if 'replay' in item:
        replay = Path(item['replay'])
    else:
        options = [folder / name for name in ('replay-inputs.jsonl', 'replay.jsonl')
                   if (folder / name).exists()]
        if len(options) != 1:
            raise ValueError(f'{item["name"]} 的重放语料不唯一，请在登记里写 replay')
        replay = options[0]
    for path in (catalog, mapping, replay):
        if not path.exists():
            raise ValueError('登记路径不存在：' + str(path))
    return catalog, mapping, replay


def capture(name, item, side, run):
    plan = Path(item['input_plan'])
    catalog, mapping, replay = plan_replay(item)
    script = item['capture']
    report = run / ('ts-jest.json' if side == 'ts' else 'java-surefire.xml')
    command = ['python3', str(TASK / 'evidence-bundle.py'), 'capture', '--side', side,
               '--catalog', str(catalog), '--mapping', str(mapping),
               '--input-plan', str(plan), '--inputs', str(run / f'{side}-inputs.jsonl'),
               '--assertions', str(run / f'{side}-assertions.jsonl'),
               '--output', str(run / f'{side}-run.json'), '--report', str(report), '--',
               'python3', str(TASK / script), side]
    if side == 'java':
        command += ['clean', 'test']
    command += ['--replay', str(replay), '--report', str(report)]
    return run_and_report(command)


def run_and_report(command):
    result = run(command)
    print(result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--update', action='store_true')
    options = parser.parse_args()
    item = local(options.name)
    run_dir = options.run.resolve()
    if run_dir.exists() and any(run_dir.iterdir()):
        raise ValueError('运行目录必须为空：' + str(run_dir))
    run_dir.mkdir(parents=True, exist_ok=True)
    plan = Path(item['input_plan'])
    capture(options.name, item, 'ts', run_dir)
    capture(options.name, item, 'java', run_dir)
    catalog, mapping, _ = plan_replay(item)
    print(run(['python3', str(TASK / 'evidence-bundle.py'),
               '--catalog', str(catalog), '--mapping', str(mapping),
               '--input-plan', str(plan),
               '--ts-inputs', str(run_dir / 'ts-inputs.jsonl'), '--java-inputs', str(run_dir / 'java-inputs.jsonl'),
               '--ts-assertions', str(run_dir / 'ts-assertions.jsonl'),
               '--java-assertions', str(run_dir / 'java-assertions.jsonl'),
               '--output', str(run_dir / 'parity.json'),
               '--ts-run-manifest', str(run_dir / 'ts-run.json'),
               '--java-run-manifest', str(run_dir / 'java-run.json'),
               '--ts-report', str(run_dir / 'ts-jest.json'),
               '--java-report', str(run_dir / 'java-surefire.xml')]))
    if options.update:
        relative = run_dir.relative_to(TASK).as_posix()
        data = read(CONFIG)
        for entry in data['locals']:
            if entry['name'] != options.name:
                continue
            entry.update({
                'ts_inputs': f'{relative}/ts-inputs.jsonl',
                'ts_assertions': f'{relative}/ts-assertions.jsonl',
                'ts_run_manifest': f'{relative}/ts-run.json',
                'ts_report': [f'{relative}/ts-jest.json'],
                'java_inputs': f'{relative}/java-inputs.jsonl',
                'java_assertions': f'{relative}/java-assertions.jsonl',
                'java_run_manifest': f'{relative}/java-run.json',
                'java_report': [f'{relative}/java-surefire.xml'],
            })
        Path(CONFIG).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'updated': options.name, 'run': relative}, ensure_ascii=False))
    print(run(['python3', str(TASK / 'local-evidence-gate.py'), 'verify', '--name', options.name]))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as error:
        raise SystemExit(str(error))
