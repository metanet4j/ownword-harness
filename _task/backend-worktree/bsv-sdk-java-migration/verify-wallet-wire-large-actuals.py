#!/usr/bin/env python3
"""校验 WalletWire 4 MiB 原断言 actual 的完整双侧字节及主轨迹摘要。"""
import argparse
import hashlib
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def summary(length, sha256):
    return {'type': 'map', 'value': {
        'length': {'type': 'number', 'value': str(length)},
        'sha256': {'type': 'string', 'value': sha256}}}


def main(args):
    index = {(row['caseId'], row['assertionId']): row for row in json.loads(Path(args.index).read_text())}
    expected = {key for key, row in index.items() if row['javaMethod'] == 'preservesLargeTypedBeef'}
    require(len(expected) == 4, '固定 BEEF 大数组断言身份不完整')
    manifests = {side: json.loads(Path(getattr(args, side + '_manifest')).read_text()) for side in ('ts', 'java')}
    actuals = {}
    for side in ('ts', 'java'):
        trace = {(row['caseId'], row['assertionId']): row['value']
                 for row in rows(getattr(args, side + '_assertions'))}
        observed = {}
        for row in rows(getattr(args, side + '_large')):
            key = (row['caseId'], row['assertionId'])
            require(key in expected and key not in observed, f'{side} 大数组断言身份缺失或重复：{key}')
            identity = index[key]
            require(row['side'] == side and row['runId'] == manifests[side]['runId'],
                    f'{side} 大数组运行来源不符：{key}')
            require(all(row[field] == identity[field] for field in ('test', 'occurrence', 'ordinal')),
                    f'{side} 大数组冻结用例身份不符：{key}')
            require(isinstance(row['bytesHex'], str) and len(row['bytesHex']) % 2 == 0,
                    f'{side} 大数组十六进制内容无效：{key}')
            full = bytes.fromhex(row['bytesHex'])
            require(len(full) == row['length'] and row['length'] == 4 * 1024 * 1024,
                    f'{side} 大数组完整长度不符：{key}')
            sha256 = hashlib.sha256(full).hexdigest()
            require(sha256 == row['sha256'], f'{side} 大数组 sidecar 字节摘要不符：{key}')
            require(key in trace and trace[key]['matcher'] == row['matcher']
                    and trace[key]['actual'] == summary(len(full), sha256),
                    f'{side} 大数组主断言轨迹与完整字节不符：{key}')
            observed[key] = full
        require(set(observed) == expected, f'{side} 大数组 sidecar 未覆盖四条原断言')
        actuals[side] = observed
    for key in expected:
        require(actuals['ts'][key] == actuals['java'][key], f'TS/Java 大数组实际字节不同：{key}')
    report = {'schemaVersion': 1, 'status': 'PASS', 'assertions': 4,
              'bytesComparedPerAssertion': 4 * 1024 * 1024,
              'tsSidecarSha256': digest(args.ts_large), 'javaSidecarSha256': digest(args.java_large),
              'tsRunId': manifests['ts']['runId'], 'javaRunId': manifests['java']['runId']}
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('index', 'ts-large', 'java-large', 'ts-assertions', 'java-assertions',
                 'ts-manifest', 'java-manifest', 'output'):
        parser.add_argument('--' + name, required=True)
    arguments = parser.parse_args()
    try:
        main(arguments)
    except (ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
