#!/usr/bin/env python3
"""路径 B：逐局部串行 TS 采集，合并成单轮全量 TS 证据（ts-inputs / ts-assertions / ts-jest）。

用法（作为 fullRun.tsCommand）：
    python3 run-full-ts-serial.py --run-dir <runDir> --report ts-jest.json

自测子集（--allow-partial 才允许覆盖不足）：
    python3 run-full-ts-serial.py --run-dir <dir> --report ts-jest.json \
        --locals broadcaster,chronicle,normative-vectors,spend-additional --allow-partial

设计要点：

1. 每个标准局部在自己的子目录 `<runDir>/local/<局部>/` 里跑它**已跑通的** TS 适配器；
   `EVIDENCE_SIDE/EVIDENCE_RUN_ID/EVIDENCE_INPUTS_PATH/EVIDENCE_ASSERTIONS_PATH/
   EVIDENCE_INPUT_PLAN` 全部指向本轮，因此所有行都带本轮 runId 与 `side=ts`。
2. 适配器形态分派**复用 `recapture-local.py` 的既有规则**（适配器源码里有 `--plan` 就传
   计划目录，否则传 `--replay` 语料），不另行发明第二套约定；带 `--local` 的适配器显式传
   局部名，避免它按计划目录名反查失败。
3. 合并三件套：
   - 输入：各局部 `inputs.jsonl` 按汇总计划重排（复用 `run-full-ts-capture.order_rows`）；
   - 断言：各局部**已转换好的** `assertions.jsonl` 按汇总计划拼接——同一原文件被两个局部
     采集时，直接拼 parity 轨迹会让 `emit-assertion-observations.py` 的
     `(文件, 用例, matcher)` 计数断档（原 TS matcher 序号不连续），逐局部转换没有这个问题；
     合并后的 parity 轨迹仍落盘，并做一次全局转换与逐局部结果交叉比对；
   - 报告：各局部 jest JSON 按文件去重后合并成一份（`audit-tests.compare_ts` 只要求一份
     报告覆盖全部原文件，不要求同一 jest 进程——与 `capture-legacy-side.py` 的既有口径一致）。
4. 除 `--allow-partial` 外，覆盖不足（用例/样本/断言/原文件少于汇总计划）即非零退出，防止
   “跑完但没有输入”的假绿；缺口逐条给出**局部名 + caseId/sampleId**。
"""
import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from pathlib import Path

TASK = Path(__file__).resolve().parent
CONFIG = TASK / 'full-evidence-locals.json'
CATALOG = TASK / 'module-tests.json'
MAPPING = TASK / 'test-map.json'


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


full_ts = load_module('full_ts_capture', TASK / 'run-full-ts-capture.py')
recapture = load_module('recapture_local', TASK / 'recapture-local.py')
preflight = load_module('full_preflight', TASK / 'full-evidence-preflight.py')
read_rows, write_rows = full_ts.read_rows, full_ts.write_rows
ENTRIES = TASK / 'ts-serial-entries.json'


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'))


def read_json(path):
    return json.loads(Path(path).read_text())


def standard_locals(config):
    return [item for item in config['locals']
            if item.get('capture') and item.get('captureKind') != 'specialized-local']


def jobs(config):
    """全部局部及其 TS 入口形态：标准局部按登记自动分派，其余取 ts-serial-entries.json。"""
    entries = read_json(ENTRIES)['entries'] if ENTRIES.is_file() else {}
    result = []
    for item in config['locals']:
        if item.get('capture') and item.get('captureKind') != 'specialized-local':
            result.append({'local': item['name'], 'shape': 'standard', 'item': item})
        elif item['name'] in entries:
            result.append({'local': item['name'], 'shape': entries[item['name']]['shape'],
                           'item': item, 'entry': entries[item['name']]})
    return result


def select(config, names, exclude):
    available = jobs(config)
    if names:
        wanted = {name.strip() for name in names if name.strip()}
        unknown = sorted(wanted - {job['local'] for job in available})
        if unknown:
            raise ValueError('未登记或无可用 TS 入口的局部：' + ','.join(unknown))
        available = [job for job in available if job['local'] in wanted]
    if exclude:
        dropped = {name.strip() for name in exclude if name.strip()}
        available = [job for job in available if job['local'] not in dropped]
    if not available:
        raise ValueError('没有选中任何局部')
    unresolved = [job['local'] for job in available if job['shape'] == 'unresolved']
    if unresolved:
        raise ValueError('这些局部没有可核实的 TS 入口：' + ','.join(unresolved))
    return available


def merge_plans(config):
    """按登记顺序合并全部局部计划；与 full-evidence-preflight.inspect 的 merged 口径一致。

    局部计划多存放在 .cache/ 下（不入版本库），其中 `comparisonRules` 由各 prepare 脚本
    按需写入。为避免某个局部漏写，这里依据 audit-tests.py 已固定的语义规则统一补齐：
    只按 SEMANTIC_CASES 与该用例自己的 assertionSites 登记，不新增任何规则，也不放宽
    任何比较——validate_plan 会逐条核对这些登记，多登记或错登记都会硬失败。
    """
    audit = preflight.audit
    merged = {}
    for item in config['locals']:
        for case_id, value in read_json(TASK / item['input_plan']).items():
            value = dict(value)
            fixed = audit.semantic_specs(case_id)
            if fixed:
                sites = value.get('assertionSites') or {}
                rules = dict(value.get('comparisonRules') or {})
                for identity in value.get('assertionIds') or []:
                    site = sites.get(identity)
                    if site in fixed:
                        rules[identity] = fixed[site][0]
                value['comparisonRules'] = rules
            if case_id in merged and canonical(merged[case_id]) != canonical(value):
                raise ValueError('同用例计划冲突：' + case_id + '／' + item['name'])
            merged[case_id] = value
    return merged


