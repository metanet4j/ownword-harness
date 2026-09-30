#!/usr/bin/env python3
"""把 auth-certificates 某个局部的固定清单、映射与计划写入计划目录。"""
import argparse
import importlib.util
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('certificate_locals', TASK / 'certificate-locals.py')
locals_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(locals_module)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', required=True)
    parser.add_argument('--directory', type=Path, required=True)
    options = parser.parse_args()
    entry, catalog, mapping, plan = locals_module.fragment(options.local)
    options.directory.mkdir(parents=True, exist_ok=True)
    for name, value in (('catalog.json', catalog), ('mapping.json', mapping), ('input-plan.json', plan)):
        (options.directory / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'local': options.local, 'file': entry['file'], 'cases': len(plan),
                      'samples': sum(len(value['sampleIds']) for value in plan.values()),
                      'assertions': sum(len(value['assertionIds']) for value in plan.values())}, ensure_ascii=False))
