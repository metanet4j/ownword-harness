#!/usr/bin/env python3
"""原断言轨迹映射必须拒绝丢失、重复及错配身份。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest


TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('emit_assertions', TASK / 'emit-assertion-observations.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ObservationMappingTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw = Path(self.temp.name) / 'raw.jsonl'
        path = 'src/wallet/__tests/sample.test.ts'
        self.catalog = {'files': [{'path': path, 'cases': [
            {'id': 'first', 'names': ['sample', 'same name'], 'occurrence': 1},
            {'id': 'second', 'names': ['sample', 'same name'], 'occurrence': 2}]}]}
        self.mapping = {'cases': [
            {'id': 'first', 'java': [{'className': 'sample.Cases', 'name': 'first'}]},
            {'id': 'second', 'java': [{'className': 'sample.Cases', 'name': 'second'}]}]}
        self.plan = {'first': {'assertionIds': ['first-1', 'first-2']},
                     'second': {'assertionIds': ['second-1']}}

    def write(self, *rows):
        self.raw.write_text(''.join(json.dumps(row) + '\n' for row in rows))

    def ts(self, occurrence, index, matcher='toEqual', passed=True):
        return {'file': '/sdk/src/wallet/__tests/sample.test.ts', 'test': 'sample same name',
                'occurrence': occurrence, 'index': index, 'matcher': matcher,
                'negated': False, 'actual': {'type': 'number', 'value': str(index)},
                'expected': {'type': 'number', 'value': str(index)}, 'pass': passed}

    def java(self, method, index):
        return {'test': 'sample.Cases#' + method, 'method': method, 'index': index,
                'matcher': 'toEqual', 'negated': False,
                'actual': {'type': 'number', 'value': str(index)},
                'expected': {'type': 'number', 'value': str(index)}}

    def convert(self, side, allow_extra=False):
        return module.observations(self.catalog, self.mapping, self.plan, side,
                                   self.raw, 'run', allow_extra)

    def test_same_name_occurrences_keep_original_matcher_counters(self):
        first = self.ts(1, 1)
        first['expected'] = [{'type': 'string', 'value': 'field'}, {'type': 'number', 'value': '1'}]
        self.write(first, self.ts(1, 1, 'toBeDefined'), self.ts(2, 2))
        rows, ignored = self.convert('ts')
        self.assertEqual(['first-1', 'first-2', 'second-1'], [r['assertionId'] for r in rows])
        self.assertEqual({'type': 'array', 'value': first['expected']}, rows[0]['value']['expected'])
        self.assertEqual(first['actual'], rows[0]['value']['actual'])
        self.assertEqual(0, ignored)

    def test_failed_or_missing_ts_assertion_is_rejected(self):
        self.write(self.ts(1, 1, passed=False), self.ts(1, 1, 'toBeDefined'), self.ts(2, 2))
        with self.assertRaisesRegex(ValueError, '原断言失败'):
            self.convert('ts')
        self.write(self.ts(1, 1), self.ts(1, 1, 'toBeDefined'))
        with self.assertRaisesRegex(ValueError, '缺少用例'):
            self.convert('ts')

    def test_whole_file_ts_capture_can_explicitly_ignore_other_passing_cases(self):
        extra = self.ts(1, 1)
        extra['test'] = 'sample other case'
        self.write(extra, self.ts(1, 1), self.ts(1, 1, 'toBeDefined'), self.ts(2, 2))
        with self.assertRaisesRegex(ValueError, '范围外 TS 断言'):
            self.convert('ts')
        rows, ignored = module.observations(self.catalog, self.mapping, self.plan,
                                            'ts', self.raw, 'run', allow_ts_extra=True)
        self.assertEqual(3, len(rows))
        self.assertEqual(1, ignored)
        extra['pass'] = False
        self.write(extra, self.ts(1, 1), self.ts(1, 1, 'toBeDefined'), self.ts(2, 2))
        with self.assertRaisesRegex(ValueError, '范围外 TS 原断言失败'):
            module.observations(self.catalog, self.mapping, self.plan,
                                'ts', self.raw, 'run', allow_ts_extra=True)

    def test_java_extras_are_explicit_and_mapped_methods_remain_complete(self):
        self.write(self.java('first', 1), self.java('first', 2), self.java('extra', 1),
                   self.java('second', 1))
        with self.assertRaisesRegex(ValueError, '范围外 Java 断言'):
            self.convert('java')
        rows, ignored = self.convert('java', True)
        self.assertEqual(3, len(rows))
        self.assertEqual(1, ignored)

    def test_java_duplicate_or_wrong_ordinal_is_rejected(self):
        self.write(self.java('first', 1), self.java('first', 1), self.java('second', 1))
        with self.assertRaisesRegex(ValueError, '序号不连续'):
            self.convert('java')
        self.write(self.java('first', 1), self.java('first', 2), self.java('first', 3),
                   self.java('second', 1))
        with self.assertRaisesRegex(ValueError, '次数多于计划'):
            self.convert('java')


if __name__ == '__main__':
    unittest.main()