def local_plan(item):
    return read_json(TASK / item['input_plan'])


def order_plan(run_dir, config):
    """排序计划 = 登记顺序合并的全部局部计划；与运行目录里的 input-plan.json 交叉核对。"""
    plan = merge_plans(config)
    path = run_dir / 'local' / 'order-plan.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
    official, problems = run_dir / 'input-plan.json', []
    if official.is_file():
        given = read_json(official)
        if list(given) != list(plan):
            problems.append('本轮 input-plan.json 的用例集合或顺序与登记不符')
        else:
            differ = [case_id for case_id in plan
                      if canonical(given[case_id]) != canonical(plan[case_id])]
            if differ:
                problems.append('本轮 input-plan.json 与登记计划不同：'
                                + json.dumps(differ[:4], ensure_ascii=False))
    return plan, path, problems


SDK = TASK.parents[2] / 'reference/ts-stack/packages/sdk'


def replace_flag(args, flag, value):
    args = list(args)
    if flag in args:
        index = args.index(flag)
        if index + 1 < len(args) and not str(args[index + 1]).startswith('--'):
            args[index + 1] = value
        else:
            args.insert(index + 1, value)
        return args
    return args + [flag, value]


def standard_entry(job, subdir):
    """标准局部：沿用 recapture-local.py 的形态分派（--plan 计划目录 / --replay 语料）。"""
    item = job['item']
    catalog, mapping, replay = recapture.plan_replay(item)
    source = (TASK / item['capture']).read_text()
    command = ['python3', str(TASK / item['capture']), 'ts']
    if "add_argument('--plan'" in source:
        if "add_argument('--local'" in source:
            command += ['--local', item['name']]
        command += ['--plan', str((TASK / item['catalog']).parent.resolve())]
    else:
        command += ['--replay', str(replay.resolve())]
    command += ['--report', str((subdir / 'ts-jest.json').resolve())]
    return command, (TASK / item['input_plan']).resolve(), catalog.resolve(), mapping.resolve()


def adapter_entry(job, subdir):
    """旧管线局部：按它自己登记过的原始命令还原入口，只把报告与轨迹目录指到本轮子目录。"""
    entry, item = job['entry'], job['item']
    args = replace_flag(entry['args'], '--report', str((subdir / 'ts-jest.json').resolve()))
    if '--raw-dir' in args:
        # 适配器自己用 mkdir(exist_ok=False) 建这个目录，这里只能清掉残留、不能预先创建。
        raw_dir = subdir / 'ts-raw'
        shutil.rmtree(raw_dir, ignore_errors=True)
        args = replace_flag(args, '--raw-dir', str(raw_dir))
    command = [sys.executable, str(TASK / entry['script']), 'ts', *args]
    plan = (TASK / entry['plan']).resolve()
    catalog = (TASK / item['catalog']).resolve() if item.get('catalog') else None
    mapping = (TASK / item['mapping']).resolve() if item.get('mapping') else None
    return command, plan, catalog, mapping


def plan_fragment(job, subdir):
    """直写型局部：清单/映射取登记，或按计划从全局清单投影（deriveCatalogFromPlan）。"""
    item = job['item']
    plan = (TASK / job['entry']['plan']).resolve()
    if item.get('catalog'):
        return plan, (TASK / item['catalog']).resolve(), (TASK / item['mapping']).resolve()
    local_catalog, local_mapping = preflight.fragment_from_plan(
        read_json(CATALOG), read_json(MAPPING), read_json(plan))
    folder = subdir / 'plan'
    folder.mkdir(parents=True, exist_ok=True)
    for name, value in (('catalog.json', local_catalog), ('mapping.json', local_mapping),
                        ('input-plan.json', read_json(plan))):
        (folder / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return plan, folder / 'catalog.json', folder / 'mapping.json'


def direct_entry(job, subdir):
    """直写型专用局部：探针自己写本轮输入，断言走共享 capture-parity 轨迹。"""
    entry = job['entry']
    command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
               '--watchman=false', '--runTestsByPath', entry['file'], '--setupFilesAfterEnv',
               str(TASK / 'ts-offline-guard.cjs'), str(TASK / entry['probe']),
               str(TASK / 'capture-parity.cjs'), '--json',
               '--outputFile=' + str((subdir / 'ts-jest.json').resolve())]
    plan, catalog, mapping = plan_fragment(job, subdir)
    return command, plan, catalog, mapping


