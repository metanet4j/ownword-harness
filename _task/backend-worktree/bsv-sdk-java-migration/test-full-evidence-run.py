#!/usr/bin/env python3
"""联合来源门禁反例；两例合成夹具不计 SDK 验收，不运行 Maven。"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

TASK = Path(__file__).resolve().parent


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, TASK / filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


runner = module('full_run', 'full-evidence-run.py')
fixtures = module('bundle_fixtures', 'test-evidence-bundle.py')


class FullRunTest(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.BundleTest()
        self.fixture.setUp()
        self.root = self.fixture.root
        self.folder = self.root / 'run'
        self.folder.mkdir()
        for old, new in [('catalog.json', 'module-tests.json'), ('mapping.json', 'test-map.json')]:
            (self.root / new).write_bytes((self.root / old).read_bytes())
        runner.write(self.root / 'module-scope.json', {'scopeReview': 'reviewed'})
        self.catalog = runner.read(self.root / 'catalog.json')
        self.interface = {'tsCommand': ['fixture-ts'], 'javaCommand': ['fixture-java', 'clean', 'test'],
                          'tsReports': ['jest.json'], 'javaReports': ['surefire.xml']}
        for name in ['ts-inputs.jsonl', 'java-inputs.jsonl', 'ts-assertions.jsonl',
                     'java-assertions.jsonl', 'jest.json', 'surefire.xml']:
            (self.folder / name).write_bytes((self.root / name).read_bytes())
        (self.folder / 'input-plan.json').write_bytes((self.root / 'plan.json').read_bytes())
        runner.write(self.folder / 'preflight.json', {'readyForFullCapture': True, 'formalAcceptance': False})
        for index, side in enumerate(('ts', 'java')):
            log = self.folder / (side + '-run.json.log')
            log.write_text('合成工具夹具，不计 SDK 验收\n')
            child = runner.read(self.root / (side + '.manifest.json'))
            child.update(startedAtNs=100 + index * 100, finishedAtNs=110 + index * 100,
                         logPath=str(log), logSha256=runner.audit.digest(log), fullRunId='f' * 32,
                         fullRunProducerSha256=runner.audit.digest(TASK / 'full-evidence-run.py'))
            runner.write(self.folder / (side + '-run.json'), child)
        self.patches = [patch.object(runner, 'TASK', self.root),
                        patch.object(runner, 'frozen', return_value=self.catalog),
                        patch.object(runner.audit, 'java_revision', return_value='test-revision')]
        for item in self.patches:
            item.start()
        self.addCleanup(lambda: [item.stop() for item in reversed(self.patches)])
        self.addCleanup(self.fixture.tearDown)
        self.path = self.folder / 'full-run.json'
        commands = runner.commands_for(self.interface, self.folder)
        stages = []
        for index, (name, command) in enumerate(zip(runner.STAGES, commands)):
            log = self.folder / (name + '.log')
            log.write_text('合成工具子进程日志\n')
            stages.append({'name': name, 'command': command, 'exitCode': 0, 'pid': 123 + index,
                'startedAtNs': 90 + index * 100, 'finishedAtNs': 120 + index * 100,
                'logSha256': runner.audit.digest(log)})
        self.manifest = dict(runner.snapshot(), schemaVersion=1, fullRunId='f' * 32,
            status='passed', upstreamCommit='fixed', casesTotal=2, interface=self.interface,
            inputPlanSha256=runner.audit.digest(self.folder / 'input-plan.json'),
            timeoutMinutes=90, retryAfter=None, startedAtNs=80, finishedAtNs=430,
            elapsedSeconds=1.0, stages=stages, formalAcceptance=False)
        args = self.capture_args()
        runner.write(self.folder / 'parity-results.json', runner.bundle.build(args))
        self.seal()

    def capture_args(self):
        values = {'catalog': str(self.root / 'module-tests.json'), 'mapping': str(self.root / 'test-map.json'),
                  'input_plan': str(self.folder / 'input-plan.json'), 'java_revision': 'test-revision'}
        for side in ('ts', 'java'):
            for kind in ('inputs', 'assertions'):
                values[side + '_' + kind] = str(self.folder / (side + '-' + kind + '.jsonl'))
            values[side + '_run_manifest'] = str(self.folder / (side + '-run.json'))
            values[side + '_report'] = [str(self.folder / name) for name in self.interface[side + 'Reports']]
        return runner.SimpleNamespace(**values)

    def seal(self):
        self.manifest['artifactSha256'] = {name: runner.audit.digest(self.folder / name)
                                         for name in runner.artifact_names(self.interface)}
        runner.write(self.path, self.manifest)

    def test_full_source_and_actual_values_are_rechecked(self):
        result = runner.verify(self.path)
        self.assertEqual((result['cases'], result['comparedAssertions']), (2, 2))
        self.assertTrue(result['formalAcceptance'])

    def test_current_java_revision_change_rejected(self):
        with patch.object(runner.audit, 'java_revision', return_value='new-revision'):
            with self.assertRaisesRegex(ValueError, 'javaRevision'):
                runner.verify(self.path)

    def test_old_local_manifest_cannot_be_spliced_even_after_rehash(self):
        child = runner.read(self.folder / 'java-run.json')
        child.update(startedAtNs=1, finishedAtNs=2)
        runner.write(self.folder / 'java-run.json', child)
        self.seal()
        with self.assertRaisesRegex(ValueError, '时间窗'):
            runner.verify(self.path)

    def test_independent_capture_identity_rejected_even_in_correct_time_window(self):
        child = runner.read(self.folder / 'java-run.json')
        child['fullRunId'] = 'e' * 32
        runner.write(self.folder / 'java-run.json', child)
        self.seal()
        with self.assertRaisesRegex(ValueError, '联合身份'):
            runner.verify(self.path)

    def test_missing_stage_and_reordered_stage_rejected(self):
        for stages in (self.manifest['stages'][:3], list(reversed(self.manifest['stages']))):
            changed = dict(self.manifest, stages=stages)
            runner.write(self.path, changed)
            with self.assertRaisesRegex(ValueError, '顺序'):
                runner.verify(self.path)

    def test_overlapping_capture_envelopes_rejected(self):
        self.manifest['stages'][1]['startedAtNs'] = 100
        self.seal()
        with self.assertRaisesRegex(ValueError, '时间不连续'):
            runner.verify(self.path)

    def test_report_mutation_and_outside_report_rejected(self):
        (self.folder / 'surefire.xml').write_text('<testsuite tests="0"/>')
        with self.assertRaisesRegex(ValueError, '摘要'):
            runner.verify(self.path)
        self.interface['javaReports'] = ['../surefire.xml']
        with self.assertRaisesRegex(ValueError, '目录内'):
            runner.checked_path(self.folder, self.interface['javaReports'][0])

    def test_report_rehash_does_not_bypass_registration_check(self):
        (self.folder / 'surefire.xml').write_text('<testsuite tests="0" failures="0" errors="0" skipped="0"/>')
        self.seal()
        with self.assertRaisesRegex(ValueError, '未实际执行'):
            runner.verify(self.path)

    def test_same_number_of_wrong_java_cases_rejected(self):
        path = self.folder / 'surefire.xml'
        path.write_text(path.read_text().replace('name="second"', 'name="different"'))
        self.seal()
        with self.assertRaisesRegex(ValueError, '未实际执行'):
            runner.verify(self.path)

    def test_shared_symlink_report_rejected(self):
        path = self.folder / 'surefire.xml'
        path.unlink()
        path.symlink_to(self.root / 'surefire.xml')
        with self.assertRaisesRegex(ValueError, '目录内|符号链接'):
            runner.verify(self.path)

    def test_filtered_java_command_rejected(self):
        for flag in ('-Dtest=OnlyOneTest', '-Dgroups=unit', '-DexcludedGroups=manual', '--projects=sdk'):
            with self.subTest(flag=flag):
                self.interface['javaCommand'] = ['fixture-java', 'clean', 'test', flag]
                self.seal()
                with self.assertRaisesRegex(ValueError, '无过滤'):
                    runner.verify(self.path)

    def test_duplicate_report_path_rejected(self):
        self.interface['javaReports'].append('surefire.xml')
        with self.assertRaisesRegex(ValueError, '重复'):
            runner.artifact_names(self.interface)

    def test_changed_adapter_rejected(self):
        (self.root / 'adapter.py').write_text('print("changed")\n')
        with self.assertRaisesRegex(ValueError, 'producerSha256'):
            runner.verify(self.path)

    def test_180_minutes_requires_actual_90_minute_timeout(self):
        state = runner.snapshot()
        plan_sha = runner.audit.digest(self.folder / 'input-plan.json')
        with self.assertRaisesRegex(ValueError, '实际触及'):
            runner.validate_retry(180, None, state, self.interface, plan_sha)
        previous = dict(self.manifest, status='timed-out', elapsedSeconds=5399,
                        stages=[dict(self.manifest['stages'][0], timedOut=True, exitCode=-15, pid=123)])
        runner.write(self.path, previous)
        with self.assertRaisesRegex(ValueError, '未实际触及'):
            runner.validate_retry(180, self.path, state, self.interface, plan_sha)
        previous['elapsedSeconds'] = 5400.01
        previous['finishedAtNs'] = previous['startedAtNs'] + 5400010000000
        runner.write(self.path, previous)
        self.assertEqual(runner.validate_retry(180, self.path, state, self.interface, plan_sha)['sha256'],
                         runner.audit.digest(self.path))
        previous['javaRevision'] = 'old'
        runner.write(self.path, previous)
        with self.assertRaisesRegex(ValueError, '来源已变化'):
            runner.validate_retry(180, self.path, state, self.interface, plan_sha)

    def test_claimed_timeout_without_child_receipt_is_rejected(self):
        previous = dict(self.manifest, status='timed-out', elapsedSeconds=5400.01,
                        finishedAtNs=self.manifest['startedAtNs'] + 5400010000000,
                        stages=[{'timedOut': True}])
        runner.write(self.path, previous)
        with self.assertRaisesRegex(ValueError, '真实超时阶段'):
            runner.validate_retry(180, self.path, runner.snapshot(), self.interface,
                                  self.manifest['inputPlanSha256'])

    def test_command_wrapper_changes_only_capture_entrypoint(self):
        original = runner.preflight.execution_sequence({'fullRun': self.interface}, self.folder,
            self.root / 'module-tests.json', self.root / 'test-map.json')
        commands = runner.commands_for(self.interface, self.folder)
        self.assertEqual(commands[2:], original[2:])
        for before, after in zip(original[:2], commands[:2]):
            self.assertEqual(before[0], sys.executable)
            self.assertEqual(before[1:3], [str(TASK / 'evidence-bundle.py'), 'capture'])
            self.assertEqual(after[1:3], [str(self.root / 'full-evidence-run.py'), 'capture-side'])
            self.assertEqual(before[3:], after[3:])

    def test_real_child_exit_is_recorded(self):
        command = [sys.executable, '-c', 'raise SystemExit(7)']
        record = runner.run_process(command, self.root / 'real-exit.log', time.monotonic() + 5, os.environ)
        self.assertEqual(record['exitCode'], 7)
        self.assertGreater(record['pid'], 0)
        self.assertLessEqual(record['startedAtNs'], record['finishedAtNs'])

    def test_real_child_timeout_stops_process(self):
        command = [sys.executable, '-c', 'import time; time.sleep(60)']
        record = runner.run_process(command, self.root / 'real-timeout.log', time.monotonic() + 0.03, os.environ)
        self.assertTrue(record['timedOut'])
        self.assertLess(record['elapsedSeconds'], 5)
        self.assertIs(type(record['exitCode']), int)
        self.assertLess(record['exitCode'], 0)
        with self.assertRaises(ProcessLookupError):
            os.kill(record['pid'], 0)


if __name__ == '__main__':
    unittest.main()
