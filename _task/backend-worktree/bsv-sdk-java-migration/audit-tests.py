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


def java_revision():
    """包含提交及未提交文件，避免新源码沿用旧报告。忽略 Git 已忽略的构建产物。"""
    snapshot = {}
    for repo in read(TASK / 'workspace.json')['repositories']:
        folder = TASK / repo['name']
        commit = subprocess.check_output(['git', '-C', str(folder), 'rev-parse', 'HEAD'], text=True).strip()
        names = subprocess.check_output(['git', '-C', str(folder), 'ls-files', '--cached', '--others', '--exclude-standard', '-z']).decode().split('\0')
        snapshot[repo['name']] = {'commit': commit, 'files': {
            name: digest(folder / name) if (folder / name).is_file() else None
            for name in sorted(set(names) - {''})}}
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


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
    actual_ts = {}
    for report_path in args.ts_report:
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
    actual_java = {}
    for report_path in args.java_report:
        root = ET.parse(report_path).getroot()
        for suite in root.iter('testsuite'):
            require(all(int(suite.get(k, '0')) == 0 for k in ('failures', 'errors', 'skipped')), f'Java 报告包含失败/跳过：{report_path}')
            require(int(suite.attrib['tests']) == len(list(suite.iter('testcase'))), f'Java 报告汇总与实际用例矛盾：{report_path}')
        for case in root.iter('testcase'):
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
    observed = indexed(observations['cases'], lambda c: c['id'], '逐用例结果')
    same_keys(cases, observed, '逐用例结果')
    assertion_count = 0
    for key, observation in observed.items():
        require(bool(re.fullmatch(r'[0-9a-f]{64}', observation['inputSha256'])), f'缺少输入/前置状态校验值：{key}')
        require(observation['inputSha256'] == observation['tsInputSha256'] == observation['javaInputSha256'], f'TS/Java 输入或前置状态不同：{key}')
        ts = indexed(observation['ts'], lambda a: a['id'], 'TS 断言结果')
        java = indexed(observation['java'], lambda a: a['id'], 'Java 断言结果')
        same_keys(mapped[key]['assertionIds'], ts, f'TS 断言结果 {key}')
        same_keys(mapped[key]['assertionIds'], java, f'Java 断言结果 {key}')
        for identity in ts:
            # JSON 类型必须保留，不能把 true 当作数值 1，或丢掉字节前导零。
            left = json.dumps(ts[identity]['value'], sort_keys=True, ensure_ascii=False, allow_nan=False)
            right = json.dumps(java[identity]['value'], sort_keys=True, ensure_ascii=False, allow_nan=False)
            require(left == right, f'实际结果不一致：{key} / {identity}')
            assertion_count += 1
    return {'files': len(files), 'cases': len(cases), 'javaCases': len(java_owners), 'comparedAssertions': assertion_count}


def collect():
    config, scope = read(TASK / 'workspace.json'), read(TASK / 'module-scope.json')
    upstream = TASK.parents[2] / config['upstream']['path']
    sdk = upstream / config['upstream']['packagePath']
    commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
    require(commit == config['upstream']['commit'] == scope['upstreamCommit'], '上游固定版本不匹配')
    require(not subprocess.check_output(['git', '-C', str(upstream), 'status', '--porcelain'], text=True).strip(), '上游工作区存在修改')
    modules = scope['selectedModules']
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
        'pendingModules': sorted(p.name for p in (sdk / 'src').iterdir() if p.is_dir() and not p.name.startswith('__') and p.name not in modules),
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
    for name in ('compare', 'check'):
        command = sub.add_parser(name, help='compare 核对所给证据；check 额外重新清点固定上游并核对冻结范围')
        command.add_argument('--catalog', default=str(TASK / 'module-tests.json'))
        command.add_argument('--mapping', default=str(TASK / 'test-map.json'))
        command.add_argument('--ts-report', action='append', default=[])
        command.add_argument('--java-report', action='append', default=[])
        command.add_argument('--observations', default=str(TASK / '.cache/evidence/parity-results.json'))
        command.add_argument('--module', action='append', default=[], help='整模块累计验收，可重复；默认全部已选模块')
        command.add_argument('--java-revision', help='compare 调试时核对源码摘要；check 始终从当前 Java 工作树重新计算')
    args = parser.parse_args()
    try:
        if args.command == 'revision':
            print(json.dumps({'javaRevision': java_revision()}))
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
                require(not current['crossModuleTestsPending'], '跨目录用例仍待归属，不能仅修改 reviewed 标志通过验收')
            print(json.dumps({'status': 'PASS', 'check': args.command, **result}, ensure_ascii=False))
    except (ValueError, KeyError, TypeError, OSError, ET.ParseError, subprocess.CalledProcessError) as error:
        print(json.dumps({'status': 'FAIL', 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
