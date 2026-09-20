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


if __name__ == '__main__':
    unittest.main()
