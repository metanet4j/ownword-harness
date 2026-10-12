#!/usr/bin/env python3
"""重跑只读验收入口，拒绝占位提交、缩减范围、过期证据与被改写的冻结向量。"""
import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('unit', ROOT / 'verify-unit.py')
unit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(unit)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(data):
    problems = []
    def require(ok, message):
        if not ok: problems.append(message)
    def execute(command):
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        require(result.returncode == 0, '入口拒绝证据：' + ' '.join(map(str, command)) + '\n' + result.stdout[-3000:] + result.stderr[-1000:])
    repos = unit.inventory()
    heads = {r['repository']: subprocess.check_output(['git', '-C', str(ROOT/r['repository']), 'rev-parse', 'HEAD'], text=True).strip() for r in repos}
    require(data.get('repositoryHeads') == heads, '最终清单与四仓库提交不一致')
    require(data.get('status') == 'PASS', '最终清单未通过')
    for scope, key, expected in [('all', 'unit', None), ('http', 'http', 5), ('component', 'integration', 124)]:
        record = data.get(key, {})
        path = ROOT / record.get('evidence', '__missing__')
        require(record.get('exitCode') == 0 and path.is_dir(), key + ' 缺少成功的独立证据')
        if not path.is_dir(): continue
        if scope == 'all':
            execute([sys.executable, str(ROOT/'verify-unit.py'), '--mode', 'accept', '--scope', 'all', '--evidence', str(path)])
        else:
            summary = json.loads((path/'summary.json').read_text())
            require(summary.get('full') is True and summary.get('formalAcceptance') is True and not summary.get('problems'), key + ' 不是全量验收')
            require(sum(m['tests'] for m in summary['moduleCounts'].values()) == expected, key + ' 实例数不符')
            require(scope != 'component' or len(summary['classes']) == 18, 'component 必须执行 18 类')
            execute([sys.executable, str(ROOT/'verify-integration.py'), '--scope', scope, '--evidence', str(path)])
    dependencies = json.loads((ROOT/'bsv-replace-dependencies.json').read_text())
    poms = {str(Path(r['repository'])/m['path']/'pom.xml') for r in repos for m in r['modules']}
    poms = {str(Path(p)) for p in poms}
    require(len(poms) == 25 and {t['pom'] for t in dependencies['trees']} == poms and len(dependencies['trees']) == 25, '25 POM 的依赖树未齐全')
    require(dependencies['repositoryHeads'] == heads, '依赖树提交已过期')
    for tree in dependencies['trees']:
        path = ROOT/tree['path']; pom = ROOT/tree['pom']
        require(path.is_file() and sha(path) == tree['sha256'] and sha(pom) == tree['pomSha256'] and tree['exitCode'] == 0, '依赖树来源不符：' + tree['pom'])
        if path.is_file(): require(not any(p in path.read_text() for p in ['io.bitcoinsv', 'org.bitcoinj']), '依赖树残留旧库：' + tree['pom'])
    require(dependencies['oldReferences']['count'] == 0 and dependencies['attachedJars'] == 0, '旧引用或手工 JAR 未清零')
    api = json.loads((ROOT/'bsv-replace-api-map.json').read_text())
    require(api['currentReconciliation']['unmigrated'] == 0 and api['currentReconciliation']['unverified'] == 0, 'API 映射未验收')
    require(all(e.get('targetMethodsVerified') for e in api['entries']), 'API 成员存在未核实项')
    tests = json.loads((ROOT/'bsv-replace-test-map.json').read_text())
    dispositions = [m for e in tests['entries'] for m in e['methodDispositions']]
    require(len(dispositions) == 1016 and all(m.get('reason') and (m['disposition'] == 'cancelled-subject' or m['targets']) for m in dispositions), '冻结测试方法未逐项对账')
    binding = json.loads((ROOT/'bsv-replace-current-vector-bindings.json').read_text())
    frozen = json.loads((ROOT/'evidence/bsv-replace/r0-api-work/vectors-summary.json').read_text())
    require(binding['frozenSha256'] == sha(ROOT/'bsv-replace-vectors.json') == frozen['artifactFingerprint']['sha256'], '冻结输入或独立预期值被改写')
    require(len(binding['groups']) == 14 and binding.get('formalAcceptance') is True and all(g.get('verified') is True for g in binding['groups']), 'V01—V14 缺少实际执行绑定')
    for group in binding['groups']:
        require(all(item.get('executed') or item['disposition'] == 'cancelled-subject' for item in group['bindings']), group['id'] + ' 绑定方法未执行')
    features = json.loads((ROOT/'feature_list.json').read_text())
    for feature in features['features']:
        if not feature['id'].startswith('bsv-'): continue
        require(feature['status'] == 'done' and bool(feature.get('commits')), '事项未完成或缺少提交：' + feature['id'])
        for record in feature.get('commits', []):
            repository = ROOT.parents[2] if record['repository'] == 'ownword' else ROOT/record['repository']
            result = subprocess.run(['git', '-C', str(repository), 'merge-base', '--is-ancestor', record['commit'], 'HEAD'], capture_output=True)
            require(result.returncode == 0, '占位或非当前历史提交：' + feature['id'])
        for record in feature.get('evidence', []):
            if isinstance(record, dict): require((ROOT/record['path']).exists(), '证据缺失：' + feature['id'])
    return problems


if __name__ == '__main__':
    try:
        problems = verify(json.loads((ROOT/'bsv-replace-final-acceptance.json').read_text()))
    except (OSError, ValueError, KeyError) as error:
        problems = [str(error)]
    print(json.dumps({'status': 'FAIL' if problems else 'PASS', 'problems': problems}, ensure_ascii=False, indent=2))
    sys.exit(bool(problems))
