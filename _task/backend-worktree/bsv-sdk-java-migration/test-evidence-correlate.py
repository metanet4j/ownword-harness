#!/usr/bin/env python3
"""只读轨迹关联自测；合成夹具不计 SDK 验收。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('correlate', TASK/'evidence-correlate.py')
correlate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(correlate)


class CorrelateTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root/'.cache/evidence').mkdir(parents=True)
        file = 'src/example.test.ts'
        self.put('feature_list.json', {'features': [{'id': 'slice', 'kind': 'implementation-slice', 'testFiles': [file]}]})
        self.put('module-tests.json', {'upstreamCommit': 'fixed', 'files': [{'path': file, 'cases': [
            {'id': 'one', 'names': ['suite', 'one'], 'occurrence': 1},
            {'id': 'loop', 'names': ['suite', 'loop'], 'occurrence': 1}],
            'sites': [{'id': 'site-one'}, {'id': 'site-loop'}]}]})
        self.put('test-map.json', {'cases': [
            {'id': 'one', 'java': [{'className': 'ExampleTest', 'name': 'one'}], 'assertionIds': ['site-one']},
            {'id': 'loop', 'java': [{'className': 'ExampleTest', 'name': 'loop'}], 'assertionIds': ['site-loop']}],
            'siteReviews': [{'id': 'site-one'}, {'id': 'site-loop'}]})
        self.put('api-catalog.json', {'entries': []})
        self.put('api-map.json', {'entries': []})
        self.put('module-scope.json', {'scopeReview': 'pending'})
        self.put('.cache/evidence/task-report.json', {'taskId': 'slice', 'casesTotal': 2, 'casesCompared': 2,
            'assertionsCompared': 3, 'missingCases': 0, 'missingAssertions': 0, 'uncompared': 0,
            'taskAcceptancePassed': True, 'cases': [
                {'id': 'one', 'tsAssertions': 1, 'javaAssertions': 1, 'matchedAssertions': 1},
                {'id': 'loop', 'tsAssertions': 2, 'javaAssertions': 2, 'matchedAssertions': 2}]})
        self.ts = [self.row('suite one', 1, file=file), self.row('suite loop', 2, file=file),
                   self.row('suite loop', 3, file=file)]
        self.java = [self.row('ExampleTest#one', 1), self.row('ExampleTest#loop', 2),
                     self.row('ExampleTest#loop', 3)]
        self.lines('ts-parity.jsonl', self.ts)
        self.lines('java-parity.jsonl', self.java)

    def tearDown(self):
        self.temp.cleanup()

    def put(self, name, value):
        path = self.root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))

    def lines(self, name, rows):
        self.put_lines(self.root/'.cache/evidence'/name, rows)

    @staticmethod
    def put_lines(path, rows):
        path.write_text(''.join(json.dumps(row)+'\n' for row in rows))

    @staticmethod
    def row(test, actual, file=None):
        row = {'test': test, 'matcher': 'toBe', 'actual': {'type': 'number', 'value': str(actual)},
               'expected': {'type': 'number', 'value': str(actual)}, 'pass': True}
        if file:
            row.update(file=file, occurrence=1)
        else:
            row['method'] = test.split('#')[-1]
        return row

    def test_only_single_site_can_link_without_callsite(self):
        result = correlate.analyze(self.root)
        self.assertEqual(result['totals']['taskReportCases'], 2)
        self.assertEqual(result['totals']['siteCardinalityExactCases'], 1)
        self.assertEqual(result['totals']['siteCardinalityAmbiguousCases'], 1)
        self.assertEqual([x['caseId'] for x in result['linkedEvents']], ['one'])
        self.assertEqual(result['linkedEvents'][0]['assertions'][0]['siteId'], 'site-one')
        self.assertTrue(all('inputSha' not in row for row in result['linkedEvents']))
        self.assertEqual(len(result['missingInputLedgerCaseIds']), 2)
        self.assertIn('siteCardinalityMismatchOrRepeatedSite',
                      next(x['reasons'] for x in result['caseGaps'] if x['caseId'] == 'loop'))

    def test_duplicate_trace_pair_is_ambiguous(self):
        self.lines('copy-parity.jsonl', self.ts)
        result = correlate.analyze(self.root)
        self.assertEqual(result['totals'].get('rawUniquePairCases', 0), 0)
        self.assertEqual(result['linkedEvents'], [])
        self.assertIn('duplicateTSTraceCandidates',
                      next(x['reasons'] for x in result['caseGaps'] if x['caseId'] == 'one'))

    def test_missing_java_trace_does_not_link(self):
        (self.root/'.cache/evidence/java-parity.jsonl').unlink()
        result = correlate.analyze(self.root)
        self.assertEqual(result['totals']['rawMissingCases'], 2)
        self.assertEqual(result['linkedEvents'], [])


if __name__ == '__main__':
    unittest.main()
