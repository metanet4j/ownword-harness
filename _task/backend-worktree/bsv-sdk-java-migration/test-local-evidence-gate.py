#!/usr/bin/env python3
"""local-evidence-gate 篡改目标选择的固定语义站点跳过规则自测；合成夹具只证明门禁，不计 SDK 用例。

固定规则站点（例如 Random.test.ts 的字节区间断言）在循环里会重复执行，计划里的实例身份是
`<站点>#<轮次>`；跳过判定必须按裸站点 ID 比较，否则这些实例会被当成普通断言去逐值重写，
篡改只会被专用规则拒绝，门禁就报“篡改未被拒绝”。
"""
import importlib.util
import unittest
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('local_evidence_gate', TASK / 'local-evidence-gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

# audit-tests.py 固定的 Random.test.ts 用例：站点 6:5、7:5 受 random-length-v1 约束。
RANDOM_CASE = 'c6ca731b61455ef1e4c19491a8afb0cee5758584cf6fc79d8009535634b7ccdf'
RANDOM_FILE = 'src/primitives/__tests/Random.test.ts'


class TamperSkipTest(unittest.TestCase):
    def test_guarded_sites_are_bare_site_ids(self):
        rows = [{'caseId': RANDOM_CASE, 'assertionId': f'{RANDOM_FILE}:6:5:assertion'}]
        guarded = gate.guarded_sites(rows)
        self.assertEqual(guarded, {f'{RANDOM_FILE}:6:5:assertion', f'{RANDOM_FILE}:7:5:assertion'})

    def test_repeated_instance_of_guarded_site_is_skipped(self):
        guarded = {f'{RANDOM_FILE}:17:7:assertion'}
        self.assertTrue(gate.tamper_skipped(f'{RANDOM_FILE}:17:7:assertion', guarded))
        self.assertTrue(gate.tamper_skipped(f'{RANDOM_FILE}:17:7:assertion#2', guarded))
        self.assertTrue(gate.tamper_skipped(f'{RANDOM_FILE}:17:7:assertion#100', guarded))

    def test_repeated_instance_of_plain_site_is_still_tampered(self):
        guarded = {f'{RANDOM_FILE}:17:7:assertion', f'{RANDOM_FILE}:18:7:assertion'}
        self.assertFalse(gate.tamper_skipped(f'{RANDOM_FILE}:32:7:assertion', guarded))
        self.assertFalse(gate.tamper_skipped(f'{RANDOM_FILE}:32:7:assertion#11', guarded))

    def test_unrelated_site_is_not_skipped(self):
        self.assertFalse(gate.tamper_skipped('src/primitives/__tests/PrivateKey.test.ts:93:9:assertion#4',
                                            {f'{RANDOM_FILE}:17:7:assertion'}))


if __name__ == '__main__':
    unittest.main()
