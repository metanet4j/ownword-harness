#!/usr/bin/env python3
"""证据汇总工具自测；合成夹具只证明门禁，不计 SDK 用例。"""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
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
        self.write('plan.json', {'case1': {'sampleIds': ['fixture', 'loop-0', 'loop-1'], 'assertionIds': ['a1'],
                                          'assertionSites': {'a1': 'a1'}},
                                 'case2': {'sampleIds': ['fixture'], 'assertionIds': ['a2'],
                                          'assertionSites': {'a2': 'a2'}}})
        inputs = [{'caseId': 'case1', 'sampleId': 'fixture', 'value': {'type': 'hex', 'value': '0001'}},
                  {'caseId': 'case1', 'sampleId': 'loop-0', 'value': {'type': 'number', 'value': '0'}},
                  {'caseId': 'case1', 'sampleId': 'loop-1', 'value': {'type': 'number', 'value': '1'}},
                  {'caseId': 'case2', 'sampleId': 'fixture', 'value': {'type': 'null'}}]
        assertions = [{'caseId': 'case1', 'assertionId': 'a1', 'value': {'kind': 'return', 'value': {'type': 'hex', 'value': '0001'}}},
                      {'caseId': 'case2', 'assertionId': 'a2', 'value': {'kind': 'throw', 'name': 'Error', 'message': 'bad'}}]
        for name in ('ts-inputs.jsonl', 'java-inputs.jsonl'):
            side = name.split('-')[0]
            self.write_lines(name, [dict(row, side=side, runId=('a' if side == 'ts' else 'b')*32) for row in inputs])
        for name in ('ts-assertions.jsonl', 'java-assertions.jsonl'):
            side = name.split('-')[0]
            self.write_lines(name, [dict(row, side=side, runId=('a' if side == 'ts' else 'b')*32) for row in assertions])
        self.write('jest.json', {'success': True, 'numTotalTests': 2, 'numPassedTests': 2,
            'numFailedTests': 0, 'numPendingTests': 0, 'numTodoTests': 0,
            'testResults': [{'name': '/sdk/src/compat/example.test.ts', 'status': 'passed',
                'assertionResults': [{'ancestorTitles': ['suite'], 'title': 'first', 'status': 'passed'},
                                     {'ancestorTitles': ['suite'], 'title': 'second', 'status': 'passed'}]}]})
        self.path('surefire.xml').write_text('<testsuite tests="2" failures="0" errors="0" skipped="0"><testcase classname="ExampleTest" name="first"/><testcase classname="ExampleTest" name="second"/></testsuite>')
        self.manifests()

    def manifests(self):
        # 合成来源只用于工具反例；不表示 SDK 执行或验收。
        digest = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
        for side in ('ts', 'java'):
            self.path(side+'.log').write_text('合成工具夹具；不计 SDK 测试\n')
            self.write(side+'.manifest.json', {'schemaVersion': 1, 'side': side,
                'runId': ('a' if side == 'ts' else 'b')*32,
                'producerSha256': digest(TASK/'evidence-bundle.py'),
                'upstreamCommit': 'fixed', 'sourceRevision': 'fixed' if side == 'ts' else 'test-revision',
                'sourceRevisionAfter': 'fixed' if side == 'ts' else 'test-revision',
                'catalogSha256': digest(self.path('catalog.json')), 'mappingSha256': digest(self.path('mapping.json')),
                'inputPlanSha256': digest(self.path('plan.json')), 'startedAtNs': 1, 'finishedAtNs': 2,
                'command': ['fixture-ts'] if side == 'ts' else ['fixture-java', 'clean', 'test'], 'exitCode': 0,
                'inputsSha256': digest(self.path(side+'-inputs.jsonl')),
                'assertionsSha256': digest(self.path(side+'-assertions.jsonl')),
                'reportSha256': [digest(self.path('jest.json' if side == 'ts' else 'surefire.xml'))],
                'logPath': side+'.log', 'logSha256': digest(self.path(side+'.log'))})

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
                '--java-report', str(self.path('surefire.xml')),
                '--ts-run-manifest', str(self.path('ts.manifest.json')),
                '--java-run-manifest', str(self.path('java.manifest.json'))]

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
        self.write_lines('java-inputs.jsonl', [dict(json.loads(line), side='java', runId='b'*32)
                                             for line in self.path('ts-inputs.jsonl').read_text().splitlines()])
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

    def test_ts_files_cannot_be_reused_as_java_capture(self):
        self.path('java-inputs.jsonl').unlink()
        self.path('java-inputs.jsonl').symlink_to(self.path('ts-inputs.jsonl'))
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('独立采集', result.stderr)

    def test_testcases_without_surefire_suite_are_rejected(self):
        self.path('surefire.xml').write_text('<notASurefireReport>'
            '<testcase classname="ExampleTest" name="first"/>'
            '<testcase classname="ExampleTest" name="second"/></notASurefireReport>')
        self.manifests()
        self.assertEqual(self.bundle().returncode, 0)
        result = self.audit()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Surefire', result.stderr)

    def test_reviewed_source_assertion_cannot_be_omitted_from_plan(self):
        catalog = json.loads(self.path('catalog.json').read_text())
        catalog['files'][0]['sites'].append({'id': 'a3', 'kind': 'assertion'})
        self.write('catalog.json', catalog)
        mapping = json.loads(self.path('mapping.json').read_text())
        mapping['siteReviews'].append({'id': 'a3', 'status': 'reviewed',
                                      'note': '第三条仍在冻结源码中', 'caseIds': ['case1']})
        self.write('mapping.json', mapping)
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('冻结断言站点', result.stderr)

    def test_cli_revision_cannot_restamp_existing_execution(self):
        self.assertEqual(self.bundle().returncode, 0)
        result = subprocess.run(['python3', str(TASK/'evidence-bundle.py'), *self.common(),
            '--java-revision', 'changed-without-execution', '--output', str(self.path('results.json'))],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('运行', result.stderr)

    def test_inventory_rejects_report_with_only_ids_and_claimed_totals(self):
        spec = importlib.util.spec_from_file_location('inventory', TASK/'evidence-inventory.py')
        inventory = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(inventory)
        self.write('feature_list.json', {'features': [{'id': 'task1', 'kind': 'implementation-slice',
            'testFiles': ['src/compat/example.test.ts']}]})
        self.write('module-tests.json', json.loads(self.path('catalog.json').read_text()))
        self.write('test-map.json', json.loads(self.path('mapping.json').read_text()))
        self.write('api-catalog.json', {'entries': []})
        self.write('api-map.json', {'entries': []})
        self.write('module-scope.json', {'scopeReview': 'pending'})
        self.path('.cache/evidence').mkdir(parents=True)
        self.write('.cache/evidence/fake.json', {'taskId': 'task1', 'casesTotal': 2, 'casesCompared': 2,
            'assertionsCompared': 999, 'missingCases': 0, 'missingAssertions': 0, 'uncompared': 0,
            'taskAcceptancePassed': True, 'cases': [{'id': 'case1'}, {'id': 'case2'}]})
        self.assertEqual(inventory.inventory(self.root)['taskReportsComplete'], 0)
        valid = {'taskId': 'task1', 'upstreamCommit': 'fixed', 'javaRevision': 'a'*64,
            'testFiles': ['src/compat/example.test.ts'], 'casesTotal': 2, 'casesCompared': 2,
            'assertionsCompared': 2, 'missingCases': 0, 'missingAssertions': 0, 'uncompared': 0,
            'extraJavaAssertions': 0, 'taskAcceptancePassed': True,
            'cases': [{'id': identity, 'file': 'src/compat/example.test.ts', 'tsAssertions': 1,
                       'javaAssertions': 1, 'matchedAssertions': 1, 'missingAssertions': 0,
                       'extraJavaAssertions': 0} for identity in ('case1', 'case2')]}
        self.write('.cache/evidence/fake.json', valid)
        result = inventory.inventory(self.root)
        self.assertEqual(result['taskReportsComplete'], 1)
        self.assertFalse(result['formalAcceptance'])
        self.assertFalse(result['tasks'][0]['runtimeProvenanceVerified'])
        valid['assertionsCompared'] = 999
        self.write('.cache/evidence/fake.json', valid)
        self.assertEqual(inventory.inventory(self.root)['taskReportsComplete'], 0)

    def test_repeated_source_site_has_distinct_runtime_assertions(self):
        plan = json.loads(self.path('plan.json').read_text())
        plan['case1']['assertionIds'] = ['a1#1', 'a1#2']
        plan['case1']['assertionSites'] = {'a1#1': 'a1', 'a1#2': 'a1'}
        self.write('plan.json', plan)
        for side in ('ts', 'java'):
            name = side+'-assertions.jsonl'
            rows = [json.loads(line) for line in self.path(name).read_text().splitlines()]
            self.write_lines(name, [dict(rows[0], assertionId='a1#1'),
                                    dict(rows[0], assertionId='a1#2'), rows[1]])
        self.manifests()
        result = self.bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['comparedAssertions'], 3)
        mapping = json.loads(self.path('mapping.json').read_text())
        mapping['cases'][0]['assertionIds'] = ['a1#1', 'a1#2']
        self.write('mapping.json', mapping)
        self.manifests()
        result = self.bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.audit().returncode, 0)
        for side in ('ts', 'java'):
            name = side+'-assertions.jsonl'
            self.write_lines(name, [json.loads(line) for line in self.path(name).read_text().splitlines()
                                    if json.loads(line)['assertionId'] != 'a1#2'])
        self.assertNotEqual(self.bundle().returncode, 0)

    def test_dropping_samples_from_plan_and_both_sides_breaks_runtime_lock(self):
        plan = json.loads(self.path('plan.json').read_text())
        plan['case1']['sampleIds'].remove('loop-1')
        self.write('plan.json', plan)
        for side in ('ts', 'java'):
            name = side+'-inputs.jsonl'
            self.write_lines(name, [json.loads(line) for line in self.path(name).read_text().splitlines()
                                    if json.loads(line)['sampleId'] != 'loop-1'])
        result = self.bundle()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('运行前固定', result.stderr)

    def test_manifest_and_runtime_identity_are_required(self):
        self.path('java.manifest.json').unlink()
        self.assertNotEqual(self.bundle().returncode, 0)
        self.manifests()
        data = json.loads(self.path('java.manifest.json').read_text())
        data['exitCode'] = 1
        self.write('java.manifest.json', data)
        self.assertIn('退出状态', self.bundle().stderr)
        self.write_lines('java-inputs.jsonl', [json.loads(line)
                        for line in self.path('ts-inputs.jsonl').read_text().splitlines()])
        self.manifests()
        self.assertIn('运行身份或侧别', self.bundle().stderr)

    def capture_command(self, script):
        self.path('producer.py').write_text(script)
        return ['python3', str(TASK/'evidence-bundle.py'), 'capture', '--side', 'java',
            '--catalog', str(self.path('catalog.json')), '--mapping', str(self.path('mapping.json')),
            '--input-plan', str(self.path('plan.json')), '--inputs', str(self.path('fresh/inputs.jsonl')),
            '--assertions', str(self.path('fresh/assertions.jsonl')), '--report', str(self.path('fresh/surefire.xml')),
            '--output', str(self.path('fresh/run.json')), '--', sys.executable, str(self.path('producer.py')),
            'clean', 'test']

    def test_capture_binds_executed_process_and_refuses_existing_outputs(self):
        script = '''import json, os
from pathlib import Path
root = Path(__file__).parent
for name, env in [('java-inputs.jsonl', 'EVIDENCE_INPUTS_PATH'), ('java-assertions.jsonl', 'EVIDENCE_ASSERTIONS_PATH')]:
    rows = [json.loads(line) for line in (root/name).read_text().splitlines()]
    Path(os.environ[env]).write_text(''.join(json.dumps(dict(row, runId=os.environ['EVIDENCE_RUN_ID'], side=os.environ['EVIDENCE_SIDE']))+'\\n' for row in rows))
(root/'fresh/surefire.xml').write_text((root/'surefire.xml').read_text())
print('合成工具执行夹具，不计 SDK 测试')
'''
        command = self.capture_command(script)
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(self.path('fresh/run.json').read_text())
        self.assertEqual(manifest['exitCode'], 0)
        self.assertEqual(manifest['sourceRevision'], manifest['sourceRevisionAfter'])
        self.assertRegex(manifest['sourceRevision'], '^[0-9a-f]{64}$')
        self.assertIn('不计 SDK 测试', self.path('fresh/run.json.log').read_text())
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('已经存在', result.stderr)

    def test_capture_failed_command_cannot_produce_success_manifest(self):
        result = subprocess.run(self.capture_command('raise SystemExit(9)\n'), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        manifest = json.loads(self.path('fresh/run.json').read_text())
        self.assertEqual(manifest['exitCode'], 9)
        self.assertNotIn('inputsSha256', manifest)

    def test_capture_success_without_observations_is_not_execution_evidence(self):
        result = subprocess.run(self.capture_command('print("no tests")\n'), capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('captureError', json.loads(self.path('fresh/run.json').read_text()))


if __name__ == '__main__':
    unittest.main()
