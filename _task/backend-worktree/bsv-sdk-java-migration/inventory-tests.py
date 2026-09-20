#!/usr/bin/env python3
"""盘点固定上游的测试文件；文件清单不等于动态用例或 Java 映射清单。"""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re
import subprocess

task = Path(__file__).resolve().parent
config = json.loads((task / 'workspace.json').read_text())
upstream = task.parents[2] / config['upstream']['path']
sdk = upstream / config['upstream']['packagePath']
commit = subprocess.check_output(['git', '-C', str(upstream), 'rev-parse', 'HEAD'], text=True).strip()
assert commit == config['upstream']['commit'], '上游提交不匹配'
result = subprocess.run(
    [str(task / 'pnpm.sh'), '--dir', str(sdk), 'exec', 'jest', '--listTests', '--runInBand', '--watchman=false', '--json'],
    check=True, capture_output=True, text=True,
)
discovered = {Path(p).relative_to(sdk).as_posix() for p in json.loads(result.stdout)}
(task / '.cache/evidence/ts-discovered-tests.json').write_text(json.dumps(sorted(discovered), indent=2) + '\n')
# Jest 的默认命名规则，另保留手动资源用例；候选范围包含所有 src 下测试目录。
files = sorted(p for p in (sdk / 'src').rglob('*') if p.is_file() and re.search(r'\.(test|spec)\.[cm]?[jt]sx?$', p.name))
paths = {p.relative_to(sdk).as_posix() for p in files}
assert not discovered - paths, '存在尚未纳入静态盘点的 Jest 文件'
entries = []
for p in files:
    relative = p.relative_to(sdk).as_posix()
    raw = p.read_bytes()
    excluded = relative not in discovered
    assert not excluded or p.name.endswith('.man.test.ts'), '需解释额外配置排除：' + relative
    entries.append({
        'path': relative,
        'sha256': hashlib.sha256(raw).hexdigest(),
        'jestDefaultDiscovered': not excluded,
        'upstreamDefaultExclusion': 'manual/resource（上游 Jest 默认排除，迁移不能据此遗漏）' if excluded else None,
    })
inventory = {
    'upstreamCommit': commit,
    'scope': 'packages/sdk 全部测试文件；整模块范围见 module-scope.json，注册用例见 module-tests.json，Java 映射见 test-map.json',
    'testFileCount': len(entries),
    'jestDefaultFileCount': len(discovered),
    'defaultExcludedFileCount': len(paths - discovered),
    'byDirectory': dict(sorted(Counter(p.relative_to(sdk).parts[1] for p in files).items())),
    'files': entries,
    'supportFiles': [
        {'path': p.relative_to(sdk).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}
        for p in sorted((sdk / 'src').rglob('*'))
        if p.is_file() and p not in files and any(part in ('__tests', '__tests__', '__test') for part in p.parts)
    ],
}
(task / 'upstream-tests.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({k: v for k, v in inventory.items() if k not in ('files', 'supportFiles')}, ensure_ascii=False, indent=2))
print('测试辅助文件：', len(inventory['supportFiles']))
