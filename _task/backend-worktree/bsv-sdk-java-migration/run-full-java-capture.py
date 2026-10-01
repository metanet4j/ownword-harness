#!/usr/bin/env python3
"""全量 Java 采集：把本轮 TS 汇总输入接到全部 Java 重放，跑无过滤 clean test，收全部 Surefire 报告。

用法（全量运行的 javaCommand）：
    python3 run-full-java-capture.py --run-dir <runDir> --reports java-surefire.xml clean test

命令尾部的 clean test 是固定阶段声明（evidence-bundle 与 preflight 都要求最终 Java 命令里出现
无过滤的 clean test）；脚本内部始终执行无过滤 clean test。

环境变量由 evidence-bundle capture 注入；Java 断言原始轨迹写到 EVIDENCE_ASSERTIONS_PATH 旁的
java-assertions.raw.jsonl，再用 emit-assertion-observations.py 转成最终断言观察。
"""
import argparse
import fcntl
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TASK = Path(__file__).resolve().parent
PROJECT = TASK / 'metanet4j-bsv-sdk'
SUREFIRE = PROJECT / 'target/surefire-reports'
LOCK = TASK / '.cache/run.lock'
JAVA_TEST_ROOT = PROJECT / 'src/test/java'
# 只排除这一个退役局部的语料变量；不要顺手扩大范围（理由见 java_ts_input_envs 的说明）。
EXCLUDED_TS_INPUT_ENVS = ('MIGRATION_HASH_PBKDF2_TS_INPUTS',)
# A1 共享向量局部（2599 例）：`VectorInputRecorder` 把原始调用写到这个变量，Maven 结束后再由
# java-vector-inputs.py 归一化成标准行追加进 java-inputs.jsonl。
VECTOR_INPUTS_ENV = 'MIGRATION_VECTOR_JAVA_INPUTS'
VECTOR_INPUTS_SCRIPT = 'java-vector-inputs.py'
# A2 旧接口局部（736 例）：局部 → Java 入口映射表（build-java-serial-entries.py 生成）与其后置转换器。
JAVA_SERIAL_ENTRIES = TASK / 'java-serial-entries.json'
JAVA_SERIAL_CONVERTER = 'full-java-serial-convert.py'
# surefire fork 的堆上限：full-run-15 实测该 fork 在 AESGCMManualTest 处被内核 OOM 杀掉
# （dmesg：`Killed process … (java) anon-rss:4183468kB`；Maven：`Process Exit Code: 137`），
# 因为默认上限（物理内存 1/4 ≈ 3.9 GiB）允许它涨到 4.18 GiB RSS，而宿主机常驻 infra 容器 +
# 编辑器已占约 6 GiB、swap 用满。单点实测（同一用例、同一机器）：默认堆峰值 2230 MB 通过；
# `-Xmx2g` 报 `OutOfMemoryError: Java heap space`；`-Xmx2560m`／`-Xmx3g` 均 1/1 通过
# （峰值 2382／2236 MB）。取 3g：高于实测需求，又把 fork 的 RSS 封在约 3.2 GiB 内，不再被内核挑中。
# SDK 的 surefire 只配了 failIfNoTests、没有自带 argLine，因此这个 -DargLine 不会覆盖既有 JVM 参数。
MAVEN_ARG_LINE = '-Xmx3g'


def read_json(path):
    return json.loads(Path(path).read_text())


def java_ts_input_envs():
    """Java 测试源码里读的全部 MIGRATION_*_TS_INPUTS：本轮都要指向同一份 ts-inputs.jsonl。

    例外（EXCLUDED_TS_INPUT_ENVS）：`MIGRATION_HASH_PBKDF2_TS_INPUTS` 属于**已退役**局部
    `hash-pbkdf2-vectors` 的语料变量——`HashPbkdf2InputReplay.derive` 只在显式给出当年
    `call-0` 口径语料时才启用该 replay，指向本轮汇总输入会把它激活，而现行计划里这 13 个
    PBKDF2 用例的 sampleId 是标准局部 `hash` 的 `pbkdf2-01` 口径，于是整类报
    「PBKDF2 固定 TS 输入缺失或重复」。两条事实依据：①该变量全仓仅被
    `com/metanet4j/bsv/primitives/HashPbkdf2InputReplay.java` 读取；②不设置时 `derive()`
    直接走生产实现，而这些样本由 `HashTest` 主路径按 `pbkdf2-01` 正常消费（逐局部 `hash`
    运行的 java-inputs.jsonl 已证实），因此不覆盖它不会丢任何证据。
    """
    envs = set()
    for path in JAVA_TEST_ROOT.rglob('*.java'):
        envs.update(re.findall(r'System\.getenv\("(MIGRATION_[A-Z0-9_]*_TS_INPUTS)"\)',
                               path.read_text(errors='replace')))
    return sorted(envs - set(EXCLUDED_TS_INPUT_ENVS))


