#!/usr/bin/env python3
"""核验原规模 AES-GCM manual 证据，并汇总 Symmetric 任务的真实对照。"""

import argparse
import hashlib
import json
import re
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TS_ROOT = ROOT / '../../../reference/ts-stack/packages/sdk'
SIZE = 536_870_928
MANUAL = 'src/primitives/__tests/AESGCM.man.test.ts'
MANUAL_ID = 'c448b39dc316558c9ba122c1b2f4314d02bc8e8fdc81d127bf169ff72af87f43'
MANUAL_NAME = 'AESGCM resource-intensive boundary handles ciphertext longer than 2^32 bits'
TS_SHA = 'd77d292dd287c2f0903a009edc6acdf30593aa529072c6f68a910568ca1054db'
ZERO_SHA = '34c717d4ef502ab2c9c08d46d3e9572b31847f0c55c0b44c2ec68410984fc458'
CIPHER_SHA = 'a70609c67d9f189d33288271772f57c5d3f64ce48897f85354d850d581f24ae9'
TAG = '158631e7c82bc5af4939f5757faa8051'
JAVA_CLASS = 'com.metanet4j.bsv.primitives.AESGCMManualTest'
JAVA_METHOD = 'handlesCiphertextLongerThanTwoToThirtyTwoBits'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def read(path):
    return json.loads(path.read_text())


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def check_jest(path, count, suites, expected_file=None):
    data = read(path)
    for field, expected in [('success', True), ('numTotalTests', count), ('numPassedTests', count),
                            ('numFailedTests', 0), ('numPendingTests', 0),
                            ('numTotalTestSuites', suites), ('numPassedTestSuites', suites)]:
        require(data.get(field) == expected, f'{path}: {field} 应为 {expected}')
    require(sum(len(s['assertionResults']) for s in data['testResults']) == count,
            f'{path}: 原用例结果数量错误')
    require(all(s['status'] == 'passed' and all(t['status'] == 'passed' for t in s['assertionResults'])
                for s in data['testResults']), f'{path}: 存在未通过结果')
    if expected_file:
        suite = data['testResults'][0]
        require(suite['name'] == str(expected_file.resolve()), f'{path}: 原文件路径不符')
        case = suite['assertionResults'][0]
        require(case['fullName'] == MANUAL_NAME and case['numPassingAsserts'] == 3,
                f'{path}: manual 用例或 3 条 Jest 断言不符')


def check_xml(path, summary):
    suite = ET.parse(path).getroot()
    require(suite.tag == 'testsuite', f'{path}: 并非 Surefire testsuite')
    for field, expected in [('tests', '1'), ('errors', '0'), ('failures', '0'), ('skipped', '0')]:
        require(suite.get(field) == expected, f'{path}: {field} 应为 {expected}')
    case = suite.findall('testcase')
    require(len(case) == 1 and case[0].get('classname') == JAVA_CLASS
            and case[0].get('name') == JAVA_METHOD and len(case[0]) == 0,
            f'{path}: 原 Java manual 测试用例不符')
    properties = {p.get('name'): p.get('value') for p in suite.findall('./properties/property')}
    require(properties.get('migration.symmetric.manual.output') == str(summary.resolve()),
            f'{path}: Surefire 参数未指向本次 summary')


