#!/usr/bin/env python3
"""只读盘点：每个 implementation-slice 的冻结用例、已计划用例与当前来源复核情况。

用法：
    python3 item-readiness.py [--status not-started,in-progress] [--preflight <preflight.json>]

计划覆盖来自 `full-evidence-locals.json` 各局部的 input-plan；当前来源复核优先读最近一次
`full-evidence-preflight.py` 结果（--preflight，缺省取 .cache/evidence 下最新的 full-preflight-*.json）。
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def latest_preflight():
    candidates = sorted((TASK / '.cache/evidence').glob('full-preflight-*.json'),
                        key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status', default='not-started,in-progress')
    parser.add_argument('--preflight', type=Path)
    options = parser.parse_args()
    wanted = {value.strip() for value in options.status.split(',') if value.strip()}

    state = read(TASK / 'feature_list.json')
    catalog = read(TASK / 'module-tests.json')
    cases = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    file_cases = defaultdict(set)
    for case_id, path in cases.items():
        file_cases[path].add(case_id)

    config = read(TASK / 'full-evidence-locals.json')
    planned_by = defaultdict(set)
    for local in config['locals']:
        plan = Path(local['input_plan'])
        if not plan.exists():
            continue
        for case_id in read(plan):
            planned_by[case_id].add(local['name'])
    verified = set()
    preflight = options.preflight or latest_preflight()
    if preflight and preflight.exists():
        for local in read(preflight)['locals']:
            if local.get('currentCaptureVerified'):
                plan = Path(next((item['input_plan'] for item in config['locals']
                                  if item['name'] == local['name']), ''))
                if plan.exists():
                    verified |= set(read(plan))

    print(f"preflight: {preflight.name if preflight else '（无）'} | 冻结用例 {len(cases)} | "
          f"已计划 {len(planned_by)} | 当前来源复核 {len(verified)}")
    for item in state['features']:
        if item.get('kind') != 'implementation-slice' or item['status'] not in wanted:
            continue
        files = item.get('testFiles', [])
        total = sum(len(file_cases[path]) for path in files)
        planned = sum(len(file_cases[path] & set(planned_by)) for path in files)
        current = sum(len(file_cases[path] & verified) for path in files)
        gaps = [f"{path.split('/')[-1]}({len(file_cases[path] - set(planned_by))})"
                for path in files if file_cases[path] - set(planned_by)]
        print(f"{item['status']:12} {item['id']:38} 用例 {total:4} | 已计划 {planned:4} | 当前来源 {current:4}"
              + (f" | 缺计划：{', '.join(gaps)}" if gaps else ''))


if __name__ == '__main__':
    main()
