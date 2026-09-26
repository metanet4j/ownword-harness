#!/usr/bin/env python3
"""证据汇总工具自测；合成夹具只证明门禁，不计 SDK 用例。"""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

TASK = Path(__file__).resolve().parent


class BundleTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='evidence-bundle-test-')
        self.root = Path(self.tmp.name)
        self.write('catalog.json', {'upstreamCommit': 'fixed', 'modules': ['compat'],
            'moduleDependencies': {'compat': []}, 'files': [{'path': 'src/compat/example.test.ts',
            'cases': [{'id': 'case1', 'names': ['suite', 'first'], 'occurrence': 1, 'mode': 'run'},
                      {'id': 'case2', 'names': ['suite', 'second'], 'occurrence': 1, 'mode': 'run'}],
            'sites': [{'id': 'a1', 'kind': 'assertion'}, {'id': 'a2', 'kind': 'assertion'}]}]})
        self.write('mapping.json', {'upstreamCommit': 'fixed', 'cases': [
            {'id': 'case1', 'java': [{'className': 'ExampleTest', 'name': 'first'}], 'assertionIds': ['a1']},
            {'id': 'case2', 'java': [{'className': 'ExampleTest', 'name': 'second'}], 'assertionIds': ['a2']}],
            'siteReviews': [{'id': 'a1', 'status': 'reviewed', 'note': '第一条', 'caseIds': ['case1']},
                            {'id': 'a2', 'status': 'reviewed', 'note': '第二条', 'caseIds': ['case2']}]})
        self.write('plan.json', {'case1': {'sampleIds': ['fixture', 'loop-0', 'loop-1'], 'assertionIds': ['a1']},
                                 'case2': {'sampleIds': ['fixture'], 'assertionIds': ['a2']}})
        inputs = [{'caseId': 'case1', 'sampleId': 'fixture', 'value': {'type': 'hex', 'value': '0001'}},
                  {'caseId': 'case1', 'sampleId': 'loop-0', 'value': {'type': 'number', 'value': '0'}},
                  {'caseId': 'case1', 'sampleId': 'loop-1', 'value': {'type': 'number', 'value': '1'}},
                  {'caseId': 'case2', 'sampleId': 'fixture', 'value': {'type': 'null'}}]
        assertions = [{'caseId': 'case1', 'assertionId': 'a1', 'value': {'kind': 'return', 'value': {'type': 'hex', 'value': '0001'}}},
                      {'caseId': 'case2', 'assertionId': 'a2', 'value': {'kind': 'throw', 'name': 'Error', 'message': 'bad'}}]
        for name in ('ts-inputs.jsonl', 'java-inputs.jsonl'):
            self.write_lines(name, inputs)
        for name in ('ts-assertions.jsonl', 'java-assertions.jsonl'):
            self.write_lines(name, assertions)
        self.write('jest.json', {'success': True, 'numTotalTests': 2, 'numPassedTests': 2,
            'numFailedTests': 0, 'numPendingTests': 0, 'numTodoTests': 0,
            'testResults': [{'name': '/sdk/src/compat/example.test.ts', 'status': 'passed',
                'assertionResults': [{'ancestorTitles': ['suite'], 'title': 'first', 'status': 'passed'},
                                     {'ancestorTitles': ['suite'], 'title': 'second', 'status': 'passed'}]}]})
        self.path('surefire.xml').write_text('<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="ExampleTest" name="first"/><testcase classname="ExampleTest" name="second"/></testsuite>')

    def tearDown(self):
        self.tmp.cleanup()

    def path(self, name):
        return self.root / name

    def write(self, name, value):
        self.path(name).write_text(json.dumps(value, ensure_ascii=False))

    def write_lines(self, name, rows):
        self.path(name).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))

    def common(self):
        return ['--catalog', str(self.path('catalog.json')), '--mapping', str(self.path('mapping.json')),
                '--input-plan', str(self.path('plan.json')), '--ts-inputs', str(self.path('ts-inputs.jsonl')),
                '--java-inputs', str(self.path('java-inputs.jsonl')), '--ts-assertions', str(self.path('ts-assertions.jsonl')),
                '--java-assertions', str(self.path('java-assertions.jsonl')), '--ts-report', str(self.path('jest.json')),
                '--java-report', str(self.path('surefire.xml'))]

    def bundle(self):
        return subprocess.run(['python3', str(TASK/'evidence-bundle.py'), *self.common(),
                               '--java-revision', 'test-revision', '--output', str(self.path('results.json'))], capture_output=True, text=True)

    def audit(self):
        return subprocess.run(['python3', str(TASK/'audit-tests.py'), 'compare', *self.common(),
                               '--observations', str(self.path('results.json')), '--java-revision', 'test-revision'], capture_output=True, text=True)

    def test_real_pipeline_shape(self):
        bundle = self.bundle()
        self.assertEqual(bundle.returncode, 0, bundle.stderr)
        audit = self.audit()
        self.assertEqual(audit.returncode, 0, audit.stderr)
        result = json.loads(self.path('results.json').read_text())
        self.assertEqual(len(result['cases']), 2)
        self.assertEqual(len(result['cases'][0]['inputSamples']['TS']), 3)
        self.assertEqual(json.loads(audit.stdout)['comparedAssertions'], 2)

    def test_missing_loop_sample_from_both_sides_is_rejected(self):
        for side in ('ts', 'java'):
            name = side+'-inputs.jsonl'
            rows = [json.loads(line) for line in self.path(name).read_text().splitlines()]
            self.write_lines(name, [row for row in rows if row.get('sampleId') != 'loop-1'])
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('输入样本顺序', result.stderr)

    def test_same_missing_assertion_in_mapping_and_both_traces_is_rejected(self):
        data = json.loads(self.path('mapping.json').read_text())
        data['cases'][0]['assertionIds'] = []
        self.write('mapping.json', data)
        for side in ('ts', 'java'):
            name = side+'-assertions.jsonl'
            rows = [json.loads(line) for line in self.path(name).read_text().splitlines()]
            self.write_lines(name, [row for row in rows if row['caseId'] != 'case1'])
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue('独立计划' in result.stderr or '断言用例' in result.stderr, result.stderr)

    def test_byte_mutation_and_duplicate_assertion_are_rejected(self):
        rows = [json.loads(line) for line in self.path('java-assertions.jsonl').read_text().splitlines()]
        rows[0]['value']['value']['value'] = '0002'
        self.write_lines('java-assertions.jsonl', rows)
        self.assertIn('实际结果不一致', self.bundle().stderr)
        self.write_lines('java-assertions.jsonl', rows+rows[:1])
        self.assertIn('重复 assertionId', self.bundle().stderr)

    def test_changed_input_and_stale_report_are_rejected(self):
        rows = [json.loads(line) for line in self.path('java-inputs.jsonl').read_text().splitlines()]
        rows[0]['value']['value'] = '0002'
        self.write_lines('java-inputs.jsonl', rows)
        self.assertIn('输入或前置状态不同', self.bundle().stderr)
        self.write_lines('java-inputs.jsonl', [json.loads(line) for line in self.path('ts-inputs.jsonl').read_text().splitlines()])
        self.assertEqual(self.bundle().returncode, 0)
        self.path('jest.json').write_text(self.path('jest.json').read_text()+'\n')
        self.assertIn('校验值', self.audit().stderr)

    def test_capture_mutation_and_no_execution_are_rejected(self):
        self.assertEqual(self.bundle().returncode, 0)
        self.path('ts-inputs.jsonl').write_text(self.path('ts-inputs.jsonl').read_text()+'\n')
        self.assertIn('采集校验值', self.audit().stderr)
        self.path('surefire.xml').write_text('<testsuite tests="0" failures="0" errors="0" skipped="0"/>')
        self.assertIn('未实际执行', self.audit().stderr)

    def test_summary_cannot_replace_raw_actuals(self):
        self.assertEqual(self.bundle().returncode, 0)
        result = json.loads(self.path('results.json').read_text())
        result['cases'][0]['ts'][0]['value']['value']['value'] = '0002'
        result['cases'][0]['java'][0]['value']['value']['value'] = '0002'
        self.write('results.json', result)
        self.assertIn('原始采集不同', self.audit().stderr)


if __name__ == '__main__':
    unittest.main()