def vector_entry(job, subdir):
    """共享向量局部：用它们自己的 *-vector-evidence.py ts 子命令。"""
    entry, item = job['entry'], job['item']
    folder = subdir / 'vector'
    command = [sys.executable, str(TASK / entry['script']), 'ts',
               '--plan', str((TASK / item['input_plan']).parent.resolve()),
               '--output', str(folder)]
    return command, (TASK / item['input_plan']).resolve(), None, None


def convert_assertions(subdir, plan, catalog, mapping, run_id):
    """把本轮共享 parity 轨迹按本局部计划转成断言行（直写型局部用）。"""
    raw = subdir / 'ts-assertions.raw.jsonl'
    if not raw.is_file() or not raw.stat().st_size:
        return '缺少共享断言轨迹：' + str(raw)
    command = ['python3', str(TASK / 'emit-assertion-observations.py'), '--catalog', str(catalog),
               '--mapping', str(mapping), '--plan', str(plan), '--side', 'ts', '--raw', str(raw),
               '--run-id', run_id, '--output', str(subdir / 'assertions.jsonl'),
               # 原文件里还有别的局部/未计划用例的断言行；与本轮无关的行按既有口径跳过。
               '--allow-ts-extra']
    result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
    return None if not result.returncode else (result.stderr or result.stdout)[-600:]


def collect_vector(subdir):
    folder = subdir / 'vector'
    for source, target in (('inputs.jsonl', 'inputs.jsonl'), ('assertions.jsonl', 'assertions.jsonl'),
                           ('jest.json', 'ts-jest.json'),
                           ('assertions.raw.jsonl', 'ts-assertions.raw.jsonl')):
        origin = folder / source
        if origin.is_file():
            (subdir / target).write_bytes(origin.read_bytes())
    return None if (subdir / 'inputs.jsonl').is_file() else '向量证据脚本没有产出 inputs.jsonl'


def entry_for(job, subdir):
    if job['shape'] == 'standard':
        return standard_entry(job, subdir)
    if job['shape'] == 'adapter':
        return adapter_entry(job, subdir)
    if job['shape'] == 'direct':
        return direct_entry(job, subdir)
    return vector_entry(job, subdir)


def local_environment(run_id, subdir, plan_path):
    env = dict(os.environ)
    env['EVIDENCE_SIDE'] = 'ts'
    env['EVIDENCE_RUN_ID'] = run_id
    env['EVIDENCE_INPUTS_PATH'] = str(subdir / 'inputs.jsonl')
    env['EVIDENCE_ASSERTIONS_PATH'] = str(subdir / 'assertions.jsonl')
    env['EVIDENCE_INPUT_PLAN'] = str(plan_path)
    # ts-offline-guard.cjs / capture-parity.cjs 要求显式给出路径；适配器会覆盖成自己的路径。
    env.setdefault('MIGRATION_NETWORK_LOG', str(subdir / 'ts-network.jsonl'))
    env.setdefault('MIGRATION_PARITY_TS_OBSERVATIONS', str(subdir / 'ts-assertions.raw.jsonl'))
    return env


def rows_of(path):
    return read_rows(path) if Path(path).is_file() else []


def merge_extra_probes(job, subdir, run_id, plan_path, timeout):
    """额外直写探针：独立 jest 调用采集，并按登记的 `replaces` 覆盖入口探针的同身份行。

    必须独立调用：多个直写探针在同一次 jest 里会争用同一个模块工厂（`jest.doMock` 后注册者生效），
    而且同一 (caseId, sampleId) 会被两个探针各写一行，破坏「逐用例样本唯一」。本函数只并入输入行；
    额外调用的断言轨迹写进丢弃文件（入口调用已经覆盖全部用例的断言）。
    `replaces` 之外的覆盖、以及入口运行没有的身份，一律报错而不是静默接受。
    """
    extras = job.get('entry', {}).get('extraProbes') or []
    if not extras:
        return None
    inputs = subdir / 'inputs.jsonl'
    rows = rows_of(inputs)
    index = {(row.get('caseId'), row.get('sampleId')): position for position, row in enumerate(rows)}
    replaced = []
    for number, extra in enumerate(extras, 1):
        probe, allowed = extra['probe'], set(extra['replaces'])
        stem = subdir / ('extra-probe-' + str(number))
        command = [str(TASK / 'pnpm.sh'), '--dir', str(SDK), 'exec', 'jest', '--runInBand',
                   '--watchman=false', '--runTestsByPath', job['entry']['file'], '--setupFilesAfterEnv',
                   str(TASK / 'ts-offline-guard.cjs'), str(TASK / probe), str(TASK / 'capture-parity.cjs'),
                   '--json', '--outputFile=' + str(stem.with_suffix('.jest.json'))]
        env = local_environment(run_id, subdir, plan_path)
        env.update(EVIDENCE_INPUTS_PATH=str(stem.with_suffix('.inputs.jsonl')),
                   EVIDENCE_ASSERTIONS_PATH=str(stem.with_suffix('.assertions.jsonl')),
                   MIGRATION_PARITY_TS_OBSERVATIONS=str(stem.with_suffix('.parity.jsonl')),
                   MIGRATION_NETWORK_LOG=str(stem.with_suffix('.network.jsonl')))
        log = subdir / ('extra-probe-' + str(number) + '.log')
        try:
            with log.open('w') as stream:
                result = subprocess.run(command, cwd=TASK, env=env, stdout=stream,
                                        stderr=subprocess.STDOUT, timeout=timeout)
        except (subprocess.TimeoutExpired, OSError) as error:
            return f'{probe} 无法完成：{error}'
        if result.returncode:
            return f'{probe} 退出码非零（日志 {log.name}）'
        produced = rows_of(stem.with_suffix('.inputs.jsonl'))
        if not produced:
            return f'{probe} 未产出输入行'
        for row in produced:
            key = (row.get('caseId'), row.get('sampleId'))
            if key not in index:
                return f'{probe} 产出了入口运行没有的身份：{key}'
            if key[0] not in allowed:
                return f'{probe} 未登记替换该 caseId：{key[0]}'
            rows[index[key]] = row
            replaced.append({'caseId': key[0], 'sampleId': key[1], 'probe': probe})
    inputs.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in rows))
    return replaced


