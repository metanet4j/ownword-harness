#!/usr/bin/env python3
"""从已登记的原始运行 manifest 生成「非标准局部 → TS 证据入口」映射表（ts-serial-entries.json）。

非标准局部（18 个 `specialized-local` + 29 个没登记 `capture` 的旧管线局部）不在
`recapture-local.py` 的标准分派范围内，但它们的输入计划同样是冻结全集的一部分：
`compare_ts`／`audit.compare` 要求 133 个原文件与 5329 个用例全覆盖，只跑标准局部到不了终点。

入口**不靠猜**，逐局部取权威来源：

1. 旧管线局部：取它登记里 `ts_run_manifest` 指向的原始 manifest 的 `command`
   （那是当时真实跑通的 `evidence-bundle capture` 命令），只把 `--report` 指向本轮子目录；
2. 16 个 auth-fetch 直写型专用局部：取 `full-run-probes.json` 里该局部探针（`mode=direct`），
   计划文件即登记里的 `input_plan`；
3. 2 个共享向量局部（`script-spend-shared-vectors`／`transaction-shared-vectors`）：
   取各自 `*-vector-evidence.py ts` 子命令；
4. 上面三类都核不到、或引用的语料路径已不存在的，标成 `unresolved` 并列原因，不实现、不猜。
"""
import argparse
import json
import shlex
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
PROBES = TASK / 'full-run-probes.json'
# 额外直写探针：少数局部的观测分散在多个直写探针里，而登记表只登记了其中一个。
# `replaces` 必须显式列出会被覆盖的 caseId——两个探针会对同一 (caseId, sampleId) 各写一行，
# 而计划里该用例只有一个样本；驱动用独立 jest 调用采集（避免探针之间争用 jest.doMock 的模块工厂），
# 并且只保留这里声明的那一行。
EXTRA_PROBES = {
    'auth-fetch-known-txids': [{
        'probe': 'capture-auth-fetch-knownTxids-peer-inputs.cjs',
        'replaces': ['189790cbac0f42250b37519c090b906ad9619403b2b3dd8f02ee0be3fe1e1b09'],
        'reason': '付款探针与 Peer 探针都会为该用例写 sampleId=call-0 的一行（value.kind 分别是 '
                  'AuthFetch.knownTxidsInput 与 AuthFetch.knownTxidsPeerInput），而计划只有 1 个样本；'
                  'Java 侧 AuthFetchKnownTxidsPeerInputReplay 只认 Peer 行（付款重放的固定 case 表里没有这一例），'
                  '因此用独立 jest 调用采 Peer 观测并显式替换付款行。'}],
}
UNRESOLVED = {'shape': 'unresolved'}


def read(path):
    return json.loads(Path(path).read_text())


def resolve(value):
    path = Path(value)
    return path if path.is_absolute() else TASK / path


def from_manifest(item):
    """旧管线局部：按原始 manifest 的 command 还原入口（命令形如 python3 <适配器> ts …）。"""
    manifest = item.get('ts_run_manifest')
    if not manifest or not resolve(manifest).is_file():
        return None
    command = read(resolve(manifest)).get('command')
    if not command:
        return None
    words = [str(word) for word in command]
    if words[0].endswith(('python', 'python3')):
        if len(words) < 2:
            return None
        script, arguments = words[1], words[2:]
    else:
        script, arguments = words[0], words[1:]
    if arguments[:1] == ['ts']:
        arguments = arguments[1:]
    if not arguments or 'ts' not in words[:3]:
        return None
    return {'script': script, 'args': arguments, 'manifest': manifest}


def direct_probe(item, table):
    """直写型专用局部：探针自己写 EVIDENCE_INPUTS_PATH，断言走 capture-parity 共享轨迹。"""
    for path, entry in table['files'].items():
        for probe in entry.get('probes', []):
            if probe['local'] == item['name'] and probe.get('mode') == 'direct':
                return {'script': probe['probe'], 'probe': probe['probe'], 'file': path}
    return None


def classify(item, table):
    name = item['name']
    if name in ('script-spend-shared-vectors', 'transaction-shared-vectors'):
        script = 'script-vector-evidence.py' if name.startswith('script') else 'transaction-vector-evidence.py'
        return {'shape': 'vector', 'script': script, 'source': '证据脚本自带 ts 子命令'}
    found = direct_probe(item, table)
    if found:
        return {'shape': 'direct', 'probe': found['script'], 'file': found['file'],
                'plan': item['input_plan'], 'source': 'full-run-probes.json 的 direct 探针'}
    legacy = from_manifest(item)
    if legacy:
        entry = {'shape': 'adapter', 'script': legacy['script'], 'args': legacy['args'],
                 'source': 'ts_run_manifest ' + legacy['manifest']}
        entry['plan'] = item['input_plan']
        return entry
    return dict(UNRESOLVED, reason='登记里没有可用的原始 TS 命令或直写探针')


CHECKED_FLAGS = ('--catalog', '--mapping', '--replay', '--corpus', '--plan')
# 语料回退：旧运行的 --replay 指向 /tmp 下的临时副本，原文件是冻结 SDK 仓里的同名资源。
# 只在同名文件确实存在于冻结资源目录时回退，并记录替换来源；适配器自身会用计划逐行校验语料，
# 语料不符会直接失败，因此这里的等价性是**运行期可验证**的，不是猜测。
CORPUS_FALLBACK = TASK / 'metanet4j-bsv-sdk/src/test/resources/migration'