def java_property_replays():
    """仍靠 -Dmigration.* 冻结语料驱动的 Java 重放：本轮不消费 ts-inputs.jsonl，需要登记说明。

    注意属性名里允许连字符（`migration.origin-header.corpus`），早期版本的正则漏了这类名字。
    """
    rows = {}
    for path in JAVA_TEST_ROOT.rglob('*.java'):
        text = path.read_text(errors='replace')
        found = re.findall(r'System\.getProperty\("(migration\.[A-Za-z0-9_.-]+)"', text)
        found += re.findall(r'Boolean\.getBoolean\("(migration\.[A-Za-z0-9_.-]+)"', text)
        for prop in sorted(set(found)):
            rows.setdefault(prop, []).append(str(path.relative_to(PROJECT)))
    return {prop: sorted(set(files)) for prop, files in sorted(rows.items())}


def corpus_sample_ids(path):
    """冻结语料里逐用例的 sampleId：重放会把这些 sampleId 原样写进 java-inputs.jsonl，必须与计划一致。"""
    result = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get('caseId') and row.get('sampleId'):
            result.setdefault(row['caseId'], []).append(row['sampleId'])
    return result


def sample_id_problems(label, sample_ids, expected):
    """语料内 sampleId 与本轮 input-plan 的比对：不一致就没必要跑 Maven（bundle 必然报样本不符）。"""
    problems = []
    for case, ids in sorted(sample_ids.items()):
        want = expected.get(case, {}).get('sampleIds')
        if want is not None and ids != want:
            problems.append(f'{label} 的冻结语料 sampleId 与本轮计划不同：{case} '
                            f'语料 {ids[:2]} vs 计划 {want[:2]}')
    return problems


def serial_plan(run_dir):
    """按 java-serial-entries.json 准备 A2 注入（合并语料、校验引用、清理输出落点）。

    返回 `(properties, environment, summary, problems)`：properties 直接拼进 Maven 命令行。
    这里的数据全部来自 build-java-serial-entries.py 从「已跑通的单局部 Java 采集记录」提取并逐条
    核实过的入口（属性名被该局部 Java 源码读取、引用文件存在），本函数只做运行期展开与检查。
    """
    table = read_json(JAVA_SERIAL_ENTRIES) if JAVA_SERIAL_ENTRIES.is_file() else {}
    properties, environment = {}, {}
    summary, problems, substitutions = {}, [], []
    merged_names = set()
    plan_path = run_dir / 'input-plan.json'
    expected = read_json(plan_path) if plan_path.is_file() else {}
    for name, spec in table.get('mergedFiles', {}).items():
        output = Path(spec['output'].replace('{runDir}', str(run_dir)))
        lines, owner, sample_ids = [], {}, {}
        for member in spec['members']:
            for row in Path(member['corpus']).read_text().splitlines():
                if not row.strip():
                    continue
                parsed = json.loads(row)
                method = parsed.get('javaMethod')
                if method is None:
                    problems.append(f'{name} 的冻结语料缺 javaMethod：{member["corpus"]}')
                    continue
                if owner.setdefault(method, member['local']) != member['local']:
                    problems.append(f'{name} 的 javaMethod 跨局部重叠，合并会破坏按位置消费：{method}')
                if parsed.get('caseId') and parsed.get('sampleId'):
                    sample_ids.setdefault(parsed['caseId'], []).append(parsed['sampleId'])
                lines.append(row)
        problems.extend(sample_id_problems(name, sample_ids, expected))
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text('\n'.join(lines) + '\n')
        properties[name] = str(output)
        merged_names.add(name)
        summary[name] = {'output': str(output), 'members': len(spec['members']), 'rows': len(lines)}
    for local, entry in sorted(table.get('entries', {}).items()):
        for name, record in list(entry.get('properties', {}).items()) + \
                list(entry.get('env', {}).items()):
            if name in merged_names:
                continue
            value = record['value'].replace('{runDir}', str(run_dir))
            if record.get('role') == 'output':
                # 原始轨迹的落点：本轮必须是新文件，避免把上一轮的行当成本轮结果。
                path = Path(value)
                path.parent.mkdir(parents=True, exist_ok=True)
                if path.exists():
                    path.unlink()
            elif record['kind'] == 'runDir' and not Path(value).is_file():
                fallback = record.get('fallback')
                if fallback and Path(fallback).is_file():
                    substitutions.append({'local': local, 'name': name, 'missing': value,
                                          'used': fallback})
                    value = fallback
                else:
                    problems.append(f'{local} 的 {name} 缺少本轮输入文件：{value}')
            elif record['kind'] == 'file' and not Path(value).is_file():
                problems.append(f'{local} 的 {name} 引用文件不存在：{value}')
            elif record['kind'] == 'file' and name.rsplit('.', 1)[-1] in ('plan', 'corpus') \
                    and value.endswith('.jsonl'):
                # 重放会把语料里的 sampleId 原样写成 Java 输入行；与本轮计划不符就没必要跑 Maven。
                problems.extend(sample_id_problems(f'{local} 的 {name}',
                                                   corpus_sample_ids(value), expected))
            if name in entry.get('properties', {}):
                properties[name] = value
            else:
                environment[name] = value
    if substitutions:
        summary['substitutions'] = substitutions
    return properties, environment, summary, problems


