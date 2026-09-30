#!/usr/bin/env python3
"""只读：对已登记局部的输入计划做结构校验（不受并行改源码影响）。

与 `full-evidence-preflight.py` 的区别：preflight 要求 Java 源码在校验期间不变，
并行采集时经常无法运行；本脚本只读计划/catalog/mapping，随时可用。

用法：
    python3 validate-plans.py [--name <局部>]…
"""
import argparse
import importlib.util
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', action='append', default=[])
    options = parser.parse_args()
    audit = load('audit_tests', TASK / 'audit-tests.py')
    config = json.loads((TASK / 'full-evidence-locals.json').read_text())
    selected = [item for item in config['locals']
                if not options.name or item['name'] in options.name]
    passed, failed, specialized = 0, [], []
    for local in selected:
        if 'catalog' not in local or 'mapping' not in local:
            specialized.append(local['name'])
            continue
        try:
            catalog = json.loads((TASK / local['catalog']).read_text())
            mapping = json.loads((TASK / local['mapping']).read_text())
            plan = json.loads((TASK / local['input_plan']).read_text())
            audit.validate_plan(catalog, mapping, plan)
            passed += 1
        except Exception as error:  # noqa: BLE001 - 报告全部失败原因
            failed.append((local['name'], str(error)[:160]))
    print(json.dumps({'checked': passed, 'failed': len(failed),
                      'specializedSkipped': len(specialized),
                      'failures': failed}, ensure_ascii=False))
    raise SystemExit(1 if failed else 0)


if __name__ == '__main__':
    main()
