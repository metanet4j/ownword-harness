#!/usr/bin/env python3
"""把两端独立采集的输入和断言轨迹绑定到原始 Jest/Surefire 报告。"""
import argparse
import hashlib
import json
import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import subprocess
import sys
import time
import uuid

spec = spec_from_file_location('audit_tests', Path(__file__).resolve().parent / 'audit-tests.py')
audit = module_from_spec(spec)
spec.loader.exec_module(audit)
TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def fail(message):
    raise ValueError(message)


def lines(path):
    result = []
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if line.strip():
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError as error:
                fail(f'{path}:{number} 不是 JSON：{error}')
    return result


def grouped(path, field):
    by_case = {}
    for row in lines(path):
        case_id = row.get('caseId')
        if not isinstance(case_id, str) or not isinstance(row.get(field), str):
            fail(f'{path} 缺少 caseId 或 {field}')
        by_case.setdefault(case_id, []).append(row)
    return by_case


def same(expected, actual, label):
    if set(expected) != set(actual):
        fail(f'{label}：缺失 {sorted(set(expected)-set(actual))[:4]}；多余 {sorted(set(actual)-set(expected))[:4]}')


def unique(rows, field, label):
    keys = [row[field] for row in rows]
    if len(keys) != len(set(keys)):
        fail(f'{label} 重复 {field}')


def build(args):
    capture_paths = {'inputPlan': args.input_plan, 'tsInputs': args.ts_inputs,
                     'javaInputs': args.java_inputs, 'tsAssertions': args.ts_assertions,
                     'javaAssertions': args.java_assertions}
    audit.independent_captures(capture_paths)
    catalog, mapping, plan = read(args.catalog), read(args.mapping), read(args.input_plan)
    cases = {case['id']: case for file in catalog['files'] for case in file['cases']}
    mapped = {case['id']: case for case in mapping['cases']}
    if len(cases) != sum(len(file['cases']) for file in catalog['files']) or len(mapped) != len(mapping['cases']):
        fail('用例 ID 重复')
    same(cases, mapped, '映射用例')
    same(cases, plan, '输入计划用例')
    ts_inputs, java_inputs = grouped(args.ts_inputs, 'sampleId'), grouped(args.java_inputs, 'sampleId')
    ts_results, java_results = grouped(args.ts_assertions, 'assertionId'), grouped(args.java_assertions, 'assertionId')
    for label, rows in [('TS 输入', ts_inputs), ('Java 输入', java_inputs), ('TS 断言', ts_results), ('Java 断言', java_results)]:
        same(cases, rows, label + '用例')
    audit.validate_plan(catalog, mapping, plan)
    output = []
    for case_id in cases:
        expected_samples = plan[case_id].get('sampleIds')
        expected_assertions = plan[case_id].get('assertionIds')
        if not isinstance(expected_samples, list) or not expected_samples or not all(isinstance(x, str) for x in expected_samples):
            fail(f'输入计划为空或格式错误：{case_id}')
        if len(set(expected_samples)) != len(expected_samples):
            fail(f'输入计划样本重复：{case_id}')
        if not isinstance(expected_assertions, list) or not expected_assertions or len(set(expected_assertions)) != len(expected_assertions):
            fail(f'独立断言计划为空或重复：{case_id}')
        inputs = {}
        for label, rows in [('TS', ts_inputs[case_id]), ('Java', java_inputs[case_id])]:
            unique(rows, 'sampleId', label + ' 输入')
            if [row['sampleId'] for row in rows] != expected_samples:
                fail(f'{label} 输入样本顺序、数量或 ID 不符：{case_id}')
            if any('value' not in row for row in rows):
                fail(f'{label} 输入缺少实际值：{case_id}')
            inputs[label] = [{'sampleId': row['sampleId'], 'value': row['value']} for row in rows]
        ts_hash = hashlib.sha256(canonical(inputs['TS']).encode()).hexdigest()
        java_hash = hashlib.sha256(canonical(inputs['Java']).encode()).hexdigest()
        if ts_hash != java_hash:
            fail(f'TS/Java 输入或前置状态不同：{case_id}')
        results = {}
        for label, rows in [('TS', ts_results[case_id]), ('Java', java_results[case_id])]:
            unique(rows, 'assertionId', label + ' 断言')
            if [row['assertionId'] for row in rows] != expected_assertions:
                fail(f'{label} 断言顺序、数量或 ID 不符：{case_id}')
            if any('value' not in row for row in rows):
                fail(f'{label} 断言缺少实际值：{case_id}')
            results[label] = [{'id': row['assertionId'], 'value': row['value']} for row in rows]
        for left, right in zip(results['TS'], results['Java']):
            if canonical(left['value']) != canonical(right['value']):
                fail(f'实际结果不一致：{case_id} / {left["id"]}')
        output.append({'id': case_id, 'inputSha256': ts_hash, 'tsInputSha256': ts_hash,
                       'javaInputSha256': java_hash, 'inputSamples': inputs,
                       'ts': results['TS'], 'java': results['Java']})
    revision, run_hashes = audit.runtime_provenance(args, catalog, capture_paths)
    return {'upstreamCommit': catalog['upstreamCommit'], 'javaRevision': revision,
            'runManifestSha256': run_hashes,
            'catalogSha256': digest(args.catalog),
            'tsReportSha256': sorted(digest(p) for p in args.ts_report),
            'javaReportSha256': sorted(digest(p) for p in args.java_report),
            'captureSha256': {key: digest(path) for key, path in capture_paths.items()},
            'cases': output}


