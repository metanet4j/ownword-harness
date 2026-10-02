#!/usr/bin/env python3
"""把 audit-tests.py 已固定的语义规则写进局部计划的 `comparisonRules`。

背景：原测试的某些断言按跨语言约定在两侧写法不同（例如 TS 写基类 `Error`、Java 写
`SdkException`）。这些差异已按站点固定在 audit-tests.py 的 `SEMANTIC_CASES` 里，比较时
由 `compare_actuals` 逐条判定；而 `validate_plan` 要求计划显式登记这些规则，登记与实际
规则不一致会硬失败（既不允许漏登记，也不允许借计划扩大适用范围）。

各 prepare 脚本在生成局部计划时调用 `apply_semantic_rules(plan)`，与
`prepare-cached-keyderiver-inputs.py`、`prepare-primitives-last-local.py` 的既有做法一致。
这里不新增任何规则，只把已固定的规则登记进计划。
"""
import importlib.util
from pathlib import Path

TASK = Path(__file__).resolve().parent


def _audit():
    spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_semantic_rules(plan):
    """就地登记固定语义规则；返回登记了多少条断言。"""
    audit = _audit()
    registered = 0
    for case_id, entry in plan.items():
        fixed = audit.semantic_specs(case_id)
        if not fixed:
            continue
        sites = entry.get('assertionSites') or {}
        rules = dict(entry.get('comparisonRules') or {})
        for identity in entry.get('assertionIds') or []:
            site = sites.get(identity)
            if site in fixed:
                rules[identity] = fixed[site][0]
                registered += 1
        entry['comparisonRules'] = rules
    return registered
