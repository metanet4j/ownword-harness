#!/usr/bin/env python3
"""固定 ValidationHelpers 147 例的真实公开入参及 203 条原断言，保留 undefined/null 差异。"""
import argparse
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/__tests/validationHelpers.test.ts'
JAVA_CLASS = 'com.metanet4j.bsv.wallet.ValidationHelpersTest'
FROZEN_PLAN = TASK / 'validation-helpers-input-plan.json'
spec = importlib.util.spec_from_file_location('audit_tests', TASK / 'audit-tests.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source():
    catalog = read(TASK / 'module-tests.json')
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    mapping = read(TASK / 'test-map.json')
    case_ids = {case['id'] for case in file['cases']}
    site_ids = {site['id'] for site in file['sites']}
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in case_ids]
    mapping['siteReviews'] = [review for review in mapping['siteReviews'] if review['id'] in site_ids]
    assert len(file['cases']) == len(mapping['cases']) == 147
    assert sum(len(case['assertionIds']) for case in mapping['cases']) == 203
    return catalog, file, mapping


def by_test(raw):
    result = defaultdict(list)
    for item in raw:
        result[item['test']].append(item)
    return result


def input_rows(raw, file, mapping, plan=None):
    observed = by_test(raw)
    mapped = {case['id']: case for case in mapping['cases']}
    result = []
    for case_index, case in enumerate(file['cases'], 1):
        case_id = case['id']
        test = ' '.join(case['names'])
        calls = observed.pop(test)
        expected = plan[case_id]['sampleIds'] if plan else None
        assert len(calls) in (1, 2) and (expected is None or len(calls) == len(expected)), test
        occurrences = defaultdict(int)
        for number, call in enumerate(calls, 1):
            assert call['method'] in ('specOpThrowReviewActions', *EXPORTS), call
            assert isinstance(call['args'], list), call
            occurrences[call['method']] += 1
            if 'case' in call:
                assert call['case'] == case_index and call['occurrence'] == occurrences[call['method']], call
            else:
                assert call['source'] == FILE and isinstance(call['line'], int), call
            if plan:
                sample_id = expected[number - 1]
                if 'line' in call:
                    assert sample_id.startswith(f'{FILE}:{call["line"]}:'), call
            else:
                assert isinstance(call['line'], int) and call['line'] > 0
                sample_id = f'{FILE}:{call["line"]}:{call["method"]}#{number:04d}'
            value = {'test': test, 'method': call['method'], 'args': call['args'],
                     'preState': {'javaMethod': mapped[case_id]['java'][0]['name'], 'callIndex': number}}
            if 'constantValue' in call:
                value['constantValue'] = call['constantValue']
            result.append({'caseId': case_id, 'sampleId': sample_id, 'value': value})
    assert not observed, f'范围外输入：{list(observed)[:3]}'
    assert len(result) == 149
    return result


EXPORTS = {
    'parseWalletOutpoint', 'validateSatoshis', 'validateOptionalInteger', 'validateInteger',
    'validatePositiveIntegerOrZero', 'validateStringLength', 'validateBase64String', 'isHexString',
    'validateCreateActionInput', 'validateCreateActionOutput', 'validateCreateActionOptions',
    'validateCreateActionArgs', 'validateSignActionOptions', 'validateSignActionArgs',
    'validateAbortActionArgs', 'validateWalletPayment', 'validateBasketInsertion',
    'validateInternalizeOutput', 'validateOriginator', 'validateOptionalOutpointString',
    'validateOutpointString', 'validateRelinquishOutputArgs', 'validateRelinquishCertificateArgs',
    'validateListCertificatesArgs', 'validateAcquireIssuanceCertificateArgs',
    'validateAcquireDirectCertificateArgs', 'validateProveCertificateArgs',
    'validateDiscoverByIdentityKeyArgs', 'validateDiscoverByAttributesArgs',
    'validateListOutputsArgs', 'validateListActionsArgs'
}


def assertions_for(side, raw, file, mapping):
    reports = rows(raw)
    by_name = {' '.join(case['names']): case for case in file['cases']}
    by_method = {entry['java'][0]['name']: entry for entry in mapping['cases']}
    mapped = {entry['id']: entry for entry in mapping['cases']}
    positions = defaultdict(int)
    result = []
    for item in reports:
        case = by_name[item['test']] if side == 'ts' else by_method[item['method']]
        case_id = case['id']
        if side == 'java':
            assert item['test'] == JAVA_CLASS + '#' + item['method']
        position = positions[case_id]
        positions[case_id] += 1
        if side == 'java':
            assert item['index'] == position + 1
        identity = mapped[case_id]['assertionIds'][position]
        if side == 'ts':
            assert item['pass'] is True
        result.append({'caseId': case_id, 'assertionId': identity,
                       'value': {'matcher': item['matcher'], 'negated': item['negated'],
                                 'actual': item['actual']}})
    assert len(result) == 203
    for entry in mapping['cases']:
        assert positions[entry['id']] == len(entry['assertionIds'])
    return result


def prepare(args):
    catalog, file, mapping = source()
    ts_inputs = input_rows(rows(args.ts_inputs), file, mapping)
    assertions_for('ts', args.ts_assertions, file, mapping)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    plan = {}
    for case in file['cases']:
        case_id = case['id']
        identity = next(item for item in mapping['cases'] if item['id'] == case_id)['assertionIds']
        plan[case_id] = {'sampleIds': [item['sampleId'] for item in ts_inputs if item['caseId'] == case_id],
                         'assertionIds': identity, 'assertionSites': {site: site for site in identity},
                         'loopSamples': {}}
    audit.validate_plan(catalog, mapping, plan)
    assert plan == read(FROZEN_PLAN), '本轮 TS 输入或断言站点偏离提交的冻结计划'
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    write(output / 'catalog.json', catalog)
    write(output / 'mapping.json', mapping)
    write(output / 'input-plan.json', plan)
    write_rows(output / 'frozen-ts-inputs.jsonl', ts_inputs)
    print(json.dumps({'cases': 147, 'calls': 148, 'samples': 149, 'assertions': 203,
                      'output': str(output)}, ensure_ascii=False))


