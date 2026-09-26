#!/usr/bin/env python3
"""固定 ChronicleOpcodes 全文件的真实输入与断言局部对照。"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('script_vectors', TASK / 'script-vector-evidence.py')
vectors = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vectors)
audit, preflight = vectors.audit, vectors.preflight
FILE = 'src/script/__tests/ChronicleOpcodes.test.ts'
CLASS = 'com.metanet4j.bsv.script.ChronicleOpcodesTest'
LOOPS = {'Post-Chronicle opcode activation (all should succeed)': 458,
         'Undefined opcodes (>= 0xba) must fail': 483,
         'Valid NOPs still work': 505,
         'OP_RIGHT slice fix': 543}
vectors.FILES = (FILE,)
vectors.CLASSES = ('ChronicleOpcodesTest',)
original_fingerprints = vectors.fingerprints


def fingerprints(folder):
    return dict(original_fingerprints(folder), **{str(Path(__file__)): audit.digest(__file__)})


vectors.fingerprints = fingerprints


def prepare(folder):
    catalog, mapping = (vectors.read(TASK / name) for name in ('module-tests.json', 'test-map.json'))
    source = next(file for file in catalog['files'] if file['path'] == FILE)
    chosen = {case['id']: case for case in source['cases']}
    selected = [case for case in mapping['cases'] if case['id'] in chosen]
    audit.require(len(selected) == len(chosen) == 74, '固定 Chronicle 用例数变化')
    local_catalog = dict(catalog, files=[source], partialImplementationOnly=True)
    ids = set(chosen)
    sites = {site['id'] for site in source['sites']}
    local_mapping = dict(mapping, cases=[], siteReviews=[dict(review,
        caseIds=[identity for identity in review['caseIds'] if identity in ids])
        for review in mapping['siteReviews'] if review['id'] in sites])
    plan = {}
    for case in selected:
        owner = chosen[case['id']]
        audit.require(len(case['assertionIds']) == 1 and len(case['java']) == 1
                      and case['java'][0]['className'] == CLASS, '原断言或 Java 身份变化')
        count = 4 if owner['names'][1] == 'OP_RIGHT slice fix' else 1
        sample_ids = [f'input#{index:03d}' for index in range(1, count + 1)]
        site = case['assertionIds'][0]
        assertion_ids = [site + f'#{index:03d}' for index in range(1, count + 1)] if count > 1 else [site]
        local_mapping['cases'].append(dict(case, assertionIds=assertion_ids))
        loop = LOOPS.get(owner['names'][1])
        plan[case['id']] = {'sampleIds': sample_ids, 'assertionIds': assertion_ids,
            'assertionSites': {identity: site for identity in assertion_ids},
            'loopSamples': {f'{FILE}:{loop}:5:loop' if loop != 543 else f'{FILE}:543:7:loop': sample_ids}
                           if loop else {}}
    preflight.validate_subset(catalog, mapping, local_catalog, local_mapping, plan)
    audit.require(sum(len(value['sampleIds']) for value in plan.values()) == 77, '固定 Spend 调用次数变化')
    folder.mkdir(parents=True, exist_ok=False)
    for name, value in [('catalog', local_catalog), ('mapping', local_mapping), ('input-plan', plan)]:
        vectors.write(folder / (name + '.json'), value)
    print(json.dumps({'cases': len(plan), 'samples': 77, 'assertions': 77}, ensure_ascii=False))


def validate_inputs(case, values):
    audit.require(all(value.get('method') == 'Spend.constructor' and len(value.get('args', [])) == 1
                      for value in values), 'Spend 实际调用形态变化：' + case['id'])
    fields = {'sourceTXID', 'sourceOutputIndex', 'sourceSatoshis', 'lockingScriptHex',
              'transactionVersion', 'otherInputs', 'outputs', 'inputIndex',
              'unlockingScriptHex', 'inputSequence', 'lockTime'}
    for value in values:
        input_value = value['args'][0]
        audit.require(set(input_value) == fields, 'Spend 实际字段变化：' + case['id'])
        audit.require(input_value['sourceTXID'] == '0' * 64 and input_value['otherInputs'] == []
                      and input_value['outputs'] == [] and input_value['sourceOutputIndex'] == '0'
                      and input_value['sourceSatoshis'] == '1' and input_value['inputIndex'] == '0'
                      and input_value['inputSequence'] == '4294967295' and input_value['lockTime'] == '0'
                      and isinstance(input_value['lockingScriptHex'], str)
                      and isinstance(input_value['unlockingScriptHex'], str),
                      'Spend 固定前置状态变化：' + case['id'])


vectors.validate_inputs = validate_inputs


def compare(plan_folder, ts_folder, java_folder, java, output):
    manifests = {side: vectors.verify_manifest(folder, side, plan_folder, java)
                 for side, folder in [('ts', ts_folder), ('java', java_folder)]}
    audit.require(manifests['ts']['runId'] != manifests['java']['runId'], '两侧运行身份重复')
    catalog, mapping, plan = (vectors.read(plan_folder / (name + '.json'))
                              for name in ('catalog', 'mapping', 'input-plan'))
    preflight.validate_subset(vectors.read(TASK / 'module-tests.json'),
                              vectors.read(TASK / 'test-map.json'), catalog, mapping, plan)
    full_catalog = vectors.read(TASK / 'module-tests.json')
    audit.compare_ts(dict(full_catalog, files=[file for file in full_catalog['files'] if file['path'] == FILE]),
                     [ts_folder / 'jest.json'])
    registration = preflight.java_registrations(mapping, catalog, list(java_folder.glob('*.xml')))
    audit.require(registration['surefireCases'] == 74 and not registration['missingMappedIdentities']
                  and not registration['duplicateReferences'] and not registration['duplicateSurefireIdentities'],
                  'Java 实际注册不完整')
    for name, key in [('inputs.jsonl', 'sampleId'), ('assertions.jsonl', 'assertionId')]:
        audit.require(not (ts_folder / name).samefile(java_folder / name), '两侧不能共用同一轨迹')
        values = {}
        for side, folder in [('ts', ts_folder), ('java', java_folder)]:
            normalized = audit.capture_rows(folder / name, key)
            audit.same_keys(plan, normalized, side + ' 实际用例')
            for identity, entries in normalized.items():
                expected = plan[identity]['sampleIds' if key == 'sampleId' else 'assertionIds']
                audit.require([row[key] for row in entries] == expected, '逐调用顺序不同：' + identity)
                audit.require(all(row['side'] == side and row['runId'] == manifests[side]['runId']
                                  for row in entries), '轨迹运行身份不同')
            values[side] = {identity: [row['value'] for row in entries]
                            for identity, entries in normalized.items()}
        for identity in plan:
            audit.require(audit.canonical(values['ts'][identity]) == audit.canonical(values['java'][identity]),
                          name + ' 两侧实际值不同：' + identity)
    result = {'formalAcceptance': False, 'localParityPassed': True, 'cases': 74,
              'samplesCompared': 77, 'assertionsCompared': 77,
              'javaRevision': manifests['java']['sourceRevision'], 'javaWorktree': str(java),
              'manifestSha256': {side: audit.digest(folder / 'manifest.json')
                                 for side, folder in [('ts', ts_folder), ('java', java_folder)]}}
    vectors.write(output, result)
    print(json.dumps(result, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'ts', 'java', 'compare'))
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--ts', type=Path)
    parser.add_argument('--java', type=Path)
    parser.add_argument('--java-worktree', type=Path, default=TASK / 'metanet4j-bsv-sdk')
    args = parser.parse_args()
    plan, java = args.plan.resolve(), args.java_worktree.resolve()
    try:
        if args.command == 'prepare': prepare(plan)
        elif args.command == 'compare': compare(plan, args.ts.resolve(), args.java.resolve(), java, args.output.resolve())
        else: vectors.capture(args.command, args.output.resolve(), plan, java)
    except (ValueError, KeyError, OSError) as error:
        parser.error(str(error))


if __name__ == '__main__':
    main()
