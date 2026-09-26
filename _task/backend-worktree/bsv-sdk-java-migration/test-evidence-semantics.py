#!/usr/bin/env python3
"""固定语义协议的命令行反例；合成观测不计 SDK 验收。"""
import importlib.util
import hashlib
import json
from pathlib import Path
import unittest

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('fixtures', TASK/'test-evidence-bundle.py')
fixtures = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fixtures)


def number(value):
    return {'type': 'number', 'value': str(value)}


def observation(matcher, actual, expected, negated=False):
    return {'kind': 'assertion', 'matcher': matcher, 'actual': actual,
            'expected': expected, 'negated': negated, 'pass': True}


def byte_array(values):
    return {'type': 'array', 'value': [number(value) for value in values]}


def text_value(value):
    return {'type': 'string', 'value': value}


class SemanticTest(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.BundleTest()
        self.f.setUp()
        self.addCleanup(self.f.tearDown)

    def case(self, case_id, specs, sample=None):
        catalog = json.loads((TASK/'module-tests.json').read_text())
        file = next(file for file in catalog['files'] if any(c['id'] == case_id for c in file['cases']))
        case = next(case for case in file['cases'] if case['id'] == case_id)
        sites = [file['path'] + ':' + suffix + ':assertion' for suffix, _, _, _ in specs]
        unique_sites = list(dict.fromkeys(sites))
        selected = dict(file, cases=[case], sites=[s for s in file['sites'] if s['id'] in unique_sites])
        self.f.write('catalog.json', dict(catalog, modules=[file['module']],
                     moduleDependencies={file['module']: []}, files=[selected]))
        self.f.write('mapping.json', {'upstreamCommit': catalog['upstreamCommit'], 'cases': [
            {'id': case_id, 'java': [{'className': 'ExampleTest', 'name': 'first'}], 'assertionIds': unique_sites}],
            'siteReviews': [{'id': site, 'status': 'reviewed', 'note': '固定源码工具夹具', 'caseIds': [case_id]}
                            for site in unique_sites]})
        seen = {}
        instances = []
        for site in sites:
            seen[site] = seen.get(site, 0) + 1
            instances.append(site if sites.count(site) == 1 else site+'#'+str(seen[site]))
        self.f.write('plan.json', {case_id: {'sampleIds': ['fixture'], 'assertionIds': instances,
            'assertionSites': dict(zip(instances, sites)),
            'comparisonRules': {instance: rule for instance, (_, rule, _, _) in zip(instances, specs) if rule}}})
        for side, offset in (('ts', 2), ('java', 3)):
            meta = {'caseId': case_id, 'side': side, 'runId': ('a' if side == 'ts' else 'b')*32}
            self.f.write_lines(side+'-inputs.jsonl', [dict(meta, sampleId='fixture', value=sample or {'fixture': 'fixed'})])
            self.f.write_lines(side+'-assertions.jsonl', [dict(meta, assertionId=instance, value=entry[offset])
                                for instance, entry in zip(instances, specs)])
        self.f.write('jest.json', {'success': True, 'numTotalTests': 1, 'numPassedTests': 1,
            'numFailedTests': 0, 'numPendingTests': 0, 'numTodoTests': 0,
            'testResults': [{'name': file['path'], 'status': 'passed', 'assertionResults': [
                {'ancestorTitles': case['names'][:-1], 'title': case['names'][-1], 'status': 'passed'}]}]})
        self.f.path('surefire.xml').write_text('<testsuite tests="1" failures="0" errors="0" skipped="0">'
            '<testcase classname="ExampleTest" name="first"/></testsuite>')
        self.case_id = case_id
        self.upstream = catalog['upstreamCommit']

    def manifests(self):
        self.f.manifests()
        for side in ('ts', 'java'):
            name = side+'.manifest.json'
            data = json.loads(self.f.path(name).read_text())
            data['upstreamCommit'] = self.upstream
            if side == 'ts':
                data['sourceRevision'] = data['sourceRevisionAfter'] = self.upstream
            self.f.write(name, data)

    def bundle(self):
        self.manifests()
        return self.f.bundle()

    def accepts(self):
        result = self.bundle()
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.f.audit()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)['formalAcceptance'])

    def mutate_java(self, change):
        rows = [json.loads(line) for line in self.f.path('java-assertions.jsonl').read_text().splitlines()]
        change(rows)
        self.f.write_lines('java-assertions.jsonl', rows)

    def rejects_mutations(self, name, changes):
        original = self.f.path(name).read_text()
        for label, change in changes:
            with self.subTest(label=label):
                data = json.loads(original)
                change(data)
                self.f.write(name, data)
                self.assertNotEqual(self.bundle().returncode, 0)
        self.f.path(name).write_text(original)

    def test_mnemonic_defined_objects_keep_real_observations_at_three_sites(self):
        cases = [('3615b20d761861ac232b77920af6fcb2926bb073fa24598e4ad5529b463f02da', '10:5'),
                 ('ade4e3788cc1ef20f22d3aee360d2dc4f5a6751ab67a6018cacdbd84af9f4beb', '122:7'),
                 ('cc1994143b51b506fc43ce7c967f2ed28a9ce5668e42db3d36cb263d85324589', '129:7')]
        for case_id, site in cases:
            with self.subTest(site=site):
                left = observation('toBeDefined', text_value('真实 TS 类源码或助记词'), [])
                right = observation('toBeDefined', text_value('[object Object]'), [])
                right.pop('pass')
                self.case(case_id, [(site, 'mnemonic-defined-object-v1', left, right)])
                self.accepts()
                original = self.f.path('java-assertions.jsonl').read_text()
                for change in [lambda v: v.update(actual={'type': 'undefined'}),
                               lambda v: v.pop('actual'),
                               lambda v: v.update(actual={}),
                               lambda v: v.update(matcher='toBeTruthy'),
                               lambda v: v.update(expected=text_value('different')),
                               lambda v: v.update(negated=True),
                               lambda v: v.update({'pass': False})]:
                    self.f.path('java-assertions.jsonl').write_text(original)
                    self.mutate_java(lambda rows: change(rows[0]['value']))
                    self.assertNotEqual(self.bundle().returncode, 0)
                self.f.path('java-assertions.jsonl').write_text(original)
                self.rejects_mutations('catalog.json', [
                    ('源码改变', lambda data: data['files'][0].update(sha256='0'*64)),
                    ('版本改变', lambda data: data.update(upstreamCommit='0'*40))])
                self.rejects_mutations('plan.json', [
                    ('未知站点', lambda data: data[self.case_id]['comparisonRules'].update(
                        {'invented': 'mnemonic-defined-object-v1'})),
                    ('删除规则', lambda data: data[self.case_id].pop('comparisonRules'))])
                ts = [json.loads(line) for line in self.f.path('ts-assertions.jsonl').read_text().splitlines()]
                ts[0]['value'].pop('pass')
                self.f.write_lines('ts-assertions.jsonl', ts)
                self.assertNotEqual(self.bundle().returncode, 0)

    def test_async_ready_null_adapter_is_limited_to_two_original_sites(self):
        left = observation('toBeUndefined', {'type': 'undefined'}, [])
        right = observation('toBeUndefined', {'type': 'null'}, [])
        self.case('5e08c3e9cd40aa0723c8bc4888818daf1fee79d866e74c68f6c76194748dc0c7',
                  [('38:7', 'async-ready-null-adapter-v1', left, right),
                   ('42:7', 'async-ready-null-adapter-v1', left, right)])
        self.accepts()
        original = self.f.path('java-assertions.jsonl').read_text()
        for label, change in [
            ('Java 改为未定义', lambda value: value.update(actual={'type': 'undefined'})),
            ('Java 改为字符串', lambda value: value.update(actual=text_value('undefined'))),
            ('原 matcher 改动', lambda value: value.update(matcher='toBeNull')),
            ('只报告 pass', lambda value: value.pop('actual')),
            ('原预期改动', lambda value: value.update(expected={'type': 'undefined'})),
        ]:
            with self.subTest(label=label):
                self.f.path('java-assertions.jsonl').write_text(original)
                self.mutate_java(lambda rows: change(rows[0]['value']))
                self.assertNotEqual(self.bundle().returncode, 0)
        self.f.path('java-assertions.jsonl').write_text(original)
        self.rejects_mutations('plan.json', [
            ('新增站点', lambda data: data[self.case_id]['comparisonRules'].update(
                {'invented': 'async-ready-null-adapter-v1'})),
            ('删规则', lambda data: data[self.case_id]['comparisonRules'].pop(
                next(iter(data[self.case_id]['comparisonRules'])))),
        ])

    def test_native_absence_adapters_keep_original_matchers_and_actuals(self):
        left = observation('toBeUndefined', {'type': 'undefined'}, [])
        right = observation('toBeNull', {'type': 'null'}, {'type': 'array', 'value': []})
        cases = [('9cb7ee6ed920ce4f9b0822ea4209d7c8f520e334a16e45f7913fdc989025a0be', '862:11'),
                 ('5c6b78e562b2b310489abb962a64b66061f9e2e226acd80d4998b6f2ad8f571f', '1139:5')]
        for case_id, site in cases:
            with self.subTest(case_id=case_id):
                self.case(case_id, [(site, 'native-null-absence-v1', left, right)])
                self.accepts()
                original = self.f.path('java-assertions.jsonl').read_text()
                self.mutate_java(lambda rows: rows[0]['value'].pop('pass'))
                self.accepts()
                self.f.path('java-assertions.jsonl').write_text(original)
                for change in [
                    lambda value: value.update(actual={'type': 'undefined'}),
                    lambda value: value.update(matcher='toBeUndefined'),
                    lambda value: value.update(expected=[]),
                    lambda value: value.pop('actual'),
                    lambda value: value.update({'pass': False}),
                ]:
                    self.f.path('java-assertions.jsonl').write_text(original)
                    self.mutate_java(lambda rows: change(rows[0]['value']))
                    self.assertNotEqual(self.bundle().returncode, 0)
                self.f.path('java-assertions.jsonl').write_text(original)
                ts_original = self.f.path('ts-assertions.jsonl').read_text()
                ts_rows = [json.loads(line) for line in ts_original.splitlines()]
                ts_rows[0]['value'].pop('pass')
                self.f.write_lines('ts-assertions.jsonl', ts_rows)
                self.assertNotEqual(self.bundle().returncode, 0)
                self.f.path('ts-assertions.jsonl').write_text(ts_original)

    def test_void_completion_adapter_keeps_three_original_return_values(self):
        left = observation('not.toThrow', {'type': 'undefined'}, [], True)
        right = observation('not.toThrow', {'type': 'null'}, [], True)
        cases = [('07a5dbdce1f6d9f8c7cf13e2e2c12109004de34ab68186fde3e000b0910ee7d0', '77:11'),
                 ('d7c84d782a644801d5697f2676a786714ad43a1999e2d3bd26bfe8b2cc67a9d2', '129:11'),
                 ('4c3b952ad3546f2aa72a27b21cc960ae4cf10925bc9346822aefec05fe0b44c5', '157:11')]
        for case_id, site in cases:
            with self.subTest(case_id=case_id):
                self.case(case_id, [(site, 'void-completion-null-adapter-v1', left, right)])
                self.accepts()
                original = self.f.path('java-assertions.jsonl').read_text()
                for change in [
                    lambda value: value.update(actual={'type': 'undefined'}),
                    lambda value: value.update(actual={'type': 'string', 'value': 'null'}),
                    lambda value: value.update(matcher='toThrow'),
                    lambda value: value.update(negated=False),
                    lambda value: value.pop('actual'),
                ]:
                    self.f.path('java-assertions.jsonl').write_text(original)
                    self.mutate_java(lambda rows: change(rows[0]['value']))
                    self.assertNotEqual(self.bundle().returncode, 0)
                self.f.path('java-assertions.jsonl').write_text(original)

    def test_fixed_timing_bounds_recompute_actuals_and_reject_pass_only(self):
        left = observation('toBeLessThan', number(2), number(50))
        right = observation('toBeLessThan', number(7), number(50))
        self.case('7eaf894b954c8a61105fc2ce63e4218989c2a07e1b6d93b23fb4e166540aa553',
                  [('822:5', 'timing-ms-v1', left, right)])
        self.accepts()
        original = self.f.path('java-assertions.jsonl').read_text()
        for label, change in [
            ('放宽边界', lambda value: value.update(expected=number(500))),
            ('负耗时', lambda value: value.update(actual=number(-1))),
            ('非有限值', lambda value: value.update(actual=number('NaN'))),
            ('更换matcher', lambda value: value.update(matcher='toBeGreaterThanOrEqual')),
        ]:
            with self.subTest(label=label):
                self.f.path('java-assertions.jsonl').write_text(original)
                self.mutate_java(lambda rows: change(rows[0]['value']))
                self.assertNotEqual(self.bundle().returncode, 0)
        self.f.path('java-assertions.jsonl').write_text(original)
        self.mutate_java(lambda rows: rows[0]['value'].update(actual=number(50)))
        self.assertNotEqual(self.bundle().returncode, 0)

    def test_rule_scope_and_source_cannot_be_changed(self):
        value = observation('toBeLessThan', number(1), number(50))
        self.case('7eaf894b954c8a61105fc2ce63e4218989c2a07e1b6d93b23fb4e166540aa553',
                  [('822:5', 'timing-ms-v1', value, value)])
        self.accepts()
        self.rejects_mutations('plan.json', [
            ('未知规则', lambda data: data[self.case_id].update(comparisonRules={
                data[self.case_id]['assertionIds'][0]: 'always-pass'})),
            ('删规则', lambda data: data[self.case_id].pop('comparisonRules')),
            ('未知实例', lambda data: data[self.case_id]['comparisonRules'].update(invented='timing-ms-v1')),
            ('任意未执行理由', lambda data: data[self.case_id].update(unexecutedSites={'invented': 'not reached'})),
        ])
        self.rejects_mutations('catalog.json', [
            ('源码改变', lambda data: data['files'][0].update(sha256='0'*64)),
            ('版本改变', lambda data: data.update(upstreamCommit='0'*40)),
        ])

    def test_audit_recomputes_predicate_after_consistent_fixture_resealing(self):
        value = observation('toBeLessThan', number(1), number(50))
        self.case('7eaf894b954c8a61105fc2ce63e4218989c2a07e1b6d93b23fb4e166540aa553',
                  [('822:5', 'timing-ms-v1', value, value)])
        self.accepts()
        result = json.loads(self.f.path('results.json').read_text())
        for side in ('ts', 'java'):
            name = side+'-assertions.jsonl'
            rows = [json.loads(line) for line in self.f.path(name).read_text().splitlines()]
            rows[0]['value']['actual'] = number(50)
            self.f.write_lines(name, rows)
            result['cases'][0][side][0]['value']['actual'] = number(50)
        self.manifests()
        digest = lambda name: hashlib.sha256(self.f.path(name).read_bytes()).hexdigest()
        for side in ('ts', 'java'):
            result['captureSha256'][side+'Assertions'] = digest(side+'-assertions.jsonl')
            result['runManifestSha256'][side] = digest(side+'.manifest.json')
        self.f.write('results.json', result)
        audit = self.f.audit()
        self.assertNotEqual(audit.returncode, 0)
        self.assertIn('实际耗时不满足固定原断言', audit.stderr)

    def test_random_iteration_count_and_paired_observations_are_fixed(self):
        specs = []
        for index in range(100):
            for position, matcher, bound in [('17:7', 'toBeGreaterThanOrEqual', 0),
                                              ('18:7', 'toBeLessThanOrEqual', 255)]:
                specs.append((position, 'random-byte-v1', observation(matcher, number(index), number(bound)),
                              observation(matcher, number(index + 1), number(bound))))
        self.case('848124cde9210d75b0dba6c87bb690fceb48e80509981a2248de901d22e61ee6', specs)
        self.accepts()
        original = self.f.path('java-assertions.jsonl').read_text()
        for value in (number(256), number('1.5'), number(2)):
            with self.subTest(value=value):
                self.f.path('java-assertions.jsonl').write_text(original)
                self.mutate_java(lambda rows: rows[0]['value'].update(actual=value))
                self.assertNotEqual(self.bundle().returncode, 0)
        self.f.path('java-assertions.jsonl').write_text(original)
        plan = json.loads(self.f.path('plan.json').read_text())
        expected = plan[self.case_id]
        removed = expected['assertionIds'].pop()
        expected['assertionSites'].pop(removed)
        expected['comparisonRules'].pop(removed)
        self.f.write('plan.json', plan)
        for side in ('ts', 'java'):
            name = side+'-assertions.jsonl'
            rows = [json.loads(line) for line in self.f.path(name).read_text().splitlines()]
            self.f.write_lines(name, rows[:-1])
        self.assertNotEqual(self.bundle().returncode, 0, '两端和计划同删一次迭代必须失败')
        self.mutate_java(lambda rows: rows[0].update(value={'pass': True}))
        self.assertNotEqual(self.bundle().returncode, 0)

    def test_random_length_and_distinctness_keep_real_bytes(self):
        self.case('c6ca731b61455ef1e4c19491a8afb0cee5758584cf6fc79d8009535634b7ccdf', [
            ('6:5', 'random-length-v1', observation('toHaveLength', byte_array([1]*3), number(3)),
             observation('toHaveLength', byte_array([2]*3), number(3))),
            ('7:5', 'random-length-v1', observation('toHaveLength', byte_array([3]*10), number(10)),
             observation('toHaveLength', byte_array([4]*10), number(10)))])
        self.accepts()
        self.mutate_java(lambda rows: rows[0]['value']['actual']['value'].pop())
        self.assertNotEqual(self.bundle().returncode, 0)
        self.case('61c17607ef11ee67bafe1096807885f72b10f33070c22870c32d2e3259c4505b', [
            ('12:5', 'random-distinct-v1', observation('not.toEqual', byte_array([1]*32), byte_array([2]*32), True),
             observation('not.toEqual', byte_array([3]*32), byte_array([4]*32), True))])
        self.accepts()
        self.mutate_java(lambda rows: rows[0]['value'].update(expected=rows[0]['value']['actual']))
        self.assertNotEqual(self.bundle().returncode, 0)

    def test_payment_logs_only_allow_fixed_dynamic_fields(self):
        specs = []
        for attempt, position in ((1, '293:11'), (2, '299:11')):
            stable = {'attempt': number(attempt), 'message': text_value(f'payment attempt {attempt} failed')}
            expected = {'type': 'map', 'value': stable}
            values = [observation('toEqual', {'type': 'map', 'value': dict(stable,
                timestamp=text_value(timestamp), stack=text_value(f'Error: payment attempt {attempt} failed\n{frame}'))},
                expected) for timestamp, frame in [('2026-09-26T10:00:00.001Z', '    at TS.test'),
                                                   ('2026-09-26T10:00:01.001Z', '    at Java.test')]]
            specs.append((position, 'auth-payment-log-v1', *values))
        self.case('61b4ecc5ca8e8e0e52d508368744a12c06c31d670ea752d08a5d880a62cf5f63', specs)
        self.accepts()
        original = self.f.path('java-assertions.jsonl').read_text()
        for label, change in [
            ('非法日期', lambda fields: fields.update(timestamp=text_value('2026-02-30T10:00:00.001Z'))),
            ('空堆栈', lambda fields: fields.update(stack=text_value(''))),
            ('伪消息', lambda fields: fields.update(message=text_value('ignored'))),
            ('额外字段', lambda fields: fields.update(ignored=text_value('ignored'))),
        ]:
            with self.subTest(label=label):
                self.f.path('java-assertions.jsonl').write_text(original)
                self.mutate_java(lambda rows: change(rows[0]['value']['actual']['value']))
                self.assertNotEqual(self.bundle().returncode, 0)
        self.f.path('java-assertions.jsonl').write_text(original)
        self.mutate_java(lambda rows: rows[0]['value']['actual']['value'].update(attempt=number(2)))
        self.assertNotEqual(self.bundle().returncode, 0)

    def test_fixed_branch_uses_fixture_operands_and_executed_throw(self):
        file = 'src/primitives/__tests/DRBG.test.ts'
        value = observation('toThrow', {'kind': 'throw', 'name': 'Error',
            'message': 'Nonce must be exactly 32 bytes (256 bits)'}, {'type': 'undefined'})
        sample = {'kind': 'branch', 'guardSiteId': file+':15:9:conditional',
            'entropyHex': 'ca851911349384bffe89de1cbdc46e6831e44d34a4fb935ee285dd14b71a7488',
            'nonceHex': '659ba96c601dc69fc902940805ec0ca8', 'taken': True, 'controlFlow': 'return'}
        self.case('b432ac30f3bce72b304c6ecc3b0da498289d8cfbc14b0a4ca7198f8ae38b8b9f',
                  [('16:11', None, value, value)], sample)
        catalog = json.loads(self.f.path('catalog.json').read_text())
        original = next(f for f in json.loads((TASK/'module-tests.json').read_text())['files'] if f['path'] == file)
        extra = [site for site in original['sites'] if site['id'] in
                 {file+':15:9:conditional', file+':26:9:assertion', file+':27:9:assertion'}]
        catalog['files'][0]['sites'].extend(extra)
        self.f.write('catalog.json', catalog)
        mapping = json.loads(self.f.path('mapping.json').read_text())
        mapping['siteReviews'].extend({'id': site['id'], 'status': 'reviewed', 'note': '固定分支工具夹具',
                                       'caseIds': [self.case_id]} for site in extra)
        self.f.write('mapping.json', mapping)
        plan = json.loads(self.f.path('plan.json').read_text())
        plan[self.case_id]['unexecutedSites'] = {file+':'+position+':assertion': {
            'ruleId': 'drbg-nist-invalid-input-v1', 'guardSiteId': file+':15:9:conditional',
            'sampleId': 'fixture'} for position in ('26:9', '27:9')}
        self.f.write('plan.json', plan)
        self.accepts()
        self.assertEqual(json.loads(self.f.audit().stdout)['justifiedUnexecutedAssertions'], 2)
        self.rejects_mutations('plan.json', [
            ('删分支证明', lambda data: data[self.case_id].pop('unexecutedSites')),
            ('自由文本理由', lambda data: data[self.case_id]['unexecutedSites'].update({file+':26:9:assertion': 'not reached'})),
            ('未知分支规则', lambda data: data[self.case_id]['unexecutedSites'][file+':26:9:assertion'].update(ruleId='skip')),
            ('伪条件站点', lambda data: data[self.case_id]['unexecutedSites'][file+':26:9:assertion'].update(guardSiteId='invented')),
            ('缺原样本', lambda data: data[self.case_id]['unexecutedSites'][file+':26:9:assertion'].update(sampleId='missing')),
            ('删实际异常断言', lambda data: data[self.case_id].update(assertionIds=[], assertionSites={})),
        ])
        originals = {side: self.f.path(side+'-inputs.jsonl').read_text() for side in ('ts', 'java')}
        for label, change in [('未进入分支', lambda value: value.update(taken=False)),
                              ('未提前返回', lambda value: value.update(controlFlow='continue'))]:
            with self.subTest(label=label):
                for side in ('ts', 'java'):
                    rows = [json.loads(line) for line in originals[side].splitlines()]
                    change(rows[0]['value'])
                    self.f.write_lines(side+'-inputs.jsonl', rows)
                self.assertNotEqual(self.bundle().returncode, 0)
        for side in ('ts', 'java'):
            self.f.path(side+'-inputs.jsonl').write_text(originals[side])
        assertions = {side: self.f.path(side+'-assertions.jsonl').read_text() for side in ('ts', 'java')}
        for side in ('ts', 'java'):
            rows = [json.loads(line) for line in assertions[side].splitlines()]
            rows[0]['value'] = {'pass': True}
            self.f.write_lines(side+'-assertions.jsonl', rows)
        self.assertNotEqual(self.bundle().returncode, 0)
        for side in ('ts', 'java'):
            self.f.path(side+'-assertions.jsonl').write_text(assertions[side])
        for side in ('ts', 'java'):
            name = side+'-inputs.jsonl'
            rows = [json.loads(line) for line in self.f.path(name).read_text().splitlines()]
            rows[0]['value']['nonceHex'] = '00'*32
            self.f.write_lines(name, rows)
        self.assertNotEqual(self.bundle().returncode, 0)


if __name__ == '__main__':
    unittest.main()