def differences(ts, java, path=''):
    if ts == java:
        return []
    if ts == {'type': 'undefined'} and java == {'type': 'null'}:
        return [{'path': path, 'ts': ts, 'java': java, 'absenceTranslation': True}]
    if isinstance(ts, dict) and isinstance(java, dict) and set(ts) == set(java):
        out = []
        for key in ts:
            out.extend(differences(ts[key], java[key], path + '/' + key))
        return out
    if isinstance(ts, list) and isinstance(java, list) and len(ts) == len(java):
        out = []
        for index, (left, right) in enumerate(zip(ts, java)):
            out.extend(differences(left, right, path + '/' + str(index)))
        return out
    return [{'path': path, 'ts': ts, 'java': java,
             'absenceTranslation': ts == {'type': 'undefined'} and java == {'type': 'null'}}]


def compare(args):
    folder = Path(args.plan)
    catalog, mapping, plan = (read(folder / name) for name in ('catalog.json', 'mapping.json', 'input-plan.json'))
    audit.validate_plan(catalog, mapping, plan)
    assert plan == read(FROZEN_PLAN), '局部计划与提交的冻结计划不同'
    file = catalog['files'][0]
    ts_inputs = input_rows(rows(args.ts_inputs), file, mapping, plan)
    java_inputs = input_rows(rows(args.java_inputs), file, mapping, plan)
    assert ts_inputs == rows(folder / 'frozen-ts-inputs.jsonl'), '本轮 TS 实际输入偏离冻结计划'
    def order_assertions(side, path):
        observed = assertions_for(side, path, file, mapping)
        indexed = {(row['caseId'], row['assertionId']): row for row in observed}
        assert len(indexed) == len(observed)
        return [indexed[(case['id'], identity)] for case in file['cases']
                for identity in plan[case['id']]['assertionIds']]
    ts_assertions = order_assertions('ts', args.ts_assertions)
    java_assertions = order_assertions('java', args.java_assertions)
    assert [row['assertionId'] for row in ts_assertions] == [row['assertionId'] for row in java_assertions]
    assertion_errors = []
    for left, right in zip(ts_assertions, java_assertions):
        try:
            audit.compare_actuals(left['caseId'], plan[left['caseId']], left['assertionId'],
                                  left['value'], right['value'])
        except ValueError as error:
            assertion_errors.append({'caseId': left['caseId'], 'assertionId': left['assertionId'],
                                     'error': str(error), 'ts': left['value'], 'java': right['value']})
    mismatches = []
    for left, right in zip(ts_inputs, java_inputs):
        assert left['caseId'] == right['caseId'] and left['sampleId'] == right['sampleId']
        for difference in differences(left['value'], right['value']):
            mismatches.append({'caseId': left['caseId'], 'sampleId': left['sampleId'], **difference})
    real = [item for item in mismatches if not item['absenceTranslation']]
    report = {'formalAcceptance': False, 'source': FILE, 'cases': len(plan), 'calls': 148,
              'samples': len(ts_inputs), 'assertions': len(ts_assertions),
              'sourceSha256': {'catalog': digest(folder / 'catalog.json'),
                               'mapping': digest(folder / 'mapping.json'),
                               'plan': digest(folder / 'input-plan.json'),
                               'tsInputs': digest(args.ts_inputs), 'javaInputs': digest(args.java_inputs),
                               'tsAssertions': digest(args.ts_assertions),
                               'javaAssertions': digest(args.java_assertions)},
              'exactInputCases': 147 - len({item['caseId'] for item in mismatches}),
              'absenceTranslationCases': len({item['caseId'] for item in mismatches if item['absenceTranslation']}),
              'absenceTranslationSlots': sum(item['absenceTranslation'] for item in mismatches),
              'otherInputDifferences': real, 'assertionDifferences': assertion_errors,
              'allInputDifferences': mismatches,
              'inputSamples': [{'caseId': left['caseId'], 'sampleId': left['sampleId'],
                                'ts': left['value'], 'java': right['value']}
                               for left, right in zip(ts_inputs, java_inputs)],
              'assertionSamples': [{'caseId': left['caseId'], 'assertionId': left['assertionId'],
                                    'ts': left['value'], 'java': right['value']}
                                   for left, right in zip(ts_assertions, java_assertions)]}
    write(args.report, report)
    print(json.dumps({key: report[key] for key in ('cases', 'samples', 'assertions', 'exactInputCases',
                      'absenceTranslationCases', 'absenceTranslationSlots')}
                     | {'otherInputDifferences': len(real), 'assertionDifferences': len(assertion_errors)}, ensure_ascii=False))
    if mismatches or assertion_errors:
        raise SystemExit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'compare'))
    parser.add_argument('--ts-inputs', required=True)
    parser.add_argument('--ts-assertions', required=True)
    parser.add_argument('--java-inputs')
    parser.add_argument('--java-assertions')
    parser.add_argument('--output')
    parser.add_argument('--plan')
    parser.add_argument('--report')
    args = parser.parse_args()
    if args.action == 'prepare':
        assert args.output
        prepare(args)
    else:
        assert args.plan and args.java_inputs and args.java_assertions and args.report
        compare(args)
