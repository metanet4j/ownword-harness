#!/usr/bin/env python3
"""整模块测试清点及证据核对；任何缺失、跳过或差异均返回非零。"""
import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent
SEMANTIC_UPSTREAM = 'f999e0c1aad9a7afd0cbadaaf23841d049af9d5a'
AUTH_WAIT_FILE = 'src/auth/clients/__tests__/AuthFetch.additional.test.ts'
CACHE_FILE = 'src/wallet/__tests/CachedKeyDeriver.test.ts'
RANDOM_FILE = 'src/primitives/__tests/Random.test.ts'
RANDOM_EXTRA_FILE = 'src/primitives/__tests/Random.additional.test.ts'
RANDOM_SHA = '38884385f346d89216c2768d1e46f0e11d3d24e66adad88e8d78365ce6fcc156'
RANDOM_EXTRA_SHA = 'd9011ae424d67daa5e148915ecdcd7374ef937a5d9c7d2e217e4901ef963d625'
DRBG_FILE = 'src/primitives/__tests/DRBG.test.ts'
DRBG_SHA = '8359f4f5fa218206c6be2ecff259a61d290ed989d14ca9d991d5fa4a53b312e9'
DRBG_VECTORS = 'src/primitives/__tests/DRBG.vectors.ts'
DRBG_VECTORS_SHA = 'be1f1971750f3e4ac99bff7a18dce3f3f39ec263d35431eb9c6c5e692fb921b4'
DRBG_GUARD = DRBG_FILE + ':15:9:conditional'
DRBG_THROW = DRBG_FILE + ':16:11:assertion'
DRBG_UNEXECUTED = {DRBG_FILE + ':26:9:assertion', DRBG_FILE + ':27:9:assertion'}
# 固定上游清点器的 ID 算法；仅登记这 15 个固定名称及 occurrence=1。
DRBG_BRANCH_CASES = {hashlib.sha256(json.dumps([DRBG_FILE, ['DRBG', 'NIST vector compatibility',
    f'handles NIST-style vector {index} consistently'], 1], separators=(',', ':')).encode()).hexdigest(): index
    for index in range(15)}
# 每项固定为：文件、源码摘要、站点 → (规则 ID、原 matcher、原边界、执行次数)。
SEMANTIC_CASES = {
    '5e08c3e9cd40aa0723c8bc4888818daf1fee79d866e74c68f6c76194748dc0c7':
        ('src/primitives/__tests/AsyncCryptoBackend.test.ts',
         '7b0c97ba0be75a72fc7d3d2ffc708802553fe9658e6f4b893722504bbb545fe2',
         {'38:7': ('async-ready-null-adapter-v1', 'toBeUndefined', None, 1),
          '42:7': ('async-ready-null-adapter-v1', 'toBeUndefined', None, 1)}),
    '9cb7ee6ed920ce4f9b0822ea4209d7c8f520e334a16e45f7913fdc989025a0be':
        (AUTH_WAIT_FILE, '177e6ca599905a61274e400c0b85d8719526a2e09003ac207b0513a3fb60afc6',
         {'862:11': ('native-null-absence-v1', 'toBeUndefined', None, 1)}),
    '5c6b78e562b2b310489abb962a64b66061f9e2e226acd80d4998b6f2ad8f571f':
        (AUTH_WAIT_FILE, '177e6ca599905a61274e400c0b85d8719526a2e09003ac207b0513a3fb60afc6',
         {'1139:5': ('native-null-absence-v1', 'toBeUndefined', None, 1)}),
    '61b4ecc5ca8e8e0e52d508368744a12c06c31d670ea752d08a5d880a62cf5f63':
        ('src/auth/clients/__tests__/AuthFetch.test.ts',
         '0312c9107dbd4acddab1cd282355090fad28dfe58b0f395b642641cca7654f0a',
         {'293:11': ('auth-payment-log-v1', 'toEqual', 1, 1),
          '299:11': ('auth-payment-log-v1', 'toEqual', 2, 1)}),
    'c6ca731b61455ef1e4c19491a8afb0cee5758584cf6fc79d8009535634b7ccdf':
        (RANDOM_FILE, RANDOM_SHA, {'6:5': ('random-length-v1', 'toHaveLength', 3, 1),
                                  '7:5': ('random-length-v1', 'toHaveLength', 10, 1)}),
    '61c17607ef11ee67bafe1096807885f72b10f33070c22870c32d2e3259c4505b':
        (RANDOM_FILE, RANDOM_SHA, {'12:5': ('random-distinct-v1', 'not.toEqual', 32, 1)}),
    '848124cde9210d75b0dba6c87bb690fceb48e80509981a2248de901d22e61ee6':
        (RANDOM_FILE, RANDOM_SHA, {'17:7': ('random-byte-v1', 'toBeGreaterThanOrEqual', 0, 100),
                                  '18:7': ('random-byte-v1', 'toBeLessThanOrEqual', 255, 100)}),
    'd1c4c7c391647d93d40519c4065a74598d5a1c760b73eec665dcff78b3e92600':
        (RANDOM_FILE, RANDOM_SHA, {str(line) + ':5': ('random-length-v1', 'toHaveLength', size, 1)
                                  for line, size in ((22, 1), (23, 16), (24, 32), (25, 64), (26, 256))}),
    'b00646e1f384f536e1a5d78b958072753e42b772c17ebd79e304900d3b3dcb19':
        (RANDOM_EXTRA_FILE, RANDOM_EXTRA_SHA, {'62:7': ('random-length-v1', 'toHaveLength', 16, 1),
              '64:9': ('random-byte-v1', 'toBeGreaterThanOrEqual', 0, 16),
              '65:9': ('random-byte-v1', 'toBeLessThanOrEqual', 255, 16)}),
    '68dadce6b69efc64e2c3ece1fc81baf3439ece6853b6c8341441748b4c6912ed':
        (RANDOM_EXTRA_FILE, RANDOM_EXTRA_SHA, {'234:7': ('random-length-v1', 'toHaveLength', 8, 1),
              '236:9': ('random-byte-v1', 'toBeGreaterThanOrEqual', 0, 8),
              '237:9': ('random-byte-v1', 'toBeLessThanOrEqual', 255, 8)}),
    '1ccb62346e2135618c6d5ef88233d2d0386fcb3a43d040dbc0c5063181afeddb':
        (RANDOM_EXTRA_FILE, RANDOM_EXTRA_SHA, {str(line) + ':9': ('random-length-v1', 'toHaveLength', 4, 1)
                                              for line in (269, 270, 271)}),
    '7eaf894b954c8a61105fc2ce63e4218989c2a07e1b6d93b23fb4e166540aa553':
        (AUTH_WAIT_FILE, '177e6ca599905a61274e400c0b85d8719526a2e09003ac207b0513a3fb60afc6',
         {'822:5': ('timing-ms-v1', 'toBeLessThan', 50, 1)}),
    '585bb68f6e2a74b0946cdcb6ac5f1d08b90e629cf72f0687aaa401a175bb155e':
        (AUTH_WAIT_FILE, '177e6ca599905a61274e400c0b85d8719526a2e09003ac207b0513a3fb60afc6',
         {'829:5': ('timing-ms-v1', 'toBeLessThan', 50, 1)}),
    '8cafa389ea1819ec6268cd946171ee603bb27f4bdc4a0cab23277aaf37a1abd0':
        (CACHE_FILE, '66fbf8f800232d906dae3fe83736bbaf4875f45e24ae1f5b9283439d4624d698',
         {'405:7': ('timing-ms-v1', 'toBeGreaterThanOrEqual', 50, 1),
          '406:7': ('timing-ms-v1', 'toBeLessThan', 10, 1)}),
}


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def capture_rows(path, identity):
    rows = {}
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        require(isinstance(row.get('caseId'), str) and isinstance(row.get(identity), str) and 'value' in row,
                f'原始采集缺少 caseId、{identity} 或实际值：{path}:{number}')
        rows.setdefault(row['caseId'], []).append(row)
    return rows


