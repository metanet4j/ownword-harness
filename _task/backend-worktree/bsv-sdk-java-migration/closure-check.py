#!/usr/bin/env python3
"""只读结项检查：逐事项核对冻结用例、计划覆盖、当前来源复核与 taskAcceptance 字段。

用法：
    python3 closure-check.py [--item ID]… [--all] [--preflight <preflight.json>]

判定口径（与 implementationPolicy.taskAcceptanceRule 一致）：
- testFiles 的冻结用例全部被已登记局部的输入计划覆盖；
- taskAcceptance.status=passed、casesCompared 等于冻结用例数、missingCases／missingAssertions／uncompared 均为 0；
- compareReport 非空且文件存在；
- 该事项覆盖的局部在最近一次 preflight 中 currentCaptureVerified=true（缺 preflight 时只提示）。
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
    parser.add_argument('--item', action='append', default=[])
    parser.add_argument('--all', action='store_true')
    parser.add_argument('--preflight', type=Path)
    options = parser.parse_args()

    state = read(TASK / 'feature_list.json')
    catalog = read(TASK / 'module-tests.json')
    file_cases = {file['path']: {case['id'] for case in file['cases']} for file in catalog['files']}
    config = read(TASK / 'full-evidence-locals.json')
    planned, current = {}, set()
    for local in config['locals']:
        plan = Path(local['input_plan'])
        if plan.exists():
            for case_id in read(plan):
                planned.setdefault(case_id, set()).add(local['name'])
    preflight = options.preflight or latest_preflight()
    if preflight and preflight.exists():
        for local in read(preflight)['locals']:
            if local.get('currentCaptureVerified'):
                plan = Path(next((item['input_plan'] for item in config['locals']
                                  if item['name'] == local['name']), ''))
                if plan.exists():
                    current |= set(read(plan))

    items = [item for item in state['features']
             if item.get('kind') == 'implementation-slice'
             and (options.all or item['id'] in options.item)]
    print(f"preflight: {preflight.name if preflight else '（无）'}")
    for item in items:
        files = item.get('testFiles', [])
        frozen = set().union(*(file_cases.get(path, set()) for path in files)) if files else set()
        uncovered = sorted(frozen - set(planned))
        acceptance = item.get('taskAcceptance') or {}
        reasons = []
        if uncovered:
            reasons.append(f'未计划 {len(uncovered)} 例')
        if acceptance.get('status') != 'passed':
            reasons.append('taskAcceptance 未通过')
        if acceptance.get('casesCompared') != len(frozen):
            reasons.append(f"casesCompared={acceptance.get('casesCompared')} ≠ {len(frozen)}")
        for key in ('missingCases', 'missingAssertions', 'uncompared'):
            if acceptance.get(key) not in (0, None):
                reasons.append(f'{key}={acceptance.get(key)}')
        report = acceptance.get('compareReport')
        if not report:
            reasons.append('compareReport 为空')
        elif not (TASK / report).exists():
            reasons.append('compareReport 文件不存在')
        stale = sorted(case_id for case_id in frozen if case_id not in current)
        if preflight and stale:
            reasons.append(f'当前来源未复核 {len(stale)} 例（收尾统一重采后消失）')
        verdict = 'READY' if not reasons else 'BLOCKED'
        print(f"{verdict:8} {item['id']:38} 冻结 {len(frozen):4} 已计划 {len(frozen) - len(uncovered):4} "
              f"当前来源 {len(frozen) - len(stale):4}" + (f" ｜ {'；'.join(reasons)}" if reasons else ''))


if __name__ == '__main__':
    main()
