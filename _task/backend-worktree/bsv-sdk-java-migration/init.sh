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
for name in ['AGENTS.md', 'README.md', 'feature_list.json', 'progress.md', 'session-handoff.md', 'workspace.json', 'env.sh', 'mvn.sh', 'pnpm.sh', 'verify.sh', 'upstream-tests.json']:
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
    check(repo['name'] + ' worktree、分支与基线', verify_repo)
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