def order_rows(rows, plan, plan_path):
    """按汇总计划重排去重，复用 run-full-ts-capture.order_rows。

    该文件与路径 A 的修复并行演进，第二参数在两种版本里分别是计划字典与计划文件路径；
    两种签名都按原语义兼容，避免把对方的重构当成缺陷。
    """
    try:
        return full_ts.order_rows(rows, plan, None)
    except AttributeError:
        return full_ts.order_rows(rows, plan_path, None)


def validate_side(record, rows, label, run_id):
    wrong = sorted({str(row.get('runId')) for row in rows if row.get('runId') != run_id})
    sides = sorted({str(row.get('side')) for row in rows if row.get('side') != 'ts'})
    if wrong:
        record['problems'].append(f'{label} 存在非本轮 runId 的行：{wrong[:3]}')
    if sides:
        record['problems'].append(f'{label} 存在非 ts 侧别的行：{sides[:3]}')


def check_sequence(record, rows, plan, field, label):
    """逐用例核对标识序列与局部计划完全一致；不一致时报局部名 + caseId + 具体标识。"""
    identity = 'sampleId' if field == 'sampleIds' else 'assertionId'
    grouped = {}
    for row in rows:
        grouped.setdefault(row.get('caseId'), []).append(row.get(identity))
    for case_id, expected in plan.items():
        got = grouped.pop(case_id, [])
        if got != expected[field]:
            record['problems'].append(
                f'{label} 与计划不符（局部 {record["local"]}／case {case_id}）：'
                + json.dumps({'缺失': [x for x in expected[field] if x not in got][:4],
                              '多余': [x for x in got if x not in expected[field]][:4],
                              '数量': [len(expected[field]), len(got)]}, ensure_ascii=False))
    for case_id, got in list(grouped.items())[:4]:
        record['problems'].append(f'{label} 出现计划外用例（局部 {record["local"]}）：{case_id}／{got[:3]}')


