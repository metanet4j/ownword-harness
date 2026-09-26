#!/usr/bin/env python3
"""运行并验证同一轮完整 TS/Java 证据；需宿主提权调用 run。"""
import argparse
import importlib.util
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from types import SimpleNamespace

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('full_preflight', TASK / 'full-evidence-preflight.py')
preflight = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preflight)
audit, bundle = preflight.audit, preflight.bundle
read, write, require = preflight.load, preflight.write, audit.require
STAGES = ('ts-capture', 'java-capture', 'bundle', 'check')


def producers():
    # 采集适配器会导入同目录 helpers；一起固定，避免只校验入口而遗漏依赖。
    return {path.name: audit.digest(path) for path in sorted(TASK.iterdir())
            if path.is_file() and path.suffix in ('.py', '.cjs', '.mjs', '.sh')}


def frozen():
    catalog = read(TASK / 'module-tests.json')
    require(not catalog.get('partialImplementationOnly'), '全量运行禁止局部清单')
    current = audit.collect()
    require(catalog == current, '冻结清单与当前完整源码清点不同')
    require(read(TASK / 'module-scope.json')['scopeReview'] == 'reviewed'
            and not current['pendingModules'] and not current['crossModuleTestsPending'],
            '完整模块及跨目录范围尚未复核')
    return catalog


def checked_path(folder, name):
    path = folder / name
    require(isinstance(name, str) and not Path(name).is_absolute()
            and path.resolve().is_relative_to(folder.resolve()), '运行文件必须位于本轮目录内')
    require(not any(part.is_symlink() for part in (path, *path.parents)), '运行文件禁止符号链接')
    return path


def artifact_names(interface):
    names = ['input-plan.json', 'preflight.json', 'parity-results.json']
    for side in ('ts', 'java'):
        names.extend([side + '-inputs.jsonl', side + '-assertions.jsonl',
                      side + '-run.json', side + '-run.json.log', *interface[side + 'Reports']])
    names.extend(stage + '.log' for stage in STAGES)
    require(len(names) == len(set(names)), '完整运行的输出文件名重复')
    return names


def commands_for(interface, folder):
    java = interface['javaCommand']
    filters = r'-D(?:test|it\.test|groups|excludedGroups|includes|excludes|surefire\.(?:includes|excludes))(?:=|$)'
    require(not any(audit.re.search(filters, part) or part in
                    ('-pl', '--projects', '-rf', '--resume-from', '-N', '--non-recursive')
                    or part.startswith(('--projects=', '--resume-from=')) for part in java),
            '完整 Java 命令必须无过滤，禁止裁剪测试组、类或工程')
    commands = preflight.execution_sequence({'fullRun': interface}, folder,
        TASK / 'module-tests.json', TASK / 'test-map.json')
    # 子进程自身在成功 capture 后登记联合身份，父进程不能追认已有局部 manifest。
    for command in commands[:2]:
        command[1:3] = [str(TASK / 'full-evidence-run.py'), 'capture-side']
    return commands


def capture_side(args):
    identity = os.environ.get('EVIDENCE_FULL_RUN_ID', '')
    require(bool(audit.re.fullmatch(r'[0-9a-f]{32}', identity)), '缺少父运行身份')
    bundle.capture(args)
    manifest = read(args.output)
    manifest.update(fullRunId=identity, fullRunProducerSha256=audit.digest(__file__))
    write(args.output, manifest)
    return {'side': args.side, 'fullRunId': identity}


def snapshot():
    return {'javaRevision': audit.java_revision(), 'producerSha256': producers(),
            'catalogSha256': audit.digest(TASK / 'module-tests.json'),
            'mappingSha256': audit.digest(TASK / 'test-map.json'),
            'scopeSha256': audit.digest(TASK / 'module-scope.json')}


def same_snapshot(manifest):
    for key, value in snapshot().items():
        require(manifest.get(key) == value, '当前源码、工具或清单与本轮来源不同：' + key)


