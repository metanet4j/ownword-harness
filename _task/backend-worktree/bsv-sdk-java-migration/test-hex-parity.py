#!/usr/bin/env python3
"""以一次真实 Hex 运行批次验证漏采、重复、输入及结果差异会被拒绝；不计 SDK 用例。"""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('hex_parity', Path(__file__).with_name('run-hex-parity.py'))
parity = importlib.util.module_from_spec(spec)
spec.loader.exec_module(parity)
EVIDENCE = Path(sys.argv.pop(1)).resolve()


class HexParityTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'evidence'
        shutil.copytree(EVIDENCE, self.folder)

    def change_ts(self, change):
        path = self.folder / 'ts.calls.jsonl'
        rows = [json.loads(line) for line in path.read_text().splitlines()]
        change(rows)
        path.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def test_real_evidence_passes(self):
        self.assertEqual(parity.compare(self.folder)['comparedAssertions'], 19)

    def test_missing_call_fails(self):
        self.change_ts(lambda rows: rows.pop())
        with self.assertRaisesRegex(ValueError, '实际调用缺失或重复'):
            parity.compare(self.folder)

    def test_duplicate_call_fails(self):
        self.change_ts(lambda rows: rows.__setitem__(1, rows[0]))
        with self.assertRaisesRegex(ValueError, '重复'):
            parity.compare(self.folder)

    def test_different_input_fails(self):
        self.change_ts(lambda rows: rows[0]['input'].update(value='a'))
        with self.assertRaisesRegex(ValueError, '输入或前置状态不同'):
            parity.compare(self.folder)

    def test_different_result_fails(self):
        self.change_ts(lambda rows: rows[0]['outcome'].update(value={'type': 'null'}))
        with self.assertRaisesRegex(ValueError, '实际结果不一致'):
            parity.compare(self.folder)

    def test_different_error_type_fails(self):
        def change(rows):
            next(row for row in rows if row['outcome']['kind'] == 'throw')['outcome']['name'] = 'TypeError'
        self.change_ts(change)
        with self.assertRaisesRegex(ValueError, '实际结果不一致'):
            parity.compare(self.folder)

    def test_tampered_report_fails(self):
        with (self.folder / 'ts.jest.json').open('a') as output:
            output.write(' ')
        with self.assertRaisesRegex(ValueError, '原始证据已变化'):
            parity.verify(self.folder)


# 累计批次还验证循环样本及调用轨迹；旧 Hex 批次仍只执行原来的 7 项。
if (EVIDENCE / 'ts.bn.calls.jsonl').exists():
    class BigNumberParityTest(unittest.TestCase):
        setUp = HexParityTest.setUp

        def change_bn(self, change):
            path = self.folder / 'ts.bn.calls.jsonl'
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            change(rows)
            path.write_text(''.join(json.dumps(row) + '\n' for row in rows))

        def test_bn_real_evidence_passes(self):
            self.assertEqual(parity.compare_bn(self.folder)['comparedAssertions'], 52)

        def test_bn_missing_loop_sample_fails(self):
            self.change_bn(lambda rows: rows.remove(next(r for r in rows if r['line'] == 139)))
            with self.assertRaisesRegex(ValueError, '实际断言缺失或重复'):
                parity.compare_bn(self.folder)

        def test_bn_duplicate_loop_sample_fails(self):
            def change(rows):
                loop = [r for r in rows if r['line'] == 139]
                loop[1]['occurrence'] = loop[0]['occurrence']
            self.change_bn(change)
            with self.assertRaisesRegex(ValueError, '重复'):
                parity.compare_bn(self.folder)

        def test_bn_missing_api_call_fails(self):
            self.change_bn(lambda rows: rows[0]['calls'].pop())
            with self.assertRaisesRegex(ValueError, 'API 调用轨迹缺失'):
                parity.compare_bn(self.folder)

        def test_bn_different_input_fails(self):
            self.change_bn(lambda rows: rows[0]['calls'][0]['args'][0].update(bits='0000000000000000'))
            with self.assertRaisesRegex(ValueError, '输入或前置状态不同'):
                parity.compare_bn(self.folder)

        def test_bn_different_actual_value_fails(self):
            self.change_bn(lambda rows: rows[0]['actual']['value'].update(value='3038'))
            with self.assertRaisesRegex(ValueError, '实际结果不一致'):
                parity.compare_bn(self.folder)

        def test_bn_different_error_message_fails(self):
            def change(rows):
                next(r for r in rows if r['actual']['kind'] == 'throw')['actual']['message'] = '错误消息已改变'
            self.change_bn(change)
            with self.assertRaisesRegex(ValueError, '实际结果不一致'):
                parity.compare_bn(self.folder)


if __name__ == '__main__':
    unittest.main()
