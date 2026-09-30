#!/usr/bin/env python3
"""全量 TS 采集：按探针分派表跑完整模块测试，把原始轨迹转成本轮 ts-inputs.jsonl / ts-assertions.jsonl。

用法（全量运行的 tsCommand）：
    python3 run-full-ts-capture.py --run-dir <runDir> --report ts-jest.json

自测可以用 --files 只跑子集（例如 --files 'src/primitives/__tests/TransactionSignature.additional.test.ts'）。
默认严格模式：有原文件没有探针、探针没装成、raw 型轨迹缺失或转换失败都非零退出；子集自测加
--allow-unresolved。

三层输入／断言来源（都在本脚本内合并成一个 ts-inputs.jsonl / ts-assertions.jsonl）：
  1. direct 探针：自己把本轮最终行写进 EVIDENCE_INPUTS_PATH；
  2. raw 探针 + emit 段：跑分派表登记的 emit-ts 转换器，输出收集到 runDir/emit/；
  3. legacy 局部（旧管线，探针自己记录原断言）：跑 full-run-overrides.json 登记的本轮转换器，
     输入合并进 ①/②，断言单独收集；其余局部的断言由一份共享原始断言轨迹经
     emit-assertion-observations.py 统一转换。
legacy 局部的断言索引必须显式排除在标准转换器的计划之外（旧轨迹与 capture-parity.cjs 的
matcher 序号口径不同，混在一个文件里会报“原 TS matcher 序号不连续”）。

环境变量由 evidence-bundle capture 注入（EVIDENCE_SIDE／EVIDENCE_RUN_ID／EVIDENCE_INPUTS_PATH／
EVIDENCE_ASSERTIONS_PATH／EVIDENCE_INPUT_PLAN）；直接运行时按运行目录补默认值。
"""
import argparse
import glob as globlib
import json
import re
import os
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

TASK = Path(__file__).resolve().parent
SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'
DEFAULT_PROBES = TASK / 'full-run-probes.json'
DEFAULT_CATALOG = TASK / 'module-tests.json'
DEFAULT_MAPPING = TASK / 'test-map.json'


def read_json(path):
    return json.loads(Path(path).read_text())


def read_rows(path):
    if not Path(path).exists():
        return []
    rows = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as error:
                raise ValueError(f'{path}:{number} 不是 JSON：{error}') from error
    return rows


def write_rows(path, rows):
    # ensure_ascii=True：JS 字符串可含未配对代理字符（\ud800 等），直接以 UTF-8 写会抛
    # UnicodeEncodeError；转义成 \uXXXX 后文件是纯 ASCII，任何消费者都能读回同一字符串。
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=True) + '\n' for row in rows),
                          encoding='utf-8')


def build_env(options):
    run_dir = options.run_dir.resolve()
    env = dict(os.environ)
    env['MIGRATION_FULL_RUN_DIR'] = str(run_dir)
    env['MIGRATION_FULL_PROBES'] = str(options.probes.resolve())
    env['EVIDENCE_SIDE'] = env.get('EVIDENCE_SIDE') or 'ts'
    env['EVIDENCE_RUN_ID'] = env.get('EVIDENCE_RUN_ID') or uuid.uuid4().hex
    env['MIGRATION_NETWORK_LOG'] = env.get('MIGRATION_NETWORK_LOG') or str(run_dir / 'ts-network.jsonl')
    env['MIGRATION_PARITY_TS_OBSERVATIONS'] = \
        env.get('MIGRATION_PARITY_TS_OBSERVATIONS') or str(run_dir / 'ts-assertions.raw.jsonl')
    env['EVIDENCE_INPUTS_PATH'] = options.inputs.resolve() if options.inputs \
        else env.get('EVIDENCE_INPUTS_PATH') or str(run_dir / 'ts-inputs.jsonl')
    env['EVIDENCE_ASSERTIONS_PATH'] = options.assertions.resolve() if options.assertions \
        else env.get('EVIDENCE_ASSERTIONS_PATH') or str(run_dir / 'ts-assertions.jsonl')
    plan = options.plan.resolve() if options.plan else Path(env.get('EVIDENCE_INPUT_PLAN', ''))
    if plan and plan.is_file():
        env['EVIDENCE_INPUT_PLAN'] = str(plan)
    elif 'EVIDENCE_INPUT_PLAN' in env and not Path(env['EVIDENCE_INPUT_PLAN']).is_file():
        env.pop('EVIDENCE_INPUT_PLAN')
    return env