def run_process(command, log, deadline, environment):
    """统一截止时间覆盖所有阶段及后代进程，超时停止整个进程组。"""
    start = time.monotonic()
    record = {'command': command, 'startedAtNs': time.time_ns(), 'exitCode': None}
    with log.open('x') as stream:
        process = subprocess.Popen(command, cwd=TASK, env=environment, stdout=stream,
                                   stderr=subprocess.STDOUT, start_new_session=True)
        record['pid'] = process.pid
        try:
            record['exitCode'] = process.wait(timeout=max(0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            record['timedOut'] = True
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait()
            raise
        record['exitCode'] = process.returncode
    record.update(finishedAtNs=time.time_ns(), elapsedSeconds=time.monotonic() - start,
                  logSha256=audit.digest(log))
    return record


def validate_retry(timeout, previous, state, interface, plan_sha):
    require(timeout in (90, 180), '完整运行上限只能为 90 或 180 分钟')
    if timeout == 90:
        require(previous is None, '90 分钟运行无需重试来源')
        return None
    require(previous is not None, '180 分钟须引用实际触及 90 分钟上限的运行')
    old = read(previous)
    require(old.get('schemaVersion') == 1 and old.get('status') == 'timed-out'
            and old.get('timeoutMinutes') == 90 and old.get('elapsedSeconds', 0) >= 90 * 60
            and any(stage.get('timedOut') for stage in old.get('stages', [])),
            '重试来源未实际触及 90 分钟上限')
    require(old.get('interface') == interface and old.get('inputPlanSha256') == plan_sha,
            '180 分钟重试必须执行相同完整命令和输入计划')
    require(bool(audit.re.fullmatch(r'[0-9a-f]{32}', old.get('fullRunId', ''))), '重试来源缺少运行身份')
    require(old.get('finishedAtNs', 0) > old.get('startedAtNs', 0) > 0
            and old['elapsedSeconds'] <= 90 * 60 + 10
            and abs((old['finishedAtNs'] - old['startedAtNs']) / 1e9 - old['elapsedSeconds']) < 5,
            '重试来源的超时时间记录无效')
    previous_folder = previous.resolve().parent
    require(audit.digest(checked_path(previous_folder, 'input-plan.json')) == plan_sha,
            '重试来源的实际输入计划不同')
    commands = commands_for(interface, previous_folder)
    stages = old['stages']
    require([stage.get('name') for stage in stages] == list(STAGES[:len(stages)])
            and stages[-1].get('timedOut') and stages[-1].get('exitCode') != 0,
            '重试来源缺少真实超时阶段')
    last = old['startedAtNs']
    for stage, command in zip(stages, commands):
        require(stage.get('command') == command and type(stage.get('pid')) is int and stage['pid'] > 0,
                '重试来源缺少实际子进程命令或身份')
        require(last <= stage['startedAtNs'] <= stage['finishedAtNs'] <= old['finishedAtNs'],
                '重试来源的子进程时间窗无效')
        require(stage.get('logSha256') == audit.digest(checked_path(previous_folder, stage['name'] + '.log')),
                '重试来源的子进程日志缺失或不同')
        last = stage['finishedAtNs']
    for key, value in state.items():
        require(old.get(key) == value, '180 分钟重试来源已变化：' + key)
    return {'path': str(previous.resolve()), 'sha256': audit.digest(previous)}


def capture(config_path, folder, timeout, previous=None):
    catalog = frozen()
    state, config = snapshot(), read(config_path)
    pre, plan = preflight.inspect(config, config_path.resolve().parent,
        TASK / 'module-tests.json', TASK / 'test-map.json', state['javaRevision'], [])
    require(pre['readyForFullCapture'], '全量前置未满足；先补齐计划、独立注册及 fullRun 适配器')
    interface = config['fullRun']
    names = artifact_names(interface)
    for name in names:
        checked_path(folder, name)
    plan_sha = hashlib.sha256((json.dumps(plan, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()
    retry = validate_retry(timeout, previous, state, interface, plan_sha)
    commands = commands_for(interface, folder)
    folder.mkdir(parents=True, exist_ok=False)
    write(folder / 'input-plan.json', plan)
    write(folder / 'preflight.json', pre)
    manifest = dict(state, schemaVersion=1, fullRunId=uuid.uuid4().hex, status='running',
        formalAcceptance=False, upstreamCommit=catalog['upstreamCommit'],
        casesTotal=sum(len(file['cases']) for file in catalog['files']),
        inputPlanSha256=audit.digest(folder / 'input-plan.json'), interface=interface,
        timeoutMinutes=timeout, retryAfter=retry, startedAtNs=time.time_ns(), stages=[])
    path = folder / 'full-run.json'
    started = time.monotonic()
    deadline = started + timeout * 60
    write(path, manifest)
    try:
        for name, command in zip(STAGES, commands):
            same_snapshot(manifest)
            stage = run_process(command, folder / (name + '.log'), deadline,
                dict(os.environ, EVIDENCE_FULL_RUN_ID=manifest['fullRunId']))
            manifest['stages'].append(dict(stage, name=name))
            write(path, manifest)
            require(not stage.get('timedOut'), '完整运行触及上限；所有后代进程已停止')
            require(stage['exitCode'] == 0, '完整运行阶段失败：' + name)
        same_snapshot(manifest)
        manifest['artifactSha256'] = {name: audit.digest(checked_path(folder, name)) for name in names}
        manifest['status'] = 'passed'
    except (ValueError, OSError, subprocess.SubprocessError, KeyboardInterrupt) as error:
        manifest['status'] = 'timed-out' if any(stage.get('timedOut') for stage in manifest['stages']) else 'failed'
        manifest['error'] = str(error)
        raise
    finally:
        manifest.update(finishedAtNs=time.time_ns(), elapsedSeconds=time.monotonic() - started)
        write(path, manifest)
    try:
        result = verify(path)
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        manifest.update(status='failed', error=str(error))
        write(path, manifest)
        raise
    manifest['formalAcceptance'] = True
    write(path, manifest)
    return result


def verify(path):
    """重验当前源码、同轮来源与逐用例实际值；不能追认独立局部报告。"""
    folder, manifest = path.resolve().parent, read(path)
    require(manifest.get('schemaVersion') == 1 and manifest.get('status') == 'passed', '完整运行尚未成功')
    require(audit.re.fullmatch(r'[0-9a-f]{32}', manifest.get('fullRunId', '')), '完整运行身份无效')
    same_snapshot(manifest)
    catalog = frozen()
    require(manifest['upstreamCommit'] == catalog['upstreamCommit']
            and manifest['casesTotal'] == sum(len(file['cases']) for file in catalog['files']),
            '完整运行范围或版本不一致')
    interface = manifest['interface']
    names = artifact_names(interface)
    require(set(manifest['artifactSha256']) == set(names), '完整运行文件集合不完整或多出局部报告')
    for name in names:
        require(audit.digest(checked_path(folder, name)) == manifest['artifactSha256'][name],
                '完整运行文件摘要不同：' + name)
    require(manifest['inputPlanSha256'] == audit.digest(folder / 'input-plan.json'), '运行前输入计划不同')
    commands = commands_for(interface, folder)
    require([stage.get('name') for stage in manifest['stages']] == list(STAGES), '完整执行顺序或阶段缺失')
    last = manifest['startedAtNs']
    for stage, command in zip(manifest['stages'], commands):
        require(stage['command'] == command and type(stage.get('pid')) is int and stage['pid'] > 0
                and type(stage['exitCode']) is int and stage['exitCode'] == 0 and not stage.get('timedOut'),
                '完整运行命令不同或阶段未成功')
        require(0 < last <= stage['startedAtNs'] <= stage['finishedAtNs'] <= manifest['finishedAtNs'],
                '运行时间不连续；禁止拼接独立报告')
        require(stage['logSha256'] == audit.digest(folder / (stage['name'] + '.log')), '子进程日志摘要不同')
        last = stage['finishedAtNs']
    timeout = manifest['timeoutMinutes']
    require(timeout in (90, 180) and 0 < manifest['elapsedSeconds'] <= timeout * 60 + 5,
            '完整运行超出明确上限')
    if timeout == 180:
        retry = manifest.get('retryAfter')
        require(isinstance(retry, dict) and audit.digest(retry['path']) == retry['sha256'], '重试来源缺失或被篡改')
        validate_retry(timeout, Path(retry['path']), snapshot(), interface, manifest['inputPlanSha256'])
    args = {'catalog': str(TASK / 'module-tests.json'), 'mapping': str(TASK / 'test-map.json'),
            'input_plan': str(folder / 'input-plan.json'), 'java_revision': manifest['javaRevision'],
            'module': [], 'command': 'check', 'observations': str(folder / 'parity-results.json')}
    for index, side in enumerate(('ts', 'java')):
        child = read(folder / (side + '-run.json'))
        require(child.get('fullRunId') == manifest['fullRunId']
                and child.get('fullRunProducerSha256') == audit.digest(__file__),
                '采集子进程缺少本轮联合身份或来自独立局部运行：' + side)
        stage = manifest['stages'][index]
        require(stage['startedAtNs'] <= child['startedAtNs'] <= child['finishedAtNs'] <= stage['finishedAtNs'],
                '采集不属于本轮真实子进程时间窗：' + side)
        require(child['command'] == [part.replace('{runDir}', str(folder)) for part in interface[side + 'Command']],
                '采集命令不属于本轮：' + side)
        require(Path(child['logPath']).resolve() == folder / (side + '-run.json.log'), '采集日志来自本轮目录外')
        for kind in ('inputs', 'assertions'):
            args[side + '_' + kind] = str(folder / (side + '-' + kind + '.jsonl'))
        args[side + '_run_manifest'] = str(folder / (side + '-run.json'))
        args[side + '_report'] = [str(checked_path(folder, name)) for name in interface[side + 'Reports']]
    result = audit.compare(SimpleNamespace(**args))
    require(result['cases'] == manifest['casesTotal'], '逐用例核验未覆盖完整冻结范围')
    same_snapshot(manifest)
    return dict(result, fullRunId=manifest['fullRunId'], javaRevision=manifest['javaRevision'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    run = sub.add_parser('run', help='宿主提权执行，必须已接入完整双侧适配器')
    run.add_argument('--config', type=Path, default=TASK / 'full-evidence-locals.json')
    run.add_argument('--run-dir', type=Path, required=True)
    run.add_argument('--timeout-minutes', type=int, choices=(90, 180), default=90)
    run.add_argument('--retry-after', type=Path, help='180 分钟重跑必须引用实际 90 分钟超时的 full-run.json')
    check = sub.add_parser('verify', help='只读重验来源、原始报告及逐用例证据')
    check.add_argument('manifest', type=Path)
    side = sub.add_parser('capture-side', help='内部子进程入口；禁止追认现有报告')
    side.add_argument('--side', choices=('ts', 'java'), required=True)
    for name in ('catalog', 'mapping', 'input-plan', 'inputs', 'assertions', 'output'):
        side.add_argument('--' + name, required=True)
    side.add_argument('--report', action='append', required=True)
    side.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        if args.action == 'capture-side':
            print(json.dumps(capture_side(args), ensure_ascii=False))
            return 0
        result = capture(args.config, args.run_dir.resolve(), args.timeout_minutes, args.retry_after) \
            if args.action == 'run' else verify(args.manifest)
        print(json.dumps({'status': 'PASS', **result}, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