def arg_pairs(arguments):
    pairs, index = [], 0
    while index < len(arguments):
        token = arguments[index]
        value = arguments[index + 1] if index + 1 < len(arguments) and not \
            str(arguments[index + 1]).startswith('--') else None
        pairs.append((token, value))
        index += 2 if value is not None else 1
    return pairs


def adapter_plan(entry):
    """适配器自己会用的计划：--plan（目录或文件）优先，否则取 --replay 语料的同目录计划。"""
    pairs = dict(arg_pairs(entry['args']))
    if pairs.get('--plan'):
        path = resolve(pairs['--plan'])
        return path / 'input-plan.json' if path.is_dir() else path
    if pairs.get('--catalog'):
        return resolve(pairs['--catalog']).parent / 'input-plan.json'
    if pairs.get('--replay'):
        return resolve(pairs['--replay']).parent / 'input-plan.json'
    return None


def same_plan(left, right):
    if left is None or not left.is_file() or not right.is_file():
        return False
    return canonical(read(left)) == canonical(read(right))


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))


def verify_plan(entry, item):
    """核实入口实际使用的计划与登记计划逐字节一致；不一致就判 unresolved，不猜。"""
    registered = resolve(item['input_plan'])
    if entry['shape'] == 'adapter':
        derived = adapter_plan(entry)
        entry['derivedPlan'] = str(derived.relative_to(TASK)) if derived else None
        if not same_plan(derived, registered):
            entry.update(shape='unresolved',
                         reason='适配器实际使用的计划与登记计划不同或不可解析：'
                                + str(entry.get('derivedPlan')))
        else:
            entry['plan'] = str(registered.relative_to(TASK))
    elif entry['shape'] == 'direct':
        plan = resolve(entry['plan'])
        if not plan.is_file():
            entry.update(shape='unresolved', reason='直写探针缺计划文件：' + str(entry['plan']))
        elif not same_plan(plan, registered):
            entry.update(shape='unresolved', reason='直写探针计划与登记计划不同：' + str(entry['plan']))
    elif entry['shape'] == 'vector':
        folder = registered.parent
        for name in ('catalog.json', 'mapping.json', 'input-plan.json'):
            if not (folder / name).is_file():
                entry.update(shape='unresolved', reason='向量局部缺计划文件：' + str(folder / name))
                break
        else:
            entry['planFolder'] = str(folder.relative_to(TASK))
    return entry


def check_paths(entry):
    """核实入口引用的输入是否仍然存在；缺失即判为 unresolved（不猜、不补造）。"""
    missing = []
    if entry['shape'] == 'adapter':
        for flag, value in arg_pairs(entry['args']):
            if flag not in CHECKED_FLAGS or value is None:
                continue
            path = Path(value)
            path = path if path.is_absolute() else TASK / path
            if path.exists():
                continue
            fallback = CORPUS_FALLBACK / path.name
            if flag in ('--replay', '--corpus') and fallback.is_file():
                entry.setdefault('substitutions', []).append(
                    {'flag': flag, 'from': value, 'to': str(fallback.relative_to(TASK)),
                     'reason': '旧运行的 /tmp 语料副本已不存在，回退到冻结 SDK 资源里的同名语料'})
                index = entry['args'].index(value)
                entry['args'][index] = str(fallback.relative_to(TASK))
                continue
            missing.append(f'{flag} {value}')
    script = TASK / str(entry.get('script') or entry.get('probe') or '')
    if not script.is_file():
        missing.append('脚本不存在：' + str(script))
    for extra in entry.get('extraProbes', []):
        if not (TASK / extra.get('probe', '')).is_file():
            missing.append('额外探针不存在：' + str(extra.get('probe')))
        if not extra.get('replaces') or not extra.get('reason'):
            missing.append('额外探针缺少 replaces/reason：' + str(extra.get('probe')))
    if missing:
        entry.update(shape='unresolved', reason='入口引用的路径已不存在：' + '；'.join(missing))
    return entry


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=TASK / 'ts-serial-entries.json')
    options = parser.parse_args()
    config, table = read(CONFIG), read(PROBES)
    standard = [item['name'] for item in config['locals']
                if item.get('capture') and item.get('captureKind') != 'specialized-local']
    entries = {}
    for item in config['locals']:
        if item['name'] in standard:
            continue
        entry = classify(item, table)
        entry['kind'] = item.get('captureKind') or 'old-pipeline'
        entry['input_plan'] = item['input_plan']
        if item['name'] in EXTRA_PROBES:
            entry['extraProbes'] = EXTRA_PROBES[item['name']]
        if entry['shape'] != 'unresolved':
            entry = check_paths(entry)
        if entry['shape'] != 'unresolved':
            entry = verify_plan(entry, item)
        entries[item['name']] = entry
    counts = {}
    for entry in entries.values():
        counts[entry['shape']] = counts.get(entry['shape'], 0) + 1
    output = {'revision': 'ts-serial-entries-v1', 'standardLocals': len(standard),
              'entries': entries, 'summary': counts}
    options.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'entries': len(entries), 'summary': counts,
                      'unresolved': sorted(name for name, entry in entries.items()
                                           if entry['shape'] == 'unresolved')},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
