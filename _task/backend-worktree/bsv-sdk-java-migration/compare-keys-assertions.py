#!/usr/bin/env python3
"""采集窗口前的快速对照：把 Java 断言轨迹按冻结计划与 TS 原断言轨迹逐位置比较。

不产生证据、不写 full-evidence-locals.json；只用于在正式 recapture 前发现
matcher／expected／actual／顺序不一致。
"""
import importlib.util
import json
import re
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

TEST_FILES = {
    'public-key': 'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/primitives/PublicKeyTest.java',
    'public-key-additional':
        'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/primitives/PublicKeyAdditionalTest.java',
    'ecdsa': 'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/primitives/ECDSATest.java',
    'schnorr': 'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/primitives/SchnorrTest.java',
    'symmetric-key': 'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/primitives/SymmetricKeyTest.java',
    'ecies': 'metanet4j-bsv-sdk/src/test/java/com/metanet4j/bsv/compat/ECIESTest.java',
}


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def java_cases(name):
    """从测试类的 CASES 表取 Java 方法名 → 用例 ID。"""
    source = (TASK / TEST_FILES[name]).read_text()
    return dict(re.findall(r'Map\.entry\("(\w+)",\s*"([0-9a-f]{64})"\)', source))


def main(directory, java_raw):
    java_rows = rows(java_raw)
    failures = 0
    for name in TEST_FILES:
        plan_dir = TASK / directory / f'{name}-plan-20260929'
        plan = json.loads((plan_dir / 'input-plan.json').read_text())
        catalog = json.loads((plan_dir / 'catalog.json').read_text())
        cases = {case['id']: case for file in catalog['files'] for case in file['cases']}
        ts_raw = rows(TASK / '.cache/evidence/keys-probe2-20260929' / f'{name}.assertions.raw.jsonl')
        by_case = {}
        for case_id, case in cases.items():
            key = (' '.join(case['names']), case['occurrence'])
            by_case[case_id] = [row for row in ts_raw if (row['test'], row['occurrence']) == key]
        methods = java_cases(name)
        java_by_case = {}
        for row in java_rows:
            if '#' not in row['test']:
                continue
            method = row['test'].split('#', 1)[1]
            case_id = methods.get(method)
            if case_id is None or case_id not in plan:
                continue
            java_by_case.setdefault(case_id, []).append(row)
        for case_id, expected in plan.items():
            planned = expected['assertionIds']
            ts = by_case[case_id]
            java = java_by_case.get(case_id, [])
            for label, got in (('TS', ts), ('Java', java)):
                if len(got) != len(planned):
                    print(f'✗ {name} {case_id[:8]} {label} 断言次数 {len(got)} != 计划 {len(planned)}')
                    failures += 1
            for position, identity in enumerate(planned):
                if position >= len(java) or position >= len(ts):
                    break
                left = {key: ts[position][key] for key in ('matcher', 'negated', 'actual', 'expected')}
                if isinstance(left['expected'], list) and left['expected']:
                    left['expected'] = {'type': 'array', 'value': left['expected']}
                left['kind'] = 'assertion'
                right = {key: java[position][key] for key in ('matcher', 'negated', 'actual', 'expected')}
                right['kind'] = 'assertion'
                if audit.canonical(left) != audit.canonical(right):
                    site = expected['assertionSites'][identity]
                    print(f'✗ {name} {case_id[:8]} {site} 第 {position + 1} 条不同')
                    print('   TS  =', audit.canonical(left)[:300])
                    print('   Java=', audit.canonical(right)[:300])
                    failures += 1
    print(json.dumps({'locals': len(TEST_FILES), 'mismatches': failures}, ensure_ascii=False))
    return 0 if failures == 0 else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1], sys.argv[2]))