def java_revision(repo_paths=None):
    """包含提交及未提交文件，避免新源码沿用旧报告。忽略 Git 已忽略的构建产物。"""
    repo_paths = repo_paths or {}
    snapshot = {}
    for repo in read(TASK / 'workspace.json')['repositories']:
        folder = Path(repo_paths.get(repo['name'], TASK / repo['name']))
        commit = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
        names = subprocess.check_output(['git', '-C', str(folder), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
        snapshot[repo['name']] = {'commit': commit, 'files': {
            name: digest(folder / name) if (folder / name).is_file() else None
            for name in sorted(set(names) - {''})}}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def independent_captures(paths):
    for ts in ('tsInputs', 'tsAssertions'):
        for java in ('javaInputs', 'javaAssertions'):
            require(not Path(paths[ts]).samefile(paths[java]),
                    f'TS/Java 必须独立采集，不能使用同一物理文件：{ts} / {java}')


def semantic_specs(case_id):
    entry = SEMANTIC_CASES.get(case_id)
    return {} if entry is None else {entry[0] + ':' + position + ':assertion': rule
                                    for position, rule in entry[2].items()}


def semantic_number(value):
    require(isinstance(value, dict) and set(value) == {'type', 'value'} and value['type'] == 'number'
            and isinstance(value['value'], str), '语义观测必须保留 number 类型和无损数值字符串')
    require(bool(re.fullmatch(r'-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?', value['value'])),
            '语义观测包含无效数值')
    try:
        result = Decimal(value['value'])
    except InvalidOperation as error:
        raise ValueError('语义观测包含无效数值') from error
    require(result.is_finite(), '语义观测数值必须有限')
    return result


def semantic_bytes(value, length):
    require(isinstance(value, dict) and set(value) == {'type', 'value'} and value['type'] == 'array'
            and isinstance(value['value'], list) and len(value['value']) == length,
            '随机源必须保留原始字节数组及固定长度，不能只上报长度或 pass')
    numbers = [semantic_number(item) for item in value['value']]
    require(all(byte == byte.to_integral_value() and 0 <= byte <= 255 for byte in numbers),
            '随机源观测包含无效字节')
    return numbers


def semantic_payment_log(value, attempt):
    actual = value['actual']
    require(isinstance(actual, dict) and set(actual) == {'type', 'value'} and actual['type'] == 'map'
            and isinstance(actual['value'], dict)
            and set(actual['value']) == {'attempt', 'timestamp', 'message', 'stack'}, '支付失败日志字段不完整或越界')
    fields = actual['value']
    message = f'payment attempt {attempt} failed'
    fixed = {'attempt': {'type': 'number', 'value': str(attempt)},
             'message': {'type': 'string', 'value': message}}
    require(canonical(value['expected']) == canonical({'type': 'map', 'value': fixed})
            and canonical({key: fields[key] for key in fixed}) == canonical(fixed),
            '支付失败日志的固定 attempt/message 或原始预期被修改')
    for key in ('timestamp', 'stack'):
        require(isinstance(fields[key], dict) and set(fields[key]) == {'type', 'value'}
                and fields[key]['type'] == 'string' and isinstance(fields[key]['value'], str),
                f'支付失败日志 {key} 必须保留原始字符串')
    timestamp, stack = fields['timestamp']['value'], fields['stack']['value']
    require(bool(re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z', timestamp)), '支付失败日志时间戳格式错误')
    datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    frames = stack.splitlines()
    require(len(frames) > 1 and frames[0].endswith(message) and any(frame.strip() for frame in frames[1:]),
            '支付失败日志堆栈未保留错误消息及调用帧')


def validate_semantic_observations(case_id, expected, rows):
    specs = semantic_specs(case_id)
    byte_sites = [site for site, spec in specs.items() if spec[0] == 'random-byte-v1']
    if not byte_sites:
        return
    actual = {site: [semantic_number(row['value']['actual']) for row in rows
                     if expected['assertionSites'][row['id']] == site] for site in byte_sites}
    require(all(values == actual[byte_sites[0]] for values in actual.values()),
            f'同一随机字节在不同边界断言中的原始观测不一致：{case_id}')
    for row in rows:
        spec = specs.get(expected['assertionSites'][row['id']])
        if spec and spec[0] == 'random-length-v1':
            require(semantic_bytes(row['value']['actual'], spec[2]) == actual[byte_sites[0]],
                    f'随机源长度断言与逐字节断言不来自同一数组：{case_id}')


def validate_branch_plan(catalog, case_id, source, expected):
    exclusions = expected.get('unexecutedSites', {})
    require(isinstance(exclusions, dict), f'未执行断言证明格式无效：{case_id}')
    if case_id not in DRBG_BRANCH_CASES:
        require(not exclusions, f'没有已核验的固定分支规则，不能豁免断言：{case_id}')
        return set()
    require(catalog['upstreamCommit'] == SEMANTIC_UPSTREAM and source['path'] == DRBG_FILE
            and source.get('sha256') == DRBG_SHA
            and catalog.get('moduleFiles', {}).get(DRBG_VECTORS) == DRBG_VECTORS_SHA,
            f'分支规则与固定测试或向量来源不符：{case_id}')
    same_keys(DRBG_UNEXECUTED, exclusions, f'DRBG 固定提前返回后的未执行站点 {case_id}')
    require(DRBG_GUARD in {site['id'] for site in source['sites'] if site['kind'] == 'conditional'},
            '固定分支证明缺少原条件站点')
    require(list(expected['assertionSites'].values()) == [DRBG_THROW],
            'DRBG 固定无效向量必须实际执行原异常断言，不能伪造其他断言')
    sample_ids = set()
    for proof in exclusions.values():
        require(isinstance(proof, dict) and set(proof) == {'ruleId', 'guardSiteId', 'sampleId'}
                and proof['ruleId'] == 'drbg-nist-invalid-input-v1' and proof['guardSiteId'] == DRBG_GUARD
                and proof['sampleId'] in expected['sampleIds'], '未执行理由必须绑定固定规则、条件和实际样本')
        sample_ids.add(proof['sampleId'])
    require(len(sample_ids) == 1, '同一次提前返回须引用同一份分支观测')
    return set(exclusions)


def validate_branch_observations(case_id, expected, samples, rows):
    if case_id not in DRBG_BRANCH_CASES:
        return
    config = read(TASK / 'workspace.json')['upstream']
    fixture = TASK.parents[2] / config['path'] / config['packagePath'] / DRBG_VECTORS
    require(digest(fixture) == DRBG_VECTORS_SHA, 'DRBG 固定向量文件发生变化')
    vectors = re.findall(r"entropy: '([0-9a-f]+)',\s*nonce: '([0-9a-f]+)'", fixture.read_text())
    require(len(vectors) == 15, 'DRBG 固定向量格式或数量发生变化')
    entropy, nonce = vectors[DRBG_BRANCH_CASES[case_id]]
    sample_id = next(iter(expected['unexecutedSites'].values()))['sampleId']
    values = [sample['value'] for sample in samples if sample['sampleId'] == sample_id]
    require(len(values) == 1, '未执行断言缺少唯一实际分支样本')
    actual = values[0]
    require(isinstance(actual, dict) and set(actual) == {'kind', 'guardSiteId', 'entropyHex', 'nonceHex', 'taken', 'controlFlow'}
            and actual['kind'] == 'branch' and actual['guardSiteId'] == DRBG_GUARD
            and actual['entropyHex'] == entropy and actual['nonceHex'] == nonce,
            '未执行断言的实际输入不对应固定向量，不能捏造分支理由')
    predicate = len(bytes.fromhex(actual['entropyHex'])) != 32 or len(bytes.fromhex(actual['nonceHex'])) != 32
    require(predicate and actual['taken'] is True and actual['controlFlow'] == 'return',
            '原条件没有证明提前返回，不能删除后续断言')
    require(len(rows) == 1 and expected['assertionSites'][rows[0]['id']] == DRBG_THROW,
            '固定分支缺少实际异常断言')
    observation = rows[0]['value']
    require(isinstance(observation, dict) and observation.get('kind') == 'assertion'
            and observation.get('matcher') == 'toThrow' and observation.get('negated') is False
            and observation.get('pass', True) is True and observation.get('expected') == {'type': 'undefined'},
            '固定分支必须保留原 toThrow 观察，pass 不能代替执行')
    thrown = observation.get('actual')
    require(isinstance(thrown, dict) and thrown.get('kind') == 'throw'
            and isinstance(thrown.get('name'), str) and bool(thrown['name'])
            and isinstance(thrown.get('message'), str), '固定分支未观察到实际异常')


def compare_actuals(case_id, expected, identity, left, right):
    rule = semantic_specs(case_id).get(expected['assertionSites'][identity]) if expected else None
    if rule is None:
        require(canonical(left) == canonical(right), f'实际结果不一致：{case_id} / {identity}')
        return
    rule_id, matcher, boundary, _ = rule
    if rule_id in ('async-ready-null-adapter-v1', 'native-null-absence-v1'):
        for side, value, actual, original_matcher, original_expected in (
                ('TS', left, {'type': 'undefined'}, 'toBeUndefined', []),
                ('Java', right, {'type': 'null'},
                 'toBeUndefined' if rule_id == 'async-ready-null-adapter-v1' else 'toBeNull',
                 [] if rule_id == 'async-ready-null-adapter-v1' else {'type': 'array', 'value': []})):
            require(isinstance(value, dict) and set(value) ==
                    {'kind', 'matcher', 'negated', 'actual', 'expected', 'pass'}
                    and value['kind'] == 'assertion' and value['matcher'] == original_matcher
                    and value['negated'] is False and value['pass'] is True
                    and value['actual'] == actual and value['expected'] == original_expected,
                    f'固定 Java null 适配 {side} 必须保留 undefined/null 实际观测：{identity}')
        return
    for value in (left, right):
        require(isinstance(value, dict) and value.get('kind') == 'assertion'
                and value.get('matcher') == matcher and value.get('negated') is matcher.startswith('not.')
                and value.get('pass', True) is True and 'actual' in value and 'expected' in value,
                f'有界语义缺少原 matcher、实际观测或预期；pass 标记不能代替断言：{identity}')
        if rule_id == 'timing-ms-v1':
            actual, bound = semantic_number(value['actual']), semantic_number(value['expected'])
            require(bound == boundary and actual >= 0, f'耗时断言的固定边界或实际值无效：{identity}')
            valid = actual < bound if matcher == 'toBeLessThan' else actual >= bound
            require(valid, f'实际耗时不满足固定原断言：{identity}')
        elif rule_id == 'random-length-v1':
            require(semantic_number(value['expected']) == boundary, f'随机长度预期被修改：{identity}')
            semantic_bytes(value['actual'], boundary)
        elif rule_id == 'random-distinct-v1':
            require(semantic_bytes(value['actual'], boundary) != semantic_bytes(value['expected'], boundary),
                    f'两次随机调用实际字节相同：{identity}')
        elif rule_id == 'random-byte-v1':
            actual = semantic_number(value['actual'])
            require(semantic_number(value['expected']) == boundary and actual == actual.to_integral_value()
                    and 0 <= actual <= 255, f'随机字节实际值或固定边界无效：{identity}')
        elif rule_id == 'auth-payment-log-v1':
            semantic_payment_log(value, boundary)
        else:
            raise ValueError(f'未实现的固定语义规则：{rule_id}')


def validate_plan(catalog, mapping, plan):
    cases = {case['id']: file for file in catalog['files'] for case in file['cases']}
    mapped = {case['id']: case for case in mapping['cases']}
    same_keys(cases, plan, '独立输入/断言计划用例')
    expected_sites = {site['id'] for file in catalog['files'] for site in file['sites']
                      if site['kind'] == 'assertion'}
    expected_loops = {site['id'] for file in catalog['files'] for site in file['sites']
                      if site['kind'] == 'loop'}
    covered_sites, covered_loops = set(), set()
    for case_id, expected in plan.items():
        samples, assertions = expected.get('sampleIds'), expected.get('assertionIds')
        for values, label in ((samples, '样本'), (assertions, '断言')):
            require(isinstance(values, list) and bool(values)
                    and all(isinstance(value, str) and bool(value) for value in values)
                    and len(values) == len(set(values)), f'独立{label}计划无效：{case_id}')
        sites = expected.get('assertionSites')
        require(isinstance(sites, dict), f'计划缺少冻结断言站点关联：{case_id}')
        same_keys(assertions, sites, f'断言实例与冻结断言站点关联 {case_id}')
        file_sites = {site['id'] for site in cases[case_id]['sites'] if site['kind'] == 'assertion'}
        require(all(isinstance(site, str) and site in file_sites for site in sites.values()),
                f'计划断言必须关联本文件的冻结断言站点：{case_id}')
        rules = expected.get('comparisonRules', {})
        require(isinstance(rules, dict) and set(rules) <= set(assertions), f'语义规则引用未知断言实例：{case_id}')
        fixed_rules = semantic_specs(case_id)
        if fixed_rules:
            source, source_sha, _ = SEMANTIC_CASES[case_id]
            require(catalog['upstreamCommit'] == SEMANTIC_UPSTREAM and cases[case_id]['path'] == source
                    and cases[case_id].get('sha256') == source_sha,
                    f'语义规则与固定上游源码不符：{case_id}')
        for identity in assertions:
            rule = fixed_rules.get(sites[identity])
            require(rules.get(identity) == (rule[0] if rule else None),
                    f'断言缺少固定语义规则或试图扩大适用范围：{case_id} / {identity}')
        counts = Counter(sites.values())
        for site, rule in fixed_rules.items():
            require(counts[site] == rule[3], f'固定语义断言执行次数不符：{case_id} / {site}')
        mapped_sites = []
        for identity in mapped[case_id]['assertionIds']:
            require(identity in file_sites or identity in sites,
                    f'映射中的断言实例未列入独立计划：{case_id} / {identity}')
            mapped_sites.append(identity if identity in file_sites else sites[identity])
        require(list(dict.fromkeys(sites[identity] for identity in assertions)) == list(dict.fromkeys(mapped_sites)),
                f'映射断言站点与独立计划的执行顺序不符：{case_id}')
        covered_sites.update(sites.values())
        covered_sites.update(validate_branch_plan(catalog, case_id, cases[case_id], expected))
        loops = expected.get('loopSamples', {})
        require(isinstance(loops, dict), f'循环样本计划无效：{case_id}')
        file_loops = {site['id'] for site in cases[case_id]['sites'] if site['kind'] == 'loop'}
        require(set(loops) <= file_loops, f'循环样本必须关联本文件的冻结循环站点：{case_id}')
        for site, ids in loops.items():
            require(isinstance(ids, list) and bool(ids) and all(isinstance(x, str) for x in ids)
                    and len(ids) == len(set(ids)) and set(ids) <= set(samples),
                    f'冻结循环站点缺少完整输入样本：{case_id} / {site}')
            covered_loops.add(site)
    same_keys(expected_sites, covered_sites, '冻结断言站点覆盖')
    same_keys(expected_loops, covered_loops, '冻结循环站点覆盖')


def runtime_provenance(args, catalog, paths):
    """校验执行器在运行前固定、运行后封存的来源；打包器无权追认旧文件。"""
    manifests = {}
    hashes = {}
    for side in ('ts', 'java'):
        path = getattr(args, side + '_run_manifest', None)
        require(bool(path), f'缺少 {side} 运行来源 manifest；须由 capture 包装真实执行后生成，不能追认旧报告')
        manifest = read(path)
        require(manifest.get('schemaVersion') == 1 and manifest.get('side') == side,
                f'{side} 运行来源 manifest 格式或侧别无效')
        require(not manifest.get('captureError'), f'{side} 采集失败：{manifest.get("captureError")}')
        require(isinstance(manifest.get('runId'), str)
                and bool(re.fullmatch(r'[0-9a-f]{32}', manifest['runId'])), f'{side} 运行身份无效')
        require(manifest.get('producerSha256') == digest(TASK / 'evidence-bundle.py'),
                f'{side} 运行来源不是当前 capture 执行器产生')
        require(manifest.get('upstreamCommit') == catalog['upstreamCommit'], f'{side} 运行的固定上游版本不同')
        for key, artifact in (('catalogSha256', args.catalog), ('mappingSha256', args.mapping),
                              ('inputPlanSha256', paths['inputPlan'])):
            require(manifest.get(key) == digest(artifact), f'{side} 运行前固定的清单、映射或输入计划已变化：{key}')
        command = manifest.get('command')
        require(isinstance(command, list) and bool(command)
                and all(isinstance(part, str) and bool(part) for part in command), f'{side} 运行命令缺失')
        require(type(manifest.get('exitCode')) is int and manifest['exitCode'] == 0,
                f'{side} 运行未完成或退出状态非零')
        require(type(manifest.get('startedAtNs')) is int and type(manifest.get('finishedAtNs')) is int
                and 0 < manifest['startedAtNs'] <= manifest['finishedAtNs'], f'{side} 运行时间记录不完整')
        require(isinstance(manifest.get('sourceRevision'), str) and bool(manifest['sourceRevision'])
                and manifest['sourceRevision'] == manifest.get('sourceRevisionAfter'),
                f'{side} 运行中源码版本变化或版本记录缺失')
        if side == 'ts':
            require(manifest['sourceRevision'] == catalog['upstreamCommit'], 'TS 运行来源不是固定上游版本')
        else:
            require('clean' in command and 'test' in command
                    and command.index('clean') < command.index('test')
                    and not any(re.search(r'skipTests|maven\.test\.skip|testFailureIgnore|failIfNoTests=false', part)
                                for part in command), 'Java 运行必须是未跳过测试的 clean test')
        for suffix, field in (('Inputs', 'inputsSha256'), ('Assertions', 'assertionsSha256')):
            require(manifest.get(field) == digest(paths[side + suffix]), f'{side} 运行原始采集校验值不同：{field}')
            for rows in capture_rows(paths[side + suffix], 'sampleId' if suffix == 'Inputs' else 'assertionId').values():
                require(all(row.get('runId') == manifest['runId'] and row.get('side') == side for row in rows),
                        f'{side} 原始采集运行身份或侧别不符；禁止复制、重放其他运行轨迹')
        require(manifest.get('reportSha256') == sorted(digest(p) for p in getattr(args, side + '_report')),
                f'{side} 运行原始报告校验值不同')
        log = manifest.get('logPath')
        require(isinstance(log, str) and bool(log), f'{side} 运行日志缺失')
        require(manifest.get('logSha256') == digest(Path(path).parent / log), f'{side} 运行日志校验值不同')
        manifests[side], hashes[side] = manifest, digest(path)
    require(manifests['ts']['runId'] != manifests['java']['runId'], 'TS/Java 必须具有独立运行身份')
    revision = manifests['java']['sourceRevision']
    if getattr(args, 'java_revision', None):
        require(args.java_revision == revision, 'Java 运行来源版本与要求不同；禁止用打包参数重写旧执行版本')
    return revision, hashes


def indexed(rows, key, label):
    result = {}
    for row in rows:
        identity = key(row)
        require(identity not in result, f'{label}重复：{identity}')
        result[identity] = row
    return result


def same_keys(expected, actual, label):
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    require(not missing and not extra,
            f'{label}：缺失 {len(missing)}，多余 {len(extra)}；'
            f'缺失示例 {sorted(missing)[:8]}；多余示例 {sorted(extra)[:8]}')


def compare_ts(catalog, report_paths):
    files = indexed(catalog['files'], lambda f: f['path'], '上游文件')
    require(bool(files), '禁止使用空清单通过 TS 验收')
    require(all(f['cases'] for f in files.values()), '禁止使用空用例通过 TS 验收')
    actual_ts = {}
    for report_path in report_paths:
        report = read(report_path)
        require(report.get('success') is True, f'TS 报告未全部成功：{report_path}')
        count = sum(len(f['assertionResults']) for f in report['testResults'])
        require(report['numTotalTests'] == report['numPassedTests'] == count
                and all(report[k] == 0 for k in ('numFailedTests', 'numPendingTests', 'numTodoTests')),
                f'TS 报告汇总与实际用例矛盾：{report_path}')
        for file in report['testResults']:
            name = file['name'].replace('\\', '/')
            matches = [p for p in files if name == p or name.endswith('/' + p)]
            require(len(matches) == 1, f'TS 报告存在范围外文件：{name}')
            name = matches[0]
            require(name not in actual_ts, f'TS 报告文件重复：{name}')
            require(file['status'] == 'passed', f'TS 文件未通过：{name}')
            actual_ts[name] = file['assertionResults']
    same_keys(files, actual_ts, 'TS 实际执行文件')
    for name, file in files.items():
        expected = Counter(tuple(c['names']) for c in file['cases'])
        executed = Counter(tuple(c['ancestorTitles'] + [c['title']]) for c in actual_ts[name])
        require(expected == executed, f'TS 实际用例/参数行不一致：{name}')
        require(all(c['mode'] == 'run' for c in file['cases']), f'存在 skip/todo/only 用例：{name}')
        require(all(c['status'] == 'passed' for c in actual_ts[name]), f'TS 存在失败/跳过/未执行：{name}')
    return {'files': len(files), 'cases': sum(len(f['cases']) for f in files.values())}


def compare(args):
    catalog, mapping = read(args.catalog), read(args.mapping)
    selected = set(args.module or catalog['modules'])
    require(selected <= set(catalog['modules']), '只能选择冻结清单中的完整模块')
    require(all(set(catalog['moduleDependencies'][m]) <= selected for m in selected), '阶段必须包含依赖模块的累计验收；循环依赖需联合验收')
    if args.module:
        all_ids = {c['id'] for f in catalog['files'] for c in f['cases']}
        require(all(c['id'] in all_ids for c in mapping['cases']), '映射包含未知上游用例')
        # 只按整目录过滤，不提供按文件、测试名或函数裁剪的入口。
        catalog['files'] = [f for f in catalog['files'] if f.get('module', f['path'].split('/')[1]) in selected]
        selected_ids = {c['id'] for f in catalog['files'] for c in f['cases']}
        selected_sites = {s['id'] for f in catalog['files'] for s in f['sites']}
        mapping['cases'] = [c for c in mapping['cases'] if c['id'] in selected_ids]
        mapping['siteReviews'] = [r for r in mapping['siteReviews'] if r['id'] in selected_sites]
    files = indexed(catalog['files'], lambda f: f['path'], '上游文件')
    cases = indexed([dict(c, file=f['path']) for f in files.values() for c in f['cases']], lambda c: c['id'], '上游用例')
    require(bool(files) and bool(cases), '禁止使用空清单通过验收')
    require(mapping['upstreamCommit'] == catalog['upstreamCommit'], '映射的上游版本不一致')
    mapped = indexed(mapping['cases'], lambda c: c['id'], 'Java 映射')
    same_keys(cases, mapped, '未映射上游用例')
    java_owners = {}
    for key, case in mapped.items():
        require(bool(case['java']) and bool(case['assertionIds']), f'缺少 Java 测试或断言映射：{key}')
        require(len(set(case['assertionIds'])) == len(case['assertionIds']), f'断言标识重复：{key}')
        for java in case['java']:
            identity = (java['className'], java['name'])
            require(identity not in java_owners, f'Java 用例被重复用于多个映射：{identity}')
            java_owners[identity] = key
    sites = {s['id'] for f in files.values() for s in f['sites']}
    reviews = indexed(mapping['siteReviews'], lambda r: r['id'], '源码语义复核')
    same_keys(sites, reviews, '注册点、断言、循环与条件分支复核')
    for key, review in reviews.items():
        require(review['status'] == 'reviewed' and bool(review['note']) and bool(review['caseIds']), f'源码语义未复核：{key}')
        require(set(review['caseIds']) <= set(cases), f'源码复核引用未知用例：{key}')
    compare_ts(catalog, args.ts_report)
    actual_java = {}
    for report_path in args.java_report:
        root = ET.parse(report_path).getroot()
        require(root.tag in ('testsuite', 'testsuites'), f'Surefire XML 根节点无效：{report_path}')
        suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
        require(bool(suites) and len(suites) == len(list(root.iter('testsuite'))),
                f'Surefire XML 缺少有效 testsuite 或存在嵌套 suite：{report_path}')
        testcases = [case for suite in suites for case in suite.findall('testcase')]
        require(len(testcases) == len(list(root.iter('testcase'))),
                f'Surefire testcase 不属于直接 testsuite：{report_path}')
        for suite in suites:
            require(all(int(suite.get(k, '0')) == 0 for k in ('failures', 'errors', 'skipped')), f'Java 报告包含失败/跳过：{report_path}')
            require(int(suite.attrib['tests']) == len(list(suite.iter('testcase'))), f'Java 报告汇总与实际用例矛盾：{report_path}')
        for case in testcases:
            identity = (case.attrib['classname'], case.attrib['name'])
            require(identity not in actual_java, f'Java 实际执行记录重复：{identity}')
            require(not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped')), f'Java 用例未通过：{identity}')
            actual_java[identity] = case
    missing = set(java_owners) - set(actual_java)
    require(not missing, f'Java 未实际执行 {len(missing)} 个映射用例：{sorted(missing)[:8]}')
    observations = read(args.observations)
    require(observations['upstreamCommit'] == catalog['upstreamCommit'] and bool(observations['javaRevision']), '结果缺少匹配的代码版本')
    if args.java_revision:
        require(observations['javaRevision'] == args.java_revision, '结果来自不同的 Java 源码版本')
    require(observations['catalogSha256'] == digest(args.catalog), '结果与用例清单不匹配')
    for name, paths in [('tsReportSha256', args.ts_report), ('javaReportSha256', args.java_report)]:
        require(sorted(observations[name]) == sorted(digest(p) for p in paths), f'结果与原始报告校验值不匹配：{name}')
    capture_names = {'inputPlan': 'input_plan', 'tsInputs': 'ts_inputs', 'javaInputs': 'java_inputs',
                     'tsAssertions': 'ts_assertions', 'javaAssertions': 'java_assertions'}
    capture_paths = {name: getattr(args, option, None) for name, option in capture_names.items()}
    if getattr(args, 'command', 'compare') == 'check' or observations.get('captureSha256') is not None or any(capture_paths.values()):
        require(all(capture_paths.values()) and isinstance(observations.get('captureSha256'), dict),
                '完整验收缺少两端原始采集、独立输入/断言计划或校验值')
        require(set(observations['captureSha256']) == set(capture_names), '原始采集文件清单不完整')
        independent_captures(capture_paths)
        for name, path in capture_paths.items():
            require(observations['captureSha256'][name] == digest(path), f'原始采集校验值不匹配：{name}')
        plan = read(capture_paths['inputPlan'])
        validate_plan(catalog, mapping, plan)
        raw_captures = {name: capture_rows(capture_paths[name], identity) for name, identity in (
            ('tsInputs', 'sampleId'), ('javaInputs', 'sampleId'),
            ('tsAssertions', 'assertionId'), ('javaAssertions', 'assertionId'))}
        for name, rows in raw_captures.items():
            same_keys(cases, rows, f'{name} 原始采集用例')
        revision, run_hashes = runtime_provenance(args, catalog, capture_paths)
        require(observations['javaRevision'] == revision, '汇总 Java 版本与实际运行来源不符')
        require(observations.get('runManifestSha256') == run_hashes, '汇总运行 manifest 校验值不符')
    observed = indexed(observations['cases'], lambda c: c['id'], '逐用例结果')
    same_keys(cases, observed, '逐用例结果')
    assertion_count = 0
    for key, observation in observed.items():
        require(bool(re.fullmatch(r'[0-9a-f]{64}', observation['inputSha256'])), f'缺少输入/前置状态校验值：{key}')
        require(observation['inputSha256'] == observation['tsInputSha256'] == observation['javaInputSha256'], f'TS/Java 输入或前置状态不同：{key}')
        if capture_paths['inputPlan']:
            samples = observation.get('inputSamples')
            require(isinstance(samples, dict) and set(samples) == {'TS', 'Java'}, f'缺少两端实际输入样本：{key}')
            for side in ('TS', 'Java'):
                require([row['sampleId'] for row in samples[side]] == plan[key]['sampleIds'],
                        f'{side} 输入样本数量、顺序或 ID 不符：{key}')
                raw = raw_captures['tsInputs' if side == 'TS' else 'javaInputs'][key]
                require(canonical(samples[side]) == canonical([{'sampleId': row['sampleId'], 'value': row['value']} for row in raw]),
                        f'{side} 汇总输入与原始采集不同：{key}')
                require(hashlib.sha256(canonical(samples[side]).encode()).hexdigest() == observation['inputSha256'],
                        f'{side} 实际输入样本与摘要不符：{key}')
        ts = indexed(observation['ts'], lambda a: a['id'], 'TS 断言结果')
        java = indexed(observation['java'], lambda a: a['id'], 'Java 断言结果')
        expected_ids = plan[key]['assertionIds'] if capture_paths['inputPlan'] else mapped[key]['assertionIds']
        same_keys(expected_ids, ts, f'TS 断言结果 {key}')
        same_keys(expected_ids, java, f'Java 断言结果 {key}')
        if capture_paths['inputPlan']:
            for side, actual in [('tsAssertions', observation['ts']), ('javaAssertions', observation['java'])]:
                raw = raw_captures[side][key]
                require([row['assertionId'] for row in raw] == plan[key]['assertionIds'],
                        f'{side} 原始断言数量、顺序或 ID 不符：{key}')
                require(canonical(actual) == canonical([{'id': row['assertionId'], 'value': row['value']} for row in raw]),
                        f'{side} 汇总断言与原始采集不同：{key}')
        for identity in ts:
            # JSON 类型必须保留，不能把 true 当作数值 1，或丢掉字节前导零。
            compare_actuals(key, plan[key] if capture_paths['inputPlan'] else None,
                           identity, ts[identity]['value'], java[identity]['value'])
            assertion_count += 1
        if capture_paths['inputPlan']:
            validate_semantic_observations(key, plan[key], observation['ts'])
            validate_semantic_observations(key, plan[key], observation['java'])
            for side, label in (('ts', 'TS'), ('java', 'Java')):
                validate_branch_observations(key, plan[key], observation['inputSamples'][label], observation[side])
    return {'files': len(files), 'cases': len(cases), 'javaCases': len(java_owners),
            'comparedAssertions': assertion_count,
            'justifiedUnexecutedAssertions': sum(len(case.get('unexecutedSites', {})) for case in plan.values())
                if capture_paths['inputPlan'] else 0,
            'formalAcceptance': getattr(args, 'command', 'compare') == 'check'}


def collect():
    config, scope = read(TASK / 'workspace.json'), read(TASK / 'module-scope.json')
    upstream = TASK.parents[2] / config['upstream']['path']
    sdk = upstream / config['upstream']['packagePath']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['upstream']['commit'] == scope['upstreamCommit'], '上游固定版本不匹配')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(), '上游工作区存在修改')
    modules = scope['selectedModules']
    available = {p.name for p in (sdk / 'src').iterdir() if p.is_dir() and not p.name.startswith('__')}
    reviews = scope.get('moduleReviews', {})
    require(set(reviews) <= available, '范围复核包含未知模块')
    for module, review in reviews.items():
        require(review.get('decision') in ('selected', 'excluded') and bool(review.get('reason'))
                and bool(review.get('evidence')), f'模块范围缺少结论或依据：{module}')
        require((review['decision'] == 'selected') == (module in modules), f'模块范围结论与已选列表矛盾：{module}')
    require(bool(modules) and len(set(modules)) == len(modules), '模块列表为空或重复')
    require(all(re.fullmatch(r'[a-z][a-z0-9-]*', m) and (sdk / 'src' / m).is_dir() for m in modules), '只接受完整顶层模块名，禁止文件/方法过滤')
    all_files = sorted(p for m in modules for p in (sdk / 'src' / m).rglob('*') if p.is_file())
    cross = {p.relative_to(sdk).as_posix(): p for d in (sdk / 'src').iterdir()
             if d.is_dir() and d.name.startswith('__') for p in d.rglob('*.test.ts')}
    owners = scope.get('crossModuleTestOwners', {})
    require(set(owners) <= set(cross), '跨目录测试归属包含未知文件')
    for name, owner in owners.items():
        require(bool(owner['reason']) and bool(re.fullmatch(r'[a-z][a-z0-9-]*', owner['module']))
                and (sdk / 'src' / owner['module']).is_dir(), f'跨目录归属无效：{name}')
        if owner['module'] in modules:
            all_files.append(cross[name])
    all_files.sort()
    tests = [p.relative_to(sdk).as_posix() for p in all_files if re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', p.name)]
    require(bool(tests), '选中模块没有测试文件')
    with tempfile.TemporaryDirectory(prefix='bsv-census-') as tmp:
        output = Path(tmp) / 'cases.json'
        subprocess.run([config['tools']['node'], str(TASK / 'collect-cases.cjs'), '--sdk', str(sdk), '--output', str(output), *tests], check=True)
        result = read(output)
    result['moduleDependencies'] = {m: result['moduleDependencies'][m] for m in modules}
    for file in result['files']:
        file['module'] = owners[file['path']]['module'] if file['path'] in owners else file['path'].split('/')[1]
    result.update({
        'upstreamCommit': commit, 'scopeSha256': digest(TASK / 'module-scope.json'),
        'modules': modules,
        'moduleFiles': {p.relative_to(sdk).as_posix(): digest(p) for p in all_files},
        'pendingModules': sorted(available - set(reviews)),
        'excludedModules': sorted(m for m, r in reviews.items() if r['decision'] == 'excluded'),
        'crossModuleTestOwners': owners,
        'crossModuleTestsPending': sorted(set(cross) - set(owners)),
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('revision', help='生成已登记 Java 仓库当前提交及工作树文件摘要，供真实结果采集记录')
    inventory = sub.add_parser('inventory', help='清点所有已选整模块，含参数化/循环注册与 manual 文件；不执行测试体')
    inventory.add_argument('--output', default=str(TASK / 'module-tests.json'))
    ts_only = sub.add_parser('compare-ts', help='仅核对 TS 原始报告与完整冻结清单；不代表 Java 迁移或最终 check 通过')
    ts_only.add_argument('--catalog', default=str(TASK / 'module-tests.json'))
    ts_only.add_argument('--ts-report', action='append', required=True)
    for name in ('compare', 'check'):
        command = sub.add_parser(name, help='compare 核对所给证据；check 额外重新清点固定上游并核对冻结范围')
        command.add_argument('--catalog', default=str(TASK / 'module-tests.json'))
        command.add_argument('--mapping', default=str(TASK / 'test-map.json'))
        command.add_argument('--ts-report', action='append', default=[])
        command.add_argument('--java-report', action='append', default=[])
        command.add_argument('--observations', default=str(TASK / '.cache/evidence/parity-results.json'))
        command.add_argument('--module', action='append', default=[], help='整模块累计验收，可重复；默认全部已选模块')
        command.add_argument('--java-revision', help='compare 调试时核对源码摘要；check 始终从当前 Java 工作树重新计算')
        for name in ('input-plan', 'ts-inputs', 'java-inputs', 'ts-assertions', 'java-assertions'):
            command.add_argument('--' + name)
        for side in ('ts', 'java'):
            command.add_argument('--' + side + '-run-manifest')
    args = parser.parse_args()
    try:
        if args.command == 'revision':
            print(json.dumps({'javaRevision': java_revision()}))
        elif args.command == 'compare-ts':
            print(json.dumps({'status': 'PASS', 'check': 'compare-ts', **compare_ts(read(args.catalog), args.ts_report)}))
        elif args.command == 'inventory':
            result = collect()
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({'modules': result['modules'], 'sourceAndTestFiles': len(result['moduleFiles']), 'testFiles': len(result['files']), 'cases': sum(len(f['cases']) for f in result['files'])}, ensure_ascii=False))
        else:
            if args.command == 'check':
                current = collect()
                require(current == read(args.catalog), '冻结清单与重新清点不一致：存在源码/测试/参数行/模块范围漂移；禁止直接覆盖后当作通过')
                args.java_revision = java_revision()
            result = compare(args)
            if args.command == 'check':
                require(read(TASK / 'module-scope.json')['scopeReview'] == 'reviewed', '依赖模块及跨目录测试归属尚未审查完成')
                require(not current['pendingModules'], '存在未逐项决定范围的候选模块')
                require(not current['crossModuleTestsPending'], '跨目录用例仍待归属，不能仅修改 reviewed 标志通过验收')
            print(json.dumps({'status': 'PASS', 'check': args.command, **result}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