def capture_one(job, run_dir, run_id, timeout, resume):
    item, name = job['item'], job['local']
    subdir = (run_dir / 'local' / name).resolve()
    done = subdir / 'local-run.json'
    if resume and done.is_file():
        saved = read_json(done)
        if saved.get('status') == 'passed' and saved.get('runId') == run_id:
            saved['resumed'] = True
            return saved
    subdir.mkdir(parents=True, exist_ok=True)
    for stale in ('inputs.jsonl', 'assertions.jsonl', 'ts-jest.json', 'ts-assertions.raw.jsonl'):
        (subdir / stale).unlink(missing_ok=True)
    if job['shape'] == 'vector':
        # 向量证据脚本要求输出目录必须新建；失败重跑时清掉上一次的残留。
        shutil.rmtree(subdir / 'vector', ignore_errors=True)
    record = {'local': name, 'shape': job['shape'], 'subdir': str(subdir), 'runId': run_id,
              'status': 'running', 'problems': []}
    try:
        command, plan_path, catalog, mapping = entry_for(job, subdir)
    except (ValueError, OSError, KeyError, TypeError) as error:
        record.update(status='failed', error='入口不可用：' + str(error))
        done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        return record
    record.update(command=command, plan=str(plan_path),
                  capture=item.get('capture') or job.get('entry', {}).get('script'),
                  catalog=str(catalog) if catalog else None,
                  mapping=str(mapping) if mapping else None,
                  emitterConversion=(job['shape'] == 'direct' or (
                      job['shape'] == 'standard'
                      and 'emit-assertion-observations' in (TASK / item['capture']).read_text()
                      and 'normalized' not in (TASK / item['capture']).read_text())))
    log = subdir / 'ts-capture.log'
    started = time.monotonic()
    try:
        with log.open('w') as stream:
            result = subprocess.run(command, cwd=TASK,
                                    env=local_environment(run_id, subdir, plan_path),
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
        record['exitCode'] = result.returncode
    except subprocess.TimeoutExpired:
        record.update(status='failed', error=f'局部超时（{timeout} 秒）')
    except OSError as error:
        record.update(status='failed', error='无法启动适配器：' + str(error))
    record['elapsedSeconds'] = round(time.monotonic() - started, 1)
    if record.get('error'):
        record['logTail'] = log.read_text(errors='replace')[-1200:] if log.is_file() else ''
        done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        return record
    if record['exitCode']:
        record['problems'].append(f'入口命令退出码非零：{record["exitCode"]}')
    if job['shape'] == 'direct' and not record['problems']:
        replaced = merge_extra_probes(job, subdir, run_id, plan_path, timeout)
        if isinstance(replaced, str):
            record['problems'].append('额外探针失败：' + replaced)
        elif replaced:
            record['extraProbes'] = replaced
    if job['shape'] == 'vector' and not record['problems']:
        failure = collect_vector(subdir)
        if failure:
            record['problems'].append(failure)
    if job['shape'] == 'direct' and not record['problems']:
        failure = convert_assertions(subdir, plan_path, catalog, mapping, run_id)
        if failure:
            record['problems'].append('断言转换失败：' + failure)
    inputs, assertions, report = subdir / 'inputs.jsonl', subdir / 'assertions.jsonl', subdir / 'ts-jest.json'
    for path, label in ((inputs, 'TS 输入'), (assertions, 'TS 断言')):
        if not path.is_file() or not path.stat().st_size:
            record['problems'].append(f'{label}缺失或为空：{path.name}')
    plan = read_json(plan_path)
    record['cases'] = len(plan)
    if not record['problems']:
        input_rows, assertion_rows = rows_of(inputs), rows_of(assertions)
        validate_side(record, input_rows, 'TS 输入', run_id)
        validate_side(record, assertion_rows, 'TS 断言', run_id)
        check_sequence(record, input_rows, plan, 'sampleIds', 'TS 输入')
        check_sequence(record, assertion_rows, plan, 'assertionIds', 'TS 断言')
        data = read_json(report)
        summary = {key: data.get(key) for key in ('success', 'numTotalTests', 'numPassedTests',
                                                  'numFailedTests', 'numFailedTestSuites',
                                                  'numRuntimeErrorTestSuites')}
        if data.get('success') is not True or summary['numFailedTests'] or summary['numFailedTestSuites'] \
                or summary['numRuntimeErrorTestSuites'] or not summary['numTotalTests']:
            record['problems'].append('Jest 未全部通过：' + json.dumps(summary, ensure_ascii=False))
        record['jest'] = summary
        record['inputs'], record['assertions'] = len(input_rows), len(assertion_rows)
        raw = subdir / 'ts-assertions.raw.jsonl'
        record['parityRaw'] = raw.stat().st_size if raw.is_file() else 0
    record['status'] = 'failed' if record['problems'] else 'passed'
    if record['problems']:
        record['logTail'] = log.read_text(errors='replace')[-1200:] if log.is_file() else ''
    done.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record


def merge_inputs(records, plan, plan_path, selected_plan):
    rows = []
    for record in records:
        if record['status'] != 'passed':
            continue
        for row in rows_of(Path(record['subdir']) / 'inputs.jsonl'):
            rows.append(dict(row, _local=record['local']))
    clean = [{key: value for key, value in row.items() if key != '_local'} for row in rows]
    ordered, missing, extra, duplicates = order_rows(clean, plan, plan_path)
    owner = {(row.get('caseId'), row.get('sampleId')): row['_local'] for row in rows}
    scoped = [dict(row, local=owner.get((row['caseId'], row['sampleId']), '?'))
              for row in missing if row['caseId'] in selected_plan]
    return {'ordered': ordered, 'missing': missing, 'extra': extra, 'duplicates': duplicates,
            'scopedMissing': scoped}


def merge_assertions(records, plan):
    by_case, duplicates, problems = {}, [], []
    for record in records:
        if record['status'] != 'passed':
            continue
        for row in rows_of(Path(record['subdir']) / 'assertions.jsonl'):
            key = (row.get('caseId'), row.get('assertionId'))
            if key in by_case:
                duplicates.append({'local': record['local'], 'caseId': key[0], 'assertionId': key[1]})
                continue
            by_case[key] = (record['local'], row)
    ordered = []
    for case_id, expected in plan.items():
        for assertion_id in expected['assertionIds']:
            item = by_case.pop((case_id, assertion_id), None)
            if item is not None:
                ordered.append(item[1])
    for (case_id, assertion_id), (local, _) in list(by_case.items())[:10]:
        problems.append(f'计划外断言（局部 {local}）：{case_id}／{assertion_id}')
    return ordered, duplicates, problems


def case_key(row):
    return tuple(row.get('ancestorTitles') or []) + (row.get('title'),)


def merge_reports(records, report_path):
    """按文件去重合并逐局部 jest JSON；计数从合并后的 testResults 重算，不用各局部之和。

    一个局部可能产出多份报告（旧管线 `hex-bn` 用 `--kind both` 写 ts-jest.json 与
    ts-jest-bn.json，其适配器只在 Java 分支合并两份），因此这里收全部 `ts-jest*.json`。
    `compare_ts` 只要求一份报告覆盖全部原文件，不要求同一 Jest 进程。
    """
    results, seen, problems, locals_by_file, sources = [], {}, [], {}, {}
    for record in records:
        if record['status'] != 'passed':
            continue
        for path in sorted(Path(record['subdir']).glob('ts-jest*.json')):
            sources.setdefault(record['local'], []).append(path.name)
            for row in read_json(path).get('testResults') or []:
                name = str(row.get('name', '')).replace(chr(92), '/')
                if name in seen:
                    if sorted(map(case_key, row.get('assertionResults') or [])) != \
                            sorted(map(case_key, seen[name].get('assertionResults') or [])):
                        problems.append(f'同一原文件两次采集的用例集合不同：{name}')
                    continue
                if row.get('status') != 'passed':
                    problems.append('Jest 文件未通过：' + name)
                bad = [case_key(case) for case in row.get('assertionResults') or []
                       if case.get('status') != 'passed']
                if bad:
                    problems.append('Jest 存在失败/跳过用例：' + json.dumps(bad[:3], ensure_ascii=False))
                seen[name] = row
                results.append(row)
                locals_by_file[name] = record['local']
    tests = sum(len(row.get('assertionResults') or []) for row in results)
    merged = {'success': not problems, 'numTotalTestSuites': len(results), 'numTotalTests': tests,
              'numPassedTests': tests, 'numFailedTests': 0, 'numFailedTestSuites': 0,
              'numPendingTests': 0, 'numTodoTests': 0, 'numRuntimeErrorTestSuites': 0,
              'testResults': results}
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(merged, ensure_ascii=False) + '\n')
    return merged, problems, locals_by_file, sources


