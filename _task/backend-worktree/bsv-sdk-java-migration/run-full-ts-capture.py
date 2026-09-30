#!/usr/bin/env python3
"""全量 TS 采集：按探针分派表跑完整模块测试，把原始轨迹转成本轮 ts-inputs.jsonl / ts-assertions.jsonl。

用法（全量运行的 tsCommand）：
    python3 run-full-ts-capture.py --run-dir <runDir> --report ts-jest.json

自测可以用 --files 只跑子集（例如 --files 'src/primitives/__tests/TransactionSignature.additional.test.ts'）。
默认严格模式：有原文件没有探针、探针没装成、raw 型轨迹缺失或转换失败都非零退出；子集自测加
--allow-unresolved。

环境变量由 evidence-bundle capture 注入（EVIDENCE_SIDE／EVIDENCE_RUN_ID／EVIDENCE_INPUTS_PATH／
EVIDENCE_ASSERTIONS_PATH／EVIDENCE_INPUT_PLAN）；直接运行时按运行目录补默认值。
"""
import argparse
import glob as globlib
import json
import os
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
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))


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
        for probe in entry['probes']:
            if probe['mode'] != 'raw':
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


def order_rows(rows, plan_path, inputs_path):
    """按本轮计划顺序重排并去重；返回 (rows, 缺失样本, 计划外样本, 重复样本)。"""
    plan = read_json(plan_path)
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


def emit_assertions(options, env, run_dir, raw, strict, report):
    """返回真实失败列表；跳过类说明只写进报告，不计为问题。"""
    if not raw.exists() or not raw.stat().st_size:
        report.setdefault('notes', []).append({'step': 'assertions', 'reason': '没有原始断言轨迹：' + str(raw)})
        return []
    plan = env.get('EVIDENCE_INPUT_PLAN')
    if not plan:
        report.setdefault('notes', []).append({'step': 'assertions', 'reason': '缺少本轮输入计划，跳过断言转换'})
        return []
    command = ['python3', str(TASK / 'emit-assertion-observations.py'),
               '--catalog', str(options.catalog.resolve()), '--mapping', str(options.mapping.resolve()),
               '--plan', plan, '--side', 'ts', '--raw', str(raw),
               '--run-id', env['EVIDENCE_RUN_ID'], '--output', env['EVIDENCE_ASSERTIONS_PATH'],
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
    return []


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

    command, selected = jest_command(options, env, catalog)
    print(json.dumps({'jest': command[:8], 'tests': len(selected) or len(catalog['files']),
                      'runDir': str(options.run_dir)}, ensure_ascii=False))
    result = run_jest(command, env, options.run_dir)
    report = {'runId': env['EVIDENCE_RUN_ID'], 'runDir': str(options.run_dir),
              'files': [str(path) for path in selected], 'jestExitCode': result.returncode}
    problems = []
    if not options.report.exists():
        problems.append('Jest 未产出 JSON 报告：' + str(options.report))
    else:
        data, summary, failures = describe_jest(options.report)
        report['jest'] = summary
        problems.extend(failures)
    if result.returncode and not problems:
        problems.append(f'Jest 退出码非零：{result.returncode}')

    network = Path(env['MIGRATION_NETWORK_LOG'])
    if network.exists() and network.read_text().strip():
        problems.append('固定原测试出现网络调用：' + str(network))

    unmapped = read_rows(options.run_dir / 'unmapped-files.jsonl')
    if unmapped:
        report['unmapped'] = unmapped
        if strict:
            problems.append('有原文件没有可用探针或探针装载失败：'
                            + json.dumps(sorted({row['file'] for row in unmapped}), ensure_ascii=False))
    if options.files:
        for path in read_rows(options.run_dir / 'dispatched-files.jsonl'):
            if not path.get('installed'):
                continue
        report['subset'] = sorted(selected and [str(path.relative_to(SDK)) for path in selected] or [])

    files = executed_files(options.report) if options.report.exists() else set()
    present, missing = audit_raw_trajectories(table, files, options.run_dir, strict)
    if missing:
        report['missingRawTrajectories'] = missing
        if strict:
            problems.append('原始轨迹缺失或为空：'
                            + json.dumps(sorted({row['local'] for row in missing}), ensure_ascii=False))

    inputs_path = Path(env['EVIDENCE_INPUTS_PATH'])
    direct_rows = read_rows(inputs_path)
    rows, emit_problems, emitted = emit_inputs(table, files, options.run_dir, env, strict)
    report['emitted'] = emitted
    if emit_problems:
        report['emitProblems'] = emit_problems
        if strict or options.strict_emit:
            problems.append('raw 型转换器未全部成功：'
                            + json.dumps(sorted({row['local'] for row in emit_problems}), ensure_ascii=False))
    all_rows = direct_rows + rows
    plan = env.get('EVIDENCE_INPUT_PLAN')
    if plan and Path(plan).is_file():
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
    else:
        write_rows(inputs_path, all_rows)
        report['inputs'] = {'path': str(inputs_path), 'rows': len(all_rows), 'plan': None}
    problems.extend(emit_assertions(options, env, options.run_dir,
                                    Path(env['MIGRATION_PARITY_TS_OBSERVATIONS']), strict, report))
    report['problems'] = problems
    (options.run_dir / 'ts-capture-report.json').write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'tsInputs': report.get('inputs'), 'jest': report.get('jest'),
                      'problems': len(problems)}, ensure_ascii=False))
    for problem in problems:
        print('TS-CAPTURE-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
