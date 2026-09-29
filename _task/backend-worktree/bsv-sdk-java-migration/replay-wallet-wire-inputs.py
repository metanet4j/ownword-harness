#!/usr/bin/env python3
"""固定 WalletWire 集成测试 82 例的实际帧、随机熵和原断言计划。"""
import argparse
import json
from pathlib import Path

TASK = Path(__file__).resolve().parent
FILE = 'src/wallet/substrates/__tests/WalletWire.integration.test.ts'
JAVA_CLASS = 'com.metanet4j.bsv.wallet.substrates.WalletWireIntegrationTest'
LOOP_METHOD = 'roundTripsAuthenticationAndNetworkMetadata'
LOOP_SITE = FILE + ':83:5:loop'


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def write_rows(path, values):
    Path(path).write_text(''.join(json.dumps(value, ensure_ascii=False, sort_keys=True) + '\n' for value in values))


def source():
    catalog = read(TASK / 'module-tests.json')
    file = next(item for item in catalog['files'] if item['path'] == FILE)
    mapping = read(TASK / 'test-map.json')
    ids = {case['id'] for case in file['cases']}
    mapping['cases'] = [case for case in mapping['cases'] if case['id'] in ids]
    sites = {site['id'] for site in file['sites']}
    mapping['siteReviews'] = [review for review in mapping['siteReviews'] if review['id'] in sites]
    assert len(file['cases']) == len(mapping['cases']) == 82
    return catalog, file, mapping


def assertion_instances(mapped):
    sites = mapped['assertionIds']
    if mapped['java'][0]['name'] != LOOP_METHOD:
        return sites, {site: site for site in sites}
    assert len(sites) == 5
    identities = sites[:4] + [f'{sites[4]}#{index:03d}' for index in range(1, 5)]
    return identities, {identity: sites[position] if position < 4 else sites[4]
                        for position, identity in enumerate(identities)}


def input_plan(frames, entropy, clock, parity):
    _, file, mapping = source()
    frame_rows, entropy_rows, clock_rows, assertions = rows(frames), rows(entropy), rows(clock), rows(parity)
    assert len(frame_rows) == 122 and len(entropy_rows) == 55 and len(clock_rows) == 2 and len(assertions) == 300
    observed = {}
    for row in frame_rows:
        assert row['method'] == 'transmitToWalletUint8Array' and row['line'] > 0
        observed.setdefault((row['test'], row['occurrence']), []).append((row['sequence'], 'frame', row))
    for row in entropy_rows:
        assert row['line'] > 0 and row['length'] * 2 == len(row['bytesHex'])
        observed.setdefault((row['test'], row['occurrence']), []).append((row['sequence'], 'entropy', row))
    for row in clock_rows:
        assert row['line'] > 0 and row['iso'] == '2026-09-27T00:00:00.000Z'
        observed.setdefault((row['test'], row['occurrence']), []).append((row['sequence'], 'clock', row))
    assert len(observed) == 82
    mapped = {case['id']: case for case in mapping['cases']}
    case_occurrences = {}
    result = []
    for case in file['cases']:
        test = ' '.join(case['names'])
        occurrence = case_occurrences.get(test, 0) + 1
        case_occurrences[test] = occurrence
        events = sorted(observed[(test, occurrence)])
        assert [item[0] for item in events] == list(range(1, len(events) + 1))
        checks = [row for row in assertions if (row['test'], row['occurrence']) == (test, occurrence)]
        assert len(checks) == len(assertion_instances(mapped[case['id']])[0])
        assert all(row['pass'] is True for row in checks)
        java = mapped[case['id']]['java']
        assert len(java) == 1 and java[0]['className'] == JAVA_CLASS
        for index, kind, row in events:
            method = row['method'] if kind == 'frame' else 'crypto.getRandomValues' if kind == 'entropy' else 'Date.constructor'
            if kind == 'clock':
                call = {'method': method, 'args': [{'type': 'string', 'value': row['iso']}]}
            else:
                bytes_hex = row['bytesHex']
                call = {'method': method, 'args': [{'type': 'bytes', 'length': len(bytes_hex) // 2,
                                                    'bytesHex': bytes_hex}]}
            state = {'javaMethod': java[0]['name'], 'callIndex': index}
            if kind == 'frame':
                state['wireId'] = row['wireId']
                assert row['callIndex'] > 0
            result.append({'caseId': case['id'],
                           'sampleId': f'{FILE}:{row["line"]}:{method}:case{occurrence}#{index:04d}',
                           'value': {'test': test, 'source': {'file': FILE, 'line': row['line'],
                                                            'occurrence': occurrence},
                                     'preState': state, 'calls': [call]}})
    assert len(result) == 179
    return result


def prepare(args):
    catalog, file, mapping = source()
    inputs = input_plan(args.frames, args.entropy, args.clock, args.parity)
    catalog['files'] = [file]
    catalog['partialImplementationOnly'] = True
    mapped = {case['id']: case for case in mapping['cases']}
    plan = {}
    assertion_index = []
    case_occurrences = {}
    for case in file['cases']:
        method = mapped[case['id']]['java'][0]['name']
        test = ' '.join(case['names'])
        occurrence = case_occurrences.get(test, 0) + 1
        case_occurrences[test] = occurrence
        samples = [row for row in inputs if row['caseId'] == case['id']]
        identities, sites = assertion_instances(mapped[case['id']])
        for ordinal, identity in enumerate(identities, 1):
            assertion_index.append({'caseId': case['id'], 'test': test, 'occurrence': occurrence,
                                    'javaMethod': method, 'ordinal': ordinal, 'assertionId': identity})
        loop_samples = [row['sampleId'] for row in samples if row['value']['calls'][0]['method'] ==
                        'transmitToWalletUint8Array']
        plan[case['id']] = {'sampleIds': [row['sampleId'] for row in samples],
                            'assertionIds': identities, 'assertionSites': sites,
                            'loopSamples': {LOOP_SITE: loop_samples} if method == LOOP_METHOD else {}}
    folder = Path(args.output)
    folder.mkdir(parents=True, exist_ok=True)
    write(folder / 'catalog.json', catalog)
    write(folder / 'mapping.json', mapping)
    write(folder / 'input-plan.json', plan)
    write(folder / 'assertion-index.json', assertion_index)
    write_rows(folder / 'replay-inputs.jsonl', inputs)
    print(json.dumps({'cases': 82, 'frames': 122, 'entropy': 55, 'clock': 2, 'assertions': 300,
                      'output': str(folder)}))


def emit_ts(args):
    """按冻结计划核对本轮 TS 原始帧、熵与时钟，只写输入轨迹；断言由标准发射器输出。"""
    planned = rows(args.plan)
    assert planned == input_plan(args.frames, args.entropy, args.clock, args.parity), '固定 TS 帧、熵与时钟不等于运行前计划'
    write_rows(args.inputs, [dict(row, runId=args.run_id, side='ts') for row in planned])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'emit-ts'))
    for name in ('frames', 'entropy', 'clock', 'parity', 'output', 'plan', 'run-id', 'inputs'):
        parser.add_argument('--' + name, required=name == 'parity')
    args = parser.parse_args()
    {'prepare': prepare, 'emit-ts': emit_ts}[args.action](args)
