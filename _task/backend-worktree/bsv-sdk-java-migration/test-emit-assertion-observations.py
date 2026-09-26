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


class AuthFetchAsyncOrderTest(unittest.TestCase):
    CASE = '61b4ecc5ca8e8e0e52d508368744a12c06c31d670ea752d08a5d880a62cf5f63'
    FILE = 'src/auth/clients/__tests__/AuthFetch.test.ts'
    MATCHERS = ('toBe', 'toMatchObject', 'toHaveLength', 'toEqual', 'toEqual',
                'toBe', 'toBe', 'toThrow', 'toBe', 'toHaveLength')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raw = Path(self.temp.name) / 'raw.jsonl'
        self.catalog = {'upstreamCommit': 'f999e0c1aad9a7afd0cbadaaf23841d049af9d5a',
                        'files': [{'path': self.FILE,
                                   'sha256': '0312c9107dbd4acddab1cd282355090fad28dfe58b0f395b642641cca7654f0a',
                                   'cases': [{'id': self.CASE, 'names': ['AuthFetch payment handling',
                                       'handlePaymentAndRetry exhausts attempts and throws detailed error'],
                                              'occurrence': 1}]}]}
        self.mapping = {'cases': [{'id': self.CASE, 'java': [{
            'className': 'com.metanet4j.bsv.auth.clients.AuthFetchTest',
            'name': 'paymentRetryExhaustsAttemptsWithDetails'}]}]}
        sites = (271, 281, 284, 292, 293, 299, 305, 306, 314, 315)
        ids = [f'{self.FILE}:{site}:{5 if site >= 314 else 11}:assertion' for site in sites]
        self.plan = {self.CASE: {'assertionIds': ids, 'comparisonRules': {
            ids[4]: 'auth-payment-log-v1', ids[5]: 'auth-payment-log-v1'}}}

    def rows(self, side='ts'):
        counts = {}
        rows = []
        for number, matcher in enumerate(self.MATCHERS, 1):
            counts[matcher] = counts.get(matcher, 0) + 1
            common = {'index': counts[matcher] if side == 'ts' else number,
                      'matcher': matcher, 'negated': False,
                      'actual': {'type': 'number', 'value': str(number)},
                      'expected': {'type': 'number', 'value': str(number)}}
            if side == 'ts':
                common.update(file='/sdk/' + self.FILE,
                              test='AuthFetch payment handling handlePaymentAndRetry exhausts attempts and throws detailed error',
                              occurrence=1)
                common['pass'] = True
            else:
                common.update(test='com.metanet4j.bsv.auth.clients.AuthFetchTest#paymentRetryExhaustsAttemptsWithDetails',
                              method='paymentRetryExhaustsAttemptsWithDetails')
            rows.append(common)
        return rows

    def convert(self, rows, side='ts'):
        original = ''.join(json.dumps(row) + '\n' for row in rows)
        self.raw.write_text(original)
        result = module.observations(self.catalog, self.mapping, self.plan, side, self.raw, 'run')[0]
        self.assertEqual(original, self.raw.read_text())
        return result

    def test_outer_rejection_is_at_original_source_site_on_both_sides(self):
        for side in ('ts', 'java'):
            with self.subTest(side=side):
                result = self.convert(self.rows(side), side)
                self.assertEqual(self.plan[self.CASE]['assertionIds'], [row['assertionId'] for row in result])
                self.assertEqual('8', result[0]['value']['actual']['value'])
                self.assertEqual('1', result[1]['value']['actual']['value'])
                self.assertEqual('4', result[4]['value']['actual']['value'])
                self.assertEqual(side == 'ts', 'pass' in result[4]['value'])

    def test_misaligned_matcher_or_changed_source_is_rejected(self):
        rows = self.rows()
        rows[7]['matcher'] = 'toBe'
        with self.assertRaisesRegex(ValueError, 'matcher 执行顺序变化'):
            self.convert(rows)
        self.catalog['files'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, '源码或站点身份变化'):
            self.convert(self.rows())

    def test_missing_and_extra_assertions_are_rejected(self):
        with self.assertRaisesRegex(ValueError, '次数与计划不符'):
            self.convert(self.rows()[:-1])
        with self.assertRaisesRegex(ValueError, '次数多于计划'):
            self.convert(self.rows() + [self.rows()[-1]])


if __name__ == '__main__':
    unittest.main()