def check_manual(args):
    source = TS_ROOT / MANUAL
    require(sha(source) == TS_SHA, '固定 TS manual 源码 SHA 不符')
    check_jest(args.ts_jest, 1, 1, source)
    obs = rows(args.ts_observations)
    require(len(obs) == 3, 'TS manual 必须有且仅有 3 条原始观察')
    for index, (row, matcher) in enumerate(zip(obs, ('not.toBeNull', 'toHaveLength', 'toHaveLength')), 1):
        require(row.get('test') == MANUAL_NAME and row.get('index') == index
                and row.get('matcher') == matcher and row.get('pass') is True
                and row.get('actualLength') == SIZE,
                f'TS manual 第 {index} 条原始观察无效')
        require(row.get('expectedLength') == (None if index == 1 else SIZE),
                f'TS manual 第 {index} 条期望长度无效')
    require(obs[0].get('actualSha256') == ZERO_SHA, 'TS 解密输出摘要不符')

    check_xml(args.java_xml, args.java_summary)
    java = read(args.java_summary)
    for field, expected in [('sourceFile', 'AESGCM.man.test.ts'),
                            ('case', 'handles ciphertext longer than 2^32 bits'),
                            ('length', SIZE), ('bytewiseCompared', SIZE),
                            ('assertionsPassed', 3), ('decryptedSha256', ZERO_SHA)]:
        require(java.get(field) == expected, f'Java manual {field} 不符')
    require(re.fullmatch(r'[0-9a-f]{64}', java.get('ciphertextSha256', ''))
            and re.fullmatch(r'[0-9a-f]{32}', java.get('tag', '')),
            'Java manual 密文摘要或 tag 格式无效')
    oracle = read(args.node_oracle)
    require(oracle.get('source') == 'node:crypto independent streaming AES-128-GCM oracle'
            and oracle.get('inputBytes') == SIZE
            and oracle.get('ciphertextSha256') == CIPHER_SHA and oracle.get('tag') == TAG
            and java['ciphertextSha256'] == oracle.get('ciphertextSha256')
            and java['tag'] == oracle.get('tag'), 'Java 密文或 tag 与独立 Node oracle 不符')

    worktree = args.java_worktree.resolve()
    revision = subprocess.check_output(['git', '-C', str(worktree), 'rev-parse', 'HEAD'], text=True).strip()
    require(revision == args.java_revision, 'Java worktree 提交不符')
    require(not subprocess.check_output(['git', '-C', str(worktree), 'status', '--porcelain'], text=True).strip(),
            'Java worktree 必须干净')
    require((worktree / 'src/test/java/com/metanet4j/bsv/primitives/AESGCMManualTest.java').is_file(),
            'Java 原测试源码缺失')
    return {'id': MANUAL_ID, 'file': MANUAL, 'tsAssertions': 3, 'javaAssertions': 3,
            'matchedAssertions': 3, 'missingAssertions': 0, 'extraJavaAssertions': 0,
            'manualComparisonKind': '原 TS Jest 3 条断言与原 Java JUnit 3 条断言的语义摘要；逐字节循环由原测试执行，Node oracle 只交叉核验密文与 tag',
            'bytewiseCompared': SIZE, 'decryptedSha256': ZERO_SHA,
            'ciphertextSha256': java['ciphertextSha256'], 'tag': java['tag'],
            'javaRevision': revision}


def check_normal(args):
    check_jest(args.ts_normal_jest, 51, 4)
    expected_classes = {'AESGCMTest': 30, 'AsyncCryptoBackendTest': 3,
                        'SymmetricKeyTest': 15, 'SymmetricKeyCompatibilityTest': 3}
    current_xml = []
    for simple, count in expected_classes.items():
        path = args.java_normal_xml_dir / f'TEST-com.metanet4j.bsv.primitives.{simple}.xml'
        suite = ET.parse(path).getroot()
        require(suite.tag == 'testsuite' and suite.get('tests') == str(count)
                and all(suite.get(field) == '0' for field in ('errors', 'failures', 'skipped'))
                and len(suite.findall('testcase')) == count
                and all(c.get('classname') == f'com.metanet4j.bsv.primitives.{simple}'
                        and not c.findall('failure') and not c.findall('error')
                        for c in suite.findall('testcase')),
                f'{path}: 当前提交 Java 普通用例数或执行状态不符')
        properties = {p.get('name'): p.get('value') for p in suite.findall('./properties/property')}
        require(properties.get('migration.parity.java.output') == str(args.java_normal.resolve()),
                f'{path}: Surefire 参数未指向本次 Java 原始轨迹')
        current_xml.append(path)
    feature = read(ROOT / 'feature_list.json')
    task = next(x for x in feature['features'] if x['id'] == 'migration-impl-symmetric')
    files = set(task['testFiles']) - {MANUAL}
    catalogue = read(ROOT / 'module-tests.json')
    mapping = {x['id']: x for x in read(ROOT / 'test-map.json')['cases']}
    ts_by, java_by = defaultdict(list), defaultdict(list)
    for row in rows(args.ts_normal):
        source = row.get('file', '').replace('\\', '/')
        matching = [file for file in files if source == file or source.endswith('/' + file)]
        require(len(matching) == 1, f'TS 普通轨迹来源不唯一：{source}')
        ts_by[(matching[0], row.get('test'), row.get('occurrence', 1))].append(row)
    for row in rows(args.java_normal):
        java_by[row.get('test')].append(row)
    result, seen_ts, seen_java = [], set(), set()
    for file in catalogue['files']:
        if file['path'] not in files:
            continue
        require(sha(TS_ROOT / file['path']) == file['sha256'], f'固定 TS 源码变更：{file["path"]}')
        for case in file['cases']:
            key = (file['path'], ' '.join(case['names']), case.get('occurrence', 1))
            java = mapping[case['id']]['java']
            require(len(java) == 1, f'Java 映射非单项：{case["id"]}')
            identity = java[0]['className'] + '#' + java[0]['name']
            left, right = ts_by[key], java_by[identity]
            require(left and len(left) == len(right), f'普通用例断言数量不符：{key}')
            for index, (ts, jv) in enumerate(zip(left, right), 1):
                require(ts.get('pass') is True, f'普通 TS 用例 {case["id"]} 第 {index} 条未通过')
                for field in ('matcher', 'negated', 'actual', 'expected'):
                    require(ts.get(field) == jv.get(field), f'普通用例 {case["id"]} 第 {index} 条 {field} 不符')
            result.append({'id': case['id'], 'file': file['path'], 'tsAssertions': len(left),
                           'javaAssertions': len(right), 'matchedAssertions': len(left),
                           'missingAssertions': 0, 'extraJavaAssertions': 0,
                           'comparisonKind': '原始观察值逐字段精确比较'})
            seen_ts.add(key)
            seen_java.add(identity)
    require(set(ts_by) == seen_ts and set(java_by) == seen_java,
            '普通轨迹存在未映射的 TS 或 Java 用例')
    require(len(result) == 51 and sum(c['matchedAssertions'] for c in result) == 384,
            '普通用例总数或断言总数不符')
    return result, current_xml