def capture(args):
    """先固定来源再执行，禁止把已经存在的报告包装成一次新运行。"""
    catalog, mapping, plan = read(args.catalog), read(args.mapping), read(args.input_plan)
    audit.validate_plan(catalog, mapping, plan)
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    audit.require(bool(command), 'capture 缺少实际测试/采集命令')
    if args.side == 'java':
        audit.require('clean' in command and 'test' in command
                      and command.index('clean') < command.index('test')
                      and not any(audit.re.search(r'skipTests|maven\.test\.skip|testFailureIgnore|failIfNoTests=false', p)
                                  for p in command), 'Java 运行必须是未跳过测试的 clean test')
    output = Path(args.output).resolve()
    log = output.with_suffix(output.suffix + '.log')
    destinations = [Path(p).absolute() for p in (args.inputs, args.assertions, *args.report)] + [output, log]
    audit.require(len({str(p.resolve()) for p in destinations}) == len(destinations), '采集输出路径重复')
    audit.require(all(not p.exists() and not p.is_symlink() for p in destinations),
                  '采集输出或报告已经存在；必须使用新的运行目录，禁止重放旧文件')
    for path in destinations:
        path.parent.mkdir(parents=True, exist_ok=True)

    def source_revision():
        if args.side == 'java':
            return audit.java_revision()
        config = read(TASK / 'workspace.json')['upstream']
        upstream = TASK.parents[2] / config['path']
        revision = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
        audit.require(revision == config['commit'] == catalog['upstreamCommit'], 'TS 采集来源不是固定上游提交')
        audit.require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(),
                      'TS 采集来源工作区有修改')
        return revision

    manifest = {'schemaVersion': 1, 'side': args.side, 'runId': uuid.uuid4().hex,
                'producerSha256': digest(__file__), 'upstreamCommit': catalog['upstreamCommit'],
                'sourceRevision': source_revision(), 'catalogSha256': digest(args.catalog),
                'mappingSha256': digest(args.mapping), 'inputPlanSha256': digest(args.input_plan),
                'command': command, 'startedAtNs': time.time_ns(), 'exitCode': None, 'logPath': str(log)}
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    environment = dict(os.environ, EVIDENCE_RUN_ID=manifest['runId'], EVIDENCE_SIDE=args.side,
                       EVIDENCE_INPUTS_PATH=str(Path(args.inputs).resolve()),
                       EVIDENCE_ASSERTIONS_PATH=str(Path(args.assertions).resolve()),
                       EVIDENCE_INPUT_PLAN=str(Path(args.input_plan).resolve()))
    try:
        with log.open('w') as stream:
            result = subprocess.run(command, env=environment, stdout=stream, stderr=subprocess.STDOUT)
        manifest.update(exitCode=result.returncode, finishedAtNs=time.time_ns(),
                        sourceRevisionAfter=source_revision(), logSha256=digest(log))
        audit.require(result.returncode == 0, f'{args.side} 实际运行失败，退出码 {result.returncode}；日志：{log}')
        audit.require(manifest['sourceRevision'] == manifest['sourceRevisionAfter'], '采集期间源码发生变化，须重新执行')
        for key, path in (('catalogSha256', args.catalog), ('mappingSha256', args.mapping), ('inputPlanSha256', args.input_plan)):
            audit.require(manifest[key] == digest(path), f'采集期间固定输入发生变化：{key}')
        for path, identity in ((args.inputs, 'sampleId'), (args.assertions, 'assertionId')):
            rows = audit.capture_rows(path, identity)
            audit.require(bool(rows), f'运行未产生实际采集：{path}')
            audit.require(all(row.get('runId') == manifest['runId'] and row.get('side') == args.side
                              for case in rows.values() for row in case), '运行输出缺少本次 runId/side；禁止复制或重放旧轨迹')
        manifest.update(inputsSha256=digest(args.inputs), assertionsSha256=digest(args.assertions),
                        reportSha256=sorted(digest(path) for path in args.report))
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        manifest['captureError'] = str(error)
        raise
    finally:
        output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'side': args.side, 'runId': manifest['runId'], 'manifest': str(output)}, ensure_ascii=False))


def capture_main():
    parser = argparse.ArgumentParser(description='包装一次真实采集；现存报告不能追认为本次执行')
    parser.add_argument('--side', choices=('ts', 'java'), required=True)
    for name in ('catalog', 'mapping', 'input-plan', 'inputs', 'assertions', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--report', action='append', required=True)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args(sys.argv[2:])
    try:
        capture(args)
    except (ValueError, OSError, KeyError, TypeError, subprocess.CalledProcessError) as error:
        parser.error(str(error))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalog', 'mapping', 'input-plan', 'ts-inputs', 'java-inputs',
                 'ts-assertions', 'java-assertions', 'output'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--java-revision', help='只校验运行来源版本，不能覆盖 manifest 中的版本')
    parser.add_argument('--ts-run-manifest')
    parser.add_argument('--java-run-manifest')
    parser.add_argument('--ts-report', action='append', required=True)
    parser.add_argument('--java-report', action='append', required=True)
    args = parser.parse_args()
    try:
        result = build(args)
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.error(str(error))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'cases': len(result['cases']), 'assertions': sum(len(c['ts']) for c in result['cases']),
                      'output': args.output}, ensure_ascii=False))


if __name__ == '__main__':
    if sys.argv[1:2] == ['capture']:
        capture_main()
    else:
        main()
