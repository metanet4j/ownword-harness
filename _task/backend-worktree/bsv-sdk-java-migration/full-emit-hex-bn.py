#!/usr/bin/env python3
"""hex-bn 旧局部的本轮转换器：把原轨迹的断言行号归位后再交给既有转换脚本。

背景：`BigNumber.constructor.test.ts` 里 `expect(() => …).toThrow()` 形态的断言，探针记录的
行号是回调体所在行（例如 141），而冻结清单里的断言站点是 `expect(` 所在行（139）。既有转换脚本
`prepare-hex-bn-inputs.py` 按站点行号反查身份，行号对不上就 StopIteration。这里只在**本轮内存
副本**上把行号归位到「同一文件里不大于它的最近断言站点行」，冻结语料与探针都不改。

用法（由 full-run-overrides.json 登记）：
    python3 full-emit-hex-bn.py --run-dir <本轮目录> --plan <冻结 replay> \
        --inputs <输入行输出> --assertions <断言行输出>
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILES = {'hex': 'src/primitives/__tests/hex.test.ts',
         'bn': 'src/primitives/__tests/BigNumber.constructor.test.ts'}
RAW = {'hex': 'hex.raw.jsonl', 'bn': 'bn.raw.jsonl'}


def sites(path):
    catalog = json.loads((TASK / 'module-tests.json').read_text())
    file = next(item for item in catalog['files'] if item['path'] == path)
    return sorted(site['line'] for site in file['sites'] if site['kind'] == 'assertion')


def align(source, target, lines):
    """行号归位：命中站点行原样保留，否则取不大于它的最近站点行。"""
    moved, kept = 0, 0
    with source.open() as stream, target.open('w') as output:
        for line in stream:
            if not line.strip():
                continue
            row = json.loads(line)
            if row['line'] not in lines:
                candidates = [value for value in lines if value <= row['line']]
                if not candidates:
                    raise SystemExit(f'原轨迹行号 {row["line"]} 之前没有断言站点：{source}')
                row['line'] = max(candidates)
                moved += 1
            else:
                kept += 1
            output.write(json.dumps(row, ensure_ascii=False) + '\n')
    return kept, moved


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', required=True)
    parser.add_argument('--plan', required=True)
    parser.add_argument('--inputs', required=True)
    parser.add_argument('--assertions', required=True)
    args = parser.parse_args()
    run_dir = Path(args.run_dir)
    folder = run_dir / 'hex-bn-aligned'
    folder.mkdir(parents=True, exist_ok=True)
    aligned = {}
    for kind, path in FILES.items():
        source = run_dir / RAW[kind]
        if not source.is_file():
            raise SystemExit('缺少原始轨迹：' + str(source))
        target = folder / RAW[kind]
        kept, moved = align(source, target, sites(path))
        aligned[kind] = {'kept': kept, 'moved': moved, 'path': str(target)}
    command = [sys.executable, str(TASK / 'prepare-hex-bn-inputs.py'), 'emit-ts', '--kind', 'both',
               '--raw-hex', aligned['hex']['path'], '--raw-bn', aligned['bn']['path'],
               '--plan', args.plan, '--inputs', args.inputs, '--assertions', args.assertions,
               '--side', 'ts']
    result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
    if result.returncode:
        raise SystemExit('hex-bn emit-ts 失败：' + (result.stderr or result.stdout)[-1500:])
    print(json.dumps({'side': 'ts', 'local': 'hex-bn', 'aligned': aligned,
                      'stdout': result.stdout.strip()[-200:]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