def emitter_conversion(record):
    """该局部的断言行是否由标准发射器当场产出；自写转换的局部不能按同一口径重放比对。"""
    if 'emitterConversion' in record:
        return record['emitterConversion']
    if record['shape'] == 'direct':
        return True
    if record['shape'] != 'standard':
        return False
    command = record.get('command') or []
    script = next((part for part in command if str(part).endswith('.py')), None)
    if not script or not (TASK / script).is_file():
        return False
    source = (TASK / script).read_text()
    # drbg29 这类适配器会先把轨迹规范化再交发射器，重放原始轨迹与当场结果必然不同。
    return 'emit-assertion-observations' in source and 'normalized' not in source


def per_local_check(records, run_id):
    """逐局部重放一次自己的轨迹→断言行，与当场产出的行逐条比对（仅限标准发射器口径的局部）。"""
    checked, skipped, failures = 0, [], []
    for record in records:
        if record['status'] != 'passed' or not record.get('parityRaw'):
            continue
        if not record.get('catalog') or not record.get('mapping'):
            continue
        if not emitter_conversion(record):
            skipped.append(record['local'])
            continue
        subdir = Path(record['subdir'])
        output = subdir / 'assertions.recheck.jsonl'
        command = ['python3', str(TASK / 'emit-assertion-observations.py'),
                   '--catalog', record['catalog'], '--mapping', record['mapping'],
                   '--plan', record['plan'], '--side', 'ts',
                   '--raw', str(subdir / 'ts-assertions.raw.jsonl'),
                   '--run-id', run_id, '--output', str(output), '--allow-ts-extra']
        result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
        if result.returncode:
            failures.append({'local': record['local'],
                             'error': (result.stderr or result.stdout)[-300:]})
            continue
        original = {(row['caseId'], row['assertionId']): canonical(row['value'])
                    for row in rows_of(subdir / 'assertions.jsonl')}
        replayed = {(row['caseId'], row['assertionId']): canonical(row['value'])
                    for row in rows_of(output)}
        if original != replayed:
            failures.append({'local': record['local'],
                             'missing': sorted(set(original) - set(replayed))[:3],
                             'extra': sorted(set(replayed) - set(original))[:3],
                             'differ': [key for key in set(original) & set(replayed)
                                        if original[key] != replayed[key]][:3]})
        else:
            checked += 1
        output.unlink(missing_ok=True)
    return {'localsChecked': checked, 'skippedCustomConversion': skipped, 'failures': failures}


def cross_check(run_dir, records, run_id, jobs_list):
    """合并可提供 parity 轨迹的局部轨迹做一次全局转换，与逐局部结果逐行比对。"""
    rawable = [record for record in records
               if record['status'] == 'passed' and record.get('parityRaw')]
    merged_raw = run_dir / 'ts-assertions.raw.jsonl'
    with merged_raw.open('wb') as out:
        for record in rawable:
            out.write((Path(record['subdir']) / 'ts-assertions.raw.jsonl').read_bytes())
    by_name = {job['local']: job['item'] for job in jobs_list}
    raw_plan = {}
    for record in rawable:
        raw_plan.update(local_plan(by_name[record['local']]))
    plan_file = run_dir / 'local' / 'raw-plan.json'
    plan_file.write_text(json.dumps(raw_plan, ensure_ascii=False, indent=2) + '\n')
    output = run_dir / 'local' / 'ts-assertions.global.jsonl'
    command = ['python3', str(TASK / 'emit-assertion-observations.py'), '--catalog', str(CATALOG),
               '--mapping', str(MAPPING), '--plan', str(plan_file), '--side', 'ts',
               '--raw', str(merged_raw), '--run-id', run_id, '--output', str(output)]
    result = subprocess.run(command, cwd=TASK, capture_output=True, text=True)
    summary = {'ok': False, 'locals': len(rawable), 'rawBytes': merged_raw.stat().st_size}
    if result.returncode:
        summary['error'] = (result.stderr or result.stdout)[-600:]
        return summary
    converted, primary = rows_of(output), []
    for record in rawable:
        primary.extend(rows_of(Path(record['subdir']) / 'assertions.jsonl'))
    converted.sort(key=lambda row: (row['caseId'], row['assertionId']))
    primary.sort(key=lambda row: (row['caseId'], row['assertionId']))
    if [row['assertionId'] for row in converted] != [row['assertionId'] for row in primary] \
            or [row['caseId'] for row in converted] != [row['caseId'] for row in primary]:
        left = {(row['caseId'], row['assertionId']) for row in converted}
        right = {(row['caseId'], row['assertionId']) for row in primary}
        summary['mismatches'] = [{'missing': sorted(left - right)[:4], 'extra': sorted(right - left)[:4]}]
        return summary
    mismatches = [{'caseId': left['caseId'], 'assertionId': left['assertionId']}
                  for left, right in zip(converted, primary)
                  if canonical(left['value']) != canonical(right['value'])]
    summary.update(ok=not mismatches, assertions=len(converted), mismatches=mismatches[:4])
    return summary


