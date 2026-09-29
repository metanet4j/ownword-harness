#!/usr/bin/env python3
"""登记或更新一个标准双侧局部；整体读改写都在 flock 内，供多代理并行使用。

用法：
    python3 register-local.py --name live-policy --catalog <catalog.json> --mapping <mapping.json> \
        --input-plan <input-plan.json> --capture <capture-*-side.py> [--replay <replay.jsonl>]
"""
import argparse
import fcntl
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
LOCK = TASK / '.cache/locals.lock'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--mapping', required=True)
    parser.add_argument('--input-plan', required=True)
    parser.add_argument('--capture', required=True)
    parser.add_argument('--replay')
    options = parser.parse_args()
    entry = {'name': options.name, 'catalog': options.catalog, 'mapping': options.mapping,
             'input_plan': options.input_plan, 'capture': options.capture}
    if options.replay:
        entry['replay'] = options.replay
    for key in ('catalog', 'mapping', 'input_plan', 'replay'):
        if key in entry:
            target = Path(entry[key]) if Path(entry[key]).is_absolute() else TASK / entry[key]
            if not target.exists():
                raise SystemExit(f'登记路径不存在：{entry[key]}')
    LOCK.parent.mkdir(parents=True, exist_ok=True)
    with open(LOCK, 'w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        data = json.loads(CONFIG.read_text())
        names = [item['name'] for item in data['locals']]
        if options.name in names:
            data['locals'] = [entry if item['name'] == options.name else item for item in data['locals']]
        else:
            data['locals'].append(entry)
        CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
        fcntl.flock(lock, fcntl.LOCK_UN)
    print(json.dumps({'registered': options.name, 'locals': len(data['locals'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