def hydrate_plan_dirs(table, run_dir, plan, strict):
    """旧管线探针要按局部冻结清单（catalog.json + input-plan.json）解析自己的用例。

    全量运行只有本轮汇总计划，且采集期间冻结目录必须一字不改，因此这里把相关局部计划目录
    的冻结文件复制到 <runDir>/plans/<local>/，再把探针的 EVIDENCE_INPUT_PLAN 指到副本。
    """
    copied, missing = {}, []
    names = {probe.get('probePlan') for entry in table['locals'].values()
             for probe in entry['probes'] if probe.get('probePlan')}
    for local in sorted(names):
        entry = table['locals'].get(local) or {}
        source = Path(entry.get('plan') or '')
        target = run_dir / 'plans' / local
        if not source.is_file() or not (source.parent / 'catalog.json').is_file():
            missing.append({'local': local, 'plan': str(source)})
            continue
        target.mkdir(parents=True, exist_ok=True)
        for name in ('catalog.json', 'mapping.json'):
            origin = source.parent / name
            if origin.is_file():
                shutil.copyfile(origin, target / name)
        subset = {case_id: value for case_id, value in plan.items() if case_id in entry.get('cases', [])}
        (target / 'input-plan.json').write_text(
            json.dumps(subset, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        copied[local] = str(target / 'input-plan.json')
    return copied, missing


def jest_command(options, env, catalog):
    # jest.config.js 里 testPathIgnorePatterns 含 `\.man\.test\.ts$`，只给 --runTestsByPath 时
    # 这些文件仍会被过滤掉（实测 --listTests 不列出），因此显式覆盖为只忽略 node_modules——
    # 与 run-ts-baseline.py / collect-cases.cjs 的既有做法一致，否则 `AESGCM.man.test.ts`
    # 会被全量 TS 捕获静默跳过，strict 模式下以“轨迹缺失”整轮非零退出。
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand', '--watchman=false',
               '--testPathIgnorePatterns', '/node_modules/',
               '--setupFilesAfterEnv', str(TASK / 'ts-offline-guard.cjs'),
               str(TASK / 'capture-full-dispatch.cjs'), str(TASK / 'capture-parity.cjs')]
    selected = []
    for pattern in options.files:
        matches = sorted(globlib.glob(str(SDK / pattern), recursive=True))
        selected.extend(matches)
    if options.files:
        if not selected:
            raise ValueError('--files 没有匹配到测试文件：' + ','.join(options.files))
        command.extend(['--runTestsByPath', *selected])
    else:
        command.extend(['--runTestsByPath',
                        *[str(SDK / file['path']) for file in catalog['files']]])
    command.extend(['--json', '--outputFile=' + str(options.report.resolve())])
    return command, [Path(path) for path in selected]


def run_jest(command, env, run_dir):
    log = run_dir / 'ts-jest.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=TASK, env=env, stdout=stream, stderr=subprocess.STDOUT)
    print(log.read_text()[-4000:], file=sys.stderr)
    return result


def describe_jest(report):
    data = read_json(report)
    summary = {key: data.get(key) for key in ('success', 'numTotalTestSuites', 'numTotalTests', 'numPassedTests',
                                              'numFailedTests', 'numFailedTestSuites', 'numPendingTests',
                                              'numTodoTests', 'numRuntimeErrorTestSuites')}
    failures = []
    if data.get('success') is not True or summary['numFailedTests'] or summary['numFailedTestSuites'] \
            or summary['numRuntimeErrorTestSuites'] or summary['numPendingTests'] or summary['numTodoTests']:
        failures.append('Jest 未全部通过：' + json.dumps(summary, ensure_ascii=False))
    if not summary['numTotalTests']:
        failures.append('Jest 没有执行任何用例：' + json.dumps(summary, ensure_ascii=False))
    return data, summary, failures


def executed_files(report):
    names = set()
    for row in read_json(report).get('testResults', []):
        name = row['name'].replace('\\', '/')
        names.add('src/' + name.split('/src/').pop() if '/src/' in name else name)
    return names


def audit_raw_trajectories(table, files, run_dir, strict):
    """raw 型探针必须真的写出非空轨迹；strict 时缺失即失败。"""
    missing, present = [], {}
    for path in sorted(files):
        for probe in table['files'].get(path, {}).get('probes', []):
            for env, name in (probe.get('outputs') or {}).items():
                if env == 'MIGRATION_PARITY_TS_OBSERVATIONS' and probe.get('parity') == 'shared':
                    continue
                target = run_dir / name
                if target.exists() and target.stat().st_size:
                    present[(probe['local'], env)] = target
                else:
                    missing.append({'local': probe['local'], 'probe': probe['probe'], 'file': path,
                                    'env': env, 'raw': str(target)})
    return present, missing


def emit_inputs(table, files, run_dir, env, strict):
    """所有 raw 型探针按分派表里的 emit 段转换成本轮输入行。"""
    rows, problems, emitted = [], [], []
    for name, entry in sorted(table['locals'].items()):
        if entry.get('legacyEmit'):
            continue  # 旧管线局部统一走 emit_legacy
        if files and not (set(entry.get('files') or []) & files):
            continue  # 子集自测：本局部对应的原文件本轮没跑
        for probe in entry['probes']:
            if probe['mode'] != 'raw' or probe.get('parity') == 'legacy':
                continue
            emit = (probe.get('emit') or {}).get('argv') or []
            raw = probe.get('raw')
            if not raw or not (run_dir / raw).exists():
                continue
            if not emit:
                problems.append({'local': name, 'probe': probe['probe'],
                                 'reason': '没有可用的 emit-ts 转换器', 'raw': raw})
                continue
            output = run_dir / 'emit' / f'{name}.jsonl'
            output.parent.mkdir(parents=True, exist_ok=True)
            argv = [part.replace('{runDir}', str(run_dir)).replace('{local}', name)
                    .replace('{output}', str(output)) for part in emit]
            result = subprocess.run(argv, cwd=TASK, env=env, capture_output=True, text=True)
            if result.returncode:
                problems.append({'local': name, 'probe': probe['probe'], 'reason': 'emit-ts 失败',
                                 'argv': argv, 'stderr': (result.stderr or result.stdout)[-800:]})
                continue
            rows.extend(read_rows(output))
            emitted.append({'local': name, 'probe': probe['probe'], 'output': str(output),
                            'rows': len(read_rows(output))})
    return rows, problems, emitted


def filtered_parity(table, run_dir, env, locals_in_scope):
    """把共享断言轨迹按局部裁成私有文件：旧管线转换器只认自己那份局部轨迹。

    逐局部采集时 `ts-assertions.raw.jsonl` 只有该局部的行；全量运行所有文件共用一份，
    而 replay-*/prepare-* 的转换器会遍历全文件并按测试名索引，混入他行会 KeyError 或计数不符。
    这里单遍流式扫描，并且**只用正则取行首的 file 字段**（轨迹可达 800 MB，个别行上 200 MB，
    json.loads 整行会吃光内存），按归属分流到各局部文件。
    """
    shared = Path(env.get('MIGRATION_PARITY_TS_OBSERVATIONS') or '')
    owners = {}
    for name in locals_in_scope:
        for path in (table['locals'][name].get('files') or []):
            owners.setdefault(path, []).append(name)
    made, streams = {}, {}
    if not shared.is_file() or not owners:
        return made
    target_dir = run_dir / 'legacy-parity'
    target_dir.mkdir(parents=True, exist_ok=True)
    pattern = re.compile(r'^\s*\{\s*"test":.*?"file":\s*"([^"]*)"')
    plain = re.compile(r'"file":\s*"([^"]*)"')
    try:
        with shared.open() as source:
            for line in source:
                if not line.strip():
                    continue
                match = pattern.match(line) or plain.search(line[:4096])
                if not match:
                    continue
                name = match.group(1).replace('\\', '/')
                key = next((path for path in owners if name.endswith('/' + path)), None)
                if key is None:
                    continue
                for local in owners[key]:
                    if local not in streams:
                        streams[local] = (target_dir / f'{local}.raw.jsonl').open('w')
                        made[local] = target_dir / f'{local}.raw.jsonl'
                    streams[local].write(line if line.endswith('\n') else line + '\n')
    finally:
        for stream in streams.values():
            stream.close()
    return made


def emit_legacy(table, run_dir, env, strict, files=None):
    """旧管线局部：跑本轮转换器，输入并入总输入，断言单独收集到 legacy/ 目录。

    逐局部采集时这些转换器直接读局部冻结计划目录；全量运行把该目录复制到
    `<runDir>/plans/<local>/`，{planDir} 指副本（内容逐字节同源），{replay} 指冻结语料。
    """
    rows, problems, emitted, assertion_rows = [], [], [], []
    scope = [name for name, entry in sorted(table['locals'].items())
             if entry.get('legacyEmit')
             and not (files and not (set(entry.get('files') or []) & files))]
    parity_files = filtered_parity(table, run_dir, env, scope)
    for name in scope:
        entry = table['locals'][name]
        legacy = entry['legacyEmit']
        probe = next((item for item in entry['probes'] if item.get('parity') == 'legacy'),
                     entry['probes'][0])
        raw = probe.get('raw') or next(iter((probe.get('outputs') or {}).values()), None)
        if not raw or not (run_dir / raw).exists():
            problems.append({'local': name, 'probe': probe['probe'], 'reason': '原始轨迹缺失', 'raw': raw})
            continue
        output = run_dir / 'emit' / f'{name}.jsonl'
        sidecar = entry.get('assertionSource', 'standard') == 'sidecar'
        assertions = run_dir / 'legacy' / (f'{name}.assertions.jsonl' if sidecar
                                           else f'{name}.discard.jsonl')
        output.parent.mkdir(parents=True, exist_ok=True)
        assertions.parent.mkdir(parents=True, exist_ok=True)
        outputs = {key: str(run_dir / value) for key, value in (probe.get('outputs') or {}).items()}
        substitutions = {
            '{runDir}': str(run_dir), '{local}': name, '{output}': str(output),
            '{assertions}': str(assertions), '{raw}': str(run_dir / raw) if raw else '',
            '{parity}': str(parity_files.get(name)
                            or env.get('MIGRATION_PARITY_TS_OBSERVATIONS') or ''),
            '{planDir}': str(run_dir / 'plans' / name),
            '{plan}': str(entry.get('plan') or ''), '{replay}': str(entry.get('replay') or ''),
            '{outputs}': json.dumps(outputs, ensure_ascii=False),
        }

        def substitute(part):
            for key, value in substitutions.items():
                part = part.replace(key, value)
            return part

        argv = [substitute(part) for part in legacy]
        result = subprocess.run(argv, cwd=TASK, env=env, capture_output=True, text=True)
        if result.returncode:
            problems.append({'local': name, 'reason': '旧管线 emit-ts 失败', 'argv': argv,
                             'stderr': (result.stderr or result.stdout)[-1200:]})
            continue
        local_rows = read_rows(output)
        rows.extend(local_rows)
        emitted.append({'local': name, 'output': str(output), 'rows': len(local_rows)})
        if sidecar and assertions.exists():
            assertion_rows.extend(read_rows(assertions))
    return rows, assertion_rows, problems, emitted


def order_rows(rows, plan, inputs_path):
    """按本轮计划顺序重排并去重；返回 (rows, 缺失样本, 计划外样本, 重复样本)。"""
    by_key, duplicates, extra = {}, [], []
    for row in rows:
        key = (row.get('caseId'), row.get('sampleId'))
        if key in by_key:
            duplicates.append({'caseId': key[0], 'sampleId': key[1]})
            continue
        by_key[key] = row
    ordered, missing = [], []
    for case_id, expected in plan.items():
        for sample_id in expected.get('sampleIds', []):
            row = by_key.pop((case_id, sample_id), None)
            if row is None:
                missing.append({'caseId': case_id, 'sampleId': sample_id})
            else:
                ordered.append(row)
    for key, row in sorted(by_key.items(), key=lambda item: (str(item[0][0]), str(item[0][1]))):
        extra.append({'caseId': key[0], 'sampleId': key[1]})
        ordered.append(row)
    return ordered, missing, extra, duplicates


def emit_assertions(options, env, run_dir, raw, strict, report, plan, skip_cases):
    """共享断言轨迹 → 标准断言行；跳过 legacy 局部自己的用例。

    legacy 局部（探针自己记录原断言）的轨迹行不带 capture-parity.cjs 的 matcher 序号口径，
    混进同一个文件会破坏“序号连续”校验，因此这里把它们的用例从计划里摘掉，由各自转换器产出。
    """
    subset = {case_id: value for case_id, value in plan.items() if case_id not in skip_cases}
    report['assertionsPlan'] = {'total': len(plan), 'standard': len(subset), 'legacy': len(plan) - len(subset)}
    if not subset:
        report.setdefault('notes', []).append({'step': 'assertions', 'reason': '计划全部由旧管线局部覆盖'})
        return []
    if not raw.exists() or not raw.stat().st_size:
        report.setdefault('notes', []).append({'step': 'assertions', 'reason': '没有原始断言轨迹：' + str(raw)})
        return []
    plan_path = run_dir / 'standard-assertions-plan.json'
    plan_path.write_text(json.dumps(subset, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    # 自产断言的旧局部（探针替换了 global.expect 的文件）即使有行落进共享轨迹，也不能进标准转换：
    # 标准转换器要求轨迹里的文件都在计划内，这里按「计划内的原文件」把共享轨迹裁一份出来。
    case_files = {case['id']: file['path'] for file in read_json(options.catalog)['files']
                  for case in file['cases']}
    wanted = {case_files[case_id] for case_id in subset if case_id in case_files}
    filtered = run_dir / 'standard-assertions.raw.jsonl'
    kept = 0
    if raw.is_file():
        pattern = re.compile(r'"file":\s*"([^"]*)"')
        with raw.open() as source, filtered.open('w') as target:
            for line in source:
                if not line.strip():
                    continue
                match = pattern.search(line[:4096])
                if not match:
                    continue
                name = match.group(1).replace('\\', '/')
                if any(name.endswith('/' + path) for path in wanted):
                    target.write(line if line.endswith('\n') else line + '\n')
                    kept += 1
    report['standardRaw'] = {'path': str(filtered), 'rows': kept, 'shared': str(raw)}
    if not kept:
        report.setdefault('notes', []).append({'step': 'assertions', 'reason': '标准断言轨迹为空'})
        return []
    output = run_dir / 'standard-assertions.jsonl'
    command = ['python3', str(TASK / 'emit-assertion-observations.py'),
               '--catalog', str(options.catalog.resolve()), '--mapping', str(options.mapping.resolve()),
               '--plan', str(plan_path), '--side', 'ts', '--raw', str(filtered),
               '--run-id', env['EVIDENCE_RUN_ID'], '--output', str(output),
               '--allow-ts-extra']
    result = subprocess.run(command, cwd=TASK, env=env, capture_output=True, text=True)
    if result.returncode:
        if not (strict or options.strict_emit):
            report.setdefault('notes', []).append(
                {'step': 'assertions', 'reason': '断言转换未完成（子集自测允许）',
                 'stderr': (result.stderr or result.stdout)[-400:]})
            return []
        return ['断言转换失败：' + (result.stderr or result.stdout)[-400:]]
    report['assertions'] = json.loads(result.stdout.strip().splitlines()[-1])
    report['standardAssertions'] = {'path': str(output), 'rows': len(read_rows(output))}
    return []


def merge_assertions(env, run_dir, plan, legacy_rows, report):
    """标准断言行 + legacy 断言行 → 最终 EVIDENCE_ASSERTIONS_PATH（按计划顺序）。"""
    standard = read_rows(run_dir / 'standard-assertions.jsonl')
    by_key, duplicates, problems = {}, [], []
    for row in standard + legacy_rows:
        key = (row.get('caseId'), row.get('assertionId'))
        if key in by_key:
            duplicates.append({'caseId': key[0], 'assertionId': key[1]})
            continue
        by_key[key] = row
    ordered, missing = [], []
    for case_id, expected in plan.items():
        for assertion_id in expected.get('assertionIds', []):
            row = by_key.pop((case_id, assertion_id), None)
            if row is None:
                missing.append({'caseId': case_id, 'assertionId': assertion_id})
            else:
                ordered.append(row)
    extra = sorted({f'{case}:{identity}' for case, identity in by_key})
    report['assertionsMerged'] = {'total': len(ordered), 'standard': len(standard),
                                  'legacy': len(legacy_rows), 'missing': len(missing),
                                  'extra': len(extra), 'duplicates': len(duplicates)}
    if missing:
        report['missingAssertions'] = missing[:50]
        problems.append(f'本轮断言缺少 {len(missing)} 个计划身份（例如 '
                        + json.dumps(missing[:3], ensure_ascii=False) + '）')
    if duplicates:
        problems.append('本轮断言出现重复 (caseId, assertionId)：'
                        + json.dumps(duplicates[:5], ensure_ascii=False))
    if extra:
        problems.append('本轮断言出现计划外身份：' + json.dumps(extra[:5], ensure_ascii=False))
    write_rows(env['EVIDENCE_ASSERTIONS_PATH'], ordered)
    report['assertions'] = {'path': env['EVIDENCE_ASSERTIONS_PATH'], 'rows': len(ordered)}
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--files', action='append', default=[], help='自测用：相对 TS SDK 根目录的 glob')
    parser.add_argument('--probes', type=Path, default=DEFAULT_PROBES)
    parser.add_argument('--catalog', type=Path, default=DEFAULT_CATALOG)
    parser.add_argument('--mapping', type=Path, default=DEFAULT_MAPPING)
    parser.add_argument('--inputs', type=Path)
    parser.add_argument('--assertions', type=Path)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--allow-unresolved', action='store_true', help='子集自测：允许覆盖缺口')
    parser.add_argument('--strict-emit', action='store_true', help='转换缺口也非零退出')
    options = parser.parse_args()

    options.run_dir = options.run_dir.resolve()
    options.run_dir.mkdir(parents=True, exist_ok=True)
    options.report = options.report if options.report.is_absolute() else options.run_dir / options.report
    options.report.parent.mkdir(parents=True, exist_ok=True)
    env = build_env(options)
    table = read_json(options.probes)
    catalog = read_json(options.catalog)
    strict = not options.allow_unresolved

    plan = None
    plan_path = env.get('EVIDENCE_INPUT_PLAN')
    if plan_path and Path(plan_path).is_file():
        plan = read_json(plan_path)
    hydrated, hydrate_missing = hydrate_plan_dirs(table, options.run_dir, plan or {}, strict)

    command, selected = jest_command(options, env, catalog)
    print(json.dumps({'jest': command[:8], 'tests': len(selected) or len(catalog['files']),
                      'runDir': str(options.run_dir), 'hydratedPlans': len(hydrated)}, ensure_ascii=False))
    result = run_jest(command, env, options.run_dir)
    report = {'runId': env['EVIDENCE_RUN_ID'], 'runDir': str(options.run_dir),
              'files': [str(path) for path in selected], 'jestExitCode': result.returncode,
              'hydratedPlans': hydrated}
    problems = []
    if not options.report.exists():
        problems.append('Jest 未产出 JSON 报告：' + str(options.report))
    else:
        data, summary, failures = describe_jest(options.report)
        report['jest'] = summary
        problems.extend(failures)

    network = Path(env['MIGRATION_NETWORK_LOG'])
    if network.exists() and network.read_text().strip():
        problems.append('固定原测试出现网络调用：' + str(network))

    unmapped = read_rows(options.run_dir / 'unmapped-files.jsonl')
    if unmapped:
        report['unmapped'] = unmapped
        if strict:
            problems.append('有原文件没有可用探针或探针装载失败：'
                            + json.dumps(sorted({row['file'] for row in unmapped}), ensure_ascii=False))

    files = executed_files(options.report) if options.report.exists() else set()
    if plan is not None and options.files:
        # 子集自测的计划裁剪：以冻结清单的「用例 → 原文件」为准（不依赖局部登记，否则没有
        # cases 的局部会把整文件的用例一起丢掉，断言转换会报“轨迹文件不在唯一冻结范围”）。
        case_files = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
        selected_file_set = {str(path.relative_to(SDK)) for path in selected} or set(files)
        plan = {case_id: value for case_id, value in plan.items()
                if case_files.get(case_id) in selected_file_set}
        report['subsetPlanCases'] = len(plan)
    present, missing = audit_raw_trajectories(table, files, options.run_dir, strict)
    if missing:
        report['missingRawTrajectories'] = missing
        if strict:
            problems.append('原始轨迹缺失或为空：'
                            + json.dumps(sorted({row['local'] for row in missing}), ensure_ascii=False))

    inputs_path = Path(env['EVIDENCE_INPUTS_PATH'])
    direct_rows = read_rows(inputs_path)
    rows, emit_problems, emitted = emit_inputs(table, files, options.run_dir, env, strict)
    legacy_rows, legacy_assertions, legacy_problems, legacy_emitted = emit_legacy(
        table, options.run_dir, env, strict, files)
    report['emitted'] = emitted + legacy_emitted
    report['legacyAssertions'] = len(legacy_assertions)
    all_problems = emit_problems + legacy_problems
    if all_problems:
        report['emitProblems'] = all_problems
        if strict or options.strict_emit:
            problems.append('raw 型转换器未全部成功：'
                            + json.dumps(sorted({row['local'] for row in all_problems}), ensure_ascii=False))
    # 只有「自己产断言」的旧局部才从标准转换器的计划里摘除；其余旧局部只借转换器产输入，
    # 断言仍来自共享断言轨迹。
    legacy_cases = {case_id for entry in table['locals'].values()
                    if entry.get('legacyEmit') and entry.get('assertionSource', 'standard') == 'sidecar'
                    for case_id in entry.get('cases', [])}
    if plan is not None:
        all_rows = direct_rows + rows + legacy_rows
        ordered, missing_samples, extra_samples, duplicates = order_rows(all_rows, plan, inputs_path)
        report['samples'] = {'total': len(ordered), 'missing': len(missing_samples),
                             'extra': len(extra_samples), 'duplicates': len(duplicates)}
        if missing_samples:
            report['missingSamples'] = missing_samples[:200]
            if strict or options.strict_emit:
                problems.append(f'本轮输入缺少 {len(missing_samples)} 个计划样本（例如 '
                                + json.dumps(missing_samples[:3], ensure_ascii=False) + '）')
        if duplicates:
            problems.append('本轮输入出现重复 (caseId, sampleId)：' + json.dumps(duplicates[:5], ensure_ascii=False))
        write_rows(inputs_path, ordered)
        report['inputs'] = {'path': str(inputs_path), 'rows': len(ordered)}
        problems.extend(emit_assertions(options, env, options.run_dir,
                                        Path(env['MIGRATION_PARITY_TS_OBSERVATIONS']), strict, report,
                                        plan, legacy_cases))
        problems.extend(merge_assertions(env, options.run_dir, plan, legacy_assertions, report))
    else:
        write_rows(inputs_path, direct_rows + rows + legacy_rows)
        report['inputs'] = {'path': str(inputs_path), 'rows': len(direct_rows + rows + legacy_rows),
                            'plan': None}
        if legacy_assertions:
            write_rows(env['EVIDENCE_ASSERTIONS_PATH'], legacy_assertions)
    report['problems'] = problems
    (options.run_dir / 'ts-capture-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'tsInputs': report.get('inputs'), 'tsAssertions': report.get('assertions'),
                      'jest': report.get('jest'), 'problems': len(problems)}, ensure_ascii=False))
    for problem in problems:
        print('TS-CAPTURE-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
