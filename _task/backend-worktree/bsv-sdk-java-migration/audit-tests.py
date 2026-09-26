#!/usr/bin/env python3
"""整模块测试清点及证据核对；任何缺失、跳过或差异均返回非零。"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def capture_rows(path, identity):
    rows = {}
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        require(isinstance(row.get('caseId'), str) and isinstance(row.get(identity), str) and 'value' in row,
                f'原始采集缺少 caseId、{identity} 或实际值：{path}:{number}')
        rows.setdefault(row['caseId'], []).append(row)
    return rows


def java_revision(repo_paths=None):
    """包含提交及未提交文件，避免新源码沿用旧报告。忽略 Git 已忽略的构建产物。"""
    repo_paths = repo_paths or {}
    snapshot = {}
    for repo in read(TASK / 'workspace.json')['repositories']:
        folder = Path(repo_paths.get(repo['name'], TASK / repo['name']))
        commit = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
        names = subprocess.check_output(['git', '-C', str(folder), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
        snapshot[repo['name']] = {'commit': commit, 'files': {
            name: digest(folder / name) if (folder / name).is_file() else None
            for name in sorted(set(names) - {''})}}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def independent_captures(paths):
    for ts in ('tsInputs', 'tsAssertions'):
        for java in ('javaInputs', 'javaAssertions'):
            require(not Path(paths[ts]).samefile(paths[java]),
                    f'TS/Java 必须独立采集，不能使用同一物理文件：{ts} / {java}')


def validate_plan(catalog, mapping, plan):
    cases = {case['id']: file for file in catalog['files'] for case in file['cases']}
    mapped = {case['id']: case for case in mapping['cases']}
    same_keys(cases, plan, '独立输入/断言计划用例')
    expected_sites = {site['id'] for file in catalog['files'] for site in file['sites']
                      if site['kind'] == 'assertion'}
    expected_loops = {site['id'] for file in catalog['files'] for site in file['sites']
                      if site['kind'] == 'loop'}
    covered_sites, covered_loops = set(), set()
    for case_id, expected in plan.items():
        samples, assertions = expected.get('sampleIds'), expected.get('assertionIds')
        for values, label in ((samples, '样本'), (assertions, '断言')):
            require(isinstance(values, list) and bool(values)
                    and all(isinstance(value, str) and bool(value) for value in values)
                    and len(values) == len(set(values)), f'独立{label}计划无效：{case_id}')
        sites = expected.get('assertionSites')
        require(isinstance(sites, dict), f'计划缺少冻结断言站点关联：{case_id}')
        same_keys(assertions, sites, f'断言实例与冻结断言站点关联 {case_id}')
        file_sites = {site['id'] for site in cases[case_id]['sites'] if site['kind'] == 'assertion'}
        require(all(isinstance(site, str) and site in file_sites for site in sites.values()),
                f'计划断言必须关联本文件的冻结断言站点：{case_id}')
        mapped_sites = []
        for identity in mapped[case_id]['assertionIds']:
            require(identity in file_sites or identity in sites,
                    f'映射中的断言实例未列入独立计划：{case_id} / {identity}')
            mapped_sites.append(identity if identity in file_sites else sites[identity])
        require(list(dict.fromkeys(sites[identity] for identity in assertions)) == list(dict.fromkeys(mapped_sites)),
                f'映射断言站点与独立计划的执行顺序不符：{case_id}')
        covered_sites.update(sites.values())
        loops = expected.get('loopSamples', {})
        require(isinstance(loops, dict), f'循环样本计划无效：{case_id}')
        file_loops = {site['id'] for site in cases[case_id]['sites'] if site['kind'] == 'loop'}
        require(set(loops) <= file_loops, f'循环样本必须关联本文件的冻结循环站点：{case_id}')
        for site, ids in loops.items():
            require(isinstance(ids, list) and bool(ids) and all(isinstance(x, str) for x in ids)
                    and len(ids) == len(set(ids)) and set(ids) <= set(samples),
                    f'冻结循环站点缺少完整输入样本：{case_id} / {site}')
            covered_loops.add(site)
    same_keys(expected_sites, covered_sites, '冻结断言站点覆盖')
    same_keys(expected_loops, covered_loops, '冻结循环站点覆盖')


def runtime_provenance(args, catalog, paths):
    """校验执行器在运行前固定、运行后封存的来源；打包器无权追认旧文件。"""
    manifests = {}
    hashes = {}
    for side in ('ts', 'java'):
        path = getattr(args, side + '_run_manifest', None)
        require(bool(path), f'缺少 {side} 运行来源 manifest；须由 capture 包装真实执行后生成，不能追认旧报告')
        manifest = read(path)
        require(manifest.get('schemaVersion') == 1 and manifest.get('side') == side,
                f'{side} 运行来源 manifest 格式或侧别无效')
        require(not manifest.get('captureError'), f'{side} 采集失败：{manifest.get("captureError")}')
        require(isinstance(manifest.get('runId'), str)
                and bool(re.fullmatch(r'[0-9a-f]{32}', manifest['runId'])), f'{side} 运行身份无效')
        require(manifest.get('producerSha256') == digest(TASK / 'evidence-bundle.py'),
                f'{side} 运行来源不是当前 capture 执行器产生')
        require(manifest.get('upstreamCommit') == catalog['upstreamCommit'], f'{side} 运行的固定上游版本不同')
        for key, artifact in (('catalogSha256', args.catalog), ('mappingSha256', args.mapping),
                              ('inputPlanSha256', paths['inputPlan'])):
            require(manifest.get(key) == digest(artifact), f'{side} 运行前固定的清单、映射或输入计划已变化：{key}')
        command = manifest.get('command')
        require(isinstance(command, list) and bool(command)
                and all(isinstance(part, str) and bool(part) for part in command), f'{side} 运行命令缺失')
        require(type(manifest.get('exitCode')) is int and manifest['exitCode'] == 0,
                f'{side} 运行未完成或退出状态非零')
        require(type(manifest.get('startedAtNs')) is int and type(manifest.get('finishedAtNs')) is int
                and 0 < manifest['startedAtNs'] <= manifest['finishedAtNs'], f'{side} 运行时间记录不完整')
        require(isinstance(manifest.get('sourceRevision'), str) and bool(manifest['sourceRevision'])
                and manifest['sourceRevision'] == manifest.get('sourceRevisionAfter'),
                f'{side} 运行中源码版本变化或版本记录缺失')
        if side == 'ts':
            require(manifest['sourceRevision'] == catalog['upstreamCommit'], 'TS 运行来源不是固定上游版本')
        else:
            require('clean' in command and 'test' in command
                    and command.index('clean') < command.index('test')
                    and not any(re.search(r'skipTests|maven\.test\.skip|testFailureIgnore|failIfNoTests=false', part)
                                for part in command), 'Java 运行必须是未跳过测试的 clean test')
        for suffix, field in (('Inputs', 'inputsSha256'), ('Assertions', 'assertionsSha256')):
            require(manifest.get(field) == digest(paths[side + suffix]), f'{side} 运行原始采集校验值不同：{field}')
            for rows in capture_rows(paths[side + suffix], 'sampleId' if suffix == 'Inputs' else 'assertionId').values():
                require(all(row.get('runId') == manifest['runId'] and row.get('side') == side for row in rows),
                        f'{side} 原始采集运行身份或侧别不符；禁止复制、重放其他运行轨迹')
        require(manifest.get('reportSha256') == sorted(digest(p) for p in getattr(args, side + '_report')),
                f'{side} 运行原始报告校验值不同')
        log = manifest.get('logPath')
        require(isinstance(log, str) and bool(log), f'{side} 运行日志缺失')
        require(manifest.get('logSha256') == digest(Path(path).parent / log), f'{side} 运行日志校验值不同')
        manifests[side], hashes[side] = manifest, digest(path)
    require(manifests['ts']['runId'] != manifests['java']['runId'], 'TS/Java 必须具有独立运行身份')
    revision = manifests['java']['sourceRevision']
    if getattr(args, 'java_revision', None):
        require(args.java_revision == revision, 'Java 运行来源版本与要求不同；禁止用打包参数重写旧执行版本')
    return revision, hashes


def indexed(rows, key, label):
    result = {}
    for row in rows:
        identity = key(row)
        require(identity not in result, f'{label}重复：{identity}')
        result[identity] = row
    return result


def same_keys(expected, actual, label):
    missing, extra = set(expected) - set(actual), set(actual) - set(expected)
    require(not missing and not extra,
            f'{label}：缺失 {len(missing)}，多余 {len(extra)}；'
            f'缺失示例 {sorted(missing)[:8]}；多余示例 {sorted(extra)[:8]}')


def compare_ts(catalog, report_paths):
    files = indexed(catalog['files'], lambda f: f['path'], '上游文件')
    require(bool(files), '禁止使用空清单通过 TS 验收')
    require(all(f['cases'] for f in files.values()), '禁止使用空用例通过 TS 验收')
    actual_ts = {}
    for report_path in report_paths:
        report = read(report_path)
        require(report.get('success') is True, f'TS 报告未全部成功：{report_path}')
        count = sum(len(f['assertionResults']) for f in report['testResults'])
        require(report['numTotalTests'] == report['numPassedTests'] == count
                and all(report[k] == 0 for k in ('numFailedTests', 'numPendingTests', 'numTodoTests')),
                f'TS 报告汇总与实际用例矛盾：{report_path}')
        for file in report['testResults']:
            name = file['name'].replace('\\', '/')
            matches = [p for p in files if name == p or name.endswith('/' + p)]
            require(len(matches) == 1, f'TS 报告存在范围外文件：{name}')
            name = matches[0]
            require(name not in actual_ts, f'TS 报告文件重复：{name}')
            require(file['status'] == 'passed', f'TS 文件未通过：{name}')
            actual_ts[name] = file['assertionResults']
    same_keys(files, actual_ts, 'TS 实际执行文件')
    for name, file in files.items():
        expected = Counter(tuple(c['names']) for c in file['cases'])
        executed = Counter(tuple(c['ancestorTitles'] + [c['title']]) for c in actual_ts[name])
        require(expected == executed, f'TS 实际用例/参数行不一致：{name}')
        require(all(c['mode'] == 'run' for c in file['cases']), f'存在 skip/todo/only 用例：{name}')
        require(all(c['status'] == 'passed' for c in actual_ts[name]), f'TS 存在失败/跳过/未执行：{name}')
    return {'files': len(files), 'cases': sum(len(f['cases']) for f in files.values())}


def compare(args):
    catalog, mapping = read(args.catalog), read(args.mapping)
    selected = set(args.module or catalog['modules'])
    require(selected <= set(catalog['modules']), '只能选择冻结清单中的完整模块')
    require(all(set(catalog['moduleDependencies'][m]) <= selected for m in selected), '阶段必须包含依赖模块的累计验收；循环依赖需联合验收')
    if args.module:
        all_ids = {c['id'] for f in catalog['files'] for c in f['cases']}
        require(all(c['id'] in all_ids for c in mapping['cases']), '映射包含未知上游用例')
        # 只按整目录过滤，不提供按文件、测试名或函数裁剪的入口。
        catalog['files'] = [f for f in catalog['files'] if f.get('module', f['path'].split('/')[1]) in selected]
        selected_ids = {c['id'] for f in catalog['files'] for c in f['cases']}
        selected_sites = {s['id'] for f in catalog['files'] for s in f['sites']}
        mapping['cases'] = [c for c in mapping['cases'] if c['id'] in selected_ids]
        mapping['siteReviews'] = [r for r in mapping['siteReviews'] if r['id'] in selected_sites]
    files = indexed(catalog['files'], lambda f: f['path'], '上游文件')
    cases = indexed([dict(c, file=f['path']) for f in files.values() for c in f['cases']], lambda c: c['id'], '上游用例')
    require(bool(files) and bool(cases), '禁止使用空清单通过验收')
    require(mapping['upstreamCommit'] == catalog['upstreamCommit'], '映射的上游版本不一致')
    mapped = indexed(mapping['cases'], lambda c: c['id'], 'Java 映射')
    same_keys(cases, mapped, '未映射上游用例')
    java_owners = {}
    for key, case in mapped.items():
        require(bool(case['java']) and bool(case['assertionIds']), f'缺少 Java 测试或断言映射：{key}')
        require(len(set(case['assertionIds'])) == len(case['assertionIds']), f'断言标识重复：{key}')
        for java in case['java']:
            identity = (java['className'], java['name'])
            require(identity not in java_owners, f'Java 用例被重复用于多个映射：{identity}')
            java_owners[identity] = key
    sites = {s['id'] for f in files.values() for s in f['sites']}
    reviews = indexed(mapping['siteReviews'], lambda r: r['id'], '源码语义复核')
    same_keys(sites, reviews, '注册点、断言、循环与条件分支复核')
    for key, review in reviews.items():
        require(review['status'] == 'reviewed' and bool(review['note']) and bool(review['caseIds']), f'源码语义未复核：{key}')
        require(set(review['caseIds']) <= set(cases), f'源码复核引用未知用例：{key}')
    compare_ts(catalog, args.ts_report)
    actual_java = {}
    for report_path in args.java_report:
        root = ET.parse(report_path).getroot()
        require(root.tag in ('testsuite', 'testsuites'), f'Surefire XML 根节点无效：{report_path}')
        suites = [root] if root.tag == 'testsuite' else list(root.findall('testsuite'))
        require(bool(suites) and len(suites) == len(list(root.iter('testsuite'))),
                f'Surefire XML 缺少有效 testsuite 或存在嵌套 suite：{report_path}')
        testcases = [case for suite in suites for case in suite.findall('testcase')]
        require(len(testcases) == len(list(root.iter('testcase'))),
                f'Surefire testcase 不属于直接 testsuite：{report_path}')
        for suite in suites:
            require(all(int(suite.get(k, '0')) == 0 for k in ('failures', 'errors', 'skipped')), f'Java 报告包含失败/跳过：{report_path}')
            require(int(suite.attrib['tests']) == len(list(suite.iter('testcase'))), f'Java 报告汇总与实际用例矛盾：{report_path}')
        for case in testcases:
            identity = (case.attrib['classname'], case.attrib['name'])
            require(identity not in actual_java, f'Java 实际执行记录重复：{identity}')
            require(not any(case.find(tag) is not None for tag in ('failure', 'error', 'skipped')), f'Java 用例未通过：{identity}')
            actual_java[identity] = case
    missing = set(java_owners) - set(actual_java)
    require(not missing, f'Java 未实际执行 {len(missing)} 个映射用例：{sorted(missing)[:8]}')
    observations = read(args.observations)
    require(observations['upstreamCommit'] == catalog['upstreamCommit'] and bool(observations['javaRevision']), '结果缺少匹配的代码版本')
    if args.java_revision:
        require(observations['javaRevision'] == args.java_revision, '结果来自不同的 Java 源码版本')
    require(observations['catalogSha256'] == digest(args.catalog), '结果与用例清单不匹配')
    for name, paths in [('tsReportSha256', args.ts_report), ('javaReportSha256', args.java_report)]:
        require(sorted(observations[name]) == sorted(digest(p) for p in paths), f'结果与原始报告校验值不匹配：{name}')
    capture_names = {'inputPlan': 'input_plan', 'tsInputs': 'ts_inputs', 'javaInputs': 'java_inputs',
                     'tsAssertions': 'ts_assertions', 'javaAssertions': 'java_assertions'}
    capture_paths = {name: getattr(args, option, None) for name, option in capture_names.items()}
    if getattr(args, 'command', 'compare') == 'check' or observations.get('captureSha256') is not None or any(capture_paths.values()):
        require(all(capture_paths.values()) and isinstance(observations.get('captureSha256'), dict),
                '完整验收缺少两端原始采集、独立输入/断言计划或校验值')
        require(set(observations['captureSha256']) == set(capture_names), '原始采集文件清单不完整')
        independent_captures(capture_paths)
        for name, path in capture_paths.items():
            require(observations['captureSha256'][name] == digest(path), f'原始采集校验值不匹配：{name}')
        plan = read(capture_paths['inputPlan'])
        validate_plan(catalog, mapping, plan)
        raw_captures = {name: capture_rows(capture_paths[name], identity) for name, identity in (
            ('tsInputs', 'sampleId'), ('javaInputs', 'sampleId'),
            ('tsAssertions', 'assertionId'), ('javaAssertions', 'assertionId'))}
        for name, rows in raw_captures.items():
            same_keys(cases, rows, f'{name} 原始采集用例')
        revision, run_hashes = runtime_provenance(args, catalog, capture_paths)
        require(observations['javaRevision'] == revision, '汇总 Java 版本与实际运行来源不符')
        require(observations.get('runManifestSha256') == run_hashes, '汇总运行 manifest 校验值不符')
    observed = indexed(observations['cases'], lambda c: c['id'], '逐用例结果')
    same_keys(cases, observed, '逐用例结果')
    assertion_count = 0
    for key, observation in observed.items():
        require(bool(re.fullmatch(r'[0-9a-f]{64}', observation['inputSha256'])), f'缺少输入/前置状态校验值：{key}')
        require(observation['inputSha256'] == observation['tsInputSha256'] == observation['javaInputSha256'], f'TS/Java 输入或前置状态不同：{key}')
        if capture_paths['inputPlan']:
            samples = observation.get('inputSamples')
            require(isinstance(samples, dict) and set(samples) == {'TS', 'Java'}, f'缺少两端实际输入样本：{key}')
            for side in ('TS', 'Java'):
                require([row['sampleId'] for row in samples[side]] == plan[key]['sampleIds'],
                        f'{side} 输入样本数量、顺序或 ID 不符：{key}')
                raw = raw_captures['tsInputs' if side == 'TS' else 'javaInputs'][key]
                require(canonical(samples[side]) == canonical([{'sampleId': row['sampleId'], 'value': row['value']} for row in raw]),
                        f'{side} 汇总输入与原始采集不同：{key}')
                require(hashlib.sha256(canonical(samples[side]).encode()).hexdigest() == observation['inputSha256'],
                        f'{side} 实际输入样本与摘要不符：{key}')
        ts = indexed(observation['ts'], lambda a: a['id'], 'TS 断言结果')
        java = indexed(observation['java'], lambda a: a['id'], 'Java 断言结果')
        expected_ids = plan[key]['assertionIds'] if capture_paths['inputPlan'] else mapped[key]['assertionIds']
        same_keys(expected_ids, ts, f'TS 断言结果 {key}')
        same_keys(expected_ids, java, f'Java 断言结果 {key}')
        if capture_paths['inputPlan']:
            for side, actual in [('tsAssertions', observation['ts']), ('javaAssertions', observation['java'])]:
                raw = raw_captures[side][key]
                require([row['assertionId'] for row in raw] == plan[key]['assertionIds'],
                        f'{side} 原始断言数量、顺序或 ID 不符：{key}')
                require(canonical(actual) == canonical([{'id': row['assertionId'], 'value': row['value']} for row in raw]),
                        f'{side} 汇总断言与原始采集不同：{key}')
        for identity in ts:
            # JSON 类型必须保留，不能把 true 当作数值 1，或丢掉字节前导零。
            left = json.dumps(ts[identity]['value'], sort_keys=True, ensure_ascii=False, allow_nan=False)
            right = json.dumps(java[identity]['value'], sort_keys=True, ensure_ascii=False, allow_nan=False)
            require(left == right, f'实际结果不一致：{key} / {identity}')
            assertion_count += 1
    return {'files': len(files), 'cases': len(cases), 'javaCases': len(java_owners),
            'comparedAssertions': assertion_count, 'formalAcceptance': getattr(args, 'command', 'compare') == 'check'}


def collect():
    config, scope = read(TASK / 'workspace.json'), read(TASK / 'module-scope.json')
    upstream = TASK.parents[2] / config['upstream']['path']
    sdk = upstream / config['upstream']['packagePath']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['upstream']['commit'] == scope['upstreamCommit'], '上游固定版本不匹配')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(), '上游工作区存在修改')
    modules = scope['selectedModules']
    available = {p.name for p in (sdk / 'src').iterdir() if p.is_dir() and not p.name.startswith('__')}
    reviews = scope.get('moduleReviews', {})
    require(set(reviews) <= available, '范围复核包含未知模块')
    for module, review in reviews.items():
        require(review.get('decision') in ('selected', 'excluded') and bool(review.get('reason'))
                and bool(review.get('evidence')), f'模块范围缺少结论或依据：{module}')
        require((review['decision'] == 'selected') == (module in modules), f'模块范围结论与已选列表矛盾：{module}')
    require(bool(modules) and len(set(modules)) == len(modules), '模块列表为空或重复')
    require(all(re.fullmatch(r'[a-z][a-z0-9-]*', m) and (sdk / 'src' / m).is_dir() for m in modules), '只接受完整顶层模块名，禁止文件/方法过滤')
    all_files = sorted(p for m in modules for p in (sdk / 'src' / m).rglob('*') if p.is_file())
    cross = {p.relative_to(sdk).as_posix(): p for d in (sdk / 'src').iterdir()
             if d.is_dir() and d.name.startswith('__') for p in d.rglob('*.test.ts')}
    owners = scope.get('crossModuleTestOwners', {})
    require(set(owners) <= set(cross), '跨目录测试归属包含未知文件')
    for name, owner in owners.items():
        require(bool(owner['reason']) and bool(re.fullmatch(r'[a-z][a-z0-9-]*', owner['module']))
                and (sdk / 'src' / owner['module']).is_dir(), f'跨目录归属无效：{name}')
        if owner['module'] in modules:
            all_files.append(cross[name])
    all_files.sort()
    tests = [p.relative_to(sdk).as_posix() for p in all_files if re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', p.name)]
    require(bool(tests), '选中模块没有测试文件')
    with tempfile.TemporaryDirectory(prefix='bsv-census-') as tmp:
        output = Path(tmp) / 'cases.json'
        subprocess.run([config['tools']['node'], str(TASK / 'collect-cases.cjs'), '--sdk', str(sdk), '--output', str(output), *tests], check=True)
        result = read(output)
    result['moduleDependencies'] = {m: result['moduleDependencies'][m] for m in modules}
    for file in result['files']:
        file['module'] = owners[file['path']]['module'] if file['path'] in owners else file['path'].split('/')[1]
    result.update({
        'upstreamCommit': commit, 'scopeSha256': digest(TASK / 'module-scope.json'),
        'modules': modules,
        'moduleFiles': {p.relative_to(sdk).as_posix(): digest(p) for p in all_files},
        'pendingModules': sorted(available - set(reviews)),
        'excludedModules': sorted(m for m, r in reviews.items() if r['decision'] == 'excluded'),
        'crossModuleTestOwners': owners,
        'crossModuleTestsPending': sorted(set(cross) - set(owners)),
    })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('revision', help='生成已登记 Java 仓库当前提交及工作树文件摘要，供真实结果采集记录')
    inventory = sub.add_parser('inventory', help='清点所有已选整模块，含参数化/循环注册与 manual 文件；不执行测试体')
    inventory.add_argument('--output', default=str(TASK / 'module-tests.json'))
    ts_only = sub.add_parser('compare-ts', help='仅核对 TS 原始报告与完整冻结清单；不代表 Java 迁移或最终 check 通过')
    ts_only.add_argument('--catalog', default=str(TASK / 'module-tests.json'))
    ts_only.add_argument('--ts-report', action='append', required=True)
    for name in ('compare', 'check'):
        command = sub.add_parser(name, help='compare 核对所给证据；check 额外重新清点固定上游并核对冻结范围')
        command.add_argument('--catalog', default=str(TASK / 'module-tests.json'))
        command.add_argument('--mapping', default=str(TASK / 'test-map.json'))
        command.add_argument('--ts-report', action='append', default=[])
        command.add_argument('--java-report', action='append', default=[])
        command.add_argument('--observations', default=str(TASK / '.cache/evidence/parity-results.json'))
        command.add_argument('--module', action='append', default=[], help='整模块累计验收，可重复；默认全部已选模块')
        command.add_argument('--java-revision', help='compare 调试时核对源码摘要；check 始终从当前 Java 工作树重新计算')
        for name in ('input-plan', 'ts-inputs', 'java-inputs', 'ts-assertions', 'java-assertions'):
            command.add_argument('--' + name)
        for side in ('ts', 'java'):
            command.add_argument('--' + side + '-run-manifest')
    args = parser.parse_args()
    try:
        if args.command == 'revision':
            print(json.dumps({'javaRevision': java_revision()}))
        elif args.command == 'compare-ts':
            print(json.dumps({'status': 'PASS', 'check': 'compare-ts', **compare_ts(read(args.catalog), args.ts_report)}))
        elif args.command == 'inventory':
            result = collect()
            Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
            print(json.dumps({'modules': result['modules'], 'sourceAndTestFiles': len(result['moduleFiles']), 'testFiles': len(result['files']), 'cases': sum(len(f['cases']) for f in result['files'])}, ensure_ascii=False))
        else:
            if args.command == 'check':
                current = collect()
                require(current == read(args.catalog), '冻结清单与重新清点不一致：存在源码/测试/参数行/模块范围漂移；禁止直接覆盖后当作通过')
                args.java_revision = java_revision()
            result = compare(args)
            if args.command == 'check':
                require(read(TASK / 'module-scope.json')['scopeReview'] == 'reviewed', '依赖模块及跨目录测试归属尚未审查完成')
                require(not current['pendingModules'], '存在未逐项决定范围的候选模块')
                require(not current['crossModuleTestsPending'], '跨目录用例仍待归属，不能仅修改 reviewed 标志通过验收')
            print(json.dumps({'status': 'PASS', 'check': args.command, **result}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