DIGEST_KEYS = ('length', 'sha256')


def digest_summary(value):
    """识别 ParityRecorder 的「大数组摘要」：`{'type':'map','value':{'length','sha256'}}`。"""
    if not isinstance(value, dict) or value.get('type') != 'map':
        return None
    inner = value.get('value')
    if not isinstance(inner, dict) or set(inner) != set(DIGEST_KEYS):
        return None
    length, digest = inner['length'], inner['sha256']
    if not (isinstance(length, dict) and length.get('type') == 'number'
            and isinstance(digest, dict) and digest.get('type') == 'string'):
        return None
    try:
        return int(length['value']), str(digest['value'])
    except (KeyError, TypeError, ValueError):
        return None


def byte_array_bytes(value):
    """标签化数组 → 字节串；只接受整组都是 0..255 数字的扁平数组，否则返回 None。"""
    if not isinstance(value, dict) or value.get('type') != 'array' \
            or not isinstance(value.get('value'), list):
        return None
    out = bytearray()
    for item in value['value']:
        if not isinstance(item, dict) or item.get('type') != 'number':
            return None
        try:
            number = int(item.get('value'))
        except (TypeError, ValueError):
            return None
        if not 0 <= number <= 255:
            return None
        out.append(number)
    return bytes(out)


def repair_node(java, ts, label, result, problems):
    """递归对齐 Java 与本轮 TS 的同名观察：把可验证的摘要节点换成 TS 的全量数组。

    结构必须逐层同形（摘要只是把某一层数组换成 `{length,sha256}` 映射）；任何一处对不上都原样保留
    并记问题，绝不构造数据。
    """
    digest = digest_summary(java)
    if digest is not None:
        if digest_summary(ts) == digest:
            result['digestKept'] += 1  # 两侧同为摘要（wallet-wire 的 4 例），本就一致
            return java
        data = byte_array_bytes(ts)
        if data is None or len(data) != digest[0] \
                or hashlib.sha256(data).hexdigest() != digest[1]:
            problems.append(f'摘要化实际值无法用本轮 TS 同断言验证：{label}')
            return java
        result['repaired'].append({'label': label, 'length': digest[0]})
        return ts
    if isinstance(java, dict) and isinstance(ts, dict) \
            and set(java) == set(ts) and java.get('type') == ts.get('type'):
        return {key: repair_node(java[key], ts[key], f'{label}.{key}', result, problems)
                for key in java}
    if isinstance(java, list) and isinstance(ts, list) and len(java) == len(ts):
        return [repair_node(left, right, f'{label}[{index}]', result, problems)
                for index, (left, right) in enumerate(zip(java, ts))]
    return java


