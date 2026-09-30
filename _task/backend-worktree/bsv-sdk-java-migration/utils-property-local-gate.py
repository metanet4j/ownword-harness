#!/usr/bin/env python3
"""对固定 utils.property 单文件执行 audit-tests 局部映射与逐样本比较。"""
import argparse
import hashlib
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
spec = spec_from_file_location('audit', TASK / 'audit-tests.py')
audit = module_from_spec(spec)
spec.loader.exec_module(audit)
FILE = 'src/primitives/__tests/utils.property.test.ts'
TESTS = (
    'base58 property tests round-trips arbitrary non-empty byte sequences',
    'base58 property tests round-trips arbitrary Base58Check payloads and rejects checksum mutation',
    'base58 property tests matches independent vectors and enforces malformed-input and hex-output boundaries',
)
JAVA = (
    'roundTripsArbitraryNonEmptyByteSequences',
    'roundTripsBase58CheckAndRejectsChecksumMutation',
    'matchesIndependentVectorsAndMalformedBoundaries',
)


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def save(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def site(line, column):
    return f'{FILE}:{line}:{column}:assertion'


def numbered(base, count):
    return [f'{base}#{index:03d}' for index in range(1, count + 1)]


def assertion(raw):
    return {'kind': 'assertion', **{key: raw[key] for key in ('matcher', 'negated', 'actual', 'expected')}}


def run(args):
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    catalog = audit.read(TASK / 'module-tests.json')
    source = next(file for file in catalog['files'] if file['path'] == FILE)
    audit.require(len(source['cases']) == 3 and len(source['sites']) == 14, '固定单文件清单变化')
    catalog['files'] = [source]
    catalog['partialImplementationOnly'] = True
    mapping = audit.read(TASK / 'test-map.json')
    case_ids = {case['id'] for case in source['cases']}
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in case_ids]
    mapping['siteReviews'] = [review for review in mapping['siteReviews']
                              if review['id'] in {site['id'] for site in source['sites']}]
    audit.require(len(mapping['cases']) == 3 and len(mapping['siteReviews']) == 14,
                  '固定用例映射或站点复核不完整')
    tests = [case['id'] for case in source['cases']]
    samples = [rows(args.corpus), rows(args.java_inputs)]
    samples[1] = [row for name in TESTS[:2] for row in samples[1] if row['test'] == name]
    ts = rows(args.ts_assertions)
    java = rows(args.java_assertions)
    boundaries = [rows(args.ts_boundaries), rows(args.java_boundaries)]
    boundaries[0] = boundaries[0][:-1] + [{**boundaries[0][-1],
        'calls': [boundaries[0][-1]['calls'][1], boundaries[0][-1]['calls'][3]]}]
    audit.require(samples[0] == samples[1] and len(samples[0]) == 600
                  and boundaries[0] == boundaries[1] and len(boundaries[0]) == 76,
                  '两端属性样本或边界 API 输入不同')
    plan = {}
    observations = []
    bases = (site(27, 9), site(39, 9), site(46, 9), site(54, 5),
             site(55, 5), site(61, 7), site(65, 5))
    for index, case_id in enumerate(tests):
        if index == 0:
            sample_ids = numbered(bases[0], 300)
            assertion_ids = sample_ids
            sites = {identity: bases[0] for identity in assertion_ids}
            input_rows = [[{'sampleId': identity, 'value': sample} for identity, sample
                           in zip(sample_ids, pair[:300])] for pair in samples]
            loop_samples = {}
        elif index == 1:
            sample_ids = [f'{bases[1]}:input#{n:03d}' for n in range(1, 301)]
            first, second = numbered(bases[1], 300), numbered(bases[2], 300)
            assertion_ids = [identity for pair in zip(first, second) for identity in pair]
            sites = {**{identity: bases[1] for identity in first},
                     **{identity: bases[2] for identity in second}}
            input_rows = [[{'sampleId': identity, 'value': sample} for identity, sample
                           in zip(sample_ids, pair[300:])] for pair in samples]
            loop_samples = {}
        else:
            invalid_ids = numbered(bases[5], 73)
            assertion_ids = [bases[3], bases[4], *invalid_ids, bases[6]]
            sample_ids = assertion_ids
            sites = {bases[3]: bases[3], bases[4]: bases[4],
                     **{identity: bases[5] for identity in invalid_ids}, bases[6]: bases[6]}
            input_rows = [[{'sampleId': identity, 'value': sample} for identity, sample
                           in zip(sample_ids, pair)] for pair in boundaries]
            loop_samples = {f'{FILE}:60:5:loop': invalid_ids}
        plan[case_id] = {'sampleIds': sample_ids, 'assertionIds': assertion_ids,
                         'assertionSites': sites, 'loopSamples': loop_samples}
        next(item for item in mapping['cases'] if item['id'] == case_id)['assertionIds'] = assertion_ids
        raw = [[row for row in side if row['test'] == name] for side, name in
               ((ts, TESTS[index]), (java, 'com.metanet4j.bsv.primitives.UtilsPropertyTest#' + JAVA[index]))]
        audit.require(len(raw[0]) == len(raw[1]) == len(assertion_ids), '用例断言数量与冻结计划不同')
        result_rows = [[{'id': identity, 'value': assertion(row)} for identity, row
                        in zip(assertion_ids, pair)] for pair in raw]
        left_hash = hashlib.sha256(audit.canonical(input_rows[0]).encode()).hexdigest()
        right_hash = hashlib.sha256(audit.canonical(input_rows[1]).encode()).hexdigest()
        audit.require(left_hash == right_hash, '局部输入摘要不同')
        observations.append({'id': case_id, 'inputSha256': left_hash,
                             'tsInputSha256': left_hash, 'javaInputSha256': right_hash,
                             'ts': result_rows[0], 'java': result_rows[1]})
    audit.validate_plan(catalog, mapping, plan)
    catalog_path, map_path, plan_path, observed_path = (folder / name for name in
        ('catalog.json', 'mapping.json', 'input-plan.json', 'observations.json'))
    save(catalog_path, catalog)
    save(map_path, mapping)
    save(plan_path, plan)
    observed = {'upstreamCommit': catalog['upstreamCommit'],
                'javaRevision': audit.java_revision({'metanet4j-bsv-sdk': args.java_worktree}),
                'catalogSha256': audit.digest(catalog_path),
                'tsReportSha256': [audit.digest(args.ts_report)],
                'javaReportSha256': [audit.digest(args.java_report)],
                'cases': observations}
    save(observed_path, observed)
    result = audit.compare(SimpleNamespace(catalog=catalog_path, mapping=map_path,
        module=None, ts_report=[args.ts_report], java_report=[args.java_report],
        observations=observed_path, java_revision=observed['javaRevision']))
    result.update(scope='fixed utils.property.test.ts only', inputSamples=676,
                  propertyRoundsPerCase=300, shrinkCalls=0)
    save(folder / 'summary.json', result)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('output', 'corpus', 'java-inputs', 'ts-boundaries', 'java-boundaries',
                 'ts-assertions', 'java-assertions', 'ts-report', 'java-report', 'java-worktree'):
        parser.add_argument('--' + name, required=True)
    run(parser.parse_args())
