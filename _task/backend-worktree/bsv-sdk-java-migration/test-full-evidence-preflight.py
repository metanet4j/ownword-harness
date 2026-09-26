#!/usr/bin/env python3
"""全量前置工具的篡改反例；合成数据不计 SDK 验收。"""
import copy
import importlib.util
from pathlib import Path
import unittest

TASK = Path(__file__).resolve().parent


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


preflight = module('preflight', 'full-evidence-preflight.py')
fixtures = module('fixtures', 'test-evidence-bundle.py')


class PreflightTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BundleTest()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.local = {'name': 'synthetic-only', 'catalog': 'catalog.json',
                      'mapping': 'mapping.json', 'input_plan': 'plan.json'}
        for side in ('ts', 'java'):
            self.local[side + '_inputs'] = side + '-inputs.jsonl'
            self.local[side + '_assertions'] = side + '-assertions.jsonl'
            self.local[side + '_run_manifest'] = side + '.manifest.json'
            self.local[side + '_report'] = ['jest.json' if side == 'ts' else 'surefire.xml']

    def tearDown(self):
        self.fixture.tearDown()

    def inspect(self, revision='test-revision', locals=None):
        return preflight.inspect({'locals': locals or [self.local]}, self.root,
            self.root / 'catalog.json', self.root / 'mapping.json', revision,
            [str(self.root / 'surefire.xml')])[0]

    def test_valid_local_still_never_formal(self):
        result = self.inspect()
        self.assertEqual(result['structurallyPlannedCases'], 2)
        self.assertEqual(result['plannedSamples'], 4)
        self.assertEqual(result['currentCaptureVerifiedCases'], 2)
        self.assertFalse(result['formalAcceptance'])

    def test_old_revision_rejected_as_current(self):
        result = self.inspect('new-revision')
        self.assertEqual(result['currentCaptureVerifiedCases'], 0)
        self.assertIn('版本', result['locals'][0]['captureError'])

    def test_old_producer_rejected(self):
        path = self.root / 'ts.manifest.json'
        data = preflight.load(path)
        data['producerSha256'] = '0' * 64
        preflight.write(path, data)
        self.assertIn('执行器', self.inspect()['locals'][0]['captureError'])

    def test_same_physical_file_rejected(self):
        self.local['java_inputs'] = self.local['ts_inputs']
        self.assertIn('同一物理文件', self.inspect()['locals'][0]['captureError'])

    def test_missing_sample_even_with_fresh_hash_rejected(self):
        path = self.root / 'java-inputs.jsonl'
        path.write_text('\n'.join(path.read_text().splitlines()[1:]) + '\n')
        self.fixture.manifests()
        self.assertIn('样本', self.inspect()['locals'][0]['captureError'])

    def test_wrong_side_rejected(self):
        path = self.root / 'java-inputs.jsonl'
        path.write_text(path.read_text().replace('"side": "java"', '"side": "ts"'))
        self.fixture.manifests()
        self.assertIn('侧别', self.inspect()['locals'][0]['captureError'])

    def test_conflicting_case_plan_rejected_atomically(self):
        merged = {'a': {'sampleIds': ['old']}}
        with self.assertRaisesRegex(ValueError, '冲突'):
            preflight.merge_plan(merged, {'b': {}, 'a': {'sampleIds': ['new']}})
        self.assertEqual(merged, {'a': {'sampleIds': ['old']}})

    def test_changed_mapping_rejected(self):
        old = preflight.load(self.root / 'mapping.json')
        preflight.write(self.root / 'old-map.json', old)
        self.local['mapping'] = 'old-map.json'
        old['cases'][0]['java'][0]['name'] = 'differentRegistration'
        preflight.write(self.root / 'mapping.json', old)
        self.assertIn('映射已变化', self.inspect()['locals'][0]['planError'])

    def test_missing_case_visible_and_blocks(self):
        local = copy.deepcopy(self.local)
        catalog = preflight.load(self.root / 'catalog.json')
        catalog['files'][0]['cases'] = catalog['files'][0]['cases'][:1]
        catalog['files'][0]['sites'] = catalog['files'][0]['sites'][:1]
        mapping = preflight.load(self.root / 'mapping.json')
        mapping['cases'] = mapping['cases'][:1]
        mapping['siteReviews'] = mapping['siteReviews'][:1]
        plan = preflight.load(self.root / 'plan.json')
        for key, value in [('catalog', catalog), ('mapping', mapping), ('input_plan', {'case1': plan['case1']})]:
            local[key] = 'partial-' + key + '.json'
            preflight.write(self.root / local[key], value)
        result = self.inspect(locals=[local])
        self.assertEqual(result['missingPlanCases'], ['case2'])
        self.assertFalse(result['readyForFullCapture'])

    def test_java_reused_identity_blocks_and_links_surefire(self):
        path = self.root / 'mapping.json'
        mapping = preflight.load(path)
        mapping['cases'][1]['java'] = mapping['cases'][0]['java']
        preflight.write(path, mapping)
        result = self.inspect()
        self.assertEqual(result['javaRegistrations']['duplicateReferences'], 1)
        self.assertEqual(result['javaRegistrations']['duplicateGroups'][0]['surefireOccurrences'], 1)
        self.assertFalse(result['readyForFullCapture'])

    def test_four_commands_keep_two_runs_then_bundle_then_final_check(self):
        config = {'fullRun': {'tsCommand': ['python3', 'real-ts-adapter.py', '--output', '{runDir}/jest.json'],
            'javaCommand': ['python3', 'real-java-adapter.py', 'clean', 'test'],
            'tsReports': ['jest.json'], 'javaReports': ['surefire.xml']}}
        commands = preflight.execution_sequence(config, self.root / 'new-run',
            self.root / 'catalog.json', self.root / 'mapping.json')
        self.assertEqual(len(commands), 4)
        self.assertIn('ts', commands[0])
        self.assertIn('java', commands[1])
        self.assertIn('check', commands[3])
        self.assertTrue(all('{runDir}' not in part for command in commands for part in command))
        config['fullRun']['javaCommand'].append('-Dtest=OneTest')
        with self.assertRaisesRegex(ValueError, '无过滤'):
            preflight.execution_sequence(config, self.root / 'new-run',
                self.root / 'catalog.json', self.root / 'mapping.json')

    def test_missing_full_adapter_interface_blocks(self):
        result = self.inspect()
        self.assertEqual(len(result['missingFullRunInterfaces']), 4)
        self.assertFalse(result['readyForFullCapture'])


if __name__ == '__main__':
    unittest.main()
