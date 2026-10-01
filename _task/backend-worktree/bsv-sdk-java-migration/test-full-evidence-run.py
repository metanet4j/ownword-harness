#!/usr/bin/env python3
"""联合来源门禁反例；两例合成夹具不计 SDK 验收，不运行 Maven。"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
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
        # 夹具 manifest 必须与 capture() 写出的字段一致：已知缺口登记同样进 manifest 并参与重验。
        known = runner.audit.known_unroutable_canonical()
        _, rules_sha = runner.audit.cross_language_rules()
        self.manifest = dict(runner.snapshot(), schemaVersion=1, fullRunId='f' * 32,
            status='passed', upstreamCommit='fixed', casesTotal=2, interface=self.interface,
            knownUnroutableCases=known, knownGapsSha256=known['registrySha256'],
            crossLanguageRulesSha256=rules_sha,
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


class TimeoutAccountingTest(unittest.TestCase):
    """超时路径的时间记账：elapsedSeconds 必须与 startedAtNs/finishedAtNs 同一时钟、同一时刻导出。

    背景：以前 elapsedSeconds 用 time.monotonic()、起止时间用 time.time_ns()，本机（WSL2）90 分钟
    两者漂移 10.7 s，加上清理窗口后 |wall-elapsed| = 10.673 s，被 validate_retry 的 <5 s 一致性
    检查拒掉（full-run-19 → full-run-20 的真实失败）。这里既验证记账形状，也验证协议未被放宽。
    """

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='timeout-accounting-')
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_normal_completion_fields_are_consistent(self):
        record = runner.run_process([sys.executable, '-c', 'print("ok")'],
                                    self.root / 'ok.log', time.monotonic() + 30, dict(os.environ))
        self.assertIsNone(record.get('timedOut'))
        self.assertEqual(record['exitCode'], 0)
        wall = (record['finishedAtNs'] - record['startedAtNs']) / 1e9
        self.assertLess(abs(wall - record['elapsedSeconds']), 0.05)

    def test_timeout_records_deadline_instant_and_cleanup_separately(self):
        record = runner.run_process([sys.executable, '-c', 'import time; time.sleep(60)'],
                                    self.root / 'slow.log', time.monotonic() + 2, dict(os.environ))
        self.assertTrue(record.get('timedOut'))
        self.assertEqual(record['finishedAtNs'], record['deadlineHitAtNs'])
        self.assertGreater(record['cleanupSeconds'], 0)
        wall = (record['finishedAtNs'] - record['startedAtNs']) / 1e9
        self.assertLess(abs(wall - record['elapsedSeconds']), 0.05)   # 同一时钟对导出
        self.assertLess(abs(wall - 2), 1.0)                           # 恰好停在截止时刻附近

    def retry_source(self, elapsed, wall=None, timed_out=True):
        """按 capture() 的记账口径合成一份 90 分钟档 manifest。"""
        started = 1_700_000_000_000_000_000
        wall = elapsed if wall is None else wall
        document = {'schemaVersion': 1, 'status': 'timed-out' if timed_out else 'failed',
                    'timeoutMinutes': 90, 'elapsedSeconds': elapsed, 'fullRunId': 'a' * 32,
                    'startedAtNs': started, 'finishedAtNs': started + int(wall * 1e9),
                    'interface': {'tsCommand': ['x']}, 'inputPlanSha256': 'b' * 64}
        path = self.root / ('retry-%s.json' % elapsed)
        path.write_text(json.dumps(document))
        return path, {'schemaVersion': 1}

    def test_validate_retry_accepts_consistent_90_minute_source(self):
        path, _ = self.retry_source(5400.05)
        with patch.object(runner, 'commands_for', return_value=[]), \
             patch.object(runner.audit, 'digest', return_value='b' * 64):
            document = json.loads(path.read_text())
            document['stages'] = [{'name': 'ts-capture', 'command': ['x'], 'pid': 1,
                                   'startedAtNs': document['startedAtNs'] + 1,
                                   'finishedAtNs': document['finishedAtNs'], 'timedOut': True,
                                   'exitCode': -15, 'logSha256': 'c' * 64}]
            path.write_text(json.dumps(document))
            runner.validate_retry(180, path, self.state(document), document['interface'],
                                  document['inputPlanSha256'])

    def state(self, document):
        """重试来源需要与当前 state 的键值一致；只取能对齐的键做形状验证。"""
        return {key: document.get(key) for key in document
                if key not in ('status', 'elapsedSeconds', 'finishedAtNs', 'error', 'stages')}

    def test_validate_retry_rejects_inconsistent_or_tampered_records(self):
        for elapsed, wall, message in ((5400.0, 5444.0, '记录无效'),      # 硬写 5400 但 wall 不一致
                                       (5400.05, 5406.5, '记录无效'),    # 差 > 5 s
                                       (5390.0, 5390.0, '触及 90 分钟上限')):  # 没到上限
            with self.subTest(message=message, elapsed=elapsed):
                path, _ = self.retry_source(elapsed, wall)
                with patch.object(runner, 'commands_for', return_value=[]), \
                     patch.object(runner.audit, 'digest', return_value='b' * 64):
                    document = json.loads(path.read_text())
                    document['stages'] = [{'name': 'ts-capture', 'command': ['x'], 'pid': 1,
                                           'startedAtNs': document['startedAtNs'] + 1,
                                           'finishedAtNs': document['finishedAtNs'], 'timedOut': True,
                                           'exitCode': -15, 'logSha256': 'c' * 64}]
                    path.write_text(json.dumps(document))
                    with self.assertRaisesRegex(ValueError, message):
                        runner.validate_retry(180, path, self.state(document), document['interface'],
                                              document['inputPlanSha256'])


if __name__ == '__main__':
    unittest.main()
