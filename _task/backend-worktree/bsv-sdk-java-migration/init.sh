#!/usr/bin/env bash
# 只读环境自检；不安装、不联网、不启动服务，不代表完整迁移验收。
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")"
python3 - <<'PY'
from pathlib import Path
import hashlib, json, re, subprocess, sys
task = Path.cwd()
workspace = task.parents[2]
d = json.loads((task / 'workspace.json').read_text())
failures = []
def check(label, fn):
    try:
        result = fn()
        if result is False:
            raise ValueError('不满足要求')
        print('[OK]', label)
    except Exception as error:
        failures.append(label)
        print('[FAIL]', label, str(error))
def cmd(*args):
    return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT).strip()
for name in ['AGENTS.md', 'README.md', 'feature_list.json', 'progress.md', 'session-handoff.md', 'workspace.json', 'env.sh', 'mvn.sh', 'pnpm.sh', 'verify.sh', 'upstream-tests.json', 'module-scope.json', 'module-tests.json', 'test-map.json', 'audit-tests.py', 'collect-cases.cjs', 'test-audit.test.cjs', 'run-ts-baseline.py', 'ts-offline-guard.cjs']:
    check(name, lambda n=name: (task / n).is_file())
for repo in d['repositories']:
    p = task / repo['name']
    def verify_repo(p=p, repo=repo):
        assert Path(cmd('git', '-C', str(p), 'rev-parse', '--show-toplevel')) == p
        assert cmd('git', '-C', str(p), 'branch', '--show-current') == d['branch']
        subprocess.run(['git', '-C', str(p), 'merge-base', '--is-ancestor', repo['baseCommit'], 'HEAD'], check=True, capture_output=True)
        status = cmd('git', '-C', str(p), 'status', '--porcelain')
        if status:
            print('[WARN]', repo['name'], '有未提交修改，提交前核对归属')
    check(repo['name'] + ' 仓库、分支与基线', verify_repo)
def verify_java_target():
    import xml.etree.ElementTree as E
    target = d['javaTarget']
    assert target['project'] in {r['name'] for r in d['repositories']}
    project = task / target['project']
    ns = {'m': 'http://maven.apache.org/POM/4.0.0'}
    pom = E.parse(project / 'pom.xml').getroot()
    assert pom.findtext('m:artifactId', namespaces=ns) == target['project']
    package = target['package'].replace('.', '/')
    for module in json.loads((task / 'module-scope.json').read_text())['selectedModules']:
        assert (project / 'src/main/java' / package / module / 'package-info.java').is_file()
        assert (project / 'src/test/java' / package / module).is_dir()
        assert (project / 'src/test/resources/upstream' / module).is_dir()
check('独立 Java 目标工程与整模块目录', verify_java_target)
upstream = workspace / d['upstream']['path']
def verify_upstream():
    assert cmd('git', '-C', str(upstream), 'rev-parse', 'HEAD') == d['upstream']['commit']
    assert not cmd('git', '-C', str(upstream), 'status', '--porcelain')
    package = json.loads((upstream / d['upstream']['packagePath'] / 'package.json').read_text())
    root = json.loads((upstream / 'package.json').read_text())
    assert package['version'] == d['upstream']['version']
    assert root['packageManager'] == 'pnpm@' + d['tools']['pnpmVersion']
check('TypeScript 固定提交、包版本与源码完整性', verify_upstream)
def verify_inventory():
    inventory = json.loads((task / 'upstream-tests.json').read_text())
    assert inventory['upstreamCommit'] == d['upstream']['commit']
    sdk = upstream / d['upstream']['packagePath']
    paths = {p.relative_to(sdk).as_posix() for p in (sdk / 'src').rglob('*') if p.is_file() and re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', p.name)}
    assert paths == {entry['path'] for entry in inventory['files']}
    assert len(paths) == inventory['testFileCount'] == len(inventory['files'])
    for entry in inventory['files'] + inventory['supportFiles']:
        assert hashlib.sha256((sdk / entry['path']).read_bytes()).hexdigest() == entry['sha256'], entry['path']
check('上游测试文件清单与辅助向量校验值', verify_inventory)
def verify_module_inventory():
    scope = json.loads((task / 'module-scope.json').read_text())
    catalog = json.loads((task / 'module-tests.json').read_text())
    assert catalog['upstreamCommit'] == scope['upstreamCommit'] == d['upstream']['commit']
    assert catalog['scopeSha256'] == hashlib.sha256((task / 'module-scope.json').read_bytes()).hexdigest()
    assert catalog['modules'] == scope['selectedModules']
    sdk = upstream / d['upstream']['packagePath']
    files = {p.relative_to(sdk).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for module in scope['selectedModules'] for p in (sdk / 'src' / module).rglob('*') if p.is_file()}
    files.update({name: hashlib.sha256((sdk / name).read_bytes()).hexdigest()
                  for name, owner in scope.get('crossModuleTestOwners', {}).items()
                  if owner['module'] in scope['selectedModules']})
    assert catalog['moduleFiles'] == files
    tests = {name for name in files if re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', name)}
    assert tests == {f['path'] for f in catalog['files']}
check('整模块范围及全部源码/测试文件校验值（不代替动态用例验收）', verify_module_inventory)
check('Node 版本', lambda: cmd(d['tools']['node'], '--version') == d['tools']['nodeVersion'])
check('pnpm 锁定版本', lambda: cmd(str(task / 'pnpm.sh'), '--version') == d['tools']['pnpmVersion'])
def verify_maven():
    version = cmd(str(task / 'mvn.sh'), '-v')
    assert 'Apache Maven 3.9.16' in version and 'Java version: 25.' in version
check('Maven 与 JDK 25', verify_maven)
check('独立 Maven 产物', lambda: (task / '.cache/maven/com/metanet4j/metanet4j-sdk/0.2.0/metanet4j-sdk-0.2.0.jar').is_file())
check('TS SDK 构建产物', lambda: (upstream / 'packages/sdk/dist/esm/mod.js').is_file())
for tool, target in d['globalDefaults'].items():
    check('全局 ' + tool + ' 默认未变', lambda tool=tool, target=target: str((Path.home() / '.sdkman/candidates' / tool / 'current').resolve()) == target)
for tool, expected in d['globalCommandVersions'].items():
    check('全局 ' + tool + ' 版本未变', lambda tool=tool, expected=expected: cmd(tool, '--version') == expected)
def verify_state():
    state = json.loads((task / 'feature_list.json').read_text())
    assert sum(f['status'] == 'in-progress' for f in state['features']) <= 1
check('任务状态可解析且至多一个进行中事项', verify_state)
print('环境自检通过；完整测试迁移状态见 feature_list.json。' if not failures else f'环境自检失败：{len(failures)} 项。')
sys.exit(bool(failures))
PY
