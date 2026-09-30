#!/usr/bin/env python3
"""全量采集前置检查：合并计划约束，复核局部来源，绝不拼接运行证据。"""
import argparse
from collections import Counter, defaultdict
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import xml.etree.ElementTree as ET

TASK = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('evidence_bundle', TASK / 'evidence-bundle.py')
bundle = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bundle)
audit = bundle.audit


def load(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def resolve(base, value):
    return str((base / value).resolve())


def local_args(item, base, revision):
    keys = ('catalog', 'mapping', 'input_plan', 'ts_inputs', 'java_inputs',
            'ts_assertions', 'java_assertions', 'ts_run_manifest', 'java_run_manifest')
    values = {key: resolve(base, item[key]) for key in keys}
    values.update({key: [resolve(base, path) for path in item[key]]
                   for key in ('ts_report', 'java_report')})
    return SimpleNamespace(**values, java_revision=revision)


def validate_subset(catalog, mapping, local_catalog, local_mapping, plan):
    """局部清单允许裁剪，保留的每个原始对象必须来自当前冻结清单。"""
    audit.require(local_catalog['upstreamCommit'] == local_mapping['upstreamCommit']
                  == catalog['upstreamCommit'], '局部计划上游版本不同')
    files = {file['path']: file for file in catalog['files']}
    mapped = {case['id']: case for case in mapping['cases']}
    ids = []
    for file in local_catalog['files']:
        original = files[file['path']]
        audit.require(file.get('sha256') == original.get('sha256'), '局部源码摘要不同')
        for field in ('cases', 'sites'):
            frozen = {row['id']: row for row in original[field]}
            audit.require(len({row['id'] for row in file[field]}) == len(file[field]), '局部清单重复 ID')
            for row in file[field]:
                audit.require(row == frozen.get(row['id']), '局部清单篡改冻结对象：' + row['id'])
        ids.extend(case['id'] for case in file['cases'])
    audit.require(len(ids) == len(set(ids)), '局部清单重复用例')
    audit.same_keys(ids, [case['id'] for case in local_mapping['cases']], '局部映射用例')
    for case in local_mapping['cases']:
        original = mapped.get(case['id'], {})
        # 局部计划可展开同一站点的动态断言实例；Java 注册身份和其他映射字段必须相同。
        audit.require({key: value for key, value in case.items() if key != 'assertionIds'} ==
                      {key: value for key, value in original.items() if key != 'assertionIds'},
                      '局部映射已变化：' + case['id'])
    audit.validate_plan(local_catalog, local_mapping, plan)
    audit.validate_plan(local_catalog, dict(mapping, cases=[mapped[identity] for identity in ids]), plan)


def merge_plan(merged, incoming):
    for identity, value in incoming.items():
        audit.require(identity not in merged or audit.canonical(merged[identity]) == audit.canonical(value),
                      '同用例计划冲突：' + identity)
    merged.update(incoming)


def fragment_from_plan(catalog, mapping, plan):
    """从当前冻结对象投影专用采集器的计划；投影本身不生成运行来源。"""
    ids = set(plan)
    sites = {site for row in plan.values() for site in row['assertionSites'].values()}
    sites.update(site for row in plan.values() for site in row.get('loopSamples', {}))
    sites.update(review['id'] for review in mapping['siteReviews']
                 if review['caseIds'] and set(review['caseIds']) <= ids)
    files = [dict(file, cases=[case for case in file['cases'] if case['id'] in ids],
                  sites=[site for site in file['sites'] if site['id'] in sites])
             for file in catalog['files'] if any(case['id'] in ids for case in file['cases'])]
    return (dict(catalog, files=files, partialImplementationOnly=True),
            dict(mapping, cases=[case for case in mapping['cases'] if case['id'] in ids],
                 siteReviews=[review for review in mapping['siteReviews'] if review['id'] in sites]))


def java_registrations(mapping, catalog, reports):
    files = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    owners = defaultdict(list)
    for case in mapping['cases']:
        for java in case['java']:
            owners[(java['className'], java['name'])].append(case['id'])
    actual = Counter()
    for report in reports:
        root = ET.parse(report).getroot()
        audit.require(root.tag in ('testsuite', 'testsuites'), 'Surefire 根节点无效')
        suites = [root] if root.tag == 'testsuite' else root.findall('testsuite')
        audit.require(suites and len(suites) == len(list(root.iter('testsuite'))), 'Surefire 存在嵌套 suite')
        audit.require(sum(len(suite.findall('testcase')) for suite in suites) == len(list(root.iter('testcase'))),
                      'Surefire testcase 不属于直接 suite')
        for suite in suites:
            rows = suite.findall('testcase')
            audit.require(int(suite.get('tests', '-1')) == len(rows), 'Surefire 用例汇总不符')
            audit.require(all(int(suite.get(key, '0')) == 0 for key in ('failures', 'errors', 'skipped')),
                          'Surefire 包含失败或跳过')
            for row in rows:
                audit.require(not any(row.find(tag) is not None for tag in ('failure', 'error', 'skipped')),
                              'Surefire 用例未通过')
                actual[(row.attrib['classname'], row.attrib['name'])] += 1
    duplicated = [{'className': key[0], 'name': key[1], 'caseIds': ids,
                   'files': sorted({files[identity] for identity in ids}),
                   'surefireOccurrences': actual[key] if reports else None,
                   'additionalDistinctRegistrationsRequired': len(ids) - 1}
                  for key, ids in sorted(owners.items()) if len(ids) > 1]
    by_file = Counter(files[identity] for row in duplicated for identity in row['caseIds'])
    return {'mappedReferences': sum(map(len, owners.values())), 'distinctMappedIdentities': len(owners),
            'duplicateReferences': sum(len(ids) - 1 for ids in owners.values()),
            'duplicateGroups': duplicated, 'affectedCasesByFile': dict(sorted(by_file.items())),
            'surefireProvided': bool(reports), 'surefireCases': sum(actual.values()),
            'surefireRuntimeProvenanceVerified': False,
            'surefireReports': [{'path': str(path), 'sha256': audit.digest(path)} for path in reports],
            'missingMappedIdentities': [{'className': key[0], 'name': key[1]} for key in sorted(set(owners) - set(actual))]
                if reports else None,
            'duplicateSurefireIdentities': [list(key) for key, count in actual.items() if count > 1]}


def inspect(config, base, catalog_path, mapping_path, revision, reports):
    catalog, mapping = load(catalog_path), load(mapping_path)
    audit.require(mapping['upstreamCommit'] == catalog['upstreamCommit'], '全局映射上游版本不同')
    frozen = [case['id'] for file in catalog['files'] for case in file['cases']]
    mapped_ids = [case['id'] for case in mapping['cases']]
    audit.require(bool(frozen), '禁止使用空冻结清单生成全量采集序列')
    audit.require(len(frozen) == len(set(frozen)) and len(mapped_ids) == len(set(mapped_ids)), '全局用例 ID 重复')
    audit.same_keys(frozen, mapped_ids, '全局映射用例')
    merged, verified, records, errors = {}, set(), [], []
    for item in config['locals']:
        record = {'name': item['name'], 'planValid': False, 'currentCaptureVerified': False}
        records.append(record)
        try:
            plan = load(resolve(base, item['input_plan']))
            if item.get('deriveCatalogFromPlan') is True:
                local_catalog, local_mapping = fragment_from_plan(catalog, mapping, plan)
            else:
                local_catalog = load(resolve(base, item['catalog']))
                local_mapping = load(resolve(base, item['mapping']))
            validate_subset(catalog, mapping, local_catalog, local_mapping, plan)
            merge_plan(merged, plan)
            record.update(planValid=True, cases=len(plan),
                          samples=sum(len(value['sampleIds']) for value in plan.values()),
                          assertionInstances=sum(len(value['assertionIds']) for value in plan.values()))
        except (ValueError, OSError, KeyError, TypeError) as error:
            record['planError'] = str(error)
            errors.append(item['name'] + ': ' + str(error))
            continue
        try:
            audit.require(item.get('captureKind') != 'specialized-local',
                          '专用局部采集的结构计划；尚未接入标准双侧 capture，不计当前全量来源')
            args = local_args(item, base, revision)
            result = bundle.build(args)
            java = java_registrations(local_mapping, local_catalog, args.java_report)
            audit.require(not java['duplicateReferences'] and not java['missingMappedIdentities']
                          and not java['duplicateSurefireIdentities'], '局部 Java 注册报告不完整或重复')
            # 局部采集可以运行整个原文件；按报告中的完整文件重新检查 Jest 汇总。
            reported_files = {Path(row['name']).as_posix().split('/src/', 1)[-1]
                              for path in args.ts_report for row in load(path)['testResults']}
            ts_catalog = dict(catalog, files=[file for file in catalog['files']
                              if file['path'].removeprefix('src/') in reported_files])
            audit.require({file['path'] for file in local_catalog['files']} <=
                          {file['path'] for file in ts_catalog['files']}, '局部 Jest 缺少原文件')
            audit.compare_ts(ts_catalog, args.ts_report)
            record.update(currentCaptureVerified=True, javaRevision=result['javaRevision'])
            verified.update(plan)
        except (ValueError, OSError, KeyError, TypeError, ET.ParseError) as error:
            record['captureError'] = str(error)
    cases = {case['id']: file['path'] for file in catalog['files'] for case in file['cases']}
    missing = sorted(set(cases) - set(merged))
    registration = java_registrations(mapping, catalog, reports)
    complete_error = None
    if not missing and not errors:
        try:
            audit.validate_plan(catalog, mapping, merged)
        except (ValueError, KeyError, TypeError) as error:
            complete_error = str(error)
    interfaces = config.get('fullRun', {})
    missing_interfaces = [key for key in ('tsCommand', 'javaCommand', 'tsReports', 'javaReports')
                          if not isinstance(interfaces.get(key), list) or not interfaces[key]
                          or not all(isinstance(value, str) and value for value in interfaces[key])]
    ready = not (missing or errors or complete_error or registration['duplicateReferences']
                 or missing_interfaces)
    result = {'formalAcceptance': False, 'purpose': 'full-run-preflight-only',
              'upstreamCommit': catalog['upstreamCommit'], 'javaRevision': revision,
              'catalogSha256': audit.digest(catalog_path), 'mappingSha256': audit.digest(mapping_path),
              'producerSha256': audit.digest(TASK / 'evidence-bundle.py'),
              'casesTotal': len(cases), 'structurallyPlannedCases': len(merged),
              'plannedSamples': sum(len(row['sampleIds']) for row in merged.values()),
              'plannedAssertionInstances': sum(len(row['assertionIds']) for row in merged.values()),
              'currentCaptureVerifiedCases': len(verified), 'missingPlanCases': missing,
              'missingPlanCasesByFile': dict(sorted(Counter(cases[key] for key in missing).items())),
              'locals': records, 'planErrors': errors, 'completePlanError': complete_error,
              'missingFullRunInterfaces': missing_interfaces,
              'javaRegistrations': registration, 'readyForFullCapture': ready,
              'finalRequirements': ['所有冻结用例及断言、循环、条件分支的完整输入计划',
                  '每个原用例对应独立 Java 注册身份',
                  '两端全量采集适配器消费 EVIDENCE_* 接口并记录实际输入与断言',
                  '修复完成并固定版本后，先 TS 后 Java 独立 capture；禁止沿用局部原始证据',
                  '同一次 Java clean test 后立即保存全部 Surefire XML',
                  'module-scope.json 的 scopeReview 经实际复核后为 reviewed；无过滤 API gate 通过',
                  '完整 evidence-bundle 与 audit-tests.py check，通过后才可声明正式验收']}
    return result, merged


def execution_sequence(config, folder, catalog, mapping):
    """只生成执行参数；全量适配器由调用者提供，输出必须是本次运行的新文件。"""
    folder = folder.resolve()
    plan = folder / 'input-plan.json'
    shared = ['--catalog', str(catalog.resolve()), '--mapping', str(mapping.resolve()),
              '--input-plan', str(plan)]
    capture, common = [], list(shared)
    for side in ('ts', 'java'):
        interface = config['fullRun']
        reports = [folder / name for name in interface[side + 'Reports']]
        audit.require(all(path.resolve().is_relative_to(folder) for path in reports),
                      '最终报告必须保存在新运行目录中')
        inputs, assertions = folder / (side + '-inputs.jsonl'), folder / (side + '-assertions.jsonl')
        manifest = folder / (side + '-run.json')
        command = [part.replace('{runDir}', str(folder)) for part in interface[side + 'Command']]
        if side == 'java':
            audit.require('clean' in command and 'test' in command and command.index('clean') < command.index('test')
                          and not any(audit.re.search(r'-Dtest=|skipTests|maven.test.skip|testFailureIgnore|failIfNoTests=false', part)
                                      for part in command), '最终 Java 命令必须无过滤 clean test')
        report_flags = [part for path in reports for part in ('--report', str(path))]
        capture.append([sys.executable, str(TASK / 'evidence-bundle.py'), 'capture', '--side', side,
                        *shared, '--inputs', str(inputs), '--assertions', str(assertions),
                        '--output', str(manifest), *report_flags, '--', *command])
        common.extend(['--' + side + '-inputs', str(inputs), '--' + side + '-assertions', str(assertions),
                       '--' + side + '-run-manifest', str(manifest)])
        common.extend(part for path in reports for part in ('--' + side + '-report', str(path)))
    observations = str(folder / 'parity-results.json')
    return [*capture, [sys.executable, str(TASK / 'evidence-bundle.py'), *common, '--output', observations],
            [sys.executable, str(TASK / 'audit-tests.py'), 'check', *common, '--observations', observations]]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=TASK / 'full-evidence-locals.json')
    parser.add_argument('--catalog', type=Path, default=TASK / 'module-tests.json')
    parser.add_argument('--mapping', type=Path, default=TASK / 'test-map.json')
    parser.add_argument('--java-report', action='append', default=[])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--plan-output', type=Path, help='仅输出结构计划候选；不含运行轨迹或验收结论')
    parser.add_argument('--require-ready', action='store_true', help='未满足全量采集前置时退出 1')
    parser.add_argument('--run-dir', type=Path, help='前置全部通过后，向新的运行目录写入计划与四步命令；不执行测试')
    args = parser.parse_args()
    try:
        config = load(args.config)
        revision = audit.java_revision()
        result, plan = inspect(config, args.config.resolve().parent,
                               args.catalog, args.mapping, revision, args.java_report)
        audit.require(revision == audit.java_revision(), '前置检查期间 Java 源码变化，须重新检查')
        write(args.output, result)
        if args.plan_output:
            write(args.plan_output, plan)
        if args.run_dir:
            audit.require(result['readyForFullCapture'], '全量前置未满足，拒绝生成可执行采集序列；见输出报告')
            commands = execution_sequence(config, args.run_dir, args.catalog, args.mapping)
            args.run_dir.mkdir(parents=True, exist_ok=False)
            write(args.run_dir / 'input-plan.json', plan)
            write(args.run_dir / 'commands.json', commands)
    except (ValueError, OSError, KeyError, TypeError, ET.ParseError) as error:
        parser.error(str(error))
    print(json.dumps({key: result[key] for key in ('casesTotal', 'structurallyPlannedCases',
        'plannedSamples', 'plannedAssertionInstances', 'currentCaptureVerifiedCases',
        'readyForFullCapture', 'formalAcceptance')}, ensure_ascii=False))
    return int(args.require_ready and not result['readyForFullCapture'])


if __name__ == '__main__':
    sys.exit(main())
