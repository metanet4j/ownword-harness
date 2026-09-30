#!/usr/bin/env python3
"""封存固定 utils.property 原测试输入，并核对 Java 消费及所有断言。"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent
UPSTREAM = TASK.parents[2] / 'reference/ts-stack'
TEST = UPSTREAM / 'packages/sdk/src/primitives/__tests/utils.property.test.ts'
NAMES = (
    'base58 property tests round-trips arbitrary non-empty byte sequences',
    'base58 property tests round-trips arbitrary Base58Check payloads and rejects checksum mutation',
    'base58 property tests matches independent vectors and enforces malformed-input and hex-output boundaries',
)
JAVA = (
    'roundTripsArbitraryNonEmptyByteSequences',
    'roundTripsBase58CheckAndRejectsChecksumMutation',
    'matchesIndependentVectorsAndMalformedBoundaries',
)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def check(condition, message):
    if not condition:
        raise ValueError(message)


def source():
    revision = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    pinned = json.loads((TASK / 'workspace.json').read_text())['upstream']['commit']
    check(revision == pinned and not subprocess.check_output(
        ['git', '-C', str(UPSTREAM), 'status', '--porcelain'], text=True).strip(),
        'TS 来源不是干净的固定上游提交')
    return revision


def validate_ts(folder):
    metadata = json.loads((folder / 'meta.json').read_text())
    config = metadata['configuration']
    check(config.get('numRuns') == 300 and config.get('seed') == 20260926
          and not config.get('path'), 'fast-check seed/path/轮次与固定原测试不符')
    check(len(metadata['runs']) == 2 and [run['test'] for run in metadata['runs']] == list(NAMES[:2])
          and all(run['status'] == 'passed' and run['calls'] == 300
                  and run['firstFailure'] is None and run['shrinkCalls'] == 0
                  for run in metadata['runs']), '两组原 property 运行或 shrink 记录异常')
    inputs, assertions, boundaries = (rows(folder / filename) for filename in
                                      ('inputs.jsonl', 'assertions.jsonl', 'boundaries.jsonl'))
    check(len(inputs) == 600 and [row['test'] for row in inputs] == [NAMES[0]] * 300 + [NAMES[1]] * 300,
          '原 predicate 入参数量或顺序变化')
    for group, arity, limits in ((inputs[:300], 1, [(1, 96)]),
                                 (inputs[300:], 2, [(1, 4), (0, 96)])):
        for index, row in enumerate(group, 1):
            check(row['index'] == index and row['phase'] == 'generate'
                  and len(row['inputs']) == arity, '原 predicate 样本编号或形状变化')
            for values, (minimum, maximum) in zip(row['inputs'], limits):
                check(minimum <= len(values) <= maximum
                      and all(type(value) is int and 0 <= value <= 255 for value in values),
                      '原生成器输入约束变化')
    counts = [sum(row['test'] == name for row in assertions) for name in NAMES]
    check(counts == [300, 600, 76] and len(assertions) == 976
          and all(row['pass'] is True for row in assertions), '固定 TS 976 条原断言不完整')
    check(len(boundaries) == 76 and [row['matcher'] for row in boundaries] ==
          ['toEqual', 'toBe'] + ['toThrow'] * 73 + ['toEqual'], '边界输入与断言位置不符')
    check([call['method'] for call in boundaries[0]['calls']] == ['fromBase58']
          and boundaries[0]['calls'][0]['args'] == ['111z']
          and [call['method'] for call in boundaries[1]['calls']] == ['toBase58']
          and boundaries[1]['calls'][0]['args'] == [[0, 0, 0, 57]]
          and all([call['method'] for call in row['calls']] == ['fromBase58']
                  for row in boundaries[2:75])
          and [call['method'] for call in boundaries[75]['calls']] ==
          ['toBase58', 'toBase58Check', 'fromBase58', 'fromBase58Check']
          and boundaries[75]['calls'][2]['args'] == boundaries[75]['calls'][3]['args'][:1],
          '原测试边界 API 入参未完整采集')
    invalid = ['', *[chr(code) for code in range(128)
                    if chr(code) not in '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'], 'é', '🚀']
    check([row['calls'][0]['args'][0] for row in boundaries[2:75]] == invalid,
          '无效字符循环样本与原测试不一致')
    report = json.loads((folder / 'jest.json').read_text())
    check(report['numPassedTests'] == 3 and report['numFailedTests'] == report['numPendingTests'] == 0,
          '固定原 Jest 报告未 3/3 通过')
    network = folder / 'network.jsonl'
    check(not network.exists() or not network.read_text().strip(), '固定原测试触发网络调用')
    old = (TASK / 'metanet4j-bsv-sdk/src/test/resources/utils-property-seed-20260926.txt').read_text().splitlines()
    hexes = [':'.join(bytes(values).hex() for values in row['inputs']) for row in inputs]
    check(hexes == old[2:302] + old[303:], '既有 Java seed 语料与本次实际生成入参不同')
    return inputs, assertions, boundaries


def seal(args):
    folder = Path(args.ts_dir)
    inputs, _, _ = validate_ts(folder)
    revision = source()
    corpus = Path(args.corpus)
    corpus.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(folder / 'inputs.jsonl', corpus)
    check(rows(corpus) == inputs, '封存输入与实际生成值不同')
    manifest = {'schemaVersion': 1, 'source': 'fixed TypeScript fast-check predicate arguments',
                'upstreamCommit': revision,
                'testPath': str(TEST.relative_to(UPSTREAM)), 'testSha256': sha(TEST),
                'seed': 20260926, 'path': None, 'numRunsPerProperty': 300,
                'generatorConstraints': {'nonEmptyBytes': {'minLength': 1, 'maxLength': 96},
                                         'prefixBytes': {'minLength': 1, 'maxLength': 4},
                                         'payloadBytes': {'minLength': 0, 'maxLength': 96}},
                'predicateCalls': 600, 'shrinkCalls': 0, 'boundaryInputs': 76,
                'assertions': 976, 'corpusSha256': sha(corpus),
                'tsReportSha256': sha(folder / 'jest.json'),
                'tsAssertionsSha256': sha(folder / 'assertions.jsonl'),
                'tsBoundariesSha256': sha(folder / 'boundaries.jsonl')}
    Path(args.manifest).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'samples': 600, 'assertions': 976, 'corpusSha256': manifest['corpusSha256']}))


def compare(args):
    manifest = json.loads(Path(args.manifest).read_text())
    check(source() == manifest['upstreamCommit'] and sha(TEST) == manifest['testSha256'],
          '原测试来源版本已变化')
    check(sha(args.corpus) == manifest['corpusSha256'], '版本管理语料校验失败')
    expected = rows(args.corpus)
    consumed = rows(args.java_inputs)
    ordered = [row for name in NAMES[:2] for row in consumed if row['test'] == name]
    check(ordered == expected and len(consumed) == 600, 'Java 未在各原用例内逐轮消费相同的 600 个实际样本')
    ts_boundaries, java_boundaries = rows(args.ts_boundaries), rows(args.java_boundaries)
    # 固定 TS 模块导出代理还观察到末尾两个外层调用的内部 Base58 调用；
    # 保留原始轨迹，仅在跨语言公开 API 入参对照时选取外层调用。
    public_boundaries = ts_boundaries[:-1] + [{**ts_boundaries[-1],
        'calls': [ts_boundaries[-1]['calls'][1], ts_boundaries[-1]['calls'][3]]}]
    check(sha(args.ts_boundaries) == manifest['tsBoundariesSha256']
          and public_boundaries == java_boundaries and len(ts_boundaries) == 76,
          '两端边界 API 实际入参不一致')
    ts, java = rows(args.ts_assertions), rows(args.java_assertions)
    check(sha(args.ts_assertions) == manifest['tsAssertionsSha256']
          and len(ts) == len(java) == 976, '两端原断言数量不一致')
    for name, method, count in zip(NAMES, JAVA, (300, 600, 76)):
        left = [row for row in ts if row['test'] == name]
        right = [row for row in java if row['test'] ==
                 'com.metanet4j.bsv.primitives.UtilsPropertyTest#' + method]
        check(len(left) == len(right) == count, '用例断言缺失：' + name)
        for index, (a, b) in enumerate(zip(left, right), 1):
            for key in ('matcher', 'negated', 'actual', 'expected'):
                check(a[key] == b[key], f'{name} 第 {index} 条 {key} 实际值不同')
            check(a['pass'] is True, f'{name} 第 {index} 条原断言失败')
    root = ET.parse(args.surefire).getroot()
    check(root.get('tests') == '3' and all(root.get(key) == '0' for key in ('failures', 'errors', 'skipped'))
          and len(root.findall('testcase')) == 3, 'Java Surefire 原用例未 3/3 执行通过')
    print(json.dumps({'cases': 3, 'inputSamples': 676, 'assertionsCompared': 976,
                      'exact': True, 'scope': 'utils.property.test.ts only', 'formalAcceptance': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seal', 'compare'))
    for name in ('ts-dir', 'corpus', 'manifest', 'java-inputs', 'ts-boundaries',
                 'java-boundaries', 'ts-assertions', 'java-assertions', 'surefire'):
        parser.add_argument('--' + name)
    args = parser.parse_args()
    {'seal': seal, 'compare': compare}[args.action](args)