def repair_digest_actuals(run_dir, env, summary, problems):
    """把 Java 侧被 `migration.parity.largeArrays=true` 摘要化、而本轮 TS 记全量数组的实际值还原。

    为什么需要：wallet-wire 的 4 个 4 MiB 断言只有「摘要」形态才与本轮 TS 一致，而且不摘要会让
    Java 原始断言轨迹涨到 800 MB（`emit-assertion-observations.py` 会 OOM 被 kill —— full-run-14
    的 dmesg 里有该 python3 被 OOM 的记录，java-assertions.jsonl 只落了 1036/56744 行）。但
    `migration.parity.largeArrays` 是 JVM 级开关，会把另外两个 >65536 字节的实际值
    （`PushDropTest#passesVariousTestVectors` 的 70000 字节、`TransactionPerformanceTest#
    deepSourceGraph` 的 186101 字节）也摘要化，而它们在 TS 侧是全量数组 → 逐值比较必然不一致。

    还原只做**验证性替换**：仅当本轮 TS 同一 `(caseId, assertionId)` 的对应数组成员按字节算出的
    length 与 sha256 与 Java 摘要完全一致时，才认定该数组就是 Java 记录器当时摘要的那串字节并写回。
    """
    output = Path(env.get('EVIDENCE_ASSERTIONS_PATH') or (run_dir / 'java-assertions.jsonl'))
    ts_path = Path(env.get('EVIDENCE_TS_ASSERTIONS_PATH') or (run_dir / 'ts-assertions.jsonl'))
    result = {'javaAssertions': str(output), 'tsAssertions': str(ts_path),
              'repaired': [], 'digestKept': 0, 'repairedCount': 0}
    if not output.is_file() or not ts_path.is_file():
        summary['digestRepair'] = {**result, 'skipped': '缺少本轮一侧的最终断言文件'}
        return
    theirs = {}
    for line in ts_path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            theirs[(row['caseId'], row['assertionId'])] = row.get('value') or {}
    rows, changed = [], 0
    for line in output.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        value = row.get('value') or {}
        counterpart = theirs.get((row['caseId'], row['assertionId']))
        if counterpart is None:
            rows.append(line)
            continue
        repaired = repair_node(value, counterpart, f'{row["caseId"]}/{row["assertionId"]}',
                               result, problems)
        if repaired == value:
            rows.append(line)
            continue
        row['value'] = repaired
        rows.append(json.dumps(row, ensure_ascii=False))
        changed += 1
    if changed:
        output.write_text('\n'.join(rows) + '\n')
    result['repairedCount'] = changed
    summary['digestRepair'] = result