def main():
    p = argparse.ArgumentParser(description=__doc__)
    evidence = ROOT / '.cache/evidence'
    defaults = {
        'ts-jest': 'symmetric-manual-ts-retry-20260926-jest.json',
        'ts-observations': 'symmetric-manual-ts-retry-20260926.jsonl',
        'java-summary': 'symmetric-manual-java-current-c0d9fdd.json',
        'java-xml': 'symmetric-manual-java-current-c0d9fdd-surefire.xml',
        'node-oracle': 'symmetric-manual-node-crypto-oracle.json',
        'ts-normal-jest': 'symmetric-ts-jest.json',
        'ts-normal': 'symmetric-ts-parity.jsonl',
        'java-normal': 'symmetric-java-parity-current-c0d9fdd.jsonl',
    }
    for name, file in defaults.items():
        p.add_argument('--' + name, type=Path, default=evidence / file)
    p.add_argument('--java-worktree', type=Path, default=Path('/tmp/bsv-symmetric-manual-c0d9fdd'))
    p.add_argument('--java-normal-xml-dir', type=Path,
                   default=evidence / 'symmetric-java-current-c0d9fdd-surefire')
    p.add_argument('--java-revision', default='c0d9fdd995e455b23b535d1084b6b59f38ace9db')
    p.add_argument('--output', type=Path, default=evidence / 'symmetric-task-parity-c0d9fdd.json')
    args = p.parse_args()
    try:
        manual = check_manual(args)
        normal, normal_xml = check_normal(args)
    except (ValueError, KeyError, ET.ParseError, FileNotFoundError) as error:
        p.error(str(error))
    files = [getattr(args, name.replace('-', '_')) for name in defaults] + normal_xml
    report = {'taskId': 'migration-impl-symmetric', 'javaRevision': args.java_revision,
              'upstreamCommit': read(ROOT / 'module-tests.json')['upstreamCommit'],
              'casesTotal': 52, 'casesCompared': 52, 'assertionsCompared': 387,
              'missingCases': 0, 'missingAssertions': 0, 'uncompared': 0,
              'extraJavaAssertions': 0, 'taskAcceptancePassed': True,
              'manualComparisonKind': manual['manualComparisonKind'],
              'normalComparisonKind': '固定 TS 轨迹与当前 c0d9fdd Java 原始轨迹的 51 个原用例、384 条断言，逐字段精确比较；Surefire XML 同时核验轨迹输出路径',
              'normalRawTraceRevision': args.java_revision,
              'evidenceSha256': {str(path): sha(path) for path in files},
              'cases': sorted(normal + [manual], key=lambda c: c['id'])}
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('taskId', 'casesTotal', 'casesCompared',
                                             'assertionsCompared', 'taskAcceptancePassed')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
