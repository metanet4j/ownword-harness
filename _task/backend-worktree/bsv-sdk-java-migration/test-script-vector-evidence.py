#!/usr/bin/env python3
"""共享向量采集器反例；合成用例不计入 SDK 验收。"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('vector_evidence', TASK / 'script-vector-evidence.py')
vector = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vector)


class VectorEvidenceTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.plan = self.root / 'plan'
        self.plan.mkdir()
        self.run = self.root / 'run'
        self.run.mkdir()
        self.identity = 'synthetic-case'
        self.java = 'com.metanet4j.bsv.script.ScriptVectorsTest#validVector1'
        self.case = {'id': self.identity, 'java': [{'className': self.java.split('#')[0], 'name': 'validVector1'}]}
        vector.write(self.plan / 'catalog.json', {'files': [{'path': vector.FILES[0], 'cases': [
            {'id': self.identity, 'names': ['fixture'], 'occurrence': 1}]}]})
        vector.write(self.plan / 'mapping.json', {'cases': [self.case]})
        vector.write(self.plan / 'input-plan.json', {self.identity: {
            'sampleIds': [f'input#{i:03d}' for i in range(1, 9)], 'assertionIds': ['a1', 'a2', 'a3', 'a4']}})
        args = ['00', '00', '51', '51', '00', 'OP_0', '51', 'OP_1']
        self.inputs = [{'runId': 'a' * 32, 'side': 'ts', 'caseId': self.identity, 'test': 'fixture',
                        'input': {'method': method, 'args': [value]}} for method, value in zip(vector.METHODS, args)]
        self.assertions = [{'file': '/sdk/' + vector.FILES[0], 'test': 'fixture', 'occurrence': 1,
            'matcher': 'toEqual', 'negated': False, 'actual': {'type': 'string', 'value': 'OP_0'},
            'expected': {'type': 'string', 'value': 'OP_0'}, 'pass': True} for _ in range(4)]
        self.save()

    def tearDown(self):
        self.temp.cleanup()

    def save(self):
        vector.write_rows(self.run / 'inputs.raw.jsonl', self.inputs)
        vector.write_rows(self.run / 'assertions.raw.jsonl', self.assertions)

    def normalize(self):
        return vector.normalize(self.run, self.plan, 'ts', 'a' * 32)

    def manifest(self):
        vector.write(self.run / 'manifest.json', {'side': 'ts', 'exitCode': 0, 'runId': 'a' * 32,
            'fixedInputs': vector.fingerprints(self.plan), 'sourceRevision': 'fixture', 'sourceRevisionAfter': 'fixture',
            'startedAtNs': 1, 'finishedAtNs': 2,
            'artifacts': {path.name: vector.audit.digest(path) for path in self.run.iterdir() if path.name != 'manifest.json'}})

    def test_exact_actual_call_sequence(self):
        result = self.normalize()
        self.assertEqual(len(result['inputs.jsonl']), 8)
        self.assertEqual(len(result['assertions.jsonl']), 4)
        self.assertEqual(result['inputs.jsonl'][5]['value'], {'method': 'Script.fromASM', 'args': ['OP_0']})

    def test_invalid_vectors_reuse_first_two_parsed_objects(self):
        self.case['java'][0]['name'] = 'invalidVector1'
        vector.write(self.plan / 'mapping.json', {'cases': [self.case]})
        plan = vector.read(self.plan / 'input-plan.json')
        plan[self.identity]['sampleIds'] = plan[self.identity]['sampleIds'][:6]
        vector.write(self.plan / 'input-plan.json', plan)
        self.inputs = [self.inputs[index] for index in (0, 2, 4, 5, 6, 7)]
        self.save()
        self.assertEqual(len(self.normalize()['inputs.jsonl']), 6)

    def test_missing_sample(self):
        self.inputs.pop()
        self.save()
        with self.assertRaisesRegex(ValueError, '数量'):
            self.normalize()

    def test_wrong_side_and_run_identity(self):
        self.inputs[0]['side'] = 'java'
        self.save()
        with self.assertRaisesRegex(ValueError, '身份'):
            self.normalize()

    def test_original_assertion_failure(self):
        self.assertions[1]['pass'] = False
        self.save()
        with self.assertRaisesRegex(ValueError, '未通过'):
            self.normalize()

    def test_vector_consumption_order(self):
        self.inputs[1]['input']['args'] = ['ff']
        self.save()
        with self.assertRaisesRegex(ValueError, '消费顺序'):
            self.normalize()

    def test_spend_front_state_missing_field(self):
        case = {'id': 'spend', 'java': [{'className': 'SpendValidVectorsTest'}]}
        with self.assertRaisesRegex(ValueError, '前置字段'):
            vector.validate_inputs(case, [{'method': 'Spend.constructor', 'args': [{'sourceTXID': '00'}]}])

    def test_old_producer_fingerprint(self):
        self.normalize()
        self.manifest()
        path = self.run / 'manifest.json'
        data = vector.read(path)
        data['fixedInputs'][str(TASK / 'script-vector-evidence.py')] = '0' * 64
        vector.write(path, data)
        with self.assertRaisesRegex(ValueError, '采集器'):
            vector.verify_manifest(self.run, 'ts', self.plan, self.root)

    def test_raw_tamper_rejected_even_after_refreshing_artifact_hash(self):
        self.normalize()
        self.inputs[5]['input']['args'] = ['changed-actual-input']
        self.save()
        self.manifest()
        with patch.object(vector, 'source_revision', return_value='fixture'):
            with self.assertRaisesRegex(ValueError, '规范化轨迹'):
                vector.verify_manifest(self.run, 'ts', self.plan, self.root)


if __name__ == '__main__':
    unittest.main()
