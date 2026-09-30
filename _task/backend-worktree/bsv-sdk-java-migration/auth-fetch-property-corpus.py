#!/usr/bin/env python3
"""封存固定 TS fast-check 输入，并复核 Java 按相同顺序真实消费。"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

TASK = Path(__file__).resolve().parent
UPSTREAM = TASK.parents[2] / 'reference/ts-stack'
TEST = UPSTREAM / 'packages/sdk/src/auth/clients/__tests__/AuthFetch.property.test.ts'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def records(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line]


def seal(args):
    metadata = json.loads(Path(args.metadata).read_text())
    inputs = records(args.ts_inputs)
    assertions = records(args.ts_assertions)
    report = json.loads(Path(args.ts_report).read_text())
    if metadata['status'] != 'passed' or metadata['configuration']['numRuns'] != 300:
        raise ValueError('固定 TS 性质测试没有完整通过 300 轮')
    if metadata['calls'] != 300 or metadata['shrinkCalls'] != 0 or len(inputs) != 300:
        raise ValueError('本批原测试调用数量或缩减记录异常')
    if [row['index'] for row in inputs] != list(range(1, 301)):
        raise ValueError('原测试输入顺序缺失或重复')
    if len(assertions) != 600 or not all(row['pass'] for row in assertions):
        raise ValueError('固定 TS 600 条原断言未全部通过')
    if report['numPassedTests'] != 1 or report['numFailedTests'] or report['numPendingTests']:
        raise ValueError('固定原 Jest 报告未通过')
    if metadata['configuration'].get('seed') != args.seed or metadata['configuration'].get('path'):
        raise ValueError('fast-check seed/path 与运行命令不一致')
    revision = subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip()
    pinned = json.loads((TASK / 'workspace.json').read_text())['upstream']['commit']
    if revision != pinned or subprocess.check_output(['git', '-C', str(UPSTREAM), 'status', '--porcelain'], text=True).strip():
        raise ValueError('TypeScript 输入来源不是干净的固定上游提交')
    corpus = Path(args.corpus)
    corpus.parent.mkdir(parents=True, exist_ok=True)
    corpus.write_bytes(Path(args.ts_inputs).read_bytes())
    result = {'schemaVersion': 1, 'source': 'fixed TypeScript fast-check predicate arguments',
              'upstreamCommit': revision, 'testPath': str(TEST.relative_to(UPSTREAM)),
              'testSha256': digest(TEST.read_bytes()), 'fastCheckVersion': metadata['fastCheckVersion'],
              'seed': args.seed, 'path': None, 'numRuns': 300, 'predicateCalls': 300,
              'shrinkCalls': 0, 'assertions': 600, 'corpusSha256': digest(corpus.read_bytes()),
              'tsReportSha256': digest(Path(args.ts_report).read_bytes()),
              'tsAssertionsSha256': digest(Path(args.ts_assertions).read_bytes())}
    Path(args.manifest).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'corpus': str(corpus), 'sha256': result['corpusSha256'], 'calls': 300}))


def compare(args):
    manifest = json.loads(Path(args.manifest).read_text())
    corpus_path = Path(args.corpus)
    if digest(corpus_path.read_bytes()) != manifest['corpusSha256']:
        raise ValueError('版本管理的原输入语料 SHA 不一致')
    source = records(corpus_path)
    consumed = records(args.java_inputs)
    if source != consumed or len(source) != 300:
        raise ValueError('Java 未按固定 TS 原输入逐轮消费 300 个样本')
    ts = [row for row in records(args.ts_assertions)
          if row.get('file', '').endswith('AuthFetch.property.test.ts')]
    java = [row for row in records(args.java_assertions)
            if row.get('test') == 'com.metanet4j.bsv.auth.clients.AuthFetchPropertyTest#boundedResponseFieldsAlwaysSettleAndReleaseState']
    if len(ts) != len(java) or len(ts) != 600:
        raise ValueError('TS/Java 原断言数量不是 600/600')
    for index, (left, right) in enumerate(zip(ts, java), 1):
        if any(left[key] != right[key] for key in ('matcher', 'actual', 'expected')):
            raise ValueError(f'第 {index} 条 TS/Java 实际断言值不同')
        if not left['pass']:
            raise ValueError(f'第 {index} 条固定 TS 原断言未通过')
    print(json.dumps({'samples': len(source), 'assertionsCompared': len(ts), 'exact': True,
                      'corpusSha256': manifest['corpusSha256']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('seal', 'compare'))
    parser.add_argument('--metadata')
    parser.add_argument('--ts-inputs')
    parser.add_argument('--ts-assertions', required=True)
    parser.add_argument('--ts-report')
    parser.add_argument('--corpus', required=True)
    parser.add_argument('--manifest', required=True)
    parser.add_argument('--seed', type=int)
    parser.add_argument('--java-inputs')
    parser.add_argument('--java-assertions')
    args = parser.parse_args()
    {'seal': seal, 'compare': compare}[args.action](args)