def run_step(script, run_dir, env, problems):
    """Maven 后置的一步转换（A1 归一化 / A2 raw→标准行）；失败即计入 problems。"""
    command = ['python3', str(TASK / script), '--run-dir', str(run_dir)]
    result = subprocess.run(command, cwd=TASK, env=env, capture_output=True, text=True)
    if result.returncode:
        problems.append(f'{script} 退出码 {result.returncode}：{(result.stderr or result.stdout)[-800:]}')
        return {'error': result.returncode, 'argv': command}
    try:
        return json.loads(result.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return {'stdout': result.stdout[-400:]}


def lock_held():
    if not LOCK.exists():
        return False
    with open(LOCK, 'a+') as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
        return False


def maven_command(report_path, properties=None):
    command = [str(TASK / 'lock.sh'), str(TASK / 'mvn.sh'), '-f', str(PROJECT / 'pom.xml'),
               'clean', 'test', '-Dmigration.parity.java.output=' + str(report_path),
               '-DargLine=' + MAVEN_ARG_LINE]
    for name, value in sorted((properties or {}).items()):
        command.append(f'-D{name}={value}')
    if lock_held():
        # 外层（evidence-bundle capture 序列）已经持有同一把锁；flock 不可重入，这里不能再套一层。
        command = command[1:]
        print('LOCK-ALREADY-HELD 外层已持锁，直接运行 Maven（仍受同一把锁保护）', file=sys.stderr)
    return command


def run_maven(command, env, run_dir):
    log = run_dir / 'java-maven.log'
    with log.open('w') as stream:
        result = subprocess.run(command, cwd=TASK, env=env, stdout=stream, stderr=subprocess.STDOUT)
    print(log.read_text()[-4000:], file=sys.stderr)
    return result


def suite_report(path):
    root = ET.parse(path).getroot()
    suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
    problems = []
    for suite in suites:
        if any(int(suite.get(key, '0')) for key in ('failures', 'errors')):
            problems.append('Surefire 存在失败或错误：' + str(path))
        if int(suite.get('skipped', '0')):
            problems.append('Surefire 存在跳过用例：' + str(path))
    return suites, problems


def collect_reports(run_dir, requested):
    """把 target/surefire-reports 收进运行目录；requested 里的汇总名生成合并 XML。"""
    if not SUREFIRE.is_dir():
        return [], ['缺少 Surefire 报告目录：' + str(SUREFIRE)]
    sources = sorted(SUREFIRE.glob('TEST-*.xml'))
    if not sources:
        return [], ['Surefire 没有产出任何 TEST-*.xml']
    copied = run_dir / 'surefire'
    copied.mkdir(parents=True, exist_ok=True)
    suites, problems, total = [], [], 0
    for path in sources:
        parsed, found = suite_report(path)
        problems.extend(found)
        suites.extend(parsed)
        total += sum(int(suite.get('tests', '0')) for suite in parsed)
        shutil.copyfile(path, copied / path.name)
    if not total:
        problems.append('Surefire 报告里没有执行任何用例')
    aggregate = ET.Element('testsuites', {'name': 'metanet4j-bsv-sdk', 'tests': str(total),
                                          'failures': str(sum(int(s.get('failures', '0')) for s in suites)),
                                          'errors': str(sum(int(s.get('errors', '0')) for s in suites)),
                                          'skipped': str(sum(int(s.get('skipped', '0')) for s in suites))})
    for suite in suites:
        aggregate.append(suite)
    produced = []
    for name in requested:
        source = SUREFIRE / name
        target = run_dir / name
        if source.is_file():
            shutil.copyfile(source, target)
        else:
            ET.ElementTree(aggregate).write(target, encoding='utf-8', xml_declaration=True)
        produced.append(str(target))
    return produced, problems


def read_rows(path):
    text = Path(path).read_text() if Path(path).is_file() else ''
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def merge_assertion_rows(plan, legacy, shared, problems):
    """按计划顺序合并两侧断言行；身份重复、缺失、计划外一律记问题（不静默取舍）。"""
    index = {}
    for label, rows in (('JVM 端', legacy), ('共享轨迹', shared)):
        for row in rows:
            key = (row.get('caseId'), row.get('assertionId'))
            if key in index:
                problems.append(f'断言行重复（{index[key][0]} 与 {label}）：{key[0]}/{key[1]}')
                continue
            index[key] = (label, row)
    ordered, missing, extra = [], [], []
    for case_id, spec in plan.items():
        for assertion_id in spec.get('assertionIds', []):
            found = index.pop((case_id, assertion_id), None)
            if found is None:
                missing.append(f'{case_id}/{assertion_id}')
            else:
                ordered.append(found[1])
    for key in index:
        extra.append(f'{key[0]}/{key[1]}')
    if missing:
        problems.append(f'Java 断言行缺失 {len(missing)} 条，例如 {missing[:3]}')
    if extra:
        problems.append(f'Java 断言行出现计划外身份 {len(extra)} 条，例如 {extra[:3]}')
    return ordered


def emit_assertions(run_dir, env, raw, summary, problems):
    """把本轮 Java 断言补齐成计划全集：**合并**而不是覆盖。

    两个产出者写同一个文件：
      ① JVM 内的 legacy 重放（`LegacyInputReplay` 等）在 Maven 期间直接向 EVIDENCE_ASSERTIONS_PATH
         追加行——它们的测试类不使用共享记录器，共享 parity 轨迹里根本没有这些用例；
      ② `emit-assertion-observations.py` 按共享轨迹产出其余用例。
    因此这里先读 JVM 端已写的行，用「全量计划 − 已覆盖用例」的**子计划**调共享转换（写侧文件），
    再按计划的用例顺序与逐用例 assertionIds 顺序合并写回。任何身份冲突、缺失、计划外或计数不符都
    记问题并保持最终文件不被改写（阶段非零退出），不放宽共享转换自身的逐用例严格性。
    """
    output = Path(env.get('EVIDENCE_ASSERTIONS_PATH') or (run_dir / 'java-assertions.jsonl'))
    if not env.get('EVIDENCE_ASSERTIONS_PATH'):
        summary['assertions'] = {'skipped': '缺少 EVIDENCE_ASSERTIONS_PATH'}
        return
    plan_path = env.get('EVIDENCE_INPUT_PLAN')
    catalog = Path(env.get('EVIDENCE_CATALOG', TASK / 'module-tests.json'))
    mapping = Path(env.get('EVIDENCE_MAPPING', TASK / 'test-map.json'))
    if not plan_path or not Path(plan_path).is_file():
        plan_path = run_dir / 'input-plan.json'
    plan = read_json(plan_path)
    legacy = read_rows(output)
    covered = {row.get('caseId') for row in legacy}
    unknown = sorted(covered - set(plan))
    if unknown:
        problems.append(f'JVM 端断言行出现计划外用例 {len(unknown)} 个：{unknown[:3]}')
    subplan = {case_id: spec for case_id, spec in plan.items() if case_id not in covered}
    side = run_dir / 'java-assertions.shared.jsonl'
    if side.exists():
        side.unlink()
    shared, emitted = [], None
    if subplan:
        subplan_path = run_dir / 'java-assertions.subplan.json'
        subplan_path.write_text(json.dumps(subplan, ensure_ascii=False) + '\n')
        command = ['python3', str(TASK / 'emit-assertion-observations.py'),
                   '--catalog', str(catalog), '--mapping', str(mapping), '--plan', str(subplan_path),
                   '--side', 'java', '--raw', str(raw), '--run-id', env.get('EVIDENCE_RUN_ID', ''),
                   '--output', str(side), '--allow-java-extra']
        result = subprocess.run(command, cwd=TASK, env=env, capture_output=True, text=True)
        if result.returncode:
            summary['assertions'] = {'error': (result.stderr or result.stdout)[-800:], 'argv': command}
            problems.append(f'共享断言转换失败（退出码 {result.returncode}）：'
                            + (result.stderr or result.stdout)[-300:])
            return
        emitted = json.loads(result.stdout.strip().splitlines()[-1])
        shared = read_rows(side)
    ordered = merge_assertion_rows(plan, legacy, shared, problems)
    sources = {'legacy': {'cases': len(covered), 'rows': len(legacy)},
               'shared': {'cases': len({row.get('caseId') for row in shared}), 'rows': len(shared)},
               'total': len(ordered)}
    summary['assertionSources'] = sources
    summary['assertions'] = {'subplan': emitted, 'mergedRows': len(ordered), 'sources': sources,
                             'legacyRows': len(legacy), 'sharedRows': len(shared)}
    if problems:
        return
    output.write_text(''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in ordered))
    (run_dir / 'java-assertion-sources.json').write_text(
        json.dumps(sources, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True)
    parser.add_argument('--reports', action='append', default=[])
    parser.add_argument('--probes', type=Path, default=TASK / 'full-run-probes.json')
    parser.add_argument('stages', nargs='*', help='固定阶段声明，只接受 clean test')
    options = parser.parse_args()
    if options.stages and options.stages != ['clean', 'test']:
        parser.error('最终 Java 命令只接受无过滤的 clean test 阶段')
    options.run_dir = options.run_dir.resolve()
    options.run_dir.mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    ts_inputs = options.run_dir / 'ts-inputs.jsonl'
    if not ts_inputs.is_file():
        raise SystemExit('缺少本轮 TS 汇总输入：' + str(ts_inputs))
    table = read_json(options.probes) if options.probes.is_file() else {'envs': {}, 'locals': {}}
    configured = sorted({name for name in table.get('envs', {}) if name.endswith('_TS_INPUTS')})
    discovered = java_ts_input_envs()
    # 真正的注入点是这里：既要覆盖源码扫描到的变量，也要覆盖分派表登记（configured）的变量。
    # 只在 java_ts_input_envs() 里过滤不够——分派表 envs（115 个）会把退役局部的语料变量
    # 重新并回来（full-run-13 实测：configured 仍含它 → HashTest 13 个 PBKDF2 用例报错）。
    targets = sorted((set(configured) | set(discovered)) - set(EXCLUDED_TS_INPUT_ENVS))
    for name in targets:
        env[name] = str(ts_inputs)
    raw_assertions = options.run_dir / 'java-assertions.raw.jsonl'
    if not env.get('MIGRATION_PARITY_JAVA_OUTPUT'):
        env['MIGRATION_PARITY_JAVA_OUTPUT'] = str(raw_assertions)
    if not env.get('EVIDENCE_SIDE'):
        env['EVIDENCE_SIDE'] = 'java'
    # A1：向量局部的原始输入轨迹落点（Maven 前必须给出，否则 VectorInputRecorder 不记录）。
    env[VECTOR_INPUTS_ENV] = str(options.run_dir / 'java-vector-inputs.raw.jsonl')
    # A2：旧接口局部的 -D 属性与自有 env（含 wallet-wire 的 4 项 recipe：plan + largeArrays +
    # ASSERTION_INDEX + JAVA_LARGE_ACTUALS 必须一起给，缺一项要么 OOM 要么不产见证）。
    properties, serial_env, serial_summary, problems = serial_plan(options.run_dir)
    env.update(serial_env)
    if problems:
        for problem in problems:
            print('JAVA-SERIAL-PROBLEM ' + problem, file=sys.stderr)
        raise SystemExit('A2 Java 入口映射表在运行期校验失败，先修映射再跑：' + str(JAVA_SERIAL_ENTRIES))

    command = maven_command(raw_assertions, properties)
    print(json.dumps({'maven': command, 'tsInputs': str(ts_inputs), 'tsInputEnvs': len(targets),
                      'serialProperties': len(properties), 'serialEnv': len(serial_env)},
                     ensure_ascii=False))
    result = run_maven(command, env, options.run_dir)
    summary = {'runId': env.get('EVIDENCE_RUN_ID'), 'runDir': str(options.run_dir),
               'maven': command, 'mavenExitCode': result.returncode,
               'tsInputs': str(ts_inputs), 'tsInputEnvs': targets,
               'tsInputEnvsNotInProbeTable': sorted(set(discovered) - set(configured)),
               'excludedTsInputEnvs': list(EXCLUDED_TS_INPUT_ENVS),
               'mavenArgLine': MAVEN_ARG_LINE,
               'serialEntries': serial_summary,
               'serialProperties': sorted(properties), 'serialEnv': sorted(serial_env),
               'propertyDrivenReplays': java_property_replays()}
    if result.returncode:
        problems.append(f'Maven clean test 退出码非零：{result.returncode}；日志 '
                        + str(options.run_dir / 'java-maven.log'))
    # 两处后置归一化都必须在 bundle 之前完成：它们把原始轨迹折成 java-inputs.jsonl 的标准行。
    summary['vectorInputs'] = run_step(VECTOR_INPUTS_SCRIPT, options.run_dir, env, problems)
    summary['serialInputs'] = run_step(JAVA_SERIAL_CONVERTER, options.run_dir, env, problems)
    produced, report_problems = collect_reports(options.run_dir, options.reports or ['java-surefire.xml'])
    summary['reports'] = produced
    problems.extend(report_problems)
    emit_assertions(options.run_dir, env, raw_assertions, summary, problems)
    # 最后一道：把被 largeArrays 摘要化、而 TS 记全量数组的实际值按摘要校验后还原。
    repair_digest_actuals(options.run_dir, env, summary, problems)
    summary['problems'] = problems
    (options.run_dir / 'java-capture-report.json').write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'reports': produced, 'problems': len(problems),
                      'tsInputEnvs': len(targets), 'vectorInputs': summary['vectorInputs'],
                      'serialInputs': summary['serialInputs']}, ensure_ascii=False))
    for problem in problems:
        print('JAVA-CAPTURE-PROBLEM ' + problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == '__main__':
    sys.exit(main())