def coverage_of(records, covered, plan, catalog, locals_by_file, jobs_list):
    files = {file['path']: file for file in catalog['files']}
    covered_files = {}
    for name, local in locals_by_file.items():
        for path in files:
            if name == path or name.endswith('/' + path):
                covered_files[path] = local
    owner = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    missing_cases = [case_id for case_id in plan if case_id not in covered]
    missing_files = sorted(set(files) - set(covered_files))
    return {'filesCovered': len(covered_files), 'filesPlanned': len(files),
            'casesPlanned': len(plan), 'casesCovered': len(plan) - len(missing_cases),
            'samplesPlanned': sum(len(v['sampleIds']) for v in plan.values()),
            'assertionsPlanned': sum(len(v['assertionIds']) for v in plan.values()),
            'missingFiles': missing_files,
            'missingFileOwners': {path: sorted(job['local'] for job in jobs_list
                                               if any(case_id in local_plan(job['item']) for case_id in
                                                      [case['id'] for case in files[path]['cases']]))
                                  for path in missing_files},
            'missingCases': len(missing_cases),
            'missingSamples': sum(len(plan[case_id]['sampleIds']) for case_id in missing_cases),
            'missingCaseSample': [{'caseId': case_id, 'file': owner.get(case_id),
                                   'samples': len(plan[case_id]['sampleIds'])}
                                  for case_id in missing_cases[:8]],
            'casesWithRows': len(covered),
            'localsSelected': len(records),
            'localsFailed': [record['local'] for record in records if record['status'] != 'passed']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, default=Path('ts-jest.json'))
    parser.add_argument('--locals', action='append', default=[], help='自测用：逗号分隔的局部名')
    parser.add_argument('--exclude', action='append', default=[])
    parser.add_argument('--timeout-seconds', type=int, default=7200)
    parser.add_argument('--allow-partial', action='store_true', help='允许覆盖不足（仅子集自测）')
    parser.add_argument('--no-cross-check', action='store_true')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--run-id', help='固定本轮身份（配合 --resume 续跑时用）')
    parser.add_argument('--verify-only', action='store_true',
                        help='不重跑，只按已有 local-run.json 重做合并、对账与覆盖校验')
    parser.add_argument('--config', type=Path, default=CONFIG)
    options = parser.parse_args()

    run_dir = options.run_dir.resolve()
    if not run_dir.is_dir():
        raise SystemExit('运行目录不存在：' + str(run_dir))
    config = read_json(options.config)
    names = [name for chunk in options.locals for name in chunk.split(',')]
    exclude = [name for chunk in options.exclude for name in chunk.split(',')]
    jobs_list = select(config, names, exclude)
    run_id = options.run_id or os.environ.get('EVIDENCE_RUN_ID') or uuid.uuid4().hex
    if options.verify_only and not (options.run_id or os.environ.get('EVIDENCE_RUN_ID')):
        # 只读复核时沿用已落盘记录里的本轮身份，否则逐行身份校验会误报。
        for candidate in jobs_list:
            done = run_dir / 'local' / candidate['local'] / 'local-run.json'
            if done.is_file():
                run_id = read_json(done).get('runId') or run_id
                break
    report_path = options.report if options.report.is_absolute() else run_dir / options.report
    plan, plan_path, problems = order_plan(run_dir, config)
    print(json.dumps({'locals': len(jobs_list), 'runId': run_id, 'runDir': str(run_dir),
                      'planCases': len(plan), 'report': str(report_path)}, ensure_ascii=False))

    records, started = [], time.monotonic()
    for index, job in enumerate(jobs_list, 1):
        if options.verify_only:
            done = run_dir / 'local' / job['local'] / 'local-run.json'
            if not done.is_file():
                raise SystemExit('缺少局部记录，无法只读复核：' + str(done))
            record = read_json(done)
            if record.get('status') != 'passed':
                record.setdefault('problems', [])
        else:
            record = capture_one(job, run_dir, run_id, options.timeout_seconds, options.resume)
            print(json.dumps({'step': f'{index}/{len(jobs_list)}', 'local': job['local'],
                              'status': record['status'], 'seconds': record.get('elapsedSeconds'),
                              'elapsed': round(time.monotonic() - started, 1)},
                             ensure_ascii=False), flush=True)
        records.append(record)

    selected_plan = {}
    for job in jobs_list:
        selected_plan.update(local_plan(job['item']))
    merge = merge_inputs(records, plan, plan_path, selected_plan)
    if merge['scopedMissing']:
        problems.append(f"选中范围内缺少 {len(merge['scopedMissing'])} 个计划样本："
                        + json.dumps(merge['scopedMissing'][:5], ensure_ascii=False))
    if merge['duplicates']:
        problems.append('本轮输入出现重复 (caseId, sampleId)：'
                        + json.dumps(merge['duplicates'][:5], ensure_ascii=False))
    if merge['extra']:
        problems.append('本轮输入出现计划外样本：' + json.dumps(merge['extra'][:5], ensure_ascii=False))
    for record in records:
        problems.extend(f'{record["local"]}: {item}' for item in record['problems'])
    write_rows(run_dir / 'ts-inputs.jsonl', merge['ordered'])

    assertions, duplicates, extra_assertions = merge_assertions(records, plan)
    if duplicates:
        problems.append('本轮断言出现重复 (caseId, assertionId)：'
                        + json.dumps(duplicates[:5], ensure_ascii=False))
    problems.extend(extra_assertions)
    present = {row['caseId'] for row in assertions}
    missing_assertions = [case_id for case_id in selected_plan if case_id not in present]
    if missing_assertions:
        problems.append(f'选中范围内缺少 {len(missing_assertions)} 个用例的断言：'
                        + json.dumps(missing_assertions[:5], ensure_ascii=False))
    write_rows(run_dir / 'ts-assertions.jsonl', assertions)

    merged, report_problems, locals_by_file, report_sources = merge_reports(records, report_path)
    problems.extend(report_problems)
    # 与最终门禁同一口径复核 TS 报告：必须覆盖全部原文件且逐用例名一致。
    compare = {'skipped': True}
    if not options.allow_partial:
        try:
            compare = preflight.audit.compare_ts(read_json(CATALOG), [report_path])
        except (ValueError, KeyError, TypeError) as error:
            compare = {'ok': False, 'error': str(error)[:400]}
            problems.append('TS 报告未通过完整口径核对：' + str(error)[:400])

    recheck = {'skipped': True}
    if not options.no_cross_check and assertions:
        recheck = per_local_check(records, run_id)
        if recheck['failures']:
            problems.append('逐局部轨迹重放与当场产出的断言行不一致：'
                            + json.dumps(recheck['failures'][:3], ensure_ascii=False)[:500])
    # 合并轨迹的全局转换只作诊断：同一原文件被多个局部采集时，合并轨迹里同一
    # (文件, 用例, matcher) 会出现多次，序号口径必然断档（这正是路径 A 失败的原因），
    # 因此断言行以各局部当场转换的结果为准，这里只如实记录诊断结论。
    diagnostic = {'skipped': True}
    if not options.no_cross_check and assertions:
        diagnostic = cross_check(run_dir, records, run_id, jobs_list)

    # 覆盖按“真正写出的行”统计：局部失败时它的计划仍在选中范围内，不能算作已覆盖。
    present_cases = ({row['caseId'] for row in merge['ordered']}
                     | {row['caseId'] for row in assertions})
    coverage = coverage_of(records, present_cases, plan, read_json(CATALOG), locals_by_file, jobs_list)
    if not options.allow_partial:
        if coverage['missingCases']:
            problems.append(f"覆盖不足：缺少 {coverage['missingCases']} 个用例／"
                            f"{coverage['missingSamples']} 个样本，缺 {len(coverage['missingFiles'])} 个原文件")
        if coverage['filesCovered'] != coverage['filesPlanned']:
            problems.append('Jest 报告未覆盖全部原文件：'
                            + json.dumps(coverage['missingFiles'][:6], ensure_ascii=False))
    coverage.update(runId=run_id, runDir=str(run_dir), report=str(report_path),
                    shapes={shape: sum(1 for record in records if record['shape'] == shape)
                            for shape in sorted({record['shape'] for record in records})},
                    inputsWritten=len(merge['ordered']), assertionsWritten=len(assertions),
                    jestFiles=len(merged['testResults']), jestTests=merged['numTotalTests'],
                    jestReportSources={local: names for local, names in report_sources.items()
                                       if len(names) > 1},
                    crossCheck=recheck, mergedRawConversion=diagnostic, compareTs=compare,
                    partial=options.allow_partial,
                    elapsedSeconds=round(time.monotonic() - started, 1), problems=problems)
    (run_dir / 'ts-serial-report.json').write_text(json.dumps(coverage, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({key: coverage[key] for key in
                      ('localsSelected', 'localsFailed', 'filesCovered', 'filesPlanned', 'casesPlanned',
                       'casesCovered', 'missingCases', 'missingSamples', 'inputsWritten',
                       'assertionsWritten')}, ensure_ascii=False))
    for problem in problems:
        print('TS-SERIAL-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
